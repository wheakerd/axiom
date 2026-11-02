"""Canonical consequential external-action contract cases."""

from __future__ import annotations

from axiom_validation.context import REPOSITORY_ROOT, display_path
from axiom_validation.external_action import EXTERNAL_ACTION_ENVELOPE_FIELDS, external_action_gate
from .evidence import check_strict_evidence_gate


def check_external_action_scenarios(failures: list[str]) -> int:
    skill_root = REPOSITORY_ROOT / "plugin" / "skills" / "confirm-external-action"
    skill_path = skill_root / "SKILL.md"
    # The envelope fields live in the routed reference; the entry keeps the summary and gates.
    contract = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (skill_path, skill_root / "references" / "action-envelope.md")
    )
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
        "before the first attempt",
        "visible text",
        "in its own tool request",
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
