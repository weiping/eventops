"""Every morning: pull registrants for open events, screen them, post the list."""

from __future__ import annotations

import csv
import json
import logging
import os
import pathlib
import re
import subprocess

from scripts.platform_client import EventPlatform, dry_run_enabled
from scripts.screening import screen, summarise

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("screening")

COMPETITORS = pathlib.Path("config/competitor-domains.txt")

# setup_event.py 把这一行写进汇总评论，这里再读回来。
_PLATFORM_ID = re.compile(r"platform_event_id[:=]\s*`?([A-Za-z0-9_-]+)`?")


def extract_platform_id(body: str | None) -> str | None:
    match = _PLATFORM_ID.search(body or "")
    return match.group(1) if match else None


def account_domains() -> set[str]:
    """CRM 没有 API，它的命令行工具走浏览器登录，所以这里没有第二个密钥要管。"""
    out = subprocess.run(
        ["crm", "export", "accounts", "--fields", "domain", "--format", "csv"],
        check=True, capture_output=True, text=True,
    ).stdout
    return {row["domain"].strip().lower() for row in csv.DictReader(out.splitlines()) if row.get("domain")}


def competitor_domains() -> set[str]:
    if not COMPETITORS.exists():
        return set()
    return {
        line.strip().lower()
        for line in COMPETITORS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def open_events() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--label", "event-staged", "--state", "open",
         "--json", "number,title,body", "--limit", "100"],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)


def report(processed: int, skipped: int, failed: int) -> None:
    line = f"processed {processed}, skipped {skipped}, failed {failed}"
    log.info(line)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Morning screening\n\n{line}\n")


def main() -> int:
    platform = EventPlatform()
    accounts, rivals = account_domains(), competitor_domains()
    processed = skipped = failed = 0

    for issue in open_events():
        event_id = extract_platform_id(issue["body"])
        if not event_id:
            log.warning("issue #%s has no platform_event_id yet, skipping", issue["number"])
            skipped += 1
            continue
        try:
            registrants = platform.list_registrants(event_id)
        except Exception:
            log.exception("could not fetch registrants for issue #%s", issue["number"])
            failed += 1
            continue

        decisions = [(r, screen(r, accounts, rivals)) for r in registrants]
        body = f"Registrants as of today: {len(registrants)}\n\n" + summarise(decisions)

        for registrant, decision in decisions:
            if decision.verdict == "approve" and not dry_run_enabled():
                platform.approve_registrant(event_id, registrant["id"])

        subprocess.run(["gh", "issue", "comment", str(issue["number"]), "--body", body], check=True)
        processed += 1

    report(processed, skipped, failed)

    # 一个活动都没处理，本身就是故障。成功地什么也没干，是最难发现的那种失败。
    if processed == 0:
        log.error("no event was screened at all, treating this run as a failure")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
