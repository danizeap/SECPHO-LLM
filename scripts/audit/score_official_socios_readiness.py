from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def has_text(value):
    if pd.isna(value):
        return False

    text = str(value).strip()

    return text != "" and text.lower() not in {"nan", "none", "n/d", "no definido"}


def readiness_label(score):
    if score >= 80:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def main():
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")
    coverage = pd.read_csv(PROCESSED_DIR / "official_socios_coverage.csv")

    df = socios.merge(
        coverage[
            [
                "socio_key",
                "member_profile_count",
                "contact_record_count",
                "subscriber_contact_count",
                "retos_as_issuer_count",
                "retos_as_applicant_count",
                "has_member_profiles",
                "has_contact_records",
                "has_subscriber_contacts",
                "has_retos_signal",
            ]
        ],
        on="socio_key",
        how="left",
    )

    df["has_activity_summary"] = df["activity_summary"].apply(has_text)
    df["has_main_contact_email"] = df["main_contact_email"].apply(has_text)

    df["readiness_score"] = 0

    df.loc[df["has_member_profiles"] == True, "readiness_score"] += 30
    df.loc[df["has_subscriber_contacts"] == True, "readiness_score"] += 20
    df.loc[df["has_retos_signal"] == True, "readiness_score"] += 20
    df.loc[df["has_activity_summary"] == True, "readiness_score"] += 15
    df.loc[df["has_main_contact_email"] == True, "readiness_score"] += 15

    df["readiness_label"] = df["readiness_score"].apply(readiness_label)

    output_columns = [
        "socio",
        "company_type",
        "member_type",
        "readiness_score",
        "readiness_label",
        "member_profile_count",
        "subscriber_contact_count",
        "retos_as_issuer_count",
        "retos_as_applicant_count",
        "has_activity_summary",
        "has_main_contact_email",
        "province",
        "website",
    ]

    output = df[output_columns].sort_values(
        ["readiness_score", "socio"],
        ascending=[False, True],
    )

    output_path = PROCESSED_DIR / "official_socios_readiness.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved official socios readiness to: {output_path}")
    print(f"Rows: {len(output)}")

    print("\nReadiness distribution:")
    print(output["readiness_label"].value_counts().to_string())

    print("\nAverage readiness score:")
    print(round(output["readiness_score"].mean(), 2))

    print("\nTop 15 most ready socios:")
    print(output.head(15)[["socio", "readiness_score", "readiness_label"]].to_string(index=False))

    print("\nLowest 15 readiness socios:")
    print(output.tail(15)[["socio", "readiness_score", "readiness_label"]].to_string(index=False))


if __name__ == "__main__":
    main()