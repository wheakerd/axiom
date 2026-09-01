"""Focused tests for the public documentation information architecture."""

from __future__ import annotations

import subprocess
import sys
import unittest

from axiom_validation.cases.documentation import (
    NEGATIVE_FIXTURES,
    check_documentation_negative_fixtures,
)
from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.documentation import check_documentation


class DocumentationValidationTests(unittest.TestCase):
    def test_checked_in_documentation_contract(self):
        failures: list[str] = []
        report = check_documentation(failures)
        self.assertEqual([], failures)
        self.assertEqual(117, report.markdown_count)
        self.assertEqual(18, report.current_document_count)
        self.assertEqual(13, report.indexed_document_count)
        self.assertEqual(20, report.generated_region_count)
        self.assertEqual(8605, report.readme_bytes)
        self.assertEqual("within", report.preferred_budget_status)

    def test_named_negative_fixtures_are_all_rejected(self):
        failures: list[str] = []
        rejected = check_documentation_negative_fixtures(failures)
        self.assertEqual(len(NEGATIVE_FIXTURES), rejected)
        self.assertEqual(17, rejected)
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
            "README 8605 bytes (preferred 8-12 KiB: within)", result.stdout
        )
        self.assertIn("17 negative fixtures", result.stdout)


if __name__ == "__main__":
    unittest.main()
