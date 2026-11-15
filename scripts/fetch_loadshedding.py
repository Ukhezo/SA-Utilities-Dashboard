"""Fetch load-shedding data from the EskomSePush Business API and save it as JSON.

EskomSePush does not allow requests straight from a web page (no CORS), and the
API token must stay private. So this script runs on GitHub Actions on a schedule,
using the token stored as the repository secret ESP_TOKEN, and writes
data/loadshedding.json. The dashboard then reads that file.

Environment variables:
    ESP_TOKEN   EskomSePush API token (required)
    ESP_AREA    area to search for the first time (default: Cape Town)

Calls per run: 2 (status + schedule). The area and schedule IDs are saved in the
JSON file, so the area search (2 extra calls) only happens on the first run or
when ESP_AREA changes.

Usage:
    ESP_TOKEN=xxxx python scripts/fetch_loadshedding.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://developer.sepush.co.za/business/3.1"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "loadshedding.json"
DEFAULT_AREA = "Cape Town"


class EspError(RuntimeError):
    """The EskomSePush API returned an error or an unexpected response."""


def api_get(path: str, token: str, **params: str) -> dict:
    """GET an EskomSePush endpoint and return the decoded JSON."""
    url = f"{API_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"token": token, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")[:200]
        hints = {403: "check that ESP_TOKEN is correct", 429: "daily API allowance used up"}
        hint = f" ({hints[err.code]})" if err.code in hints else ""
        raise EspError(f"{path} returned HTTP {err.code}{hint}: {body}") from err
    except urllib.error.URLError as err:
        raise EspError(f"could not reach EskomSePush: {err.reason}") from err


def find_area(token: str, query: str) -> dict:
    """Search for an area by name and return the best match."""
    data = api_get("areas_search", token, text=query)
    areas = [a for a in data.get("areas", []) if isinstance(a, dict) and a.get("id") is not None]
    if not areas:
        raise EspError(f'no EskomSePush area found for "{query}"')
    exact = [a for a in areas if str(a.get("name", "")).lower() == query.lower()]
    return (exact or areas)[0]


def find_schedule(token: str, area_id: str) -> dict:
    """Return the recommended load-shedding schedule for an area."""
    data = api_get("area", token, id=area_id)
    schedules = [
        s for s in data.get("schedules", [])
        if isinstance(s, dict) and s.get("type") == "loadshedding" and s.get("id") is not None
    ]
    if not schedules:
        raise EspError(f"no load-shedding schedule listed for area {area_id}")
    return next((s for s in schedules if s.get("auto_enabled")), schedules[0])


def national_stage(status: dict) -> dict:
    """Pull the national stage and upcoming stage changes out of a status response."""
    eskom = (status.get("status") or {}).get("eskom") or {}
    stage = eskom.get("stage")
    return {
        "stage": int(stage) if str(stage).isdigit() else None,
        "updated": eskom.get("stage_updated"),
        "next_stages": [
            {"stage": int(s["stage"]) if str(s.get("stage")).isdigit() else s.get("stage"),
             "start": s.get("stage_start_timestamp")}
            for s in eskom.get("next_stages", []) if isinstance(s, dict)
        ],
    }


def clean_events(schedule: dict) -> list[dict]:
    """Keep only the fields the dashboard shows."""
    events = schedule.get("events")
    if not isinstance(events, list):
        raise EspError("the schedule response did not contain an events list")
    return [
        {"start": e.get("start"), "end": e.get("end"), "note": e.get("note") or "Load-shedding"}
        for e in events if isinstance(e, dict)
    ]


def load_previous(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def build_snapshot(token: str, area_query: str, previous: dict) -> dict:
    """Fetch everything and return the data to save."""
    area = previous.get("area") or {}
    if area.get("query") != area_query or not area.get("id") or not area.get("schedule_id"):
        found = find_area(token, area_query)
        schedule_info = find_schedule(token, str(found["id"]))
        area = {
            "query": area_query,
            "id": str(found["id"]),
            "name": found.get("name") or area_query,
            "region": found.get("region") or found.get("municipality") or "",
            "schedule_id": str(schedule_info["id"]),
        }

    schedule = api_get("schedule", token, id=area["schedule_id"])
    status = api_get("status", token)
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "EskomSePush Business API v3.1",
        "area": area,
        "schedule_name": schedule.get("name") or area["schedule_id"],
        "national": national_stage(status),
        "events": clean_events(schedule),
    }


def main() -> int:
    token = os.environ.get("ESP_TOKEN", "").strip()
    if not token:
        print("ESP_TOKEN is not set. Add it as a repository secret to enable load-shedding updates.")
        return 0  # not an error: the dashboard shows a 'not set up yet' message

    area_query = os.environ.get("ESP_AREA", "").strip() or DEFAULT_AREA
    try:
        snapshot = build_snapshot(token, area_query, load_previous(OUTPUT))
    except EspError as err:
        print(f"Load-shedding update failed: {err}", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    stage = snapshot["national"]["stage"]
    print(f"Saved {len(snapshot['events'])} event(s) for {snapshot['area']['name']}; national stage {stage}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
