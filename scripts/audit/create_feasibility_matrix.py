from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def main():
    rows = [
        {
            "signal": "Profile similarity",
            "status": "Feasible",
            "confidence": "High",
            "main_sources": "members_normalized.csv | socios_normalized.csv",
            "usable_fields": "profile_text, technology_parents, technology_subs, sector_parents, sector_subs, ambitos, activity_summary",
            "limitations": "Strongest for socios with rich member profiles. Company-only profiles are weaker.",
            "phase_1_decision": "Use in Phase 1",
        },
        {
            "signal": "Technology and sector overlap",
            "status": "Feasible",
            "confidence": "High",
            "main_sources": "members_normalized.csv | events_normalized.csv | retos_normalized.csv",
            "usable_fields": "technology_parents, technology_subs, sector_parents, sector_subs, technologies, sectors",
            "limitations": "Socios without member profiles may lack rich technology/sector detail.",
            "phase_1_decision": "Use in Phase 1",
        },
        {
            "signal": "Complementarity",
            "status": "Feasible",
            "confidence": "Medium-High",
            "main_sources": "members_normalized.csv | socios_normalized.csv",
            "usable_fields": "technology fields, sector fields, ambitos, value_chain, needs_general, needs_specific, activity_summary",
            "limitations": "Needs careful scoring rules. Complementarity is not the same as similarity.",
            "phase_1_decision": "Use in Phase 1 with transparent rules",
        },
        {
            "signal": "Supply-demand matching through retos",
            "status": "Feasible",
            "confidence": "Medium",
            "main_sources": "retos_normalized.csv | members_normalized.csv | socios_normalized.csv",
            "usable_fields": "title, sectors, issuing_entities, applying_entities, closing_date, reto_text",
            "limitations": "Only 11 of 174 retos have full descriptions. Issuing entity is missing in around half of retos.",
            "phase_1_decision": "Use in Phase 1, but do not rely only on description text",
        },
        {
            "signal": "Event metadata matching",
            "status": "Feasible",
            "confidence": "High",
            "main_sources": "events_normalized.csv | members_normalized.csv",
            "usable_fields": "event_date, title, typology, technologies, ambitos, sectors, location_type, province",
            "limitations": "This supports event recommendation, not co-attendance relationship scoring.",
            "phase_1_decision": "Use in Phase 1",
        },
        {
            "signal": "Co-attendance graph",
            "status": "Blocked",
            "confidence": "Low",
            "main_sources": "Missing event attendance forms or attendance endpoint",
            "usable_fields": "Not available yet",
            "limitations": "actosagenda has event metadata and counts, but not attendee identities.",
            "phase_1_decision": "Do not use until attendance data is provided",
        },
        {
            "signal": "Subscriber engagement",
            "status": "Partially feasible",
            "confidence": "Medium",
            "main_sources": "suscriptores_normalized.csv",
            "usable_fields": "open_rate, click_rate, emails_count, lists, company",
            "limitations": "Useful for engagement/churn context, but not strong for technical matching.",
            "phase_1_decision": "Use as supporting signal, not primary recommender signal",
        },
        {
            "signal": "Contact availability",
            "status": "Feasible",
            "confidence": "High",
            "main_sources": "socios_normalized.csv | datoscontacto.csv | suscriptores_normalized.csv",
            "usable_fields": "main_contact_email, Contacto_Email, subscriber email",
            "limitations": "Contact info should not drive match quality. It only supports actionability.",
            "phase_1_decision": "Use for operational handoff and report generation",
        },
        {
            "signal": "Official socio readiness",
            "status": "Feasible",
            "confidence": "High",
            "main_sources": "official_socios_readiness.csv | official_socios_coverage.csv",
            "usable_fields": "readiness_score, readiness_label, member_profile_count, subscriber_contact_count, retos counts",
            "limitations": "This is not a recommendation score. It is only data readiness.",
            "phase_1_decision": "Use to choose pilot socios and confidence levels",
        },
        {
            "signal": "Churn or retention risk",
            "status": "Partially feasible",
            "confidence": "Low-Medium",
            "main_sources": "suscriptores_normalized.csv | members_normalized.csv | events_normalized.csv",
            "usable_fields": "open_rate, click_rate, emails_count, Engag. In SECPHO",
            "limitations": "No renewal/churn labels and no attendee-level event history yet.",
            "phase_1_decision": "Do not build churn model yet. Keep for later Phase 3.",
        },
    ]

    output = pd.DataFrame(rows)

    output_path = PROCESSED_DIR / "signal_feasibility_matrix.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved signal feasibility matrix to: {output_path}")
    print(f"Rows: {len(output)}")

    print("\nStatus distribution:")
    print(output["status"].value_counts().to_string())

    phase_1_usable = output[
        output["phase_1_decision"].str.startswith("Use", na=False)
    ]

    print("\nPhase 1 usable signals:")
    print(
        phase_1_usable[
            ["signal", "status", "confidence"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()