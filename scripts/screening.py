"""Classify registrants for invite-only events."""

from __future__ import annotations

from dataclasses import dataclass

FREE_MAIL = {"gmail.com", "outlook.com", "yahoo.co.jp", "naver.com", "icloud.com", "qq.com"}
EDU_SUFFIXES = (".edu", ".ac.jp", ".ac.kr", ".edu.cn", ".edu.sg")

VERDICTS = ("approve", "review", "reject")


@dataclass(frozen=True)
class Decision:
    verdict: str
    reason: str


def domain_of(email: str) -> str:
    return email.strip().rsplit("@", 1)[-1].lower() if "@" in email else ""


def screen(registrant: dict, account_domains: set[str], competitor_domains: set[str]) -> Decision:
    """account_domains comes from the CRM export, competitor_domains from a checked-in list."""
    domain = domain_of(registrant.get("email", ""))
    if not domain:
        return Decision("reject", "no usable email address")
    if domain in competitor_domains:
        return Decision("reject", f"competitor domain ({domain})")
    if domain.endswith(EDU_SUFFIXES):
        return Decision("reject", "student or academic address")
    if domain in FREE_MAIL:
        return Decision("review", "personal mailbox, company cannot be verified")
    if domain in account_domains:
        return Decision("approve", f"matches a known account ({domain})")
    return Decision("review", f"unknown corporate domain ({domain})")


def summarise(decisions: list[tuple[dict, Decision]]) -> str:
    counts = {v: 0 for v in VERDICTS}
    for _, d in decisions:
        counts[d.verdict] += 1
    header = " / ".join(f"{v} {counts[v]}" for v in VERDICTS)
    rows = "\n".join(
        f"| {r.get('name', '')} | {domain_of(r.get('email', ''))} | {d.verdict} | {d.reason} |"
        for r, d in decisions
        if d.verdict != "approve"
    )
    table = "| Name | Domain | Verdict | Reason |\n| --- | --- | --- | --- |\n" + rows
    return f"**{header}**\n\n{table if rows else '_Nothing needs a human this morning._'}"
