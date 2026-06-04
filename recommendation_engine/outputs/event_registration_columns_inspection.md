# Event Registration Columns Inspection

Input: `C:\Users\Daniel Paez\Desktop\secpho_intelligence_system\data\processed\event_registrations_matched.csv`

- Rows: 2202
- Columns: 32

## Columns

- `event_file` | dtype: `str` | non-null: 2202 | missing: 0 | example: `'10 Reunión anual secpho_2025-04-25_10-51'.xls`
- `event_title_from_file` | dtype: `str` | non-null: 2202 | missing: 0 | example: `10 Reunión anual secpho`
- `sheet_name` | dtype: `str` | non-null: 2202 | missing: 0 | example: `html_table_0`
- `read_method` | dtype: `str` | non-null: 2202 | missing: 0 | example: `read_html_from_xls`
- `source_row_index` | dtype: `int64` | non-null: 2202 | missing: 0 | example: `0`
- `first_name` | dtype: `str` | non-null: 2201 | missing: 1 | example: `Antonio`
- `last_name` | dtype: `str` | non-null: 2103 | missing: 99 | example: `Sanchez`
- `full_name` | dtype: `str` | non-null: 2202 | missing: 0 | example: `Antonio Sanchez`
- `full_name_key` | dtype: `str` | non-null: 2202 | missing: 0 | example: `antoniosanchez`
- `email` | dtype: `str` | non-null: 2110 | missing: 92 | example: `asanchez@asorcad.es`
- `email_key` | dtype: `str` | non-null: 2110 | missing: 92 | example: `asanchezasorcades`
- `company` | dtype: `str` | non-null: 1953 | missing: 249 | example: `3765_AsorCAD Engineering`
- `company_key` | dtype: `str` | non-null: 1950 | missing: 252 | example: `3765asorcadengineering`
- `role` | dtype: `str` | non-null: 2000 | missing: 202 | example: `CEO`
- `phone` | dtype: `str` | non-null: 2172 | missing: 30 | example: `935707782`
- `is_secpho_member_raw` | dtype: `str` | non-null: 744 | missing: 1458 | example: `si`
- `selected_socio_raw` | dtype: `str` | non-null: 694 | missing: 1508 | example: `3765`
- `selected_socio_key` | dtype: `str` | non-null: 694 | missing: 1508 | example: `3765`
- `comments` | dtype: `str` | non-null: 424 | missing: 1778 | example: `Deseo asistir a todo el evento`
- `source_type` | dtype: `str` | non-null: 2202 | missing: 0 | example: `registration`
- `email_match_key` | dtype: `str` | non-null: 2110 | missing: 92 | example: `asanchez@asorcad.es`
- `full_name_match_key` | dtype: `str` | non-null: 2202 | missing: 0 | example: `antoniosanchez`
- `company_match_key` | dtype: `str` | non-null: 1950 | missing: 252 | example: `3765asorcadengineering`
- `selected_socio_match_key` | dtype: `str` | non-null: 694 | missing: 1508 | example: `3765`
- `matched_source` | dtype: `str` | non-null: 1584 | missing: 618 | example: `members_normalized`
- `matched_person_name` | dtype: `str` | non-null: 1571 | missing: 631 | example: `Antonio Sanchez`
- `matched_email` | dtype: `str` | non-null: 1584 | missing: 618 | example: `asanchez@asorcad.es`
- `matched_socio` | dtype: `str` | non-null: 1561 | missing: 641 | example: `AsorCAD Engineering`
- `matched_socio_key` | dtype: `str` | non-null: 1560 | missing: 642 | example: `asorcadengineering`
- `match_method` | dtype: `str` | non-null: 1584 | missing: 618 | example: `email_to_members`
- `match_confidence` | dtype: `str` | non-null: 2202 | missing: 0 | example: `high`
- `matched_to_official_socio` | dtype: `bool` | non-null: 2202 | missing: 0 | example: `True`

## Confirmed Useful Fields For V1.1

- Event identifier/title fields: `event_file`, `event_title_from_file`
- Person fields: `email`, `email_key`, `full_name`, `full_name_key`
- Matched fields: `matched_person_name`, `matched_email`, `matched_socio`, `matched_socio_key`
- Match quality fields: `match_method`, `match_confidence`, `matched_to_official_socio`

## Terminology Rule

These rows represent event registration/interest records, not confirmed attendance. The recommendation signal must be named `event_interest_overlap_score`.