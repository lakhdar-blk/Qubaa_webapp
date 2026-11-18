#!/usr/bin/env python
"""Check that every interface string has an Arabic translation.

Scans templates and Python modules for gettext strings, then compares them with
the msgids present in locale/ar/LC_MESSAGES/django.po.

Usage:
    python scripts/check_po.py          # report missing / unused strings
    python scripts/check_po.py --list   # also print the missing msgids

Exit code is 1 when translations are missing, which makes it usable in CI.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PO_PATH = ROOT / "locale" / "ar" / "LC_MESSAGES" / "django.po"

TRANSLATE_RE = re.compile(
    r"""\{%\s*translate\s+(?P<quote>["'])(?P<text>(?:\\.|(?!\1).)*)\1"""
)
BLOCK_RE = re.compile(
    r"\{%\s*blocktranslate(?P<args>[^%]*)%\}(?P<body>.*?)\{%\s*endblocktranslate\s*%\}",
    re.S,
)
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
WS_RE = re.compile(r"\s+")
PY_FUNCS = {"_", "gettext", "gettext_lazy", "gettext_noop"}


def unescape(value: str) -> str:
    return value.replace("\\'", "'").replace('\\"', '"')


def template_strings(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    found: set[str] = set()

    for match in TRANSLATE_RE.finditer(text):
        found.add(unescape(match.group("text")))

    for match in BLOCK_RE.finditer(text):
        body = match.group("body")
        # Plural blocks: only the singular form is the msgid.
        body = body.split("{% plural %}")[0]
        body = VAR_RE.sub(lambda m: f"%({m.group(1)})s", body)
        body = WS_RE.sub(" ", body).strip()
        if body:
            found.add(body)

    return found


def python_strings(path: Path) -> set[str]:
    found: set[str] = set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return found

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name not in PY_FUNCS:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            found.add(arg.value)
    return found


def po_msgids(path: Path) -> set[str]:
    ids: set[str] = set()
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            current_block.append(raw)
        elif current_block:
            blocks.append(current_block)
            current_block = []
    if current_block:
        blocks.append(current_block)

    for index, block in enumerate(blocks):
        # The first block is the catalog header (empty msgid).
        if index == 0 and any(line.strip() == 'msgid ""' for line in block):
            continue

        msgid: str | None = None
        collecting = False

        for raw in block:
            line = raw.strip()
            if line.startswith("#"):
                continue
            if line.startswith("msgid "):
                value = line[len("msgid ") :]
                msgid = ast.literal_eval(value) if value.startswith('"') else ""
                collecting = True
            elif line.startswith('"') and collecting and msgid is not None:
                msgid += ast.literal_eval(line)
            elif line.startswith(("msgstr", "msgctxt", "msgid_plural")):
                collecting = False

        if msgid:
            ids.add(msgid)

    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print missing msgids.")
    args = parser.parse_args()

    found: set[str] = set()
    for path in (ROOT / "templates").rglob("*.html"):
        found |= template_strings(path)
    for app in ("announcements", "config", "dashboard"):
        for path in (ROOT / app).rglob("*.py"):
            if "migrations" in path.parts:
                continue
            found |= python_strings(path)

    translated = po_msgids(PO_PATH)
    missing = sorted(found - translated)
    unused = sorted(translated - found - {""})

    print(f"Strings in code : {len(found)}")
    print(f"Strings in PO   : {len(translated)}")
    print(f"Missing         : {len(missing)}")
    print(f"Unused in PO    : {len(unused)}")

    if missing and args.list:
        print("\nMissing translations:")
        for item in missing:
            print(f"  {item!r}")

    if unused and args.list:
        print("\nUnused entries (can be removed):")
        for item in unused:
            print(f"  {item!r}")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
