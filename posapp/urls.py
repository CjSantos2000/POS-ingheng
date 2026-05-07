from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("terminal/", views.pos_terminal, name="pos_terminal"),
    path("terminal/scan/", views.scan_barcode, name="scan_barcode"),
    path("terminal/cart/<int:product_id>/", views.update_cart, name="update_cart"),
    path("terminal/cart/clear/", views.clear_cart_view, name="clear_cart"),
    path("terminal/checkout/", views.checkout, name="checkout"),
    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/barcode/", views.product_barcode_print_view, name="product_barcode_print"),
    path("products/import/", views.product_import_view, name="product_import"),
    path("products/stock-in/", views.stock_import_view, name="stock_import"),
    path("products/export/", views.product_export_view, name="product_export"),
    path("products/export/stock-template/", views.stock_template_export_view, name="stock_template_export"),
    path("products/export/stock-levels/", views.stock_levels_export_view, name="stock_levels_export"),
    path("products/barcodes/", views.product_barcodes_print_view, name="product_barcodes_print"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/<int:pk>/receipt/", views.receipt_view, name="receipt_view"),
    path("reports/", views.reports_view, name="reports"),
    path("low-stock/", views.low_stock_view, name="low_stock"),
    path("customers/", views.customers_view, name="customers"),
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle_active, name="user_toggle_active"),
]
