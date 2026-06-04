from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"
MATCHES_PATH = OUTPUT_DIR / "people_matches_v1.csv"


def clean_value(value) -> str:
    if pd.isna(value):
        return "N/D"

    value = str(value).strip()

    if not value or value.lower() in {"nan", "none", "n/d"}:
        return "N/D"

    return value


def print_match(row, rank: int) -> None:
    print("\n" + "-" * 80)
    print(f"#{rank} | {row['candidate_name']}")
    print(f"Socio: {row['candidate_socio']}")
    print(f"Role: {clean_value(row.get('candidate_role'))}")
    print(f"Email: {clean_value(row.get('candidate_email'))}")
    print("")
    print(f"Final score: {row['final_score']}")
    print(f"Profile similarity: {row['profile_similarity']}")
    print(f"Structured overlap: {row['structured_overlap']}")
    print(f"Needs overlap: {row['needs_overlap']}")
    print(f"Confidence score: {row['confidence_score']}")
    print("")
    print("Evidence:")
    print(f"- Shared technologies: {clean_value(row.get('shared_technologies'))}")
    print(f"- Shared sectors: {clean_value(row.get('shared_sectors'))}")
    print(f"- Shared ámbitos: {clean_value(row.get('shared_ambitos'))}")
    print(f"- Shared needs: {clean_value(row.get('shared_needs'))}")


def search_people(matches: pd.DataFrame, query: str) -> pd.DataFrame:
    query = query.lower().strip()

    people = (
        matches[
            [
                "target_member_id",
                "target_name",
                "target_email",
                "target_socio",
                "target_role",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    mask = (
        people["target_name"].str.lower().str.contains(query, na=False)
        | people["target_socio"].str.lower().str.contains(query, na=False)
        | people["target_email"].str.lower().str.contains(query, na=False)
    )

    return people[mask].sort_values(["target_socio", "target_name"])


def show_recommendations(matches: pd.DataFrame, target_member_id: int, top_n: int = 5) -> None:
    person_matches = (
        matches[matches["target_member_id"] == target_member_id]
        .sort_values("final_score", ascending=False)
        .head(top_n)
    )

    if person_matches.empty:
        print("No matches found for this person.")
        return

    target = person_matches.iloc[0]

    print("\n" + "=" * 80)
    print("SECPHO PEOPLE MATCHER V1")
    print("=" * 80)
    print(f"Target person: {target['target_name']}")
    print(f"Target socio: {target['target_socio']}")
    print(f"Target role: {clean_value(target.get('target_role'))}")
    print(f"Target email: {clean_value(target.get('target_email'))}")
    print("")
    print(f"Showing top {len(person_matches)} recommended contacts")
    print("Rule applied: same-socio matches are excluded")

    for rank, (_, row) in enumerate(person_matches.iterrows(), start=1):
        print_match(row, rank)


def main() -> None:
    if not MATCHES_PATH.exists():
        raise FileNotFoundError(
            f"Missing {MATCHES_PATH}. Run build_people_matcher_v1.py first."
        )

    matches = pd.read_csv(MATCHES_PATH)

    print("\nSECPHO People Matcher V1 Demo")
    print("=" * 80)
    print("Search by person name, socio, or email.")
    print("Example: David Santana, Fujitsu, ICFO")
    print("Type 'exit' to quit.")

    while True:
        query = input("\nSearch person: ").strip()

        if query.lower() in {"exit", "quit", "salir"}:
            print("Demo closed.")
            break

        if not query:
            print("Please type a search term.")
            continue

        results = search_people(matches, query)

        if results.empty:
            print("No people found. Try another name or socio.")
            continue

        print("\nMatches found:")
        for i, (_, row) in enumerate(results.head(10).iterrows(), start=1):
            print(
                f"{i}. {row['target_name']} | {row['target_socio']} | "
                f"{clean_value(row.get('target_role'))}"
            )

        try:
            choice = int(input("\nChoose a person number: ").strip())
        except ValueError:
            print("Please enter a valid number.")
            continue

        if choice < 1 or choice > min(10, len(results)):
            print("Choice out of range.")
            continue

        selected = results.head(10).iloc[choice - 1]
        show_recommendations(matches, selected["target_member_id"], top_n=5)


if __name__ == "__main__":
    main()