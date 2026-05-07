from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import Customer, Product, SaleTransaction, User
from .services import generate_product_sku, generate_unique_barcode


class POSAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


class ProductForm(forms.ModelForm):
    barcode_mode = forms.ChoiceField(
        choices=[
            (Product.BarcodeSource.MANUAL, "Use scanned or typed barcode"),
            (Product.BarcodeSource.GENERATED, "Generate barcode automatically"),
        ],
        widget=forms.RadioSelect,
        initial=Product.BarcodeSource.MANUAL,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["barcode"].required = False
        if self.instance.pk:
            self.fields["barcode_mode"].initial = self.instance.barcode_source

    def clean(self):
        cleaned_data = super().clean()
        barcode_mode = cleaned_data.get("barcode_mode")
        barcode = (cleaned_data.get("barcode") or "").strip()
        sku = (cleaned_data.get("sku") or "").strip()

        if barcode_mode == Product.BarcodeSource.MANUAL and not barcode:
            self.add_error("barcode", "Scan or enter a barcode, or switch to automatic barcode generation.")

        if barcode:
            duplicate = Product.objects.exclude(pk=self.instance.pk).filter(barcode=barcode).exists()
            if duplicate:
                self.add_error("barcode", "This barcode already exists.")

        if sku:
            duplicate_sku = Product.objects.exclude(pk=self.instance.pk).filter(sku=sku).exists()
            if duplicate_sku:
                self.add_error("sku", "This SKU already exists.")

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        barcode_mode = self.cleaned_data["barcode_mode"]
        barcode = (self.cleaned_data.get("barcode") or "").strip()
        sku = (self.cleaned_data.get("sku") or "").strip()
        name = (self.cleaned_data.get("name") or "").strip()

        if barcode_mode == Product.BarcodeSource.GENERATED:
            if not (self.instance.pk and self.instance.barcode_source == Product.BarcodeSource.GENERATED and self.instance.barcode):
                product.barcode = generate_unique_barcode()
            else:
                product.barcode = self.instance.barcode
            product.barcode_source = Product.BarcodeSource.GENERATED
        else:
            product.barcode = barcode
            product.barcode_source = Product.BarcodeSource.MANUAL

        product.sku = sku or product.sku or generate_product_sku(name or product.barcode)

        if commit:
            product.save()
        return product

    class Meta:
        model = Product
        fields = [
            "barcode_mode",
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
            "sku": forms.TextInput(attrs={"placeholder": "Auto-generated", "class": "sku-field"}),
            "barcode": forms.TextInput(attrs={"placeholder": "Scan or type barcode", "id": "barcode-field", "class": "barcode-field"}),
            "name": forms.TextInput(attrs={"placeholder": "Product name", "class": "name-field"}),
            "category": forms.Select(attrs={"class": "category-select"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Product description (optional)"}),
            "cost_price": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Cost price"}),
            "selling_price": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Selling price"}),
            "stock_quantity": forms.NumberInput(attrs={"min": "0", "placeholder": "Quantity in stock"}),
            "reorder_level": forms.NumberInput(attrs={"min": "0", "placeholder": "Reorder level"}),
        }


class ImportProductsForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV or XLSX.")
    generate_missing_barcodes = forms.BooleanField(required=False, initial=True, help_text="Generate barcodes for rows that do not provide one.")


class StockImportForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV or XLSX with barcode or SKU and stock_in_quantity columns.")
    reference = forms.CharField(required=False, max_length=64, initial="stock-in-import", help_text="Reference saved with stock movements.")


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


class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            validate_password(password1)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role"]


class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        label="New password",
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Leave blank to keep current"}),
        help_text="Leave blank to keep the current password.",
    )

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password")
        if password:
            validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "is_active"]