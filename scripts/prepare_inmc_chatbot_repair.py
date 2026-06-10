#!/usr/bin/env python3
"""
Guarded repair preflight for INMC chatbot setup.

This script is intentionally conservative:
  - Default is dry-run only.
  - It does not execute the agent.
  - It does not create contacts.
  - It refuses --apply unless passed with --confirm-live-ghl-chatbot-repair.
  - Even then, it blocks if private chat-widget scope is missing.

Current purpose: produce the target configuration and show why live apply is
or is not safe.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_ENV = Path("/Users/danielaroustamian/.env")
LOCATION_ENV = "GHL_LOC_INMC"
TOKEN_ENV = "GHL_INMC_PIT"
WIDGET_ID = "69cc91e086ec4f5dc6900723"
AGENT_ID = "df35e393-0714-4603-8999-bbc80784aac4"
WEBSITE_PIPELINE_NAME = "Website Leads"
TARGET_AGENT_NAME = "INMC Website Concierge"
TARGET_STAGE_NAMES = [
    "New Lead",
    "Needs Reply",
    "Discovery Call Requested",
    "Consultation Scheduled",
    "Active Patient",
    "Not A Fit",
]

TARGET_PROMPT = """You are the website concierge for Integrative Natural Medical Clinic in Pasadena, California.

Your job is to help website visitors get the right next step.

Clinic facts you may use:
Name: Integrative Natural Medical Clinic
Doctor: Dr. Amaliya Santiago, ND
Address: 301 S Fair Oaks Ave, Suite 401, Pasadena, CA 91105
Phone: 626 714 7400
Backup phone: 833 269 3526
Email: info@dramaliyasantiago.com
Care focus: naturopathic and integrative medicine
Common service interests: EBOO ozone therapy, IV nutrition, bioidentical hormones, natural oncology support, peptide therapy, medical weight loss, pain management, regenerative medicine, prolozone, exosomes, PRP, PEMF, Roxiva, sauna, and general root cause care

Primary goal:
Help the visitor understand whether INMC may be a fit, then collect contact details for the clinic team.

Tone:
Warm, calm, concise, and professional.
Use plain language.
Ask one question at a time.
Do not sound like a sales bot.

Medical safety rules:
Do not diagnose.
Do not recommend a treatment plan.
Do not say a service is right for the visitor.
Do not promise results.
Do not say symptoms are caused by any condition.
Do not give dosing, medication, supplement, or lab interpretation advice.
Do not replace the doctor.
If the visitor mentions severe symptoms, chest pain, trouble breathing, fainting, stroke signs, suicidal thoughts, or another emergency, tell them to call 911 or seek emergency care now.

Approved way to answer service questions:
Explain what the service is generally used for at a high level.
Then say Dr. Santiago would need to review their history before deciding what is appropriate.

Lead capture:
Collect these fields when natural:
1. Name
2. Phone
3. Email
4. Main concern
5. Service interest
6. How soon they want help

Qualification:
Hot lead: wants a consult or call, gives name and phone, has a clear concern.
Warm lead: interested but not ready, missing details, or asks general questions.
Needs human: asks clinical advice, pricing certainty, scheduling details, insurance, urgent symptoms, or wants Dr. Santiago.

Handoff:
When the visitor is ready, say:
Thanks. I can pass this to the clinic team so they can follow up with you.

If they ask for booking:
Say:
The clinic team can help with the right appointment option. What is the best phone number to reach you?

If they ask about price:
Say:
The clinic can confirm current pricing. Many first visits are more in depth than a standard appointment because Dr. Santiago reviews the full history. The team can explain what applies to your situation.

If they ask whether a treatment will work:
Say:
That depends on your history and exam. Dr. Santiago would need to review your case before saying what is appropriate.

