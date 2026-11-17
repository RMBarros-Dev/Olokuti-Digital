import csv
from collections.abc import Iterable

from django.http import HttpResponse


def csv_safe(value) -> str:
    """Neutralize spreadsheet formula prefixes (=, +, -, @, tab, CR) in exported CSV cells."""
    text = str(value)
    if text[:1] in {"\t", "\r"} or text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def build_csv_response(
    filename: str, headers: Iterable[str], rows: Iterable[Iterable]
) -> HttpResponse:
    """Create a UTF-8 BOM CSV download response with formula-injection protection on all cells."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(list(headers))
    for row in rows:
        writer.writerow([csv_safe(val) for val in row])
    return response
