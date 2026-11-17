import array
import re
import struct
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

_PO_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
_PO_ESCAPE_RE = re.compile(r'\\([ntr"\\])')


def _unescape_po_fragment(raw: str) -> str:
    return _PO_ESCAPE_RE.sub(lambda match: _PO_ESCAPES[match.group(1)], raw)


def parse_po_messages(po_path: Path) -> dict[bytes, bytes]:
    """Parse msgid/msgstr (and optional plural) entries from a UTF-8 gettext .po file."""
    messages: dict[bytes, bytes] = {}
    section: str | None = None
    msgid_parts: list[str] = []
    plural_parts: list[str] = []
    msgstr_map: dict[int, list[str]] = {}
    current_idx = 0
    fuzzy = False

    def flush():
        nonlocal msgid_parts, plural_parts, msgstr_map, fuzzy
        if section is not None and (msgid_parts or msgstr_map):
            key = "".join(msgid_parts)
            if plural_parts:
                key = f"{key}\x00{''.join(plural_parts)}"
                val = "\x00".join("".join(msgstr_map[i]) for i in sorted(msgstr_map))
            else:
                val = "".join(msgstr_map.get(0, []))
            if not fuzzy and val:
                messages[key.encode("utf-8")] = val.encode("utf-8")
        msgid_parts = []
        plural_parts = []
        msgstr_map = {}
        fuzzy = False

    for raw_line in po_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            flush()
            section = None
            continue
        if line.startswith("#"):
            if line.startswith("#,") and "fuzzy" in line:
                fuzzy = True
            continue
        if line.startswith("msgid "):
            flush()
            section = "id"
            msgid_parts.append(_unescape_po_fragment(line[6:].strip()[1:-1]))
        elif line.startswith("msgid_plural "):
            section = "plural"
            plural_parts.append(_unescape_po_fragment(line[13:].strip()[1:-1]))
        elif line.startswith("msgstr["):
            section = "str"
            bracket_end = line.index("]")
            current_idx = int(line[7:bracket_end])
            msgstr_map.setdefault(current_idx, []).append(
                _unescape_po_fragment(line[bracket_end + 1 :].strip()[1:-1])
            )
        elif line.startswith("msgstr "):
            section = "str"
            current_idx = 0
            msgstr_map.setdefault(0, []).append(_unescape_po_fragment(line[7:].strip()[1:-1]))
        elif line.startswith('"') and line.endswith('"'):
            fragment = _unescape_po_fragment(line[1:-1])
            if section == "id":
                msgid_parts.append(fragment)
            elif section == "plural":
                plural_parts.append(fragment)
            elif section == "str":
                msgstr_map.setdefault(current_idx, []).append(fragment)

    flush()
    return messages


def compile_po_to_mo(po_path: Path, mo_path: Path) -> None:
    """Compile a single .po catalogue to binary GNU gettext .mo format."""
    catalog = parse_po_messages(po_path)
    sorted_keys = sorted(catalog.keys())

    offsets: list[tuple[int, int, int, int]] = []
    ids_blob = b""
    strs_blob = b""

    for key in sorted_keys:
        val = catalog[key]
        offsets.append((len(ids_blob), len(key), len(strs_blob), len(val)))
        ids_blob += key + b"\x00"
        strs_blob += val + b"\x00"

    header_size = 7 * 4
    table_size = len(sorted_keys) * 8
    ids_start = header_size + table_size * 2
    strs_start = ids_start + len(ids_blob)

    key_offsets: list[int] = []
    val_offsets: list[int] = []
    for id_off, id_len, str_off, str_len in offsets:
        key_offsets.extend([id_len, ids_start + id_off])
        val_offsets.extend([str_len, strs_start + str_off])

    output = struct.pack(
        "<Iiiiiii",
        0x950412DE,
        0,
        len(sorted_keys),
        header_size,
        header_size + table_size,
        0,
        0,
    )
    output += array.array("i", key_offsets).tobytes()
    output += array.array("i", val_offsets).tobytes()
    output += ids_blob + strs_blob
    mo_path.write_bytes(output)


def compile_all_locale_directories(locale_paths=None) -> int:
    """Compile every locale/*/LC_MESSAGES/django.po catalogue using pure Python."""
    roots = locale_paths or getattr(settings, "LOCALE_PATHS", [])
    compiled = 0
    for root in roots:
        for po_path in Path(root).glob("*/LC_MESSAGES/django.po"):
            compile_po_to_mo(po_path, po_path.with_suffix(".mo"))
            compiled += 1
    return compiled


class Command(BaseCommand):
    help = "Compile the checked-in gettext catalogues without changing their source files."

    def handle(self, *args, **options):
        try:
            call_command("compilemessages", verbosity=options["verbosity"])
        except CommandError:
            compiled = compile_all_locale_directories()
            self.stdout.write(
                self.style.SUCCESS(f"Compiled {compiled} locale catalogues via Python fallback.")
            )
