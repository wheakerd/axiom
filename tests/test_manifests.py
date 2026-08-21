"""Focused tests for manifest and marketplace policy."""

import unittest

from axiom_validation.context import RELEASE_VERSION, release_version
from axiom_validation.manifests import (
    JSON_FILES,
    check_manifest_capability_schema,
    check_manifest_versions,
    load_json,
)
from tests.fixtures.manifests import check_manifest_schema_fixtures


class ManifestPolicyTests(unittest.TestCase):
    def documents(self):
        failures = []
        documents = {}
        from axiom_validation.context import REPOSITORY_ROOT

        for relative_path in JSON_FILES:
            document = load_json(REPOSITORY_ROOT / relative_path, failures)
            if document is not None:
                documents[relative_path] = document
        self.assertEqual([], failures)
        return documents

    def test_synchronized_manifests_are_the_release_source(self):
        self.assertEqual(RELEASE_VERSION, release_version())
        self.assertIsNotNone(release_version())

    def test_checked_in_schema_and_versions(self):
        failures = []
        documents = self.documents()
        check_manifest_capability_schema(documents, failures)
        check_manifest_versions(documents, failures)
        self.assertEqual([], failures)

    def test_schema_mutations_are_rejected(self):
        failures = []
        count = check_manifest_schema_fixtures(self.documents(), failures)
        self.assertEqual(5, count)
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
