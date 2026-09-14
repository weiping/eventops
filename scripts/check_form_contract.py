"""Fail the build if an issue-form label no longer maps to a parser key."""

from __future__ import annotations

import pathlib
import sys

import yaml

from scripts.event_form import LABEL_TO_KEY
from scripts.utm import CHANNELS

FORMS = pathlib.Path(".github/ISSUE_TEMPLATE")


def main() -> int:
    problems: list[str] = []
    for form in sorted(FORMS.glob("*.yml")):
        spec = yaml.safe_load(form.read_text(encoding="utf-8"))
        for block in spec.get("body", []):
            attrs = block.get("attributes", {})
            label = attrs.get("label")
            if not label or block.get("type") == "markdown":
                continue
            if label not in LABEL_TO_KEY:
                problems.append(f"{form.name}: label {label!r} has no key in LABEL_TO_KEY")
            if block.get("type") == "checkboxes" and LABEL_TO_KEY.get(label) == "channels":
                for option in attrs.get("options", []):
                    if option["label"] not in CHANNELS:
                        problems.append(f"{form.name}: channel {option['label']!r} has no UTM row")
    for problem in problems:
        print(f"::error title=Form contract broken::{problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
