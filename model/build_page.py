"""Rebuild index.html from the model grid and MODEL.md.

Two things are injected into the page, and both are GENERATED -- never hand-edited:

  1. the precomputed parameter grid (model/explorer_data.json) replaces the single
     `var EXPLORER=...;` line, and
  2. MODEL.md is rendered to HTML between the MODEL_TAB_START / MODEL_TAB_END markers,
     which is what the "Model details" tab shows.

Run this after changing either, or the published page silently goes stale.

    python model/build_page.py
"""
from __future__ import annotations
import os, sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GRID = os.path.join(HERE, "explorer_data.json")
MD = os.path.join(ROOT, "MODEL.md")
PAGE = os.path.join(ROOT, "index.html")
START, END = "<!--MODEL_TAB_START-->", "<!--MODEL_TAB_END-->"


def inject_grid(lines: list[str]) -> list[str]:
    hits = [i for i, l in enumerate(lines) if l.startswith("var EXPLORER=")]
    if len(hits) != 1:
        raise SystemExit(f"expected one 'var EXPLORER=' line, found {len(hits)}")
    grid = open(GRID, encoding="utf-8").read().strip()
    lines[hits[0]] = "var EXPLORER=" + grid + ";"
    return lines


def inject_model_tab(page: str) -> str:
    if START not in page or END not in page:
        raise SystemExit(f"markers {START} / {END} not found in {PAGE}")
    body = markdown.markdown(open(MD, encoding="utf-8").read(),
                             extensions=["tables", "fenced_code", "sane_lists"])
    body = body.replace('href="GLOSSARY.md"', 'href="GLOSSARY.md"')
    i, j = page.index(START) + len(START), page.index(END)
    return page[:i] + "\n" + body + "\n" + page[j:]


def main() -> int:
    page = open(PAGE, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in page else "\n"
    page = nl.join(inject_grid(page.split(nl)))
    page = inject_model_tab(page)
    open(PAGE, "w", encoding="utf-8", newline="").write(page)
    print(f"index.html rebuilt: {os.path.getsize(PAGE)/1e6:.2f} MB "
          f"(grid {os.path.getsize(GRID)/1e6:.2f} MB inlined, MODEL.md rendered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
