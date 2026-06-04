import re
import html
import unicodedata
from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw/event_registrations")
PROCESSED_DIR = Path("data/processed")

SUPPORTED_EXTENSIONS = {".xls", ".xlsx", ".csv", ".html", ".htm"}


COLUMN_ALIASES = {
    "first_name": [
        "nombre",
        "nombre:",
        "first name",
        "first name:",
        "name",
    ],
    "last_name": [
        "apellidos",
        "apellidos:",
        "last name",
        "last name:",
        "surname",
    ],
    "company": [
        "empresa/institución",
        "empresa/institución:",
        "empresa",
        "empresa:",
        "company/institution",
        "company/institution:",
        "company",
        "organization",
        "organisation",
    ],
    "role": [
        "cargo/función",
        "cargo/función:",
        "cargo",
        "función",
        "position",
        "position:",
        "job title",
        "role",
    ],
    "phone": [
        "teléfono",
        "teléfono:",
        "telefono",
        "telephone",
        "telephone:",
        "phone",
        "mobile",
    ],
    "email": [
        "email",
        "email:",
        "correo",
        "correo electrónico",
        "e-mail",
    ],
    "is_secpho_member_raw": [
        "miembro de secpho?",
        "miembro de secpho",
        "secpho member",
        "member of secpho",
        "are you a secpho member",
    ],
    "selected_socio_raw": [
        "selecciona tu entidad",
        "selecciona una entidad",
        "please select",
        "select your entity",
        "socio",
    ],
    "comments": [
        "comentarios",
        "comments",
        "observaciones",
    ],
}


def normalize_text(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_value(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).strip()

    if text.lower() in {"nan", "none", "n/d", "no definido", "-", "null"}:
        return ""

    return text


def clean_email(value):
    text = clean_value(value).lower()

    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)

    if match:
        return match.group(0)

    return text


def normalize_key(value):
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def event_title_from_file(file_name):
    name = Path(file_name).stem

    # Remove surrounding single quotes sometimes present in SharePoint downloads.
    name = name.strip("'").strip('"')

    # Remove trailing export timestamp pattern.
    name = re.sub(r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$", "", name)

    # Clean separators.
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def find_column(df, aliases):
    normalized_columns = {
        column: normalize_text(column)
        for column in df.columns
    }

    normalized_aliases = [normalize_text(alias) for alias in aliases]

    for column, normalized_column in normalized_columns.items():
        for alias in normalized_aliases:
            if alias and alias == normalized_column:
                return column

    for column, normalized_column in normalized_columns.items():
        for alias in normalized_aliases:
            if alias and alias in normalized_column:
                return column

    return None


def read_tables_from_file(path):
    extension = path.suffix.lower()
    tables = []

    if extension == ".xls":
        try:
            html_tables = pd.read_html(path)
            for index, df in enumerate(html_tables):
                tables.append((f"html_table_{index}", "read_html_from_xls", df))
            return tables
        except Exception:
            pass

        try:
            excel_file = pd.ExcelFile(path, engine="xlrd")
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet_name, engine="xlrd")
                tables.append((sheet_name, "read_excel_xlrd", df))
            return tables
        except Exception:
            return tables

    if extension == ".xlsx":
        try:
            excel_file = pd.ExcelFile(path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet_name)
                tables.append((sheet_name, "read_excel_openpyxl", df))
            return tables
        except Exception:
            return tables

    if extension == ".csv":
        try:
            df = pd.read_csv(path)
            tables.append(("", "read_csv", df))
            return tables
        except Exception:
            return tables

    if extension in {".html", ".htm"}:
        try:
            html_tables = pd.read_html(path)
            for index, df in enumerate(html_tables):
                tables.append((f"html_table_{index}", "read_html", df))
            return tables
        except Exception:
            return tables

    return tables


def detect_columns(df):
    detected = {}

    for target_column, aliases in COLUMN_ALIASES.items():
        detected[target_column] = find_column(df, aliases)

    return detected


