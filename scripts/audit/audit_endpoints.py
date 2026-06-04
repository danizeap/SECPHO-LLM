import os
import json
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("SECPHO_API_AUTH_TOKEN")
BASE_URL = "https://secpho.org/wp-json/reports/v1"

ENDPOINTS = {
    "members": "/members",
    "suscriptores": "/suscriptores",
    "datosnegocio": "/datosnegocio",
    "datoscontacto": "/datoscontacto",
    "actosagenda": "/actosagenda",
    "retos": "/retos",
}

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def fetch_endpoint(name, route):
    if not TOKEN or TOKEN == "PASTE_TOKEN_HERE":
        raise ValueError("Missing SECPHO_API_AUTH_TOKEN in .env")

    url = f"{BASE_URL}{route}"
    params = {"auth": TOKEN}

    print(f"\nFetching {name}...")

    response = requests.get(
        url,
        params=params,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=90,
    )

    print(f"Status code: {response.status_code}")
    response.raise_for_status()

    return response.json()


def json_to_dataframe(data):
    df = pd.DataFrame(data)

    if df.shape[0] < df.shape[1]:
        df_t = df.T
        if df_t.shape[0] > df.shape[0]:
            return df_t.reset_index(drop=False).rename(columns={"index": "_source_id"})

    return df.reset_index(drop=False).rename(columns={"index": "_source_id"})


def audit_dataframe(name, df):
    mostly_empty_cols = []

    for col in df.columns:
        missing_ratio = df[col].isna().mean()

        if missing_ratio >= 0.8:
            mostly_empty_cols.append(col)

    possible_id_cols = [
        col for col in df.columns
        if "id" in str(col).lower()
        or "nombre" in str(col).lower()
        or "socio" in str(col).lower()
        or "entidad" in str(col).lower()
        or "email" in str(col).lower()
        or "correo" in str(col).lower()
        or "título" in str(col).lower()
        or "titulo" in str(col).lower()
    ]

    summary = {
        "endpoint": name,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": [str(c) for c in df.columns],
        "mostly_empty_columns_80_percent_plus": [str(c) for c in mostly_empty_cols],
        "possible_join_or_identity_columns": [str(c) for c in possible_id_cols],
    }

    return summary


def main():
    all_summaries = {}

    for name, route in ENDPOINTS.items():
        try:
            data = fetch_endpoint(name, route)

            raw_path = RAW_DIR / f"{name}.json"

            with open(raw_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

            df = json_to_dataframe(data)

            csv_path = PROCESSED_DIR / f"{name}.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

            summary = audit_dataframe(name, df)
            all_summaries[name] = summary

            print(f"Saved raw JSON: {raw_path}")
            print(f"Saved CSV: {csv_path}")
            print(f"Rows: {summary['rows']}")
            print(f"Columns: {summary['columns']}")
            print("Possible join/id columns:")
            print(summary["possible_join_or_identity_columns"])

        except Exception as error:
            all_summaries[name] = {
                "endpoint": name,
                "error": str(error),
            }

            print(f"Error fetching {name}: {error}")

    summary_path = PROCESSED_DIR / "endpoint_audit_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(all_summaries, file, ensure_ascii=False, indent=2)

    print(f"\nAudit summary saved to: {summary_path}")


if __name__ == "__main__":
    main()