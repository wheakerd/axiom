"""Focused tests for the public documentation information architecture."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from axiom_validation.cases.documentation import (
    NEGATIVE_FIXTURES,
    check_documentation_negative_fixtures,
)
from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.documentation import (
    check_documentation,
    check_lifecycle_text,
    check_skill_reference_inventory_text,
    check_task_navigation_text,
    is_current_document,
)


class DocumentationValidationTests(unittest.TestCase):
    def test_checked_in_documentation_contract(self):
        failures: list[str] = []
        report = check_documentation(failures)
        self.assertEqual([], failures)
        self.assertEqual(154, report.markdown_count)
        self.assertEqual(25, report.current_document_count)
        self.assertEqual(19, report.indexed_document_count)
        self.assertEqual(40, report.generated_region_count)
        self.assertEqual((REPOSITORY_ROOT / "README.md").stat().st_size, report.readme_bytes)
        self.assertEqual("within", report.preferred_budget_status)

    def test_named_negative_fixtures_are_all_rejected(self):
        failures: list[str] = []
        rejected = check_documentation_negative_fixtures(failures)
        self.assertEqual(len(NEGATIVE_FIXTURES), rejected)
        self.assertEqual(21, rejected)
        self.assertEqual([], failures)

    def test_standard_library_command_line_entrypoint(self):
        result = subprocess.run(
            [sys.executable, "scripts/check-documentation.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn(
            f"README {(REPOSITORY_ROOT / 'README.md').stat().st_size} bytes "
            "(preferred 4-8 KiB: within)", result.stdout
        )
        self.assertIn("21 negative fixtures", result.stdout)

    def test_skill_inventory_ignores_headings_in_usage_examples(self):
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                failures: list[str] = []
                check_skill_reference_inventory_text(
                    "# A\n\n## Shared skills\n\n"
                    "### using-axiom\n\n**Usage:**\n\n"
                    f"{fence}text\n## Shared skills\n### example-only\n{fence}\n\n"
                    "### fixture-route\n\n## Renamed and retired skills\n\n"
                    "### retired-route\n",
                    "# Gate\n\n## Bundled Routes\n\n- `fixture-route`: route.\n",
                    failures,
                )
                self.assertEqual([], failures)

    def test_skill_inventory_does_not_leak_into_following_sections(self):
        for heading in ("# Other", "## Other"):
            with self.subTest(heading=heading):
                failures: list[str] = []
                check_skill_reference_inventory_text(
                    "# A\n\n## Shared skills\n\n### using-axiom\n\n"
                    f"{heading}\n\n### fixture-route\n",
                    "# Gate\n\n## Bundled Routes\n\n- `fixture-route`: route.\n",
                    failures,
                )
                self.assertTrue(any(
                    "differs from the canonical front door" in failure
                    for failure in failures
                ))

    def test_skill_inventory_requires_each_skill_once_in_canonical_order(self):
        for skills in (
            ("using-axiom",),
            ("using-axiom", "fixture-route", "fixture-route"),
            ("fixture-route", "using-axiom"),
        ):
            with self.subTest(skills=skills):
                failures: list[str] = []
                check_skill_reference_inventory_text(
                    "# A\n\n## Shared skills\n\n"
                    + "\n\n".join(f"### {skill}" for skill in skills) + "\n",
                    "# Gate\n\n## Bundled Routes\n\n- `fixture-route`: route.\n",
                    failures,
                )
                self.assertTrue(any(
                    "differs from the canonical front door" in failure
                    for failure in failures
                ))

    def test_skill_inventory_rejects_duplicate_shared_sections(self):
        failures: list[str] = []
        check_skill_reference_inventory_text(
            "# A\n\n## Shared skills\n\n### using-axiom\n\n"
            "## Shared skills\n\n### fixture-route\n",
            "# Gate\n\n## Bundled Routes\n\n- `fixture-route`: route.\n",
            failures,
        )
        self.assertTrue(any(
            "exactly one parseable Shared skills heading" in failure
            for failure in failures
        ))

    def test_task_navigation_rejects_archive_directories_and_their_files(self):
        root = Path("/fixture").resolve()
        for destination in (
            "releases/", "releases/v0.1.0.md",
            "../project/", "../project/plan.md",
            "../evidence/", "../evidence/record.json",
            "../evals/results/", "../evals/results/record.json",
            "../evals/history/", "../evals/history/method.md",
        ):
            with self.subTest(destination=destination):
                failures: list[str] = []
                check_task_navigation_text(
                    root / "docs" / "README.md",
                    f"# Index\n\n## Start By Task\n\n[Record]({destination})\n",
                    root,
                    failures,
                )
                self.assertTrue(any("historical or project-plan" in failure for failure in failures))

    def test_evaluation_guides_are_current_but_history_is_not(self):
        for path in ("evals/README.md", "evals/context-budget/README.md"):
            with self.subTest(path=path):
                self.assertTrue(is_current_document(path))
        self.assertFalse(is_current_document("evals/history/codex-core-v1-v2.md"))

    def test_historical_evaluation_accepts_preserved_lifecycle(self):
        failures: list[str] = []
        check_lifecycle_text(
            "evals/history/codex-core-v1-v2.md",
            "# Historical Method\n\n<!-- lifecycle: historical -->\n",
            failures,
        )
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
