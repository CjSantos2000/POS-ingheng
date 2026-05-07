from django.urls import path

from .views import ProductDetailAPI, ProductListAPI, ScanProductAPI


urlpatterns = [
    path("products/", ProductListAPI.as_view(), name="api_products"),
    path("products/<int:pk>/", ProductDetailAPI.as_view(), name="api_product_detail"),
    path("scan/", ScanProductAPI.as_view(), name="api_scan"),
]
