from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.audit.models import AuditLog
from apps.audit.services import record_event
from apps.catalog.models import Product
from apps.operations.models import OperationalTask

from .forms import ManagedUserCreationForm, ManagedUserUpdateForm, PublicRegistrationForm
from .ratelimit import check_rate_limit, rate_limit_response
from .services import (
    DEFAULT_ROLE_GROUPS,
    can_manage_target_user,
    ensure_default_role_groups,
    invalidate_user_sessions,
)

__all__ = [
    "AccountLoginView",
    "AccountPasswordResetConfirmView",
    "AccountPasswordResetView",
    "DEFAULT_ROLE_GROUPS",
    "dashboard",
    "ensure_default_role_groups",
    "register",
    "setup_default_groups",
    "user_create",
    "user_list",
    "user_update",
]


def staff_access_required(view_func):
    """Require an active staff account and return HTTP 403 for authenticated non-staff users."""

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


class AccountLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        blocked, retry_after = check_rate_limit(
            request,
            "login",
            limit=settings.RATE_LIMIT_LOGIN_MAX,
            window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW,
        )
        if blocked:
            return rate_limit_response(
                retry_after,
                _("Too many sign-in attempts. Please wait before trying again."),
            )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        record_event(
            user=self.request.user,
            action="login_succeeded",
            entity="auth.User",
            entity_id=self.request.user.pk,
            details={"method": "password"},
        )
        return response

    def form_invalid(self, form):
        attempted = self.request.POST.get("username", "").strip()[:64]
        record_event(
            user=None,
            action="login_failed",
            entity="auth.User",
            entity_id="anonymous",
            details={"username": attempted or "unknown"},
        )
        return super().form_invalid(form)


class AccountPasswordResetView(auth_views.PasswordResetView):
    def post(self, request, *args, **kwargs):
        blocked, retry_after = check_rate_limit(
            request,
            "password_reset",
            limit=settings.RATE_LIMIT_PASSWORD_RESET_MAX,
            window_seconds=settings.RATE_LIMIT_PASSWORD_RESET_WINDOW,
        )
        if blocked:
            return rate_limit_response(
                retry_after,
                _("Too many password reset attempts. Please wait before trying again."),
            )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        record_event(
            user=None,
            action="password_reset_requested",
            entity="auth.User",
            entity_id="anonymous",
            details={"channel": "email"},
        )
        return super().form_valid(form)


class AccountPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            invalidate_user_sessions(self.user)
            record_event(
                user=self.user,
                action="password_reset_completed",
                entity="auth.User",
                entity_id=self.user.pk,
                details={"method": "token"},
            )
        return response


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        blocked, retry_after = check_rate_limit(
            request,
            "register",
            limit=settings.RATE_LIMIT_REGISTER_MAX,
            window_seconds=settings.RATE_LIMIT_REGISTER_WINDOW,
        )
        if blocked:
            return rate_limit_response(
                retry_after,
                _("Too many registration attempts. Please wait before trying again."),
            )
        form = PublicRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Public registration creates an unprivileged account. Role assignment
                # is an explicit administrative action performed after account review.
                user = form.save()
                record_event(
                    user=user,
                    action="created",
                    entity="auth.User",
                    entity_id=user.pk,
                    details={"registration_type": "public"},
                )
            auth_login(request, user)
            messages.success(request, _("User account created."))
            return redirect("accounts:dashboard")
    else:
        form = PublicRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    can_view_products = request.user.has_perm("catalog.view_product")
    can_view_tasks = request.user.has_perm("operations.view_operationaltask")
    can_view_audit = request.user.has_perm("audit.view_auditlog")
    today = timezone.localdate()

    context = {
        "product_count": Product.objects.count() if can_view_products else None,
        "pending_count": None,
        "completed_count": None,
        "overdue_count": None,
        "recent_activity": AuditLog.objects.select_related("user")[:8] if can_view_audit else [],
        "can_view_products": can_view_products,
        "can_view_tasks": can_view_tasks,
    }
    if can_view_tasks:
        tasks = OperationalTask.objects.all()
        total_tasks = tasks.count()
        context["pending_count"] = tasks.exclude(
            status__in=[OperationalTask.Status.DONE, OperationalTask.Status.CANCELLED]
        ).count()
        context["completed_count"] = tasks.filter(status=OperationalTask.Status.DONE).count()
        context["overdue_count"] = (
            tasks.filter(due_date__lt=today)
            .exclude(status__in=[OperationalTask.Status.DONE, OperationalTask.Status.CANCELLED])
            .count()
        )
        labels = dict(OperationalTask.Status.choices)
        context["task_statuses"] = [
            {
                "status": item["status"],
                "label": labels[item["status"]],
                "total": item["total"],
                "percent": round((item["total"] / total_tasks) * 100) if total_tasks else 0,
            }
            for item in tasks.values("status").annotate(total=Count("id")).order_by("status")
        ]
    return render(request, "dashboard.html", context)