End state:
When you have name and phone, summarize the concern in one sentence and tell the visitor the clinic team will follow up.
"""

TARGET_RUNTIME_VARIABLES = [
    {
        "key": "visitorName",
        "type": "string",
        "description": "Visitor name if provided",
        "required": False,
    },
    {
        "key": "visitorPhone",
        "type": "string",
        "description": "Visitor phone if provided",
        "required": False,
    },
    {
        "key": "visitorEmail",
        "type": "string",
        "description": "Visitor email if provided",
        "required": False,
    },
    {
        "key": "mainConcern",
        "type": "string",
        "description": "Main health concern in the visitor's own words",
        "required": False,
    },
    {
        "key": "serviceInterest",
        "type": "string",
        "description": "Service or care area the visitor asked about",
        "required": False,
    },
    {
        "key": "timeline",
        "type": "string",
        "description": "How soon the visitor wants help",
        "required": False,
    },
    {
        "key": "leadQuality",
        "type": "string",
        "description": "hot, warm, needs human, or invalid",
        "required": True,
    },
    {
        "key": "handoffReason",
        "type": "string",
        "description": "Why staff should review or follow up",
        "required": False,
    },
    {
        "key": "conversationSummary",
        "type": "string",
        "description": "One sentence summary for clinic staff",
        "required": True,
    },
]


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
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
    )
    return sess


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


def prod_version(agent: dict[str, Any]) -> dict[str, Any]:
    for version in agent.get("versions") or []:
        if version.get("state") == "prod":
            return version
    return {}


def build_agent_payload(version: dict[str, Any], location_id: str) -> dict[str, Any]:
    nodes = copy.deepcopy(version.get("nodes") or [])
    for node in nodes:
        config = node.get("nodeConfig") or {}
        if config.get("triggerType") == "chat":
            config["enabled"] = True
            node["nodeConfig"] = config
        if node.get("nodeType") == "llmNode" or node.get("frontendNodeType") == "llm":
            prompt = config.get("prompt") or ""
            if "company" in prompt.lower() or "lead qualification analyst" in prompt.lower():
                config["prompt"] = TARGET_PROMPT
                config["runtimeVariables"] = copy.deepcopy(TARGET_RUNTIME_VARIABLES)
                config["humanFallbackAllowed"] = True
                node["nodeConfig"] = config
                break
    return {
        "locationId": location_id,
        "versionName": "INMC Website Concierge v1",
        "description": "INMC-safe website concierge for patient inquiry capture and human handoff.",
        "nodes": nodes,
        "edges": copy.deepcopy(version.get("edges") or []),
        "globalVariables": copy.deepcopy(version.get("globalVariables") or []),
        "inputVariables": copy.deepcopy(version.get("inputVariables") or []),
        "runtimeVariables": copy.deepcopy(TARGET_RUNTIME_VARIABLES),
        "globalConfig": copy.deepcopy(version.get("globalConfig") or {}),
        "userName": "Codex",
    }


def summarize_widget_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "chat_type": config.get("chat-type"),
        "chat_types": config.get("all-in-one-chat-types"),
        "agency_name": config.get("agency-name"),
        "show_agency_branding": config.get("show-agency-branding"),
        "ack_message": config.get("live-chat-ack-msg"),
        "location_id": config.get("location-id"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--token-env", default=TOKEN_ENV)
    parser.add_argument("--location-env", default=LOCATION_ENV)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-live-ghl-chatbot-repair", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    env = load_env(Path(args.env))
    token = env.get(args.token_env)
    location_id = env.get(args.location_env)
    blockers: list[str] = []
    actions: list[dict[str, Any]] = []

    if not token or not location_id:
        blockers.append(f"Missing {args.token_env} or {args.location_env} in env.")

    result: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if args.apply else "dry-run",
        "safeToApply": False,
        "blockers": blockers,
        "plannedActions": actions,
    }

    if token and location_id:
        ghl23 = session(token, "2023-02-21")
        ghl21 = session(token, "2021-07-28")

        status, private_widget = get_json(
            ghl23,
            "https://services.leadconnectorhq.com/chat-widget/list",
            params={"locationId": location_id, "limit": 1, "offset": 0},
        )
        if status != 200:
            blockers.append("Current INMC PIT lacks private chat-widget scope; cannot safely update or attach widget.")
        result["privateWidgetScope"] = {
            "status": status,
            "error": private_widget.get("message") if isinstance(private_widget, dict) else private_widget,
        }

        status, public_widget = get_json(
            ghl23,
            f"https://services.leadconnectorhq.com/chat-widget/public/config/{WIDGET_ID}",
        )
        widget_config = public_widget.get("config") if isinstance(public_widget, dict) else {}
        if not isinstance(widget_config, dict):
            widget_config = {}
        result["currentWidget"] = summarize_widget_config(widget_config)
        actions.append(
            {
                "target": "chat-widget",
                "widgetId": WIDGET_ID,
                "changes": {
                    "agency-name": "Integrative Natural Medical Clinic",
                    "show-agency-branding": False,
                    "live-chat-ack-msg": "Your chat has ended.",
                    "attach_ai_agent": TARGET_AGENT_NAME,
                },
                "canApplyWithCurrentToken": status == 200 and result.get("privateWidgetScope", {}).get("status") == 200,
            }
        )

        status, agent_payload = get_json(
            ghl23,
            f"https://services.leadconnectorhq.com/agent-studio/agent/{AGENT_ID}",
            params={"locationId": location_id},
        )
        agent = agent_payload.get("agent") if isinstance(agent_payload, dict) else {}
        if not isinstance(agent, dict):
            agent = {}
        version = prod_version(agent)
        if not version:
            blockers.append("Could not find production Agent Studio version.")
        else:
            prepared_payload = build_agent_payload(version, location_id)
            result["agentPatchPreview"] = {
                "agentId": AGENT_ID,
                "versionId": version.get("versionId"),
                "newVersionName": prepared_payload["versionName"],
                "nodeCount": len(prepared_payload["nodes"]),
                "runtimeVariableKeys": [item["key"] for item in TARGET_RUNTIME_VARIABLES],
                "promptContainsINMC": "Integrative Natural Medical Clinic" in TARGET_PROMPT,
                "chatTriggerWillBeEnabled": any(
                    ((node.get("nodeConfig") or {}).get("triggerType") == "chat")
                    and ((node.get("nodeConfig") or {}).get("enabled") is True)
                    for node in prepared_payload["nodes"]
                ),
            }
            actions.append(
                {
                    "target": "agent-studio-version",
                    "agentId": AGENT_ID,
                    "versionId": version.get("versionId"),
                    "changes": [
                        "enable chat trigger",
                        "replace generic B2B prompt with INMC concierge prompt",
                        "replace empty runtime variable key set",
                        "allow human fallback",
                    ],
                    "canApplyWithCurrentToken": True,
                }
            )

        status, pipelines = get_json(
            ghl21,
            "https://services.leadconnectorhq.com/opportunities/pipelines",
            params={"locationId": location_id},
        )
        pipeline_rows = pipelines.get("pipelines") if isinstance(pipelines, dict) else []
        if not isinstance(pipeline_rows, list):
            pipeline_rows = []
        website_pipeline = next((item for item in pipeline_rows if item.get("name") == WEBSITE_PIPELINE_NAME), {})
        actions.append(
            {
                "target": "pipeline",
                "pipelineId": website_pipeline.get("id"),
                "currentStages": [stage.get("name") for stage in website_pipeline.get("stages") or []],
                "targetStages": TARGET_STAGE_NAMES,
                "canApplyWithCurrentToken": False,
                "reason": "Pipeline stage update endpoint was not exercised; keep as UI/manual or separate scoped script.",
            }
        )

    if args.apply and not args.confirm_live_ghl_chatbot_repair:
        blockers.append("Apply requested without --confirm-live-ghl-chatbot-repair.")

    # Full live apply must be all-or-nothing for this repair. Do not partially
    # enable the agent while the public widget cannot be updated or attached.
    if any(action.get("target") == "chat-widget" and not action.get("canApplyWithCurrentToken") for action in actions):
        blockers.append("Widget cannot be updated with current token, so live apply is blocked.")

    result["blockers"] = blockers
    result["safeToApply"] = bool(args.apply and args.confirm_live_ghl_chatbot_repair and not blockers)

    if args.write_report:
        Path("reports").mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        out = Path("reports") / f"inmc-chatbot-repair-preflight-{stamp}.json"
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        result["reportPath"] = str(out)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.apply:
        print("Live apply is intentionally not executed by this version until widget scope is available.")
        return 2

    return 0 if not blockers else 1


if __name__ == "__main__":
    sys.exit(main())
