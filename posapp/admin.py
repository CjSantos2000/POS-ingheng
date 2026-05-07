from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Customer, Product, SaleItem, SaleTransaction, StockMovement, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (("POS", {"fields": ("role",)}),)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "barcode", "selling_price", "stock_quantity", "reorder_level", "is_active")
    search_fields = ("name", "sku", "barcode")
    list_filter = ("category", "is_active")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "cashier", "total_amount", "payment_method", "created_at")
    list_filter = ("payment_method", "created_at")
    search_fields = ("receipt_number", "cashier__username")
    inlines = [SaleItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity_delta", "reference", "created_at")
    list_filter = ("movement_type", "created_at")
