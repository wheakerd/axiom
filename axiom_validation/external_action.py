"""Pure authorization gate for consequential external actions."""

from __future__ import annotations

from .git_contracts import all_evidence

EXTERNAL_ACTION_ENVELOPE_FIELDS = (
    "actor_bound",
    "action_bound",
    "target_bound",
    "payload_bound",
    "disclosure_bound",
    "cost_bound",
    "count_bound",
    "retry_bound",
    "current_user_authority",
    "envelope_unchanged",
    "host_approval_satisfied",
)


def external_action_gate(evidence: dict[str, bool]) -> bool:
    return all_evidence(evidence, EXTERNAL_ACTION_ENVELOPE_FIELDS)
