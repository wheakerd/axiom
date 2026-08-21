"""Pure evidence gate for reversible system changes."""

from __future__ import annotations

ROLLBACK_EVIDENCE_FIELDS = (
    "prior_state_bound",
    "location_unambiguous",
    "restore_principal_readable",
    "restore_prerequisites_present",
    "complete_effect_coverage",
    "current_restore_validation",
    "rollback_authorized",
    "post_restore_checks_defined",
    "evidence_fresh",
)


def rollback_gate(evidence: dict[str, bool]) -> bool:
    return all(evidence.get(field, False) for field in ROLLBACK_EVIDENCE_FIELDS)
