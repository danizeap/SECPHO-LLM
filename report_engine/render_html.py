"""Render a structured Report into an HTML fragment for the in-chat preview.

Consumes the SAME `layout.blocks(report)` as `render_docx`, so what the curator sees in chat
is identical (structure, wording, order, numbers) to the downloaded .docx. All text is
HTML-escaped — the report carries member data, never markup.
"""
from __future__ import annotations

import html

from . import layout

_TAG = {
    "title": ("<h2 class=\"rep-title\">", "</h2>"),
    "sub": ("<div class=\"rep-sub\">", "</div>"),
    "h1": ("<h3 class=\"rep-h1\">", "</h3>"),
    "h2": ("<h4 class=\"rep-h2\">", "</h4>"),
    "p": ("<p>", "</p>"),
    "rationale": ("<p class=\"rep-why\">", "</p>"),
}


def render(report) -> str:
    parts: list[str] = ["<div class=\"rep\">"]
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    for block in layout.blocks(report):
        kind = block[0]
        if kind in ("li", "li2"):
            if not in_list:
                parts.append("<ul class=\"rep-list\">")
                in_list = True
            cls = " class=\"lvl2\"" if kind == "li2" else ""
            parts.append(f"<li{cls}>{html.escape(block[1])}</li>")
            continue
        close_list()
        if kind == "itemhead":
            rest = html.escape(block[2]) if block[2] else ""
            parts.append(f"<p class=\"rep-item\"><strong>{html.escape(block[1])}</strong>{rest}</p>")
        elif kind in _TAG:
            open_t, close_t = _TAG[kind]
            parts.append(f"{open_t}{html.escape(block[1])}{close_t}")
    close_list()
    parts.append("</div>")
    return "".join(parts)
