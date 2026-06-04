from pathlib import Path
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"

INPUT_PATH = OUTPUT_DIR / "person_profiles_v1.csv"
OUTPUT_PATH = OUTPUT_DIR / "people_matches_v1.csv"
DEMO_PATH = OUTPUT_DIR / "people_matcher_demo_examples.csv"


TOP_K = 10


def split_terms(value) -> set:
    """
    Converts fields like:
    'Fotónica | Materiales avanzados'
    into clean comparable sets.
    """
    if pd.isna(value):
        return set()

    text = str(value).strip()
    if not text:
        return set()

    parts = re.split(r"\s*\|\s*|,\s*|;\s*", text)

    return {
        p.strip().lower()
        for p in parts
        if p and p.strip() and p.strip().lower() not in {"nan", "none", "n/d"}
    }


def jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0

    union = set_a | set_b
    if not union:
        return 0.0

    return len(set_a & set_b) / len(union)


def shared_terms(set_a: set, set_b: set) -> str:
    shared = sorted(set_a & set_b)
    return " | ".join(shared)


def build_term_sets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["technology_parent_set"] = df["technology_parents"].apply(split_terms)
    df["technology_sub_set"] = df["technology_subs"].apply(split_terms)
    df["sector_parent_set"] = df["sector_parents"].apply(split_terms)
    df["sector_sub_set"] = df["sector_subs"].apply(split_terms)
    df["ambitos_set"] = df["ambitos"].apply(split_terms)
    df["needs_general_set"] = df["needs_general"].apply(split_terms)
    df["needs_specific_set"] = df["needs_specific"].apply(split_terms)

    return df


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_PATH}. Run build_person_profiles_v1.py first."
        )

    people = pd.read_csv(INPUT_PATH)
    people = build_term_sets(people)

    people["person_recommender_text"] = people["person_recommender_text"].fillna("")

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

        for candidate_idx, candidate in people.iterrows():
            if target_idx == candidate_idx:
                continue

            # Hard rule: no same-company recommendations.
            if target["socio_match_key"] == candidate["socio_match_key"]:
                continue

            profile_similarity = float(similarity_matrix[target_idx, candidate_idx])

            tech_parent_overlap = jaccard(
                target["technology_parent_set"],
                candidate["technology_parent_set"],
            )
            tech_sub_overlap = jaccard(
                target["technology_sub_set"],
                candidate["technology_sub_set"],
            )
            sector_parent_overlap = jaccard(
                target["sector_parent_set"],
                candidate["sector_parent_set"],
            )
            sector_sub_overlap = jaccard(
                target["sector_sub_set"],
                candidate["sector_sub_set"],
            )
            ambitos_overlap = jaccard(
                target["ambitos_set"],
                candidate["ambitos_set"],
            )
            needs_overlap = jaccard(
                target["needs_general_set"] | target["needs_specific_set"],
                candidate["needs_general_set"] | candidate["needs_specific_set"],
            )

            structured_overlap = (
                0.30 * tech_parent_overlap
                + 0.20 * tech_sub_overlap
                + 0.25 * sector_parent_overlap
                + 0.15 * sector_sub_overlap
                + 0.10 * ambitos_overlap
            )

            final_score = (
                0.60 * profile_similarity
                + 0.30 * structured_overlap
                + 0.10 * needs_overlap
            )

            confidence_score = (
                (
                    float(target.get("readiness_score", 0) or 0)
                    + float(candidate.get("readiness_score", 0) or 0)
                )
                / 2
                / 100
            )

            candidate_scores.append(
                {
                    "target_member_id": target["member_id"],
                    "target_name": target["full_name"],
                    "target_email": target["email"],
                    "target_socio": target["socio"],
                    "target_role": target.get("role_title", ""),
                    "candidate_member_id": candidate["member_id"],
                    "candidate_name": candidate["full_name"],
                    "candidate_email": candidate["email"],
                    "candidate_socio": candidate["socio"],
                    "candidate_role": candidate.get("role_title", ""),
                    "final_score": round(final_score, 4),
                    "profile_similarity": round(profile_similarity, 4),
                    "structured_overlap": round(structured_overlap, 4),
                    "needs_overlap": round(needs_overlap, 4),
                    "confidence_score": round(confidence_score, 4),
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
                    "shared_ambitos": shared_terms(
                        target["ambitos_set"],
                        candidate["ambitos_set"],
                    ),
                    "shared_needs": shared_terms(
                        target["needs_general_set"] | target["needs_specific_set"],
                        candidate["needs_general_set"] | candidate["needs_specific_set"],
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

    # Demo file: one top recommendation per target, sorted by score.
    demo = (
        recommendations
        .sort_values("final_score", ascending=False)
        .groupby("target_member_id", as_index=False)
        .head(1)
        .head(25)
    )
    demo.to_csv(DEMO_PATH, index=False, encoding="utf-8-sig")

    print("People matcher v1 created")
    print(f"People in matcher: {len(people)}")
    print(f"Recommendations created: {len(recommendations)}")
    print(f"Top-k per person: {TOP_K}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Demo examples: {DEMO_PATH}")


if __name__ == "__main__":
    main()