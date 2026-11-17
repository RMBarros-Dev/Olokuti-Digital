from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from config.forms import apply_bootstrap_classes

from .models import Category, Product, ProductTranslation


class ProductForm(forms.ModelForm):
    currency = forms.ChoiceField(
        choices=Product.Currency.choices,
        required=False,
        initial=Product.Currency.EUR,
        label=_("Currency"),
    )
    image_url = forms.URLField(
        required=False,
        assume_scheme="https",
        label=_("Image URL"),
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "barcode",
            "category",
            "origin",
            "price",
            "currency",
            "image_url",
            "description",
            "sustainability_info",
            "attributes",
        ]
        labels = {
            "name": _("Name"),
            "sku": _("SKU"),
            "barcode": _("Barcode"),
            "category": _("Category"),
            "origin": _("Origin"),
            "price": _("Price"),
            "currency": _("Currency"),
            "image_url": _("Image URL"),
            "description": _("Description"),
            "sustainability_info": _("Sustainability information"),
            "attributes": _("Attributes (JSON)"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "sustainability_info": forms.Textarea(attrs={"rows": 3}),
            "attributes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attributes"].required = False
        apply_bootstrap_classes(self.fields)

    def clean_currency(self):
        return self.cleaned_data.get("currency") or Product.Currency.EUR

    def clean_sku(self):
        sku = (self.cleaned_data.get("sku") or "").strip()
        if sku:
            qs = Product.objects.filter(sku=sku)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_("A product with this SKU already exists."))
        return sku

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < Decimal("0"):
            raise forms.ValidationError(_("Price must be zero or positive."))
        return price

    def clean_attributes(self):
        attrs = self.cleaned_data.get("attributes")
        if attrs is None:
            return {}
        if not isinstance(attrs, dict):
            raise forms.ValidationError(
                _('Attributes must be a JSON object (e.g. {"material": "cotton"}).')
            )
        return attrs


class ProductTranslationForm(forms.ModelForm):
    class Meta:
        model = ProductTranslation
        fields = ["locale", "name", "description", "sustainability_info"]
        labels = {
            "locale": _("Language"),
            "name": _("Translated name"),
            "description": _("Translated description"),
            "sustainability_info": _("Translated sustainability information"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "sustainability_info": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        labels = {
            "name": _("Category name"),
            "description": _("Description"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)
