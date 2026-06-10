#!/usr/bin/env python3
"""
Read-only verifier for the INMC HighLevel chatbot setup.

Default behavior:
  - Loads /Users/danielaroustamian/.env
  - Checks the live Vercel site for the LeadConnector widget
  - Checks HighLevel public widget config
  - Checks Agent Studio production agent state
  - Checks Website Leads pipeline stages
  - Exits 1 until the chatbot is actually configured correctly

No writes. No paid AI execution. No contact creation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_ENV = Path("/Users/danielaroustamian/.env")
DEFAULT_BASE_URL = "https://inmc-option-1.vercel.app"
DEFAULT_WIDGET_ID = "69cc91e086ec4f5dc6900723"
DEFAULT_AGENT_ID = "df35e393-0714-4603-8999-bbc80784aac4"
DEFAULT_PIPELINE_NAME = "Website Leads"
EXPECTED_LOCATION_NAME = "Integrative Natural Medical Center"
EXPECTED_LOCATION_ID_ENV = "GHL_LOC_INMC"
EXPECTED_TOKEN_ENV = "GHL_INMC_PIT"
EXPECTED_PIPELINE_STAGES = [
    "New Lead",
    "Needs Reply",
    "Discovery Call Requested",
    "Consultation Scheduled",
    "Active Patient",
    "Not A Fit",
]
LIVE_ROUTES = ["/", "/about.html", "/testimonials.html", "/blog.html"]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key] = value.strip().strip('"').strip("'")
    return env


def session(token: str, version: str) -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Version": version,
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
        }
    )
    return sess


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, details: dict[str, Any]) -> None:
    checks.append({"name": name, "ok": ok, "details": details})


def get_json(sess: requests.Session, url: str, **kwargs: Any) -> tuple[int, Any]:
    try:
        resp = sess.get(url, timeout=25, **kwargs)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return resp.status_code, body
    except Exception as exc:
        return 0, {"error": str(exc)}


def normalize_chat_types(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except Exception:
            return [value]
    return []


def walk_agent_prompts(agent: dict[str, Any], prod_only: bool = True) -> list[str]:
    prompts: list[str] = []
    versions = agent.get("versions") or []
    if prod_only:
        versions = [version for version in versions if version.get("state") == "prod"]
    for version in versions:
        for node in version.get("nodes") or []:
            config = node.get("nodeConfig") or {}
            prompt = config.get("prompt")
            if isinstance(prompt, str) and prompt.strip():
                prompts.append(prompt)
    return prompts


def prod_version(agent: dict[str, Any]) -> dict[str, Any]:
    for version in agent.get("versions") or []:
        if version.get("state") == "prod":
            return version
    return {}


def prod_chat_triggers(version: dict[str, Any]) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    for node in version.get("nodes") or []:
        config = node.get("nodeConfig") or {}
        trigger_type = config.get("triggerType") or config.get("type")
        if trigger_type == "chat" or node.get("nodeType") == "triggerNode":
            triggers.append(
                {
                    "nodeId": node.get("nodeId"),
                    "display": node.get("nodeDisplayName"),
                    "type": trigger_type,
                    "enabled": config.get("enabled"),
                }
            )
    return triggers


def prod_runtime_variables(version: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for node in version.get("nodes") or []:
        config = node.get("nodeConfig") or {}
        for variable in config.get("runtimeVariables") or []:
            keys.append(str(variable.get("key") or ""))
    return keys


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# INMC Chatbot Verification",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Overall OK: `{report['ok']}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        mark = "PASS" if check["ok"] else "FAIL"
        lines.append(f"- `{mark}` {check['name']}: `{json.dumps(check['details'], ensure_ascii=False)}`")
    lines.extend(
        [
            "",
            "## Required Before Complete",
            "",
            "- Widget must expose or use an AI capable chat path, not live/email chat only.",
            "- Widget branding must be INMC or agency branding must be disabled.",
            "- Widget acknowledgement typo must be fixed.",
            "- Production chat trigger must be enabled.",
            "- Production agent prompt must be INMC medical concierge specific.",
            "- Runtime variable keys must be non empty.",
            "- Website Leads pipeline must use clinic intake stages.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--token-env", default=EXPECTED_TOKEN_ENV)
    parser.add_argument("--location-env", default=EXPECTED_LOCATION_ID_ENV)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--widget-id", default=DEFAULT_WIDGET_ID)
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    env = load_env(Path(args.env))
    token = env.get(args.token_env)
    location_id = env.get(args.location_env)
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "env has INMC token and location",
        bool(token and location_id),
        {"has_token": bool(token), "token_length": len(token or ""), "location_id": location_id},
    )

    web = requests.Session()
    web.headers.update({"User-Agent": "Mozilla/5.0"})
    page_results = []
    for route in LIVE_ROUTES:
        try:
            resp = web.get(args.base_url.rstrip("/") + route, timeout=25)
            text = resp.text
            page_results.append(
                {
                    "route": route,
                    "status": resp.status_code,
                    "widget_present": args.widget_id in text,
                    "loader_present": "widgets.leadconnectorhq.com/loader.js" in text,
                }
            )
        except Exception as exc:
            page_results.append({"route": route, "error": str(exc)})
    add_check(
        checks,
        "live pages embed expected widget",
        all(item.get("status") == 200 and item.get("widget_present") and item.get("loader_present") for item in page_results),
        {"pages": page_results},
    )

    if token and location_id:
        ghl23 = session(token, "2023-02-21")
        ghl21 = session(token, "2021-07-28")

        status, location = get_json(ghl21, f"https://services.leadconnectorhq.com/locations/{location_id}")
        location_obj = (location or {}).get("location") if isinstance(location, dict) else {}
        if not isinstance(location_obj, dict):
            location_obj = {}
        add_check(
            checks,
            "GHL location is INMC",
            status == 200 and (location_obj.get("name") or location_obj.get("businessName")) == EXPECTED_LOCATION_NAME,
            {"status": status, "name": location_obj.get("name") or location_obj.get("businessName")},
        )

        status, widget = get_json(
            ghl23,
            f"https://services.leadconnectorhq.com/chat-widget/public/config/{args.widget_id}",
        )
        config = widget.get("config") if isinstance(widget, dict) else {}
        if not isinstance(config, dict):
            config = {}
        chat_types = normalize_chat_types(config.get("all-in-one-chat-types"))
        ai_chat_types = {
            "ai",
            "aichat",
            "ai_chat",
            "conversationai",
            "conversation_ai",
            "conversationalai",
            "conversational_ai",
            "voiceai",
            "voice_ai",
            "voiceaichat",
            "voice_ai_chat",
        }
        normalized_chat_types = {re.sub(r"[^a-z0-9_]", "", item.lower()) for item in chat_types}
        widget_has_ai = bool(ai_chat_types & normalized_chat_types) or any(
            key in config for key in ["agent-id", "agentId", "conversation-ai-agent-id", "conversationAiAgentId"]
        )
        add_check(
            checks,
            "public widget config belongs to INMC",
            status == 200 and config.get("location-id") == location_id,
            {"status": status, "location_id": config.get("location-id")},
        )
        add_check(
            checks,
            "widget is AI capable",
            widget_has_ai,
            {"chat_type": config.get("chat-type"), "chat_types": chat_types},
        )
        add_check(
            checks,
            "widget branding is INMC or disabled",
            (config.get("show-agency-branding") is False)
            or str(config.get("agency-name") or "").lower() in {"integrative natural medical clinic", "inmc"},
            {
                "show_agency_branding": config.get("show-agency-branding"),
                "agency_name": config.get("agency-name"),
            },
        )
        add_check(
            checks,
            "widget acknowledgement copy is clean",
            config.get("live-chat-ack-msg") != "Your chat has ende",
            {"live_chat_ack_msg": config.get("live-chat-ack-msg")},
        )

        private_status, private_widget = get_json(
            ghl23,
            "https://services.leadconnectorhq.com/chat-widget/list",
            params={"locationId": location_id, "limit": 1, "offset": 0},
        )
        add_check(
            checks,
            "token has private chat widget scope",
            private_status == 200,
            {
                "status": private_status,
                "error": private_widget.get("message") if isinstance(private_widget, dict) else private_widget,
            },
        )

        status, agent_payload = get_json(
            ghl23,
            f"https://services.leadconnectorhq.com/agent-studio/agent/{args.agent_id}",
            params={"locationId": location_id},
        )
        agent = agent_payload.get("agent") if isinstance(agent_payload, dict) else {}
        if not isinstance(agent, dict):
            agent = {}
        version = prod_version(agent)
        prompts = walk_agent_prompts(agent, prod_only=True)
        prompt_text = "\n".join(prompts).lower()
        trigger_summary = prod_chat_triggers(version)
        runtime_keys = prod_runtime_variables(version)
        add_check(
            checks,
            "Agent Studio production agent exists",
            status == 200 and bool(version),
            {
                "status": status,
                "agent_name": agent.get("name"),
                "agent_status": agent.get("status"),
                "prod_version_id": version.get("versionId"),
                "prod_is_published": version.get("isPublished"),
            },
        )
        add_check(
            checks,
            "production chat trigger enabled",
            any(trigger.get("type") == "chat" and trigger.get("enabled") is True for trigger in trigger_summary),
            {"triggers": trigger_summary},
        )
        add_check(
            checks,
            "production prompt is INMC specific",
            all(term in prompt_text for term in ["integrative natural medical", "santiago", "pasadena"])
            and "company" not in prompt_text,
            {"prompt_count": len(prompts), "has_company_word": "company" in prompt_text},
        )
        add_check(
            checks,
            "runtime variable keys are non empty",
            bool(runtime_keys) and all(key.strip() for key in runtime_keys),
            {"runtime_keys": runtime_keys},
        )

        status, pipelines = get_json(
            ghl21,
            "https://services.leadconnectorhq.com/opportunities/pipelines",
            params={"locationId": location_id},
        )
        pipeline_rows = pipelines.get("pipelines") if isinstance(pipelines, dict) else []
        if not isinstance(pipeline_rows, list):
            pipeline_rows = []
        website_pipeline = next((pipeline for pipeline in pipeline_rows if pipeline.get("name") == DEFAULT_PIPELINE_NAME), {})
        current_stages = [stage.get("name") for stage in website_pipeline.get("stages") or []]
        add_check(
            checks,
            "Website Leads pipeline uses clinic intake stages",
            current_stages == EXPECTED_PIPELINE_STAGES,
            {"status": status, "pipeline_id": website_pipeline.get("id"), "current_stages": current_stages},
        )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": all(check["ok"] for check in checks),
        "checks": checks,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.write_report:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        json_path = reports_dir / f"inmc-chatbot-verification-{stamp}.json"
        md_path = reports_dir / f"inmc-chatbot-verification-{stamp}.md"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        md_path.write_text(make_markdown(report))
        print(json.dumps({"report_json": str(json_path), "report_md": str(md_path)}))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
