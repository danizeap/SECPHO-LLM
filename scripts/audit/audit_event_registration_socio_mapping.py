import re
import html
import unicodedata
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def clean_value(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).strip()

    if text.lower() in {"nan", "none", "n/d", "no definido", "-", "null"}:
        return ""

    return text


def normalize_key(value):
    text = clean_value(value).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def main():
    matched = pd.read_csv(PROCESSED_DIR / "event_registrations_matched.csv")
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")
    entity_universe = pd.read_csv(PROCESSED_DIR / "entity_universe.csv")

    official_socio_keys = set(socios["socio"].apply(normalize_key))
    known_entity_keys = set(entity_universe["entity_key"].dropna().astype(str))

    matched["matched_socio_key_check"] = matched["matched_socio"].apply(normalize_key)
    matched["company_key_check"] = matched["company"].apply(normalize_key)
    matched["selected_socio_key_check"] = matched["selected_socio_raw"].apply(normalize_key)

    matched["matched_socio_is_official"] = matched["matched_socio_key_check"].isin(official_socio_keys)
    matched["company_is_official"] = matched["company_key_check"].isin(official_socio_keys)
    matched["selected_socio_is_official"] = matched["selected_socio_key_check"].isin(official_socio_keys)

    matched["company_is_known_entity"] = matched["company_key_check"].isin(known_entity_keys)
    matched["matched_socio_is_known_entity"] = matched["matched_socio_key_check"].isin(known_entity_keys)

    subscriber_rows = matched[matched["matched_source"] == "suscriptores_normalized"].copy()
    subscriber_not_official = subscriber_rows[~subscriber_rows["matched_socio_is_official"]].copy()

    potential_rescues = matched[
        (~matched["matched_socio_is_official"])
        & (
            matched["company_is_official"]
            | matched["selected_socio_is_official"]
        )
    ].copy()

    summary_rows = [
        {
            "metric": "total_registration_rows",
            "value": len(matched),
        },
        {
            "metric": "rows_matched_to_any_source",
            "value": int((matched["match_confidence"] != "unmatched").sum()),
        },
        {
            "metric": "rows_linked_to_official_socio_current",
            "value": int(matched["matched_to_official_socio"].sum()),
        },
        {
            "metric": "rows_where_matched_socio_is_official",
            "value": int(matched["matched_socio_is_official"].sum()),
        },
        {
            "metric": "rows_where_company_field_is_official",
            "value": int(matched["company_is_official"].sum()),
        },
        {
            "metric": "rows_where_selected_socio_is_official",
            "value": int(matched["selected_socio_is_official"].sum()),
        },
        {
            "metric": "potential_rescues_from_company_or_selected_socio",
            "value": len(potential_rescues),
        },
        {
            "metric": "subscriber_matched_rows",
            "value": len(subscriber_rows),
        },
        {
            "metric": "subscriber_matched_not_official",
            "value": len(subscriber_not_official),
        },
        {
            "metric": "rows_company_is_known_entity",
            "value": int(matched["company_is_known_entity"].sum()),
        },
        {
            "metric": "rows_matched_socio_is_known_entity",
            "value": int(matched["matched_socio_is_known_entity"].sum()),
        },
    ]

    summary = pd.DataFrame(summary_rows)

    summary_path = PROCESSED_DIR / "event_registration_socio_mapping_summary.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    potential_rescues_path = PROCESSED_DIR / "event_registration_potential_socio_rescues.csv"
    potential_rescues.to_csv(potential_rescues_path, index=False, encoding="utf-8-sig")

    unmatched_socio_names = (
        subscriber_not_official["matched_socio"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    unmatched_socio_names = unmatched_socio_names[unmatched_socio_names != ""]

    unmatched_summary = (
        unmatched_socio_names
        .value_counts()
        .reset_index()
    )
    unmatched_summary.columns = ["matched_socio_name", "registration_rows"]

    unmatched_summary_path = PROCESSED_DIR / "event_registration_unofficial_socio_names.csv"
    unmatched_summary.to_csv(unmatched_summary_path, index=False, encoding="utf-8-sig")

    print(f"Saved summary to: {summary_path}")
    print(f"Saved potential rescues to: {potential_rescues_path}")
    print(f"Saved unofficial socio names to: {unmatched_summary_path}")

    print("\nSummary:")
    print(summary.to_string(index=False))

    print("\nTop subscriber matched names that are not official socios:")
    print(unmatched_summary.head(30).to_string(index=False))


if __name__ == "__main__":
    main()