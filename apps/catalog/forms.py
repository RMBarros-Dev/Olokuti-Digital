from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductTranslation


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "category", "origin", "sustainability_info"]
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "category": _("Category"),
            "origin": _("Origin"),
            "sustainability_info": _("Sustainability information"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "sustainability_info": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


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
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


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
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
