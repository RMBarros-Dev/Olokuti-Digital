from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from apps.audit.services import record_event
from config.csv import build_csv_response

from .forms import CategoryForm, ProductForm, ProductTranslationForm
from .models import Category, Product, ProductTranslation
from .selectors import (
    attach_active_translations,
    filter_products,
    get_product_history,
    iter_products_for_csv,
)


@permission_required("catalog.view_product", raise_exception=True)
def product_list(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()
    products = filter_products(query=query, category_id=category_id, status=status)
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    attach_active_translations(page.object_list, get_language())
    template = (
        "catalog/_product_table.html"
        if request.headers.get("HX-Request") == "true"
        else "catalog/product_list.html"
    )
    return render(
        request,
        template,
        {
            "products": page,
            "categories": Category.objects.all(),
            "query": query,
            "selected_category": category_id,
            "selected_status": status,
        },
    )


@permission_required("catalog.view_product", raise_exception=True)
def export_products_csv(request):
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()
    headers = [
        _("Name"),
        _("SKU"),
        _("Barcode"),
        _("Status"),
        _("Price"),
        _("Currency"),
        _("Translated name"),
        _("Category"),
        _("Origin"),
        _("Description"),
        _("Sustainability information"),
    ]
    rows = iter_products_for_csv(
        query=query,
        category_id=category_id,
        status=status,
        language_code=get_language(),
    )
    return build_csv_response("olokuti-catalogue.csv", headers, rows)


@permission_required("catalog.view_product", raise_exception=True)
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "created_by").prefetch_related(
            "translations", "operational_tasks__assigned_to"
        ),
        pk=pk,
    )
    product.active_translation = product.get_translation(get_language())
    can_view_tasks = request.user.has_perm("operations.view_operationaltask")
    tasks = product.operational_tasks.all() if can_view_tasks else []
    history = get_product_history(product) if request.user.has_perm("audit.view_auditlog") else []
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "translations": product.translations.all(),
            "tasks": tasks,
            "can_view_tasks": can_view_tasks,
            "history": history,
        },
    )


@permission_required("catalog.add_product", raise_exception=True)
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                product = form.save(commit=False)
                product.created_by = request.user
                product.save()
                record_event(
                    user=request.user,
                    action="created",
                    entity="catalog.Product",
                    entity_id=product.pk,
                    details={"category_id": product.category_id},
                )
            messages.success(request, _("Product added to the catalogue."))
            return redirect("catalog:product-list")
    else:
        form = ProductForm()
    return render(request, "catalog/product_form.html", {"form": form, "heading": _("Add product")})


@permission_required("catalog.change_product", raise_exception=True)
def product_update(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related("translations"), pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                record_event(
                    user=request.user,
                    action="updated",
                    entity="catalog.Product",
                    entity_id=product.pk,
                    details={"changed_fields": form.changed_data},
                )
            messages.success(request, _("Product changes saved."))
            return redirect("catalog:product-list")
    else:
        form = ProductForm(instance=product)
    translation_form = ProductTranslationForm(initial={"locale": get_language() or "pt-br"})
    return render(
        request,
        "catalog/product_form.html",
        {
            "form": form,
            "heading": _("Edit product"),
            "product": product,
            "translations": product.translations.all(),
            "translation_form": translation_form,
        },
    )


@permission_required("catalog.change_product", raise_exception=True)
def product_translation_save(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    locale_value = request.POST.get("locale", "").strip()
    existing = ProductTranslation.objects.filter(product=product, locale=locale_value).first()
    form = ProductTranslationForm(request.POST, instance=existing)
    if form.is_valid():
        with transaction.atomic():
            translation = form.save(commit=False)
            translation.product = product
            translation.save()
            record_event(
                user=request.user,
                action="updated" if existing else "created",
                entity="catalog.ProductTranslation",
                entity_id=translation.pk,
                details={"product_id": str(product.pk), "locale": translation.locale},
            )
        messages.success(request, _("Product translation saved."))
        return redirect("catalog:product-update", pk=product.pk)
    return render(
        request,
        "catalog/product_form.html",
        {
            "form": ProductForm(instance=product),
            "heading": _("Edit product"),
            "product": product,
            "translations": product.translations.all(),
            "translation_form": form,
        },
    )


@permission_required("catalog.change_product", raise_exception=True)
def product_translation_delete(request, pk, translation_id):
    product = get_object_or_404(Product, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    translation = get_object_or_404(ProductTranslation, pk=translation_id, product=product)
    with transaction.atomic():
        locale = translation.locale
        translation.delete()
        record_event(
            user=request.user,
            action="deleted",
            entity="catalog.ProductTranslation",
            entity_id=translation_id,
            details={"product_id": str(product.pk), "locale": locale},
        )
    messages.success(request, _("Product translation removed."))
    return redirect("catalog:product-update", pk=product.pk)


@require_POST
@permission_required("catalog.change_product", raise_exception=True)
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    with transaction.atomic():
        previous = product.is_active
        product.is_active = not previous
        product.save(update_fields=["is_active", "updated_at"])
        record_event(
            user=request.user,
            action="status_changed",
            entity="catalog.Product",
            entity_id=product.pk,
            details={"previous_active": previous, "is_active": product.is_active},
        )
    messages.success(
        request,
        _("Product reactivated.") if product.is_active else _("Product archived (inactive)."),
    )
    return redirect("catalog:product-detail", pk=product.pk)


@permission_required("catalog.delete_product", raise_exception=True)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            product_id = product.pk
            product.delete()
            record_event(
                user=request.user,
                action="deleted",
                entity="catalog.Product",
                entity_id=product_id,
            )
        messages.success(request, _("Product deleted."))
        return redirect("catalog:product-list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(request, "catalog/product_confirm_delete.html", {"product": product})


@require_GET
@permission_required("catalog.view_category", raise_exception=True)
def category_list(request):
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "catalog/category_list.html", {"categories": categories})


@require_POST
@permission_required("catalog.add_category", raise_exception=True)
def category_create(request):
    form = CategoryForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            category = form.save()
            record_event(
                user=request.user,
                action="created",
                entity="catalog.Category",
                entity_id=category.pk,
            )
        messages.success(request, _("Category created."))
        return redirect("catalog:category-list")
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(
        request,
        "catalog/category_list.html",
        {"categories": categories, "form": form},
        status=400,
    )


@permission_required("catalog.change_category", raise_exception=True)
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                form.save()
                record_event(
                    user=request.user,
                    action="updated",
                    entity="catalog.Category",
                    entity_id=category.pk,
                    details={"changed_fields": form.changed_data},
                )
            messages.success(request, _("Category updated."))
            return redirect("catalog:category-list")
    elif request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(
        request,
        "catalog/category_form.html",
        {"category": category, "form": form},
        status=400 if request.method == "POST" else 200,
    )


@require_POST
@permission_required("catalog.delete_category", raise_exception=True)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    try:
        with transaction.atomic():
            category_id = category.pk
            category.delete()
            record_event(
                user=request.user,
                action="deleted",
                entity="catalog.Category",
                entity_id=category_id,
            )
        messages.success(request, _("Category deleted."))
    except ProtectedError:
        messages.error(
            request,
            _("Cannot delete this category while products are still assigned to it."),
        )
    return redirect("catalog:category-list")
