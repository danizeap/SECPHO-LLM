"""Render a structured Report into a .docx with clean, well-typeset styling.

Consumes the shared `layout.blocks(report)` so the .docx and the chat HTML are identical by
construction. Until the branded plantilla4.docx is supplied, this uses neutral programmatic
styles isolated here so the template swap is a one-liner later.
"""
from __future__ import annotations

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt, RGBColor

from . import layout

BRAND = RGBColor(0x00, 0x86, 0x8C)
DARK = RGBColor(0x1B, 0x1C, 0x20)
MUTED = RGBColor(0x5A, 0x5C, 0x63)


def _ensure_styles(doc) -> None:
    existing = {s.name for s in doc.styles}

    def mk(name, size, bold, color, space_before, space_after):
        st = doc.styles[name] if name in existing else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.bold = bold
        st.font.color.rgb = color
        st.paragraph_format.space_before = Pt(space_before)
        st.paragraph_format.space_after = Pt(space_after)

    mk("RG Title", 22, True, BRAND, 0, 14)
    mk("RG H1", 15, True, BRAND, 16, 6)
    mk("RG H2", 12, True, DARK, 10, 4)
    mk("RG Muted", 9.5, False, MUTED, 0, 8)


def _bullet(doc, text: str, level: int = 1) -> None:
    style = "List Bullet" if level == 1 else "List Bullet 2"
    try:
        doc.add_paragraph(text, style=style)
    except KeyError:
        doc.add_paragraph(("   • " if level > 1 else "• ") + text)


_STYLE = {"title": "RG Title", "sub": "RG Muted", "h1": "RG H1", "h2": "RG H2"}


def render(report):
    doc = Document()
    _ensure_styles(doc)
    for block in layout.blocks(report):
        kind = block[0]
        if kind in _STYLE:
            doc.add_paragraph(block[1], style=_STYLE[kind])
        elif kind == "p" or kind == "rationale":
            doc.add_paragraph(block[1])
        elif kind == "li":
            _bullet(doc, block[1], level=1)
        elif kind == "li2":
            _bullet(doc, block[1], level=2)
        elif kind == "itemhead":
            p = doc.add_paragraph()
            p.add_run(block[1]).bold = True
            if block[2]:
                p.add_run(block[2])
    return doc
