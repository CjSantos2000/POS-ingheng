from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "barcode",
            "name",
            "category",
            "selling_price",
            "stock_quantity",
            "reorder_level",
            "is_active",
        ]
