from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import base64
import hashlib
import hmac
import mimetypes
import html
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "recommendation_engine" / "outputs"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

MATCHES_PATH = OUTPUT_DIR / "people_matches_v1_1_events.csv"
PEOPLE_PATH = OUTPUT_DIR / "person_profiles_v1.csv"
PERSON_EVENTS_PATH = OUTPUT_DIR / "person_event_interest_v1.csv"
SOCIO_EVENTS_PATH = OUTPUT_DIR / "socio_event_interest_v1.csv"
SOCIOS_PATH = PROCESSED_DIR / "socios_normalized.csv"
READINESS_PATH = PROCESSED_DIR / "official_socios_readiness.csv"
EVENT_REG_PATH = PROCESSED_DIR / "event_registrations_matched.csv"
STATIC_DIR = BASE_DIR / "backend_api" / "static"
APP_STATE_DIR = BASE_DIR / "data" / "app_state"
MISSING_TOOL_REQUESTS_PATH = APP_STATE_DIR / "missing_tool_requests.jsonl"
GENERATED_TOOLS_REGISTRY_PATH = APP_STATE_DIR / "generated_tools_registry.json"
TOOL_BUILD_EVENTS_PATH = APP_STATE_DIR / "tool_build_events.jsonl"
FEEDBACK_INBOX_PATH = APP_STATE_DIR / "feedback_inbox.md"
GENERATED_ARTIFACTS_DIR = BASE_DIR / "data" / "generated_artifacts"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
SESSION_COOKIE_NAME = "secpho_session"
SESSION_TTL_SECONDS = int(os.getenv("SECPHO_SESSION_TTL_SECONDS", "28800"))
APP_PASSWORD = os.getenv("SECPHO_APP_PASSWORD") or os.getenv("APP_ACCESS_PASSWORD")
ADMIN_PASSWORD = os.getenv("SECPHO_ADMIN_PASSWORD")
SESSION_SECRET = os.getenv("SECPHO_SESSION_SECRET") or os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32)
AUTH_REQUIRED = bool(APP_PASSWORD or ADMIN_PASSWORD)
RATE_LIMIT_EVENTS: dict[str, list[float]] = {}


RATE_LIMITS = {
    "login": (8, 300),
    "llm": (30, 60),
    "api": (120, 60),
    "feedback": (10, 300),
}


LLM_INSTRUCTIONS = """
You are the SECPHO Matchmaker explanation layer.

Hard rules:
- The deterministic matcher already selected and ranked the recommendations.
- Do not invent matches.
- Do not reorder recommendations.
- Do not add evidence that is not present in the supplied JSON.
- Event overlap means shared SECPHO registration interest, not confirmed attendance.
- Write clearly for SECPHO leadership and non-technical staff.
- Treat scores as model outputs, not personal judgments.
- Preserve the principle: math decides, the LLM explains.

Style:
- Professional, concise, useful.
- Make the report feel like an internal one-page briefing.
- Use plain language, not technical jargon.
"""


def clean(value, fallback="N/D") -> str:
    if pd.isna(value):
        return fallback
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "n/d"}:
        return fallback
    return text


def load_data() -> dict:
    required = [MATCHES_PATH, PEOPLE_PATH, PERSON_EVENTS_PATH, SOCIO_EVENTS_PATH]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required files: " + ", ".join(missing))

    return {
        "matches": pd.read_csv(MATCHES_PATH),
        "people": pd.read_csv(PEOPLE_PATH),
        "person_events": pd.read_csv(PERSON_EVENTS_PATH),
        "socio_events": pd.read_csv(SOCIO_EVENTS_PATH),
        "socios": pd.read_csv(SOCIOS_PATH) if SOCIOS_PATH.exists() else pd.DataFrame(),
        "readiness": pd.read_csv(READINESS_PATH) if READINESS_PATH.exists() else pd.DataFrame(),
        "event_regs": pd.read_csv(EVENT_REG_PATH) if EVENT_REG_PATH.exists() else pd.DataFrame(),
    }


DATA = load_data()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def openai_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sign_value(value: str) -> str:
    return hmac.new(SESSION_SECRET.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def make_session_cookie(role: str) -> str:
    now = int(time.time())
    payload = {
        "role": role,
        "iat": now,
        "exp": now + SESSION_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded = b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{encoded}.{sign_value(encoded)}"


def parse_cookie_header(header: str) -> dict:
    cookies = {}
    for part in header.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def parse_session_cookie(cookie_value: str) -> dict | None:
    if not cookie_value or "." not in cookie_value:
        return None
    encoded, signature = cookie_value.rsplit(".", 1)
    if not hmac.compare_digest(signature, sign_value(encoded)):
        return None
    try:
        payload = json.loads(b64url_decode(encoded).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    if payload.get("role") not in {"user", "admin"}:
        return None
    return payload


def check_password(password: str) -> str | None:
    if ADMIN_PASSWORD and hmac.compare_digest(password, ADMIN_PASSWORD):
        return "admin"
    if APP_PASSWORD and hmac.compare_digest(password, APP_PASSWORD):
        return "user"
    if not APP_PASSWORD and ADMIN_PASSWORD and hmac.compare_digest(password, ADMIN_PASSWORD):
        return "admin"
    return None


def rate_limit_key(ip: str, bucket: str) -> str:
    return f"{bucket}:{ip}"


def is_rate_limited(ip: str, bucket: str) -> bool:
    max_events, window = RATE_LIMITS.get(bucket, RATE_LIMITS["api"])
    now = time.time()
    key = rate_limit_key(ip, bucket)
    events = [ts for ts in RATE_LIMIT_EVENTS.get(key, []) if now - ts < window]
    if len(events) >= max_events:
        RATE_LIMIT_EVENTS[key] = events
        return True
    events.append(now)
    RATE_LIMIT_EVENTS[key] = events
    return False


def extract_response_text(payload: dict) -> str:
    if payload.get("output_text"):
        return payload["output_text"]

    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def call_llm(prompt: str, max_output_tokens: int = 1400) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "", "fallback_no_api_key"

    body = {
        "model": os.getenv("OPENAI_MODEL", OPENAI_MODEL),
        "instructions": LLM_INSTRUCTIONS,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "store": False,
    }

    try:
        response = requests.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=25,
        )
        if response.status_code >= 400:
            return "", f"fallback_openai_http_{response.status_code}"
        text = extract_response_text(response.json())
        if not text:
            return "", "fallback_empty_llm_response"
        return text, f"llm_{body['model']}"
    except Exception as exc:
        return "", f"fallback_llm_error_{type(exc).__name__}"


def parse_json_object(text: str) -> dict:
    if not text:
        return {}
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def llm_route_question(question: str, selected_member_id: int | None = None) -> dict:
    fallback = {"action": "general_answer", "args": {"question": question}}
    if not openai_available():
        return fallback

    selected = get_person(selected_member_id) if selected_member_id else None
    prompt = f"""
Classify the user's SECPHO intelligence question into exactly one backend action.

Return ONLY valid JSON. No markdown. No commentary.

Available actions:
- search_people: find people by name, company/socio, email, technology, sector, or role.
  args: query, company, name, technology, sector, role
- search_socios: find official socios/companies by name, province, company type, member type, technology-ish text.
  args: query, name, province, company_type, member_type
- rank_socios: rank official socios/companies.
  args: metric, limit. metric must be one of readiness, event, people.
- get_person_profile: show one person profile.
  args: query or member_id
- get_socio_profile: show one socio/company profile.
  args: query
- recommend_contacts: get deterministic model recommendations for one person.
  args: query or member_id
- generate_report: create a polished report for one person using deterministic recommendation evidence.
  args: query or member_id
- general_answer: answer conceptual/count/scoring/scope questions from the known MVP context.
  args: question
- propose_tool: use when the user asks for a data operation, ranking, workflow, export, visualization, prediction, integration, or automation that none of the existing actions can answer reliably.
  args: tool_name, purpose, inputs, data_sources, output_shape, safety_constraints, risk_level

Routing rules:
- "top socios", "top companies", "best socios", "ranking empresas" => rank_socios.
- If top/rank asks by events/registration => metric event.
- If top/rank asks by people/profiles/members => metric people.
- Otherwise rank_socios metric readiness.
- "who works at X", "people at X", "quien trabaja en X" => search_people with company X.
- "recommendations for X", "matches for X", "introductions for X" => recommend_contacts.
- "report for X", "brief for X", "one pager for X", "informe para X" => generate_report.
- If the user says "for this person" or similar and selected_person is present, use member_id.
- If ambiguous between person and company, prefer search_people unless the user says socios/companies/empresas.
- If the user asks for something requiring new calculations not covered by the available actions, return propose_tool.
- If the user asks for bulk export, sending emails, external integrations, predictions, charts not currently implemented, validation feedback workflows, or Codex/self-improvement workflows, return propose_tool.
- Do not pretend an unsupported task can be answered by search_people or general_answer.
- For propose_tool, produce a concrete, implementation-ready proposal with explicit inputs, data sources, output shape, and safety constraints.

Selected person context:
{json.dumps(selected, ensure_ascii=False) if selected else "null"}

User question:
{question}
"""
    text, mode = call_llm(prompt, max_output_tokens=500)
    route = parse_json_object(text)
    if not isinstance(route, dict) or "action" not in route:
        return {**fallback, "router_mode": mode, "router_failed": True}

    route.setdefault("args", {})
    if not isinstance(route["args"], dict):
        route["args"] = {}
    route["router_mode"] = mode
    return route


def normalize_tool_name(value: str) -> str:
    text = clean(value, "proposed_tool").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "proposed_tool"


def save_missing_tool_request(question: str, proposal: dict, router: dict | None = None) -> dict:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)

    tool_name = normalize_tool_name(proposal.get("tool_name", "proposed_tool"))
    record = {
        "id": f"toolreq_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "created_at": utc_now_iso(),
        "status": "proposed",
        "user_question": question,
        "tool_name": tool_name,
        "purpose": clean(proposal.get("purpose"), ""),
        "inputs": proposal.get("inputs", {}),
        "data_sources": proposal.get("data_sources", []),
        "output_shape": proposal.get("output_shape", proposal.get("output", "")),
        "safety_constraints": proposal.get("safety_constraints", []),
        "risk_level": clean(proposal.get("risk_level"), "medium"),
        "codex_review_notes": "",
        "router": router or {},
    }

    with MISSING_TOOL_REQUESTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def update_tool_request_status(request_id: str, status: str, notes: str = "") -> None:
    if not MISSING_TOOL_REQUESTS_PATH.exists():
        return

    updated = []
    changed = False
    for line in MISSING_TOOL_REQUESTS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("id") == request_id:
            record["status"] = status
            record["updated_at"] = utc_now_iso()
            if notes:
                record["codex_review_notes"] = notes
            changed = True
        updated.append(record)

    if changed:
        MISSING_TOOL_REQUESTS_PATH.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in updated) + "\n",
            encoding="utf-8",
        )


def load_missing_tool_requests(limit: int = 50) -> list[dict]:
    if not MISSING_TOOL_REQUESTS_PATH.exists():
        return []
    records = []
    for line in MISSING_TOOL_REQUESTS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records[-limit:][::-1]


def tool_request_status_view(limit: int = 50) -> list[dict]:
    requests_by_id = {
        record["id"]: record
        for record in load_missing_tool_requests(limit=1000)
        if record.get("id")
    }
    events = load_tool_build_events(limit=1000)
    events_by_request = {}
    for event in events:
        request_id = event.get("tool_request_id")
        if request_id and request_id not in events_by_request:
            events_by_request[request_id] = event

    rows = []
    for record in requests_by_id.values():
        event = events_by_request.get(record.get("id"), {})
        rows.append(
            {
                **record,
                "latest_build_event": event,
                "effective_status": record.get("status", "proposed"),
            }
        )
    return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)[:limit]


def render_tool_proposal(record: dict) -> str:
    sources = record.get("data_sources") or []
    constraints = record.get("safety_constraints") or []
    lines = [
        "I do not have a reliable tool for that yet, so I created a tool proposal for Codex review.",
        "",
        f"Proposed tool: `{record['tool_name']}`",
        f"Purpose: {record.get('purpose') or 'N/D'}",
        f"Risk level: {record.get('risk_level') or 'medium'}",
        f"Status: {record.get('status')}",
        "",
        "Expected inputs:",
        json.dumps(record.get("inputs", {}), ensure_ascii=False, indent=2),
        "",
        "Needed data sources:",
        "\n".join(f"- {source}" for source in sources) if sources else "- N/D",
        "",
        "Output shape:",
        str(record.get("output_shape") or "N/D"),
        "",
        "Safety constraints:",
        "\n".join(f"- {item}" for item in constraints) if constraints else "- Must remain deterministic and auditable.",
        "",
        "Codex can review this request and decide whether to build it, improve an existing tool, or reject it.",
    ]
    return "\n".join(lines)


