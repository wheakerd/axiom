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
    check_task_navigation_text,
    is_current_document,
)


class DocumentationValidationTests(unittest.TestCase):
    def test_checked_in_documentation_contract(self):
        failures: list[str] = []
        report = check_documentation(failures)
        self.assertEqual([], failures)
        self.assertEqual(131, report.markdown_count)
        self.assertEqual(22, report.current_document_count)
        self.assertEqual(17, report.indexed_document_count)
        self.assertEqual(28, report.generated_region_count)
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
            "(preferred 8-12 KiB: within)", result.stdout
        )
        self.assertIn("21 negative fixtures", result.stdout)

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
