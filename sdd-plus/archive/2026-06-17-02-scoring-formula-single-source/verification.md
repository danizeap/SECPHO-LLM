# Verification

## Change

02-scoring-formula-single-source

## Automated Checks

- [x] `python -m py_compile backend_api/mvp_web_app.py` passed (module imports
      cleanly after the constant and function edits).
- [x] Grep confirmed no remaining `0.50` / `0.25` (stale 4-weight formula)
      literal in `backend_api/mvp_web_app.py`.

## Manual Checks

- [x] Asking the chat to "explain the score logic" returns the unified 6-weight
      formula (`SCORING_FORMULA_TEXT`), including location and personal affinity.

## Documentation Updates

- [x] Specs updated: capability `recommendation-scoring` created (delta + living).
- [x] No README or user-facing docs update needed. Reason: internal formula
      description only; no user-facing setup or API surface changed.

## Result

PASS -- both LLM paths now describe the single 6-weight `SCORING_WEIGHTS`
formula, matching the served CSV; no stale formula literal remains.
