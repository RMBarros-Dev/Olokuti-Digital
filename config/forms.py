from django import forms


def apply_bootstrap_classes(fields) -> None:
    """Apply standard Bootstrap 5 form widget classes consistently across Django forms."""
    for field in fields.values():
        if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            field.widget.attrs["class"] = "form-check-input"
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"
