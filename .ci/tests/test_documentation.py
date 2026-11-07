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
    GENERATED_MARKER,
    check_documentation,
    check_translation_text,
    check_translations,
    discover_markdown,
    is_current_document,
    is_translation,
    translation_documents,
    translation_source,
)
from axiom_validation.markdown import fenced_blocks_and_masked_text


def generated_region_count(paths: tuple[Path, ...]) -> int:
    """Count closed generated regions outside code fences, independently of the validator."""
    count = 0
    for path in paths:
        _, searchable = fenced_blocks_and_masked_text(path.read_text(encoding="utf-8"))
        count += sum(1 for match in GENERATED_MARKER.finditer(searchable) if match.group(2) == "end")
    return count


class DocumentationValidationTests(unittest.TestCase):
    def test_checked_in_documentation_contract(self):
        failures: list[str] = []
        report = check_documentation(failures)
        self.assertEqual([], failures)
        # The Markdown and generated-region totals are recomputed here; the current
        # and indexed document totals change only with a deliberate documentation
        # change.
        markdown = discover_markdown(REPOSITORY_ROOT)
        self.assertEqual(len(markdown), report.markdown_count)
        self.assertEqual(20, report.current_document_count)
        self.assertEqual(14, report.indexed_document_count)
        self.assertEqual(generated_region_count(markdown), report.generated_region_count)
        self.assertEqual(6, report.translation_count)

    def test_named_negative_fixtures_are_all_rejected(self):
        failures: list[str] = []
        rejected = check_documentation_negative_fixtures(failures)
        self.assertEqual(len(NEGATIVE_FIXTURES), rejected)
        self.assertEqual(17, rejected)
        self.assertEqual([], failures)

    def test_standard_library_command_line_entrypoint(self):
        result = subprocess.run(
            [sys.executable, ".ci/scripts/check-documentation.py"],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertIn("6 translations", result.stdout)
        self.assertIn("17 negative fixtures", result.stdout)

    def test_translations_are_not_current_documents_and_name_their_source(self):
        self.assertTrue(is_translation("docs/examples.zh-CN.md"))
        self.assertFalse(is_current_document("docs/examples.zh-CN.md"))
        self.assertFalse(is_current_document("README.zh-CN.md"))
        self.assertEqual("docs/examples.md", translation_source("docs/examples.zh-CN.md"))
        self.assertEqual("README.md", translation_source("README.zh-CN.md"))

    def test_checked_in_translations_mirror_their_sources(self):
        failures: list[str] = []
        count = check_translations(REPOSITORY_ROOT, failures)
        self.assertEqual([], failures)
        self.assertEqual(6, count)
        self.assertEqual(
            {
                "README.zh-CN.md",
                "docs/README.zh-CN.md",
                "docs/examples.zh-CN.md",
                "docs/guides/getting-started.zh-CN.md",
                "docs/guides/managing-installation.zh-CN.md",
                "docs/trust-model.zh-CN.md",
            },
            {path.relative_to(REPOSITORY_ROOT).as_posix() for path in translation_documents(REPOSITORY_ROOT)},
        )

    def test_translation_may_substitute_its_own_translation_in_links(self):
        root = Path("/fixture").resolve()
        failures: list[str] = []
        check_translation_text(
            "docs/a.zh-CN.md",
            "# A\n\n[English](a.md) | \u7b80\u4f53\u4e2d\u6587\n\n[B](b.zh-CN.md) [C](c.md#anchor)\n",
            "docs/a.md",
            "# A\n\nEnglish | [Simplified Chinese (zh-CN)](a.zh-CN.md)\n\n[B](b.md) [C](c.md#other)\n",
            failures,
            root=root,
        )
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
