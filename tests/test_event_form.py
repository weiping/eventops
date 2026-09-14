import pathlib
from datetime import date

import pytest

from scripts.event_form import FormError, fiscal_quarter, parse_event, split_sections
from scripts.utm import ChannelError, build_links, tag

BODY = (pathlib.Path(__file__).parent / "fixtures" / "webinar-issue.md").read_text(encoding="utf-8")


def test_split_sections_keeps_every_label():
    assert "Event title" in split_sections(BODY)
    assert split_sections(BODY)["Region"] == "JP"


def test_parse_event_happy_path():
    event = parse_event(BODY)
    assert event.event_date == date(2026, 11, 12)
    assert event.region == "JP"
    assert event.timezone == "Asia/Tokyo"
    assert event.channels == ("X", "Newsletter")
    assert event.notes == ""
    assert event.campaign == "FY27Q2-JP-WEBINAR-AI-DEV"


def test_crlf_bodies_parse_the_same():
    assert parse_event(BODY.replace("\n", "\r\n")).campaign == parse_event(BODY).campaign


@pytest.mark.parametrize(
    "day,expected",
    [
        (date(2026, 7, 1), "FY27Q1"),
        (date(2026, 11, 12), "FY27Q2"),
        (date(2027, 2, 3), "FY27Q3"),
        (date(2027, 6, 30), "FY27Q4"),
    ],
)
def test_fiscal_quarter(day, expected):
    assert fiscal_quarter(day) == expected


def test_missing_required_field_is_rejected():
    broken = BODY.replace("2026-11-12", "_No response_")
    with pytest.raises(FormError, match="missing required field"):
        parse_event(broken)


def test_bad_date_is_rejected():
    with pytest.raises(FormError, match="YYYY-MM-DD"):
        parse_event(BODY.replace("2026-11-12", "11/12/2026"))


def test_topic_slug_must_be_kebab_case():
    with pytest.raises(FormError, match="lowercase"):
        parse_event(BODY.replace("ai-dev", "AI Dev"))


def test_renaming_a_label_fails_loudly():
    with pytest.raises(FormError, match="missing required field"):
        parse_event(BODY.replace("### Region", "### Market"))


def test_utm_links_are_stable():
    links = build_links("https://events.example.com/jp-ai-dev",
                        "FY27Q2-JP-WEBINAR-AI-DEV", ["X", "Newsletter"])
    assert links["X"] == (
        "https://events.example.com/jp-ai-dev"
        "?utm_source=x&utm_medium=social&utm_campaign=fy27q2-jp-webinar-ai-dev"
    )
    assert "utm_source=newsletter" in links["Newsletter"]


def test_existing_query_string_survives():
    out = tag("https://e.example.com/p?lang=ja", "FY27Q2-JP-WEBINAR-AI-DEV", "x", "social")
    assert "lang=ja" in out
    assert out.index("utm_source") < out.index("utm_medium") < out.index("utm_campaign")


def test_unknown_channel_is_rejected():
    with pytest.raises(ChannelError):
        build_links("https://e.example.com/p", "FY27Q2-JP-WEBINAR-AI-DEV", ["Telegram"])
