from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "phase1_input_inspection.md"


FILES = {
    "socios": "socios_normalized.csv",
    "members": "members_normalized.csv",
    "retos": "retos_normalized.csv",
    "readiness": "official_socios_readiness.csv",
    "coverage": "official_socios_coverage.csv",
    "signal_feasibility": "signal_feasibility_matrix.csv",
}


def load_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def inspect_file(name: str, filename: str) -> str:
    df = load_csv(filename)

    lines = []
    lines.append(f"## {name.upper()} | `{filename}`")
    lines.append("")
    lines.append(f"- Rows: {len(df)}")
    lines.append(f"- Columns: {len(df.columns)}")
    lines.append("")
    lines.append("### Columns")
    lines.append("")

    for col in df.columns:
        non_null = df[col].notna().sum()
        missing = df[col].isna().sum()
        dtype = df[col].dtype

        lines.append(
            f"- `{col}` | dtype: `{dtype}` | non-null: {non_null} | missing: {missing}"
        )

    lines.append("")
    lines.append("### Sample rows")
    lines.append("")
    lines.append("```text")
    lines.append(df.head(3).to_string(index=False))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sections = []
    sections.append("# SECPHO Recommendation Engine: Phase 1 Input Inspection")
    sections.append("")
    sections.append(f"Processed data folder: `{PROCESSED_DIR}`")
    sections.append("")

    for name, filename in FILES.items():
        sections.append(inspect_file(name, filename))

    OUTPUT_PATH.write_text("\n\n".join(sections), encoding="utf-8")

    print(f"Inspection document created:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()