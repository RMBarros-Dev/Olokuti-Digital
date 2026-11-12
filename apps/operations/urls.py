from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("new/", views.task_create, name="task-create"),
    path("<uuid:pk>/edit/", views.task_update, name="task-update"),
    path("<uuid:pk>/status/", views.task_quick_status, name="task-status"),
    path("<uuid:pk>/delete/", views.task_delete, name="task-delete"),
]
