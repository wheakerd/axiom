"""Canonical reversible-system-change evidence and source-contract cases."""

from __future__ import annotations

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.rollback import ROLLBACK_EVIDENCE_FIELDS, rollback_gate
from .evidence import check_strict_evidence_gate


def check_reversible_safety_scenarios(failures: list[str]) -> int:
    gate_scenario_count = check_strict_evidence_gate(
        rollback_gate,
        ROLLBACK_EVIDENCE_FIELDS,
        "rollback",
        failures,
    )

    skill_root = REPOSITORY_ROOT / "skills" / "reversible-system-change"
    contract_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            skill_root / "SKILL.md",
            skill_root / "references" / "preflight-and-rollback.md",
            skill_root / "references" / "execution-and-verification.md",
            skill_root / "references" / "recovery-material-preparation.md",
        )
    )
    for evidence_label in (
        "identified",
        "present",
        "readable",
        "restore-validated",
        "rehearsed",
    ):
        if f"`{evidence_label}`" not in contract_text:
            failures.append(
                f"reversible-system-change is missing rollback evidence label {evidence_label!r}"
            )

    normalized_contract = " ".join(contract_text.split()).casefold()
    for phase_anchor in (
        "non-mutating workflow rehearsal",
        "isolated restore rehearsal",
        "rehearsal-write authority",
        "cannot affect active state or data",
        "Before candidate or active-state mutation",
        "It does not require an already validated backup.",
        "Creation fails on collision",
        "without restoring the source or relying on the not-yet-created backup",
        "Preparation-only authority ends with the observed material",
    ):
        if phase_anchor.casefold() not in normalized_contract:
            failures.append(
                f"reversible-system-change is missing rehearsal phase contract {phase_anchor!r}"
            )
    return gate_scenario_count
