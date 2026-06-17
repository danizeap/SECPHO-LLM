# Engineering Standards

## General

- Prefer the existing stack and project patterns.
- Keep changes scoped to the active SDD+ change.
- Choose simple, maintainable designs over clever abstractions.
- Add abstractions only when they remove real duplication or complexity.
- Verify behavior before calling work complete.

## Safety

- Never commit secrets or credentials.
- Avoid destructive commands unless the user explicitly asks for them.
- Do not revert user changes unless explicitly requested.
- Treat auth, permissions, production data, migrations, billing, and deployment as high-impact.

## Testing

Match verification effort to risk:

- Small docs-only changes need SDD+ verification.
- Small code changes need focused smoke checks.
- Shared logic needs focused tests.
- Data/schema/security changes need explicit before/after verification.

## Git

- Keep commits intentional and scoped.
- Commit the SDD+ change packet with the work it documents.
- Do not include local artifacts, generated caches, secrets, or downloads.