def load_generated_tools_registry() -> dict:
    if not GENERATED_TOOLS_REGISTRY_PATH.exists():
        return {"tools": {}}
    try:
        return json.loads(GENERATED_TOOLS_REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"tools": {}}


def save_generated_tools_registry(registry: dict) -> None:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_TOOLS_REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_tool_build_event(event: dict) -> None:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)
    with TOOL_BUILD_EVENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def save_feedback(text: str, meta: dict | None = None) -> dict:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)

    clean_text = clean(text, "").strip()
    if not clean_text:
        return {"ok": False, "error": "Feedback cannot be empty."}
    if len(clean_text) > 6000:
        clean_text = clean_text[:6000].rstrip() + "\n\n[truncated at 6000 characters]"

    meta = meta or {}
    feedback_id = f"fb_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    created_at = utc_now_iso()
    selected_member_id = clean(meta.get("selected_member_id"), "")
    source = clean(meta.get("source"), "chat")
    user_agent = clean(meta.get("user_agent"), "")

    if not FEEDBACK_INBOX_PATH.exists():
        FEEDBACK_INBOX_PATH.write_text(
            "# SECPHO Feedback Inbox\n\n"
            "Captured from the live chat app. Review newest appended entries and turn useful items into product work.\n\n",
            encoding="utf-8",
        )

    entry = [
        f"## {created_at} - {feedback_id}",
        "",
        f"- Source: {source}",
    ]
    if selected_member_id:
        entry.append(f"- Selected member id: {selected_member_id}")
    if user_agent:
        entry.append(f"- Browser: {user_agent[:180]}")
    entry.extend(["", "### Feedback", "", clean_text, ""])

    with FEEDBACK_INBOX_PATH.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry) + "\n")

    return {"ok": True, "id": feedback_id, "created_at": created_at}


def load_feedback_inbox() -> str:
    if not FEEDBACK_INBOX_PATH.exists():
        return "# SECPHO Feedback Inbox\n\nNo feedback captured yet.\n"
    return FEEDBACK_INBOX_PATH.read_text(encoding="utf-8")


def codex_review_and_build_tool(record: dict) -> dict:
    tool_name = normalize_tool_name(record.get("tool_name", ""))
    base_event = {
        "tool_request_id": record.get("id"),
        "tool_name": tool_name,
        "reviewed_at": utc_now_iso(),
        "reviewer": "codex_auto_gate",
    }

    allowed_builders = {
        "create_socio_metric_chart": {
            "executor": "generic_socio_metric_chart_v1",
            "description": "Create safe aggregated SVG charts for official socio metrics.",
            "allowed_metrics": [
                "readiness_score",
                "people_in_matcher",
                "registered_event_count",
                "event_interest_source_rows",
                "subscriber_contact_count",
                "retos_total",
            ],
        }
    }

    if tool_name not in allowed_builders:
        event = {
            **base_event,
            "decision": "queued",
            "reason": "No approved auto-builder template exists for this requested tool.",
        }
        append_tool_build_event(event)
        return event

    if record.get("risk_level") == "high":
        event = {
            **base_event,
            "decision": "queued",
            "reason": "High-risk tools require human review before build.",
        }
        append_tool_build_event(event)
        return event

    registry = load_generated_tools_registry()
    registry.setdefault("tools", {})
    registry["tools"][tool_name] = {
        "name": tool_name,
        "status": "built",
        "built_at": utc_now_iso(),
        "source_request_id": record.get("id"),
        **allowed_builders[tool_name],
        "safety_constraints": record.get("safety_constraints", []),
    }
    save_generated_tools_registry(registry)

    event = {
        **base_event,
        "decision": "built",
        "reason": "Matched approved safe auto-builder template.",
        "executor": allowed_builders[tool_name]["executor"],
    }
    append_tool_build_event(event)
    return event


def load_tool_build_events(limit: int = 50) -> list[dict]:
    if not TOOL_BUILD_EVENTS_PATH.exists():
        return []
    records = []
    for line in TOOL_BUILD_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records[-limit:][::-1]


def socio_metrics_table() -> pd.DataFrame:
    rows = pd.DataFrame(top_socios(limit=500, metric="readiness"))
    if rows.empty:
        return rows
    rows["retos_total"] = rows["retos_as_issuer_count"] + rows["retos_as_applicant_count"]
    return rows


def infer_chart_metrics(question: str) -> tuple[str, str]:
    lower = question.lower()
    x_metric = "readiness_score"
    y_metric = "registered_event_count"
    if "people" in lower or "profiles" in lower or "members" in lower:
        y_metric = "people_in_matcher"
    elif "subscriber" in lower or "contacts" in lower:
        y_metric = "subscriber_contact_count"
    elif "reto" in lower or "challenge" in lower:
        y_metric = "retos_total"
    elif "source rows" in lower:
        y_metric = "event_interest_source_rows"
    return x_metric, y_metric


def metric_label(metric: str) -> str:
    labels = {
        "readiness_score": "Readiness score",
        "people_in_matcher": "People profiles",
        "registered_event_count": "Event-interest events",
        "event_interest_source_rows": "Event-interest rows",
        "subscriber_contact_count": "Subscriber contacts",
        "retos_total": "Retos signals",
    }
    return labels.get(metric, metric)


def create_socio_metric_chart(question: str, limit: int = 12) -> dict:
    GENERATED_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    df = socio_metrics_table()
    if df.empty:
        return {"error": "No socio metrics available."}

    x_metric, y_metric = infer_chart_metrics(question)
    for col in [x_metric, y_metric]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    chart_df = (
        df.sort_values([y_metric, x_metric, "socio"], ascending=[False, False, True])
        .head(limit)
        .copy()
    )

    width = 920
    row_h = 34
    top = 94
    left = 250
    bar_max = 540
    height = top + row_h * len(chart_df) + 72
    max_value = max(float(chart_df[y_metric].max()), 1.0)

    title = f"Top socios by {metric_label(y_metric).lower()}"
    subtitle = "Aggregated official-socio data. Event metrics mean registration interest, not confirmed attendance."

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#111113"/>',
        f'<text x="28" y="38" fill="#f4f4f5" font-family="Arial" font-size="24" font-weight="700">{html.escape(title)}</text>',
        f'<text x="28" y="64" fill="#a6a7ab" font-family="Arial" font-size="13">{html.escape(subtitle)}</text>',
    ]

    for idx, row in enumerate(chart_df.itertuples(index=False), start=0):
        y = top + idx * row_h
        socio = clean(getattr(row, "socio"))
        value = float(getattr(row, y_metric))
        readiness = float(getattr(row, "readiness_score"))
        bar_w = int((value / max_value) * bar_max)
        color = "#00c3c7" if idx % 2 == 0 else "#ff3158"
        svg_lines.extend(
            [
                f'<text x="28" y="{y + 20}" fill="#f4f4f5" font-family="Arial" font-size="13">{idx + 1}. {html.escape(socio[:28])}</text>',
                f'<rect x="{left}" y="{y + 5}" width="{bar_w}" height="18" rx="5" fill="{color}" opacity="0.88"/>',
                f'<text x="{left + bar_w + 10}" y="{y + 19}" fill="#f4f4f5" font-family="Arial" font-size="13">{value:.0f}</text>',
                f'<text x="{width - 115}" y="{y + 19}" fill="#a6a7ab" font-family="Arial" font-size="12">R {readiness:.0f}/100</text>',
            ]
        )

    svg_lines.append("</svg>")
    artifact_id = datetime.now(timezone.utc).strftime("socio_chart_%Y%m%d%H%M%S%f")
    artifact_path = GENERATED_ARTIFACTS_DIR / f"{artifact_id}.svg"
    artifact_path.write_text("\n".join(svg_lines), encoding="utf-8")

    return {
        "tool_name": "create_socio_metric_chart",
        "artifact_path": str(artifact_path),
        "artifact_url": f"/artifacts/{artifact_path.name}",
        "title": title,
        "x_metric": x_metric,
        "y_metric": y_metric,
        "rows": chart_df[
            [
                "rank",
                "socio",
                "readiness_score",
                "people_in_matcher",
                "subscriber_contact_count",
                "registered_event_count",
                "event_interest_source_rows",
                "retos_total",
            ]
        ].to_dict(orient="records"),
        "caveat": "Event metrics indicate registration interest, not confirmed attendance.",
    }


def looks_like_missing_tool_request(question: str) -> bool:
    lower = question.lower()
    unsupported_terms = [
        "plot",
        "chart",
        "graph",
        "visualize",
        "visualise",
        "png",
        "pdf",
        "export",
        "download",
        "send email",
        "email all",
        "schedule",
        "calendar",
        "dashboard",
        "integrate",
        "integration",
        "predict",
        "forecast",
        "churn",
        "compare over time",
        "time series",
        "upload",
        "write to",
    ]
    return any(term in lower for term in unsupported_terms)


def heuristic_tool_proposal(question: str) -> dict:
    lower = question.lower()
    if any(term in lower for term in ["plot", "chart", "graph", "visualize", "visualise", "png"]):
        return {
            "tool_name": "create_socio_metric_chart",
            "purpose": "Create a chart from official socio metrics such as readiness, event interest, people profiles, and retos signals.",
            "inputs": {
                "x_metric": "string",
                "y_metric": "string",
                "group_by": "optional string",
                "output_format": "png | html",
            },
            "data_sources": [
                "official_socios_readiness.csv",
                "socio_event_interest_v1.csv",
                "person_profiles_v1.csv",
            ],
            "output_shape": "Chart artifact path plus the underlying ranked/aggregated data table.",
            "safety_constraints": [
                "Use aggregated socio-level data only by default.",
                "Do not expose personal emails in charts.",
                "Label event metrics as registration interest, not confirmed attendance.",
            ],
            "risk_level": "medium",
        }

    if any(term in lower for term in ["export", "download", "pdf"]):
        return {
            "tool_name": "export_grounded_results",
            "purpose": "Export a grounded answer, recommendation set, or report into an approved file format.",
            "inputs": {
                "result_type": "report | recommendations | socios | people",
                "format": "pdf | html | csv",
                "scope": "current_result | selected_person | selected_socio",
            },
            "data_sources": [
                "people_matches_v1_1_events.csv",
                "person_profiles_v1.csv",
                "socios_normalized.csv",
            ],
            "output_shape": "File path or download URL with export metadata.",
            "safety_constraints": [
                "Require authorization for exports containing personal contact data.",
                "Log user, timestamp, query, and exported fields.",
            ],
            "risk_level": "high",
        }

    return {
        "tool_name": "new_secpho_intelligence_tool",
        "purpose": "Support a SECPHO intelligence request that is not covered by the current tool registry.",
        "inputs": {"user_question": "string"},
        "data_sources": ["To be determined by Codex review"],
        "output_shape": "Structured JSON with evidence and caveats.",
        "safety_constraints": [
            "Codex must review before implementation.",
            "Use deterministic calculations for rankings and evidence.",
            "Do not expose sensitive data without authorization.",
        ],
        "risk_level": "medium",
    }


def person_list() -> pd.DataFrame:
    people = DATA["people"][
        ["member_id", "full_name", "email", "socio", "role_title", "technology_parents", "sector_parents"]
    ].copy()
    return people.sort_values(["socio", "full_name"])


def search_people(query: str) -> list[dict]:
    people = person_list()
    query = query.strip().lower()
    if query:
        mask = (
            people["full_name"].astype(str).str.lower().str.contains(query, na=False)
            | people["socio"].astype(str).str.lower().str.contains(query, na=False)
            | people["email"].astype(str).str.lower().str.contains(query, na=False)
            | people["technology_parents"].astype(str).str.lower().str.contains(query, na=False)
            | people["sector_parents"].astype(str).str.lower().str.contains(query, na=False)
        )
        people = people[mask]

    return [
        {
            "member_id": int(row["member_id"]),
            "name": clean(row["full_name"]),
            "socio": clean(row["socio"]),
            "role": clean(row["role_title"], ""),
            "email": clean(row["email"], ""),
        }
        for _, row in people.head(50).iterrows()
    ]


