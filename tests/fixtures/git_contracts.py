"""Traceable-Git source contracts and pure gate regression fixtures."""

from __future__ import annotations

import re

from axiom_validation.context import REPOSITORY_ROOT, display_path
from axiom_validation.git_contracts import (
    CLEANUP_AUTHORITY_FIELDS,
    all_evidence,
    direct_branch_ref_gate,
    safe_git_execution_envelope,
    safe_git_oid,
    safe_git_operand,
    safe_git_transport,
)
from axiom_validation.routing_contracts import require_ordered_contract_anchors


def check_traceable_security_contracts(failures: list[str]) -> int:
    skill_root = REPOSITORY_ROOT / "skills" / "traceable-git-submit"
    required_anchors = {
        "SKILL.md": (
            "references/safe-git-values-and-metadata.md",
            "references/commit-construction.md",
            "references/repository-and-remote-targets.md",
            "references/post-consolidation-recovery.md",
            "non-executable Git configuration and environment boundary",
            "cleanupReady",
            "Cleanup requires separate exact authority",
        ),
        "references/safe-git-values-and-metadata.md": (
            "literal argument-vector element",
            "git check-ref-format",
            "target-controlled",
            "core.fsmonitor",
            "core.sshCommand",
            "credential helpers",
            "`GIT_*`",
            "installed Git version",
            "no-follow",
            "linked worktree",
            "parent identity",
            "require strict UTF-8",
            "invalid/overlong/surrogate encodings",
            "NUL, CR, LF, ASCII C0, DEL, C1",
            "`U+2028`, `U+2029`",
            "`Cc`, `Cf`, `Zl`, and `Zp`",
        ),
        "references/baseline-and-preflight.md": (">/dev/null 2>&1",),
        "references/repository-and-remote-targets.md": (
            "non-visible literal-argument capture",
            "a configured remote explicitly named in the current request",
            "`branch.<branch>.pushRemote`",
            "`remote.pushDefault`",
            "current `upstreamRemote`",
            "`pushRemote != upstreamRemote`",
            "`fetch.bundleURI`",
            "Bypass pre-push hooks unless their exact frozen identity and action are separately authorized",
            "<helper>::<address>",
            "`protocol.allow=never`",
        ),
        "references/post-consolidation-recovery.md": (
            "cleanupReady",
            "separate authority for both deletions",
            "exact repository",
            "Push/recovery authority never implies fetch",
            "Local-only consolidation persists the initial",
            "then transition once to",
            "Never overwrite or rebind a bound record",
        ),
        "references/consolidation-and-push.md": (
            "Network-push authority never authorizes it",
            "Generic prune needs separate exact authority",
            "Delete no backup or active record without the separately authorized exact cleanup envelope",
        ),
    }
    for relative_path, anchors in required_anchors.items():
        path = skill_root / relative_path
        text = path.read_text(encoding="utf-8")
        normalized_text = " ".join(text.split()).casefold()
        for anchor in anchors:
            if " ".join(anchor.split()).casefold() not in normalized_text:
                failures.append(
                    f"{display_path(path)} is missing traceable security contract {anchor!r}"
                )

    refresh_command = (
        "git -C <repo> -c fetch.all=false -c fetch.prune=false -c fetch.pruneTags=false "
        "-c fetch.recurseSubmodules=false -c fetch.writeCommitGraph=false "
        "-c maintenance.auto=false fetch --no-all --no-tags --no-prune --no-prune-tags "
        "--no-recurse-submodules --no-write-fetch-head --no-auto-maintenance "
        "--no-write-commit-graph --refmap= <fetch-target> <source-ref>"
    )
    push_command = (
        "git -C <repo> -c push.followTags=false -c push.recurseSubmodules=no "
        "-c push.gpgSign=false -c push.pushOption= -c push.negotiate=false "
        "-c push.autoSetupRemote=false push --no-verify --no-follow-tags "
        "--recurse-submodules=no --no-signed --no-push-option --no-set-upstream "
        "--no-prune --no-force --no-force-with-lease --no-force-if-includes "
        "<push-target> <branch-ref>:<merge-ref>"
    )
    require_ordered_contract_anchors(
        skill_root / "references/consolidation-and-push.md",
        (
            "## Exact Remote Refresh",
            "Freeze and validate `objectFormat`",
            "source-only refspec is exactly validated `mergeRef`",
            refresh_command,
            "Re-query `sourceRef`, require the same `sourceOid`",
            "git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>",
            "The old value is compare-and-swap.",
            "recompute `@{u}`, divergence, cache, and provenance",
            push_command,
        ),
        failures,
        "exact refresh and consolidated push",
    )
    require_ordered_contract_anchors(
        skill_root / "references/commit-construction.md",
        (
            "do not probe for absence before create",
            "git -C <repo> update-ref --no-deref <backup-ref> <old-head> <null-oid>",
            "The null old value makes it create-only",
            "Never fall back to an unconditional `update-ref`.",
            "## Atomically Update And Verify Branch",
            "git -C <repo> update-ref --no-deref <branch-ref> <new-commit> <old-head>",
            "If verification fails before push, restore with compare-and-swap",
            "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>",
        ),
        failures,
        "create-only backup ref",
    )
    require_ordered_contract_anchors(
        skill_root / "references/safe-git-values-and-metadata.md",
        (
            "## Object Format And OIDs",
            "git rev-parse --show-object-format",
            "Accept only `sha1`/40 hex or `sha256`/64 hex",
            "same-width all-zero null OID",
            "Recheck before commit creation, network access, each ref mutation, and final proof",
        ),
        failures,
        "object-format OID",
    )
    require_ordered_contract_anchors(
        skill_root / "references/safe-git-values-and-metadata.md",
        (
            "Require direct-OID `branchRef`",
            "git symbolic-ref --quiet <branch-ref>",
            "must classify it non-symbolic",
            "git rev-parse --verify <branch-ref>",
            "must equal frozen `HEAD`",
            "Recheck before source use or mutation",
            "symbolic/uncertain state stops",
            "Branch CAS must use `update-ref --no-deref`",
        ),
        failures,
        "direct branch ref",
    )
    require_ordered_contract_anchors(
        skill_root / "references/baseline-and-preflight.md",
        (
            "## Required Git Facts",
            "git -C <repo> rev-parse --show-object-format",
            "git -C <repo> symbolic-ref --quiet HEAD",
            "git -C <repo> rev-parse --verify HEAD",
        ),
        failures,
        "object format before ref and OID reads",
    )
    require_ordered_contract_anchors(
        skill_root / "references/repository-and-remote-targets.md",
        (
            "## Direct Submit Preflight",
            push_command,
            "the exact frozen pre-push hook identity and action",
            "query every authorized target",
            "Push authority never grants fetch",
        ),
        failures,
        "direct push closure and verification",
    )
    direct_push_text = (
        skill_root / "references/repository-and-remote-targets.md"
    ).read_text(encoding="utf-8")
    consolidated_push_text = (
        skill_root / "references/consolidation-and-push.md"
    ).read_text(encoding="utf-8")
    if direct_push_text.count(push_command) != 1 or consolidated_push_text.count(push_command) != 1:
        failures.append("direct and consolidated push owners must each contain the exact closed push argv once")
    traceable_text = "\n".join(
        path.read_text(encoding="utf-8") for path in skill_root.rglob("*.md")
    )
    if re.search(r"\bfetch\s+--prune\s+<remote>", traceable_text):
        failures.append("traceable-git-submit must not restore broad fetch --prune <remote>")
    branch_restore = "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>"
    checkpoint_text = (
        skill_root / "references/checkpoint-provenance.md"
    ).read_text(encoding="utf-8")
    if checkpoint_text.count(branch_restore) != 1:
        failures.append("checkpoint persistence recovery must contain the exact no-deref branch restore once")

    checkpoint_execution = (
        skill_root / "references/checkpoint-execution.md"
    ).read_text(encoding="utf-8")
    checkpoint_commit_tree = (
        "git -C <repo> commit-tree <staged-tree-sha> -p <parent-sha>"
    )
    checkpoint_branch_cas = (
        "git -C <repo> update-ref --no-deref <branch-ref> "
        "<candidate-commit-sha> <parent-sha>"
    )
    if checkpoint_execution.count(checkpoint_commit_tree) != 1:
        failures.append(
            "checkpoint execution must construct exactly one candidate from stagedTreeSha"
        )
    if checkpoint_execution.count(checkpoint_branch_cas) != 1:
        failures.append(
            "checkpoint execution must install exactly one candidate with branch compare-and-swap"
        )
    if re.search(
        r"^git -C <repo> commit(?:\s|$)", checkpoint_execution, re.MULTILINE
    ):
        failures.append("checkpoint execution must never prescribe ordinary git commit")

    push_binding_path = (
        skill_root / "references/repository-and-remote-targets.md"
    )
    require_ordered_contract_anchors(
        push_binding_path,
        (
            "a configured remote explicitly named in the current request",
            "`branch.<branch>.pushRemote` when present",
            "`remote.pushDefault` when present",
            "current `upstreamRemote`",
        ),
        failures,
        "effective push-remote precedence",
    )
    push_binding_text = push_binding_path.read_text(encoding="utf-8")
    normalized_push_binding = " ".join(push_binding_text.split())
    for anchor in (
        "`upstreamRemote` comes only from `branch.<branch>.remote` and owns `@{u}` and refresh",
        "Resolve effective `pushRemote` independently",
        "Freeze `pushRemote`, resolution source, `mergeRef`, branch, and upstream identity separately",
        "Refresh still uses `upstreamRemote`",
        "`pushRemote != upstreamRemote`",
    ):
        if " ".join(anchor.split()) not in normalized_push_binding:
            failures.append(
                f"{display_path(push_binding_path)} is missing distinct push/upstream identity contract {anchor!r}"
            )

    provenance_binding_path = (
        skill_root / "references/post-consolidation-recovery.md"
    )
    require_ordered_contract_anchors(
        provenance_binding_path,
        (
            "Local-only consolidation persists the initial\n`pushTargetState.state == unbound`",
            "may\nthen transition once to:",
            '"pushTargetState": {\n    "state": "bound"',
            "Never overwrite or rebind a bound record",
        ),
        failures,
        "one-time push-target binding",
    )
    provenance_binding_text = provenance_binding_path.read_text(encoding="utf-8")
    if provenance_binding_text.count('"state": "bound"') != 1:
        failures.append("push-target binding must define exactly one canonical bound state")
    if (
        "`post-consolidation-recovery.md` owns the one-time\n`unbound` to `bound` transition"
        not in checkpoint_text
    ):
        failures.append(
            "checkpoint provenance must delegate the one-time unbound-to-bound transition"
        )
    if "retain `pushTargetState.state == unbound`" not in consolidated_push_text:
        failures.append("local-only consolidation must retain unbound push-target state")

    hostile_path = skill_root / "references/safe-git-values-and-metadata.md"
    require_ordered_contract_anchors(
        hostile_path,
        (
            "require strict UTF-8",
            "invalid/overlong/surrogate encodings",
            "NUL, CR, LF, ASCII C0",
            "DEL, C1, `U+2028`, `U+2029`",
            "`Cc`, `Cf`, `Zl`, and `Zp`",
        ),
        failures,
        "hostile Git metadata scalar rejection",
    )
    if re.search(
        r"git[^\n]*(?:log|show|for-each-ref)[^\n]*%s",
        consolidated_push_text,
        re.IGNORECASE,
    ):
        failures.append("consolidation must not expose a percent-s Git metadata path")

    route_contracts = {
        "SKILL.md": (
            "references/safe-git-values-and-metadata.md",
            "references/commit-construction.md",
            "references/repository-and-remote-targets.md",
            "references/post-consolidation-recovery.md",
        ),
        "references/commit-construction.md": (
            "safe-git-values-and-metadata.md",
        ),
        "references/repository-and-remote-targets.md": (
            "post-consolidation-recovery.md",
        ),
        "references/checkpoint-provenance.md": (
            "post-consolidation-recovery.md",
        ),
    }
    for relative_path, references in route_contracts.items():
        route_text = (skill_root / relative_path).read_text(encoding="utf-8")
        for reference in references:
            if reference not in route_text:
                failures.append(
                    f"{display_path(skill_root / relative_path)} does not route to {reference!r}"
                )
    if re.search(
        r"^git -C <repo> update-ref (?![^\n]*--no-deref(?:\s|$))[^\n]*<branch-ref>",
        traceable_text,
        re.MULTILINE,
    ):
        failures.append("every branch install or restore update-ref must use --no-deref")

    operand_scenarios = (
        ("normal-ref", "ref", "refs/heads/release-1", True, True),
        ("shell-syntax-stays-literal", "ref", "refs/heads/release;$(touch-pwn)", True, True),
        ("shell-syntax-string-host-stops", "ref", "refs/heads/release;$(touch-pwn)", False, False),
        ("option-shaped-ref-stops", "ref", "refs/heads/-upload", True, False),
        ("control-character-stops", "ref", "refs/heads/release\nnext", True, False),
        ("c1-control-stops", "ref", "refs/heads/release\x85next", True, False),
        ("normal-remote", "remote", "origin", True, True),
        ("option-shaped-remote-stops", "remote", "--upload-pack=evil", True, False),
    )
    for name, kind, value, literal_arguments, expected in operand_scenarios:
        if safe_git_operand(kind, value, literal_arguments) != expected:
            failures.append(f"safe Git operand scenario {name!r} returned the wrong gate result")

    oid_scenarios = (
        ("sha1-oid", "a" * 40, "sha1", False, True),
        ("sha256-oid", "b" * 64, "sha256", False, True),
        ("wrong-width-stops", "a" * 40, "sha256", False, False),
        ("unknown-format-stops", "a" * 40, "future", False, False),
        ("null-object-stops", "0" * 40, "sha1", False, False),
        ("null-update-ref-sentinel", "0" * 64, "sha256", True, True),
    )
    for name, value, object_format, allow_null, expected in oid_scenarios:
        if safe_git_oid(value, object_format, allow_null=allow_null) != expected:
            failures.append(f"safe Git OID fixture {name!r} returned the wrong gate result")

    head_oid = "c" * 40
    branch_ref_scenarios = (
        ("direct-current", "non-symbolic", head_oid, head_oid, True, True),
        ("symbolic-same-oid-stops", "symbolic", head_oid, head_oid, True, False),
        ("uncertain-same-oid-stops", "uncertain", head_oid, head_oid, True, False),
        ("direct-oid-drift-stops", "non-symbolic", "d" * 40, head_oid, True, False),
        ("missing-source-recheck-stops", "non-symbolic", head_oid, head_oid, False, False),
    )
    for name, classification, resolved_oid, frozen_head, rechecked, expected in branch_ref_scenarios:
        if direct_branch_ref_gate(classification, resolved_oid, frozen_head, rechecked) != expected:
            failures.append(f"direct branch-ref fixture {name!r} returned the wrong gate result")

    transport_scenarios = (
        ("https", "https://example.test/org/repo.git", True),
        ("ssh", "ssh://git@example.test/org/repo.git", True),
        ("scp-like", "git@example.test:org/repo.git", True),
        ("plaintext-http", "http://example.test/org/repo.git", False),
        ("local-file", "file:///tmp/repo.git", False),
        ("remote-helper", "ext::sh -c exploit", False),
    )
    for name, value, expected in transport_scenarios:
        if safe_git_transport(value) != expected:
            failures.append(f"safe Git transport scenario {name!r} returned the wrong gate result")

    execution_envelope_scenarios = (
        ("benign-config", ("core.filemode", "remote.origin.url"), (), (), True),
        ("fsmonitor-stops", ("core.fsmonitor",), (), (), False),
        (
            "neutralized-fsmonitor",
            ("core.fsmonitor",),
            (),
            ("core.fsmonitor",),
            True,
        ),
        ("ssh-command-stops", ("core.sshCommand",), (), (), False),
        ("pager-command-stops", ("core.pager",), (), (), False),
        ("credential-helper-stops", ("credential.helper",), (), (), False),
        ("filter-process-stops", ("filter.lfs.process",), (), (), False),
        ("url-rewrite-stops", ("url.ssh://example/.insteadOf",), (), (), False),
        ("git-environment-stops", (), ("GIT_SSH_COMMAND",), (), False),
        ("pager-environment-stops", (), ("GIT_PAGER",), (), False),
    )
    for (
        name,
        config_keys,
        environment_names,
        handled_keys,
        expected,
    ) in execution_envelope_scenarios:
        if safe_git_execution_envelope(config_keys, environment_names, handled_keys) != expected:
            failures.append(
                f"safe Git execution-envelope scenario {name!r} returned the wrong gate result"
            )

    complete_cleanup = {field: True for field in CLEANUP_AUTHORITY_FIELDS}
    if not all_evidence(complete_cleanup, CLEANUP_AUTHORITY_FIELDS):
        failures.append("complete exact cleanup authority must permit cleanup")
    for missing_field in CLEANUP_AUTHORITY_FIELDS:
        incomplete = dict(complete_cleanup)
        incomplete[missing_field] = False
        if all_evidence(incomplete, CLEANUP_AUTHORITY_FIELDS):
            failures.append(
                f"cleanup scenario without {missing_field!r} must retain recovery state"
            )
    return (
        len(operand_scenarios)
        + len(oid_scenarios)
        + len(branch_ref_scenarios)
        + len(transport_scenarios)
        + len(execution_envelope_scenarios)
        + len(CLEANUP_AUTHORITY_FIELDS)
        + 11
    )
