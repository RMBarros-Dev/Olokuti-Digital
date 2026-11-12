from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.audit.services import record_event

from .forms import OperationalTaskForm
from .models import OperationalTask


@permission_required("operations.view_operationaltask", raise_exception=True)
def task_list(request):
    tasks = OperationalTask.objects.select_related("assigned_to", "product")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    scope = request.GET.get("scope", "")
    query = request.GET.get("q", "").strip()
    if status in OperationalTask.Status.values:
        tasks = tasks.filter(status=status)
    if priority in OperationalTask.Priority.values:
        tasks = tasks.filter(priority=priority)
    if scope == "mine":
        tasks = tasks.filter(assigned_to=request.user)
    elif scope == "overdue":
        tasks = tasks.filter(due_date__lt=timezone.localdate()).exclude(
            status__in=[OperationalTask.Status.DONE, OperationalTask.Status.CANCELLED]
        )
    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))
    page = Paginator(tasks, 15).get_page(request.GET.get("page"))
    template = (
        "operations/_task_table.html"
        if request.headers.get("HX-Request") == "true"
        else "operations/task_list.html"
    )
    return render(
        request,
        template,
        {
            "tasks": page,
            "status_choices": OperationalTask.Status.choices,
            "priority_choices": OperationalTask.Priority.choices,
            "selected_status": status,
            "selected_priority": priority,
            "selected_scope": scope,
            "query": query,
        },
    )


@permission_required("operations.add_operationaltask", raise_exception=True)
def task_create(request):
    if request.method == "POST":
        form = OperationalTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.updated_by = request.user
            task.save()
            record_event(
                user=request.user,
                action="created",
                entity="operations.OperationalTask",
                entity_id=task.pk,
            )
            messages.success(request, _("Task created."))
            return redirect("operations:task-list")
    else:
        form = OperationalTaskForm()
    return render(request, "operations/task_form.html", {"form": form, "heading": _("Add task")})


@permission_required("operations.change_operationaltask", raise_exception=True)
def task_update(request, pk):
    task = get_object_or_404(OperationalTask, pk=pk)
    previous_status = task.status
    if request.method == "POST":
        form = OperationalTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.updated_by = request.user
            task.save()
            action = "status_changed" if previous_status != task.status else "updated"
            record_event(
                user=request.user,
                action=action,
                entity="operations.OperationalTask",
                entity_id=task.pk,
            )
            messages.success(request, _("Task changes saved."))
            return redirect("operations:task-list")
    else:
        form = OperationalTaskForm(instance=task)
    return render(
        request,
        "operations/task_form.html",
        {"form": form, "heading": _("Edit task"), "task": task},
    )


@permission_required("operations.change_operationaltask", raise_exception=True)
def task_quick_status(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    task = get_object_or_404(OperationalTask, pk=pk)
    new_status = request.POST.get("status", "")
    if new_status in OperationalTask.Status.values and new_status != task.status:
        task.status = new_status
        task.updated_by = request.user
        task.save(update_fields=["status", "updated_by", "updated_at"])
        record_event(
            user=request.user,
            action="status_changed",
            entity="operations.OperationalTask",
            entity_id=task.pk,
        )
        messages.success(request, _("Task status updated."))
    return redirect("operations:task-list")


@permission_required("operations.delete_operationaltask", raise_exception=True)
def task_delete(request, pk):
    task = get_object_or_404(OperationalTask, pk=pk)
    if request.method == "POST":
        task_id = task.pk
        task.delete()
        record_event(
            user=request.user,
            action="deleted",
            entity="operations.OperationalTask",
            entity_id=task_id,
        )
        messages.success(request, _("Task deleted."))
        return redirect("operations:task-list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(request, "operations/task_confirm_delete.html", {"task": task})
