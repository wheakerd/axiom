"""Aggregate Axiom publication validation without adding runtime dependencies."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .action_graph import (
    check_distribution_workflow_contract,
    check_github_action_pins,
    check_unit_test_workflow_contract,
)
from .context import RELEASE_VERSION, REPOSITORY_ROOT
from .context_budget import check_context_budget
from .hooks import (
    check_declared_hook_paths,
    check_exact_hook_shapes,
)
from .manifests import (
    JSON_FILES,
    check_codex_interface,
    check_distribution_identity,
    check_manifest_capability_schema,
    check_manifest_versions,
    check_shared_source_roots,
    load_json,
)
from .markdown import check_documented_hook_commands, check_markdown_links
from .release_policy import check_release_signature_workflow_contract
from .reporting import run_policy
from .repository_policy import (
    REQUIRED_PUBLIC_FILES,
    check_compatibility_evidence,
    check_packaged_skills,
    check_repository_governance_contract,
    check_release_version_surfaces,
    check_required_files,
    check_skill_contracts,
)
from .rollback import ROLLBACK_EVIDENCE_FIELDS
from .routing_contracts import (
    check_cross_route_resume_contracts,
    check_readme_lifecycle_commands,
    check_routing_scenarios,
    check_routing_source_contracts,
)
from .routing_evals import check_routing_evaluations
from tests.fixtures.action_graph import check_pull_request_validation_fixtures
from tests.fixtures.external_action import check_external_action_scenarios
from tests.fixtures.git_contracts import check_traceable_security_contracts
from tests.fixtures.hooks import check_hook_lifecycle_fixtures
from tests.fixtures.manifests import check_manifest_schema_fixtures
from tests.fixtures.parsers import check_validator_negative_fixtures
from tests.fixtures.release_policy import check_release_script_runtime_contract
from tests.fixtures.rollback import check_reversible_safety_scenarios
from tests.fixtures.routing import ROUTING_SCENARIOS


def main() -> int:
    failures: list[str] = []

    run_policy("repository", check_required_files, failures)
    governance_owner_count = run_policy(
        "repository-governance", check_repository_governance_contract, failures
    )
    run_policy("release", check_release_version_surfaces, failures)
    context_scenario_count = run_policy(
        "context-budget", check_context_budget, failures
    )
    validator_fixture_count = run_policy(
        "parsers", check_validator_negative_fixtures, failures
    )
    evidence_record_count, evidence_fixture_count = run_policy(
        "compatibility-evidence", check_compatibility_evidence, failures
    )

    documents: dict[str, dict[str, Any]] = {}

    def load_documents(domain_failures: list[str]) -> None:
        for relative_path in JSON_FILES:
            document = load_json(REPOSITORY_ROOT / relative_path, domain_failures)
            if document is not None:
                documents[relative_path] = document

    run_policy("manifests", load_documents, failures)
    run_policy(
        "manifests",
        lambda domain_failures: check_manifest_capability_schema(
            documents, domain_failures
        ),
        failures,
    )
    manifest_schema_fixture_count = run_policy(
        "manifests",
        lambda domain_failures: check_manifest_schema_fixtures(
            documents, domain_failures
        ),
        failures,
    )
    for operation in (
        check_manifest_versions,
        check_codex_interface,
        check_distribution_identity,
        check_shared_source_roots,
    ):
        run_policy(
            "manifests",
            lambda domain_failures, operation=operation: operation(
                documents, domain_failures
            ),
            failures,
        )

    for operation in (
        check_declared_hook_paths,
        check_exact_hook_shapes,
        check_documented_hook_commands,
    ):
        run_policy(
            "hooks",
            lambda domain_failures, operation=operation: operation(
                documents, domain_failures
            ),
            failures,
        )
    hook_lifecycle_fixture_count = run_policy(
        "hooks",
        lambda domain_failures: check_hook_lifecycle_fixtures(
            documents, domain_failures
        ),
        failures,
    )

    action_pin_count = run_policy("action-graph", check_github_action_pins, failures)
    distribution_workflow_document = run_policy(
        "action-graph", check_distribution_workflow_contract, failures
    )
    unit_test_workflow_document = run_policy(
        "action-graph", check_unit_test_workflow_contract, failures
    )
    release_workflow_text = run_policy(
        "release", check_release_signature_workflow_contract, failures
    )
    pull_request_fixture_count = run_policy(
        "action-graph",
        lambda domain_failures: check_pull_request_validation_fixtures(
            distribution_workflow_document,
            unit_test_workflow_document,
            release_workflow_text,
            documents,
            domain_failures,
        ),
        failures,
    )
    release_provenance_fixture_count = run_policy(
        "release",
        lambda domain_failures: check_release_script_runtime_contract(
            release_workflow_text, domain_failures
        ),
        failures,
    )

    run_policy("routing", check_readme_lifecycle_commands, failures)
    run_policy("repository", check_packaged_skills, failures)
    run_policy("repository", check_skill_contracts, failures)
    run_policy("routing", check_routing_source_contracts, failures)
    cross_route_contract_count = run_policy(
        "routing", check_cross_route_resume_contracts, failures
    )
    run_policy(
        "routing",
        lambda domain_failures: check_routing_scenarios(
            ROUTING_SCENARIOS, domain_failures
        ),
        failures,
    )
    routing_eval_case_count, routing_benchmark_case_count, routing_result_count = (
        run_policy("routing-evals", check_routing_evaluations, failures)
    )
    traceable_security_scenarios = run_policy(
        "git-contracts", check_traceable_security_contracts, failures
    )
    external_action_scenarios = run_policy(
        "external-action", check_external_action_scenarios, failures
    )
    run_policy("rollback", check_reversible_safety_scenarios, failures)
    markdown_count = run_policy("markdown", check_markdown_links, failures)

    conventional_hook = REPOSITORY_ROOT / "hooks" / "hooks.json"
    if conventional_hook.exists():
        failures.append(
            "[hooks] hooks/hooks.json must remain absent so platform-specific hooks "
            "are not auto-discovered"
        )

    if failures:
        print("Publication validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        "Publication validation passed: "
        f"{len(REQUIRED_PUBLIC_FILES)} required files, {len(JSON_FILES)} JSON files, "
        f"{markdown_count} Markdown files, {len(ROUTING_SCENARIOS)} offline route contract fixtures, "
        f"{routing_eval_case_count} black-box routing cases, "
        f"{routing_benchmark_case_count} fixed host benchmark cases, "
        f"{routing_result_count} labeled host result records, "
        f"{context_scenario_count} routing-context lifecycle scenarios, "
        f"{governance_owner_count} critical-path CODEOWNERS entries, "
        f"{traceable_security_scenarios} traceable-Git contract fixtures, "
        f"{external_action_scenarios} external-action gate fixtures, "
        f"{len(ROLLBACK_EVIDENCE_FIELDS) + 1} rollback gate fixtures, "
        f"{cross_route_contract_count} source-linked cross-route/resume contracts, "
        f"{validator_fixture_count} validator parser fixtures, version {RELEASE_VERSION}, "
        f"{evidence_record_count} compatibility evidence records, "
        f"{evidence_fixture_count} compatibility evidence negative fixtures, "
        f"{manifest_schema_fixture_count} manifest schema fixtures, "
        f"{hook_lifecycle_fixture_count} hook lifecycle fixtures, "
        f"{pull_request_fixture_count} pull-request event-graph fixtures, "
        f"{release_provenance_fixture_count} release-provenance fixtures, "
        f"{action_pin_count} immutable action pins, hooks, and packaged skills."
    )
    return 0
