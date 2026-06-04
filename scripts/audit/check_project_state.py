from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")

EXPECTED_FILES = [
    "members.csv",
    "suscriptores.csv",
    "datosnegocio.csv",
    "datoscontacto.csv",
    "actosagenda.csv",
    "retos.csv",
    "members_normalized.csv",
    "socios_normalized.csv",
    "retos_normalized.csv",
    "events_normalized.csv",
    "suscriptores_normalized.csv",
    "entity_universe.csv",
    "official_socios_coverage.csv",
    "official_socios_readiness.csv",
    "signal_feasibility_matrix.csv",
    "column_profile.csv",
    "endpoint_audit_summary.json",
]


def describe_csv(path):
    df = pd.read_csv(path)
    return len(df), len(df.columns)


def main():
    print("SECPHO 01_Data_Audit project state")
    print("=" * 45)

    missing_files = []

    for filename in EXPECTED_FILES:
        path = PROCESSED_DIR / filename

        if not path.exists():
            missing_files.append(filename)
            print(f"[MISSING] {filename}")
            continue

        if filename.endswith(".csv"):
            rows, columns = describe_csv(path)
            print(f"[OK] {filename} | rows: {rows} | columns: {columns}")
        else:
            print(f"[OK] {filename}")

    print("\nSummary")
    print("=" * 45)

    if missing_files:
        print("Missing files:")
        for filename in missing_files:
            print(f"- {filename}")
    else:
        print("All expected audit files are present.")

    readiness_path = PROCESSED_DIR / "official_socios_readiness.csv"
    feasibility_path = PROCESSED_DIR / "signal_feasibility_matrix.csv"

    if readiness_path.exists():
        readiness = pd.read_csv(readiness_path)
        print("\nOfficial socios readiness:")
        print(readiness["readiness_label"].value_counts().to_string())

    if feasibility_path.exists():
        feasibility = pd.read_csv(feasibility_path)
        print("\nSignal feasibility:")
        print(feasibility["status"].value_counts().to_string())


if __name__ == "__main__":
    main()