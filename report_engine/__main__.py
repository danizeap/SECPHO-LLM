"""CLI: python -m report_engine --type person --id <member_id> --out file.docx
        python -m report_engine --type company --socio "AINIA" --out file.docx
"""
from __future__ import annotations

import argparse

from . import report as rg


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="report_engine",
        description="Generate a SECPHO 'Informe de Valor y Oportunidades' (.docx).",
    )
    ap.add_argument("--type", required=True, choices=["person", "company"])
    ap.add_argument("--id", help="member_id (required for --type person)")
    ap.add_argument("--socio", help="socio name (required for --type company)")
    ap.add_argument("--out", required=True, help="output .docx path")
    args = ap.parse_args()

    if args.type == "person":
        if not args.id:
            ap.error("--id is required for --type person")
        path = rg.generate("person", args.id, args.out)
    else:
        if not args.socio:
            ap.error("--socio is required for --type company")
        path = rg.generate("company", args.socio, args.out)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
