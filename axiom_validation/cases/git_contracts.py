"""Canonical traceable-Git source contracts and pure gate cases."""

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
from .evidence import check_strict_evidence_gate


# The hook policy of every traceable phase: repository hooks run by default, and the
# one sentence below is the only authorized bypass.
HOOK_BYPASS_SENTENCE = (
    "Add `--no-verify` only when the user explicitly authorized bypassing this "
    "repository's pre-push hook for this push"
)
HEAVY_PUSH_COMMAND = "git -C <repo> push --no-follow-tags <push-remote> <branch-ref>:<merge-ref>"
REFRESH_COMMAND = (
    "git -C <repo> fetch --no-tags --no-recurse-submodules --refmap= <upstream-remote> <merge-ref>"
)


def check_traceable_security_contracts(failures: list[str]) -> int:
    skill_root = REPOSITORY_ROOT / "plugin" / "skills" / "traceable-git-submit"
    required_anchors = {
        "SKILL.md": (
            "references/direct-submit.md",
            "references/git-values.md",
            "references/baseline-and-preflight.md",
            "references/checkpoint.md",
            "references/consolidation.md",
            "references/remote-targets.md",
            "references/prepared-release-submit.md",
            "references/phase-outcomes.md",
            "the verified live remote tip is an ancestor of the final commit",
            "normal repository hooks",
            "general push authority never includes it",
        ),
        "references/phase-outcomes.md": (
            "cleanupReady",
            "Cleanup requires separate exact authority",
        ),
        "references/git-values.md": (
            "one argument-vector element",
            "`--` before paths",
            "never build a command string",
            "git check-ref-format",
            "repository code the model has not reviewed",
            "do not add flags that bypass one",
            "linked worktree",
            "One writer at a time is assumed",
            "never by URL",
        ),
        "references/baseline-and-preflight.md": (
            "push authority never grants a refresh or any fetch",
        ),
        "references/remote-targets.md": (
            "a configured remote explicitly named in the current request",
            "`branch.<branch>.pushRemote`",
            "`remote.pushDefault`",
            "current `upstreamRemote`",
            "`pushRemote != upstreamRemote`",
            "git merge-base --is-ancestor <target-baseline-sha> <final-sha>",
            "A stale local tracking ref is informational",
            "liveBaselineSha",
            "Different targets may have different ancestor baselines",
            "A consolidated submission uses its recorded `baselineSha` for every target instead",
            "never force-push on this route",
            "Push authority never grants fetch",
        ),
        "references/consolidation.md": (
            "Network-push authority never authorizes a refresh",
            "Generic prune needs separate exact authority",
            "Never retry a push automatically",
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

    require_ordered_contract_anchors(
        skill_root / "references/consolidation.md",
        (
            "## Exact Remote Refresh",
            REFRESH_COMMAND,
            "git -C <repo> update-ref --no-deref <upstream-tracking-ref> <source-oid> <old-tracking-oid>",
            "`--refmap=` keeps the fetch from updating configured refs",
            "recompute `@{u}`",
            "## Backup And Final Commit",
            "the null old value makes it fail when the ref already exists",
            "Never fall back to an unconditional `update-ref`.",
            "git -C <repo> update-ref --no-deref <backup-ref> <old-head> <null-oid>",
            "git -C <repo> commit-tree <final-tree> -p <upstream-sha>",
            "## Install And Persist",
            "git -C <repo> update-ref --no-deref <branch-ref> <new-commit> <old-head>",
            "restore the branch with compare-and-swap",
            "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>",
            "## Push",
            "repository hooks running",
            HEAVY_PUSH_COMMAND,
            HOOK_BYPASS_SENTENCE,
            "Stop issuing pushes at the first failure",
            "Never retry a push automatically",
        ),
        failures,
        "exact refresh and consolidated push",
    )
    require_ordered_contract_anchors(
        skill_root / "references/git-values.md",
        (
            "## Literal Arguments",
            "git rev-parse --show-object-format",
            "40 hex characters for `sha1`, 64 for `sha256`",
            "all-zero OID is only the old-value sentinel of `update-ref`",
            "Reject NUL, CR, LF, and other control characters",
            "## Git Metadata State",
            "git -C <repo> rev-parse --path-format=absolute --git-path axiom/<file>",
            "stop when a reread shows a record you did not write",
            "## Endpoints",
        ),
        failures,
        "literal values and metadata",
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
        skill_root / "references/remote-targets.md",
        (
            "## Push Identity",
            "## Targets",
            "git -C <repo> ls-remote <push-url> <merge-ref>",
            "git merge-base --is-ancestor <target-baseline-sha> <final-sha>",
            "## Push And Read-Back",
            "any missing, changed, non-commit, or non-ancestor result means zero pushes",
            "repository hooks running",
            HEAVY_PUSH_COMMAND,
            HOOK_BYPASS_SENTENCE,
            "Stop issuing pushes at the first failure",
            "Read every target back",
            "never retry automatically",
            "Push authority never grants fetch",
            "## Recovery Of A Consolidated Record",
            "accept only `baselineSha` or `newCommit`",
            "## Cleanup",
            "git -C <repo> update-ref --no-deref -d <backup-ref> <old-head>",
            "A changed or symbolic ref stops",
            "An already absent ref is observed state, not proof that cleanup ran",
        ),
        failures,
        "direct push closure, recovery, and cleanup",
    )
    require_ordered_contract_anchors(
        skill_root / "references/prepared-release-submit.md",
        (
            "## Freeze Preparation",
            "Require an empty index or one that already matches the authorized path set exactly",
            "Require the local tag absent before the commit exists",
            "bind its branch `liveBaselineSha`",
            "## Construct Local Objects",
            "branch compare-and-swap from `oldHead` to `finalSha`",
            "reuse that verified commit as `finalSha`",
            "never add an empty commit",
            "`update-ref --no-deref <tag-ref> <tag-oid> <null-oid>`",
            "## Atomic Branch And Tag Push",
            "repository hooks running",
            "git -C <repo> push --atomic",
            "<push-remote> <branch-ref>:<merge-ref> <tag-ref>:<tag-ref>",
            HOOK_BYPASS_SENTENCE,
            "If the receiver lacks atomic support, stop; never silently split the update",
            "unknown attempts enter verification only",
        ),
        failures,
        "prepared release commit and tag submission",
    )
    require_ordered_contract_anchors(
        skill_root / "references/checkpoint.md",
        (
            "## Active Record",
            "git -C <repo> rev-parse --path-format=absolute --git-path axiom/traceable-git-submit-active-checkpoints.json",
            "## Begin And Resume",
            "Never overwrite an existing record",
            "## Freeze The Write Set",
            "Require an empty index",
            "## Stage And Prove",
            "never `git add .` or a glob",
            "require exact equality with the frozen set",
            "## Construct And Install",
            "git -C <repo> commit-tree <staged-tree-sha> -p <parent-sha>",
            "git -C <repo> update-ref --no-deref <branch-ref> <candidate-commit-sha> <parent-sha>",
            "A failed compare-and-swap is branch drift",
            "never retry or fall back to `git commit`",
            "## Failure And Recovery",
            "a marker, subject, author, time, or apparent path match never replaces that confirmation",
        ),
        failures,
        "checkpoint write set, candidate, and record",
    )
    direct_push_text = (
        skill_root / "references/remote-targets.md"
    ).read_text(encoding="utf-8")
    lightweight_push_text = (
        skill_root / "references/direct-submit.md"
    ).read_text(encoding="utf-8")
    consolidated_push_text = (
        skill_root / "references/consolidation.md"
    ).read_text(encoding="utf-8")
    prepared_push_text = (
        skill_root / "references/prepared-release-submit.md"
    ).read_text(encoding="utf-8")
    if direct_push_text.count(HEAVY_PUSH_COMMAND) != 1 or consolidated_push_text.count(HEAVY_PUSH_COMMAND) != 1:
        failures.append("direct and consolidated push owners must each contain the exact push argv once")
    for name, text in (
        ("remote-targets", direct_push_text),
        ("consolidation", consolidated_push_text),
        ("prepared-release-submit", prepared_push_text),
    ):
        if re.search(r"^git[^\n]*--no-verify", text, re.MULTILINE):
            failures.append(f"{name} must not put --no-verify in a default command")
        if text.count(HOOK_BYPASS_SENTENCE) != 1:
            failures.append(f"{name} must state the one authorized hook bypass sentence exactly once")
    require_ordered_contract_anchors(
        skill_root / "references/direct-submit.md",
        (
            "## Scope",
            "## Pre-Commit Conflict Gate",
            "## Effective Configuration Before Every Push",
            "Inspect effective configuration immediately before every direct push, including push-only requests",
            "For a combined request, also inspect it before the commit",
            "the pre-push inspection checks for drift",
            "conditional, worktree, environment, and command-scope configuration",
            "push.followTags=true",
            "push.pushOption",
            "remote.<name>.mirror=true",
            "Evaluate `push.recurseSubmodules` and `submodule.recurse` jointly in Git's configuration traversal order for the executing environment",
            "The last entry of either key decides the mode",
            "`push.recurseSubmodules` supplies its mode",
            "`submodule.recurse=true` supplies `on-demand`",
            "`submodule.recurse=false` supplies `no`",
            "Stop when the resulting mode is `on-demand` or `only`",
            "Modes `no` and `check` are safe only when they remain the final mode",
            "boolean parsing and ordered multi-value empty-reset semantics",
            "Absent settings use Git defaults",
            "Distinguish absence from an inspection or parse error",
            "malformed, unreadable, conflicting, or unclassifiable evidence stops",
            "never add flags, change configuration",
            "signing policy, endpoint privacy, and one-attempt boundary",
            "Retain only the conflicting key and effect category",
            "At both inspections, resolve the command's source-only refspec",
            "executing Git version's effective mapping rules",
            "first matching `remote.<name>.push` refspec",
            "`push.default=upstream`",
            "`branch.<name>.remote` and `branch.<name>.merge`",
            "Stop if the effective refspec is forced (leading `+`) or its destination differs from the frozen destination branch",
            "stop if the named remote argument resolves as a remote group",
            "`remotes.<name>`",
            "including a group that shadows a configured remote of the same name",
            "never invoke group members",
            "Unresolved mapping or group status is unclassifiable evidence and stops",
            "At both inspections, stop on a nonempty inherited `GIT_NAMESPACE`",
            "or when its propagation to the receiving side is unclassifiable",
            "never clear or override it",
            "Any other effective setting or inherited environment that would change the exact command's refs, destinations, remotes, force, tags, submodules, or push options is also a conflict and stops",
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
    using_axiom_path = REPOSITORY_ROOT / "plugin" / "skills" / "using-axiom" / "SKILL.md"
    require_ordered_contract_anchors(
        REPOSITORY_ROOT / "plugin" / "skills" / "confirm-external-action" / "SKILL.md",
        (
            "Keep ordinary Git host-native; select `traceable-git-submit` only under `../using-axiom/SKILL.md`",
            "Persistent install, deployment, migration, promotion, retention, service, or data risk belongs to `reversible-system-change`",
            "keep both authorization gates independent",
        ),
        failures,
        "external-action canonical Git route separation",
    )
    require_ordered_contract_anchors(
        skill_root / "references/baseline-and-preflight.md",
        (
            "Ordinary Git stays host-native",
            "Return to `../SKILL.md` for phase selection",
            "an explicitly selected simple direct push reads only `direct-submit.md`",
            "creates no Axiom metadata",
            "Reading Git facts never authorizes cache mutation",
            "only for the exact selected traceable phase",
        ),
        failures,
        "baseline canonical Git phase separation",
    )
    require_ordered_contract_anchors(
        using_axiom_path,
        (
            "A no-match result is not a denial",
            "does not create authorization",
            "does not manufacture a repository-state conflict",
            "No match continues host-native.",
            "ordinary named-remote Git remains host-native",
        ),
        failures,
        "ordinary no-route Git boundary",
    )
    require_ordered_contract_anchors(
        skill_root / "SKILL.md",
        (
            "Ordinary named-remote non-force Git",
            "stays host-native",
            "merely mentioning submit, publish, or push does not select this route",
        ),
        failures,
        "ordinary no-route Git description",
    )
    require_ordered_contract_anchors(
        skill_root / "references/direct-submit.md",
        (
            "An ordinary commit-and-push request",
            "stays in the host's normal workflow",
            "already visible material conflict",
            "An expected staged set that exactly matches the authorized payload",
            "extra or unknown staged paths stop",
            "Ask one concise question only when user input is required",
            "Do not ask again when the frozen actor",
        ),
        failures,
        "ordinary combined commit and push owner",
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
    for forbidden, reason in (
        (r"\breset --hard\b", "reset --hard"),
        (r"-c push\.", "command-scoped push.* overrides"),
        (r"\bno-follow\b(?!-tags)", "no-follow file semantics"),
        (r"\bsibling lock\b", "exclusive sibling locks"),
    ):
        # A line may name the practice only to forbid it.
        if any(
            re.search(forbidden, line) and "never" not in line.casefold()
            for line in traceable_text.splitlines()
        ):
            failures.append(f"traceable-git-submit must not prescribe {reason}")
    branch_restore = "git -C <repo> update-ref --no-deref <branch-ref> <old-head> <new-commit>"
    if consolidated_push_text.count(branch_restore) != 1:
        failures.append("consolidation must contain the exact no-deref branch restore once")

    checkpoint_execution = (
        skill_root / "references/checkpoint.md"
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
        skill_root / "references/remote-targets.md"
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
        "Resolve the effective `pushRemote` independently",
        "Freeze `pushRemote`, its resolution source, `mergeRef`, the branch, and the upstream identity",
        "Refresh still uses `upstreamRemote`",
        "`pushRemote != upstreamRemote`",
    ):
        if " ".join(anchor.split()) not in normalized_push_binding:
            failures.append(
                f"{display_path(push_binding_path)} is missing distinct push/upstream identity contract {anchor!r}"
            )
    for relative_path, anchor in (
        ("references/checkpoint.md", "`pushRemote` is set at most once"),
        ("references/consolidation.md", "bind `pushRemote` in the record once"),
        ("references/remote-targets.md", "Bind `pushRemote` now under current push authority when it is unset, and require it to match when it is set"),
    ):
        text = " ".join((skill_root / relative_path).read_text(encoding="utf-8").split())
        if anchor not in text:
            failures.append(
                f"{display_path(skill_root / relative_path)} is missing one-time push-remote binding {anchor!r}"
            )
    if "retain the backup and the record with `pushRemote` unset" not in consolidated_push_text:
        failures.append("local-only consolidation must retain the record with the push remote unset")
    if re.search(
        r"git[^\n]*(?:log|show|for-each-ref)[^\n]*%s",
        consolidated_push_text,
        re.IGNORECASE,
    ):
        failures.append("consolidation must not expose a percent-s Git metadata path")

    route_contracts = {
        "SKILL.md": (
            "references/direct-submit.md",
            "references/git-values.md",
            "references/checkpoint.md",
            "references/consolidation.md",
            "references/remote-targets.md",
        ),
        "references/consolidation.md": (
            "baseline-and-preflight.md",
            "remote-targets.md",
        ),
        "references/remote-targets.md": (
            "git-values.md",
            "direct-submit.md",
        ),
        "references/checkpoint.md": (
            "git-values.md",
            "remote-targets.md",
        ),
        "references/prepared-release-submit.md": (
            "git-values.md",
            "remote-targets.md",
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
        "effective_configuration_safe": True,
        "configuration_rechecked": True,
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
        ("configuration-conflict-stops", ("effective_configuration_safe", False), False),
        ("configuration-unknown-stops", ("effective_configuration_safe", None), False),
        ("configuration-drift-not-rechecked-stops", ("configuration_rechecked", False), False),
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

    cleanup_evidence_scenarios = check_strict_evidence_gate(
        lambda evidence: all_evidence(evidence, CLEANUP_AUTHORITY_FIELDS),
        CLEANUP_AUTHORITY_FIELDS,
        "cleanup-authority",
        failures,
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
        + cleanup_evidence_scenarios
        + 10
    )
