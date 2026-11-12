import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.views import ensure_default_role_groups


@pytest.mark.django_db
def test_default_role_group_setup_preserves_custom_permissions():
    catalogue_group = Group.objects.create(name="Catalogue Team")
    ensure_default_role_groups()
    custom_permission = Permission.objects.get(codename="change_user")
    catalogue_group.permissions.add(custom_permission)

    ensure_default_role_groups()

    assert catalogue_group.permissions.filter(pk=custom_permission.pk).exists()
    assert catalogue_group.permissions.filter(codename="delete_category").exists()


@pytest.mark.django_db
def test_demo_seed_is_blocked_when_debug_is_disabled(settings):
    settings.DEBUG = False

    with pytest.raises(CommandError, match="DEBUG=True"):
        call_command("seed_demo")
