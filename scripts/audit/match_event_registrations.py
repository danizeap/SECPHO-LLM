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


def normalize_text(value):
    text = clean_value(value).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_key(value):
    text = normalize_text(value)
    text = re.sub(r"[^a-z0-9]", "", text)

    return text


def normalize_email(value):
    text = clean_value(value).lower()

    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)

    if match:
        return match.group(0)

    return text


def build_lookup(df, key_column):
    lookup = {}

    for _, row in df.iterrows():
        key = clean_value(row.get(key_column, ""))

        if key and key not in lookup:
            lookup[key] = row

    return lookup


def main():
    registrations = pd.read_csv(PROCESSED_DIR / "event_registrations_normalized.csv")
    members = pd.read_csv(PROCESSED_DIR / "members_normalized.csv")
    subscribers = pd.read_csv(PROCESSED_DIR / "suscriptores_normalized.csv")
    contacts = pd.read_csv(PROCESSED_DIR / "datoscontacto.csv")
    socios = pd.read_csv(PROCESSED_DIR / "socios_normalized.csv")

    # Normalize lookup keys
    registrations["email_match_key"] = registrations["email"].apply(normalize_email)
    registrations["full_name_match_key"] = registrations["full_name"].apply(normalize_key)
    registrations["company_match_key"] = registrations["company"].apply(normalize_key)
    registrations["selected_socio_match_key"] = registrations["selected_socio_raw"].apply(normalize_key)

    members["email_match_key"] = members["email"].apply(normalize_email)
    members["full_name_match_key"] = members["full_name"].apply(normalize_key)
    members["socio_match_key"] = members["socio"].apply(normalize_key)

    subscribers["email_match_key"] = subscribers["email"].apply(normalize_email)
    subscribers["full_name_match_key"] = subscribers["full_name"].apply(normalize_key)
    subscribers["company_match_key"] = subscribers["company"].apply(normalize_key)
    subscribers["socio_match_key"] = subscribers["socio"].apply(normalize_key)

    contacts["email_match_key"] = contacts["Contacto_Email"].apply(normalize_email)
    contacts["entity_match_key"] = contacts["Entidad"].apply(normalize_key)

    socios["socio_match_key"] = socios["socio"].apply(normalize_key)

    member_email_lookup = build_lookup(
        members[members["email_match_key"] != ""],
        "email_match_key",
    )
    subscriber_email_lookup = build_lookup(
        subscribers[subscribers["email_match_key"] != ""],
        "email_match_key",
    )
    contact_email_lookup = build_lookup(
        contacts[contacts["email_match_key"] != ""],
        "email_match_key",
    )

    member_name_lookup = build_lookup(
        members[members["full_name_match_key"] != ""],
        "full_name_match_key",
    )
    subscriber_name_lookup = build_lookup(
        subscribers[subscribers["full_name_match_key"] != ""],
        "full_name_match_key",
    )

    socio_lookup = build_lookup(
        socios[socios["socio_match_key"] != ""],
        "socio_match_key",
    )

    matched_rows = []

    for _, row in registrations.iterrows():
        email_key = row.get("email_match_key", "")
        name_key = row.get("full_name_match_key", "")
        company_key = row.get("company_match_key", "")
        selected_socio_key = row.get("selected_socio_match_key", "")

        matched_source = ""
        matched_person_name = ""
        matched_email = ""
        matched_socio = ""
        matched_socio_key = ""
        match_method = ""
        match_confidence = "unmatched"

        # 1. Email to rich members
        if email_key and email_key in member_email_lookup:
            matched = member_email_lookup[email_key]
            matched_source = "members_normalized"
            matched_person_name = clean_value(matched.get("full_name", ""))
            matched_email = clean_value(matched.get("email", ""))
            matched_socio = clean_value(matched.get("socio", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "email_to_members"
            match_confidence = "high"

        # 2. Email to subscribers
        elif email_key and email_key in subscriber_email_lookup:
            matched = subscriber_email_lookup[email_key]
            matched_source = "suscriptores_normalized"
            matched_person_name = clean_value(matched.get("full_name", ""))
            matched_email = clean_value(matched.get("email", ""))
            matched_socio = clean_value(matched.get("socio", "")) or clean_value(matched.get("company", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "email_to_subscribers"
            match_confidence = "high"

        # 3. Email to contact records
        elif email_key and email_key in contact_email_lookup:
            matched = contact_email_lookup[email_key]
            first_name = clean_value(matched.get("Contacto_Nombre", ""))
            last_name = clean_value(matched.get("Contacto_Apellidos", ""))
            matched_source = "datoscontacto"
            matched_person_name = f"{first_name} {last_name}".strip()
            matched_email = clean_value(matched.get("Contacto_Email", ""))
            matched_socio = clean_value(matched.get("Entidad", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "email_to_contact"
            match_confidence = "high_medium"

        # 4. Full name to members
        elif name_key and name_key in member_name_lookup:
            matched = member_name_lookup[name_key]
            matched_source = "members_normalized"
            matched_person_name = clean_value(matched.get("full_name", ""))
            matched_email = clean_value(matched.get("email", ""))
            matched_socio = clean_value(matched.get("socio", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "full_name_to_members"
            match_confidence = "medium"

        # 5. Full name to subscribers
        elif name_key and name_key in subscriber_name_lookup:
            matched = subscriber_name_lookup[name_key]
            matched_source = "suscriptores_normalized"
            matched_person_name = clean_value(matched.get("full_name", ""))
            matched_email = clean_value(matched.get("email", ""))
            matched_socio = clean_value(matched.get("socio", "")) or clean_value(matched.get("company", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "full_name_to_subscribers"
            match_confidence = "medium"

        # 6. Company field to official socios
        elif company_key and company_key in socio_lookup:
            matched = socio_lookup[company_key]
            matched_source = "socios_normalized"
            matched_person_name = clean_value(row.get("full_name", ""))
            matched_email = clean_value(row.get("email", ""))
            matched_socio = clean_value(matched.get("socio", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "company_to_official_socio"
            match_confidence = "low_medium"

        # 7. Selected socio dropdown to official socios
        elif selected_socio_key and selected_socio_key in socio_lookup:
            matched = socio_lookup[selected_socio_key]
            matched_source = "socios_normalized"
            matched_person_name = clean_value(row.get("full_name", ""))
            matched_email = clean_value(row.get("email", ""))
            matched_socio = clean_value(matched.get("socio", ""))
            matched_socio_key = normalize_key(matched_socio)
            match_method = "selected_socio_to_official_socio"
            match_confidence = "low_medium"

        output_row = row.to_dict()
        output_row.update(
            {
                "matched_source": matched_source,
                "matched_person_name": matched_person_name,
                "matched_email": matched_email,
                "matched_socio": matched_socio,
                "matched_socio_key": matched_socio_key,
                "match_method": match_method,
                "match_confidence": match_confidence,
                "matched_to_official_socio": matched_socio_key in set(socios["socio_match_key"]),
            }
        )

        matched_rows.append(output_row)

    output = pd.DataFrame(matched_rows)

    output_path = PROCESSED_DIR / "event_registrations_matched.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    unmatched = output[output["match_confidence"] == "unmatched"].copy()
    unmatched_path = PROCESSED_DIR / "event_registrations_unmatched.csv"
    unmatched.to_csv(unmatched_path, index=False, encoding="utf-8-sig")

    print(f"Saved matched registrations to: {output_path}")
    print(f"Rows: {len(output)}")

    print(f"\nSaved unmatched registrations to: {unmatched_path}")
    print(f"Unmatched rows: {len(unmatched)}")

    print("\nMatch confidence distribution:")
    print(output["match_confidence"].value_counts().to_string())

    print("\nMatch method distribution:")
    print(output["match_method"].replace("", "unmatched").value_counts().to_string())

    official_matches = output["matched_to_official_socio"].sum()
    print("\nOfficial socio linkage:")
    print(f"Rows linked to official socios: {official_matches}")
    print(f"Percent linked to official socios: {(official_matches / len(output)) * 100:.2f}%")

    print("\nUnique matched official socios:")
    print(output[output["matched_to_official_socio"]]["matched_socio"].nunique())

    print("\nTop matched socios by registration rows:")
    print(
        output[output["matched_to_official_socio"]]["matched_socio"]
        .value_counts()
        .head(20)
        .to_string()
    )


if __name__ == "__main__":
    main()