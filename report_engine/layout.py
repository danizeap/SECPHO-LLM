"""The single source of the report's structure and text.

`blocks(report)` turns a Report model into an ordered list of typed blocks. BOTH renderers
(`render_docx`, `render_html`) consume this same list, so the chat preview and the downloaded
.docx are identical by construction — they cannot drift in structure, wording, or order.

Block kinds (tuples):
  ("title", text)            document title
  ("sub", text)              muted subtitle line
  ("h1", text) / ("h2", text)  section / subsection heading
  ("p", text)                paragraph
  ("li", text) / ("li2", text)  bullet (level 1 / level 2)
  ("itemhead", bold, rest)   one line: `bold` rendered bold, `rest` appended normal
  ("rationale", text)        LLM "why this is a good match" paragraph (indented prose)
No LLM and no rendering here — pure structure.
"""
from __future__ import annotations


def _contact_evidence_bullets(c: dict) -> list:
    """Deterministic evidence bullets for one contact, in a fixed order."""
    out = []
    if c.get("shared_tech"):
        out.append(("li2", f"Tecnologías en común: {c['shared_tech']}"))
    if c.get("shared_sectors"):
        out.append(("li2", f"Sectores en común: {c['shared_sectors']}"))
    if c.get("shared_ambitos"):
        out.append(("li2", f"Ámbitos en común: {c['shared_ambitos']}"))
    if c.get("shared_university"):
        out.append(("li2", f"Universidad en común: {c['shared_university']}"))
    if c.get("shared_languages"):
        out.append(("li2", f"Idiomas en común: {c['shared_languages']}"))
    if c.get("shared_hobbies"):
        out.append(("li2", f"Aficiones en común: {c['shared_hobbies']}"))
    if c.get("shared_sports"):
        out.append(("li2", f"Deportes en común: {c['shared_sports']}"))
    return out


def blocks(report) -> list:
    b: list = []
    b.append(("title", report.title))
    b.append(("sub", "Informe interno de matchmaking y oportunidades · SECPHO"))

    b.append(("h1", "Índice"))
    for item in report.indice:
        b.append(("li", item))

    # 1. Introducción
    b.append(("h1", "1. Introducción"))
    for para in report.intro:
        b.append(("p", para))
    if report.exec_summary:
        b.append(("h2", "Resumen ejecutivo"))
        b.append(("p", report.exec_summary))

    # 2. Resumen de datos (Ficha)
    b.append(("h1", f"2. Resumen de datos de {report.subject_name}"))
    b.append(("h2", report.ficha_label))
    for label, value in report.ficha:
        b.append(("itemhead", f"{label}: ", value))

    # 3. Contactos recomendados
    b.append(("h1", "3. Contactos recomendados"))
    b.append((
        "p",
        "Contactos del ecosistema SECPHO sugeridos por afinidad de capacidades, "
        "tecnologías clave y áreas de interés. El orden lo determina el modelo de "
        "recomendación: la matemática decide, el informe lo explica.",
    ))
    if report.weighting_note:
        b.append(("p", report.weighting_note))
    if report.contacts:
        for i, c in enumerate(report.contacts, 1):
            extra = " — ".join(x for x in [c.get("socio"), c.get("role")] if x)
            b.append(("itemhead", f"{i}. {c['name']}", f" · {extra}" if extra else ""))
            if c.get("rationale"):
                b.append(("rationale", c["rationale"]))
            b.extend(_contact_evidence_bullets(c))
    else:
        b.append(("p", "No se han encontrado contactos recomendados para este perfil en este momento."))

    # 4. Eventos y actividades
    b.append(("h1", "4. Eventos y actividades"))
    b.append(("h2", "Próximos eventos recomendados"))
    if report.events_rec:
        for e in report.events_rec:
            b.append(("itemhead", e["title"], f"  ({e['score']:.0f}% de afinidad)"))
            b.append(("li2", f"Tecnologías: {e['technologies']}"))
            b.append(("li2", f"Sectores: {e['sectors']}"))
            b.append(("li2", f"Ámbitos: {e['ambitos']}"))
            b.append(("li2", f"Ubicación: {e['location']} · Fecha: {e['date']}"))
    else:
        b.append(("p", "No hay próximos eventos relevantes que recomendar en este momento."))

    b.append(("h2", "Histórico de participación en eventos SECPHO"))
    if report.attended:
        for a in report.attended:
            line = f"{a['title']} ({a['date']})"
            if a.get("attendees"):
                line += f" — {a['attendees']}"
            b.append(("li", line))
    else:
        b.append(("p", "Todavía no se registra asistencia a eventos organizados por SECPHO."))

    # 5. Retos tecnológicos
    b.append(("h1", "5. Retos tecnológicos"))
    b.append(("h2", "Retos tecnológicos activos recomendados"))
    if report.retos_rec:
        for r in report.retos_rec:
            head = f"{r['number']} — {r['title']}" if r.get("number") else r["title"]
            b.append(("itemhead", head, ""))
            if r.get("description"):
                b.append(("li2", r["description"]))
            b.append(("li2", f"Sector(es): {r['sectors']}"))
            b.append(("li2", f"Entidad emisora: {r['issuer']}"))
            b.append(("li2", f"Fecha de cierre: {r['closing']}"))
    else:
        b.append(("p", "No se han encontrado retos tecnológicos activos relevantes en este momento."))

    # Emitted/applied retos are entity-level: only when there is a socio/company.
    if report.entity_for_retos:
        b.append(("h2", f"Retos emitidos por {report.entity_for_retos} a través de SECPHO"))
        if report.retos_emit:
            for r in report.retos_emit:
                head = f"{r['number']} — {r['title']}" if r.get("number") else r["title"]
                b.append(("li", f"{head} (cierre: {r['closing']})"))
        else:
            b.append(("p", f"{report.entity_for_retos} no ha emitido retos tecnológicos a través de SECPHO."))

        b.append(("h2", f"Retos en los que {report.entity_for_retos} ha aplicado"))
        if report.retos_appl:
            for r in report.retos_appl:
                head = f"{r['number']} — {r['title']}" if r.get("number") else r["title"]
                b.append(("li", f"{head} — emisor: {r['issuer']} (cierre: {r['closing']})"))
        else:
            b.append(("p", f"{report.entity_for_retos} no consta como aplicante en retos tecnológicos."))

    return b
