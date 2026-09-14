"""Build the UTM-tagged URL set for one campaign."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# One row per promotion channel. The labels on the left must match the
# checkbox labels in the issue form.
CHANNELS = {
    "X": ("x", "social"),
    "LinkedIn": ("linkedin", "social"),
    "Newsletter": ("newsletter", "email"),
    "Invitation email": ("invite", "email"),
    "Partner": ("partner", "referral"),
    "Community Slack": ("slack", "community"),
}


class ChannelError(ValueError):
    pass


def tag(url: str, campaign: str, source: str, medium: str, content: str = "") -> str:
    """Add UTM parameters to a URL, keeping any query string already there."""
    parts = urlsplit(url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    params.update(
        {
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign.lower(),
        }
    )
    if content:
        params["utm_content"] = content
    ordered = ["utm_source", "utm_medium", "utm_campaign", "utm_content"]
    query = urlencode(
        sorted(params.items(), key=lambda kv: (ordered.index(kv[0]) if kv[0] in ordered else -1, kv[0]))
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def build_links(landing_url: str, campaign: str, channels) -> dict[str, str]:
    unknown = [c for c in channels if c not in CHANNELS]
    if unknown:
        raise ChannelError(f"unknown channel(s): {', '.join(unknown)}")
    return {
        name: tag(landing_url, campaign, *CHANNELS[name])
        for name in channels
    }


def as_markdown(links: dict[str, str]) -> str:
    rows = "\n".join(f"| {name} | `{url}` |" for name, url in links.items())
    return "| Channel | URL |\n| --- | --- |\n" + rows
