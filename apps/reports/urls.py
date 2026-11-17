from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.summary, name="summary"),
    path("tasks.csv", views.export_tasks_csv, name="tasks-csv"),
    path("inventory.csv", views.export_inventory_csv, name="inventory-csv"),
    path("summary.pdf", views.export_summary_pdf, name="summary-pdf"),
]
