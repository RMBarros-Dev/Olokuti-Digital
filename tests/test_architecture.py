from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import Product, ProductTranslation
from apps.catalog.selectors import iter_products_for_csv
from apps.operations.models import OperationalTask
from config.csv import build_csv_response, csv_safe


def test_csv_safe_neutralizes_formula_injection():
    assert csv_safe("=SUM(A1:A2)") == "'=SUM(A1:A2)"
    assert csv_safe("  +cmd") == "'  +cmd"
    assert csv_safe("-100") == "'-100"
    assert csv_safe("@user") == "'@user"
    assert csv_safe("\tcell") == "'\tcell"
    assert csv_safe("Normal text") == "Normal text"


def test_build_csv_response_sets_utf8_bom_and_sanitizes_cells():
    resp = build_csv_response("demo.csv", ["Name", "Formula"], [["Safe", "=1+1"]])
    assert resp["Content-Type"] == "text/csv; charset=utf-8"
    assert 'filename="demo.csv"' in resp["Content-Disposition"]
    decoded = resp.content.decode("utf-8-sig")
    assert "Name,Formula" in decoded
    assert "Safe,'=1+1" in decoded


@pytest.mark.django_db
def test_operational_task_queryset_open_and_overdue_filters():
    today = timezone.localdate()
    overdue = OperationalTask.objects.create(
        title="Past due", status=OperationalTask.Status.TODO, due_date=today - timedelta(days=2)
    )
    future = OperationalTask.objects.create(
        title="Upcoming",
        status=OperationalTask.Status.IN_PROGRESS,
        due_date=today + timedelta(days=3),
    )
    done = OperationalTask.objects.create(
        title="Completed past",
        status=OperationalTask.Status.DONE,
        due_date=today - timedelta(days=5),
    )

    assert set(OperationalTask.objects.open()) == {overdue, future}
    assert list(OperationalTask.objects.overdue()) == [overdue]
    assert list(OperationalTask.objects.overdue(reference_date=today + timedelta(days=5))) == [
        overdue,
        future,
    ]
    assert done not in OperationalTask.objects.open()


@pytest.mark.django_db
def test_iter_products_for_csv_streams_localized_rows():
    product = Product.objects.create(
        name="Olive Soap",
        sku="SKU-SOAP-01",
        barcode="8400001112223",
        price="12.50",
        currency="EUR",
        description="Orig desc",
    )
    ProductTranslation.objects.create(
        product=product,
        locale="pt-br",
        name="Sabonete de Oliva",
        description="Desc PT-BR",
        sustainability_info="Sem palma",
    )

    rows = list(iter_products_for_csv(query="Olive", language_code="pt-br"))
    assert len(rows) == 1
    assert rows[0][0] == "Olive Soap"
    assert rows[0][1] == "SKU-SOAP-01"
    assert rows[0][2] == "8400001112223"
    assert rows[0][3] == "active"
    assert str(rows[0][4]) == "12.50"
    assert rows[0][5] == "EUR"
    assert rows[0][6] == "Sabonete de Oliva"
    assert rows[0][9] == "Desc PT-BR"
    assert rows[0][10] == "Sem palma"
