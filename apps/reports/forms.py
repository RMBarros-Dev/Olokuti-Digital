from django import forms
from django.utils.translation import gettext_lazy as _


class ReportFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", _("End date must be on or after start date."))
        return cleaned
