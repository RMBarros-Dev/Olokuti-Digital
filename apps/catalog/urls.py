from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product-list"),
    path("export-csv/", views.export_products_csv, name="product-export-csv"),
    path("new/", views.product_create, name="product-create"),
    path("categories/", views.category_list, name="category-list"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category-delete"),
    path("<uuid:pk>/", views.product_detail, name="product-detail"),
    path("<uuid:pk>/edit/", views.product_update, name="product-update"),
    path("<uuid:pk>/delete/", views.product_delete, name="product-delete"),
    path("<uuid:pk>/translations/", views.product_translation_save, name="product-translation-save"),
    path(
        "<uuid:pk>/translations/<int:translation_id>/delete/",
        views.product_translation_delete,
        name="product-translation-delete",
    ),
]
