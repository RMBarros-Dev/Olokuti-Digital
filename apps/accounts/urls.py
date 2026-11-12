from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import (
    AccountLoginView,
    dashboard,
    setup_default_groups,
    user_create,
    user_list,
    user_update,
)

app_name = "accounts"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("accounts/login/", AccountLoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("accounts/users/", user_list, name="user-list"),
    path("accounts/users/new/", user_create, name="user-create"),
    path("accounts/users/<int:pk>/edit/", user_update, name="user-update"),
    path("accounts/users/setup-groups/", setup_default_groups, name="setup-groups"),
]
