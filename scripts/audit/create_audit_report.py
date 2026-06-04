from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")
DOCS_DIR = Path("docs")


def read_count(path):
    df = pd.read_csv(path)
    return len(df), len(df.columns)


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    endpoint_files = {
        "members": "members.csv",
        "suscriptores": "suscriptores.csv",
        "datosnegocio": "datosnegocio.csv",
        "datoscontacto": "datoscontacto.csv",
        "actosagenda": "actosagenda.csv",
        "retos": "retos.csv",
    }

    normalized_files = {
        "members_normalized": "members_normalized.csv",
        "socios_normalized": "socios_normalized.csv",
        "retos_normalized": "retos_normalized.csv",
        "events_normalized": "events_normalized.csv",
        "suscriptores_normalized": "suscriptores_normalized.csv",
        "entity_universe": "entity_universe.csv",
        "official_socios_coverage": "official_socios_coverage.csv",
        "official_socios_readiness": "official_socios_readiness.csv",
        "signal_feasibility_matrix": "signal_feasibility_matrix.csv",
        "column_profile": "column_profile.csv",
    }

    readiness = pd.read_csv(PROCESSED_DIR / "official_socios_readiness.csv")
    feasibility = pd.read_csv(PROCESSED_DIR / "signal_feasibility_matrix.csv")
    coverage = pd.read_csv(PROCESSED_DIR / "official_socios_coverage.csv")

    lines = []

    lines.append("# SECPHO 01_Data_Audit Summary")
    lines.append("")
    lines.append("## Module")
    lines.append("01_Data_Audit")
    lines.append("")
    lines.append("## Session goal")
    lines.append(
        "Audit the available SECPHO data sources, confirm which endpoints work, normalize the core tables, "
        "check joins between official socios and people/contact data, and define which recommendation signals "
        "are feasible for Phase 1."
    )
    lines.append("")
    lines.append("## Scope decision")
    lines.append(
        "The Phase 1 recommendation universe is limited to official socios/companies from `datosnegocio`."
    )
    lines.append("")
    lines.append("- Official socios are the canonical recommendation universe.")
    lines.append("- Wider entities from contacts/subscribers are enrichment only, not primary recommendation targets.")
    lines.append("- `datosnegocio` currently contains 192 official socios.")
    lines.append("")
    lines.append("## Endpoint audit")
    lines.append("")
    lines.append("| Endpoint | Rows | Columns |")
    lines.append("|---|---:|---:|")

    for name, filename in endpoint_files.items():
        rows, cols = read_count(PROCESSED_DIR / filename)
        lines.append(f"| `{name}` | {rows} | {cols} |")

    lines.append("")
    lines.append("All six core endpoints were successfully fetched and saved locally as raw JSON plus processed CSV.")
    lines.append("")
    lines.append("## Normalized outputs created")
    lines.append("")
    lines.append("| File | Rows | Columns |")
    lines.append("|---|---:|---:|")

    for name, filename in normalized_files.items():
        rows, cols = read_count(PROCESSED_DIR / filename)
        lines.append(f"| `{filename}` | {rows} | {cols} |")

    lines.append("")
    lines.append("## Official socios coverage")
    lines.append("")
    lines.append(f"- Official socios: {len(coverage)}")
    lines.append(f"- With member profiles: {int(coverage['has_member_profiles'].sum())}")
    lines.append(f"- With contact records: {int(coverage['has_contact_records'].sum())}")
    lines.append(f"- With subscriber contacts: {int(coverage['has_subscriber_contacts'].sum())}")
    lines.append(f"- With retos signal: {int(coverage['has_retos_signal'].sum())}")
    lines.append("")
    lines.append("## Official socios readiness")
    lines.append("")
    lines.append("| Readiness label | Count |")
    lines.append("|---|---:|")

    for label, count in readiness["readiness_label"].value_counts().items():
        lines.append(f"| {label} | {count} |")

    lines.append("")
    lines.append(f"Average readiness score: {readiness['readiness_score'].mean():.2f} / 100")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("")
    lines.append(
        "- High-readiness socios are the best pilot candidates because they have richer connected data."
    )
    lines.append(
        "- Medium-readiness socios can be included with lower confidence or simpler explanations."
    )
    lines.append(
        "- Low-readiness socios likely need enrichment before strong recommendations can be made."
    )
    lines.append("")
    lines.append("## Signal feasibility matrix")
    lines.append("")
    lines.append("| Signal | Status | Confidence | Phase 1 decision |")
    lines.append("|---|---|---|---|")

    for _, row in feasibility.iterrows():
        lines.append(
            f"| {row['signal']} | {row['status']} | {row['confidence']} | {row['phase_1_decision']} |"
        )

    lines.append("")
    lines.append("## Key findings")
    lines.append("")
    lines.append("- The endpoint data is strong enough to continue into `02_Recommendation_Engine`.")
    lines.append("- `members.Tecnologías json` and `members.Sectores json` are 100% parseable and should be preferred over plain text technology/sector columns.")
    lines.append("- `datosnegocio.Socio` matches `datoscontacto.Entidad` for all 192 official socios after normalization.")
    lines.append("- All official socios have contact records.")
    lines.append("- 180 of 192 official socios have subscriber contacts.")
    lines.append("- 108 of 192 official socios have rich member/person profiles.")
    lines.append("- Retos are usable, but descriptions are sparse: only a small subset has full description text.")
    lines.append("- Event metadata is strong, but attendee identities are not available yet.")
    lines.append("")
    lines.append("## Blockers")
    lines.append("")
    lines.append("### Co-attendance graph")
    lines.append("")
    lines.append(
        "Blocked until SECPHO provides attendee-level event data. The current `actosagenda` endpoint includes event metadata and aggregate counts, "
        "but not attendee names, emails, or companies."
    )
    lines.append("")
    lines.append("Needed fields:")
    lines.append("")
    lines.append("- Event title or event ID")
    lines.append("- Attendee name")
    lines.append("- Attendee surname")
    lines.append("- Email")
    lines.append("- Company/entity")
    lines.append("- Role, if available")
    lines.append("- Event date, if available")
    lines.append("")
    lines.append("Once received, this data should be processed in Module 01 first, creating `attendance_normalized.csv`, before being used in Module 02.")
    lines.append("")
    lines.append("## Files touched or created")
    lines.append("")
    lines.append("Main audit scripts are stored in:")
    lines.append("")
    lines.append("`scripts/audit/`")
    lines.append("")
    lines.append("Main generated data files are stored in:")
    lines.append("")
    lines.append("`data/processed/`")
    lines.append("")
    lines.append("Legacy prototype script is stored in:")
    lines.append("")
    lines.append("`legacy/old_code.py`")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(
        "Proceed to `02_Recommendation_Engine` using the normalized tables created in this module. "
        "Start with official socios only, prioritize high-readiness socios, and build scoring logic where math decides and the LLM explains."
    )
    lines.append("")

    output_path = DOCS_DIR / "01_data_audit_summary.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Saved audit report to: {output_path}")


if __name__ == "__main__":
    main()