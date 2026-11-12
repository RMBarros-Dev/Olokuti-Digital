import csv

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from apps.audit.services import record_event

from .forms import CategoryForm, ProductForm, ProductTranslationForm
from .models import Category, Product, ProductTranslation


def _filtered_products(request):
    products = Product.objects.select_related("category", "created_by").prefetch_related(
        "translations"
    )
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(origin__icontains=query)
            | Q(sustainability_info__icontains=query)
            | Q(translations__name__icontains=query)
            | Q(translations__description__icontains=query)
        ).distinct()
    if category_id.isdigit():
        products = products.filter(category_id=category_id)
    return products, query, category_id


def _csv_safe(value):
    text = str(value)
    if text[:1] in {"\t", "\r"} or text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


@permission_required("catalog.view_product", raise_exception=True)
def product_list(request):
    products, query, category_id = _filtered_products(request)
    page = Paginator(products, 12).get_page(request.GET.get("page"))
    active_lang = get_language()
    for item in page.object_list:
        item.active_translation = item.get_translation(active_lang)
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
        },
    )


@permission_required("catalog.view_product", raise_exception=True)
def export_products_csv(request):
    products, _query, _category_id = _filtered_products(request)
    active_lang = get_language()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="olokuti-catalogue.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(
        [
            _("Name"),
            _("Translated name"),
            _("Category"),
            _("Origin"),
            _("Description"),
            _("Sustainability information"),
        ]
    )
    for product in products:
        trans = product.get_translation(active_lang)
        row = [
            product.name,
            trans.name if trans else "",
            product.category.name if product.category else "",
            product.origin,
            trans.description if (trans and trans.description) else product.description,
            trans.sustainability_info
            if (trans and trans.sustainability_info)
            else product.sustainability_info,
        ]
        writer.writerow([_csv_safe(val) for val in row])
    return response


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
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "translations": product.translations.all(),
            "tasks": tasks,
            "can_view_tasks": can_view_tasks,
        },
    )


@permission_required("catalog.add_product", raise_exception=True)
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            record_event(
                user=request.user, action="created", entity="catalog.Product", entity_id=product.pk
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
            form.save()
            record_event(
                user=request.user, action="updated", entity="catalog.Product", entity_id=product.pk
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
        translation = form.save(commit=False)
        translation.product = product
        translation.save()
        record_event(
            user=request.user,
            action="updated" if existing else "created",
            entity="catalog.ProductTranslation",
            entity_id=translation.pk,
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
    translation.delete()
    record_event(
        user=request.user,
        action="deleted",
        entity="catalog.ProductTranslation",
        entity_id=translation_id,
    )
    messages.success(request, _("Product translation removed."))
    return redirect("catalog:product-update", pk=product.pk)


@permission_required("catalog.delete_product", raise_exception=True)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product_id = product.pk
        product.delete()
        record_event(
            user=request.user, action="deleted", entity="catalog.Product", entity_id=product_id
        )
        messages.success(request, _("Product deleted."))
        return redirect("catalog:product-list")
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])
    return render(request, "catalog/product_confirm_delete.html", {"product": product})


@permission_required("catalog.view_product", raise_exception=True)
def category_list(request):
    if request.method == "POST":
        if not request.user.has_perm("catalog.add_product"):
            return HttpResponseNotAllowed(["GET"])
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            record_event(
                user=request.user,
                action="created",
                entity="catalog.Category",
                entity_id=category.pk,
            )
            messages.success(request, _("Category created."))
            return redirect("catalog:category-list")
    else:
        form = CategoryForm()
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(
        request,
        "catalog/category_list.html",
        {"categories": categories, "form": form},
    )


@permission_required("catalog.delete_product", raise_exception=True)
def category_delete(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    category = get_object_or_404(Category, pk=pk)
    try:
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
