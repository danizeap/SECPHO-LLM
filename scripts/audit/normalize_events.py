import ast
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


def parse_list_like(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, list):
            clean_items = [str(item).strip() for item in parsed if str(item).strip()]
            return " | ".join(dict.fromkeys(clean_items))
    except Exception:
        pass

    return text


def main():
    events = pd.read_csv(PROCESSED_DIR / "actosagenda.csv")

    normalized_rows = []

    for _, row in events.iterrows():
        normalized_row = {
            "event_id": clean_value(row.get("ID", "")),
            "event_date": clean_value(row.get("Fecha", "")),
            "title": clean_value(row.get("Título", "")),
            "location_type": clean_value(row.get("Ubicación", "")),
            "province": clean_value(row.get("Provincia", "")),
            "country": clean_value(row.get("País", "")),
            "city": clean_value(row.get("Ciudad", "")),
            "place": clean_value(row.get("Lugar", "")),
            "link": clean_value(row.get("Link", "")),
            "typology": parse_list_like(row.get("Tipología", "")),
            "technologies": parse_list_like(row.get("Tecnología", "")),
            "ambitos": parse_list_like(row.get("Ámbito", "")),
            "sectors": parse_list_like(row.get("Sector", "")),
            "in_collaboration": clean_value(row.get("En colaboración", "")),
            "partner": clean_value(row.get("Partner", "")),
            "num_speakers": clean_value(row.get("Num. ponentes", "")),
            "num_attendees": clean_value(row.get("Num. asistentes", "")),
            "num_registered": clean_value(row.get("Num. registrados", "")),
        }

        event_text_parts = [
            normalized_row["title"],
            normalized_row["typology"],
            normalized_row["technologies"],
            normalized_row["ambitos"],
            normalized_row["sectors"],
            normalized_row["location_type"],
            normalized_row["province"],
            normalized_row["city"],
            normalized_row["partner"],
        ]

        normalized_row["event_text"] = ". ".join(
            part for part in event_text_parts if part and str(part).strip()
        )

        normalized_rows.append(normalized_row)

    output = pd.DataFrame(normalized_rows)

    output_path = PROCESSED_DIR / "events_normalized.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved normalized events to: {output_path}")
    print(f"Rows: {len(output)}")
    print(f"Columns: {len(output.columns)}")
    print("\nColumns:")
    print(list(output.columns))

    print("\nMissing key fields:")
    for column in ["event_date", "title", "technologies", "ambitos", "sectors", "location_type"]:
        missing = output[column].eq("").mean() * 100
        print(f"{column}: {missing:.2f}%")


if __name__ == "__main__":
    main()