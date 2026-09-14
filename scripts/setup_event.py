"""Stage one event. Reads EVENT (JSON) from the environment, writes files and a summary."""

from __future__ import annotations

import json
import logging
import os
import pathlib
from datetime import date

from scripts.event_form import Event
from scripts.platform_client import EventPlatform, dry_run_enabled
from scripts.utm import as_markdown, build_links

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("setup")

DRAFTS = pathlib.Path("drafts")
TEMPLATES = pathlib.Path("templates")


def event_from_env() -> Event:
    raw = json.loads(os.environ["EVENT"])
    return Event(
        title=raw["title"],
        event_date=date.fromisoformat(raw["event_date"]),
        start_time=raw["start_time"],
        region=raw["region"],
        event_type=raw["event_type"],
        topic=raw["topic"],
        audience=raw["audience"],
        channels=tuple(raw["channels"]),
        reference_event_id=raw["reference_event_id"],
        notes=raw["notes"],
    )


def render(template_name: str, **values) -> str:
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def main() -> int:
    event = event_from_env()
    dry_run = dry_run_enabled()
    platform = EventPlatform(dry_run=dry_run)

    landing = platform.clone_event(event.reference_event_id, event)
    landing_url = landing.get("public_url") or \
        f"https://events.example.com/preview/{event.campaign.lower()}"
    platform_event_id = landing.get("id", "pending-dry-run")

    links = build_links(landing_url, event.campaign, event.channels)

    out = DRAFTS / event.campaign
    out.mkdir(parents=True, exist_ok=True)
    (out / "invitation.md").write_text(
        render(
            f"invitation-{event.region.lower()}.md",
            title=event.title,
            date=event.event_date.isoformat(),
            time=f"{event.start_time} {event.timezone}",
            url=links.get("Invitation email", landing_url),
        ),
        encoding="utf-8",
    )
    (out / "request.md").write_text(
        "\n".join(
            [
                f"Campaign: `{event.campaign}`",
                f"Send date: {event.event_date.isoformat()} minus 10 days",
                f"Audience: {event.audience or 'see the event issue'}",
                "",
                "Body: `" + str(out / "invitation.md") + "`",
                "",
                as_markdown(links),
            ]
        ),
        encoding="utf-8",
    )
    (out / "links.json").write_text(json.dumps(links, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = "\n".join(
        [
            f"### `{event.campaign}` staged"
            + ("  (DRY RUN, nothing left this repository)" if dry_run else ""),
            "",
            f"- platform_event_id: `{platform_event_id}`",
            f"- Landing page: {landing_url}",
            f"- Local time: {event.event_date.isoformat()} {event.start_time} {event.timezone}",
            f"- Invitation draft: `{out / 'invitation.md'}`",
            "",
            as_markdown(links),
        ]
    )
    pathlib.Path("summary.md").write_text(summary, encoding="utf-8")
    log.info("staged %s (dry_run=%s)", event.campaign, dry_run)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
