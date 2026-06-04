from pathlib import Path
import re

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"

EVENT_MATCHES_PATH = PROCESSED_DIR / "event_registrations_matched.csv"
PERSON_PROFILES_PATH = OUTPUT_DIR / "person_profiles_v1.csv"
PERSON_OUTPUT_PATH = OUTPUT_DIR / "person_event_interest_v1.csv"
SOCIO_OUTPUT_PATH = OUTPUT_DIR / "socio_event_interest_v1.csv"


HIGH_CONFIDENCE = {"high", "high-medium"}


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_email(value) -> str:
    return clean_text(value).lower()


def normalize_key(value) -> str:
    text = clean_text(value).lower()
    text = text.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", text)


def event_key(row: pd.Series) -> str:
    title = clean_text(row.get("event_title_from_file"))
    source = title or clean_text(row.get("event_file"))
    return normalize_key(source)


def event_title(row: pd.Series) -> str:
    title = clean_text(row.get("event_title_from_file"))
    return title or clean_text(row.get("event_file"))


def join_sorted(values) -> str:
    cleaned = sorted({clean_text(v) for v in values if clean_text(v)})
    return " | ".join(cleaned)


def join_event_pairs(group: pd.DataFrame) -> str:
    pairs = []
    for _, row in group.drop_duplicates(["event_key"]).iterrows():
        key = clean_text(row.get("event_key"))
        title = clean_text(row.get("event_title"))
        if key and title:
            pairs.append(f"{key}::{title}")
    return " | ".join(sorted(set(pairs)))


def confidence_label(values) -> str:
    value_set = {clean_text(v).lower() for v in values if clean_text(v)}
    if value_set and value_set <= HIGH_CONFIDENCE:
        return "high"
    if "low-medium" in value_set:
        return "low-medium"
    if "medium" in value_set:
        return "medium"
    if "high-medium" in value_set:
        return "high-medium"
    if "high" in value_set:
        return "high"
    return "unknown"


def build_person_event_interest(events: pd.DataFrame, people: pd.DataFrame) -> pd.DataFrame:
    people = people.copy()
    people["email_norm"] = people["email"].apply(normalize_email)
    people["full_name_key_local"] = people["full_name"].apply(normalize_key)
    people["socio_key_local"] = people["socio"].apply(normalize_key)

    email_to_people = {
        row["email_norm"]: row
        for _, row in people.iterrows()
        if row["email_norm"]
    }

    rows = []
    for _, event in events.iterrows():
        match_confidence = clean_text(event.get("match_confidence")).lower()
        if match_confidence not in HIGH_CONFIDENCE:
            continue

        matched_email = normalize_email(event.get("matched_email")) or normalize_email(event.get("email"))
        person = email_to_people.get(matched_email)

        if person is None:
            continue

        rows.append(
            {
                "member_id": person["member_id"],
                "full_name": person["full_name"],
                "email": person["email"],
                "socio": person["socio"],
                "event_key": event["event_key"],
                "event_title": event["event_title"],
                "match_method": event.get("match_method", ""),
                "match_confidence": event.get("match_confidence", ""),
                "source_row_index": event.get("source_row_index", ""),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "member_id",
                "full_name",
                "email",
                "socio",
                "registered_event_count",
                "registered_event_titles",
                "registered_event_keys",
                "event_interest_source_rows",
                "event_interest_confidence",
            ]
        )

    detail = pd.DataFrame(rows).drop_duplicates(["member_id", "event_key"])

    grouped = []
    for member_id, group in detail.groupby("member_id", sort=False):
        first = group.iloc[0]
        grouped.append(
            {
                "member_id": member_id,
                "full_name": first["full_name"],
                "email": first["email"],
                "socio": first["socio"],
                "registered_event_count": int(group["event_key"].nunique()),
                "registered_event_titles": join_sorted(group["event_title"]),
                "registered_event_keys": join_sorted(group["event_key"]),
                "registered_event_pairs": join_event_pairs(group),
                "event_interest_source_rows": int(len(group)),
                "event_interest_confidence": confidence_label(group["match_confidence"]),
            }
        )

    return pd.DataFrame(grouped).sort_values(
        ["registered_event_count", "socio", "full_name"],
        ascending=[False, True, True],
    )


def build_socio_event_interest(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    official_events = events[events["matched_to_official_socio_bool"]].copy()

    for socio_key, group in official_events.groupby("matched_socio_key", dropna=True):
        group = group[group["event_key"].astype(str).str.len() > 0]
        if group.empty:
            continue

        first = group.iloc[0]
        distinct_events = group.drop_duplicates(["matched_socio_key", "event_key"])
        rows.append(
            {
                "socio": first.get("matched_socio", ""),
                "socio_key": socio_key,
                "registered_event_count": int(distinct_events["event_key"].nunique()),
                "registered_event_titles": join_sorted(distinct_events["event_title"]),
                "registered_event_keys": join_sorted(distinct_events["event_key"]),
                "registered_event_pairs": join_event_pairs(distinct_events),
                "event_interest_source_rows": int(len(group)),
                "event_interest_confidence": confidence_label(group["match_confidence"]),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["registered_event_count", "socio"],
        ascending=[False, True],
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not EVENT_MATCHES_PATH.exists():
        raise FileNotFoundError(f"Missing file: {EVENT_MATCHES_PATH}")
    if not PERSON_PROFILES_PATH.exists():
        raise FileNotFoundError(
            f"Missing {PERSON_PROFILES_PATH}. Run build_person_profiles_v1.py first."
        )

    events = pd.read_csv(EVENT_MATCHES_PATH)
    people = pd.read_csv(PERSON_PROFILES_PATH)

    events["event_key"] = events.apply(event_key, axis=1)
    events["event_title"] = events.apply(event_title, axis=1)
    events["matched_to_official_socio_bool"] = (
        events["matched_to_official_socio"].astype(str).str.lower().eq("true")
    )

    person_interest = build_person_event_interest(events, people)
    socio_interest = build_socio_event_interest(events)

    person_interest.to_csv(PERSON_OUTPUT_PATH, index=False, encoding="utf-8-sig")
    socio_interest.to_csv(SOCIO_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Event interest profiles created")
    print(f"Person event profiles: {len(person_interest)}")
    print(f"Socio event profiles: {len(socio_interest)}")
    print(f"Output: {PERSON_OUTPUT_PATH}")
    print(f"Output: {SOCIO_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
