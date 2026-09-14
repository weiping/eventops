"""Thin client for the event platform, with the DRY_RUN gate built in."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger("platform")

SAFE_METHODS = {"GET", "HEAD"}


def dry_run_enabled() -> bool:
    """未设置、空串、纯空白，一律当作彩排。Actions 在仓库变量缺失时注入的正是空串。"""
    value = (os.environ.get("DRY_RUN") or "").strip().lower()
    return (value or "true") in {"1", "true", "yes", "on"}


class PlatformError(RuntimeError):
    pass


class EventPlatform:
    def __init__(self, base_url: str | None = None, token: str | None = None, dry_run: bool | None = None):
        self.base_url = (base_url or os.environ["EVENT_PLATFORM_URL"]).rstrip("/")
        self.token = token or os.environ["EVENT_PLATFORM_TOKEN"]
        self.dry_run = dry_run_enabled() if dry_run is None else dry_run

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if self.dry_run and method.upper() not in SAFE_METHODS:
            log.warning("[DRY_RUN] skipped %s %s payload=%s", method, path,
                        json.dumps(payload, ensure_ascii=False))
            return {"dry_run": True, "method": method, "path": path, "request": payload or {}}

        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as exc:
            raise PlatformError(f"{method} {path} -> {exc.code} {exc.read()[:400]!r}") from exc

    # Reads are allowed during a rehearsal; they change nothing.
    def get_event(self, event_id: str) -> dict:
        return self._request("GET", f"/v1/events/{event_id}")

    def list_registrants(self, event_id: str) -> list[dict]:
        return self._request("GET", f"/v1/events/{event_id}/registrants").get("items", [])

    # Writes are what DRY_RUN holds back.
    def clone_event(self, reference_event_id: str, event) -> dict:
        return self._request(
            "POST",
            f"/v1/events/{reference_event_id}/copy",
            {
                "name": event.title,
                "starts_at": f"{event.event_date.isoformat()}T{event.start_time}:00",
                "timezone": event.timezone,
                "external_ref": event.campaign,
                "status": "draft",
            },
        )

    def approve_registrant(self, event_id: str, registrant_id: str) -> dict:
        return self._request("POST", f"/v1/events/{event_id}/registrants/{registrant_id}/approve")
