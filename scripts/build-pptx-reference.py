#!/usr/bin/env python3
"""Generate a Pandoc-compatible pptx reference-doc that mirrors the
revealjs SMF Academic theme (white background, black text, serif font).

Pandoc's pptx writer reuses the slide masters / layouts of the reference
document; we therefore start from python-pptx's default presentation
(which already provides the standard layout names Pandoc looks up) and
rewrite the relevant style fields:

  - 16:9 slide size matching the revealjs deck (1280x720 ratio).
  - White slide background.
  - Cambria as the default font (Office-default serif; closest analog
    to Computer Modern that Office installs ship with — student
    machines are very unlikely to have CMU installed).
  - Black text colour on titles and body placeholders.

This script is run **once** locally; the resulting binary is committed
at assets/styles/pptx-reference.pptx and referenced from
courses/<id>/lectures/_metadata.yml under the pptx format.

Re-run it whenever the brand changes:

    python scripts/build-pptx-reference.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
from lxml import etree


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = REPO_ROOT / "assets" / "styles" / "pptx-reference.pptx"

SERIF = "Cambria"
INK = RGBColor(0x11, 0x11, 0x11)
PAPER = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0x5B, 0x7A, 0x8C)

A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
NSMAP = {"a": A_NS, "p": P_NS}


def set_typeface(element, font_name: str) -> None:
    """Rewrite every <a:latin typeface="..."/> inside `element` to the
    given font name, and add <a:latin> where missing on text run props
    that lack one."""
    for latin in element.findall(f".//{{{A_NS}}}latin"):
        latin.set("typeface", font_name)


def set_text_colour(element, hex_rgb: str) -> None:
    """Force every solid-fill <a:srgbClr> on text properties to a given
    hex value. Leaves shape fills alone."""
    for rpr in element.findall(f".//{{{A_NS}}}rPr") + element.findall(
        f".//{{{A_NS}}}defRPr"
    ):
        # Remove any existing fill children, replace with srgbClr.
        for child in list(rpr):
            tag = etree.QName(child).localname
            if tag in {"solidFill", "gradFill", "pattFill", "blipFill", "noFill"}:
                rpr.remove(child)
        solid = etree.SubElement(rpr, f"{{{A_NS}}}solidFill")
        clr = etree.SubElement(solid, f"{{{A_NS}}}srgbClr")
        clr.set("val", hex_rgb)


def set_paper_background(slide_master) -> None:
    """Replace whatever fill the master uses with a plain white solidFill."""
    bg_elements = slide_master.element.findall(f".//{{{P_NS}}}bg")
    for bg in bg_elements:
        # Strip existing children, install solid white.
        for child in list(bg):
            bg.remove(child)
        bg_pr = etree.SubElement(bg, f"{{{P_NS}}}bgPr")
        solid = etree.SubElement(bg_pr, f"{{{A_NS}}}solidFill")
        clr = etree.SubElement(solid, f"{{{A_NS}}}srgbClr")
        clr.set("val", "FFFFFF")
        etree.SubElement(bg_pr, f"{{{A_NS}}}effectLst")


def main() -> None:
    prs = Presentation()
    # 16:9 = 13.333" x 7.5"
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Whole-deck font + colour rewrite on the slide master and every layout.
    targets = [prs.slide_master.element] + [
        layout.element for layout in prs.slide_layouts
    ]
    for el in targets:
        set_typeface(el, SERIF)
        set_text_colour(el, "111111")

    set_paper_background(prs.slide_master)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
