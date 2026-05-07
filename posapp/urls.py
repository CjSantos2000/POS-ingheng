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
    path("products/import/", views.product_import_view, name="product_import"),
    path("products/export/", views.product_export_view, name="product_export"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/<int:pk>/receipt/", views.receipt_view, name="receipt_view"),
    path("reports/", views.reports_view, name="reports"),
    path("low-stock/", views.low_stock_view, name="low_stock"),
    path("customers/", views.customers_view, name="customers"),
]