def find_people_rows(query: str, limit: int = 12) -> pd.DataFrame:
    people = person_list()
    query = query.strip().lower()
    if not query:
        return people.head(limit)

    mask = pd.Series(False, index=people.index)
    for token in [t for t in re.split(r"[^a-z0-9@áéíóúüñç.]+", query) if len(t) >= 2]:
        mask = mask | people["full_name"].astype(str).str.lower().str.contains(token, na=False, regex=False)
        mask = mask | people["socio"].astype(str).str.lower().str.contains(token, na=False, regex=False)
        mask = mask | people["email"].astype(str).str.lower().str.contains(token, na=False, regex=False)
        mask = mask | people["technology_parents"].astype(str).str.lower().str.contains(token, na=False, regex=False)
        mask = mask | people["sector_parents"].astype(str).str.lower().str.contains(token, na=False, regex=False)
    return people[mask].head(limit)


def find_people_by_company(company_query: str, limit: int = 20) -> pd.DataFrame:
    people = person_list()
    q = company_query.strip().lower()
    if not q:
        return pd.DataFrame(columns=people.columns)
    exactish = people[people["socio"].astype(str).str.lower().str.contains(q, na=False, regex=False)]
    if not exactish.empty:
        return exactish.head(limit)

    compact = re.sub(r"[^a-z0-9]+", "", q)
    if not compact:
        return exactish
    socio_compact = people["socio"].astype(str).str.lower().apply(lambda x: re.sub(r"[^a-z0-9]+", "", x))
    return people[socio_compact.str.contains(compact, na=False, regex=False)].head(limit)


def extract_company_query(question: str) -> str:
    q = question.strip()
    patterns = [
        r"who works (?:at|in|for) (.+?)\??$",
        r"who is in (.+?)\??$",
        r"people (?:at|in|from) (.+?)\??$",
        r"works in (.+?)\??$",
        r"qu[ií]en trabaja (?:en|para) (.+?)\??$",
        r"empresa (.+?)\??$",
    ]
    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ?.!")
    return q


