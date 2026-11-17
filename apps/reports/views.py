from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Product
from apps.inventory.models import StockItem
from apps.inventory.selectors import iter_stock_items_for_csv
from config.csv import build_csv_response
from config.pdf import build_pdf_response

from .forms import ReportFilterForm
from .selectors import (
    filter_tasks_for_report,
    summarize_collaborator_activity,
    summarize_inventory_metrics,
    summarize_task_counts,
)


def _build_summary_context(request, form, tasks) -> dict:
    counts, task_total = summarize_task_counts(tasks)
    can_view_stock = request.user.has_perm("inventory.view_stockitem")
    inventory_summary = summarize_inventory_metrics() if can_view_stock else None
    return {
        "form": form,
        "tasks": tasks[:100],
        "task_counts": counts,
        "task_total": task_total,
        "collaborator_metrics": summarize_collaborator_activity(tasks),
        "product_count": Product.objects.count(),
        "active_product_count": Product.objects.active().count(),
        "can_view_stock": can_view_stock,
        "inventory_summary": inventory_summary,
    }


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def summary(request):
    form = ReportFilterForm(request.GET)
    tasks = filter_tasks_for_report(form, has_query_params=bool(request.GET))
    return render(request, "reports/summary.html", _build_summary_context(request, form, tasks))


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def export_tasks_csv(request):
    form = ReportFilterForm(request.GET)
    tasks = filter_tasks_for_report(form, has_query_params=bool(request.GET))
    if not form.is_valid():
        return render(
            request,
            "reports/summary.html",
            {
                **_build_summary_context(request, form, tasks.none()),
                "tasks": [],
                "task_counts": [],
                "task_total": 0,
            },
            status=400,
        )

    headers = [
        _("Title"),
        _("Category"),
        _("Status"),
        _("Priority"),
        _("Assigned to"),
        _("Due date"),
        _("Product"),
    ]
    rows = (
        [
            task.title,
            task.get_category_display(),
            task.get_status_display(),
            task.get_priority_display(),
            task.assigned_to.get_username() if task.assigned_to else "",
            task.due_date or "",
            task.product.name if task.product else "",
        ]
        for task in tasks.iterator(chunk_size=200)
    )
    return build_csv_response("olokuti-task-report.csv", headers, rows)


@permission_required(["inventory.view_stockitem", "catalog.view_product"], raise_exception=True)
def export_inventory_csv(request):
    items = StockItem.objects.active().with_relations().order_by("product__name", "location__name")
    headers = [
        _("Product"),
        _("SKU"),
        _("Location"),
        _("Code"),
        _("Quantity"),
        _("Minimum stock"),
        _("Low stock"),
        _("Updated at"),
    ]
    return build_csv_response(
        "olokuti-inventory-report.csv", headers, iter_stock_items_for_csv(items)
    )


@permission_required(
    ["operations.view_operationaltask", "catalog.view_product"], raise_exception=True
)
def export_summary_pdf(request):
    form = ReportFilterForm(request.GET)
    tasks = filter_tasks_for_report(form, has_query_params=bool(request.GET))
    if not form.is_valid():
        return render(
            request,
            "reports/summary.html",
            {
                **_build_summary_context(request, form, tasks.none()),
                "tasks": [],
                "task_counts": [],
                "task_total": 0,
            },
            status=400,
        )

    ctx = _build_summary_context(request, form, tasks)
    lines = [
        f"Catalogue products: {ctx['product_count']} (Active: {ctx['active_product_count']})",
        f"Tasks in period: {ctx['task_total']}",
        "",
        "Task Summary by Status:",
    ]
    for _code, label, count in ctx["task_counts"]:
        lines.append(f"  * {label}: {count}")

    if ctx["collaborator_metrics"]:
        lines.extend(["", "Collaborator Activity:"])
        for row in ctx["collaborator_metrics"]:
            lines.append(
                f"  * {row['username']}: total={row['total']}, done={row['done']}, "
                f"open={row['open_count']}, overdue={row['overdue']}"
            )

    if ctx["inventory_summary"]:
        inv = ctx["inventory_summary"]
        lines.extend(
            [
                "",
                "Inventory Summary:",
                f"  * Active stock lines: {inv['item_count']} across {inv['location_count']} locations",
                f"  * Total units on hand: {inv['total_units']}",
                f"  * Low-stock alerts: {inv['low_stock_count']}",
            ]
        )

    lines.extend(["", "Recent Tasks (up to 40):"])
    for task in tasks[:40]:
        assignee = task.assigned_to.get_username() if task.assigned_to else "-"
        lines.append(
            f"  - [{task.get_status_display()}] {task.title} ({task.get_priority_display()}, {assignee})"
        )

    return build_pdf_response(
        "olokuti-summary-report.pdf",
        title="Olokuti Digital - Operational Summary Report",
        lines=lines,
    )
