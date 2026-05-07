from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Customer, Product, SaleTransaction


class POSAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "sku",
            "barcode",
            "name",
            "category",
            "description",
            "cost_price",
            "selling_price",
            "stock_quantity",
            "reorder_level",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ImportProductsForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV or XLSX.")


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "loyalty_code"]


class CheckoutForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    payment_method = forms.ChoiceField(choices=SaleTransaction.PaymentMethod.choices)
    discount_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, initial=0)


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
