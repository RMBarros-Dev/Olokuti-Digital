from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.audit.models import AuditLog
from apps.catalog.models import Product
from apps.inventory.models import StockItem
from apps.inventory.selectors import get_low_stock_items
from apps.operations.models import OperationalTask


def get_dashboard_context(user) -> dict:
    """Build permission-gated overview metrics and recent audit events for the dashboard."""
    can_view_products = user.has_perm("catalog.view_product")
    can_view_tasks = user.has_perm("operations.view_operationaltask")
    can_view_audit = user.has_perm("audit.view_auditlog")
    can_view_stock = user.has_perm("inventory.view_stockitem")

    context = {
        "product_count": Product.objects.count() if can_view_products else None,
        "pending_count": None,
        "completed_count": None,
        "overdue_count": None,
        "stock_item_count": StockItem.objects.active().count() if can_view_stock else None,
        "low_stock_count": (
            StockItem.objects.active().low_stock().count() if can_view_stock else None
        ),
        "low_stock_items": list(get_low_stock_items(limit=5)) if can_view_stock else [],
        "recent_activity": AuditLog.objects.select_related("user")[:8] if can_view_audit else [],
        "can_view_products": can_view_products,
        "can_view_tasks": can_view_tasks,
        "can_view_stock": can_view_stock,
    }
    if can_view_tasks:
        tasks = OperationalTask.objects.all()
        total_tasks = tasks.count()
        context["pending_count"] = tasks.open().count()
        context["completed_count"] = tasks.filter(status=OperationalTask.Status.DONE).count()
        context["overdue_count"] = tasks.overdue().count()
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
    return context


def filter_managed_users(*, query: str = "", group_id: str = ""):
    """Query active/inactive user accounts with optional text search and group filtering."""
    users = get_user_model().objects.prefetch_related("groups").order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    if group_id.isdigit():
        users = users.filter(groups__id=int(group_id)).distinct()
    return users
