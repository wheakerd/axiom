"""Pure safety gates for traceable Git operations."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

CLEANUP_AUTHORITY_FIELDS = (
    "exact_authority",
    "repo_match",
    "workflow_match",
    "backup_ref_match",
    "old_head_match",
    "new_commit_match",
    "targets_match",
    "operations_bound",
    "verification_current",
    "metadata_safe",
)

GIT_OID_WIDTHS = {"sha1": 40, "sha256": 64}


def safe_git_oid(value: str, object_format: str, *, allow_null: bool = False) -> bool:
    width = GIT_OID_WIDTHS.get(object_format)
    if width is None or re.fullmatch(rf"[0-9a-fA-F]{{{width}}}", value) is None:
        return False
    return allow_null or value != "0" * width


def direct_branch_ref_gate(
    symbolic_classification: str,
    resolved_oid: str,
    frozen_head: str,
    rechecked_before_use: bool,
) -> bool:
    return bool(
        symbolic_classification == "non-symbolic"
        and resolved_oid == frozen_head
        and rechecked_before_use
    )


def direct_push_fast_forward_gate(
    live_oid: str,
    final_oid: str,
    object_format: str,
    *,
    target_count: int,
    configured_target: bool,
    exact_ref: bool,
    force_requested: bool,
    live_object_type: str,
    live_is_ancestor: bool,
    identity_rechecked: bool,
    operation_state_clear: bool,
    target_unchanged: bool,
    live_oid_unchanged: bool,
) -> bool:
    """Accept one verified live non-force update without trusting tracking state."""
    return bool(
        type(target_count) is int
        and target_count == 1
        and configured_target is True
        and exact_ref is True
        and force_requested is False
        and safe_git_oid(live_oid, object_format)
        and safe_git_oid(final_oid, object_format)
        and live_object_type == "commit"
        and live_is_ancestor is True
        and identity_rechecked is True
        and operation_state_clear is True
        and target_unchanged is True
        and live_oid_unchanged is True
    )


def ordered_push_baselines_gate(
    frozen_targets: Sequence[Mapping[str, Any]],
    observed_targets: Sequence[Mapping[str, Any]],
    final_oid: str,
    object_format: str,
    *,
    authorization_current: bool,
    operation_state_clear: bool,
) -> bool:
    """Check all ordered targets before any push, using each target's baseline."""
    if (
        authorization_current is not True
        or operation_state_clear is not True
        or not frozen_targets
        or len(frozen_targets) != len(observed_targets)
    ):
        return False
    fingerprints: set[str] = set()
    for ordinal, (frozen, observed) in enumerate(zip(frozen_targets, observed_targets), 1):
        if not isinstance(frozen, Mapping) or not isinstance(observed, Mapping):
            return False
        fingerprint = frozen.get("fingerprint")
        baseline = frozen.get("liveBaselineSha")
        ref = frozen.get("mergeRef")
        if (
            type(fingerprint) is not str or not fingerprint or fingerprint in fingerprints
            or type(baseline) is not str or type(ref) is not str
            or not ref.startswith("refs/heads/") or not safe_git_operand("ref", ref, True)
            or type(frozen.get("ordinal")) is not int or frozen["ordinal"] != ordinal
            or type(observed.get("ordinal")) is not int or observed["ordinal"] != ordinal
            or observed.get("fingerprint") != fingerprint
            or observed.get("mergeRef") != ref
        ):
            return False
        fingerprints.add(fingerprint)
        if not direct_push_fast_forward_gate(
            baseline, final_oid, object_format,
            target_count=1,
            configured_target=True,
            exact_ref=True,
            force_requested=False,
            live_object_type=observed.get("objectType"),
            live_is_ancestor=observed.get("isAncestor"),
            identity_rechecked=True,
            operation_state_clear=operation_state_clear,
            target_unchanged=True,
            live_oid_unchanged=observed.get("oid") == baseline,
        ):
            return False
    return True


