from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from config.forms import apply_bootstrap_classes

from .models import OperationalTask, TaskComment


class OperationalTaskForm(forms.ModelForm):
    class Meta:
        model = OperationalTask
        fields = [
            "title",
            "description",
            "category",
            "product",
            "status",
            "priority",
            "assigned_to",
            "due_date",
        ]
        labels = {
            "title": _("Title"),
            "description": _("Description"),
            "category": _("Category"),
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
        self.fields["category"].required = False
        self.fields["assigned_to"].queryset = (
            get_user_model().objects.filter(is_active=True).order_by("username")
        )
        apply_bootstrap_classes(self.fields)

    def clean_category(self):
        return self.cleaned_data.get("category") or OperationalTask.Category.GENERAL


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["body"]
        labels = {"body": _("Comment")}
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": _("Add an operational update or coordination note…"),
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError(_("Comment text cannot be empty."))
        return body
