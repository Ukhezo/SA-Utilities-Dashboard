"""Tests for the load-shedding fetcher, using fake API responses (no network, no credits)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_loadshedding as esp

AREAS = {"areas": [{"id": "abc-greytown", "name": "Greytown", "region": "Umvoti"},
                   {"id": "abc-other", "name": "Greytown Ext 1", "region": "Umvoti"}]}
AREA = {"name": "Greytown", "schedules": [
    {"id": "s-water", "type": "water"},
    {"id": "s-1", "type": "loadshedding", "auto_enabled": False},
    {"id": "s-2", "type": "loadshedding", "auto_enabled": True},
]}
SCHEDULE = {"name": "Greytown block 7", "events": [
    {"start": "2026-11-15T18:00:00+02:00", "end": "2026-11-15T20:30:00+02:00", "note": "Stage 2", "extra": 1},
]}
STATUS = {"status": {"eskom": {"stage": "2", "stage_updated": "2026-11-15T05:00:00+02:00",
                               "next_stages": [{"stage": "0", "stage_start_timestamp": "2026-11-16T05:00:00+02:00"}]}}}


@pytest.fixture
def fake_api(monkeypatch):
    calls = []
    responses = {"areas_search": AREAS, "area": AREA, "schedule": SCHEDULE, "status": STATUS}

    def api_get(path, token, **params):
        calls.append((path, params))
        assert token == "test-token"
        return responses[path]

    monkeypatch.setattr(esp, "api_get", api_get)
    return calls


def test_first_run_searches_area_and_picks_recommended_schedule(fake_api):
    snap = esp.build_snapshot("test-token", "Greytown", previous={})
    assert snap["area"] == {"query": "Greytown", "id": "abc-greytown", "name": "Greytown",
                            "region": "Umvoti", "schedule_id": "s-2"}
    assert [c[0] for c in fake_api] == ["areas_search", "area", "schedule", "status"]


def test_later_runs_reuse_saved_ids_and_use_two_calls(fake_api):
    previous = {"area": {"query": "Greytown", "id": "abc-greytown", "name": "Greytown",
                         "region": "Umvoti", "schedule_id": "s-2"}}
    esp.build_snapshot("test-token", "Greytown", previous)
    assert [c[0] for c in fake_api] == ["schedule", "status"]


def test_changing_area_searches_again(fake_api):
    previous = {"area": {"query": "Kranskop", "id": "x", "name": "Kranskop", "schedule_id": "y"}}
    esp.build_snapshot("test-token", "Greytown", previous)
    assert fake_api[0][0] == "areas_search"


def test_snapshot_contents(fake_api):
    snap = esp.build_snapshot("test-token", "Greytown", previous={})
    assert snap["national"]["stage"] == 2
    assert snap["national"]["next_stages"] == [{"stage": 0, "start": "2026-11-16T05:00:00+02:00"}]
    assert snap["schedule_name"] == "Greytown block 7"
    assert snap["events"] == [{"start": "2026-11-15T18:00:00+02:00", "end": "2026-11-15T20:30:00+02:00",
                               "note": "Stage 2"}]


def test_no_areas_found(monkeypatch):
    monkeypatch.setattr(esp, "api_get", lambda *a, **k: {"areas": []})
    with pytest.raises(esp.EspError, match="no EskomSePush area"):
        esp.find_area("t", "Nowhere")


def test_no_loadshedding_schedule(monkeypatch):
    monkeypatch.setattr(esp, "api_get", lambda *a, **k: {"schedules": [{"id": "w", "type": "water"}]})
    with pytest.raises(esp.EspError, match="no load-shedding schedule"):
        esp.find_schedule("t", "abc")


def test_missing_token_is_not_an_error(monkeypatch, capsys):
    monkeypatch.delenv("ESP_TOKEN", raising=False)
    assert esp.main() == 0
    assert "not set" in capsys.readouterr().out


def test_main_writes_json(fake_api, monkeypatch, tmp_path):
    out = tmp_path / "loadshedding.json"
    monkeypatch.setattr(esp, "OUTPUT", out)
    monkeypatch.setenv("ESP_TOKEN", "test-token")
    monkeypatch.delenv("ESP_AREA", raising=False)
    assert esp.main() == 0
    saved = json.loads(out.read_text())
    assert saved["area"]["name"] == "Greytown"
    assert saved["updated_at"].endswith("+00:00")


def test_api_error_keeps_old_file(monkeypatch, tmp_path):
    out = tmp_path / "loadshedding.json"
    out.write_text('{"old": true}')
    monkeypatch.setattr(esp, "OUTPUT", out)
    monkeypatch.setenv("ESP_TOKEN", "test-token")

    def boom(*a, **k):
        raise esp.EspError("status returned HTTP 429 (daily API allowance used up)")

    monkeypatch.setattr(esp, "api_get", boom)
    assert esp.main() == 1
    assert json.loads(out.read_text()) == {"old": True}
