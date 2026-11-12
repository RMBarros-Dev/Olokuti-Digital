import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalog.models import Product, ProductTranslation


@pytest.mark.django_db
def test_product_create_and_controlled_delete(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["add_product", "view_product", "delete_product"])
    )
    client.force_login(user)
    response = client.post(
        reverse("catalog:product-create"),
        {
            "name": "Demo product",
            "description": "Original description",
            "origin": "Barcelona",
            "sustainability_info": "Demo data",
        },
    )
    assert response.status_code == 302
    product = Product.objects.get(name="Demo product")
    assert AuditLog.objects.filter(
        entity="catalog.Product", entity_id=str(product.pk), action="created"
    ).exists()

    confirm = client.get(reverse("catalog:product-delete", args=[product.pk]))
    assert confirm.status_code == 200
    deleted = client.post(reverse("catalog:product-delete", args=[product.pk]))
    assert deleted.status_code == 302
    assert not Product.objects.filter(pk=product.pk).exists()
    assert AuditLog.objects.filter(entity_id=str(product.pk), action="deleted").exists()


@pytest.mark.django_db
def test_catalog_is_forbidden_without_view_permission(client, user):
    client.force_login(user)
    response = client.get(reverse("catalog:product-list"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_product_translation_keeps_original_values(user):
    product = Product.objects.create(name="Original", description="Source language")
    ProductTranslation.objects.create(
        product=product, locale="ca", name="Traducció", description="Localized"
    )
    product.refresh_from_db()
    assert product.name == "Original"
    assert product.description == "Source language"


@pytest.mark.django_db
def test_catalog_displays_active_language_translation_and_saves_new_translation(client, user):
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "change_product"])
    )
    product = Product.objects.create(name="Cotton Tote", description="Original English")
    client.force_login(user)

    save_resp = client.post(
        f"/pt-br/catalog/{product.pk}/translations/",
        {
            "locale": "pt-br",
            "name": "Ecobag de Algodão",
            "description": "Descrição em português",
            "sustainability_info": "100% orgânico",
        },
    )
    assert save_resp.status_code == 302

    list_resp = client.get("/pt-br/catalog/")
    assert list_resp.status_code == 200
    assert "Ecobag de Algodão" in list_resp.content.decode()


@pytest.mark.django_db
def test_category_creation_and_protected_deletion(client, user):
    from apps.catalog.models import Category

    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["view_product", "add_product", "delete_product"])
    )
    client.force_login(user)

    create_resp = client.post(
        reverse("catalog:category-list"),
        {"name": "Ceramics", "description": "Handcrafted"},
    )
    assert create_resp.status_code == 302
    category = Category.objects.get(name="Ceramics")

    product = Product.objects.create(name="Mug", category=category)
    del_blocked = client.post(reverse("catalog:category-delete", args=[category.pk]))
    assert del_blocked.status_code == 302
    assert Category.objects.filter(pk=category.pk).exists()

    product.delete()
    del_ok = client.post(reverse("catalog:category-delete", args=[category.pk]))
    assert del_ok.status_code == 302
    assert not Category.objects.filter(pk=category.pk).exists()


@pytest.mark.django_db
def test_product_detail_and_csv_export(client, user):
    user.user_permissions.add(*Permission.objects.filter(codename="view_product"))
    product = Product.objects.create(
        name="=Cork Bottle",
        description="Full detailed text for cork bottle",
        sustainability_info="100% renewable cork",
    )
    client.force_login(user)

    detail_resp = client.get(reverse("catalog:product-detail", args=[product.pk]))
    assert detail_resp.status_code == 200
    assert "Full detailed text for cork bottle" in detail_resp.content.decode()

    csv_resp = client.get(reverse("catalog:product-export-csv"))
    assert csv_resp.status_code == 200
    assert "'=Cork Bottle" in csv_resp.content.decode("utf-8-sig")


