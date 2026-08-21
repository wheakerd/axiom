"""GitHub Actions and pull-request regression fixtures."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from axiom_validation.action_graph import check_github_action_pins_from_root
from axiom_validation.manifests import check_manifest_versions
from axiom_validation.yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


def check_action_graph_fixtures(failures: list[str]) -> int:
    """Exercise transitive local-action resolution without touching the repository."""
    rejected = 0
    workflow_template = (
        "name: Fixture\n"
        "on:\n"
        "  workflow_dispatch:\n"
        "jobs:\n"
        "  guard:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Guard\n"
        "        uses: {uses}\n"
    )
    composite_header = (
        "name: Fixture\n"
        "description: Fixture action\n"
        "runs:\n"
        "  using: composite\n"
        "  steps:\n"
    )

    def write(root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="axiom-action-fixtures-") as raw_root:
        fixture_root = Path(raw_root)

        indirect = fixture_root / "indirect"
        write(
            indirect,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            indirect,
            ".github/actions/wrapper/action.yml",
            composite_header
            + "    - name: Moving dependency\n"
            + "      uses: actions/setup-python@v6\n",
        )
        indirect_failures: list[str] = []
        check_github_action_pins_from_root(indirect, indirect_failures)
        if any("actions/setup-python@v6" in failure for failure in indirect_failures):
            rejected += 1
        else:
            failures.append("indirect moving-action fixture was not rejected transitively")

        moving_container = fixture_root / "moving-container"
        write(
            moving_container,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container: ubuntu:latest\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        run: echo guarded\n",
        )
        moving_container_failures: list[str] = []
        check_github_action_pins_from_root(
            moving_container, moving_container_failures
        )
        if any(
            "workflow container 'ubuntu:latest'" in failure
            for failure in moving_container_failures
        ):
            rejected += 1
        else:
            failures.append("moving workflow-container fixture was not rejected")

        traversal = fixture_root / "traversal"
        write(
            traversal,
            ".github/workflows/guard.yml",
            workflow_template.format(
                uses="./.github/actions/../actions/wrapper"
            ),
        )
        traversal_failures: list[str] = []
        check_github_action_pins_from_root(traversal, traversal_failures)
        if any("traversal or ambiguity" in failure for failure in traversal_failures):
            rejected += 1
        else:
            failures.append("local-action traversal fixture was not rejected")

        missing = fixture_root / "missing-metadata"
        write(
            missing,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(missing, ".github/actions/wrapper/README.md", "fixture\n")
        missing_failures: list[str] = []
        check_github_action_pins_from_root(missing, missing_failures)
        if any("exactly one action.yml or action.yaml" in failure for failure in missing_failures):
            rejected += 1
        else:
            failures.append("missing local-action metadata fixture was not rejected")

        cycle = fixture_root / "cycle"
        write(
            cycle,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/one"),
        )
        write(
            cycle,
            ".github/actions/one/action.yml",
            composite_header
            + "    - name: Two\n"
            + "      uses: ./.github/actions/two\n",
        )
        write(
            cycle,
            ".github/actions/two/action.yaml",
            composite_header
            + "    - name: One\n"
            + "      uses: ./.github/actions/one\n",
        )
        cycle_failures: list[str] = []
        check_github_action_pins_from_root(cycle, cycle_failures)
        if any("local uses cycle detected" in failure for failure in cycle_failures):
            rejected += 1
        else:
            failures.append("local composite-action cycle fixture was not rejected")

        duplicate = fixture_root / "duplicate-key"
        write(
            duplicate,
            ".github/workflows/guard.yml",
            workflow_template.format(uses="./.github/actions/wrapper"),
        )
        write(
            duplicate,
            ".github/actions/wrapper/action.yml",
            "name: Fixture\n"
            "description: Fixture action\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n"
            "runs:\n"
            "  using: composite\n"
            "  steps:\n",
        )
        duplicate_failures: list[str] = []
        check_github_action_pins_from_root(duplicate, duplicate_failures)
        if any("duplicate mapping key 'runs'" in failure for failure in duplicate_failures):
            rejected += 1
        else:
            failures.append("duplicate action-metadata key fixture was not rejected")

        valid = fixture_root / "valid"
        job_digest = "c" * 64
        service_digest = "d" * 64
        write(
            valid,
            ".github/workflows/guard.yml",
            "name: Fixture\n"
            "on:\n"
            "  workflow_dispatch:\n"
            "jobs:\n"
            "  guard:\n"
            "    runs-on: ubuntu-latest\n"
            "    container:\n"
            f"      image: ghcr.io/example/job@sha256:{job_digest}\n"
            "    services:\n"
            "      database:\n"
            f"        image: ghcr.io/example/database@sha256:{service_digest}\n"
            "    steps:\n"
            "      - name: Guard\n"
            "        uses: ./.github/actions/root\n",
        )
        write(
            valid,
            ".github/actions/root/action.yml",
            composite_header
            + "    - name: Nested composite\n"
            + "      uses: ./.github/actions/nested\n"
            + "    - name: Local JavaScript\n"
            + "      uses: ./.github/actions/javascript\n"
            + "    - name: Local Docker\n"
            + "      uses: ./.github/actions/docker\n",
        )
        sha = "a" * 40
        digest = "b" * 64
        write(
            valid,
            ".github/actions/nested/action.yaml",
            composite_header
            + "    - name: Pinned action\n"
            + f"      uses: actions/setup-python@{sha} # v6\n"
            + "    - name: Pinned container\n"
            + f"      uses: docker://ghcr.io/example/action@sha256:{digest}\n",
        )
        write(
            valid,
            ".github/actions/javascript/action.yml",
            "name: JavaScript fixture\n"
            "description: JavaScript fixture action\n"
            "runs:\n"
            "  using: node20\n"
            "  main: dist/index.js\n",
        )
        write(valid, ".github/actions/javascript/dist/index.js", "'use strict';\n")
        write(
            valid,
            ".github/actions/docker/action.yml",
            "name: Docker fixture\n"
            "description: Docker fixture action\n"
            "runs:\n"
            "  using: docker\n"
            "  image: Dockerfile\n",
        )
        write(valid, ".github/actions/docker/Dockerfile", "FROM scratch\n")
        valid_failures: list[str] = []
        valid_pins = check_github_action_pins_from_root(valid, valid_failures)
        if valid_failures or valid_pins != 4:
            failures.append(
                "valid pinned local composite, JavaScript, and Docker action graph failed: "
                + "; ".join(valid_failures)
            )

    return rejected + 1


def check_pull_request_validation_fixtures(
    distribution_document: dict[str, Any] | None,
    release_workflow_text: str | None,
    documents: dict[str, dict[str, Any]],
    failures: list[str],
) -> int:
    label = "pull-request validation event graph"
    if distribution_document is None or release_workflow_text is None:
        failures.append(f"{label} could not be constructed from both workflows")
        return 0
    try:
        release_document = parse_canonical_yaml_document(
            release_workflow_text,
            ".github/workflows/release-signature-guard.yml",
        )
    except CanonicalYamlError as error:
        failures.append(str(error))
        return 0

    distribution_triggers = distribution_document.get("on")
    release_triggers = release_document.get("on")
    distribution_events = (
        set(distribution_triggers) if isinstance(distribution_triggers, dict) else set()
    )
    release_events = set(release_triggers) if isinstance(release_triggers, dict) else set()
    pull_request = (
        distribution_triggers.get("pull_request")
        if isinstance(distribution_triggers, dict)
        else None
    )
    pull_request_branches = (
        {
            item.value
            for item in pull_request.get("branches", [])
            if isinstance(item, CanonicalYamlScalar)
        }
        if isinstance(pull_request, dict)
        else set()
    )
    scenarios = (
        {
            "name": "same-repository-unsigned-valid",
            "base": "main",
            "headRepository": "wheakerd/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-unsigned-valid",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": True,
        },
        {
            "name": "fork-manifest-version-violation",
            "base": "main",
            "headRepository": "contributor/axiom",
            "signed": False,
            "valid": False,
        },
    )
    for scenario in scenarios:
        name = scenario["name"]
        static_scheduled = (
            "pull_request" in distribution_events
            and scenario["base"] in pull_request_branches
        )
        provenance_scheduled = "pull_request" in release_events
        if not static_scheduled:
            failures.append(f"{label}:{name} did not schedule static validation")
        if provenance_scheduled:
            failures.append(f"{label}:{name} incorrectly scheduled release provenance")

        fixture_documents = json.loads(json.dumps(documents))
        expected_valid = bool(scenario["valid"])
        if not expected_valid:
            manifest = fixture_documents.get(".claude-plugin/plugin.json")
            if not isinstance(manifest, dict):
                failures.append(f"{label}:{name} could not construct the invalid fixture")
                continue
            manifest["version"] = "9.9.9"
        fixture_failures: list[str] = []
        check_manifest_versions(fixture_documents, fixture_failures)
        observed_valid = not fixture_failures
        if observed_valid != expected_valid:
            detail = "; ".join(fixture_failures) if fixture_failures else "accepted"
            failures.append(
                f"{label}:{name} publication result was {detail}; "
                f"expected {'pass' if expected_valid else 'rejection'}"
            )
    return len(scenarios)