def backup_ref_gate(
    backup_ref: str,
    old_head: str,
    object_format: str,
    observed_kind: str,
    observed_oid: str | None,
) -> bool:
    """Validate the recovery ref's name separately from its resolved commit OID."""
    return bool(
        type(backup_ref) is str
        and backup_ref.startswith("refs/axiom/backups/")
        and safe_git_operand("ref", backup_ref, True)
        and type(old_head) is str
        and safe_git_oid(old_head, object_format)
        and observed_kind == "non-symbolic"
        and observed_oid == old_head
    )


def backup_cleanup_transition(
    cleanup_ready: Mapping[str, Any],
    authority: Mapping[str, Any],
    *,
    backup_ref: str,
    old_head: str,
    object_format: str,
    observed_kind: str,
    observed_oid: str | None,
) -> str:
    """Resume only a proved exact cleanup state; ref absence is not intent."""
    if not all_evidence(authority, CLEANUP_AUTHORITY_FIELDS):
        return "blocked"
    if not backup_ref_gate(backup_ref, old_head, object_format, "non-symbolic", old_head):
        return "blocked"
    deleted = cleanup_ready.get("backupRefDeleted")
    if type(deleted) is not bool:
        return "blocked"
    absent = observed_kind == "absent" and observed_oid is None
    present = backup_ref_gate(backup_ref, old_head, object_format, observed_kind, observed_oid)
    intent = cleanup_ready.get("backupDeletion")
    if intent is None:
        if deleted and absent:
            return "delete-record"
        return "persist-intent" if not deleted and present else "blocked"
    if (
        not isinstance(intent, Mapping)
        or set(intent) != {"state", "backupRef", "expectedOid"}
        or intent.get("backupRef") != backup_ref
        or intent.get("expectedOid") != old_head
    ):
        return "blocked"
    if intent.get("state") == "pending" and not deleted:
        if present:
            return "delete-backup"
        return "record-complete" if absent else "blocked"
    if intent.get("state") == "complete" and deleted and absent:
        return "delete-record"
    return "blocked"


def lightweight_direct_submit_gate(
    *,
    target_count: int,
    configured_named_remote: bool,
    exact_branch: bool,
    force_requested: bool,
    widened_refspec: bool,
    fetch_requested: bool,
    retry_requested: bool,
    identity_rechecked: bool,
    operation_state_clear: bool,
    target_unchanged: bool,
    mechanism_conflict: bool,
) -> bool:
    """Accept only one unchanged named-remote, one-branch, non-force push."""
    return bool(
        type(target_count) is int
        and target_count == 1
        and configured_named_remote is True
        and exact_branch is True
        and force_requested is False
        and widened_refspec is False
        and fetch_requested is False
        and retry_requested is False
        and identity_rechecked is True
        and operation_state_clear is True
        and target_unchanged is True
        and mechanism_conflict is False
    )


def ordinary_combined_commit_push_gate(
    *,
    authorization_current: bool,
    actor_unchanged: bool,
    repository_unchanged: bool,
    branch_unchanged: bool,
    configured_named_remote: bool,
    target_unchanged: bool,
    command_unchanged: bool,
    staged_payload_matches: bool,
    extra_or_unknown_staged_paths: bool,
    operation_state_clear: bool,
    non_force_policy_unchanged: bool,
    force_requested: bool,
    widened_refspec: bool,
    target_count: int,
    instruction_conflict: bool,
    known_divergence: bool,
) -> bool:
    """Allow an ordinary combined commit/push only on concrete current facts.

    Route selection is deliberately absent: an Axiom no-match neither grants nor
    denies this host-native action and cannot manufacture a repository conflict.
    """
    return bool(
        authorization_current is True
        and actor_unchanged is True
        and repository_unchanged is True
        and branch_unchanged is True
        and configured_named_remote is True
        and target_unchanged is True
        and command_unchanged is True
        and staged_payload_matches is True
        and extra_or_unknown_staged_paths is False
        and operation_state_clear is True
        and non_force_policy_unchanged is True
        and force_requested is False
        and widened_refspec is False
        and type(target_count) is int
        and target_count == 1
        and instruction_conflict is False
        and known_divergence is False
    )


