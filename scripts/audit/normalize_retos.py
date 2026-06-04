import re
import html
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def clean_value(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in {"nan", "none", "n/d", "no definido"}:
        return ""

    return text


def clean_html_text(value):
    text = clean_value(value)

    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_list_text(value):
    text = clean_value(value)

    if not text:
        return ""

    # Some endpoint fields are comma-separated company/category strings.
    parts = [part.strip() for part in text.split(",") if part.strip()]

    # Remove duplicates while preserving order.
    unique_parts = list(dict.fromkeys(parts))

    return " | ".join(unique_parts)


def main():
    retos = pd.read_csv(PROCESSED_DIR / "retos.csv")

    normalized_rows = []

    for _, row in retos.iterrows():
        title = clean_value(row.get("Título", ""))
        description_clean = clean_html_text(row.get("Descripción", ""))

        normalized_row = {
            "reto_id": clean_value(row.get("_source_id", "")),
            "reto_number": clean_value(row.get("Num. reto", "")),
            "title": title,
            "description_clean": description_clean,
            "sectors": clean_list_text(row.get("Sector/es", "")),
            "issuing_entities": clean_list_text(row.get("Entidad emisora", "")),
            "submission_date": clean_value(row.get("Fecha envío", "")),
            "closing_date": clean_value(row.get("Fecha cierre", "")),
            "applying_entities": clean_list_text(row.get("Entidades que aplican", "")),
            "connection_type": clean_value(row.get("Tipo de conexión", "")),
            "creates_project": clean_value(row.get("¿Surge proyecto?", "")),
            "beneficiary_socio": clean_value(row.get("Socio beneficiado", "")),
        }

        profile_parts = [
            normalized_row["title"],
            normalized_row["description_clean"],
            normalized_row["sectors"],
            normalized_row["issuing_entities"],
            normalized_row["connection_type"],
        ]

        normalized_row["reto_text"] = ". ".join(
            part for part in profile_parts if part and str(part).strip()
        )

        normalized_rows.append(normalized_row)

    output = pd.DataFrame(normalized_rows)

    output_path = PROCESSED_DIR / "retos_normalized.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized retos to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns)}")
    print("\nColumns:")
    print(list(output.columns))

    missing_description = output["description_clean"].eq("").mean() * 100
    missing_sectors = output["sectors"].eq("").mean() * 100
    missing_issuer = output["issuing_entities"].eq("").mean() * 100

    print(f"\nMissing clean description: {missing_description:.2f}%")
    print(f"Missing sectors: {missing_sectors:.2f}%")
    print(f"Missing issuing entities: {missing_issuer:.2f}%")


if __name__ == "__main__":
    main()