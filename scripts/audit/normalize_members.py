import ast
import json
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")
ABSENCE_VALUES = {
    "no toco ninguno",
    "no practico ningun deporte",
    "no practico ningún deporte",
    "ninguno",
    "ninguna",
    "none",
    "n/a",
}


def get_any(row, *names, default=""):
    for name in names:
        if name in row:
            return row.get(name, default)
    return default


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

    return parsed if isinstance(parsed, list) else []


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
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    return " | ".join(cleaned)


def parse_python_list_string(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return join_list(parsed)
    except Exception:
        pass

    return text


def normalize_multi_value_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()
    if not text:
        return ""
    if text.lower() in ABSENCE_VALUES:
        return ""

    for separator in [";", ","]:
        if separator in text:
            return join_list(
                part.strip()
                for part in text.split(separator)
                if part.strip().lower() not in ABSENCE_VALUES
            )

    return text


def build_profile_text(row):
    parts = [
        row.get("full_name", ""),
        row.get("socio", ""),
        row.get("role_function", ""),
        row.get("role_title", ""),
        row.get("municipality", ""),
        row.get("province", ""),
        row.get("country", ""),
        row.get("technology_parents", ""),
        row.get("technology_subs", ""),
        row.get("sector_parents", ""),
        row.get("sector_subs", ""),
        row.get("ambitos", ""),
        row.get("needs_general", ""),
        row.get("needs_specific", ""),
        row.get("hobbies", ""),
        row.get("sports", ""),
        row.get("instruments", ""),
        row.get("languages", ""),
        row.get("university", ""),
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
        tech_json = parse_json_list(get_any(row, "Tecnologias json", "Tecnologías json", "TecnologÃ­as json"))
        sector_json = parse_json_list(get_any(row, "Sectores json"))

        first_name = str(get_any(row, "Nombre")).strip()
        last_name = str(get_any(row, "Apellidos")).strip()
        full_name = f"{first_name} {last_name}".strip()

        normalized_row = {
            "member_id": get_any(row, "_source_id", "ID", "Id", "id"),
            "full_name": full_name,
            "email": get_any(row, "Correo"),
            "socio": get_any(row, "Socio"),
            "role_function": get_any(row, "Funcion", "Función", "FunciÃ³n"),
            "role_title": get_any(row, "Cargo"),
            "municipality": get_any(row, "Municipio prof."),
            "province": get_any(row, "Provincia prof."),
            "country": get_any(row, "Pais", "País", "PaÃ­s", "Pais de origen"),
            "country_origin": get_any(row, "Pais de origen"),
            "linkedin_user_type": get_any(row, "Tipo user LinkedIn"),
            "secpho_engagement": get_any(row, "Engag. In SECPHO"),
            "status": get_any(row, "Estado"),
            "technology_parents": join_list(extract_parents(tech_json)),
            "technology_subs": join_list(extract_subs(tech_json)),
            "sector_parents": join_list(extract_parents(sector_json)),
            "sector_subs": join_list(extract_subs(sector_json)),
            "ambitos": parse_python_list_string(get_any(row, "Ambitos", "Ámbitos", "Ãmbitos")),
            "needs_general": get_any(row, "Necesidades Gen"),
            "needs_specific": get_any(row, "Necesidades Esp"),
            "hobbies": normalize_multi_value_text(get_any(row, "Hobbies")),
            "sports": normalize_multi_value_text(get_any(row, "Deportes")),
            "instruments": normalize_multi_value_text(get_any(row, "Instrumentos")),
            "languages": normalize_multi_value_text(get_any(row, "Idiomas")),
            "university": get_any(row, "Universidad"),
            "children": get_any(row, "Hijos"),
            "gender": get_any(row, "Genero", "Género", "GÃ©nero"),
            "food_preferences": get_any(row, "Alimentacion", "Alimentación", "AlimentaciÃ³n"),
            "patents_count": get_any(row, "Patentes"),
            "publications_count": get_any(row, "Publicaciones"),
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
