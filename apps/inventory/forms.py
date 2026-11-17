from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Product
from config.forms import apply_bootstrap_classes

from .models import StockItem, StockLocation, StockMovement
from .services import record_stock_movement


class StockLocationForm(forms.ModelForm):
    class Meta:
        model = StockLocation
        fields = ["name", "code", "is_active", "description"]
        labels = {
            "name": _("Name"),
            "code": _("Location code"),
            "is_active": _("Active"),
            "description": _("Description"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)

    def clean_code(self):
        return (self.cleaned_data.get("code") or "").strip().upper()


class StockItemThresholdForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = ["minimum_stock"]
        labels = {
            "minimum_stock": _("Minimum stock alert threshold"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)


class StockMovementForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.order_by("name"),
        label=_("Product"),
    )
    location = forms.ModelChoiceField(
        queryset=StockLocation.objects.filter(is_active=True).order_by("name"),
        label=_("Location"),
    )
    movement_type = forms.ChoiceField(
        choices=StockMovement.MovementType.choices,
        label=_("Movement type"),
    )
    quantity = forms.IntegerField(
        min_value=0,
        label=_("Quantity"),
        help_text=_(
            "Units added (inbound), units removed (outbound), or physical count (adjustment)."
        ),
    )
    minimum_stock = forms.IntegerField(
        required=False,
        min_value=0,
        label=_("Minimum stock threshold (optional)"),
    )
    reference = forms.CharField(
        required=False,
        max_length=120,
        label=_("Reference"),
        help_text=_("Optional order, supplier delivery note, or audit reference."),
    )
    reason = forms.CharField(
        max_length=255,
        label=_("Reason"),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)

    def save(self) -> StockMovement:
        try:
            return record_stock_movement(
                product=self.cleaned_data["product"],
                location=self.cleaned_data["location"],
                movement_type=self.cleaned_data["movement_type"],
                quantity=self.cleaned_data["quantity"],
                minimum_stock=self.cleaned_data.get("minimum_stock"),
                reference=self.cleaned_data.get("reference", ""),
                reason=self.cleaned_data["reason"],
                user=self.user,
            )
        except ValidationError as exc:
            self.add_error(None, exc)
            raise
