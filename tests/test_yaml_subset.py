"""Focused tests for the dependency-free YAML subset."""

import unittest

from axiom_validation.yaml_subset import CanonicalYamlError, parse_canonical_yaml_document


class YamlSubsetTests(unittest.TestCase):
    def test_canonical_mapping_and_sequence(self):
        document = parse_canonical_yaml_document("on:\n  push:\n    branches:\n      - main\n", "fixture")
        self.assertIn("on", document)

    def test_duplicate_mapping_key_is_rejected(self):
        with self.assertRaisesRegex(CanonicalYamlError, "duplicate mapping key"):
            parse_canonical_yaml_document("name: one\nname: two\n", "fixture:duplicate")


if __name__ == "__main__":
    unittest.main()
