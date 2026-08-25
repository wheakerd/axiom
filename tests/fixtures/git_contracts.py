"""Traceable-Git source contracts and pure gate regression fixtures."""

from __future__ import annotations

import re

from axiom_validation.context import REPOSITORY_ROOT, display_path
from axiom_validation.git_contracts import (
    CLEANUP_AUTHORITY_FIELDS,
    all_evidence,
    direct_branch_ref_gate,
    direct_push_fast_forward_gate,
    lightweight_direct_submit_gate,
    lightweight_push_arguments,
    lightweight_push_outcome,
    ordinary_combined_commit_push_gate,
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
            "references/direct-submit.md",
            "references/safe-git-values-and-metadata.md",
            "references/commit-construction.md",
            "references/repository-and-remote-targets.md",
            "references/post-consolidation-recovery.md",
            "cleanupReady",
            "Cleanup requires separate exact authority",
            "the verified live target owns the non-force baseline",
            "normal repository hooks",
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
            "git merge-base --is-ancestor <live-baseline-sha> <final-sha>",
            "The local tracking OID remains informational",
            "liveBaselineSha",
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
            "## Hardened Direct Submit Preflight",
            "Record the tracking OID and\nlocal divergence as informational state",
            "bind\n`liveBaselineSha` only from the verified live target",
            "git merge-base --is-ancestor <live-baseline-sha> <final-sha>",
            "The local tracking OID remains informational",
            "require exactly one result equal to the bound `liveBaselineSha`",
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
    lightweight_push_text = (
        skill_root / "references/direct-submit.md"
    ).read_text(encoding="utf-8")
    consolidated_push_text = (
        skill_root / "references/consolidation-and-push.md"
    ).read_text(encoding="utf-8")
    if direct_push_text.count(push_command) != 1 or consolidated_push_text.count(push_command) != 1:
        failures.append("direct and consolidated push owners must each contain the exact closed push argv once")
    require_ordered_contract_anchors(
        skill_root / "references/direct-submit.md",
        (
            "## Scope",
            "## Pre-Commit Conflict Gate",
            "git push origin main",
            "Keep normal repository pre-push hooks active",
            "## One Native Push",
            "Push exactly once",
            "## Proportional Completion",
            "Make no query when the Git result is conclusive",
            "at most one owning-remote query",
            "## Stop Conditions",
        ),
        failures,
        "lightweight direct-submit",
    )
    using_axiom_path = REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md"
    require_ordered_contract_anchors(
        using_axiom_path,
        (
            "A no-match result is not a denial",
            "does not create authorization",
            "does not manufacture a repository-state conflict",
            "an expected staged set that exactly matches the current authorized payload",
            "continue host-native without asking again",
            "Stop before commit only on concrete current evidence",
            "mere possibility, ordinary staged state, stale tracking information, or no Axiom route does not",
        ),
        failures,
        "ordinary no-route combined commit and push",
    )
    for prohibited in (
        "--no-verify",
        "generated runner",
        "execution wrapper",
        "raw URL",
        "fingerprint",
    ):
        if prohibited.casefold() not in lightweight_push_text.casefold():
            failures.append(
                f"lightweight direct-submit must prohibit {prohibited!r}"
            )
    if re.search(r"^\s*git\s+fetch\b", lightweight_push_text, re.MULTILINE):
        failures.append("lightweight direct-submit must not prescribe fetch")
    if lightweight_push_text.count("git push origin main") != 1:
        failures.append("lightweight direct-submit must contain one canonical named push")
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
            "references/direct-submit.md",
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

    direct_push_defaults = {
        "target_count": 1,
        "configured_target": True,
        "exact_ref": True,
        "force_requested": False,
        "live_object_type": "commit",
        "live_is_ancestor": True,
        "identity_rechecked": True,
        "operation_state_clear": True,
        "target_unchanged": True,
        "live_oid_unchanged": True,
    }
    direct_push_scenarios = (
        ("stale-tracking-live-fast-forward", None, True),
        ("multiple-targets-stop", ("target_count", 2), False),
        ("force-stops", ("force_requested", True), False),
        ("nonlocal-live-object-stops", ("live_object_type", "missing"), False),
        ("divergence-stops", ("live_is_ancestor", False), False),
        ("identity-drift-stops", ("identity_rechecked", False), False),
        ("operation-state-stops", ("operation_state_clear", False), False),
        ("target-drift-stops", ("target_unchanged", False), False),
        ("live-drift-stops", ("live_oid_unchanged", False), False),
    )
    for name, change, expected in direct_push_scenarios:
        scenario = dict(direct_push_defaults)
        if change is not None:
            scenario[change[0]] = change[1]
        if (
            direct_push_fast_forward_gate(
                "b" * 40,
                "c" * 40,
                "sha1",
                **scenario,
            )
            != expected
        ):
            failures.append(f"direct push fixture {name!r} returned the wrong gate result")

    lightweight_defaults = {
        "target_count": 1,
        "configured_named_remote": True,
        "exact_branch": True,
        "force_requested": False,
        "widened_refspec": False,
        "fetch_requested": False,
        "retry_requested": False,
        "identity_rechecked": True,
        "operation_state_clear": True,
        "target_unchanged": True,
        "mechanism_conflict": False,
    }
    lightweight_scenarios = (
        ("ordinary-direct", None, True),
        ("multiple-targets-stop", ("target_count", 2), False),
        ("bool-target-count-stops", ("target_count", True), False),
        ("unknown-target-stops", ("configured_named_remote", False), False),
        ("branch-drift-stops", ("exact_branch", False), False),
        ("force-stops", ("force_requested", True), False),
        ("widening-stops", ("widened_refspec", True), False),
        ("fetch-separation", ("fetch_requested", True), False),
        ("retry-stops", ("retry_requested", True), False),
        ("identity-drift-stops", ("identity_rechecked", False), False),
        ("operation-state-stops", ("operation_state_clear", False), False),
        ("target-drift-stops", ("target_unchanged", False), False),
        ("mechanism-conflict-stops", ("mechanism_conflict", True), False),
    )
    for name, change, expected in lightweight_scenarios:
        scenario = dict(lightweight_defaults)
        if change is not None:
            scenario[change[0]] = change[1]
        if lightweight_direct_submit_gate(**scenario) != expected:
            failures.append(
                f"lightweight direct-submit fixture {name!r} returned the wrong gate result"
            )

    ordinary_combined_defaults = {
        "authorization_current": True,
        "actor_unchanged": True,
        "repository_unchanged": True,
        "branch_unchanged": True,
        "configured_named_remote": True,
        "target_unchanged": True,
        "command_unchanged": True,
        "staged_payload_matches": True,
        "extra_or_unknown_staged_paths": False,
        "operation_state_clear": True,
        "non_force_policy_unchanged": True,
        "force_requested": False,
        "widened_refspec": False,
        "target_count": 1,
        "instruction_conflict": False,
        "known_divergence": False,
    }
    ordinary_combined_scenarios = (
        ("expected-staged-payload-proceeds", None, True),
        ("authorization-drift-stops", ("authorization_current", False), False),
        ("actor-drift-stops", ("actor_unchanged", False), False),
        ("repository-drift-stops", ("repository_unchanged", False), False),
        ("branch-drift-stops", ("branch_unchanged", False), False),
        ("missing-remote-stops", ("configured_named_remote", False), False),
        ("target-drift-stops", ("target_unchanged", False), False),
        ("command-drift-stops", ("command_unchanged", False), False),
        ("payload-drift-stops", ("staged_payload_matches", False), False),
        ("extra-staged-path-stops", ("extra_or_unknown_staged_paths", True), False),
        ("operation-state-stops", ("operation_state_clear", False), False),
        ("policy-drift-stops", ("non_force_policy_unchanged", False), False),
        ("force-stops", ("force_requested", True), False),
        ("widening-stops", ("widened_refspec", True), False),
        ("multiple-targets-stop", ("target_count", 2), False),
        ("bool-target-count-stops", ("target_count", True), False),
        ("instruction-conflict-stops", ("instruction_conflict", True), False),
        ("known-divergence-stops", ("known_divergence", True), False),
    )
    for name, change, expected in ordinary_combined_scenarios:
        scenario = dict(ordinary_combined_defaults)
        if change is not None:
            scenario[change[0]] = change[1]
        if ordinary_combined_commit_push_gate(**scenario) != expected:
            failures.append(
                f"ordinary combined commit/push fixture {name!r} returned the wrong gate result"
            )

    lightweight_argument_scenarios = (
        ("exact", ("git", "push", "origin", "main"), "origin", "main", True),
        ("no-verify-stops", ("git", "push", "--no-verify", "origin", "main"), "origin", "main", False),
        ("force-stops", ("git", "push", "--force", "origin", "main"), "origin", "main", False),
        ("raw-target-stops", ("git", "push", "https://example.invalid/repo.git", "main"), "origin", "main", False),
        ("widened-refspec-stops", ("git", "push", "origin", "main:other"), "origin", "main", False),
    )
    for name, arguments, remote, branch, expected in lightweight_argument_scenarios:
        if lightweight_push_arguments(arguments, remote, branch) != expected:
            failures.append(
                f"lightweight push arguments fixture {name!r} returned the wrong result"
            )

    lightweight_outcome_scenarios = (
        ("conclusive-success", "success", 0, None, "pass"),
        ("conclusive-rejection", "rejected", 0, None, "fail"),
        ("ambiguous-confirmed", "ambiguous", 1, True, "pass"),
        ("ambiguous-not-updated", "ambiguous", 1, False, "fail"),
        ("ambiguous-unresolved", "ambiguous", 1, None, "unknown"),
        ("duplicate-query-stops", "ambiguous", 2, True, "unknown"),
        ("query-after-success-stops", "success", 1, True, "unknown"),
    )
    for name, status, query_count, match, expected in lightweight_outcome_scenarios:
        if (
            lightweight_push_outcome(
                status,
                owning_remote_query_count=query_count,
                queried_tip_matches_final=match,
            )
            != expected
        ):
            failures.append(
                f"lightweight push outcome fixture {name!r} returned the wrong result"
            )

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
        + len(direct_push_scenarios)
        + len(lightweight_scenarios)
        + len(ordinary_combined_scenarios)
        + len(lightweight_argument_scenarios)
        + len(lightweight_outcome_scenarios)
        + len(transport_scenarios)
        + len(execution_envelope_scenarios)
        + len(CLEANUP_AUTHORITY_FIELDS)
        + 11
    )
