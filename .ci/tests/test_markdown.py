"""Focused tests for Markdown, Hook-reference, and repository-link policy."""

import json
import unittest

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.hooks import HOOK_FILES
from axiom_validation.markdown import (
    HOOK_REFERENCE_PATH,
    check_documented_hook_command_text,
    check_markdown_links,
    gfm_heading_slug,
)


class MarkdownPolicyTests(unittest.TestCase):
    def test_checked_in_links_and_fragments(self):
        failures = []
        count = check_markdown_links(failures)
        self.assertGreater(count, 0)
        self.assertEqual([], failures)

    def test_gfm_slug_is_deterministic(self):
        self.assertEqual("release-policy-evidence", gfm_heading_slug("Release Policy & Evidence"))

    def test_hook_reference_is_derived_from_checked_in_sources(self):
        documents = {
            relative_path: json.loads(
                (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            )
            for relative_path in HOOK_FILES
        }
        reference = HOOK_REFERENCE_PATH.read_text(encoding="utf-8")
        failures = []
        check_documented_hook_command_text(reference, documents, failures)
        self.assertEqual([], failures)

        changed = reference.replace("printf '%s\\n\\n'", "printf '%s\\n'", 1)
        self.assertNotEqual(reference, changed)
        mutation_failures = []
        check_documented_hook_command_text(changed, documents, mutation_failures)
        self.assertTrue(mutation_failures)


if __name__ == "__main__":
    unittest.main()
