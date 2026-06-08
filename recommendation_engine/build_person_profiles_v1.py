from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "person_profiles_v1.csv"


def load_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path)


def normalize_key(value) -> str:
    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("-", "")
        .replace("_", "")
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    members = load_csv("members_normalized.csv")
    socios = load_csv("socios_normalized.csv")
    readiness = load_csv("official_socios_readiness.csv")

    members["socio_match_key"] = members["socio"].apply(normalize_key)
    socios["socio_match_key"] = socios["socio"].apply(normalize_key)
    readiness["socio_match_key"] = readiness["socio"].apply(normalize_key)

    official_keys = set(socios["socio_match_key"])

    official_members = members[
        members["socio_match_key"].isin(official_keys)
    ].copy()

    person_profiles = official_members.merge(
        socios[
            [
                "socio_match_key",
                "socio_key",
                "company_type",
                "member_type",
                "public_private",
                "value_chain",
                "activity_summary",
                "province",
                "main_contact_name",
                "main_contact_role",
                "main_contact_email",
            ]
        ],
        on="socio_match_key",
        how="left",
        suffixes=("", "_company"),
    )

    person_profiles = person_profiles.merge(
        readiness[
            [
                "socio_match_key",
                "readiness_score",
                "readiness_label",
                "member_profile_count",
                "subscriber_contact_count",
                "retos_as_issuer_count",
                "retos_as_applicant_count",
            ]
        ],
        on="socio_match_key",
        how="left",
    )

    person_profiles["person_recommender_text"] = (
        person_profiles["profile_text"].fillna("")
        + ". Company context: "
        + person_profiles["company_type"].fillna("")
        + ". "
        + person_profiles["member_type"].fillna("")
        + ". "
        + person_profiles["public_private"].fillna("")
        + ". "
        + person_profiles["value_chain"].fillna("")
        + ". "
        + person_profiles["activity_summary"].fillna("")
        + ". Location: "
        + person_profiles.get("municipality", pd.Series("", index=person_profiles.index)).fillna("")
        + ". "
        + person_profiles.get("province", pd.Series("", index=person_profiles.index)).fillna("")
        + ". Personal context: "
        + person_profiles.get("hobbies", pd.Series("", index=person_profiles.index)).fillna("")
        + ". "
        + person_profiles.get("sports", pd.Series("", index=person_profiles.index)).fillna("")
        + ". "
        + person_profiles.get("instruments", pd.Series("", index=person_profiles.index)).fillna("")
        + ". "
        + person_profiles.get("languages", pd.Series("", index=person_profiles.index)).fillna("")
    )

    person_profiles.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Person profiles created")
    print(f"Output path: {OUTPUT_PATH}")
    print(f"Original members: {len(members)}")
    print(f"Members linked to official socios: {len(person_profiles)}")
    print(f"Unique official socios represented: {person_profiles['socio'].nunique()}")


if __name__ == "__main__":
    main()
