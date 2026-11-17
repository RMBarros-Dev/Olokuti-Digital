import re
import textwrap
from collections.abc import Iterable

from django.http import HttpResponse

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_ASCII_FALLBACKS = {
    "\u2014": "--",
    "\u2013": "-",
    "\u2026": "...",
    "\u20ac": "EUR",
    "\u20b9": "INR",
    "\u2022": "*",
}


def _pdf_encode(text: str) -> bytes:
    normalized = str(text)
    for src, target in _ASCII_FALLBACKS.items():
        normalized = normalized.replace(src, target)
    latin_bytes = normalized.encode("latin-1", "replace")
    escaped = bytearray()
    for byte in latin_bytes:
        if byte in (40, 41, 92):  # (, ), \
            escaped.append(92)
        escaped.append(byte)
    return bytes(escaped)


def build_pdf_document(*, title: str, lines: Iterable[str]) -> bytes:
    """Build a valid multi-page A4 PDF-1.4 binary document using pure Python."""
    wrapped_lines: list[str] = []
    for raw_line in lines:
        line = str(raw_line).strip()
        if not line:
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(
                textwrap.wrap(line, width=88, break_long_words=True, break_on_hyphens=False) or [""]
            )

    if not wrapped_lines:
        wrapped_lines = [""]

    lines_per_page = 44
    pages = [
        wrapped_lines[i : i + lines_per_page] for i in range(0, len(wrapped_lines), lines_per_page)
    ]

    # Object allocation:
    # 1: Catalog, 2: Pages, 3: Font (Helvetica), then (4 + 2*idx): Page, (5 + 2*idx): Content
    objects: list[bytes] = []
    page_refs: list[bytes] = []
    font_obj_num = 3

    for page_index, page_lines in enumerate(pages):
        page_num = 4 + (page_index * 2)
        content_num = page_num + 1
        page_refs.append(f"{page_num} 0 R".encode("ascii"))

        stream_cmds = [b"BT"]
        if page_index == 0:
            stream_cmds.append(b"/F1 14 Tf 50 792 Td (" + _pdf_encode(title) + b") Tj")
            stream_cmds.append(b"/F1 10 Tf 0 -24 Td")
        else:
            stream_cmds.append(b"/F1 10 Tf 50 792 Td")

        for row in page_lines:
            stream_cmds.append(b"(" + _pdf_encode(row) + b") Tj 0 -15 Td")

        footer = f"Page {page_index + 1} of {len(pages)}"
        stream_cmds.append(b"ET BT /F1 8 Tf 50 36 Td (" + _pdf_encode(footer) + b") Tj ET")
        stream_data = b"\n".join(stream_cmds)

        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/Contents {content_num} 0 R >>"
        ).encode("ascii")
        content_obj = (
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
            + stream_data
            + b"\nendstream"
        )
        objects.append(page_obj)
        objects.append(content_obj)

    catalog_obj = b"<< /Type /Catalog /Pages 2 0 R >>"
    pages_obj = (
        b"<< /Type /Pages /Kids ["
        + b" ".join(page_refs)
        + f"] /Count {len(pages)} >>".encode("ascii")
    )
    font_obj = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"

    all_objects = [catalog_obj, pages_obj, font_obj, *objects]

    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    current_offset = len(chunks[0])

    for index, obj_body in enumerate(all_objects, start=1):
        offsets.append(current_offset)
        entry = f"{index} 0 obj\n".encode("ascii") + obj_body + b"\nendobj\n"
        chunks.append(entry)
        current_offset += len(entry)

    xref_offset = current_offset
    xref_lines = [f"xref\n0 {len(all_objects) + 1}\n0000000000 65535 f \n".encode("ascii")]
    for offset in offsets[1:]:
        xref_lines.append(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer\n<< /Size {len(all_objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return b"".join([*chunks, *xref_lines, trailer])


def build_pdf_response(filename: str, *, title: str, lines: Iterable[str]) -> HttpResponse:
    """Wrap generated PDF bytes in an HttpResponse with safe download headers."""
    safe_name = _SAFE_FILENAME_RE.sub("-", filename).strip("-") or "report.pdf"
    if not safe_name.lower().endswith(".pdf"):
        safe_name = f"{safe_name}.pdf"
    payload = build_pdf_document(title=title, lines=lines)
    response = HttpResponse(payload, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return response
