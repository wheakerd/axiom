"""Consequential external-action contract fixtures."""

from __future__ import annotations

from axiom_validation.context import REPOSITORY_ROOT, display_path
from axiom_validation.external_action import EXTERNAL_ACTION_ENVELOPE_FIELDS, external_action_gate
from tests.fixtures.evidence import check_strict_evidence_gate


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

    return check_strict_evidence_gate(
        external_action_gate,
        EXTERNAL_ACTION_ENVELOPE_FIELDS,
        "external-action",
        failures,
    )
