import re
import html
import unicodedata
from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def normalize_key(value):
    if pd.isna(value):
        return ""

    text = html.unescape(str(value)).lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def split_pipe_keys(value):
    if pd.isna(value):
        return []

    parts = str(value).split("|")
    return [normalize_key(part) for part in parts if normalize_key(part)]


def main():
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")
    members = pd.read_csv(PROCESSED_DIR / "members_normalized.csv")
    contactos = pd.read_csv(PROCESSED_DIR / "datoscontacto.csv")
    suscriptores = pd.read_csv(PROCESSED_DIR / "suscriptores_normalized.csv")
    retos = pd.read_csv(PROCESSED_DIR / "retos_normalized.csv")

    socios["socio_key"] = socios["socio"].apply(normalize_key)
    members["socio_key"] = members["socio"].apply(normalize_key)
    contactos["entity_key"] = contactos["Entidad"].apply(normalize_key)
    suscriptores["company_key_check"] = suscriptores["company"].apply(normalize_key)

    member_counts = members[members["socio_key"] != ""].groupby("socio_key").size()
    contact_counts = contactos[contactos["entity_key"] != ""].groupby("entity_key").size()
    subscriber_counts = suscriptores[suscriptores["company_key_check"] != ""].groupby("company_key_check").size()

    retos["issuer_keys"] = retos["issuing_entities"].apply(split_pipe_keys)
    retos["applicant_keys"] = retos["applying_entities"].apply(split_pipe_keys)

    issuer_counts = {}
    applicant_counts = {}

    for _, row in retos.iterrows():
        for key in row["issuer_keys"]:
            issuer_counts[key] = issuer_counts.get(key, 0) + 1

        for key in row["applicant_keys"]:
            applicant_counts[key] = applicant_counts.get(key, 0) + 1

    coverage_rows = []

    for _, row in socios.iterrows():
        key = row["socio_key"]

        coverage_rows.append(
            {
                "socio": row["socio"],
                "socio_key": key,
                "company_type": row.get("company_type", ""),
                "member_type": row.get("member_type", ""),
                "has_business_profile": True,
                "member_profile_count": int(member_counts.get(key, 0)),
                "contact_record_count": int(contact_counts.get(key, 0)),
                "subscriber_contact_count": int(subscriber_counts.get(key, 0)),
                "retos_as_issuer_count": int(issuer_counts.get(key, 0)),
                "retos_as_applicant_count": int(applicant_counts.get(key, 0)),
            }
        )

    coverage = pd.DataFrame(coverage_rows)

    coverage["has_member_profiles"] = coverage["member_profile_count"] > 0
    coverage["has_contact_records"] = coverage["contact_record_count"] > 0
    coverage["has_subscriber_contacts"] = coverage["subscriber_contact_count"] > 0
    coverage["has_retos_signal"] = (
        (coverage["retos_as_issuer_count"] > 0)
        | (coverage["retos_as_applicant_count"] > 0)
    )

    output_path = PROCESSED_DIR / "official_socios_coverage.csv"
    coverage.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved official socios coverage to: {output_path}")
    print(f"Official socios: {len(coverage)}")

    print("\nCoverage:")
    print(f"With member profiles: {coverage['has_member_profiles'].sum()}")
    print(f"With contact records: {coverage['has_contact_records'].sum()}")
    print(f"With subscriber contacts: {coverage['has_subscriber_contacts'].sum()}")
    print(f"With retos signal: {coverage['has_retos_signal'].sum()}")

    print("\nAverages:")
    print(f"Avg member profiles per socio: {coverage['member_profile_count'].mean():.2f}")
    print(f"Avg contact records per socio: {coverage['contact_record_count'].mean():.2f}")
    print(f"Avg subscriber contacts per socio: {coverage['subscriber_contact_count'].mean():.2f}")

    print("\nSocios with no member profiles:")
    print(coverage[~coverage["has_member_profiles"]][["socio", "company_type", "member_type"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()