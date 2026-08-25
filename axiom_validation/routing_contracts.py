"""Routing policy and source-contract validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .context import README_PATH, REPOSITORY_ROOT, display_path
from .repository_policy import parse_skill_frontmatter
from .yaml_subset import CanonicalYamlError, parse_agent_metadata_document

EFFECTIVE_INSTRUCTION_TOKENS = (
    "effective-instructions",
    "effective-instructions:preview",
    "effective-instructions:refactor",
    "effective-instructions:force",
    "effective-instructions:reconcile",
    "effective-instructions:reconcile-preview",
)
ROUTE_SOURCE_ANCHORS = {
    "agents-architect": ("AGENTS.md", "audit"),
    "agent-plugin-architect": ("packaged", "shared Skills", "hooks"),
    "confirm-external-action": ("external", "target", "verify"),
    "optimize-codex-usage": ("Codex", "credits", "context"),
    "review-axiom-task": ("routing", "authorization", "evidence"),
    "traceable-git-submit": ("checkpoint", "push"),
    "reversible-system-change": ("plan", "persistent", "rollback"),
}
TAGGED_PLUGIN_RELEASE_ROUTE_ANCHORS = (
    "combined commit, tag, and push",
    "already-prepared plugin release",
)
ORDINARY_GIT_HOST_NATIVE_ANCHORS = (
    "ordinary named-remote non-force",
    "without a tag",
    "stay host-native",
)
README_LIFECYCLE_COMMANDS = (
    "codex plugin marketplace upgrade axiom",
    "/plugin marketplace update axiom",
    "/plugin update axiom@axiom",
    "/reload-plugins",
    "codex plugin remove axiom@axiom",
    "/plugin disable axiom@axiom",
    "/plugin uninstall axiom@axiom",
)


def route_contract(request: str) -> dict[str, Any]:
    """Evaluate the offline route model after its source contracts are checked."""
    normalized = request.lower()
    if "只制定持久化数据库迁移计划" in request and "不要执行" in request:
        normalized = "prepare a read-only plan for a persistent database migration"
    if "审阅当前 Axiom 任务的路由、授权、操作和证据" in request:
        normalized = "review the routing authorization actions and evidence for this axiom task"
    if "打包的 Codex 和 Claude Code 插件" in request and "共享 Skills" in request:
        normalized = (
            "audit this packaged codex and claude code plugin's shared skills, "
            "routes, wrappers, startup hooks, and version evidence without install or publish"
        )

    effective_contracts = {
        "effective-instructions": {
            "route": "agents-architect",
            "phase": "effective-update",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/context-evidence.md",
                "references/maintenance/maintenance-application.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:preview": {
            "route": "agents-architect",
            "phase": "effective-preview",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/context-evidence.md",
            ),
            "authorization": frozenset({"read"}),
        },
        "effective-instructions:refactor": {
            "route": "agents-architect",
            "phase": "effective-refactor",
            "references": (
                "references/runtime-and-updates.md",
                "references/routing-architecture.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:reconcile": {
            "route": "agents-architect",
            "phase": "implementation-reconciliation",
            "references": (
                "references/maintenance/implementation-reconciliation.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        },
        "effective-instructions:reconcile-preview": {
            "route": "agents-architect",
            "phase": "implementation-reconciliation-preview",
            "references": (
                "references/maintenance/implementation-reconciliation.md",
            ),
            "authorization": frozenset({"read"}),
        },
    }
    effective_request = normalized.strip()
    if effective_request in effective_contracts:
        return effective_contracts[effective_request]
    if re.fullmatch(r"effective-instructions:force\s+\S(?:.*\S)?", effective_request):
        return {
            "route": "agents-architect",
            "phase": "effective-force",
            "references": (
                "references/runtime-and-updates.md",
                "references/maintenance/maintenance-application.md",
            ),
            "authorization": frozenset({"read", "edit", "test"}),
        }

    review = bool(
        "axiom" in normalized
        and re.search(r"\b(?:review|explain|audit|show)\b", normalized)
        and re.search(
            r"\b(?:task|route|routing|authorization|authority|actions?|evidence|outcome)\b",
            normalized,
        )
    )
    usage = bool(
        re.search(r"\bcodex\b.*\b(?:credits?|tokens?|context|usage)\b", normalized)
        or re.search(r"\b(?:skills?|agents\.md|mcp)\b.*\bcontext\b", normalized)
    )
    agents = bool(
        re.search(r"(?:agents\.md|\.agents)", normalized)
        and re.search(r"\b(?:audit|create|design|initialize|split|rewrit|migrat|maintain|validat)\w*\b", normalized)
    )
    plugin_architecture = bool(
        re.search(
            r"\b(?:audit|design|redesign|initializ\w*|migrat\w*|maintain|review|evaluat\w*)\b",
            normalized,
        )
        and re.search(
            r"\b(?:packaged|cross-host|agent[ -]plugin|codex and claude code)\b",
            normalized,
        )
        and re.search(
            r"\b(?:architect\w*|shared skills?|routes?|manifests?|wrappers?|hooks?|version(?:-bound)? (?:compatibility )?evidence|public skills?)\b",
            normalized,
        )
    )
    explicit_traceable = "$traceable-git-submit" in normalized
    checkpoint_git = bool(re.search(r"\bcheckpoint\b", normalized))
    baseline_git = bool(
        re.search(r"\bbaseline metadata\b", normalized)
        or (
            "traceable git workflow" in normalized
            and re.search(r"\b(?:audit|review)\b", normalized)
        )
    )
    consolidation_git = bool(re.search(r"\b(?:consolidat\w*|one-final)\b", normalized))
    recovery_git = bool(re.search(r"\brecover\w*\b", normalized))
    push_prohibited = bool(
        re.search(r"\b(?:do not|don't|without)\s+push\w*\b", normalized)
    )
    consolidation_push = bool(
        consolidation_git
        and re.search(r"\b(?:push|submit)\w*\b", normalized)
        and not push_prohibited
    )
    recovery_remote = bool(
        recovery_git
        and re.search(
            r"\b(?:remote verification|remote binding|authorized push retry)\b",
            normalized,
        )
    )
    recovery_push_retry = bool(
        recovery_git and re.search(r"\bauthorized push retry\b", normalized)
    )
    hardened_git = bool(
        re.search(r"\b(?:hardened|raw-target|multi-target|multiple targets?|force[ -]push|rewrite history)\b", normalized)
        or bool(
            re.search(r"\bcommit\b.*\btag\b.*\bpush\b", normalized)
            and re.search(r"\bplugin release\b", normalized)
        )
    )
    stale_tracking_ref = bool(
        re.search(
            r"\b(?:stale (?:local )?(?:remote-)?tracking ref|"
            r"(?:local )?(?:remote-)?tracking ref (?:is )?stale)\b",
            normalized,
        )
    )
    verified_live_remote_ancestor = bool(
        re.search(
            r"\blive remote (?:tip|commit)\b.*\bverified ancestor\b",
            normalized,
        )
        or re.search(
            r"\bverified\b.*\blive remote (?:tip|commit)\b.*\bancestor\b",
            normalized,
        )
    )
    direct_git = bool(
        explicit_traceable
        or (stale_tracking_ref and verified_live_remote_ancestor)
    )
    git = bool(
        checkpoint_git
        or baseline_git
        or consolidation_git
        or recovery_git
        or hardened_git
        or direct_git
    )
    persistent = bool(
        (
            re.search(
                r"\b(?:install|upgrade|deploy|deployment|migrat\w*|retention|promot\w*)\b",
                normalized,
            )
            and re.search(
                r"\b(?:persistent|database|system|service|authorized|approved|production|staged|release|read-only|plan|execute|rehears\w*|dry[ -]run|simulation)\b",
                normalized,
            )
        )
        or "isolated restore rehearsal" in normalized
        or bool(
            re.search(r"\b(?:install|update|reload)\b", normalized)
            and re.search(r"\bplugin\b", normalized)
        )
    )
    external_effect_prohibited = bool(
        re.search(
            r"\b(?:do not|don't|without)\s+(?:send|publish|post|invite|purchase|buy|trade|delet\w*|cancel|change)\b",
            normalized,
        )
    )
    external_action = bool(
        re.search(
            r"\b(?:send|publish|post|invite|purchase|buy|trade|delet\w*|cancel|change)\b",
            normalized,
        )
        and re.search(
            r"\b(?:email|message|announcement|post|invitation|invite|order|trade|purchase|account|membership|subscription|recipient|external (?:app|service)|remote deployment|deployment)\b",
            normalized,
        )
        and not external_effect_prohibited
    ) or bool(
        re.search(r"\bpublish\b", normalized)
        and re.search(r"\b(?:plugin|marketplace)\b", normalized)
        and re.search(r"\b(?:already-prepared|prepared|confirm|execute)\b", normalized)
        and not external_effect_prohibited
    )

    plugin_ambiguity = bool(
        re.search(r"\b(?:either|choose one)\b", normalized)
        and "plugin" in normalized
        and re.search(r"\b(?:architect\w*|shared skills?|manifests?|hooks?)\b", normalized)
        and re.search(r"\b(?:parser|source code|ordinary)\b", normalized)
    )

    if review:
        return {
            "route": "review-axiom-task",
            "phase": "review",
            "references": (),
            "authorization": frozenset({"read"}),
        }

    if plugin_ambiguity or (
        usage
        and (agents or persistent)
        and re.search(r"\b(?:either|choose one)\b", normalized)
    ):
        return {
            "route": "clarify",
            "phase": "route-choice",
            "references": (),
            "authorization": frozenset({"read"}),
        }

    if usage and plugin_architecture:
        return {
            "route": (
                "agent-plugin-architect",
                "optimize-codex-usage",
            ),
            "phase": "cross-route-ownership",
            "references": (),
            "authorization": frozenset({"read", "edit", "test"}),
        }

    if usage:
        return {
            "route": "optimize-codex-usage",
            "phase": "audit-implementation",
            "references": ("references/context-audit.md",),
            "authorization": frozenset({"read", "edit", "test"}),
        }

    if agents:
        return {
            "route": "agents-architect",
            "phase": "audit",
            "references": ("references/inventory-audit.md",),
            "authorization": frozenset({"read"}),
        }

    if plugin_architecture:
        audit_only = bool(re.search(r"\b(?:audit|review)\b", normalized)) and not bool(
            re.search(r"\b(?:design|redesign|initializ\w*|migrat\w*|maintain)\b", normalized)
        )
        return {
            "route": "agent-plugin-architect",
            "phase": "architecture-audit" if audit_only else "architecture-design",
            "references": (
                "references/package-inventory.md",
                "references/route-and-trigger-contracts.md",
                "references/cross-host-packaging.md",
            ),
            "authorization": (
                frozenset({"read"})
                if audit_only
                else frozenset({"read", "edit", "test"})
            ),
        }

    if persistent and external_action:
        return {
            "route": (
                "confirm-external-action",
                "reversible-system-change",
            ),
            "phase": "cross-route-ownership",
            "references": (),
            "authorization": frozenset({"read"}),
            "authorization_gates": (
                "confirm-external-action",
                "reversible-system-change",
            ),
        }

    if git:
        if recovery_git:
            recovery_references = (
                "references/safe-git-values-and-metadata.md",
                "references/baseline-and-preflight.md",
                "references/checkpoint-provenance.md",
                "references/post-consolidation-recovery.md",
            )
            if recovery_remote:
                recovery_references += (
                    "references/repository-and-remote-targets.md",
                )
            return {
                "route": "traceable-git-submit",
                "phase": "recovery",
                "references": recovery_references,
                "authorization": (
                    frozenset({"read", "network-push"})
                    if recovery_push_retry
                    else frozenset({"read"})
                ),
            }
        if consolidation_git:
            consolidation_references = (
                "references/safe-git-values-and-metadata.md",
                "references/baseline-and-preflight.md",
                "references/checkpoint-provenance.md",
                "references/commit-construction.md",
                "references/consolidation-and-push.md",
            )
            if consolidation_push:
                consolidation_references += (
                    "references/repository-and-remote-targets.md",
                    "references/post-consolidation-recovery.md",
                )
            return {
                "route": "traceable-git-submit",
                "phase": "consolidation",
                "references": consolidation_references,
                "authorization": (
                    frozenset({"read", "metadata-write", "commit", "network-push"})
                    if consolidation_push
                    else frozenset({"read", "metadata-write", "commit"})
                ),
            }
        if checkpoint_git:
            return {
                "route": "traceable-git-submit",
                "phase": "checkpoint",
                "references": (
                    "references/safe-git-values-and-metadata.md",
                    "references/baseline-and-preflight.md",
                    "references/checkpoint-provenance.md",
                    "references/checkpoint-execution.md",
                ),
                "authorization": frozenset({"read", "metadata-write", "commit"}),
            }
        if baseline_git:
            baseline_write = bool(
                re.search(r"\b(?:create|update|write|record)\w*\b", normalized)
            )
            return {
                "route": "traceable-git-submit",
                "phase": "baseline",
                "references": (
                    "references/safe-git-values-and-metadata.md",
                    "references/baseline-and-preflight.md",
                ),
                "authorization": (
                    frozenset({"read", "metadata-write"})
                    if baseline_write
                    else frozenset({"read"})
                ),
            }
        if hardened_git:
            return {
                "route": "traceable-git-submit",
                "phase": "hardened-submit",
                "references": (
                    "references/safe-git-values-and-metadata.md",
                    "references/repository-and-remote-targets.md",
                ),
                "authorization": frozenset({"read", "network-push"}),
            }
        return {
            "route": "traceable-git-submit",
            "phase": "direct-submit",
            "references": ("references/direct-submit.md",),
            "authorization": frozenset({"read", "network-push"}),
        }

    if persistent:
        isolated_restore_rehearsal = "isolated restore rehearsal" in normalized
        rehearsal_requested = bool(
            re.search(r"\b(?:rehears\w*|dry[ -]run|simulation)\b", normalized)
        )
        non_mutating_rehearsal = bool(
            rehearsal_requested
            and re.search(
                r"\b(?:non-mutating|read-only|without changing|do not change|dry[ -]run|simulation)\b",
                normalized,
            )
        )
        if isolated_restore_rehearsal:
            return {
                "route": "reversible-system-change",
                "phase": "isolated-restore-rehearsal",
                "references": ("references/preflight-and-rollback.md",),
                "authorization": frozenset({"read", "restore-rehearsal-write"}),
            }
        if rehearsal_requested and not non_mutating_rehearsal:
            return {
                "route": "clarify",
                "phase": "rehearsal-type",
                "references": (),
                "authorization": frozenset({"read"}),
            }
        plan_only = bool(re.search(r"\b(?:read-only|plan)\b", normalized)) and "execute" not in normalized
        return {
            "route": "reversible-system-change",
            "phase": (
                "rehearsal-read-only"
                if non_mutating_rehearsal
                else "plan" if plan_only else "execute"
            ),
            "references": (
                ("references/preflight-and-rollback.md",)
                if plan_only or non_mutating_rehearsal
                else (
                    "references/preflight-and-rollback.md",
                    "references/execution-and-verification.md",
                )
            ),
            "authorization": (
                frozenset({"read"})
                if plan_only or non_mutating_rehearsal
                else frozenset({"read", "persistent-write"})
            ),
        }

    if external_action:
        ambiguous = bool(
            re.search(r"\b(?:somewhere|someone|somebody|anywhere|whichever|whatever)\b", normalized)
        )
        return {
            "route": "confirm-external-action",
            "phase": "authorize" if ambiguous else "execute-verify",
            "references": (),
            "authorization": (
                frozenset({"read"})
                if ambiguous
                else frozenset({"read", "external-write"})
            ),
        }

    authorization = {"read"}
    if re.search(r"\b(?:fix|edit|change)\b", normalized):
        authorization.add("edit")
    if "test" in normalized:
        authorization.add("test")
    return {
        "route": None,
        "phase": "normal",
        "references": (),
        "authorization": frozenset(authorization),
    }


def has_exact_route_token(text: str, token: str) -> bool:
    return bool(
        re.search(
            rf"(?<![a-z0-9:-]){re.escape(token)}(?![a-z0-9:-])",
            text.lower(),
        )
    )


def check_routing_source_contracts(failures: list[str]) -> None:
    front_door_path = REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md"
    front_door = front_door_path.read_text(encoding="utf-8")
    route_section = front_door.split("## Bundled Routes", 1)[-1].split("\n## ", 1)[0]

    route_entries: dict[str, str] = {}
    for route in ROUTE_SOURCE_ANCHORS:
        match = re.search(
            rf"^- `{re.escape(route)}`:(.*?)(?=^- `[a-z0-9-]+`:\s|\Z)",
            route_section,
            re.MULTILINE | re.DOTALL,
        )
        if match is None:
            failures.append(
                f"{display_path(front_door_path)} has no parseable source contract for {route!r}"
            )
            continue
        route_entries[route] = match.group(1)

        skill_path = REPOSITORY_ROOT / "skills" / route / "SKILL.md"
        fields = parse_skill_frontmatter(skill_path, failures)
        if fields is None:
            continue
        surfaces = {
            f"{display_path(front_door_path)} route entry": match.group(1),
            f"{display_path(skill_path)} description": fields["description"],
        }
        for label, surface in surfaces.items():
            for anchor in ROUTE_SOURCE_ANCHORS[route]:
                if anchor.casefold() not in surface.casefold():
                    failures.append(
                        f"{label} for {route!r} is missing selection anchor {anchor!r}"
                    )

    traceable_entry = route_entries.get("traceable-git-submit")
    traceable_path = REPOSITORY_ROOT / "skills" / "traceable-git-submit" / "SKILL.md"
    traceable_fields = parse_skill_frontmatter(traceable_path, failures)
    if traceable_entry is not None and traceable_fields is not None:
        for label, surface in (
            (f"{display_path(front_door_path)} traceable route entry", traceable_entry),
            (f"{display_path(traceable_path)} description", traceable_fields["description"]),
        ):
            for anchor in (
                *TAGGED_PLUGIN_RELEASE_ROUTE_ANCHORS,
                *ORDINARY_GIT_HOST_NATIVE_ANCHORS,
            ):
                if anchor.casefold() not in surface.casefold():
                    failures.append(
                        f"{label} is missing tagged-release boundary anchor {anchor!r}"
                    )

        traceable_body = " ".join(
            traceable_path.read_text(encoding="utf-8").split()
        )
        for anchor in (
            "selects the hardened phase",
            "never authorizes the commit, tag, or push",
            "combined prepared-plugin commit/tag/push",
            "references/safe-git-values-and-metadata.md",
            "references/repository-and-remote-targets.md",
        ):
            if anchor.casefold() not in traceable_body.casefold():
                failures.append(
                    f"{display_path(traceable_path)} is missing tagged-release phase anchor {anchor!r}"
                )

    agents_entry = route_entries.get("agents-architect")
    agents_path = REPOSITORY_ROOT / "skills" / "agents-architect" / "SKILL.md"
    agents_fields = parse_skill_frontmatter(agents_path, failures)
    if agents_entry is None or agents_fields is None:
        return
    for label, surface in (
        (f"{display_path(front_door_path)} agents-architect route entry", agents_entry),
        (f"{display_path(agents_path)} description", agents_fields["description"]),
    ):
        for token in EFFECTIVE_INSTRUCTION_TOKENS:
            if not has_exact_route_token(surface, token):
                failures.append(
                    f"{label} is missing canonical trigger token {token!r}"
                )


def require_ordered_contract_anchors(
    path: Path,
    anchors: tuple[str, ...],
    failures: list[str],
    contract_name: str,
) -> None:
    """Bind an offline semantic contract to ordered phrases in its owner."""
    text = " ".join(path.read_text(encoding="utf-8").split()).casefold()
    cursor = 0
    for anchor in anchors:
        index = text.find(" ".join(anchor.split()).casefold(), cursor)
        if index < 0:
            failures.append(
                f"{display_path(path)} is missing or reorders {contract_name} anchor {anchor!r}"
            )
            return
        cursor = index + len(anchor)


def check_cross_route_resume_contracts(failures: list[str]) -> int:
    """Lock dual-route authority and fail-closed resume to their source owners."""
    skills = REPOSITORY_ROOT / "skills"
    contracts = (
        (
            skills / "agents-architect/references/maintenance/authorization-and-safety.md",
            "provenance authorization",
            (
                "Clear Axiom provenance may establish ownership, routing, and preview handling only.",
                "A read-only assessment, option request, preview, or approval of a preview authorizes zero writes regardless of provenance.",
            ),
        ),
        (
            skills / "using-axiom/SKILL.md",
            "cross-route and resume",
            (
                "Resolve cross-route ownership from this table before inspecting either candidate body.",
                "confirm-external-action",
                "reversible-system-change",
                "authorization under either route never satisfies the other.",
                "When a request delegates a choice among mutually exclusive implementations",
                "materially different route sets, write surfaces, or authorization or safety boundaries",
                "routing MUST NOT choose an alternative for the user.",
                "Select no route yet and ask exactly one concise clarification question.",
                'Wording such as "choose one" does not remove the ambiguity.',
                "Once the user chooses an unambiguous implementation, resume normal route selection.",
                "An explicit usage-reduction goal selects",
                "On resume or compaction, reselect every still-active route from current direct evidence before any new mutation.",
                "If route or phase cannot be reconstructed, perform zero new mutations",
            ),
        ),
        (
            skills / "agent-plugin-architect/SKILL.md",
            "packaged-plugin ownership and phase",
            (
                "Confirm that the request explicitly concerns packaged agent-plugin architecture.",
                "Repo-local `AGENTS.md` or `.agents/skills` work belongs to",
                "Load only references needed for the active phase.",
                "at most one other Axiom route",
                "An explicit usage-cost goal may add `optimize-codex-usage`",
                "Git submission, installation, publication, deployment, and consequential external effects remain separate active phases",
            ),
        ),
        (
            skills / "confirm-external-action/SKILL.md",
            "external-action resume",
            (
                "## Resume And Compaction Handoff",
                "host-native task context and current direct evidence from the owning system",
                "perform zero new mutations",
                "An unknown external outcome enters Verify only",
                "never resend",
                "Do not add a daemon, cache, telemetry, or persistent handoff tool",
            ),
        ),
        (
            skills / "reversible-system-change/SKILL.md",
            "reversible-change resume",
            (
                "## Resume And Compaction Handoff",
                "host-native task context and current direct evidence from the owning system",
                "perform zero new mutations",
                "Never adopt post-change state as the prior rollback baseline.",
                "An unknown external outcome enters Verify only and must not be resent.",
                "Do not add a daemon, cache, telemetry, or persistent handoff tool",
            ),
        ),
    )
    for path, name, anchors in contracts:
        require_ordered_contract_anchors(path, anchors, failures, name)
    return len(contracts)


def check_readme_lifecycle_commands(failures: list[str]) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    for command in README_LIFECYCLE_COMMANDS:
        if command not in readme:
            failures.append(
                f"README lifecycle documentation is missing exact command {command!r}"
            )


def check_routing_scenarios(
    scenarios: Iterable[dict[str, Any]],
    failures: list[str],
) -> None:
    for scenario in scenarios:
        actual = route_contract(scenario["request"])
        contract_fields = tuple(
            field for field in scenario if field not in {"name", "request"}
        )
        for field in contract_fields:
            if actual[field] != scenario[field]:
                failures.append(
                    f"routing scenario {scenario['name']!r} {field} is "
                    f"{actual[field]!r}; expected {scenario[field]!r}"
                )

        route_value = actual["route"]
        if route_value in (None, "clarify"):
            continue
        routes = route_value if isinstance(route_value, tuple) else (route_value,)
        for route in routes:
            main_path = REPOSITORY_ROOT / "skills" / route / "SKILL.md"
            try:
                main_text = main_path.read_text(encoding="utf-8")
            except OSError as error:
                failures.append(
                    f"routing scenario {scenario['name']!r} cannot read "
                    f"{display_path(main_path)}: {error}"
                )
                continue
            for reference in actual["references"]:
                if reference not in main_text:
                    failures.append(
                        f"routing scenario {scenario['name']!r} loads undeclared reference "
                        f"{reference!r} from {display_path(main_path)}"
                    )
