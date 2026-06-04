from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw/event_registrations")
PROCESSED_DIR = Path("data/processed")

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".html", ".htm"}


def inventory_row(path, sheet_name, read_method, df=None, error=""):
    if df is None:
        rows = 0
        columns = 0
        column_names = ""
    else:
        rows = len(df)
        columns = len(df.columns)
        column_names = " | ".join([str(col) for col in df.columns])

    return {
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "sheet_name": sheet_name,
        "read_method": read_method,
        "rows": rows,
        "columns": columns,
        "column_names": column_names,
        "error": error,
    }


def inspect_xls_file(path):
    rows = []

    # Many CRM exports are HTML tables saved with .xls extension.
    try:
        tables = pd.read_html(path)

        for index, df in enumerate(tables):
            rows.append(
                inventory_row(
                    path=path,
                    sheet_name=f"html_table_{index}",
                    read_method="read_html_from_xls",
                    df=df,
                )
            )

        return rows

    except Exception as html_error:
        rows.append(
            inventory_row(
                path=path,
                sheet_name="",
                read_method="read_html_from_xls",
                error=str(html_error),
            )
        )

    # If read_html fails, try true old Excel format.
    try:
        excel_file = pd.ExcelFile(path, engine="xlrd")

        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(path, sheet_name=sheet_name, engine="xlrd")
                rows.append(
                    inventory_row(
                        path=path,
                        sheet_name=sheet_name,
                        read_method="read_excel_xlrd",
                        df=df,
                    )
                )
            except Exception as sheet_error:
                rows.append(
                    inventory_row(
                        path=path,
                        sheet_name=sheet_name,
                        read_method="read_excel_xlrd",
                        error=str(sheet_error),
                    )
                )

        return rows

    except Exception as excel_error:
        rows.append(
            inventory_row(
                path=path,
                sheet_name="",
                read_method="read_excel_xlrd",
                error=str(excel_error),
            )
        )

    return rows


def inspect_xlsx_file(path):
    rows = []

    try:
        excel_file = pd.ExcelFile(path)

        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(path, sheet_name=sheet_name)
                rows.append(
                    inventory_row(
                        path=path,
                        sheet_name=sheet_name,
                        read_method="read_excel_openpyxl",
                        df=df,
                    )
                )
            except Exception as sheet_error:
                rows.append(
                    inventory_row(
                        path=path,
                        sheet_name=sheet_name,
                        read_method="read_excel_openpyxl",
                        error=str(sheet_error),
                    )
                )

    except Exception as excel_error:
        rows.append(
            inventory_row(
                path=path,
                sheet_name="",
                read_method="ExcelFile_openpyxl",
                error=str(excel_error),
            )
        )

    return rows


def inspect_csv_file(path):
    try:
        df = pd.read_csv(path)
        return [
            inventory_row(
                path=path,
                sheet_name="",
                read_method="read_csv",
                df=df,
            )
        ]
    except Exception as error:
        return [
            inventory_row(
                path=path,
                sheet_name="",
                read_method="read_csv",
                error=str(error),
            )
        ]


def inspect_html_file(path):
    rows = []

    try:
        tables = pd.read_html(path)

        for index, df in enumerate(tables):
            rows.append(
                inventory_row(
                    path=path,
                    sheet_name=f"html_table_{index}",
                    read_method="read_html",
                    df=df,
                )
            )

    except Exception as error:
        rows.append(
            inventory_row(
                path=path,
                sheet_name="",
                read_method="read_html",
                error=str(error),
            )
        )

    return rows


def inspect_file(path):
    extension = path.suffix.lower()

    if extension == ".xls":
        return inspect_xls_file(path)

    if extension == ".xlsx":
        return inspect_xlsx_file(path)

    if extension == ".csv":
        return inspect_csv_file(path)

    if extension in {".html", ".htm"}:
        return inspect_html_file(path)

    return [
        inventory_row(
            path=path,
            sheet_name="",
            read_method="unsupported",
            error="Unsupported file extension",
        )
    ]


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        path
        for path in RAW_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    print(f"Found files: {len(files)}")

    all_rows = []

    for path in files:
        print(f"Inspecting: {path.name}")
        all_rows.extend(inspect_file(path))

    output = pd.DataFrame(all_rows)

    output_path = PROCESSED_DIR / "event_registration_file_inventory.csv"
    output.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\nSaved inventory to: {output_path}")
    print(f"Inventory rows: {len(output)}")

    if not output.empty:
        print("\nRead methods:")
        print(output["read_method"].value_counts().to_string())

        print("\nExtensions:")
        print(output["extension"].value_counts().to_string())

        print("\nRows summary:")
        print(output["rows"].describe().to_string())

        errors = output[output["error"].fillna("").str.strip() != ""]
        print(f"\nRows with errors: {len(errors)}")

        if len(errors) > 0:
            print(errors[["file_name", "read_method", "error"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()