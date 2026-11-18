#!/usr/bin/env python
"""Compile gettext .po files into .mo files without external tools.

Render's Python image has no gettext binaries, and Windows developers often
do not have them either. This script implements the small subset of the PO
format used by this project (msgid, msgid_plural, msgstr[n], msgctxt) and
writes a valid binary .mo catalog.

Usage:
    python scripts/compile_po.py
"""

from __future__ import annotations

import ast
import struct
import sys
from pathlib import Path

HEADER = struct.pack("<Iiiiiii", 0x950412DE, 0, 0, 0, 0, 0, 0)


def unquote(value: str) -> str | None:
    value = value.strip()
    if not value.startswith('"'):
        return None
    return ast.literal_eval(value)


def parse_po(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in text.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    messages: dict[str, str] = {}

    for block in blocks:
        # Ignore obsolete (#~) and fuzzy entries.
        if any(line.startswith("#~") for line in block):
            continue
        if any(
            line.startswith("#,") and "fuzzy" in line for line in block
        ):
            continue

        msgctxt = None
        msgid = None
        plural = None
        forms: dict[int, str] = {}
        field = None
        index = None

        for raw in block:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("msgctxt "):
                field, index = "ctxt", None
                msgctxt = unquote(line[len("msgctxt ") :]) or ""
            elif line.startswith("msgid_plural "):
                field, index = "plural", None
                plural = unquote(line[len("msgid_plural ") :]) or ""
            elif line.startswith("msgid "):
                field, index = "id", None
                msgid = unquote(line[len("msgid ") :]) or ""
            elif line.startswith("msgstr["):
                end = line.index("]")
                index = int(line[len("msgstr[") : end])
                field = "form"
                forms[index] = unquote(line[end + 1 :].strip()) or ""
            elif line.startswith("msgstr "):
                field, index = "str", None
                forms[0] = unquote(line[len("msgstr ") :]) or ""
            elif line.startswith('"'):
                value = unquote(line)
                if value is None:
                    continue
                if field == "ctxt":
                    msgctxt = (msgctxt or "") + value
                elif field == "id":
                    msgid = (msgid or "") + value
                elif field == "plural":
                    plural = (plural or "") + value
                elif field == "form" and index is not None:
                    forms[index] = forms.get(index, "") + value
                elif field == "str":
                    forms[0] = forms.get(0, "") + value

        if msgid is None:
            continue
        if msgid != "" and not any(forms.values()):
            continue

        key = f"{msgctxt}\x04{msgid}" if msgctxt else msgid

        if plural is not None:
            if not forms:
                continue
            ordered = [forms.get(i, "") for i in range(max(forms) + 1)]
            # GNU .mo stores plural entries with the key
            # "msgid\0msgid_plural" and the joined translations as the value.
            messages[f"{key}\x00{plural}"] = "\x00".join(ordered)
        else:
            messages[key] = forms.get(0, "")

    return messages


def write_mo(messages: dict[str, str], path: Path) -> None:
    keys = sorted(messages, key=lambda item: item.encode("utf-8"))

    ids = b""
    strings = b""
    offsets: list[tuple[int, int, int, int]] = []

    for key in keys:
        key_bytes = key.encode("utf-8")
        value_bytes = messages[key].encode("utf-8")
        offsets.append(
            (len(ids), len(key_bytes), len(strings), len(value_bytes))
        )
        ids += key_bytes + b"\x00"
        strings += value_bytes + b"\x00"

    count = len(keys)
    key_table_offset = 7 * 4
    value_table_offset = key_table_offset + 8 * count
    key_strings_offset = value_table_offset + 8 * count
    value_strings_offset = key_strings_offset + len(ids)

    key_offsets = b""
    value_offsets = b""
    for key_offset, key_length, value_offset, value_length in offsets:
        # Offsets in the MO format are absolute positions in the file.
        key_offsets += struct.pack(
            "<ii", key_length, key_strings_offset + key_offset
        )
        value_offsets += struct.pack(
            "<ii", value_length, value_strings_offset + value_offset
        )

    header = struct.pack(
        "<Iiiiiii",
        0x950412DE,
        0,
        count,
        key_table_offset,
        value_table_offset,
        0,
        0,
    )

    path.write_bytes(header + key_offsets + value_offsets + ids + strings)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    locale_dir = root / "locale"

    files = sorted(locale_dir.glob("*/LC_MESSAGES/*.po"))
    if not files:
        print("No .po files found.")
        return 1

    for po_path in files:
        messages = parse_po(po_path)
        mo_path = po_path.with_suffix(".mo")
        write_mo(messages, mo_path)
        print(f"Compiled {po_path.relative_to(root)} -> {mo_path.name} "
              f"({len(messages)} messages)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
