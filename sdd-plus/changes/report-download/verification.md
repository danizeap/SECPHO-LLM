# Verification

## Change

report-download

## Automated Checks

- [x] `python -m pytest tests/ -q` → 18 passed: 15 report_engine (incl. `generate_bytes` returns
      a valid in-memory `.docx`) + 3 `/api/report` integration tests (unauthenticated → 401,
      authenticated → 200 `.docx`, bad type → 400) that boot the real app on a localhost port.
- [x] `python -c "ast.parse(...)"` on `mvp_web_app.py` → parses.

## Manual Checks

- [x] Live end-to-end (local server + curl): `/health` 200; login 303; `POST /api/report`
      unauthenticated → **401**; authenticated person → **200**, `Content-Type` docx, 38652b,
      `Content-Disposition: attachment; filename="Informe_Andres_Cifuentes_Fernandez.docx"`;
      company → 200, 39866b; bad `type` → **400**. Downloaded `.docx` opens as a valid Word document.
- [x] XSS: `markdown_to_chat_html` escapes a malicious socio name (`"><script>…`) into the
      `data-socio` attribute (`&quot;&gt;&lt;script&gt;…`); no raw `<script>` in the output. The
      socio name is carried in a data attribute, never interpolated into `onclick`.
- [x] PII: the report is generated in memory (`BytesIO`), streamed to authenticated staff only,
      never written to the server disk, never committed.

## Documentation Updates

- [x] `report-generation` delta spec (download capability) under `specs/`.
- [ ] No documentation update needed. Reason: captured in the delta spec.

## Result

PASS — `/api/report` streams a person/company `.docx` to authenticated staff, generated in
memory; UI download button + inline tokens (XSS-safe). Verifier subagent: VERIFIED (auth-gated
before any generation, no PII on disk or in git, XSS-safe, complete error paths). 18 tests,
including 3 endpoint integration tests that pin the PII auth gate (401), the download, and
input validation.
