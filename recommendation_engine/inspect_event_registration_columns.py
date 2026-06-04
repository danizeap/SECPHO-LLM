from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"
INPUT_PATH = PROCESSED_DIR / "event_registrations_matched.csv"
OUTPUT_PATH = OUTPUT_DIR / "event_registration_columns_inspection.md"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing file: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    lines = [
        "# Event Registration Columns Inspection",
        "",
        f"Input: `{INPUT_PATH}`",
        "",
        f"- Rows: {len(df)}",
        f"- Columns: {len(df.columns)}",
        "",
        "## Columns",
        "",
    ]

    for col in df.columns:
        non_null = int(df[col].notna().sum())
        missing = int(df[col].isna().sum())
        example = ""
        examples = df[col].dropna().astype(str)
        if not examples.empty:
            example = examples.iloc[0][:180]
        lines.append(
            f"- `{col}` | dtype: `{df[col].dtype}` | non-null: {non_null} | "
            f"missing: {missing} | example: `{example}`"
        )

    lines.extend(
        [
            "",
            "## Confirmed Useful Fields For V1.1",
            "",
            "- Event identifier/title fields: `event_file`, `event_title_from_file`",
            "- Person fields: `email`, `email_key`, `full_name`, `full_name_key`",
            "- Matched fields: `matched_person_name`, `matched_email`, `matched_socio`, `matched_socio_key`",
            "- Match quality fields: `match_method`, `match_confidence`, `matched_to_official_socio`",
            "",
            "## Terminology Rule",
            "",
            "These rows represent event registration/interest records, not confirmed attendance. "
            "The recommendation signal must be named `event_interest_overlap_score`.",
        ]
    )

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
