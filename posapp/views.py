from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CheckoutForm, CustomerForm, ImportProductsForm, ProductForm, ReportFilterForm
from .models import Customer, Product, SaleTransaction
from .serializers import ProductSerializer
from .services import (
    build_receipt_pdf,
    cart_snapshot,
    clear_cart,
    export_products_csv,
    finalize_sale,
    import_products,
    parse_product_upload,
    report_metrics,
    scan_product_into_cart,
    update_cart_item_quantity,
)


def admin_required(user) -> bool:
    return user.is_authenticated and user.can_manage_inventory


def ensure_admin(request) -> None:
    if not admin_required(request.user):
        raise PermissionDenied


@login_required
def dashboard(request):
    metrics = report_metrics()
    low_stock_products = Product.objects.filter(is_active=True, stock_quantity__lte=F("reorder_level")).order_by("stock_quantity")[:10]
    return render(request, "posapp/dashboard.html", {"metrics": metrics, "low_stock_products": low_stock_products})


@login_required
def pos_terminal(request):
    items, totals = cart_snapshot(request.user.id)
    checkout_form = CheckoutForm()
    return render(request, "posapp/pos_terminal.html", {"cart_items": items, "totals": totals, "checkout_form": checkout_form})


@login_required
@require_POST
def scan_barcode(request):
    barcode = request.POST.get("barcode", "").strip()
    if not barcode:
        return JsonResponse({"error": "Barcode is required."}, status=400)
    try:
        item, totals = scan_product_into_cart(user_id=request.user.id, barcode=barcode)
    except Product.DoesNotExist:
        return JsonResponse({"error": f"Barcode {barcode} was not found."}, status=404)
    return JsonResponse({"item": item, "totals": totals.__dict__})


@login_required
@require_POST
def update_cart(request, product_id: int):
    quantity = int(request.POST.get("quantity", 1))
    totals = update_cart_item_quantity(user_id=request.user.id, product_id=product_id, quantity=quantity)
    items, _ = cart_snapshot(request.user.id)
    return JsonResponse({"items": items, "totals": totals.__dict__})


@login_required
@require_POST
def clear_cart_view(request):
    clear_cart(request.user.id)
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def checkout(request):
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    try:
        transaction_obj = finalize_sale(
            user=request.user,
            customer=form.cleaned_data["customer"],
            payment_method=form.cleaned_data["payment_method"],
            discount_amount=form.cleaned_data["discount_amount"] or Decimal("0.00"),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"receipt_number": transaction_obj.receipt_number, "receipt_url": f"/transactions/{transaction_obj.id}/receipt/"})


@login_required
def product_list(request):
    ensure_admin(request)
    query = request.GET.get("q", "").strip()
    products = Product.objects.all().order_by("name")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(barcode__icontains=query) | Q(sku__icontains=query))
    return render(request, "posapp/product_list.html", {"products": products[:200], "query": query})


@login_required
def product_create(request):
    ensure_admin(request)
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product saved.")
        return redirect("product_list")
    return render(request, "posapp/product_form.html", {"form": form, "title": "Add Product"})


@login_required
def product_edit(request, pk: int):
    ensure_admin(request)
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated.")
        return redirect("product_list")
    return render(request, "posapp/product_form.html", {"form": form, "title": f"Edit {product.name}"})


@login_required
def product_import_view(request):
    ensure_admin(request)
    form = ImportProductsForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        rows = parse_product_upload(form.cleaned_data["file"])
        imported = import_products(rows)
        messages.success(request, f"Imported {imported} products.")
        return redirect("product_list")
    return render(request, "posapp/product_import.html", {"form": form})


@login_required
def product_export_view(request):
    ensure_admin(request)
    return export_products_csv()


@login_required
def transaction_list(request):
    transactions = SaleTransaction.objects.select_related("cashier", "customer").prefetch_related("items__product")[:100]
    return render(request, "posapp/transaction_list.html", {"transactions": transactions})


@login_required
def receipt_view(request, pk: int):
    transaction_obj = get_object_or_404(SaleTransaction.objects.select_related("cashier", "customer").prefetch_related("items__product"), pk=pk)
    if request.GET.get("format") == "pdf":
        return build_receipt_pdf(transaction_obj)
    return render(request, "posapp/receipt.html", {"transaction": transaction_obj})


@login_required
def reports_view(request):
    ensure_admin(request)
    form = ReportFilterForm(request.GET or None)
    start_date = end_date = None
    if form.is_valid():
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")
    metrics = report_metrics(start_date, end_date)
    return render(request, "posapp/reports.html", {"form": form, "metrics": metrics})


@login_required
def low_stock_view(request):
    ensure_admin(request)
    products = Product.objects.filter(is_active=True, stock_quantity__lte=F("reorder_level")).order_by("stock_quantity", "name")
    return render(request, "posapp/low_stock.html", {"products": products})


@login_required
def customers_view(request):
    form = CustomerForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("customers")
    customers = Customer.objects.order_by("name")[:200]
    return render(request, "posapp/customers.html", {"form": form, "customers": customers})


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.can_manage_inventory


class ProductListAPI(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        queryset = Product.objects.filter(is_active=True).only(
            "id", "sku", "barcode", "name", "category", "selling_price", "stock_quantity", "reorder_level", "is_active"
        )
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(barcode__icontains=query) | Q(sku__icontains=query))
        return queryset[:50]


class ProductDetailAPI(generics.RetrieveUpdateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [IsAdminOrReadOnly]


class ScanProductAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        barcode = str(request.data.get("barcode", "")).strip()
        if not barcode:
            return Response({"error": "barcode is required"}, status=400)
        try:
            item, totals = scan_product_into_cart(user_id=request.user.id, barcode=barcode)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)
        return Response({"item": item, "totals": totals.__dict__})
