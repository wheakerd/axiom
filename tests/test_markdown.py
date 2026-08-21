"""Focused tests for Markdown and repository-link policy."""

import unittest

from axiom_validation.markdown import check_markdown_links, gfm_heading_slug


class MarkdownPolicyTests(unittest.TestCase):
    def test_checked_in_links_and_fragments(self):
        failures = []
        count = check_markdown_links(failures)
        self.assertGreater(count, 0)
        self.assertEqual([], failures)

    def test_gfm_slug_is_deterministic(self):
        self.assertEqual("release-policy-evidence", gfm_heading_slug("Release Policy & Evidence"))


if __name__ == "__main__":
    unittest.main()
