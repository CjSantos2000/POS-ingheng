from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from openpyxl import load_workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.utils import timezone

from .models import Product, SaleItem, SaleTransaction, StockMovement, reduce_product_stock


CART_CACHE_TIMEOUT = 60 * 60 * 8


@dataclass
class CartTotals:
    subtotal: Decimal
    tax: Decimal
    total: Decimal


def get_cart_cache_key(user_id: int) -> str:
    return f"pos-cart-{user_id}"


def get_cart(user_id: int) -> dict:
    return cache.get(get_cart_cache_key(user_id), {})


def save_cart(user_id: int, cart: dict) -> None:
    cache.set(get_cart_cache_key(user_id), cart, timeout=CART_CACHE_TIMEOUT)


def clear_cart(user_id: int) -> None:
    cache.delete(get_cart_cache_key(user_id))


def calculate_cart_totals(cart: dict, discount_amount: Decimal = Decimal("0.00")) -> CartTotals:
    subtotal = sum(Decimal(str(item["subtotal"])) for item in cart.values())
    tax = (subtotal - discount_amount) * settings.POS_TAX_RATE
    total = max(subtotal - discount_amount + tax, Decimal("0.00"))
    return CartTotals(subtotal=subtotal, tax=tax.quantize(Decimal("0.01")), total=total.quantize(Decimal("0.01")))


def scan_product_into_cart(*, user_id: int, barcode: str) -> tuple[dict, CartTotals]:
    # Only pull the columns needed for scan-time response to keep barcode lookups fast.
    product = Product.objects.only("id", "name", "barcode", "selling_price", "stock_quantity").get(barcode=barcode, is_active=True)
    cart = get_cart(user_id)
    item = cart.get(str(product.id))

    if item:
        item["quantity"] += 1
        item["subtotal"] = str((Decimal(item["unit_price"]) * item["quantity"]).quantize(Decimal("0.01")))
    else:
        item = {
            "product_id": product.id,
            "barcode": product.barcode,
            "name": product.name,
            "unit_price": str(product.selling_price),
            "quantity": 1,
            "subtotal": str(product.selling_price.quantize(Decimal("0.01"))),
            "stock_quantity": product.stock_quantity,
        }
        cart[str(product.id)] = item

    save_cart(user_id, cart)
    totals = calculate_cart_totals(cart)
    return item, totals


def update_cart_item_quantity(*, user_id: int, product_id: int, quantity: int) -> CartTotals:
    cart = get_cart(user_id)
    key = str(product_id)
    if key not in cart:
        return calculate_cart_totals(cart)
    if quantity <= 0:
        cart.pop(key)
    else:
        unit_price = Decimal(cart[key]["unit_price"])
        cart[key]["quantity"] = quantity
        cart[key]["subtotal"] = str((unit_price * quantity).quantize(Decimal("0.01")))
    save_cart(user_id, cart)
    return calculate_cart_totals(cart)


def cart_snapshot(user_id: int) -> tuple[list[dict], CartTotals]:
    cart = get_cart(user_id)
    items = list(cart.values())
    return items, calculate_cart_totals(cart)


def generate_receipt_number() -> str:
    return timezone.localtime().strftime("R%Y%m%d%H%M%S%f")[-18:]


