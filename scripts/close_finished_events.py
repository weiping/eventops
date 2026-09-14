"""Move an event from event-staged to event-done once its date has passed."""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import date, timedelta

from scripts.event_form import FormError, parse_event
from scripts.platform_client import dry_run_enabled

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("close")

# 活动当天之后留一天缓冲，等平台那边的出席数据落库。
GRACE = timedelta(days=1)


def staged_events() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--label", "event-staged", "--state", "open",
         "--json", "number,body", "--limit", "100"],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def main(today: date | None = None) -> int:
    today = today or date.today()
    for issue in staged_events():
        try:
            event = parse_event(issue["body"])
        except FormError as exc:
            log.warning("issue #%s cannot be parsed, leaving it alone (%s)", issue["number"], exc)
            continue
        if today < event.event_date + GRACE:
            continue
        log.info("issue #%s: %s is over, marking it done", issue["number"], event.campaign)
        if dry_run_enabled():
            continue
        subprocess.run(
            ["gh", "issue", "edit", str(issue["number"]),
             "--remove-label", "event-staged", "--add-label", "event-done"],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
