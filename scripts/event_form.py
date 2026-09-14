"""Parse an issue created from a GitHub issue form into a validated Event."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date

NO_RESPONSE = "_No response_"

_HEADING = re.compile(r"^###[ \t]+(?P<label>.+?)[ \t]*$")
_CHECKBOX = re.compile(r"^[-*][ \t]+\[(?P<mark>[ xX])\][ \t]*(?P<label>.*)$")

# The rendered issue body is keyed by the field *label*, not by the field id.
# Rename a label in the YAML and you must rename it here too; the test suite
# below is what stops that from shipping silently.
LABEL_TO_KEY = {
    "Event title": "title",
    "Event date (YYYY-MM-DD)": "event_date",
    "Start time (local, HH:MM)": "start_time",
    "Region": "region",
    "Event type": "event_type",
    "Topic slug": "topic",
    "Target audience": "audience",
    "Promotion channels": "channels",
    "Reference event ID": "reference_event_id",
    "Notes": "notes",
}

REQUIRED = ("title", "event_date", "start_time", "region", "event_type", "topic")

REGION_TZ = {"JP": "Asia/Tokyo", "KR": "Asia/Seoul", "APAC": "Asia/Singapore"}
EVENT_TYPES = {"webinar": "WEBINAR", "meetup": "MEETUP", "exec-roundtable": "EXEC"}

_TOPIC = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CAMPAIGN = re.compile(r"^FY\d{2}Q[1-4]-(?:JP|KR|APAC)-(?:WEBINAR|MEETUP|EXEC)-[A-Z0-9-]+$")


class FormError(ValueError):
    """Raised when the issue body cannot be turned into a usable Event."""


def split_sections(body: str) -> dict[str, str]:
    """Split a rendered issue-form body into {label: raw text} sections."""
    sections: dict[str, str] = {}
    label, buf = None, []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        heading = _HEADING.match(line)
        if heading:
            if label is not None:
                sections[label] = "\n".join(buf).strip()
            label, buf = heading.group("label"), []
        elif label is not None:
            buf.append(line)
    if label is not None:
        sections[label] = "\n".join(buf).strip()
    return sections


def _normalise(raw: str) -> str | list[str]:
    if raw == NO_RESPONSE or raw == "":
        return ""
    lines = raw.split("\n")
    boxes = [_CHECKBOX.match(line.strip()) for line in lines if line.strip()]
    if boxes and all(boxes):
        return [b.group("label").strip() for b in boxes if b.group("mark").lower() == "x"]
    return raw


def fiscal_quarter(day: date) -> str:
    """Fiscal year starts on July 1. 2026-11-12 falls in FY27Q2."""
    fy = day.year + 1 if day.month >= 7 else day.year
    q = ((day.month - 7) % 12) // 3 + 1
    return f"FY{fy % 100:02d}Q{q}"


@dataclass(frozen=True)
class Event:
    title: str
    event_date: date
    start_time: str
    region: str
    event_type: str
    topic: str
    audience: str
    channels: tuple[str, ...]
    reference_event_id: str
    notes: str

    @property
    def timezone(self) -> str:
        return REGION_TZ[self.region]

    @property
    def campaign(self) -> str:
        return "-".join(
            [
                fiscal_quarter(self.event_date),
                self.region,
                EVENT_TYPES[self.event_type],
                self.topic.upper(),
            ]
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["event_date"] = self.event_date.isoformat()
        data["channels"] = list(self.channels)
        data["campaign"] = self.campaign
        data["timezone"] = self.timezone
        return data


def parse_event(body: str) -> Event:
    fields = {
        LABEL_TO_KEY[label]: _normalise(raw)
        for label, raw in split_sections(body).items()
        if label in LABEL_TO_KEY
    }

    missing = [k for k in REQUIRED if not fields.get(k)]
    if missing:
        raise FormError(f"missing required field(s): {', '.join(missing)}")

    try:
        day = date.fromisoformat(str(fields["event_date"]))
    except ValueError as exc:
        raise FormError(f"event date is not YYYY-MM-DD: {fields['event_date']!r}") from exc

    if not re.fullmatch(r"[0-2]\d:[0-5]\d", str(fields["start_time"])):
        raise FormError(f"start time is not HH:MM: {fields['start_time']!r}")

    region = str(fields["region"]).upper()
    if region not in REGION_TZ:
        raise FormError(f"unknown region: {region}")

    event_type = str(fields["event_type"]).strip().lower()
    if event_type not in EVENT_TYPES:
        raise FormError(f"unknown event type: {event_type}")

    topic = str(fields["topic"]).strip().lower()
    if not _TOPIC.fullmatch(topic):
        raise FormError(f"topic slug must be lowercase words joined by '-': {topic!r}")

    channels = fields.get("channels") or []
    event = Event(
        title=str(fields["title"]).strip(),
        event_date=day,
        start_time=str(fields["start_time"]),
        region=region,
        event_type=event_type,
        topic=topic,
        audience=str(fields.get("audience") or "").strip(),
        channels=tuple(channels) if isinstance(channels, list) else (),
        reference_event_id=str(fields.get("reference_event_id") or "").strip(),
        notes=str(fields.get("notes") or "").strip(),
    )

    if not _CAMPAIGN.fullmatch(event.campaign):
        raise FormError(f"generated campaign name breaks the naming rule: {event.campaign}")
    return event


if __name__ == "__main__":
    import json
    import os
    import sys

    try:
        event = parse_event(sys.stdin.read())
    except FormError as exc:
        print(f"::error title=Invalid event form::{exc}", file=sys.stderr)
        raise SystemExit(1) from None

    payload = json.dumps(event.to_dict(), ensure_ascii=False)
    print(payload)
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"event={payload}\n")
