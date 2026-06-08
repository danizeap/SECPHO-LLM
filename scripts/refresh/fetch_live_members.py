import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MEMBERS_URL = "https://secpho.org/wp-json/reports/v1/members"


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    token = os.getenv("SECPHO_API_AUTH_TOKEN")
    if not token:
        raise RuntimeError("Missing SECPHO_API_AUTH_TOKEN in environment or .env")

    response = requests.get(MEMBERS_URL, params={"auth": token}, timeout=45)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, dict):
        records = []
        for member_id, record in payload.items():
            row = dict(record)
            row["_source_id"] = member_id
            records.append(row)
    elif isinstance(payload, list):
        records = [dict(record) for record in payload]
    else:
        raise TypeError(f"Unexpected members payload type: {type(payload).__name__}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "members.csv"
    pd.DataFrame(records).to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved live members to: {output_path}")
    print(f"Rows: {len(records)}")
    print(f"Columns: {len(pd.DataFrame(records).columns)}")


if __name__ == "__main__":
    main()
