"""Pure safety gates for traceable Git operations."""

from __future__ import annotations

import re

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


def all_evidence(evidence: dict[str, bool], fields: tuple[str, ...]) -> bool:
    return all(evidence.get(field, False) for field in fields)