def extract_person_query(question: str) -> str:
    q = question.strip()
    patterns = [
        r"(?:report|brief|briefing|one pager|one-pager)\s+(?:for|about|on)\s+(.+?)\??$",
        r"(?:recommendations|recommend|matches|intros|introductions)\s+(?:for|about|on)\s+(.+?)\??$",
        r"(?:informe|reporte)\s+(?:para|sobre|de)\s+(.+?)\??$",
        r"(?:recomienda|recomendaciones)\s+(?:para|sobre|de)\s+(.+?)\??$",
    ]
    for pattern in patterns:
        match = re.search(pattern, q, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ?.!:")
    return q


def rows_to_people(rows: pd.DataFrame) -> list[dict]:
    return [
        {
            "member_id": int(row["member_id"]),
            "name": clean(row["full_name"]),
            "socio": clean(row["socio"]),
            "role": clean(row["role_title"], ""),
            "email": clean(row["email"], ""),
            "technologies": clean(row.get("technology_parents"), ""),
            "sectors": clean(row.get("sector_parents"), ""),
        }
        for _, row in rows.iterrows()
    ]


def top_socios(limit: int = 5, metric: str = "readiness") -> list[dict]:
    readiness = DATA["readiness"].copy()
    if readiness.empty:
        return []

    coverage = DATA["people"].groupby("socio").size().reset_index(name="people_in_matcher")
    event_interest = DATA["socio_events"][
        ["socio", "registered_event_count", "event_interest_source_rows"]
    ].copy()

    rows = readiness.merge(coverage, on="socio", how="left")
    rows = rows.merge(event_interest, on="socio", how="left")
    for col in [
        "people_in_matcher",
        "registered_event_count",
        "event_interest_source_rows",
        "readiness_score",
        "subscriber_contact_count",
        "retos_as_issuer_count",
        "retos_as_applicant_count",
    ]:
        if col in rows.columns:
            rows[col] = pd.to_numeric(rows[col], errors="coerce").fillna(0)

    if metric == "event":
        rows = rows.sort_values(
            ["registered_event_count", "event_interest_source_rows", "readiness_score", "socio"],
            ascending=[False, False, False, True],
        )
        metric_label = "event registration-interest coverage"
    elif metric == "people":
        rows = rows.sort_values(
            ["people_in_matcher", "readiness_score", "subscriber_contact_count", "socio"],
            ascending=[False, False, False, True],
        )
        metric_label = "people profiles represented in the matcher"
    else:
        rows = rows.sort_values(
            [
                "readiness_score",
                "people_in_matcher",
                "subscriber_contact_count",
                "registered_event_count",
                "socio",
            ],
            ascending=[False, False, False, False, True],
        )
        metric_label = "Phase 1 readiness and available evidence"

    output = []
    for rank, (_, row) in enumerate(rows.head(limit).iterrows(), start=1):
        output.append(
            {
                "rank": rank,
                "socio": clean(row.get("socio")),
                "metric": metric_label,
                "readiness_score": float(row.get("readiness_score", 0)),
                "readiness_label": clean(row.get("readiness_label"), ""),
                "company_type": clean(row.get("company_type"), ""),
                "member_type": clean(row.get("member_type"), ""),
                "province": clean(row.get("province"), ""),
                "people_in_matcher": int(row.get("people_in_matcher", 0)),
                "subscriber_contact_count": int(row.get("subscriber_contact_count", 0)),
                "retos_as_issuer_count": int(row.get("retos_as_issuer_count", 0)),
                "retos_as_applicant_count": int(row.get("retos_as_applicant_count", 0)),
                "registered_event_count": int(row.get("registered_event_count", 0)),
                "event_interest_source_rows": int(row.get("event_interest_source_rows", 0)),
            }
        )
    return output


def search_socios(query: str = "", limit: int = 12) -> list[dict]:
    readiness = DATA["readiness"].copy()
    if readiness.empty:
        return []

    q = clean(query, "").lower()
    if q:
        mask = pd.Series(False, index=readiness.index)
        searchable_cols = [
            "socio",
            "company_type",
            "member_type",
            "province",
            "city",
            "readiness_label",
        ]
        for token in [t for t in re.split(r"[^a-z0-9áéíóúüñç]+", q) if len(t) >= 2]:
            for col in searchable_cols:
                if col in readiness.columns:
                    mask = mask | readiness[col].astype(str).str.lower().str.contains(token, na=False, regex=False)
        readiness = readiness[mask]

    coverage = DATA["people"].groupby("socio").size().reset_index(name="people_in_matcher")
    event_interest = DATA["socio_events"][
        ["socio", "registered_event_count", "event_interest_source_rows"]
    ].copy()
    rows = readiness.merge(coverage, on="socio", how="left").merge(event_interest, on="socio", how="left")
    rows = rows.fillna({"people_in_matcher": 0, "registered_event_count": 0, "event_interest_source_rows": 0})
    rows = rows.sort_values(["readiness_score", "people_in_matcher", "socio"], ascending=[False, False, True])

    output = []
    for _, row in rows.head(limit).iterrows():
        output.append(
            {
                "socio": clean(row.get("socio")),
                "company_type": clean(row.get("company_type"), ""),
                "member_type": clean(row.get("member_type"), ""),
                "province": clean(row.get("province"), ""),
                "readiness_score": float(row.get("readiness_score", 0) or 0),
                "readiness_label": clean(row.get("readiness_label"), ""),
                "people_in_matcher": int(row.get("people_in_matcher", 0) or 0),
                "subscriber_contact_count": int(row.get("subscriber_contact_count", 0) or 0),
                "registered_event_count": int(row.get("registered_event_count", 0) or 0),
                "event_interest_source_rows": int(row.get("event_interest_source_rows", 0) or 0),
                "retos_as_issuer_count": int(row.get("retos_as_issuer_count", 0) or 0),
                "retos_as_applicant_count": int(row.get("retos_as_applicant_count", 0) or 0),
            }
        )
    return output


def get_socio_profile(query: str) -> dict:
    socios = DATA["socios"].copy()
    readiness = DATA["readiness"].copy()
    if socios.empty:
        return {}

    q = clean(query, "").lower()
    if not q:
        return {}

    exact = socios[socios["socio"].astype(str).str.lower().eq(q)]
    contains = socios[socios["socio"].astype(str).str.lower().str.contains(q, na=False, regex=False)]
    row_df = exact if not exact.empty else contains
    if row_df.empty:
        compact = re.sub(r"[^a-z0-9]+", "", q)
        socio_compact = socios["socio"].astype(str).str.lower().apply(lambda x: re.sub(r"[^a-z0-9]+", "", x))
        row_df = socios[socio_compact.str.contains(compact, na=False, regex=False)]
    if row_df.empty:
        return {}

    row = row_df.iloc[0]
    readiness_row = readiness[readiness["socio"].astype(str).str.lower().eq(str(row["socio"]).lower())]
    ready = readiness_row.iloc[0] if not readiness_row.empty else {}
    people = rows_to_people(find_people_by_company(row["socio"], limit=10))
    event_row = DATA["socio_events"][DATA["socio_events"]["socio"].astype(str).str.lower().eq(str(row["socio"]).lower())]

    return {
        "socio": clean(row.get("socio")),
        "company_type": clean(row.get("company_type"), ""),
        "member_type": clean(row.get("member_type"), ""),
        "public_private": clean(row.get("public_private"), ""),
        "value_chain": clean(row.get("value_chain"), ""),
        "province": clean(row.get("province"), ""),
        "city": clean(row.get("city"), ""),
        "website": clean(row.get("website"), ""),
        "activity_summary": clean(row.get("activity_summary"), ""),
        "main_contact_name": clean(row.get("main_contact_name"), ""),
        "main_contact_email": clean(row.get("main_contact_email"), ""),
        "readiness_score": float(ready.get("readiness_score", 0) or 0) if isinstance(ready, pd.Series) else 0,
        "readiness_label": clean(ready.get("readiness_label"), "") if isinstance(ready, pd.Series) else "",
        "people": people,
        "event_interest": event_row.iloc[0].to_dict() if not event_row.empty else {},
    }


def render_top_socios(socios: list[dict]) -> str:
    if not socios:
        return "I could not load the official socios table."
    metric = socios[0]["metric"]
    lines = [f"Top {len(socios)} official socios by {metric}:"]
    for socio in socios:
        lines.append(
            f"- #{socio['rank']} {socio['socio']} "
            f"(readiness {socio['readiness_score']:.0f}/100, {socio['readiness_label']}): "
            f"{socio['people_in_matcher']} people profiles, "
            f"{socio['subscriber_contact_count']} subscriber contacts, "
            f"{socio['registered_event_count']} event-interest events, "
            f"{socio['retos_as_issuer_count'] + socio['retos_as_applicant_count']} retos signals."
        )
    lines.append("This is a deterministic company ranking from available data coverage, not an LLM opinion.")
    return "\n".join(lines)


def exact_or_best_person(query: str) -> int | None:
    rows = find_people_rows(query, limit=8)
    if rows.empty:
        return None
    q = query.strip().lower()
    for _, row in rows.iterrows():
        if q and q in str(row["full_name"]).lower():
            return int(row["member_id"])
    return int(rows.iloc[0]["member_id"])


def get_person(member_id: int) -> dict:
    people = DATA["people"]
    row = people[people["member_id"] == member_id]
    if row.empty:
        return {}
    person = row.iloc[0]
    event_row = DATA["person_events"][DATA["person_events"]["member_id"] == member_id]
    events = ""
    if not event_row.empty:
        events = clean(event_row.iloc[0].get("registered_event_titles"), "")

    return {
        "member_id": int(person["member_id"]),
        "name": clean(person["full_name"]),
        "email": clean(person["email"], ""),
        "socio": clean(person["socio"]),
        "role": clean(person.get("role_title"), ""),
        "technologies": clean(person.get("technology_parents"), ""),
        "sectors": clean(person.get("sector_parents"), ""),
        "ambitos": clean(person.get("ambitos"), ""),
        "needs": clean(person.get("needs_general"), ""),
        "municipality": clean(person.get("municipality"), ""),
        "province": clean(person.get("province"), ""),
        "country": clean(person.get("country"), ""),
        "hobbies": clean(person.get("hobbies"), ""),
        "sports": clean(person.get("sports"), ""),
        "instruments": clean(person.get("instruments"), ""),
        "languages": clean(person.get("languages"), ""),
        "university": clean(person.get("university"), ""),
        "profile_text": clean(person.get("profile_text"), ""),
        "readiness_score": clean(person.get("readiness_score"), "0"),
        "readiness_label": clean(person.get("readiness_label"), ""),
        "events": events,
    }


def get_recommendations(member_id: int, limit: int = 5) -> list[dict]:
    matches = DATA["matches"]
    rows = (
        matches[matches["target_member_id"] == member_id]
        .sort_values("final_score", ascending=False)
        .head(limit)
    )
    return [
        {
            "rank": index + 1,
            "candidate_member_id": int(row["candidate_member_id"]),
            "name": clean(row["candidate_name"]),
            "socio": clean(row["candidate_socio"]),
            "role": clean(row.get("candidate_role"), ""),
            "email": clean(row.get("candidate_email"), ""),
            "final_score": float(row["final_score"]),
            "profile_similarity": float(row["profile_similarity"]),
            "structured_overlap": float(row["structured_overlap"]),
            "needs_overlap": float(row["needs_overlap"]),
            "event_interest_overlap_score": float(row["event_interest_overlap_score"]),
            "location_overlap_score": float(row.get("location_overlap_score", 0) or 0),
            "personal_affinity_score": float(row.get("personal_affinity_score", 0) or 0),
            "confidence_score": float(row["confidence_score"]),
            "shared_technologies": clean(row.get("shared_technologies"), ""),
            "shared_sectors": clean(row.get("shared_sectors"), ""),
            "shared_ambitos": clean(row.get("shared_ambitos"), ""),
            "shared_needs": clean(row.get("shared_needs"), ""),
            "shared_location": clean(row.get("shared_location"), ""),
            "shared_hobbies": clean(row.get("shared_hobbies"), ""),
            "shared_sports": clean(row.get("shared_sports"), ""),
            "shared_instruments": clean(row.get("shared_instruments"), ""),
            "shared_languages": clean(row.get("shared_languages"), ""),
            "shared_registered_events": clean(row.get("shared_registered_events"), ""),
            "event_interest_evidence_level": clean(row.get("event_interest_evidence_level"), ""),
            "event_interest_note": clean(row.get("event_interest_note"), ""),
        }
        for index, (_, row) in enumerate(rows.iterrows())
    ]


def llm_payload_for_person(member_id: int) -> dict:
    person = get_person(member_id)
    recs = get_recommendations(member_id, 5)
    return {
        "principle": "Math decides. The LLM explains.",
        "scope": "Phase 1 recommends only people linked to official SECPHO socios.",
        "event_signal_warning": (
            "Event overlap indicates shared SECPHO registration interest, "
            "not confirmed attendance."
        ),
        "person": person,
        "recommendations_ranked_by_model": recs,
        "scoring_formula": {
            "profile_similarity": 0.44,
            "structured_overlap": 0.24,
            "needs_overlap": 0.10,
            "event_interest_overlap_score": 0.14,
            "location_overlap_score": 0.06,
            "personal_affinity_score": 0.02,
        },
    }


def report_for_person(member_id: int) -> str:
    person = get_person(member_id)
    recs = get_recommendations(member_id, 5)
    if not person:
        return "No person found."

    lines = [
        f"# SECPHO Matchmaker Brief: {person['name']}",
        "",
        f"**Socio:** {person['socio']}",
        f"**Role:** {person['role'] or 'N/D'}",
        f"**Email:** {person['email'] or 'N/D'}",
        f"**Location:** {', '.join([p for p in [person['municipality'], person['province'], person['country']] if p]) or 'N/D'}",
        f"**Readiness:** {person['readiness_label']} ({person['readiness_score']}/100)",
        "",
        "## Profile Snapshot",
        "",
        f"- Technologies: {person['technologies'] or 'N/D'}",
        f"- Sectors: {person['sectors'] or 'N/D'}",
        f"- Ambitos: {person['ambitos'] or 'N/D'}",
        f"- Needs: {person['needs'] or 'N/D'}",
        f"- Hobbies: {person['hobbies'] or 'N/D'}",
        f"- Sports: {person['sports'] or 'N/D'}",
        f"- Languages: {person['languages'] or 'N/D'}",
        "",
        "## Event Interest",
        "",
        (
            f"{person['name']} has registration-interest evidence for: {person['events']}."
            if person["events"]
            else "No person-level event registration-interest profile is available for this contact."
        ),
        "",
        "Event signal means shared SECPHO registration interest. It does not prove confirmed attendance.",
        "",
        "## Recommended Introductions",
        "",
    ]

    for rec in recs:
        evidence = []
        if rec["shared_technologies"]:
            evidence.append(f"shared technologies: {rec['shared_technologies']}")
        if rec["shared_sectors"]:
            evidence.append(f"shared sectors: {rec['shared_sectors']}")
        if rec["shared_needs"]:
            evidence.append(f"shared needs: {rec['shared_needs']}")
        if rec["shared_location"]:
            evidence.append(f"location: {rec['shared_location']}")
        if rec["shared_hobbies"]:
            evidence.append(f"shared hobbies: {rec['shared_hobbies']}")
        if rec["shared_sports"]:
            evidence.append(f"shared sports: {rec['shared_sports']}")
        if rec["shared_languages"]:
            evidence.append(f"shared languages: {rec['shared_languages']}")
        if rec["shared_registered_events"]:
            evidence.append(f"shared event interest: {rec['shared_registered_events']}")

        evidence_text = "; ".join(evidence) if evidence else "limited explicit overlap; review profile context."
        lines.extend(
            [
                f"### {rec['rank']}. {rec['name']} - {rec['socio']}",
                "",
                f"**Score:** {rec['final_score']:.4f} | **Confidence:** {rec['confidence_score']:.2f}",
                "",
                f"Why this match: {evidence_text}",
                "",
                (
                    "Suggested positioning: introduce this as a targeted SECPHO connection based on "
                    "profile fit, structured technology/sector evidence, and available event-interest signals."
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## How To Read This",
            "",
            "The ranking is produced by the deterministic People Matcher V1.1 model. "
            "It combines profile similarity, structured overlap, needs overlap, event-interest evidence, "
            "location proximity, and light personal-affinity context. "
            "The LLM or report writer should explain these results, not invent or reorder them.",
        ]
    )
    return "\n".join(lines)


def llm_report_for_person(member_id: int) -> dict:
    payload = llm_payload_for_person(member_id)
    local_report = report_for_person(member_id)

    prompt = (
        "Create a polished SECPHO internal one-page matchmaker briefing from this JSON. "
        "Keep the exact recommendation order. Mention the score and 1-2 evidence points "
        "for each recommendation. Include a concise executive summary, introduction "
        "positioning, recommended next action, and the event-signal caveat.\n\n"
        f"JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    text, mode = call_llm(prompt)
    if text:
        return {"mode": mode, "markdown": text}

    fallback = (
        "# LLM-Style Briefing Draft\n\n"
        f"**Mode:** grounded fallback ({mode}).\n\n"
        "This is the same structure the LLM receives: deterministic recommendations, "
        "score evidence, introduction positioning, and caveats.\n\n"
        + local_report
    )
    return {"mode": mode, "markdown": fallback}


def answer_question(question: str) -> str:
    q = question.lower().strip()
    data = DATA

    if not q:
        return "Ask about a person, socio, event signal, counts, or recommendation logic."

    if "how many" in q or "count" in q or "cuantos" in q or "cuántos" in q:
        return (
            f"Current MVP data: {len(data['people'])} official-socio people in the matcher, "
            f"{data['people']['socio'].nunique()} official socios represented by people, "
            f"{len(data['matches'])} recommendation rows, "
            f"{len(data['event_regs'])} normalized event registration rows, "
            f"{len(data['person_events'])} person event-interest profiles, and "
            f"{len(data['socio_events'])} socio event-interest profiles."
        )

    if "event" in q or "attendance" in q or "asistencia" in q:
        top = data["socio_events"].sort_values("registered_event_count", ascending=False).head(8)
        names = ", ".join(
            f"{clean(row['socio'])} ({int(row['registered_event_count'])})"
            for _, row in top.iterrows()
        )
        return (
            "The event signal is registration interest, not confirmed attendance. "
            f"Top socios by event-interest coverage are: {names}."
        )

    if "weight" in q or "score" in q or "scoring" in q:
        return (
            "People Matcher V1.1 score = 0.44 profile similarity + 0.24 structured overlap "
            "+ 0.10 needs overlap + 0.14 event_interest_overlap_score "
            "+ 0.06 location_overlap_score + 0.02 personal_affinity_score. "
            "Readiness is shown as confidence, not as a ranking override."
        )

    if "official" in q or "socio" in q:
        return (
            "Phase 1 only recommends people linked to official socios. Wider subscribers, contacts, "
            "and event registrants enrich evidence but are not primary recommendation targets."
        )

    # Person lookup fallback.
    tokens = [t for t in re.split(r"[^a-z0-9@.]+", q) if len(t) >= 3]
    people = person_list()
    mask = pd.Series(False, index=people.index)
    for token in tokens:
        mask = mask | people["full_name"].astype(str).str.lower().str.contains(token, na=False)
        mask = mask | people["socio"].astype(str).str.lower().str.contains(token, na=False)
        mask = mask | people["email"].astype(str).str.lower().str.contains(token, na=False)

    found = people[mask].head(5)
    if not found.empty:
        bits = [
            f"{clean(row['full_name'])} ({clean(row['socio'])}, {clean(row['role_title'], 'role N/D')})"
            for _, row in found.iterrows()
        ]
        return "I found these related people: " + "; ".join(bits) + ". Select one from search to generate recommendations or a report."

    return (
        "I can answer MVP questions about matcher counts, event-interest evidence, official-socio scope, "
        "scoring logic, and people/socio lookup. For this demo, ranking still comes from the model outputs."
    )


def llm_answer_question(question: str, member_id: int | None = None) -> dict:
    context = {
        "question": question,
        "mvp_counts": {
            "people_in_matcher": len(DATA["people"]),
            "official_socios_represented_by_people": int(DATA["people"]["socio"].nunique()),
            "recommendation_rows": len(DATA["matches"]),
            "event_registration_rows": len(DATA["event_regs"]),
            "person_event_interest_profiles": len(DATA["person_events"]),
            "socio_event_interest_profiles": len(DATA["socio_events"]),
        },
        "scoring_formula": {
            "profile_similarity": 0.50,
            "structured_overlap": 0.25,
            "needs_overlap": 0.10,
            "event_interest_overlap_score": 0.15,
        },
        "rules": [
            "Only official-socio-linked people are recommendation targets in Phase 1.",
            "Do not recommend people from the same socio.",
            "Event signal is registration interest, not confirmed attendance.",
            "LLM explains and decorates; it does not match or rank.",
        ],
    }
    if member_id:
        context["selected_person_context"] = llm_payload_for_person(member_id)

    prompt = (
        "Answer the user question using only this grounded SECPHO MVP context. "
        "If the question asks for recommendations and selected_person_context is present, "
        "use the existing ranked recommendations without changing order.\n\n"
        f"CONTEXT:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )
    text, mode = call_llm(prompt, max_output_tokens=1800)
    if text:
        return {"mode": mode, "answer": text}
    return {"mode": mode, "answer": answer_question(question)}


def render_people_list(people: list[dict]) -> str:
    if not people:
        return "I could not find official-socio people matching that."
    lines = ["Here are the official-socio people I found:"]
    for person in people:
        role = f", {person['role']}" if person.get("role") else ""
        lines.append(
            f"- {person['name']} - {person['socio']}{role} "
            f"[person:{person['member_id']}]"
        )
    lines.append("You can ask me for recommendations or a report for any of them.")
    return "\n".join(lines)


def render_recommendations(member_id: int) -> str:
    person = get_person(member_id)
    recs = get_recommendations(member_id, 5)
    if not person:
        return "I could not find that person."
    lines = [f"Top model-ranked recommendations for {person['name']}:"]
    for rec in recs:
        evidence = []
        if rec["shared_technologies"]:
            evidence.append(f"tech: {rec['shared_technologies']}")
        if rec["shared_sectors"]:
            evidence.append(f"sectors: {rec['shared_sectors']}")
        if rec["shared_location"]:
            evidence.append(f"location: {rec['shared_location']}")
        if rec["shared_hobbies"]:
            evidence.append(f"hobbies: {rec['shared_hobbies']}")
        if rec["shared_registered_events"]:
            evidence.append(f"event interest: {rec['shared_registered_events']}")
        evidence_text = "; ".join(evidence) if evidence else "profile/context similarity"
        lines.append(
            f"- #{rec['rank']} {rec['name']} - {rec['socio']} "
            f"(score {rec['final_score']:.4f}): {evidence_text}"
        )
    lines.append("Event interest means registration interest, not confirmed attendance.")
    return "\n".join(lines)


def decorate_grounded_answer(task: str, payload: dict, fallback_text: str) -> tuple[str, str]:
    prompt = (
        "Write the user-facing chat answer for this SECPHO intelligence app. "
        "Use only the supplied deterministic payload. Keep any recommendation order exactly as given. "
        "If person IDs appear, preserve them in [person:ID] form so the UI can attach actions.\n\n"
        f"TASK: {task}\n\nPAYLOAD:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    text, mode = call_llm(prompt, max_output_tokens=1800)
    return (text or fallback_text, mode)


def tool_answer(action: str, args: dict, selected_member_id: int | None = None) -> dict | None:
    args = args or {}

    if action == "propose_tool":
        proposal = {
            "tool_name": args.get("tool_name", "proposed_tool"),
            "purpose": args.get("purpose", ""),
            "inputs": args.get("inputs", {}),
            "data_sources": args.get("data_sources", []),
            "output_shape": args.get("output_shape", args.get("output", "")),
            "safety_constraints": args.get("safety_constraints", []),
            "risk_level": args.get("risk_level", "medium"),
        }
        question = clean(args.get("question"), "")
        record = save_missing_tool_request(question, proposal, {"action": action, "args": args})
        build_event = codex_review_and_build_tool(record)
        if build_event.get("decision") == "built" and record["tool_name"] == "create_socio_metric_chart":
            update_tool_request_status(
                record["id"],
                "built",
                f"Auto-built with executor {build_event.get('executor')}.",
            )
            record["status"] = "built"
            chart_result = create_socio_metric_chart(question)
            answer = (
                "I did not have that exact capability, so I created a safe tool for it and ran it on your question.\n\n"
                f"Created tool: `{record['tool_name']}`\n"
                f"Status: built and executed\n"
                f"Request ID: {record['id']}\n\n"
                f"Chart: {chart_result.get('artifact_url')}\n\n"
                f"{chart_result.get('title')}\n"
                f"Caveat: {chart_result.get('caveat')}\n\n"
                "Top rows:\n"
            )
            for row in chart_result.get("rows", [])[:8]:
                answer += (
                    f"- {row['socio']}: {metric_label(chart_result['y_metric'])} "
                    f"{float(row[chart_result['y_metric']]):.0f}, readiness "
                    f"{float(row['readiness_score']):.0f}/100\n"
                )
            return {
                "answer": answer,
                "mode": "tool_built_and_executed",
                "selected_member_id": selected_member_id,
                "kind": "tool_built",
                "tool_request": record,
                "build_event": build_event,
                "tool_result": chart_result,
                "llm_available": openai_available(),
            }

        queued_status = "queued_for_codex_review"
        if build_event.get("decision") == "queued":
            queued_status = "queued_for_codex_review"
        elif build_event.get("decision") in {"rejected", "blocked"}:
            queued_status = build_event.get("decision")
        update_tool_request_status(
            record["id"],
            queued_status,
            build_event.get("reason", ""),
        )
        record["status"] = queued_status
        record["codex_review_notes"] = build_event.get("reason", "")
        queue_message = (
            "I do not have a reliable tool for that yet. I created a reviewed tool request and queued it for Codex.\n\n"
            f"Request ID: {record['id']}\n"
            f"Proposed tool: `{record['tool_name']}`\n"
            f"Status: {queued_status}\n"
            f"Reason: {build_event.get('reason', 'Pending Codex review.')}\n\n"
            "For fast, approved tool templates I can create and run the tool immediately. "
            "This one needs a real Codex review before it can be shipped safely."
        )
        return {
            "answer": queue_message + "\n\n" + render_tool_proposal(record),
            "mode": "tool_proposal_stored",
            "selected_member_id": selected_member_id,
            "kind": "tool_proposal",
            "tool_request": record,
            "build_event": build_event,
            "llm_available": openai_available(),
        }

    if action == "search_people":
        company = clean(args.get("company"), "")
        query = " ".join(
            clean(args.get(k), "")
            for k in ["query", "name", "technology", "sector", "role"]
            if clean(args.get(k), "")
        )
        rows = find_people_by_company(company, limit=20) if company else find_people_rows(query, limit=20)
        people = rows_to_people(rows)
        fallback = render_people_list(people)
        answer, mode = decorate_grounded_answer(
            "List matching official-socio people",
            {"action": action, "args": args, "people": people, "scope": "official-socio people only"},
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": people[0]["member_id"] if len(people) == 1 else selected_member_id,
            "kind": "people",
            "people": people,
            "llm_available": openai_available(),
        }

    if action == "search_socios":
        query = " ".join(
            clean(args.get(k), "")
            for k in ["query", "name", "province", "company_type", "member_type"]
            if clean(args.get(k), "")
        )
        socios = search_socios(query, limit=12)
        fallback = "Official socios found:\n" + "\n".join(
            f"- {s['socio']} ({s['readiness_score']:.0f}/100 readiness, {s['people_in_matcher']} people profiles)"
            for s in socios
        )
        answer, mode = decorate_grounded_answer(
            "List matching official socios/companies",
            {"action": action, "args": args, "socios": socios},
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected_member_id,
            "kind": "socios",
            "socios": socios,
            "llm_available": openai_available(),
        }

    if action == "rank_socios":
        metric = clean(args.get("metric"), "readiness").lower()
        if metric not in {"readiness", "event", "people"}:
            metric = "readiness"
        try:
            limit = int(args.get("limit", 5) or 5)
        except (TypeError, ValueError):
            limit = 5
        socios = top_socios(limit=max(1, min(limit, 20)), metric=metric)
        fallback = render_top_socios(socios)
        answer, mode = decorate_grounded_answer(
            "Explain deterministic top official socios ranking",
            {
                "action": action,
                "args": args,
                "ranking_basis": socios[0]["metric"] if socios else metric,
                "socios": socios,
                "important_caveat": "This is a deterministic data ranking, not an LLM opinion.",
            },
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected_member_id,
            "kind": "socios",
            "socios": socios,
            "llm_available": openai_available(),
        }

    if action == "get_person_profile":
        member_id = args.get("member_id") or selected_member_id
        if not member_id:
            member_id = exact_or_best_person(clean(args.get("query"), ""))
        person = get_person(int(member_id)) if member_id else {}
        fallback = json.dumps(person, ensure_ascii=False, indent=2) if person else "I could not find that person."
        answer, mode = decorate_grounded_answer(
            "Explain one official-socio person profile",
            {"action": action, "args": args, "person": person},
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": int(member_id) if member_id else selected_member_id,
            "kind": "person_profile",
            "llm_available": openai_available(),
        }

    if action == "get_socio_profile":
        profile = get_socio_profile(clean(args.get("query") or args.get("name"), ""))
        fallback = json.dumps(profile, ensure_ascii=False, indent=2) if profile else "I could not find that socio."
        answer, mode = decorate_grounded_answer(
            "Explain one official socio/company profile",
            {"action": action, "args": args, "socio_profile": profile},
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected_member_id,
            "kind": "socio_profile",
            "llm_available": openai_available(),
        }

    if action == "recommend_contacts":
        member_id = args.get("member_id") or selected_member_id
        if not member_id:
            member_id = exact_or_best_person(clean(args.get("query"), ""))
        if not member_id:
            return None
        fallback = render_recommendations(int(member_id))
        payload = llm_payload_for_person(int(member_id))
        answer, mode = decorate_grounded_answer("Explain model-ranked recommendations", payload, fallback)
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": int(member_id),
            "kind": "recommendations",
            "llm_available": openai_available(),
        }

    if action == "generate_report":
        member_id = args.get("member_id") or selected_member_id
        if not member_id:
            member_id = exact_or_best_person(clean(args.get("query"), ""))
        if not member_id:
            return None
        report = llm_report_for_person(int(member_id))
        return {
            "answer": report["markdown"],
            "mode": report["mode"],
            "selected_member_id": int(member_id),
            "kind": "report",
            "llm_available": openai_available(),
        }

    if action == "general_answer":
        answer = llm_answer_question(clean(args.get("question"), ""), selected_member_id)
        return {
            "answer": answer["answer"],
            "mode": answer["mode"],
            "selected_member_id": selected_member_id,
            "kind": "general",
            "llm_available": openai_available(),
        }

    return None


def chat_flow(question: str, selected_member_id: int | None = None) -> dict:
    q = question.strip()
    lower = q.lower()

    route = llm_route_question(q, selected_member_id)
    if (
        route.get("action") == "general_answer"
        and str(route.get("router_mode", "")).startswith("fallback_")
        and looks_like_missing_tool_request(q)
    ):
        route = {
            "action": "propose_tool",
            "args": {
                "question": q,
                **heuristic_tool_proposal(q),
            },
            "router_mode": route.get("router_mode", "heuristic_missing_tool"),
        }
    if route.get("action") == "propose_tool":
        route.setdefault("args", {})
        route["args"].setdefault("question", q)
    routed = tool_answer(route.get("action", ""), route.get("args", {}), selected_member_id)
    if routed:
        routed["router"] = route
        routed["mode"] = f"{routed['mode']} via router:{route.get('action')}"
        return routed

    report_intent = any(word in lower for word in ["report", "brief", "one pager", "one-pager", "informe", "briefing"])
    rec_intent = any(word in lower for word in ["recommend", "match", "intro", "introduction", "recomienda", "matchmaking"])
    people_intent = any(phrase in lower for phrase in ["who works", "who is in", "people in", "works in", "company", "empresa", "quien trabaja", "quién trabaja"])
    socio_ranking_intent = (
        ("top" in lower or "ranking" in lower or "best" in lower or "mejores" in lower)
        and any(word in lower for word in ["socios", "companies", "company", "empresas"])
    )
    general_model_intent = any(
        phrase in lower
        for phrase in [
            "score",
            "scoring",
            "logic",
            "weight",
            "how many",
            "count",
            "event signal",
            "attendance",
            "official socio",
            "math decides",
        ]
    )

    target_member_id = selected_member_id
    if report_intent or rec_intent:
        found_id = exact_or_best_person(extract_person_query(q))
        if found_id:
            target_member_id = found_id

    if report_intent and target_member_id:
        report = llm_report_for_person(target_member_id)
        return {
            "answer": report["markdown"],
            "mode": report["mode"],
            "selected_member_id": target_member_id,
            "kind": "report",
            "llm_available": openai_available(),
        }

    if rec_intent and target_member_id:
        fallback = render_recommendations(target_member_id)
        payload = llm_payload_for_person(target_member_id)
        answer, mode = decorate_grounded_answer("Explain model-ranked recommendations", payload, fallback)
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": target_member_id,
            "kind": "recommendations",
            "llm_available": openai_available(),
        }

    if socio_ranking_intent:
        metric = "readiness"
        if "event" in lower or "attendance" in lower or "registration" in lower:
            metric = "event"
        elif "people" in lower or "member" in lower or "profiles" in lower:
            metric = "people"
        socios = top_socios(limit=5, metric=metric)
        fallback = render_top_socios(socios)
        answer, mode = decorate_grounded_answer(
            "Explain deterministic top official socios ranking",
            {
                "question": q,
                "ranking_basis": socios[0]["metric"] if socios else metric,
                "socios": socios,
                "important_caveat": (
                    "This ranks official socios using available data coverage/readiness signals. "
                    "It is not a business-value judgment unless the user chooses that metric."
                ),
            },
            fallback,
        )
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected_member_id,
            "kind": "socios",
            "socios": socios,
            "llm_available": openai_available(),
        }

    if general_model_intent:
        answer = llm_answer_question(q, selected_member_id)
        return {
            "answer": answer["answer"],
            "mode": answer["mode"],
            "selected_member_id": selected_member_id,
            "kind": "general",
            "llm_available": openai_available(),
        }

    if people_intent:
        company_query = extract_company_query(q)
        rows = find_people_by_company(company_query, limit=20)
        if rows.empty:
            rows = find_people_rows(company_query, limit=12)
        people = rows_to_people(rows)
        fallback = render_people_list(people)
        answer, mode = decorate_grounded_answer(
            "List matching official-socio people",
            {
                "question": q,
                "interpreted_company_query": company_query,
                "people": people,
                "scope": "official-socio people only",
            },
            fallback,
        )
        selected = people[0]["member_id"] if len(people) == 1 else selected_member_id
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected,
            "kind": "people",
            "people": people,
            "llm_available": openai_available(),
        }

    if find_people_rows(q, limit=1).shape[0] > 0:
        people = rows_to_people(find_people_rows(q, limit=12))
        fallback = render_people_list(people)
        answer, mode = decorate_grounded_answer(
            "List matching official-socio people",
            {"question": q, "people": people, "scope": "official-socio people only"},
            fallback,
        )
        selected = people[0]["member_id"] if len(people) == 1 else selected_member_id
        return {
            "answer": answer,
            "mode": mode,
            "selected_member_id": selected,
            "kind": "people",
            "people": people,
            "llm_available": openai_available(),
        }

    answer = llm_answer_question(q, selected_member_id)
    return {
        "answer": answer["answer"],
        "mode": answer["mode"],
        "selected_member_id": selected_member_id,
        "kind": "general",
        "llm_available": openai_available(),
    }


def markdown_to_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"^# (.*)$", r"<h1>\1</h1>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^## (.*)$", r"<h2>\1</h2>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^### (.*)$", r"<h3>\1</h3>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"^- (.*)$", r"<li>\1</li>", escaped, flags=re.MULTILINE)
    escaped = escaped.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<p>{escaped}</p>"


def markdown_to_chat_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\[person:(\d+)\]", r'<button class="inline-action" onclick="setPerson(\1)">select</button>', escaped)
    escaped = re.sub(
        r"(/artifacts/[A-Za-z0-9_.-]+)",
        r'<a href="\1" target="_blank" style="color:var(--brand)">\1</a>',
        escaped,
    )
    escaped = re.sub(r"^# (.*)$", r"<h1>\1</h1>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^## (.*)$", r"<h2>\1</h2>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"^### (.*)$", r"<h3>\1</h3>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"^- (.*)$", r"<li>\1</li>", escaped, flags=re.MULTILINE)
    escaped = escaped.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<p>{escaped}</p>"


LOGIN_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SECPHO Intelligence Login</title>
  <style>
    :root {
      --bg: #111113;
      --panel: #1b1c20;
      --ink: #f4f4f5;
      --muted: #a6a7ab;
      --line: #303136;
      --brand: #00c3c7;
      --hot: #ff3158;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      background:
        radial-gradient(circle at 18% 12%, rgba(0,195,199,.14), transparent 30%),
        radial-gradient(circle at 84% 18%, rgba(255,49,88,.12), transparent 28%),
        var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    }
    main {
      width: min(420px, calc(100vw - 32px));
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(27,28,32,.94);
      padding: 24px;
      box-shadow: 0 20px 70px rgba(0,0,0,.34);
    }
    img { width: 132px; display: block; margin-bottom: 24px; }
    h1 { font-size: 22px; margin: 0 0 8px; }
    p { color: var(--muted); line-height: 1.45; margin: 0 0 18px; }
    label { display: block; color: var(--muted); font-size: 13px; margin-bottom: 7px; }
    input {
      width: 100%;
      min-height: 44px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111113;
      color: var(--ink);
      font: inherit;
      padding: 10px 12px;
    }
    button {
      width: 100%;
      margin-top: 14px;
      min-height: 44px;
      border: 0;
      border-radius: 8px;
      background: var(--brand);
      color: #061112;
      cursor: pointer;
      font: inherit;
      font-weight: 760;
    }
    .error {
      min-height: 20px;
      color: #ff8aa0;
      font-size: 13px;
      margin-top: 12px;
    }
  </style>
</head>
<body>
  <main>
    <img src="/static/secpho_logo_negative.png" alt="secpho">
    <h1>SECPHO Intelligence</h1>
    <p>This workspace is protected. Sign in to continue.</p>
    <form method="post" action="/login">
      <label for="password">Access password</label>
      <input id="password" name="password" type="password" autocomplete="current-password" autofocus>
      <button type="submit">Sign in</button>
      <div class="error">{{ERROR}}</div>
    </form>
  </main>
</body>
</html>
"""


INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SECPHO Matchmaker MVP</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5d6875;
      --line: #d8dee6;
      --soft: #f4f7f9;
      --panel: #ffffff;
      --brand: #007f8c;
      --accent: #d6422b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #eef2f4;
    }
    header {
      height: 62px;
      background: #101820;
      color: white;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 22px;
      border-bottom: 4px solid var(--brand);
    }
    header h1 { font-size: 20px; margin: 0; letter-spacing: 0; }
    header span { color: #c8d3dc; font-size: 13px; }
    main {
      display: grid;
      grid-template-columns: 320px minmax(420px, 1fr) 360px;
      gap: 14px;
      padding: 14px;
      height: calc(100vh - 62px);
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 0;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .section-head {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfd;
      font-weight: 700;
    }
    .content { padding: 14px; overflow: auto; }
    input, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 4px;
      padding: 10px;
      font: inherit;
    }
    button {
      border: 0;
      background: var(--brand);
      color: white;
      border-radius: 4px;
      padding: 9px 12px;
      font-weight: 700;
      cursor: pointer;
    }
    button.secondary { background: #33414f; }
    .person-row {
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
      cursor: pointer;
    }
    .person-row:hover { background: var(--soft); }
    .name { font-weight: 700; }
    .meta { color: var(--muted); font-size: 13px; margin-top: 3px; }
    .score {
      display: inline-block;
      min-width: 70px;
      padding: 4px 7px;
      background: #e7f4f5;
      border: 1px solid #b9dfe3;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 700;
      color: #005e69;
    }
    .rec {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 10px;
    }
    .tabs { display: flex; gap: 8px; margin-bottom: 12px; }
    .tabs button { background: #33414f; }
    .tabs button.active { background: var(--accent); }
    .note {
      background: #fff6e9;
      border: 1px solid #f1c27d;
      border-radius: 4px;
      padding: 10px;
      color: #66410d;
      font-size: 13px;
      margin-bottom: 10px;
    }
    .report {
      line-height: 1.45;
      font-size: 14px;
    }
    .report h1 { font-size: 24px; margin: 0 0 8px; }
    .report h2 { font-size: 17px; margin: 18px 0 8px; border-top: 1px solid var(--line); padding-top: 12px; }
    .report h3 { font-size: 15px; margin: 14px 0 6px; }
    .chat-log {
      flex: 1;
      overflow: auto;
      padding: 14px;
      background: #f9fbfc;
    }
    .msg {
      padding: 9px 10px;
      border-radius: 6px;
      margin-bottom: 9px;
      line-height: 1.35;
      font-size: 14px;
    }
    .user { background: #dceff1; }
    .bot { background: white; border: 1px solid var(--line); }
    .chat-compose { padding: 12px; border-top: 1px solid var(--line); }
    @media (max-width: 1100px) {
      main { grid-template-columns: 1fr; height: auto; }
      section { min-height: 360px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>SECPHO Matchmaker MVP</h1>
    <span>People Matcher V1.1 · Math decides, assistant explains</span>
  </header>
  <main>
    <section>
      <div class="section-head">Search Official-Socio People</div>
      <div class="content">
        <input id="search" placeholder="Search person, socio, email, tech..." value="David Santana">
        <div id="people"></div>
      </div>
    </section>

    <section>
      <div class="section-head" id="selectedTitle">Recommendations</div>
      <div class="content">
        <div class="note">Event signal = shared SECPHO registration interest, not confirmed attendance.</div>
        <div class="tabs">
          <button id="tabRecs" class="active" onclick="showTab('recs')">Recommendations</button>
          <button id="tabReport" onclick="showTab('report')">Report Draft</button>
          <button id="llmButton" onclick="generateLlmReport()">Generate With LLM</button>
        </div>
        <div id="llmStatus" class="meta" style="margin-bottom:10px"></div>
        <div id="personProfile"></div>
        <div id="recommendations"></div>
        <div id="report" class="report" style="display:none"></div>
      </div>
    </section>

    <section>
      <div class="section-head">Data Assistant</div>
      <div id="chatLog" class="chat-log">
        <div class="msg bot">Ask about counts, scoring, official socios, event interest, or a person/socio.</div>
      </div>
      <div class="chat-compose">
        <textarea id="chatInput" rows="3" placeholder="How many event profiles do we have?"></textarea>
        <div style="margin-top:8px; display:flex; gap:8px;">
          <button onclick="askChat()">Ask LLM</button>
          <button class="secondary" onclick="askLocalChat()">Ask Local</button>
          <button class="secondary" onclick="quickReportQuestion()">What is the score logic?</button>
        </div>
      </div>
    </section>
  </main>
  <script>
    let selectedId = null;
    let activeTab = 'recs';

    function esc(s) {
      return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;', "'":'&#39;'}[c]));
    }

    async function api(path) {
      const res = await fetch(path);
      if (res.status === 401) {
        window.location.href = '/login';
        return {};
      }
      return await res.json();
    }

    async function searchPeople() {
      const q = document.getElementById('search').value;
      const data = await api('/api/search?q=' + encodeURIComponent(q));
      const box = document.getElementById('people');
      box.innerHTML = data.results.map(p => `
        <div class="person-row" onclick="selectPerson(${p.member_id})">
          <div class="name">${esc(p.name)}</div>
          <div class="meta">${esc(p.socio)} · ${esc(p.role || 'role N/D')}</div>
          <div class="meta">${esc(p.email)}</div>
        </div>`).join('');
      if (!selectedId && data.results.length) selectPerson(data.results[0].member_id);
    }

    async function selectPerson(id) {
      selectedId = id;
      const data = await api('/api/person?id=' + encodeURIComponent(id));
      document.getElementById('selectedTitle').textContent = data.person.name + ' · ' + data.person.socio;
      document.getElementById('personProfile').innerHTML = `
        <div style="margin-bottom:12px">
          <div class="name">${esc(data.person.name)}</div>
          <div class="meta">${esc(data.person.role || 'role N/D')} · ${esc(data.person.email || '')}</div>
          <div class="meta">Technologies: ${esc(data.person.technologies || 'N/D')}</div>
          <div class="meta">Sectors: ${esc(data.person.sectors || 'N/D')}</div>
        </div>`;
      document.getElementById('recommendations').innerHTML = data.recommendations.map(r => `
        <div class="rec">
          <div style="display:flex; justify-content:space-between; gap:10px; align-items:flex-start;">
            <div>
              <div class="name">#${r.rank} ${esc(r.name)}</div>
              <div class="meta">${esc(r.socio)} · ${esc(r.role || 'role N/D')}</div>
            </div>
            <span class="score">${r.final_score.toFixed(4)}</span>
          </div>
          <div class="meta" style="margin-top:8px">
            profile ${r.profile_similarity.toFixed(3)} · structured ${r.structured_overlap.toFixed(3)} · needs ${r.needs_overlap.toFixed(3)} · event ${r.event_interest_overlap_score.toFixed(3)}
          </div>
          <div style="margin-top:8px; font-size:14px;">
            ${r.shared_technologies ? '<strong>Tech:</strong> ' + esc(r.shared_technologies) + '<br>' : ''}
            ${r.shared_sectors ? '<strong>Sectors:</strong> ' + esc(r.shared_sectors) + '<br>' : ''}
            ${r.shared_registered_events ? '<strong>Event interest:</strong> ' + esc(r.shared_registered_events) + '<br>' : ''}
            <span class="meta">${esc(r.event_interest_evidence_level)}</span>
          </div>
        </div>`).join('');
      document.getElementById('report').innerHTML = data.report_html;
      document.getElementById('llmStatus').textContent = '';
      showTab(activeTab);
    }

    async function generateLlmReport() {
      if (!selectedId) return;
      document.getElementById('llmStatus').textContent = 'Generating explanation layer...';
      const data = await api('/api/llm-report?id=' + encodeURIComponent(selectedId));
      document.getElementById('report').innerHTML = data.report_html;
      document.getElementById('llmStatus').textContent =
        data.llm_available
          ? 'LLM layer active: ' + data.model + ' (' + data.mode + ')'
          : 'LLM fallback mode: add OPENAI_API_KEY to .env for live generation (' + data.mode + ')';
      showTab('report');
    }

    function showTab(tab) {
      activeTab = tab;
      document.getElementById('tabRecs').className = tab === 'recs' ? 'active' : '';
      document.getElementById('tabReport').className = tab === 'report' ? 'active' : '';
      document.getElementById('recommendations').style.display = tab === 'recs' ? 'block' : 'none';
      document.getElementById('report').style.display = tab === 'report' ? 'block' : 'none';
    }

    async function askChat() {
      const input = document.getElementById('chatInput');
      const question = input.value.trim();
      if (!question) return;
      const log = document.getElementById('chatLog');
      log.innerHTML += '<div class="msg user">' + esc(question) + '</div>';
      input.value = '';
      const idPart = selectedId ? '&id=' + encodeURIComponent(selectedId) : '';
      const data = await api('/api/llm-chat?q=' + encodeURIComponent(question) + idPart);
      const mode = data.llm_available ? data.mode : data.mode + ' · local fallback';
      log.innerHTML += '<div class="msg bot">' + esc(data.answer) + '<div class="meta" style="margin-top:6px">' + esc(mode) + '</div></div>';
      log.scrollTop = log.scrollHeight;
    }

    async function askLocalChat() {
      const input = document.getElementById('chatInput');
      const question = input.value.trim();
      if (!question) return;
      const log = document.getElementById('chatLog');
      log.innerHTML += '<div class="msg user">' + esc(question) + '</div>';
      input.value = '';
      const data = await api('/api/chat?q=' + encodeURIComponent(question));
      log.innerHTML += '<div class="msg bot">' + esc(data.answer) + '<div class="meta" style="margin-top:6px">local deterministic answer</div></div>';
      log.scrollTop = log.scrollHeight;
    }

    function quickReportQuestion() {
      document.getElementById('chatInput').value = 'What is the score logic?';
      askChat();
    }

    document.getElementById('search').addEventListener('input', () => {
      clearTimeout(window.searchTimer);
      window.searchTimer = setTimeout(searchPeople, 180);
    });
    document.getElementById('chatInput').addEventListener('keydown', e => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) askChat();
    });
    searchPeople();
  </script>
</body>
</html>
"""


CHAT_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SECPHO Intelligence Chat</title>
  <style>
    :root {
      --bg: #111113;
      --panel: #18191b;
      --panel-2: #202124;
      --ink: #f4f4f5;
      --muted: #a6a7ab;
      --line: #303136;
      --brand: #00c3c7;
      --hot: #ff3158;
      --green: #7bd88f;
      --shadow: rgba(0,0,0,.34);
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 16% 12%, rgba(0,195,199,.12), transparent 30%),
        radial-gradient(circle at 84% 18%, rgba(255,49,88,.10), transparent 28%),
        var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
    }
    .shell {
      display: grid;
      grid-template-columns: 270px minmax(0, 1fr);
      height: 100vh;
    }
    aside {
      border-right: 1px solid var(--line);
      background: rgba(24,25,27,.94);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 48px;
    }
    .brand img { width: 122px; height: auto; display: block; }
    .badge {
      font-size: 12px;
      color: var(--green);
      border: 1px solid rgba(123,216,143,.35);
      padding: 4px 7px;
      border-radius: 999px;
      white-space: nowrap;
    }
    .new-chat {
      width: 100%;
      padding: 11px 12px;
      border: 1px solid var(--line);
      color: var(--ink);
      background: var(--panel-2);
      border-radius: 8px;
      text-align: left;
      cursor: pointer;
      font: inherit;
    }
    .side-block {
      border-top: 1px solid var(--line);
      padding-top: 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .side-block strong { color: var(--ink); }
    main {
      display: flex;
      flex-direction: column;
      min-width: 0;
      height: 100vh;
    }
    .topbar {
      height: 58px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 22px;
      background: rgba(17,17,19,.78);
      backdrop-filter: blur(12px);
    }
    .topbar h1 { margin: 0; font-size: 16px; font-weight: 650; }
    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }
    .status { color: var(--muted); font-size: 13px; }
    .ghost-button {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(32,33,36,.72);
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-size: 13px;
      min-height: 36px;
      padding: 8px 11px;
    }
    .ghost-button:hover { border-color: rgba(0,195,199,.55); }
    .chat {
      flex: 1;
      overflow: auto;
      padding: 28px 20px 150px;
    }
    .messages {
      width: min(920px, 100%);
      margin: 0 auto;
    }
    .welcome {
      margin: 8vh auto 30px;
      text-align: center;
      width: min(760px, 100%);
    }
    .welcome h2 {
      font-size: 32px;
      line-height: 1.15;
      margin: 18px 0 10px;
      font-weight: 720;
    }
    .welcome p {
      margin: 0 auto;
      max-width: 650px;
      color: var(--muted);
      line-height: 1.5;
    }
    .prompt-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 24px;
    }
    .prompt {
      border: 1px solid var(--line);
      background: rgba(32,33,36,.78);
      border-radius: 8px;
      padding: 13px;
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      font: inherit;
      min-height: 64px;
    }
    .prompt span { display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }
    .msg {
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 13px;
      margin: 22px 0;
    }
    .avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 13px;
      background: #2b2c31;
      color: var(--ink);
    }
    .assistant .avatar {
      background: linear-gradient(135deg, var(--brand), var(--hot));
      color: #071011;
    }
    .bubble {
      color: var(--ink);
      line-height: 1.55;
      max-width: 100%;
      overflow-wrap: anywhere;
    }
    .user .bubble {
      background: var(--panel-2);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px 14px;
      justify-self: start;
    }
    .assistant .bubble {
      padding: 3px 0;
    }
    .bubble h1 { font-size: 24px; margin: 0 0 10px; }
    .bubble h2 { font-size: 18px; margin: 18px 0 8px; }
    .bubble h3 { font-size: 15px; margin: 16px 0 6px; color: #dfe7ea; }
    .bubble li {
      margin: 7px 0;
      padding: 10px 12px;
      background: rgba(32,33,36,.70);
      border: 1px solid var(--line);
      border-radius: 8px;
      list-style: none;
    }
    .mode {
      margin-top: 10px;
      color: var(--muted);
      font-size: 12px;
    }
    .inline-action {
      border: 1px solid rgba(0,195,199,.45);
      color: var(--brand);
      background: rgba(0,195,199,.08);
      border-radius: 999px;
      padding: 3px 8px;
      margin-left: 5px;
      cursor: pointer;
    }
    .composer-wrap {
      position: fixed;
      left: 270px;
      right: 0;
      bottom: 0;
      padding: 18px 20px 22px;
      background: linear-gradient(to top, var(--bg) 72%, rgba(17,17,19,0));
    }
    .composer {
      width: min(920px, 100%);
      margin: 0 auto;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: #1f2024;
      box-shadow: 0 14px 38px var(--shadow);
      padding: 10px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 42px;
      gap: 8px;
      align-items: end;
    }
    textarea {
      resize: none;
      border: 0;
      outline: none;
      background: transparent;
      color: var(--ink);
      font: inherit;
      min-height: 44px;
      max-height: 150px;
      padding: 11px;
    }
    .send {
      width: 42px;
      height: 42px;
      border: 0;
      border-radius: 9px;
      cursor: pointer;
      background: var(--brand);
      color: #061112;
      font-size: 20px;
      font-weight: 900;
    }
    .fine-print {
      width: min(920px, 100%);
      margin: 8px auto 0;
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }
    .feedback-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,.62);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 18px;
      z-index: 20;
    }
    .feedback-backdrop.open { display: flex; }
    .feedback-panel {
      width: min(620px, 100%);
      background: #1b1c20;
      border: 1px solid var(--line);
      border-radius: 10px;
      box-shadow: 0 22px 80px var(--shadow);
      padding: 18px;
    }
    .feedback-panel h2 {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 680;
    }
    .feedback-panel p {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.45;
      font-size: 13px;
    }
    .feedback-panel textarea {
      width: 100%;
      min-height: 150px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111113;
      padding: 12px;
    }
    .feedback-actions {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-top: 12px;
      flex-wrap: wrap;
    }
    .feedback-actions div {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .primary-button {
      border: 0;
      border-radius: 8px;
      background: var(--brand);
      color: #061112;
      cursor: pointer;
      font: inherit;
      font-weight: 750;
      min-height: 38px;
      padding: 8px 12px;
    }
    .feedback-note {
      color: var(--muted);
      min-height: 18px;
      margin-top: 10px;
      font-size: 12px;
    }
    @media (max-width: 860px) {
      .shell { grid-template-columns: 1fr; }
      aside { display: none; }
      .composer-wrap { left: 0; }
      .prompt-grid { grid-template-columns: 1fr; }
      .status { display: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <img src="/static/secpho_logo_negative.png" alt="secpho">
        <span class="badge" id="llmBadge">LLM</span>
      </div>
      <button class="new-chat" onclick="newChat()">+ New conversation</button>
      <a class="new-chat" href="/logout" style="text-decoration:none">Sign out</a>
      <div class="side-block">
        <strong>Model rule</strong><br>
        The script does the matchmaking. The LLM explains and decorates the deterministic results.
      </div>
      <div class="side-block">
        <strong>SECPHO voice</strong><br>
        Collaborate to innovate. Deep tech connections, evidence, and practical next steps.
      </div>
      <div class="side-block">
        <strong>Try</strong><br>
        “Who works at ICFO?”<br>
        “Give me recommendations for David Santana.”<br>
        “Create a report for David Santana.”
      </div>
      <div class="side-block">
        <strong>Tool learning loop</strong><br>
        Unsupported requests become stored proposals for Codex review.<br>
        <a href="/api/tool-requests" target="_blank" style="color:var(--brand)">View proposals</a>
      </div>
      <div class="side-block">
        <strong>Feedback inbox</strong><br>
        Chat users can leave notes for product review.<br>
        <a href="/api/feedback-inbox" target="_blank" style="color:var(--brand)">View feedback</a>
      </div>
    </aside>
    <main>
      <div class="topbar">
        <h1>SECPHO Intelligence Chat</h1>
        <div class="topbar-actions">
          <div class="status" id="status">Math decides. LLM explains.</div>
          <button class="ghost-button" onclick="openFeedback()">Feedback</button>
        </div>
      </div>
      <div class="chat" id="chat">
        <div class="messages" id="messages">
          <div class="welcome" id="welcome">
            <img src="/static/secpho_logo_negative.png" alt="secpho" style="width:150px; opacity:.95">
            <h2>Ask about socios, people, recommendations, and reports.</h2>
            <p>Conversation drives the workflow. The matcher computes ranked introductions; the LLM turns the evidence into useful language.</p>
            <div class="prompt-grid">
              <button class="prompt" onclick="sendExample('Who works at ICFO?')">Who works at ICFO?<span>Find people by company</span></button>
              <button class="prompt" onclick="sendExample('Give me recommendations for David Santana')">Recommend contacts<span>Use the model ranking</span></button>
              <button class="prompt" onclick="sendExample('Create a report for David Santana')">Create a report<span>One-page LLM briefing</span></button>
              <button class="prompt" onclick="sendExample('Explain the score logic')">Explain scoring<span>Audit the model signals</span></button>
            </div>
          </div>
        </div>
      </div>
      <div class="composer-wrap">
        <div class="composer">
          <textarea id="input" placeholder="Ask SECPHO Matchmaker..." rows="1"></textarea>
          <button class="send" onclick="sendMessage()">↑</button>
        </div>
        <div class="fine-print">Event signal means shared registration interest, not confirmed attendance.</div>
      </div>
    </main>
  </div>
  <div class="feedback-backdrop" id="feedbackModal" role="dialog" aria-modal="true" aria-labelledby="feedbackTitle">
    <div class="feedback-panel">
      <h2 id="feedbackTitle">Send feedback</h2>
      <p>Write what feels broken, missing, confusing, or useful. Voice dictation works in supported browsers.</p>
      <textarea id="feedbackText" placeholder="Example: I asked for a company report and expected sources, but the answer was too generic."></textarea>
      <div class="feedback-actions">
        <button class="ghost-button" onclick="toggleVoiceFeedback()" id="voiceButton">Voice</button>
        <div>
          <button class="ghost-button" onclick="closeFeedback()">Cancel</button>
          <button class="primary-button" onclick="submitFeedback()">Save feedback</button>
        </div>
      </div>
      <div class="feedback-note" id="feedbackNote"></div>
    </div>
  </div>
  <script>
    let selectedMemberId = null;
    let feedbackRecognition = null;
    let feedbackListening = false;

    function esc(s) {
      return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;', "'":'&#39;'}[c]));
    }

    async function api(path) {
      const res = await fetch(path);
      if (res.status === 401) {
        window.location.href = '/login';
        return {};
      }
      if (res.status === 403) {
        return {error: 'forbidden'};
      }
      return await res.json();
    }

    function openFeedback() {
      const modal = document.getElementById('feedbackModal');
      modal.classList.add('open');
      document.getElementById('feedbackNote').textContent = '';
      setTimeout(() => document.getElementById('feedbackText').focus(), 30);
    }

    function closeFeedback() {
      if (feedbackRecognition && feedbackListening) {
        feedbackRecognition.stop();
      }
      feedbackListening = false;
      document.getElementById('voiceButton').textContent = 'Voice';
      document.getElementById('feedbackModal').classList.remove('open');
    }

    function toggleVoiceFeedback() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const note = document.getElementById('feedbackNote');
      const button = document.getElementById('voiceButton');
      if (!SpeechRecognition) {
        note.textContent = 'Voice dictation is not available in this browser. Typing still works.';
        return;
      }
      if (!feedbackRecognition) {
        feedbackRecognition = new SpeechRecognition();
        feedbackRecognition.continuous = true;
        feedbackRecognition.interimResults = true;
        feedbackRecognition.lang = 'en-US';
        feedbackRecognition.onresult = (event) => {
          let finalText = '';
          let interimText = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) finalText += transcript + ' ';
            else interimText += transcript;
          }
          const input = document.getElementById('feedbackText');
          if (finalText) input.value = (input.value + ' ' + finalText).trim();
          note.textContent = interimText ? 'Listening: ' + interimText : 'Listening...';
        };
        feedbackRecognition.onend = () => {
          feedbackListening = false;
          button.textContent = 'Voice';
          if (note.textContent === 'Listening...') note.textContent = '';
        };
        feedbackRecognition.onerror = () => {
          feedbackListening = false;
          button.textContent = 'Voice';
          note.textContent = 'Voice dictation stopped. You can keep typing.';
        };
      }
      if (feedbackListening) {
        feedbackRecognition.stop();
        return;
      }
      feedbackRecognition.start();
      feedbackListening = true;
      button.textContent = 'Stop voice';
      note.textContent = 'Listening...';
    }

    async function submitFeedback() {
      const textBox = document.getElementById('feedbackText');
      const note = document.getElementById('feedbackNote');
      const feedback = textBox.value.trim();
      if (!feedback) {
        note.textContent = 'Add a note first.';
        return;
      }
      note.textContent = 'Saving...';
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          feedback,
          selected_member_id: selectedMemberId,
          source: 'chat_feedback_box',
          user_agent: navigator.userAgent
        })
      });
      if (res.status === 401) {
        window.location.href = '/login';
        return;
      }
      const data = await res.json();
      if (!res.ok || !data.ok) {
        note.textContent = data.error || 'Could not save feedback.';
        return;
      }
      textBox.value = '';
      note.textContent = 'Saved. We will review this in the feedback inbox.';
      setTimeout(closeFeedback, 650);
    }

    function addMessage(role, html, mode) {
      const welcome = document.getElementById('welcome');
      if (welcome) welcome.style.display = 'none';
      const box = document.getElementById('messages');
      const node = document.createElement('div');
      node.className = 'msg ' + role;
      node.innerHTML = `
        <div class="avatar">${role === 'assistant' ? 'S' : 'You'}</div>
        <div class="bubble">${html}${mode ? '<div class="mode">' + esc(mode) + '</div>' : ''}</div>
      `;
      box.appendChild(node);
      document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
    }

    async function sendMessage() {
      const input = document.getElementById('input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      addMessage('user', esc(text));
      addMessage('assistant', '<span style="color:#a6a7ab">Checking the right tool. If it is safe to create now, I’ll build it and run it.</span>', '');
      const last = document.querySelector('#messages .msg.assistant:last-child');
      const idPart = selectedMemberId ? '&id=' + encodeURIComponent(selectedMemberId) : '';
      const data = await api('/api/chat-flow?q=' + encodeURIComponent(text) + idPart);
      if (data.selected_member_id) selectedMemberId = data.selected_member_id;
      last.querySelector('.bubble').innerHTML = data.answer_html + '<div class="mode">' + esc((data.llm_available ? 'LLM active' : 'fallback') + ' · ' + data.mode + ' · ' + data.kind) + '</div>';
      document.getElementById('llmBadge').textContent = data.llm_available ? 'LLM ON' : 'Fallback';
      document.getElementById('status').textContent = data.kind === 'report' ? 'Report generated from model evidence' : 'Math decides. LLM explains.';
      document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
    }

    function sendExample(text) {
      document.getElementById('input').value = text;
      sendMessage();
    }

    function setPerson(id) {
      selectedMemberId = id;
      document.getElementById('status').textContent = 'Selected person ID ' + id;
    }

    function newChat() {
      selectedMemberId = null;
      document.getElementById('messages').innerHTML = document.getElementById('welcome').outerHTML;
      document.getElementById('welcome').style.display = 'block';
      document.getElementById('status').textContent = 'Math decides. LLM explains.';
    }

    document.getElementById('input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    document.getElementById('input').addEventListener('input', (e) => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
    });
    document.getElementById('feedbackModal').addEventListener('click', (e) => {
      if (e.target.id === 'feedbackModal') closeFeedback();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeFeedback();
    });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def client_ip(self) -> str:
        forwarded = self.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
        return self.client_address[0] if self.client_address else "unknown"

    def session(self) -> dict | None:
        if not AUTH_REQUIRED:
            return {"role": "admin", "auth_disabled": True}
        cookies = parse_cookie_header(self.headers.get("Cookie", ""))
        return parse_session_cookie(cookies.get(SESSION_COOKIE_NAME, ""))

    def is_authenticated(self) -> bool:
        return self.session() is not None

    def is_admin(self) -> bool:
        session = self.session()
        return bool(session and session.get("role") == "admin")

    def secure_cookie_suffix(self) -> str:
        forwarded_proto = self.headers.get("X-Forwarded-Proto", "")
        is_https = forwarded_proto.lower() == "https"
        secure = "; Secure" if is_https or os.getenv("RENDER") else ""
        return f"; HttpOnly; SameSite=Lax{secure}"

    def send_security_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), payment=(), usb=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'",
        )
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_security_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_security_headers()
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_security_headers()
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_forbidden(self) -> None:
        self.send_json({"error": "forbidden"}, status=403)

    def send_unauthorized(self) -> None:
        self.send_json({"error": "authentication_required"}, status=401)

    def send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_response(404)
            self.send_security_headers()
            self.end_headers()
            return
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_security_headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/login":
            if self.is_authenticated():
                self.send_redirect("/")
                return
            self.send_html(LOGIN_HTML.replace("{{ERROR}}", ""))
            return

        if parsed.path == "/logout":
            self.send_response(303)
            self.send_security_headers()
            self.send_header("Set-Cookie", f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0{self.secure_cookie_suffix()}")
            self.send_header("Location", "/login")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path == "/":
            if not self.is_authenticated():
                self.send_redirect("/login")
                return
            self.send_html(CHAT_HTML)
            return

        if parsed.path == "/health":
            self.send_json(
                {
                    "status": "ok",
                    "llm_available": openai_available(),
                    "auth_required": AUTH_REQUIRED,
                    "people": len(DATA["people"]),
                    "matches": len(DATA["matches"]),
                }
            )
            return

        if parsed.path == "/classic":
            if not self.is_authenticated():
                self.send_redirect("/login")
                return
            self.send_html(INDEX_HTML)
            return

        if parsed.path.startswith("/static/"):
            name = Path(parsed.path.replace("/static/", "", 1)).name
            self.send_file(STATIC_DIR / name)
            return

        if parsed.path.startswith("/artifacts/"):
            if not self.is_authenticated():
                self.send_unauthorized()
                return
            name = Path(parsed.path.replace("/artifacts/", "", 1)).name
            self.send_file(GENERATED_ARTIFACTS_DIR / name)
            return

        if parsed.path.startswith("/api/"):
            if not self.is_authenticated():
                self.send_unauthorized()
                return
            bucket = "llm" if parsed.path in {"/api/chat-flow", "/api/llm-chat", "/api/llm-report"} else "api"
            if is_rate_limited(self.client_ip(), bucket):
                self.send_json({"error": "rate_limited"}, status=429)
                return

        if parsed.path == "/api/search":
            q = params.get("q", [""])[0]
            self.send_json({"results": search_people(q)})
            return

        if parsed.path == "/api/person":
            member_id = int(params.get("id", ["0"])[0])
            report = report_for_person(member_id)
            self.send_json(
                {
                    "person": get_person(member_id),
                    "recommendations": get_recommendations(member_id, 5),
                    "report_markdown": report,
                    "report_html": markdown_to_html(report),
                }
            )
            return

        if parsed.path == "/api/llm-report":
            member_id = int(params.get("id", ["0"])[0])
            report = llm_report_for_person(member_id)
            self.send_json(
                {
                    "mode": report["mode"],
                    "report_markdown": report["markdown"],
                    "report_html": markdown_to_html(report["markdown"]),
                    "llm_available": openai_available(),
                    "model": os.getenv("OPENAI_MODEL", OPENAI_MODEL),
                }
            )
            return

        if parsed.path == "/api/chat":
            q = params.get("q", [""])[0]
            self.send_json({"answer": answer_question(q)})
            return

        if parsed.path == "/api/llm-chat":
            q = params.get("q", [""])[0]
            member_id_raw = params.get("id", [""])[0]
            member_id = int(member_id_raw) if member_id_raw else None
            answer = llm_answer_question(q, member_id)
            self.send_json(
                {
                    "answer": answer["answer"],
                    "mode": answer["mode"],
                    "llm_available": openai_available(),
                    "model": os.getenv("OPENAI_MODEL", OPENAI_MODEL),
                }
            )
            return

        if parsed.path == "/api/chat-flow":
            q = params.get("q", [""])[0]
            member_id_raw = params.get("id", [""])[0]
            member_id = int(member_id_raw) if member_id_raw else None
            result = chat_flow(q, member_id)
            self.send_json(
                {
                    **result,
                    "answer_html": markdown_to_chat_html(result["answer"]),
                    "model": os.getenv("OPENAI_MODEL", OPENAI_MODEL),
                }
            )
            return

        if parsed.path == "/api/tool-requests":
            if not self.is_admin():
                self.send_forbidden()
                return
            limit_raw = params.get("limit", ["50"])[0]
            try:
                limit = int(limit_raw)
            except ValueError:
                limit = 50
            self.send_json({"requests": tool_request_status_view(limit=max(1, min(limit, 200)))})
            return

        if parsed.path == "/api/tool-build-events":
            if not self.is_admin():
                self.send_forbidden()
                return
            limit_raw = params.get("limit", ["50"])[0]
            try:
                limit = int(limit_raw)
            except ValueError:
                limit = 50
            self.send_json(
                {
                    "events": load_tool_build_events(limit=max(1, min(limit, 200))),
                    "registry": load_generated_tools_registry(),
                }
            )
            return

        if parsed.path == "/api/feedback-inbox":
            if not self.is_admin():
                self.send_forbidden()
                return
            body = load_feedback_inbox().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_security_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/login":
            if is_rate_limited(self.client_ip(), "login"):
                self.send_html(LOGIN_HTML.replace("{{ERROR}}", "Too many attempts. Try again later."), status=429)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            raw = self.rfile.read(min(length, 4096)).decode("utf-8") if length else ""
            params = parse_qs(raw)
            password = params.get("password", [""])[0]
            role = check_password(password)
            if not role:
                self.send_html(LOGIN_HTML.replace("{{ERROR}}", "Invalid password."), status=401)
                return
            self.send_response(303)
            self.send_security_headers()
            cookie = make_session_cookie(role)
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE_NAME}={cookie}; Path=/; Max-Age={SESSION_TTL_SECONDS}{self.secure_cookie_suffix()}",
            )
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path.startswith("/api/"):
            if not self.is_authenticated():
                self.send_unauthorized()
                return

        if parsed.path == "/api/feedback":
            if is_rate_limited(self.client_ip(), "feedback"):
                self.send_json({"ok": False, "error": "rate_limited"}, status=429)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length > 20000:
                self.send_json({"ok": False, "error": "Feedback payload is too large."}, status=413)
                return
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self.send_json({"ok": False, "error": "Invalid JSON payload."}, status=400)
                return

            result = save_feedback(
                payload.get("feedback", ""),
                {
                    "selected_member_id": payload.get("selected_member_id"),
                    "source": payload.get("source", "chat_feedback_box"),
                    "user_agent": payload.get("user_agent", self.headers.get("User-Agent", "")),
                },
            )
            self.send_json(result, status=200 if result.get("ok") else 400)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"SECPHO Matchmaker MVP running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
