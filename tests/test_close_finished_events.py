from datetime import date

from scripts import close_finished_events as cf
from tests.test_event_form import BODY


def _run(monkeypatch, today, body=BODY):
    calls = []
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setattr(cf, "staged_events", lambda: [{"number": 7, "body": body}])
    monkeypatch.setattr(cf.subprocess, "run", lambda *a, **k: calls.append(a[0]))
    cf.main(today=today)
    return calls


def test_event_still_upcoming_is_left_alone(monkeypatch):
    assert _run(monkeypatch, date(2026, 11, 11)) == []


def test_event_day_itself_is_left_alone(monkeypatch):
    assert _run(monkeypatch, date(2026, 11, 12)) == []


def test_day_after_flips_the_label(monkeypatch):
    calls = _run(monkeypatch, date(2026, 11, 13))
    assert calls and "--add-label" in calls[0] and "event-done" in calls[0]


def test_unparsable_issue_is_skipped(monkeypatch):
    assert _run(monkeypatch, date(2027, 1, 1), body="garbage") == []
