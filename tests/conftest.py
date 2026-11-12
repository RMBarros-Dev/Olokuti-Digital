import pytest
from django.contrib.auth.models import Permission
from django.utils import translation


@pytest.fixture(autouse=True)
def reset_language():
    translation.activate("en")
    yield
    translation.activate("en")


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="tester", password="safe-test-password")


def grant_permissions(user, *codenames):
    permissions = Permission.objects.filter(codename__in=codenames)
    user.user_permissions.add(*permissions)
