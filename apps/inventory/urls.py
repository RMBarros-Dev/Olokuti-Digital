from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.stock_list, name="stock-list"),
    path("export.csv", views.stock_export_csv, name="stock-export-csv"),
    path("items/<uuid:pk>/threshold/", views.stock_item_threshold_update, name="threshold-update"),
    path("movements/", views.movement_list, name="movement-list"),
    path("movements/new/", views.movement_create, name="movement-create"),
    path("locations/", views.location_list, name="location-list"),
    path("locations/new/", views.location_create, name="location-create"),
    path("locations/<int:pk>/edit/", views.location_update, name="location-update"),
]
