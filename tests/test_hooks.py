"""Focused tests for platform-specific hook policy."""

import unittest

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.hooks import check_declared_hook_paths, check_exact_hook_shapes
from axiom_validation.manifests import JSON_FILES, load_json
from tests.fixtures.hooks import check_hook_lifecycle_fixtures


class HookPolicyTests(unittest.TestCase):
    def documents(self):
        failures = []
        documents = {}
        for relative_path in JSON_FILES:
            document = load_json(REPOSITORY_ROOT / relative_path, failures)
            if document is not None:
                documents[relative_path] = document
        self.assertEqual([], failures)
        return documents

    def test_checked_in_hook_shapes(self):
        failures = []
        documents = self.documents()
        check_declared_hook_paths(documents, failures)
        check_exact_hook_shapes(documents, failures)
        self.assertEqual([], failures)

    def test_lifecycle_mutations_are_rejected(self):
        failures = []
        count = check_hook_lifecycle_fixtures(self.documents(), failures)
        self.assertEqual(3, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