def lightweight_push_arguments(
    arguments: tuple[str, ...],
    named_remote: str,
    branch: str,
) -> bool:
    """Require the user's ordinary four-argument named-remote push form."""
    return bool(
        safe_git_operand("remote", named_remote, True)
        and branch
        and safe_git_operand("ref", f"refs/heads/{branch}", True)
        and arguments == ("git", "push", named_remote, branch)
    )


def lightweight_push_outcome(
    push_status: str,
    *,
    owning_remote_query_count: int,
    queried_tip_matches_final: bool | None,
) -> str:
    """Classify completion from Git first and one query only if ambiguous."""
    if type(owning_remote_query_count) is not int:
        return "unknown"
    if push_status == "success":
        return (
            "pass"
            if owning_remote_query_count == 0 and queried_tip_matches_final is None
            else "unknown"
        )
    if push_status == "rejected":
        return (
            "fail"
            if owning_remote_query_count == 0 and queried_tip_matches_final is None
            else "unknown"
        )
    if push_status != "ambiguous" or owning_remote_query_count != 1:
        return "unknown"
    if queried_tip_matches_final is True:
        return "pass"
    if queried_tip_matches_final is False:
        return "fail"
    return "unknown"


def safe_git_operand(
    kind: str,
    value: str,
    literal_arguments: bool,
) -> bool:
    if not literal_arguments or not value:
        return False
    if any(
        ord(character) < 32 or 0x7F <= ord(character) <= 0x9F
        for character in value
    ):
        return False
    if "\u2028" in value or "\u2029" in value:
        return False
    if kind == "remote":
        return not value.startswith("-")
    if kind == "path":
        return True
    if kind != "ref" or not value.startswith("refs/"):
        return False
    components = value.split("/")
    if any(not component or component.startswith("-") for component in components):
        return False
    if value.endswith(("/", ".")) or ".." in value or "@{" in value:
        return False
    return not any(character in value for character in " ~^:?*[\\")


def safe_git_transport(value: str) -> bool:
    if not safe_git_operand("path", value, True) or "::" in value:
        return False
    if re.match(r"^(?:https|ssh|git\+ssh)://", value, re.IGNORECASE):
        return True
    if "://" in value:
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    return re.match(r"^(?:[^/@:\s]+@)?[^/:\s]+:.+$", value) is not None


COMMAND_CAPABLE_GIT_CONFIG = (
    re.compile(
        r"^core\.(?:fsmonitor|sshcommand|hookspath|askpass|gitproxy|pager|editor|alternaterefscommand)$"
    ),
    re.compile(r"^(?:sequence\.editor|pager\..+|gc\.recentobjectshook)$"),
    re.compile(r"^(?:commit|tag)\.gpgsign$"),
    re.compile(r"^credential(?:\..+)?\.helper$"),
    re.compile(r"^diff\.(?:external|.+\.(?:command|textconv))$"),
    re.compile(r"^filter\..+\.(?:clean|smudge|process)$"),
    re.compile(r"^remote\..+\.(?:proxy|uploadpack|receivepack)$"),
    re.compile(r"^url\..+\.(?:insteadof|pushinsteadof)$"),
    re.compile(r"^(?:gpg|gpg\..+)\.program$"),
    re.compile(r"^include(?:if\..+)?\.path$"),
)


def safe_git_execution_envelope(
    local_config_keys: tuple[str, ...],
    ambient_environment_names: tuple[str, ...],
    handled_config_keys: tuple[str, ...] = (),
) -> bool:
    handled = {key.casefold() for key in handled_config_keys}
    for raw_key in local_config_keys:
        key = raw_key.casefold()
        if any(pattern.fullmatch(key) for pattern in COMMAND_CAPABLE_GIT_CONFIG):
            if key not in handled:
                return False

    for raw_name in ambient_environment_names:
        name = raw_name.upper()
        if name.startswith("GIT_") or name in {
            "PAGER",
            "EDITOR",
            "VISUAL",
            "SSH_ASKPASS",
        }:
            return False
    return True


def all_evidence(evidence: Mapping[str, Any], fields: Sequence[str]) -> bool:
    return all(evidence.get(field) is True for field in fields)