@transaction.atomic
def finalize_sale(*, user, customer, payment_method: str, discount_amount: Decimal) -> SaleTransaction:
    cart = get_cart(user.id)
    if not cart:
        raise ValueError("Cart is empty.")

    product_ids = [int(product_id) for product_id in cart.keys()]
    # Lock scanned rows only while checkout is running so concurrent cashiers do not oversell.
    products = Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)
    product_map = {product.id: product for product in products}

    for key, item in cart.items():
        product = product_map.get(int(key))
        if product is None:
            raise ValueError(f"Product {key} is unavailable.")
        if product.stock_quantity < item["quantity"]:
            raise ValueError(f"Insufficient stock for {product.name}.")

    totals = calculate_cart_totals(cart, discount_amount=discount_amount)
    transaction_obj = SaleTransaction.objects.create(
        receipt_number=generate_receipt_number(),
        cashier=user,
        customer=customer,
        subtotal=totals.subtotal,
        tax_amount=totals.tax,
        discount_amount=discount_amount,
        total_amount=totals.total,
        payment_method=payment_method,
    )

    sale_items = []
    stock_movements = []
    for key, item in cart.items():
        product_id = int(key)
        quantity = item["quantity"]
        unit_price = Decimal(item["unit_price"])
        line_total = Decimal(item["subtotal"])
        sale_items.append(
            SaleItem(
                transaction=transaction_obj,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
        reduce_product_stock(product_id, quantity)
        stock_movements.append(
            StockMovement(
                product_id=product_id,
                movement_type=StockMovement.MovementType.SALE,
                quantity_delta=-quantity,
                reference=transaction_obj.receipt_number,
            )
        )

    SaleItem.objects.bulk_create(sale_items)
    StockMovement.objects.bulk_create(stock_movements)
    clear_cart(user.id)
    return transaction_obj


def parse_product_upload(uploaded_file) -> list[dict]:
    suffix = uploaded_file.name.lower()
    if suffix.endswith(".csv"):
        content = uploaded_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        return [row for row in reader]

    workbook = load_workbook(uploaded_file, read_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    headers = [str(value).strip() if value is not None else "" for value in rows[0]]
    parsed = []
    for row in rows[1:]:
        parsed.append({headers[index]: value for index, value in enumerate(row)})
    return parsed


def import_products(rows: list[dict]) -> int:
    count = 0
    for row in rows:
        barcode = str(row.get("barcode", "")).strip()
        if not barcode:
            continue
        product, _ = Product.objects.update_or_create(
            barcode=barcode,
            defaults={
                "sku": str(row.get("sku", barcode)).strip(),
                "name": str(row.get("name", "Unnamed Item")).strip(),
                "category": str(row.get("category", "")).strip(),
                "description": str(row.get("description", "")).strip(),
                "cost_price": Decimal(str(row.get("cost_price", "0") or "0")),
                "selling_price": Decimal(str(row.get("selling_price", "0") or "0")),
                "stock_quantity": int(row.get("stock_quantity", 0) or 0),
                "reorder_level": int(row.get("reorder_level", settings.POS_LOW_STOCK_DEFAULT) or settings.POS_LOW_STOCK_DEFAULT),
                "is_active": str(row.get("is_active", "true")).lower() not in {"false", "0", "no"},
            },
        )
        StockMovement.objects.create(
            product=product,
            movement_type=StockMovement.MovementType.IMPORT,
            quantity_delta=product.stock_quantity,
            reference="bulk-import",
        )
        count += 1
    return count


def export_products_csv() -> HttpResponse:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["sku", "barcode", "name", "category", "selling_price", "stock_quantity", "reorder_level", "is_active"])
    for product in Product.objects.order_by("name").values_list(
        "sku", "barcode", "name", "category", "selling_price", "stock_quantity", "reorder_level", "is_active"
    ):
        writer.writerow(product)
    return response


def build_receipt_pdf(transaction_obj: SaleTransaction) -> HttpResponse:
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{transaction_obj.receipt_number}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "POS Ingheng Receipt")
    y -= 25
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Receipt: {transaction_obj.receipt_number}")
    y -= 18
    pdf.drawString(50, y, f"Date: {timezone.localtime(transaction_obj.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 18
    pdf.drawString(50, y, f"Cashier: {transaction_obj.cashier.username}")
    y -= 28

    for item in transaction_obj.items.select_related("product"):
        pdf.drawString(50, y, f"{item.product.name} x {item.quantity}")
        pdf.drawRightString(width - 50, y, f"${item.line_total}")
        y -= 18

    y -= 10
    pdf.drawString(50, y, f"Subtotal: ${transaction_obj.subtotal}")
    y -= 18
    pdf.drawString(50, y, f"Tax: ${transaction_obj.tax_amount}")
    y -= 18
    pdf.drawString(50, y, f"Discount: ${transaction_obj.discount_amount}")
    y -= 18
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Total: ${transaction_obj.total_amount}")

    pdf.showPage()
    pdf.save()
    return response


def sales_summary_queryset(start_date=None, end_date=None):
    queryset = SaleTransaction.objects.all()
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    return queryset


def report_metrics(start_date=None, end_date=None) -> dict:
    queryset = sales_summary_queryset(start_date, end_date)
    gross_sales = queryset.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    transaction_count = queryset.count()
    items_sold = SaleItem.objects.filter(transaction__in=queryset).aggregate(total=Sum("quantity"))["total"] or 0
    top_products = (
        SaleItem.objects.filter(transaction__in=queryset)
        .values("product__name")
        .annotate(quantity_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-quantity_sold")[:10]
    )
    return {
        "gross_sales": gross_sales,
        "transaction_count": transaction_count,
        "items_sold": items_sold,
        "top_products": top_products,
    }
