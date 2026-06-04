from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")

FILES = [
    "members",
    "suscriptores",
    "datosnegocio",
    "datoscontacto",
    "actosagenda",
    "retos",
]


def get_examples(series, max_examples=3):
    values = series.dropna().astype(str)
    values = values[values.str.strip() != ""]

    unique_values = values.drop_duplicates().head(max_examples).tolist()

    return " | ".join(unique_values)


def profile_file(name):
    path = PROCESSED_DIR / f"{name}.csv"

    df = pd.read_csv(path)

    rows = len(df)
    profiles = []

    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_percent = round((missing_count / rows) * 100, 2) if rows > 0 else 0
        unique_count = int(df[column].nunique(dropna=True))

        profiles.append(
            {
                "endpoint": name,
                "column": column,
                "dtype": str(df[column].dtype),
                "missing_count": missing_count,
                "missing_percent": missing_percent,
                "unique_count": unique_count,
                "example_values": get_examples(df[column]),
            }
        )

    return profiles


def main():
    all_profiles = []

    for name in FILES:
        print(f"Profiling {name}...")
        all_profiles.extend(profile_file(name))

    output = pd.DataFrame(all_profiles)

    output_path = PROCESSED_DIR / "column_profile.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\nSaved column profile to: {output_path}")
    print(f"Rows in profile: {len(output)}")


if __name__ == "__main__":
    main()