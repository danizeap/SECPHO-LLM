from pathlib import Path
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"

PEOPLE_PATH = OUTPUT_DIR / "person_profiles_v1.csv"
PERSON_EVENTS_PATH = OUTPUT_DIR / "person_event_interest_v1.csv"
SOCIO_EVENTS_PATH = OUTPUT_DIR / "socio_event_interest_v1.csv"
OUTPUT_PATH = OUTPUT_DIR / "people_matches_v1_1_events.csv"
DEMO_PATH = OUTPUT_DIR / "people_matcher_demo_examples_v1_1_events.csv"


TOP_K = 50
PERSONAL_STOP_TERMS = {
    "no toco ninguno",
    "no practico ningun deporte",
    "no practico ningún deporte",
    "ninguno",
    "ninguna",
    "none",
    "n/a",
}
WEIGHTS = {
    "profile_similarity": 0.44,
    "structured_overlap": 0.24,
    "needs_overlap": 0.10,
    "event_interest_overlap": 0.14,
    "location_overlap": 0.06,
    "personal_affinity": 0.02,
}


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def split_terms(value) -> set:
    text = clean_text(value)
    if not text:
        return set()

    parts = re.split(r"\s*\|\s*|,\s*|;\s*", text)
    return {
        p.strip().lower()
        for p in parts
        if p and p.strip() and p.strip().lower() not in {"nan", "none", "n/d"}
    }


def split_personal_terms(value) -> set:
    return {term for term in split_terms(value) if term not in PERSONAL_STOP_TERMS}


def jaccard(set_a: set, set_b: set) -> float:
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def shared_terms(set_a: set, set_b: set) -> str:
    return " | ".join(sorted(set_a & set_b))


def same_clean_value(left, right) -> bool:
    return bool(clean_text(left)) and clean_text(left).lower() == clean_text(right).lower()


def location_overlap_score(target: pd.Series, candidate: pd.Series) -> float:
    if same_clean_value(target.get("municipality"), candidate.get("municipality")):
        return 1.0
    if same_clean_value(target.get("province"), candidate.get("province")):
        return 0.6
    return 0.0


def shared_location(target: pd.Series, candidate: pd.Series) -> str:
    if same_clean_value(target.get("municipality"), candidate.get("municipality")):
        return f"same municipality: {clean_text(target.get('municipality'))}"
    if same_clean_value(target.get("province"), candidate.get("province")):
        return f"same province: {clean_text(target.get('province'))}"
    return ""


def build_term_sets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["technology_parent_set"] = df["technology_parents"].apply(split_terms)
    df["technology_sub_set"] = df["technology_subs"].apply(split_terms)
    df["sector_parent_set"] = df["sector_parents"].apply(split_terms)
    df["sector_sub_set"] = df["sector_subs"].apply(split_terms)
    df["ambitos_set"] = df["ambitos"].apply(split_terms)
    df["needs_general_set"] = df["needs_general"].apply(split_terms)
    df["needs_specific_set"] = df["needs_specific"].apply(split_terms)
    df["hobbies_set"] = df.get("hobbies", pd.Series("", index=df.index)).apply(split_personal_terms)
    df["sports_set"] = df.get("sports", pd.Series("", index=df.index)).apply(split_personal_terms)
    df["instruments_set"] = df.get("instruments", pd.Series("", index=df.index)).apply(split_personal_terms)
    df["languages_set"] = df.get("languages", pd.Series("", index=df.index)).apply(split_terms)
    return df


