import re
import html
import unicodedata
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def normalize_key(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def clean_value(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).strip()

    if text.lower() in {"nan", "none", "n/d", "no definido", "-"}:
        return ""

    return text


def add_entity(records, entity_name, source, extra=None):
    entity_name = clean_value(entity_name)
    entity_key = normalize_key(entity_name)

    if not entity_name or not entity_key:
        return

    row = {
        "entity_key": entity_key,
        "entity_name": entity_name,
        "source": source,
    }

    if extra:
        row.update(extra)

    records.append(row)


def main():
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")
    datoscontacto = pd.read_csv(PROCESSED_DIR / "datoscontacto.csv")
    suscriptores = pd.read_csv(PROCESSED_DIR / "suscriptores_normalized.csv")
    members = pd.read_csv(PROCESSED_DIR / "members_normalized.csv")

    records = []

    for _, row in socios.iterrows():
        add_entity(
            records,
            row.get("socio", ""),
            "socios_normalized",
            {
                "is_official_socio": True,
                "has_business_profile": True,
                "has_contact_record": bool(clean_value(row.get("main_contact_email", ""))),
                "has_member_profile": False,
                "has_subscriber_contact": False,
            },
        )

    for _, row in datoscontacto.iterrows():
        add_entity(
            records,
            row.get("Entidad", ""),
            "datoscontacto",
            {
                "is_official_socio": False,
                "has_business_profile": False,
                "has_contact_record": True,
                "has_member_profile": False,
                "has_subscriber_contact": False,
            },
        )

    for _, row in suscriptores.iterrows():
        add_entity(
            records,
            row.get("company", ""),
            "suscriptores",
            {
                "is_official_socio": False,
                "has_business_profile": False,
                "has_contact_record": False,
                "has_member_profile": False,
                "has_subscriber_contact": True,
            },
        )

    for _, row in members.iterrows():
        add_entity(
            records,
            row.get("socio", ""),
            "members",
            {
                "is_official_socio": False,
                "has_business_profile": False,
                "has_contact_record": False,
                "has_member_profile": True,
                "has_subscriber_contact": False,
            },
        )

    raw_entities = pd.DataFrame(records)

    grouped = (
        raw_entities
        .groupby("entity_key", as_index=False)
        .agg(
            entity_name=("entity_name", "first"),
            sources=("source", lambda x: " | ".join(sorted(set(x)))),
            is_official_socio=("is_official_socio", "max"),
            has_business_profile=("has_business_profile", "max"),
            has_contact_record=("has_contact_record", "max"),
            has_member_profile=("has_member_profile", "max"),
            has_subscriber_contact=("has_subscriber_contact", "max"),
            source_count=("source", lambda x: len(set(x))),
        )
    )

    grouped = grouped.sort_values(
        ["is_official_socio", "source_count", "entity_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    output_path = PROCESSED_DIR / "entity_universe.csv"
    grouped.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved entity universe to: {output_path}")
    print(f"Rows: {len(grouped)}")

    print("\nEntity coverage:")
    print(f"Official socios: {grouped['is_official_socio'].sum()}")
    print(f"With business profile: {grouped['has_business_profile'].sum()}")
    print(f"With contact record: {grouped['has_contact_record'].sum()}")
    print(f"With member profile: {grouped['has_member_profile'].sum()}")
    print(f"With subscriber contact: {grouped['has_subscriber_contact'].sum()}")

    print("\nSource count distribution:")
    print(grouped["source_count"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()