def row_has_minimum_identity(row):
    email = row.get("email", "")
    full_name = row.get("full_name", "")
    company = row.get("company", "")

    return bool(email or full_name or company)


def normalize_table(path, sheet_name, read_method, df):
    detected = detect_columns(df)
    rows = []

    for row_index, source_row in df.iterrows():
        first_name = clean_value(source_row.get(detected["first_name"], ""))
        last_name = clean_value(source_row.get(detected["last_name"], ""))
        email = clean_email(source_row.get(detected["email"], ""))
        company = clean_value(source_row.get(detected["company"], ""))
        role = clean_value(source_row.get(detected["role"], ""))
        phone = clean_value(source_row.get(detected["phone"], ""))
        is_secpho_member_raw = clean_value(source_row.get(detected["is_secpho_member_raw"], ""))
        selected_socio_raw = clean_value(source_row.get(detected["selected_socio_raw"], ""))
        comments = clean_value(source_row.get(detected["comments"], ""))

        full_name = f"{first_name} {last_name}".strip()

        normalized_row = {
            "event_file": path.name,
            "event_title_from_file": event_title_from_file(path.name),
            "sheet_name": sheet_name,
            "read_method": read_method,
            "source_row_index": row_index,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "full_name_key": normalize_key(full_name),
            "email": email,
            "email_key": normalize_key(email),
            "company": company,
            "company_key": normalize_key(company),
            "role": role,
            "phone": phone,
            "is_secpho_member_raw": is_secpho_member_raw,
            "selected_socio_raw": selected_socio_raw,
            "selected_socio_key": normalize_key(selected_socio_raw),
            "comments": comments,
            "source_type": "registration",
        }

        if row_has_minimum_identity(normalized_row):
            rows.append(normalized_row)

    return rows, detected


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        path
        for path in RAW_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    print(f"Found files: {len(files)}")

    all_rows = []
    file_summaries = []

    for path in files:
        print(f"Normalizing: {path.name}")

        tables = read_tables_from_file(path)

        if not tables:
            file_summaries.append(
                {
                    "file_name": path.name,
                    "tables_read": 0,
                    "rows_normalized": 0,
                    "status": "unreadable",
                }
            )
            continue

        file_row_count = 0

        for sheet_name, read_method, df in tables:
            normalized_rows, detected = normalize_table(path, sheet_name, read_method, df)
            all_rows.extend(normalized_rows)
            file_row_count += len(normalized_rows)

        file_summaries.append(
            {
                "file_name": path.name,
                "tables_read": len(tables),
                "rows_normalized": file_row_count,
                "status": "ok" if file_row_count > 0 else "read_but_no_rows",
            }
        )

    output = pd.DataFrame(all_rows)
    summary = pd.DataFrame(file_summaries)

    output_path = PROCESSED_DIR / "event_registrations_normalized.csv"
    summary_path = PROCESSED_DIR / "event_registration_normalization_summary.csv"

    output.to_csv(output_path, index=False, encoding="utf-8-sig")
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print(f"\nSaved normalized registrations to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns) if not output.empty else 0}")

    print(f"\nSaved normalization summary to: {summary_path}")

    if not output.empty:
        print("\nBasic counts:")
        print(f"Unique event files: {output['event_file'].nunique()}")
        print(f"Unique event titles: {output['event_title_from_file'].nunique()}")
        print(f"Unique emails: {output['email'].replace('', pd.NA).dropna().nunique()}")
        print(f"Unique full names: {output['full_name_key'].replace('', pd.NA).dropna().nunique()}")
        print(f"Unique companies: {output['company_key'].replace('', pd.NA).dropna().nunique()}")

        print("\nMissing key fields:")
        for column in ["full_name", "email", "company", "role", "phone"]:
            missing = output[column].fillna("").eq("").mean() * 100
            print(f"{column}: {missing:.2f}%")

    print("\nFile normalization status:")
    print(summary["status"].value_counts().to_string())


if __name__ == "__main__":
    main()