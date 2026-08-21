"""Consequential external-action contract fixtures."""

from __future__ import annotations

from axiom_validation.context import REPOSITORY_ROOT, display_path
from axiom_validation.external_action import EXTERNAL_ACTION_ENVELOPE_FIELDS, external_action_gate


def check_external_action_scenarios(failures: list[str]) -> int:
    skill_path = REPOSITORY_ROOT / "skills" / "confirm-external-action" / "SKILL.md"
    contract = skill_path.read_text(encoding="utf-8")
    for anchor in (
        "acting account",
        "exact target",
        "normalized payload",
        "sensitive value",
        "cost",
        "idempotency key",
        "current user statement",
        "Do not automatically retry",
        "external system of record",
        "untrusted",
    ):
        if anchor.casefold() not in contract.casefold():
            failures.append(
                f"{display_path(skill_path)} is missing external-action contract {anchor!r}"
            )

    complete = {field: True for field in EXTERNAL_ACTION_ENVELOPE_FIELDS}
    if not external_action_gate(complete):
        failures.append("complete external action envelope must permit one execution")
    for missing_field in EXTERNAL_ACTION_ENVELOPE_FIELDS:
        incomplete = dict(complete)
        incomplete[missing_field] = False
        if external_action_gate(incomplete):
            failures.append(
                f"external-action scenario without {missing_field!r} must stop before mutation"
            )
    return len(EXTERNAL_ACTION_ENVELOPE_FIELDS) + 1
