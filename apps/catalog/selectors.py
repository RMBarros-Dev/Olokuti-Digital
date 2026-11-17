from django.db.models import Q

from apps.audit.models import AuditLog

from .models import Product


def filter_products(*, query: str = "", category_id: str = "", status: str = ""):
    """Return prefetched products filtered by text, SKU/barcode, category, and active status."""
    products = Product.objects.select_related("category", "created_by").prefetch_related(
        "translations"
    )
    if status == "active":
        products = products.active()
    elif status == "inactive":
        products = products.inactive()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(sku__icontains=query)
            | Q(barcode__icontains=query)
            | Q(description__icontains=query)
            | Q(origin__icontains=query)
            | Q(sustainability_info__icontains=query)
            | Q(translations__name__icontains=query)
            | Q(translations__description__icontains=query)
        ).distinct()
    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    return products


def attach_active_translations(products, language_code: str | None) -> None:
    """Attach exact-locale translation objects onto each product without mutating originals."""
    for item in products:
        item.active_translation = item.get_translation(language_code)


def get_product_history(product: Product):
    """Fetch bounded audit events associated with this product."""
    return AuditLog.objects.select_related("user").filter(
        entity="catalog.Product", entity_id=str(product.pk)
    )[:20]


def iter_products_for_csv(
    *, query: str = "", category_id: str = "", status: str = "", language_code: str | None
):
    """Stream localized CSV rows in bounded chunks without materializing full queryset in RAM."""
    products = filter_products(query=query, category_id=category_id, status=status)
    for product in products.iterator(chunk_size=200):
        trans = product.get_translation(language_code)
        yield [
            product.name,
            product.sku,
            product.barcode,
            "active" if product.is_active else "inactive",
            product.price if product.price is not None else "",
            product.currency,
            trans.name if trans else "",
            product.category.name if product.category else "",
            product.origin,
            trans.description if (trans and trans.description) else product.description,
            trans.sustainability_info
            if (trans and trans.sustainability_info)
            else product.sustainability_info,
        ]
