import re
import unicodedata
from pathlib import Path

import pandas as pd

import html


PROCESSED_DIR = Path("data/processed")


def normalize_key(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def main():
    members = pd.read_csv(PROCESSED_DIR / "members_normalized.csv")
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")
    retos = pd.read_csv(PROCESSED_DIR / "retos_normalized.csv")

    members["socio_key"] = members["socio"].apply(normalize_key)
    socios["socio_key_check"] = socios["socio"].apply(normalize_key)

    socio_keys = set(socios["socio_key_check"].dropna())

    members_with_socio = members[members["socio_key"] != ""].copy()
    members_matched = members_with_socio[members_with_socio["socio_key"].isin(socio_keys)].copy()
    members_unmatched = members_with_socio[~members_with_socio["socio_key"].isin(socio_keys)].copy()

    socios_with_members = socios[socios["socio_key_check"].isin(set(members["socio_key"]))].copy()
    socios_without_members = socios[~socios["socio_key_check"].isin(set(members["socio_key"]))].copy()

    retos["issuing_entity_keys"] = retos["issuing_entities"].fillna("").apply(
        lambda x: [normalize_key(part) for part in str(x).split("|") if normalize_key(part)]
    )

    reto_rows_with_issuer = retos[retos["issuing_entity_keys"].apply(len) > 0].copy()

    reto_issuer_matches = 0
    for keys in reto_rows_with_issuer["issuing_entity_keys"]:
        if any(key in socio_keys for key in keys):
            reto_issuer_matches += 1

    summary = {
        "members_total": len(members),
        "members_with_socio": len(members_with_socio),
        "members_matched_to_socios": len(members_matched),
        "members_unmatched_to_socios": len(members_unmatched),
        "socios_total": len(socios),
        "socios_with_at_least_one_member": len(socios_with_members),
        "socios_without_members": len(socios_without_members),
        "retos_total": len(retos),
        "retos_with_issuing_entity": len(reto_rows_with_issuer),
        "retos_issuer_matched_to_socios": reto_issuer_matches,
    }

    print("\nJOIN AUDIT SUMMARY")
    for key, value in summary.items():
        print(f"{key}: {value}")

    members_unmatched[["full_name", "email", "socio"]].to_csv(
        PROCESSED_DIR / "members_unmatched_to_socios.csv",
        index=False,
        encoding="utf-8-sig",
    )

    socios_without_members[["socio", "company_type", "member_type"]].to_csv(
        PROCESSED_DIR / "socios_without_members.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\nSaved:")
    print(PROCESSED_DIR / "members_unmatched_to_socios.csv")
    print(PROCESSED_DIR / "socios_without_members.csv")


if __name__ == "__main__":
    main()