def load_event_sets(path: Path, id_column: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run build_event_interest_profiles_v1.py first.")

    df = pd.read_csv(path)
    event_sets = {}
    event_titles = {}
    event_title_by_key = {}
    event_counts = {}

    if df.empty:
        return {"sets": event_sets, "titles": event_titles, "counts": event_counts}

    for _, row in df.iterrows():
        key = row[id_column]
        events = split_terms(row.get("registered_event_keys", ""))
        title_lookup = {}
        for pair in str(row.get("registered_event_pairs", "")).split("|"):
            pair = pair.strip()
            if "::" not in pair:
                continue
            event_key, title = pair.split("::", 1)
            event_key = event_key.strip()
            title = title.strip()
            if event_key and title:
                title_lookup[event_key] = title
        event_sets[key] = events
        event_titles[key] = set(title_lookup.values())
        event_title_by_key[key] = title_lookup
        event_counts[key] = int(row.get("registered_event_count", 0) or 0)

    return {
        "sets": event_sets,
        "titles": event_titles,
        "title_by_key": event_title_by_key,
        "counts": event_counts,
    }


def shared_event_titles(
    shared_keys: set,
    target_title_lookup: dict,
    candidate_title_lookup: dict,
) -> str:
    titles = []
    for key in sorted(shared_keys):
        titles.append(target_title_lookup.get(key) or candidate_title_lookup.get(key) or key)
    return " | ".join(titles)


def event_evidence_level(person_shared: str, socio_shared: str) -> str:
    if person_shared:
        return "High: shared person-level event registration interest"
    if socio_shared:
        return "Medium: shared socio-level event registration interest"
    return "Low: no shared event registration interest"


def main() -> None:
    if not PEOPLE_PATH.exists():
        raise FileNotFoundError(f"Missing {PEOPLE_PATH}. Run build_person_profiles_v1.py first.")

    people = pd.read_csv(PEOPLE_PATH)
    people = build_term_sets(people)
    people["person_recommender_text"] = people["person_recommender_text"].fillna("")

    person_events = load_event_sets(PERSON_EVENTS_PATH, "member_id")
    socio_events = load_event_sets(SOCIO_EVENTS_PATH, "socio_key")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
    )
    tfidf_matrix = vectorizer.fit_transform(people["person_recommender_text"])
    similarity_matrix = cosine_similarity(tfidf_matrix)

    rows = []

    for target_idx, target in people.iterrows():
        candidate_scores = []
        target_member_id = target["member_id"]
        target_socio_key = target["socio_key"]
        target_person_events = person_events["sets"].get(target_member_id, set())
        target_socio_events = socio_events["sets"].get(target_socio_key, set())

        for candidate_idx, candidate in people.iterrows():
            if target_idx == candidate_idx:
                continue
            if target["socio_match_key"] == candidate["socio_match_key"]:
                continue

            candidate_member_id = candidate["member_id"]
            candidate_socio_key = candidate["socio_key"]
            candidate_person_events = person_events["sets"].get(candidate_member_id, set())
            candidate_socio_events = socio_events["sets"].get(candidate_socio_key, set())

            profile_similarity = float(similarity_matrix[target_idx, candidate_idx])

            tech_parent_overlap = jaccard(
                target["technology_parent_set"],
                candidate["technology_parent_set"],
            )
            tech_sub_overlap = jaccard(target["technology_sub_set"], candidate["technology_sub_set"])
            sector_parent_overlap = jaccard(
                target["sector_parent_set"],
                candidate["sector_parent_set"],
            )
            sector_sub_overlap = jaccard(target["sector_sub_set"], candidate["sector_sub_set"])
            ambitos_overlap = jaccard(target["ambitos_set"], candidate["ambitos_set"])
            needs_overlap = jaccard(
                target["needs_general_set"] | target["needs_specific_set"],
                candidate["needs_general_set"] | candidate["needs_specific_set"],
            )
            location_overlap = location_overlap_score(target, candidate)
            hobbies_overlap = jaccard(target["hobbies_set"], candidate["hobbies_set"])
            sports_overlap = jaccard(target["sports_set"], candidate["sports_set"])
            instruments_overlap = jaccard(target["instruments_set"], candidate["instruments_set"])
            languages_overlap = jaccard(target["languages_set"], candidate["languages_set"])
            personal_affinity_score = (
                0.60 * hobbies_overlap
                + 0.25 * sports_overlap
                + 0.15 * instruments_overlap
            )

            structured_overlap = (
                0.30 * tech_parent_overlap
                + 0.20 * tech_sub_overlap
                + 0.25 * sector_parent_overlap
                + 0.15 * sector_sub_overlap
                + 0.10 * ambitos_overlap
            )

            person_event_overlap = jaccard(target_person_events, candidate_person_events)
            socio_event_overlap = jaccard(target_socio_events, candidate_socio_events)
            event_interest_overlap_score = (
                0.70 * person_event_overlap
                + 0.30 * socio_event_overlap
            )

            final_score = (
                WEIGHTS["profile_similarity"] * profile_similarity
                + WEIGHTS["structured_overlap"] * structured_overlap
                + WEIGHTS["needs_overlap"] * needs_overlap
                + WEIGHTS["event_interest_overlap"] * event_interest_overlap_score
                + WEIGHTS["location_overlap"] * location_overlap
                + WEIGHTS["personal_affinity"] * personal_affinity_score
            )

            confidence_score = (
                (
                    float(target.get("readiness_score", 0) or 0)
                    + float(candidate.get("readiness_score", 0) or 0)
                )
                / 2
                / 100
            )

            shared_person_event_keys = target_person_events & candidate_person_events
            shared_socio_event_keys = target_socio_events & candidate_socio_events
            shared_person_events = shared_event_titles(
                shared_person_event_keys,
                person_events["title_by_key"].get(target_member_id, {}),
                person_events["title_by_key"].get(candidate_member_id, {}),
            )
            shared_socio_events = shared_event_titles(
                shared_socio_event_keys,
                socio_events["title_by_key"].get(target_socio_key, {}),
                socio_events["title_by_key"].get(candidate_socio_key, {}),
            )

            candidate_scores.append(
                {
                    "target_member_id": target_member_id,
                    "target_name": target["full_name"],
                    "target_email": target["email"],
                    "target_socio": target["socio"],
                    "target_role": target.get("role_title", ""),
                    "candidate_member_id": candidate_member_id,
                    "candidate_name": candidate["full_name"],
                    "candidate_email": candidate["email"],
                    "candidate_socio": candidate["socio"],
                    "candidate_role": candidate.get("role_title", ""),
                    "final_score": round(final_score, 4),
                    "profile_similarity": round(profile_similarity, 4),
                    "structured_overlap": round(structured_overlap, 4),
                    "needs_overlap": round(needs_overlap, 4),
                    "event_interest_overlap_score": round(event_interest_overlap_score, 4),
                    "location_overlap_score": round(location_overlap, 4),
                    "personal_affinity_score": round(personal_affinity_score, 4),
                    "person_event_overlap": round(person_event_overlap, 4),
                    "socio_event_overlap": round(socio_event_overlap, 4),
                    "confidence_score": round(confidence_score, 4),
                    "target_municipality": target.get("municipality", ""),
                    "target_province": target.get("province", ""),
                    "target_country": target.get("country", ""),
                    "candidate_municipality": candidate.get("municipality", ""),
                    "candidate_province": candidate.get("province", ""),
                    "candidate_country": candidate.get("country", ""),
                    "target_readiness_label": target.get("readiness_label", ""),
                    "candidate_readiness_label": candidate.get("readiness_label", ""),
                    "shared_technologies": shared_terms(
                        target["technology_parent_set"] | target["technology_sub_set"],
                        candidate["technology_parent_set"] | candidate["technology_sub_set"],
                    ),
                    "shared_sectors": shared_terms(
                        target["sector_parent_set"] | target["sector_sub_set"],
                        candidate["sector_parent_set"] | candidate["sector_sub_set"],
                    ),
                    "shared_ambitos": shared_terms(target["ambitos_set"], candidate["ambitos_set"]),
                    "shared_needs": shared_terms(
                        target["needs_general_set"] | target["needs_specific_set"],
                        candidate["needs_general_set"] | candidate["needs_specific_set"],
                    ),
                    "shared_location": shared_location(target, candidate),
                    "shared_hobbies": shared_terms(target["hobbies_set"], candidate["hobbies_set"]),
                    "shared_sports": shared_terms(target["sports_set"], candidate["sports_set"]),
                    "shared_instruments": shared_terms(target["instruments_set"], candidate["instruments_set"]),
                    "shared_languages": shared_terms(target["languages_set"], candidate["languages_set"]),
                    "shared_registered_events": shared_person_events or shared_socio_events,
                    "shared_person_registered_events": shared_person_events,
                    "shared_socio_registered_events": shared_socio_events,
                    "target_registered_event_count": person_events["counts"].get(target_member_id, 0),
                    "candidate_registered_event_count": person_events["counts"].get(candidate_member_id, 0),
                    "target_socio_registered_event_count": socio_events["counts"].get(target_socio_key, 0),
                    "candidate_socio_registered_event_count": socio_events["counts"].get(candidate_socio_key, 0),
                    "event_interest_evidence_level": event_evidence_level(
                        shared_person_events,
                        shared_socio_events,
                    ),
                    "event_interest_note": (
                        "Event signal indicates shared SECPHO registration interest, "
                        "not confirmed attendance."
                    ),
                }
            )

        top_candidates = sorted(
            candidate_scores,
            key=lambda x: x["final_score"],
            reverse=True,
        )[:TOP_K]
        rows.extend(top_candidates)

    recommendations = pd.DataFrame(rows)
    recommendations.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    demo = (
        recommendations.sort_values("final_score", ascending=False)
        .groupby("target_member_id", as_index=False)
        .head(1)
        .head(25)
    )
    demo.to_csv(DEMO_PATH, index=False, encoding="utf-8-sig")

    print("People matcher v1.1 with event interest created")
    print(f"People in matcher: {len(people)}")
    print(f"Recommendations created: {len(recommendations)}")
    print(f"Top-k per person: {TOP_K}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Demo examples: {DEMO_PATH}")


if __name__ == "__main__":
    main()
