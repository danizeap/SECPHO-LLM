"""report_engine — deterministic, branded .docx report generation for SECPHO.

Structure and data are deterministic (the matchmaker math decides); the LLM only
polishes prose in fixed slots (later phases). Phase 1 covers the índice plus
sections 1-3 (Introducción, Resumen/Ficha, Contactos Recomendados).
"""
from .report import (  # noqa: F401
    generate,
    generate_bytes,
    generate_html,
    render_html_of,
    render_docx_bytes_of,
    build_person_report,
    build_company_report,
)

__all__ = [
    "generate",
    "generate_bytes",
    "generate_html",
    "render_html_of",
    "render_docx_bytes_of",
    "build_person_report",
    "build_company_report",
]
