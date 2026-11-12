import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("accounts:dashboard"))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize(
    "language",
    ["es-419", "es-es", "ca", "gl", "eu", "en-us", "en-gb", "en", "pt-br", "pt-pt"],
)
def test_all_configured_language_prefixes_resolve(client, language):
    response = client.get(f"/{language}/accounts/login/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_can_create_user_and_group(client, django_user_model):
    from django.contrib.auth.models import Group

    staff = django_user_model.objects.create_user(
        username="admin", password="safe-test-password", is_staff=True
    )
    group = Group.objects.create(name="Catalogue viewers")
    client.force_login(staff)
    response = client.post(
        reverse("accounts:user-create"),
        {
            "username": "new-user",
            "email": "",
            "first_name": "",
            "last_name": "",
            "groups": [str(group.pk)],
            "password1": "A-unique-safe-test-password-449!",
            "password2": "A-unique-safe-test-password-449!",
        },
    )
    assert response.status_code == 302
    created = django_user_model.objects.get(username="new-user")
    assert list(created.groups.all()) == [group]


@pytest.mark.django_db
def test_language_prefix_translates_interface_text(client):
    response = client.get("/pt-br/accounts/login/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "Bem-vindo de volta" in content
    assert "language-select-anon" in content


@pytest.mark.django_db
def test_staff_can_setup_default_groups_and_update_user(client, django_user_model):
    from django.contrib.auth.models import Group

    staff = django_user_model.objects.create_user(
        username="admin", password="safe-test-password", is_staff=True
    )
    target = django_user_model.objects.create_user(
        username="member", password="safe-test-password"
    )
    client.force_login(staff)

    setup_resp = client.post(reverse("accounts:setup-groups"))
    assert setup_resp.status_code == 302
    cat_group = Group.objects.get(name="Catalogue Team")

    edit_resp = client.post(
        reverse("accounts:user-update", args=[target.pk]),
        {
            "username": "member",
            "email": "member@olokuti.local",
            "first_name": "Maria",
            "last_name": "Silva",
            "is_active": "on",
            "is_staff": "on",
            "new_password": "Updated-safe-password-998!",
            "groups": [str(cat_group.pk)],
        },
    )
    assert edit_resp.status_code == 302
    target.refresh_from_db()
    assert target.first_name == "Maria"
    assert target.is_staff is True
    assert target.check_password("Updated-safe-password-998!")
    assert list(target.groups.all()) == [cat_group]

