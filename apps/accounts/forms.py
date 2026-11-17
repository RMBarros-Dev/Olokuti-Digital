from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from config.forms import apply_bootstrap_classes


def _validate_privileged_groups(acting_user, selected_groups):
    """Prevent non-superusers from assigning audit/manager privilege groups."""
    if getattr(acting_user, "is_superuser", False):
        return
    if selected_groups and selected_groups.filter(permissions__codename="view_auditlog").exists():
        raise ValidationError(_("Only superusers can assign audit or manager privilege groups."))


class PublicRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False, label=_("Email"))
    first_name = forms.CharField(max_length=150, required=False, label=_("First name"))
    last_name = forms.CharField(max_length=150, required=False, label=_("Last name"))

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name")
        labels = {
            "username": _("Username"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_classes(self.fields)


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

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        if acting_user is not None and not getattr(acting_user, "is_superuser", False):
            self.fields["groups"].queryset = Group.objects.exclude(
                permissions__codename="view_auditlog"
            ).order_by("name")
        apply_bootstrap_classes(self.fields)

    def clean_groups(self):
        groups = self.cleaned_data.get("groups")
        if self.acting_user is not None:
            _validate_privileged_groups(self.acting_user, groups)
        return groups

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = self.cleaned_data.get("is_staff", False)
        user.is_superuser = False
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

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        if acting_user is not None and not getattr(acting_user, "is_superuser", False):
            self.fields["groups"].queryset = Group.objects.exclude(
                permissions__codename="view_auditlog"
            ).order_by("name")
        apply_bootstrap_classes(self.fields)

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        if password:
            validate_password(password, self.instance)
        return password

    def clean_groups(self):
        groups = self.cleaned_data.get("groups")
        if self.acting_user is not None:
            _validate_privileged_groups(self.acting_user, groups)
        return groups

    def clean(self):
        cleaned = super().clean()
        if self.acting_user is not None and self.instance.pk == self.acting_user.pk:
            if not cleaned.get("is_active", True):
                self.add_error("is_active", _("You cannot deactivate your own account."))
            if not cleaned.get("is_staff", False) and not self.acting_user.is_superuser:
                self.add_error("is_staff", _("You cannot remove your own staff access."))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("new_password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user
