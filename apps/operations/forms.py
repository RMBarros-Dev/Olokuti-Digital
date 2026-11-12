from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import OperationalTask


class OperationalTaskForm(forms.ModelForm):
    class Meta:
        model = OperationalTask
        fields = [
            "title",
            "description",
            "product",
            "status",
            "priority",
            "assigned_to",
            "due_date",
        ]
        labels = {
            "title": _("Title"),
            "description": _("Description"),
            "product": _("Product"),
            "status": _("Status"),
            "priority": _("Priority"),
            "assigned_to": _("Assigned to"),
            "due_date": _("Due date"),
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = (
            get_user_model().objects.filter(is_active=True).order_by("username")
        )
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )
