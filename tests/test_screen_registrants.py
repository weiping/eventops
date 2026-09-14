import pytest

from scripts import screen_registrants as sr


@pytest.mark.parametrize("body,expected", [
    ("- platform_event_id: `evt_abc-123`", "evt_abc-123"),
    ("platform_event_id: evt_20261112_jp", "evt_20261112_jp"),
    ("platform_event_id=evt_x", "evt_x"),
    ("### Notes\n\nnothing here", None),
    ("", None),
    (None, None),
])
def test_extract_platform_id(body, expected):
    assert sr.extract_platform_id(body) == expected


def test_empty_run_is_a_failure(monkeypatch):
    monkeypatch.setattr(sr, "EventPlatform", lambda *a, **k: object())
    monkeypatch.setattr(sr, "account_domains", set)
    monkeypatch.setattr(sr, "competitor_domains", set)
    monkeypatch.setattr(sr, "open_events", list)
    assert sr.main() == 1


def test_all_events_skipped_is_also_a_failure(monkeypatch):
    monkeypatch.setattr(sr, "EventPlatform", lambda *a, **k: object())
    monkeypatch.setattr(sr, "account_domains", set)
    monkeypatch.setattr(sr, "competitor_domains", set)
    monkeypatch.setattr(sr, "open_events", lambda: [{"number": 1, "body": "no id here"}])
    assert sr.main() == 1
