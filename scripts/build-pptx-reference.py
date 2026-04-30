#!/usr/bin/env python3
"""Generate the pptx reference-doc Pandoc uses as a template for the
PowerPoint export of each lecture.

We start from **Pandoc's own default reference.pptx** (extracted via
`quarto pandoc --print-default-data-file=reference.pptx`). Pandoc's
pptx writer relies on the precise placeholder structure of the default
file's slide masters and layouts. A reference doc generated from
scratch via python-pptx looks superficially similar (same layout
names) but writes will silently produce zero-slide outputs — which is
why we layer brand customisation on top of Pandoc's known-good doc
rather than building from a python-pptx Presentation().

This script:

  1. Calls `quarto pandoc --print-default-data-file=reference.pptx` to
     dump Pandoc's bundled default into a temp file.
  2. Opens it via python-pptx and rewrites every <a:latin> typeface
     attribute on the slide master and layouts to Cambria (the closest
     widely-installed serif to Computer Modern).
  3. Walks `<a:rPr>` and `<a:defRPr>` elements on the master to force
     dark-ink (#111111) text colour.
  4. Saves the result to assets/styles/pptx-reference.pptx.

Run once locally; the resulting binary is committed.

Re-run on:
  - Pandoc / Quarto upgrade (their default reference may have changed).
  - Brand font / colour change.

    python scripts/build-pptx-reference.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from pptx import Presentation
from lxml import etree


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "assets" / "styles" / "pptx-reference.pptx"

SERIF = "Cambria"
INK_HEX = "111111"

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def fetch_pandoc_default() -> Path:
    """Run `quarto pandoc --print-default-data-file=reference.pptx` and
    capture its binary output to a temp file."""
    tmp = Path(tempfile.mkstemp(suffix=".pptx")[1])
    with tmp.open("wb") as fh:
        result = subprocess.run(
            ["quarto", "pandoc", "--print-default-data-file=reference.pptx"],
            stdout=fh,
            check=True,
        )
    if not tmp.exists() or tmp.stat().st_size < 5_000:
        raise RuntimeError(f"Pandoc default reference doc looks too small at {tmp}")
    return tmp


def set_typeface(element, font_name: str) -> int:
    """Rewrite every <a:latin typeface="..."/> inside `element`.
    Returns the number of nodes touched."""
    n = 0
    for latin in element.findall(f".//{{{A_NS}}}latin"):
        latin.set("typeface", font_name)
        n += 1
    return n


def force_text_colour(element, hex_rgb: str) -> int:
    """Replace any solidFill on text run-property elements with the
    given colour. Leaves shape-level fills alone."""
    n = 0
    for tag in ("rPr", "defRPr", "endParaRPr"):
        for rpr in element.findall(f".//{{{A_NS}}}{tag}"):
            for child in list(rpr):
                local = etree.QName(child).localname
                if local in {"solidFill", "gradFill", "pattFill", "blipFill"}:
                    rpr.remove(child)
            solid = etree.SubElement(rpr, f"{{{A_NS}}}solidFill")
            clr = etree.SubElement(solid, f"{{{A_NS}}}srgbClr")
            clr.set("val", hex_rgb)
            n += 1
    return n


def main() -> int:
    try:
        pandoc_default = fetch_pandoc_default()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.stderr.write(f"ERROR: could not extract Pandoc default reference: {exc}\n")
        return 2

    prs = Presentation(str(pandoc_default))

    # Brand the slide master and every layout.
    targets = [prs.slide_master.element] + [lo.element for lo in prs.slide_layouts]
    typeface_changes = 0
    colour_changes = 0
    for el in targets:
        typeface_changes += set_typeface(el, SERIF)
        colour_changes += force_text_colour(el, INK_HEX)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(
        f"Wrote {OUTPUT.relative_to(REPO_ROOT)} "
        f"(typeface rewrites: {typeface_changes}, colour rewrites: {colour_changes})"
    )

    try:
        pandoc_default.unlink(missing_ok=True)
    except PermissionError:
        # Windows occasionally holds a lock on the temp file briefly; the
        # OS will clean it up on the next temp sweep.
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
