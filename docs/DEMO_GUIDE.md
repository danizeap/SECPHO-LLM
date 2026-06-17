# SECPHO Intelligence Chat - Demo Guide

A conversational layer over the whole SECPHO dataset. **Math decides, the LLM explains**:
the recommender and all stats are computed deterministically; the LLM only phrases the
already-computed evidence (it never invents or re-ranks matches).

## What it can do now

Beyond the contact matchmaker, the chat now answers across the whole dataset:

| Ask | What happens |
|---|---|
| "What can you tell me about the SECPHO ecosystem?" | Dataset overview + top technologies/sectors/provinces |
| "Show me events about photonics" | Searches 521 events (accent + EN/ES aware: *photonics* matches *Fotónica*) |
| "Upcoming events" | Events with a future date (4 currently) |
| "Recent retos about industrial manufacturing" | Searches 174 retos (supply-demand challenges) |
| "Open retos" | Currently-open challenges (falls back to most recent if none open) |
| "How many socios by province?" | Deterministic distribution |
| "Who works at ICFO?" | People at a company |
| "Top socios by readiness" | Deterministic socio ranking |
| "Recommendations for David Santana" | Model-ranked introductions with evidence |
| "Create a report for David Santana" | One-page briefing grounded in the model evidence |
| "Make a chart of socios by readiness" | The tool-learning loop builds + runs a safe chart tool and returns an SVG |
| "Explain the score logic" | The exact scoring formula (single source of truth) |

If the user asks for something unsupported (export, prediction, integration, a new chart),
the **tool-learning loop** records a reviewed proposal; safe templates (charts) are auto-built
and run immediately, riskier ones are queued for review (visible under `/admin`).

## Run locally

```bash
pip install -r requirements.txt
# create .env from .env.example and fill in OPENAI_API_KEY (+ passwords if you want auth)
python backend_api/mvp_web_app.py
# opens on http://127.0.0.1:8765
```

The startup banner reports model, whether the LLM key is set, whether auth is on, and the
session-secret status.

## Deploy (Render)

`render.yaml` already defines the service. In the Render dashboard set these env vars
(they are `sync: false`, so they are NOT in the repo):

- `OPENAI_API_KEY` - required for LLM phrasing (`OPENAI_MODEL` defaults to `gpt-5-mini`)
- `SECPHO_APP_PASSWORD` - shared login for the demo audience
- `SECPHO_ADMIN_PASSWORD` - your admin login for `/admin`
- `SECPHO_SESSION_SECRET` - a long random string (keeps logins stable across restarts)

`HOST=0.0.0.0` and `$PORT` are handled automatically.

## Safety notes

- Auth is **fail-closed for admin**: with no passwords set the app is usable but never grants
  admin, so the feedback inbox / tool requests stay private.
- Sessions are signed (HMAC) cookies; bad input returns clean 4xx (no stack traces); state-file
  writes are locked; rate limits apply per IP (login 8/5min, chat 30/min, feedback 10/5min).
- All recommendation data is precomputed in `recommendation_engine/outputs/` and loaded at
  startup - the LLM never produces scores.

## Feedback loop

Anyone can leave feedback from the chat (the **Feedback** button). You review it at
`/admin` (admin login) alongside the tool-learning requests. Feedback is appended to
`data/app_state/feedback_inbox.md`.

## Demo flow suggestion

1. "What can you tell me about the SECPHO ecosystem?" - sets the stage.
2. "Show me events about photonics" - shows whole-dataset querying + the language/accent handling.
3. "How many socios by province?" - deterministic analytics.
4. "Recommendations for David Santana" - the flagship matchmaker with evidence.
5. "Create a report for David Santana" - the value report.
6. "Make a chart of socios by readiness" - the self-extending tool loop.
7. Click **Feedback**, leave a note - then show it in `/admin`.
