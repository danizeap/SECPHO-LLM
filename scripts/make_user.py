#!/usr/bin/env python3
"""Generate SECPHO_USERS entries (PBKDF2-hashed) plus plaintext passwords.

Usage:
  python scripts/make_user.py EMAIL:ROLE [EMAIL:ROLE ...]

Roles: user | admin.

Prints:
  1. The SECPHO_USERS env value (hashes only) to paste into the Render dashboard.
  2. The plaintext passwords to hand to each person — these are random, are NOT
     stored anywhere, and cannot be recovered later. Share them securely, then
     discard this output. Re-run to rotate.
"""
import hashlib
import secrets
import string
import sys

ALPHABET = string.ascii_letters + string.digits  # unambiguous-ish, no shell-special chars


def gen_password(length: int = 20) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def hash_password(password: str, iterations: int = 600000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def main(argv: list) -> None:
    if not argv:
        print(__doc__)
        return
    entries, creds = [], []
    for spec in argv:
        if ":" not in spec:
            print(f"skip {spec!r}: expected EMAIL:ROLE", file=sys.stderr)
            continue
        email, role = spec.rsplit(":", 1)
        email, role = email.strip().lower(), role.strip().lower()
        if role not in {"user", "admin"}:
            print(f"skip {spec!r}: role must be user|admin", file=sys.stderr)
            continue
        pw = gen_password()
        entries.append(f"{email}|{role}|{hash_password(pw)}")
        creds.append((email, role, pw))

    print("\n=== SECPHO_USERS (set this single env var on Render — hashes only, safe to store) ===\n")
    print(";".join(entries))
    print("\n=== Passwords to distribute (random, not stored anywhere — share securely, then discard) ===\n")
    for email, role, pw in creds:
        print(f"  {email:<34} [{role:<5}]  {pw}")


if __name__ == "__main__":
    main(sys.argv[1:])
