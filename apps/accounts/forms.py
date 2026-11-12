from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _


class ManagedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, label=_("Email"))
    first_name = forms.CharField(max_length=150, required=False, label=_("First name"))
    last_name = forms.CharField(max_length=150, required=False, label=_("Last name"))
    is_staff = forms.BooleanField(
        required=False,
        label=_("Staff access (can manage users)"),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        label=_("Groups"),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name", "is_staff", "groups")
        labels = {
            "username": _("Username"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get("is_staff", False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
        return user


class ManagedUserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False, label=_("Email"))
    first_name = forms.CharField(max_length=150, required=False, label=_("First name"))
    last_name = forms.CharField(max_length=150, required=False, label=_("Last name"))
    is_staff = forms.BooleanField(
        required=False,
        label=_("Staff access (can manage users)"),
    )
    new_password = forms.CharField(
        required=False,
        label=_("New password (optional)"),
        help_text=_("Leave blank to keep the current password."),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        label=_("Groups"),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "groups",
        )
        labels = {
            "username": _("Username"),
            "is_active": _("Active"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("new_password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user
