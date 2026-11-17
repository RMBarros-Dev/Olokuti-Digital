from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.audit.services import record_event

from .forms import OperationalTaskForm, TaskCommentForm
from .models import OperationalTask
from .selectors import filter_operational_tasks, get_task_history


@permission_required("operations.view_operationaltask", raise_exception=True)
def task_list(request):
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    category = request.GET.get("category", "")
    scope = request.GET.get("scope", "")
    query = request.GET.get("q", "").strip()
    tasks = filter_operational_tasks(
        request.user,
        status=status,
        priority=priority,
        category=category,
        scope=scope,
        query=query,
    )
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
            "category_choices": OperationalTask.Category.choices,
            "selected_status": status,
            "selected_priority": priority,
            "selected_category": category,
            "selected_scope": scope,
            "query": query,
        },
    )


def _user_can_comment(user) -> bool:
    return user.has_perm("operations.add_taskcomment") or user.has_perm(
        "operations.change_operationaltask"
    )


def _task_detail_context(request, task: OperationalTask, comment_form=None) -> dict:
    can_comment = _user_can_comment(request.user)
    return {
        "task": task,
        "comments": task.comments.select_related("author"),
        "history": get_task_history(task) if request.user.has_perm("audit.view_auditlog") else [],
        "comment_form": comment_form or TaskCommentForm(),
        "can_comment": can_comment,
    }


@permission_required("operations.view_operationaltask", raise_exception=True)
def task_detail(request, pk):
    task = get_object_or_404(
        OperationalTask.objects.select_related(
            "assigned_to", "product", "created_by", "updated_by"
        ),
        pk=pk,
    )
    return render(request, "operations/task_detail.html", _task_detail_context(request, task))


@require_POST
@permission_required("operations.view_operationaltask", raise_exception=True)
def task_comment_create(request, pk):
    if not _user_can_comment(request.user):
        raise PermissionDenied
    task = get_object_or_404(
        OperationalTask.objects.select_related(
            "assigned_to", "product", "created_by", "updated_by"
        ),
        pk=pk,
    )
    form = TaskCommentForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            record_event(
                user=request.user,
                action="comment_added",
                entity="operations.OperationalTask",
                entity_id=task.pk,
                details={"comment_id": str(comment.pk)},
            )
        messages.success(request, _("Comment added."))
        return redirect("operations:task-detail", pk=task.pk)
    return render(
        request,
        "operations/task_detail.html",
        _task_detail_context(request, task, comment_form=form),
    )


@permission_required("operations.add_operationaltask", raise_exception=True)
def task_create(request):
    if request.method == "POST":
        form = OperationalTaskForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                task = form.save(commit=False)
                task.created_by = request.user
                task.updated_by = request.user
                task.save()
                record_event(
                    user=request.user,
                    action="created",
                    entity="operations.OperationalTask",
                    entity_id=task.pk,
                    details={"status": task.status, "priority": task.priority},
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
            with transaction.atomic():
                task = form.save(commit=False)
                task.updated_by = request.user
                task.save()
                action = "status_changed" if previous_status != task.status else "updated"
                record_event(
                    user=request.user,
                    action=action,
                    entity="operations.OperationalTask",
                    entity_id=task.pk,
                    details={
                        "changed_fields": form.changed_data,
                        "previous_status": previous_status,
                        "new_status": task.status,
                    },
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
    previous_status = task.status
    new_status = request.POST.get("status", "")
    if new_status in OperationalTask.Status.values and new_status != previous_status:
        with transaction.atomic():
            task.status = new_status
            task.updated_by = request.user
            task.save(update_fields=["status", "updated_by", "updated_at"])
            record_event(
                user=request.user,
                action="status_changed",
                entity="operations.OperationalTask",
                entity_id=task.pk,
                details={"previous_status": previous_status, "new_status": new_status},
            )
        messages.success(request, _("Task status updated."))
    return redirect("operations:task-list")


@permission_required("operations.delete_operationaltask", raise_exception=True)
def task_delete(request, pk):
    task = get_object_or_404(OperationalTask, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
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
