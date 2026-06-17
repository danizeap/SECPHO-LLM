# Decision Log

## Change

07-bilingual-interface

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-06-16 | Spanish is the DEFAULT for both chat UI and assistant responses; English is opt-in via toggle | SECPHO is a Spanish-first organization and the primary demo audience is Spanish-speaking | English default with a Spanish toggle; browser `Accept-Language` negotiation |
| 2026-06-16 | Enforce response language via a per-request thread-local directive appended once in `call_llm` (`language_directive()`) | Single change point; avoids threading a `lang` argument through every tool/function | Passing `lang` explicitly through each tool; a global mutable language setting |
| 2026-06-16 | The ES/EN toggle switches BOTH the UI chrome and the response language together | A single control keeps interface and answers consistent; less user confusion | Separate toggles for UI vs response language |
| 2026-06-16 | Auto-detect the user's input language on send and flip the toggle to match | Respect the language the user actually writes without a manual switch | No detection (manual toggle only); server-side detection |
| 2026-06-16 | Keep deterministic (non-LLM) fallbacks in English; defer the ES/EN/both report-download picker | The active-LLM path covers the demo; the export picker belongs with the export feature | Localizing all fallbacks now; shipping the report-language picker in this change |