@staff_access_required
def user_list(request):
    users = get_user_model().objects.prefetch_related("groups").order_by("username")
    query = request.GET.get("q", "").strip()
    group_id = request.GET.get("group", "").strip()
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    if group_id.isdigit():
        users = users.filter(groups__id=int(group_id)).distinct()
    page = Paginator(users, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "accounts/user_list.html",
        {
            "users": page,
            "groups": Group.objects.order_by("name"),
            "query": query,
            "selected_group": group_id,
        },
    )


@staff_access_required
def user_create(request):
    if request.method == "POST":
        form = ManagedUserCreationForm(request.POST, acting_user=request.user)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                record_event(
                    user=request.user,
                    action="created",
                    entity="auth.User",
                    entity_id=user.pk,
                    details={
                        "is_staff": user.is_staff,
                        "groups": list(user.groups.values_list("name", flat=True)),
                    },
                )
            messages.success(request, _("User account created."))
            return redirect("accounts:user-list")
    else:
        form = ManagedUserCreationForm(acting_user=request.user)
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "heading": _("Add user"), "submit_label": _("Create account")},
    )


@staff_access_required
def user_update(request, pk):
    account = get_object_or_404(get_user_model(), pk=pk)
    if not can_manage_target_user(request.user, account):
        raise PermissionDenied
    if request.method == "POST":
        was_staff = account.is_staff
        old_groups = set(account.groups.values_list("name", flat=True))
        form = ManagedUserUpdateForm(request.POST, instance=account, acting_user=request.user)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save()
                new_groups = set(updated.groups.values_list("name", flat=True))
                should_revoke_sessions = bool(
                    not updated.is_active
                    or form.cleaned_data.get("new_password")
                    or was_staff != updated.is_staff
                    or old_groups != new_groups
                )
                invalidated = 0
                if should_revoke_sessions and (
                    updated.pk != request.user.pk or form.cleaned_data.get("new_password")
                ):
                    invalidated = invalidate_user_sessions(updated)
                record_event(
                    user=request.user,
                    action="updated",
                    entity="auth.User",
                    entity_id=updated.pk,
                    details={
                        "changed_fields": form.changed_data,
                        "sessions_invalidated": invalidated,
                    },
                )
            messages.success(request, _("User account updated."))
            return redirect("accounts:user-list")
    else:
        form = ManagedUserUpdateForm(instance=account, acting_user=request.user)
    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "heading": _("Edit user"),
            "submit_label": _("Save changes"),
            "account": account,
        },
    )


@staff_access_required
def setup_default_groups(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    with transaction.atomic():
        ensure_default_role_groups()
        record_event(
            user=request.user,
            action="configured",
            entity="auth.Group",
            entity_id="default-role-groups",
            details={"groups": sorted(DEFAULT_ROLE_GROUPS.keys())},
        )
    messages.success(request, _("Default permission groups configured."))
    return redirect("accounts:user-list")
