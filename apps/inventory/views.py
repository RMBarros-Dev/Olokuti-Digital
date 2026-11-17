from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from apps.audit.services import record_event
from config.csv import build_csv_response

from .forms import StockItemThresholdForm, StockLocationForm, StockMovementForm
from .models import StockItem, StockLocation, StockMovement
from .selectors import (
    filter_stock_items,
    filter_stock_movements,
    get_active_locations,
    iter_stock_items_for_csv,
)


@permission_required("inventory.view_stockitem", raise_exception=True)
def stock_list(request):
    query = request.GET.get("q", "").strip()
    location_id = request.GET.get("location", "").strip()
    low_stock_only = request.GET.get("low_stock") == "1"

    items_qs = filter_stock_items(
        query=query,
        location_id=location_id,
        low_stock_only=low_stock_only,
    )
    paginator = Paginator(items_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "stock_items": page_obj,
        "locations": StockLocation.objects.order_by("name"),
        "query": query,
        "selected_location": location_id,
        "low_stock_only": low_stock_only,
        "low_stock_count": StockItem.objects.active().low_stock().count(),
    }
    if request.headers.get("HX-Request"):
        return render(request, "inventory/_stock_table.html", context)
    return render(request, "inventory/stock_list.html", context)


@permission_required("inventory.view_stockitem", raise_exception=True)
def stock_export_csv(request):
    query = request.GET.get("q", "").strip()
    location_id = request.GET.get("location", "").strip()
    low_stock_only = request.GET.get("low_stock") == "1"

    items_qs = filter_stock_items(
        query=query,
        location_id=location_id,
        low_stock_only=low_stock_only,
    )
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
    return build_csv_response("olokuti-inventory.csv", headers, iter_stock_items_for_csv(items_qs))


@permission_required("inventory.view_stockmovement", raise_exception=True)
def movement_list(request):
    query = request.GET.get("q", "").strip()
    location_id = request.GET.get("location", "").strip()
    movement_type = request.GET.get("movement_type", "").strip()

    movements_qs = filter_stock_movements(
        query=query,
        location_id=location_id,
        movement_type=movement_type,
    )
    paginator = Paginator(movements_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "movements": page_obj,
        "locations": StockLocation.objects.order_by("name"),
        "movement_types": StockMovement.MovementType.choices,
        "query": query,
        "selected_location": location_id,
        "selected_type": movement_type,
    }
    if request.headers.get("HX-Request"):
        return render(request, "inventory/_movement_table.html", context)
    return render(request, "inventory/movement_list.html", context)


@permission_required("inventory.add_stockmovement", raise_exception=True)
def movement_create(request):
    initial = {}
    if request.GET.get("product"):
        initial["product"] = request.GET.get("product")
    if request.GET.get("location"):
        initial["location"] = request.GET.get("location")

    if request.method == "POST":
        form = StockMovementForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                movement = form.save()
            except ValidationError:
                pass
            else:
                messages.success(
                    request,
                    _("Stock updated: %(product)s at %(location)s now has %(qty)s units.")
                    % {
                        "product": movement.stock_item.product.name,
                        "location": movement.stock_item.location.code,
                        "qty": movement.balance_after,
                    },
                )
                return redirect("inventory:stock-list")
    else:
        form = StockMovementForm(initial=initial, user=request.user)

    return render(
        request,
        "inventory/movement_form.html",
        {
            "form": form,
            "heading": _("Record stock movement"),
            "has_active_locations": get_active_locations().exists(),
        },
    )


@permission_required("inventory.change_stockitem", raise_exception=True)
def stock_item_threshold_update(request, pk):
    stock_item = get_object_or_404(
        StockItem.objects.with_relations(),
        pk=pk,
    )
    if request.method == "POST":
        form = StockItemThresholdForm(request.POST, instance=stock_item)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save()
                record_event(
                    user=request.user,
                    action="threshold_updated",
                    entity="inventory.StockItem",
                    entity_id=updated.pk,
                    details={"minimum_stock": updated.minimum_stock},
                )
            messages.success(request, _("Minimum stock threshold updated."))
            return redirect("inventory:stock-list")
    else:
        form = StockItemThresholdForm(instance=stock_item)

    return render(
        request,
        "inventory/threshold_form.html",
        {
            "form": form,
            "stock_item": stock_item,
            "heading": _("Edit stock threshold"),
        },
    )


@permission_required("inventory.view_stocklocation", raise_exception=True)
def location_list(request):
    locations = StockLocation.objects.order_by("name")
    return render(request, "inventory/location_list.html", {"locations": locations})


@permission_required("inventory.add_stocklocation", raise_exception=True)
def location_create(request):
    if request.method == "POST":
        form = StockLocationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                location = form.save()
                record_event(
                    user=request.user,
                    action="created",
                    entity="inventory.StockLocation",
                    entity_id=location.pk,
                )
            messages.success(request, _("Stock location created."))
            return redirect("inventory:location-list")
    else:
        form = StockLocationForm()
    return render(
        request,
        "inventory/location_form.html",
        {"form": form, "heading": _("New stock location")},
    )


@permission_required("inventory.change_stocklocation", raise_exception=True)
def location_update(request, pk):
    location = get_object_or_404(StockLocation, pk=pk)
    if request.method == "POST":
        form = StockLocationForm(request.POST, instance=location)
        if form.is_valid():
            with transaction.atomic():
                updated = form.save()
                record_event(
                    user=request.user,
                    action="updated",
                    entity="inventory.StockLocation",
                    entity_id=updated.pk,
                )
            messages.success(request, _("Stock location updated."))
            return redirect("inventory:location-list")
    else:
        form = StockLocationForm(instance=location)
    return render(
        request,
        "inventory/location_form.html",
        {"form": form, "location": location, "heading": _("Edit stock location")},
    )
