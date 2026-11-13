from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.audit.models import AuditLog
from apps.catalog.models import Product
from apps.operations.models import OperationalTask

from .forms import ManagedUserCreationForm, ManagedUserUpdateForm, PublicRegistrationForm

DEFAULT_ROLE_GROUPS = {
    "Catalogue Team": [
        "view_product",
        "add_product",
        "change_product",
        "delete_product",
        "view_category",
        "add_category",
        "change_category",
        "delete_category",
    ],
    "Operations Team": [
        "view_operationaltask",
        "add_operationaltask",
        "change_operationaltask",
        "delete_operationaltask",
        "view_product",
    ],
    "Auditors & Managers": [
        "view_product",
        "add_product",
        "change_product",
        "delete_product",
        "view_operationaltask",
        "add_operationaltask",
        "change_operationaltask",
        "delete_operationaltask",
        "view_auditlog",
    ],
}


def ensure_default_role_groups():
    for group_name, codenames in DEFAULT_ROLE_GROUPS.items():
        group, _created = Group.objects.get_or_create(name=group_name)
        perms = Permission.objects.filter(codename__in=codenames)
        # Add defaults without wiping permissions an administrator customized.
        group.permissions.add(*perms)


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = PublicRegistrationForm(request.POST)
        if form.is_valid():
            ensure_default_role_groups()
            user = form.save()
            default_groups = Group.objects.filter(
                name__in=["Catalogue Team", "Operations Team"]
            )
            user.groups.add(*default_groups)
            AuditLog.objects.create(
                user=user,
                action="created",
                entity="auth.User",
                entity_id=str(user.pk),
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


@staff_member_required
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
    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
            "groups": Group.objects.order_by("name"),
            "query": query,
            "selected_group": group_id,
        },
    )


@staff_member_required
def user_create(request):
    if request.method == "POST":
        form = ManagedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="created",
                entity="auth.User",
                entity_id=str(user.pk),
            )
            messages.success(request, _("User account created."))
            return redirect("accounts:user-list")
    else:
        form = ManagedUserCreationForm()
    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "heading": _("Add user"), "submit_label": _("Create account")},
    )


@staff_member_required
def user_update(request, pk):
    account = get_object_or_404(get_user_model(), pk=pk)
    if request.method == "POST":
        form = ManagedUserUpdateForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action="updated",
                entity="auth.User",
                entity_id=str(account.pk),
            )
            messages.success(request, _("User account updated."))
            return redirect("accounts:user-list")
    else:
        form = ManagedUserUpdateForm(instance=account)
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


@staff_member_required
def setup_default_groups(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    ensure_default_role_groups()
    AuditLog.objects.create(
        user=request.user,
        action="configured",
        entity="auth.Group",
        entity_id="default-role-groups",
    )
    messages.success(request, _("Default permission groups configured."))
    return redirect("accounts:user-list")
