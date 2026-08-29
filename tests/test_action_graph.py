"""Focused tests for GitHub Actions graph policy."""

import unittest
from unittest import mock

from axiom_validation.action_graph import (
    check_distribution_workflow_contract,
    check_distribution_workflow_text,
    check_github_action_pin_counts,
    check_github_action_pins,
    check_hook_runtime_workflow_contract,
    check_hook_runtime_workflow_text,
    check_unit_test_workflow_contract,
    check_unit_test_workflow_text,
)
from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.cases.action_graph import check_action_graph_fixtures


class ActionGraphTests(unittest.TestCase):
    def test_checked_in_action_graph(self):
        failures = []
        counts = check_github_action_pin_counts(failures)
        count = check_github_action_pins([])
        document = check_distribution_workflow_contract(failures)
        unit_test_document = check_unit_test_workflow_contract(failures)
        hook_runtime_document = check_hook_runtime_workflow_contract(failures)
        self.assertEqual(15, count)
        self.assertEqual(15, counts.total)
        self.assertEqual(0, counts.dockerfile_base_images)
        self.assertEqual(0, counts.dockerfile_other_inputs)
        self.assertIsNotNone(document)
        self.assertIsNotNone(unit_test_document)
        self.assertIsNotNone(hook_runtime_document)
        self.assertEqual([], failures)

    def test_distribution_workflow_security_toolchain_and_validator_mutations_are_rejected(self):
        path = REPOSITORY_ROOT / ".github" / "workflows" / "distribution-drift.yml"
        original = path.read_text(encoding="utf-8")
        environment_block = (
            "      - name: Report canonical environment\n"
            "        run: |\n"
            "          cat /etc/os-release\n"
            "          python --version\n"
            "          node --version\n"
            "          git --version\n\n"
        )
        scenarios = (
            (
                "moving runner",
                original.replace("ubuntu-24.04", "ubuntu-latest", 1),
                "ubuntu-24.04",
            ),
            (
                "moving Python selector",
                original.replace('python-version: "3.14.7"', 'python-version: "3.14"', 1),
                "exact Python 3.14.7",
            ),
            (
                "moving Node.js selector",
                original.replace('node-version: "24.19.0"', 'node-version: "24"', 1),
                "Node.js 24.19.0",
            ),
            (
                "tagged setup Action",
                original.replace(
                    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
                    "actions/setup-python@v6",
                    1,
                ),
                "exact Python 3.14.7",
            ),
            (
                "package-manager cache enabled",
                original.replace("package-manager-cache: false", "package-manager-cache: true", 1),
                "caching disabled",
            ),
            (
                "environment report removed",
                original.replace(environment_block, "", 1),
                "exactly six canonical validation steps",
            ),
            (
                "checkout credentials persisted",
                original.replace("persist-credentials: false", "persist-credentials: true", 1),
                "must not persist credentials",
            ),
            (
                "pull-request target",
                original.replace("pull_request:", "pull_request_target:", 1),
                "only pull_request, push, and workflow_dispatch",
            ),
            (
                "write permission",
                original.replace("contents: read", "contents: write", 1),
                "read-only",
            ),
            (
                "secret expression",
                original.replace(
                    "permissions:\n",
                    "env:\n  FIXTURE: ${{ secrets.FIXTURE }}\n\npermissions:\n",
                    1,
                ),
                "forbidden pull-request surface",
            ),
            (
                "renamed stable check",
                original.replace("  repository-guards:\n", "  renamed-guards:\n", 1),
                "only the repository-guards job",
            ),
            (
                "merged validator purpose",
                original.replace(
                    "python -B scripts/check-distribution-drift.py",
                    "python -B scripts/check-publication.py",
                    1,
                ),
                "exact read-only validator step",
            ),
        )
        for name, mutated, owned_reason in scenarios:
            with self.subTest(name=name):
                self.assertNotEqual(original, mutated)
                failures = []
                check_distribution_workflow_text(mutated, failures)
                self.assertTrue(
                    any(owned_reason in failure for failure in failures),
                    failures,
                )

    def test_hook_runtime_workflow_gate_matrix_and_security_mutations_are_rejected(self):
        path = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "hook-runtime-integration.yml"
        )
        original = path.read_text(encoding="utf-8")
        scenarios = (
            (
                "write permission",
                original.replace("contents: read", "contents: write", 1),
                "read-only",
            ),
            (
                "pull request target",
                original.replace("pull_request:", "pull_request_target:", 1),
                "forbidden pull-request surface",
            ),
            (
                "moving Windows runner",
                original.replace("windows-2025", "windows-latest", 1),
                "exact Ubuntu, Windows, and macOS runner matrix",
            ),
            (
                "secret expression",
                original.replace(
                    "permissions:\n",
                    "env:\n  FIXTURE: ${{ secrets.FIXTURE }}\n\npermissions:\n",
                    1,
                ),
                "forbidden pull-request surface",
            ),
            (
                "duplicated hook command",
                original.replace(
                    "python -B -m unittest tests.hook_runtime_integration -v",
                    "python -B -m unittest tests.test_hooks -v",
                    1,
                ),
                "Execute exact SessionStart hooks",
            ),
            (
                "missing weekly observation",
                original.replace(
                    '  schedule:\n    - cron: "17 6 * * 1"\n',
                    "",
                    1,
                ),
                "bounded weekly schedule",
            ),
            (
                "renamed aggregate job",
                original.replace(
                    "  hook-runtime-gate:\n",
                    "  renamed-runtime-gate:\n",
                    1,
                ),
                "only hook-runtime and hook-runtime-gate jobs",
            ),
            (
                "conditional aggregate job",
                original.replace(
                    "if: ${{ always() }}",
                    "if: ${{ success() }}",
                    1,
                ),
                "use if: always()",
            ),
            (
                "aggregate ignores matrix",
                original.replace(
                    "      - hook-runtime\n",
                    "      - repository-guards\n",
                    1,
                ),
                "depend only on the full hook-runtime matrix",
            ),
            (
                "aggregate accepts failure",
                original.replace(
                    'test "$HOOK_RUNTIME_RESULT" = success',
                    'test "$HOOK_RUNTIME_RESULT" != success',
                    1,
                ),
                "fail closed",
            ),
        )
        for name, mutated, owned_reason in scenarios:
            with self.subTest(name=name):
                self.assertNotEqual(original, mutated)
                failures = []
                check_hook_runtime_workflow_text(mutated, failures)
                self.assertTrue(
                    any(owned_reason in failure for failure in failures),
                    failures,
                )

    def test_unit_test_workflow_security_and_toolchain_mutations_are_rejected(self):
        path = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "unit-and-integration-tests.yml"
        )
        original = path.read_text(encoding="utf-8")
        scenarios = (
            (
                "write permission",
                original.replace("contents: read", "contents: write", 1),
                "read-only",
            ),
            (
                "pull request target",
                original.replace("pull_request:", "pull_request_target:", 1),
                "only pull_request and push",
            ),
            (
                "moving Python",
                original.replace(
                    'python-version: "3.14.7"',
                    'python-version: "3.14"',
                    1,
                ),
                "exact Python 3.14.7",
            ),
            (
                "secret expression",
                original.replace(
                    "permissions:\n",
                    "env:\n  FIXTURE: ${{ secrets.FIXTURE }}\n\npermissions:\n",
                    1,
                ),
                "forbidden pull-request surface",
            ),
        )
        for name, mutated, owned_reason in scenarios:
            with self.subTest(name=name):
                self.assertNotEqual(original, mutated)
                failures = []
                check_unit_test_workflow_text(mutated, failures)
                self.assertTrue(
                    any(owned_reason in failure for failure in failures),
                    failures,
                )

    def test_action_graph_mutations_are_rejected(self):
        failures = []
        count = check_action_graph_fixtures(failures)
        self.assertEqual(92, count)
        self.assertEqual([], failures)

    def test_docker_action_validation_does_not_open_a_network_socket(self):
        failures = []
        with mock.patch(
            "socket.socket",
            side_effect=AssertionError("action-graph validation must stay offline"),
        ):
            count = check_action_graph_fixtures(failures)
        self.assertEqual(92, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
