"""report_engine — deterministic, branded .docx report generation for SECPHO.

Structure and data are deterministic (the matchmaker math decides); the LLM only
polishes prose in fixed slots (later phases). Phase 1 covers the índice plus
sections 1-3 (Introducción, Resumen/Ficha, Contactos Recomendados).
"""
from .report import generate, build_person_report, build_company_report  # noqa: F401

__all__ = ["generate", "build_person_report", "build_company_report"]
