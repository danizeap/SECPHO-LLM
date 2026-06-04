import re
import unicodedata
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def normalize_key(value):
    if pd.isna(value):
        return ""

    text = str(value).lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def clean_value(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in {"nan", "none", "n/d", "no definido"}:
        return ""

    return text


def build_profile_text(row):
    parts = [
        row.get("socio", ""),
        row.get("company_type", ""),
        row.get("member_type", ""),
        row.get("public_private", ""),
        row.get("participation_level", ""),
        row.get("value_chain", ""),
        row.get("activity_summary", ""),
        row.get("province", ""),
        row.get("website", ""),
    ]

    clean_parts = [
        str(part).strip()
        for part in parts
        if pd.notna(part) and str(part).strip()
    ]

    return ". ".join(clean_parts)


def main():
    datosnegocio = pd.read_csv(PROCESSED_DIR / "datosnegocio.csv")
    datoscontacto = pd.read_csv(PROCESSED_DIR / "datoscontacto.csv")

    datosnegocio["socio_key"] = datosnegocio["Socio"].apply(normalize_key)
    datoscontacto["socio_key"] = datoscontacto["Entidad"].apply(normalize_key)

    # Keep one contact row per socio.
    # Priority: rows with Contacto_Email, then Contacto_Nombre, then any matching row.
    datoscontacto["_has_email"] = datoscontacto["Contacto_Email"].notna()
    datoscontacto["_has_name"] = datoscontacto["Contacto_Nombre"].notna()

    contacto_best = (
        datoscontacto
        .sort_values(["socio_key", "_has_email", "_has_name"], ascending=[True, False, False])
        .drop_duplicates(subset=["socio_key"], keep="first")
    )

    merged = datosnegocio.merge(
        contacto_best,
        on="socio_key",
        how="left",
        suffixes=("_negocio", "_contacto"),
    )

    normalized_rows = []

    for _, row in merged.iterrows():
        contact_first_name = clean_value(row.get("Contacto_Nombre", ""))
        contact_last_name = clean_value(row.get("Contacto_Apellidos", ""))
        main_contact_name = f"{contact_first_name} {contact_last_name}".strip()

        normalized_row = {
            "socio_id": clean_value(row.get("_source_id_negocio", "")),
            "socio": clean_value(row.get("Socio", "")),
            "socio_key": clean_value(row.get("socio_key", "")),
            "company_type": clean_value(row.get("Tipo de empresa", "")),
            "member_type": clean_value(row.get("Tipo de socio", "")),
            "public_private": clean_value(row.get("Pub./Priv.", "")),
            "strategic_partner": clean_value(row.get("Socio Estratégico", "")),
            "investment_program": clean_value(row.get("Prog. Inversión", "")),
            "participation_level": clean_value(row.get("Nivel de participación", "")),
            "value_chain": clean_value(row.get("Cadena de valor", "")),
            "activity_summary": clean_value(row.get("Resumen actividad", "")),
            "revenue": clean_value(row.get("Cifra de negocio", "")),
            "employees": clean_value(row.get("Num. de empleados", "")),
            "exportation": clean_value(row.get("Exportación", "")),
            "cnae": clean_value(row.get("CNAE", "")),
            "province": clean_value(row.get("F_Provincia", "")),
            "city": clean_value(row.get("F_Municipio", "")),
            "website": clean_value(row.get("Web", "")),
            "main_contact_name": main_contact_name,
            "main_contact_role": clean_value(row.get("Contacto_Cargo", "")),
            "main_contact_email": clean_value(row.get("Contacto_Email", "")),
        }

        normalized_row["profile_text"] = build_profile_text(normalized_row)

        normalized_rows.append(normalized_row)

    output = pd.DataFrame(normalized_rows)

    output_path = PROCESSED_DIR / "socios_normalized.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized socios to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns)}")
    print("\nColumns:")
    print(list(output.columns))

    missing_contact_email = output["main_contact_email"].eq("").mean() * 100
    missing_activity = output["activity_summary"].eq("").mean() * 100

    print(f"\nMissing main contact email: {missing_contact_email:.2f}%")
    print(f"Missing activity summary: {missing_activity:.2f}%")


if __name__ == "__main__":
    main()