import json
from pathlib import Path

import pandas as pd

import ast


PROCESSED_DIR = Path("data/processed")


def parse_json_list(value):
    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, list):
        return parsed

    return []


def extract_parents(json_items):
    parents = []

    for item in json_items:
        parent = item.get("parent")

        if parent and parent not in parents:
            parents.append(parent)

    return parents


def extract_subs(json_items):
    subs = []

    for item in json_items:
        for sub in item.get("sub", []):
            if sub and sub not in subs:
                subs.append(sub)

    return subs


def join_list(values):
    if not values:
        return ""

    return " | ".join(values)

def parse_python_list_string(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return join_list([str(item).strip() for item in parsed if str(item).strip()])
    except Exception:
        pass

    return text

def build_profile_text(row):
    parts = [
        row.get("full_name", ""),
        row.get("socio", ""),
        row.get("role_function", ""),
        row.get("role_title", ""),
        row.get("province", ""),
        row.get("technology_parents", ""),
        row.get("technology_subs", ""),
        row.get("sector_parents", ""),
        row.get("sector_subs", ""),
        row.get("ambitos", ""),
        row.get("needs_general", ""),
        row.get("needs_specific", ""),
    ]

    clean_parts = [
        str(part).strip()
        for part in parts
        if pd.notna(part) and str(part).strip()
    ]

    return ". ".join(clean_parts)


def main():
    members_path = PROCESSED_DIR / "members.csv"
    members = pd.read_csv(members_path)

    normalized_rows = []

    for _, row in members.iterrows():
        tech_json = parse_json_list(row.get("Tecnologías json"))
        sector_json = parse_json_list(row.get("Sectores json"))

        first_name = str(row.get("Nombre", "")).strip()
        last_name = str(row.get("Apellidos", "")).strip()
        full_name = f"{first_name} {last_name}".strip()

        normalized_row = {
            "member_id": row.get("_source_id", ""),
            "full_name": full_name,
            "email": row.get("Correo", ""),
            "socio": row.get("Socio", ""),
            "role_function": row.get("Función", ""),
            "role_title": row.get("Cargo", ""),
            "province": row.get("Provincia prof.", ""),
            "country": row.get("País", ""),
            "linkedin_user_type": row.get("Tipo user LinkedIn", ""),
            "secpho_engagement": row.get("Engag. In SECPHO", ""),
            "status": row.get("Estado", ""),
            "technology_parents": join_list(extract_parents(tech_json)),
            "technology_subs": join_list(extract_subs(tech_json)),
            "sector_parents": join_list(extract_parents(sector_json)),
            "sector_subs": join_list(extract_subs(sector_json)),
            "ambitos": parse_python_list_string(row.get("Ámbitos", "")),
            "needs_general": row.get("Necesidades Gen", ""),
            "needs_specific": row.get("Necesidades Esp", ""),
            "patents_count": row.get("Patentes", ""),
            "publications_count": row.get("Publicaciones", ""),
        }

        normalized_row["profile_text"] = build_profile_text(normalized_row)

        normalized_rows.append(normalized_row)

    output = pd.DataFrame(normalized_rows)

    output_path = PROCESSED_DIR / "members_normalized.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized members to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns)}")
    print("\nColumns:")
    print(list(output.columns))


if __name__ == "__main__":
    main()