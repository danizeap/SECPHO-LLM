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


def clean_number(value):
    if pd.isna(value):
        return None

    text = str(value).replace("%", "").replace(",", ".").strip()

    try:
        return float(text)
    except ValueError:
        return None


def build_contact_name(first_name, last_name):
    return f"{clean_value(first_name)} {clean_value(last_name)}".strip()


def build_profile_text(row):
    parts = [
        row.get("full_name", ""),
        row.get("company", ""),
        row.get("socio", ""),
        row.get("role_title", ""),
        row.get("province", ""),
        row.get("sector", ""),
        row.get("lists", ""),
    ]

    return ". ".join(
        str(part).strip()
        for part in parts
        if pd.notna(part) and str(part).strip()
    )


def main():
    suscriptores = pd.read_csv(PROCESSED_DIR / "suscriptores.csv")

    normalized_rows = []

    for _, row in suscriptores.iterrows():
        full_name = build_contact_name(row.get("Nombre", ""), row.get("Apellidos", ""))

        normalized_row = {
            "subscriber_id": clean_value(row.get("_source_id", "")),
            "email": clean_value(row.get("Email", "")),
            "full_name": full_name,
            "first_name": clean_value(row.get("Nombre", "")),
            "last_name": clean_value(row.get("Apellidos", "")),
            "role_title": clean_value(row.get("Cargo", "")),
            "socio": clean_value(row.get("Socio", "")),
            "company": clean_value(row.get("Empresa", "")),
            "company_key": normalize_key(row.get("Empresa", "")),
            "phone": clean_value(row.get("Teléfono", "")),
            "province": clean_value(row.get("Provincia", "")),
            "sector": clean_value(row.get("Sector", "")),
            "lists": clean_value(row.get("Listas", "")),
            "open_rate": clean_number(row.get("% Open rate", "")),
            "click_rate": clean_number(row.get("% Click rate", "")),
            "subscribed_since": clean_value(row.get("Suscrito desde", "")),
            "emails_count": clean_number(row.get("Emails", "")),
        }

        normalized_row["profile_text"] = build_profile_text(normalized_row)

        normalized_rows.append(normalized_row)

    output = pd.DataFrame(normalized_rows)

    output_path = PROCESSED_DIR / "suscriptores_normalized.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized subscribers to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns)}")
    print("\nColumns:")
    print(list(output.columns))

    print("\nMissing key fields:")
    for column in ["email", "full_name", "company", "role_title", "province", "sector"]:
        missing = output[column].fillna("").eq("").mean() * 100
        print(f"{column}: {missing:.2f}%")

    print("\nEngagement stats:")
    print(f"Average open rate: {output['open_rate'].mean():.2f}")
    print(f"Average click rate: {output['click_rate'].mean():.2f}")


if __name__ == "__main__":
    main()