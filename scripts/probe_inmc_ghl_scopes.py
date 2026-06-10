#!/usr/bin/env python3
"""Read-only scope probe for local GHL credentials against the INMC location."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


DEFAULT_ENV = Path("/Users/danielaroustamian/.env")
DEFAULT_LOCATION_ENV = "GHL_LOC_INMC"
DEFAULT_LOCATION_ID = "x8il6XPJdeSXlgJFFiCJ"


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


def call(token: str, version: str, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Version": version,
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
    )
    try:
        response = session.get(url, params=params, timeout=20)
        try:
            body = response.json()
        except Exception:
            body = {}
        message = body.get("message") if isinstance(body, dict) else None
        location_name = None
        if isinstance(body, dict):
            location = body.get("location") or body
            if isinstance(location, dict):
                location_name = location.get("name") or location.get("businessName")
        return {"status": response.status_code, "message": message, "locationName": location_name}
    except Exception as exc:
        return {"status": 0, "message": str(exc), "locationName": None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--location-id", default=None)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    env = load_env(Path(args.env))
    location_id = args.location_id or env.get(DEFAULT_LOCATION_ENV) or DEFAULT_LOCATION_ID
    token_keys = sorted(
        key
        for key, value in env.items()
        if key.upper().startswith("GHL") and value.startswith("pit-") and len(value) == 40
    )

    rows = []
    for key in token_keys:
        token = env[key]
        row = {
            "key": key,
            "fingerprint": hashlib.sha256(token.encode()).hexdigest()[:12],
            "length": len(token),
        }
        location = call(token, "2021-07-28", f"https://services.leadconnectorhq.com/locations/{location_id}")
        widget = call(
            token,
            "2023-02-21",
            "https://services.leadconnectorhq.com/chat-widget/list",
            {"locationId": location_id, "limit": 1, "offset": 0},
        )
        agent = call(
            token,
            "2023-02-21",
            "https://services.leadconnectorhq.com/agent-studio/agent",
            {"locationId": location_id, "limit": 1, "offset": 0},
        )
        row.update(
            {
                "locationStatus": location["status"],
                "locationName": location.get("locationName"),
                "chatWidgetStatus": widget["status"],
                "chatWidgetMessage": widget.get("message"),
                "agentStudioStatus": agent["status"],
                "agentStudioMessage": agent.get("message"),
                "usableForPrivateWidget": widget["status"] == 200,
                "usableForAgentStudio": agent["status"] == 200,
            }
        )
        rows.append(row)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "locationId": location_id,
        "tokenCount": len(rows),
        "privateWidgetTokenFound": any(row["usableForPrivateWidget"] for row in rows),
        "agentStudioTokenFound": any(row["usableForAgentStudio"] for row in rows),
        "rows": rows,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.write_report:
        Path("reports").mkdir(exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = Path("reports") / f"inmc-ghl-scope-probe-{stamp}.json"
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"reportPath": str(path)}))

    return 0 if report["privateWidgetTokenFound"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

