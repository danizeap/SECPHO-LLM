import json
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def try_parse_json(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def inspect_json_column(df, column_name, max_examples=3):
    total = len(df)

    parsed = df[column_name].apply(try_parse_json)
    parse_success = parsed.notna().sum()
    parse_percent = round((parse_success / total) * 100, 2) if total else 0

    print(f"\nCOLUMN: {column_name}")
    print(f"Rows: {total}")
    print(f"Parsed successfully: {parse_success}")
    print(f"Parse success %: {parse_percent}")

    examples = parsed.dropna().head(max_examples).tolist()

    print("\nExamples:")
    for example in examples:
        print(json.dumps(example, ensure_ascii=False, indent=2))


def main():
    members = pd.read_csv(PROCESSED_DIR / "members.csv")

    inspect_json_column(members, "Tecnologías json")
    inspect_json_column(members, "Sectores json")


if __name__ == "__main__":
    main()