"""Focused tests for the dependency-free YAML subset."""

import unittest

from axiom_validation.yaml_subset import (
    CanonicalYamlError,
    CanonicalYamlScalar,
    parse_canonical_yaml_document,
    split_yaml_comment,
)


class YamlSubsetTests(unittest.TestCase):
    def test_canonical_mapping_and_sequence(self):
        document = parse_canonical_yaml_document("on:\n  push:\n    branches:\n      - main\n", "fixture")
        self.assertIn("on", document)

    def test_duplicate_mapping_key_is_rejected(self):
        with self.assertRaisesRegex(CanonicalYamlError, "duplicate mapping key"):
            parse_canonical_yaml_document("name: one\nname: two\n", "fixture:duplicate")

    def test_comment_split_respects_quoted_hashes(self):
        cases = (
            ("'plain value' # comment", ("'plain value'", "comment")),
            (
                "'can''t # inside' # outside",
                ("'can''t # inside'", "outside"),
            ),
            ('"hash # inside" # outside', ('"hash # inside"', "outside")),
            ("plain # outside", ("plain", "outside")),
            ("plain#inside", ("plain#inside", "")),
            (
                "'two '''' quotes' # outside",
                ("'two '''' quotes'", "outside"),
            ),
            ("'a''b' # one comment", ("'a''b'", "one comment")),
            ("# at zero", ("", "at zero")),
            (
                '"escaped \\\\ and \\" # inside" # outside',
                ('"escaped \\\\ and \\" # inside"', "outside"),
            ),
        )
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(expected, split_yaml_comment(raw))

    def test_quoted_scalars_decode_and_keep_comments(self):
        cases = (
            (
                "value: 'can''t # inside' # outside\n",
                CanonicalYamlScalar("can't # inside", "outside", 1),
            ),
            (
                "value: 'two '''' quotes' # outside\n",
                CanonicalYamlScalar("two '' quotes", "outside", 1),
            ),
            (
                "value: '''' # outside\n",
                CanonicalYamlScalar("'", "outside", 1),
            ),
            (
                'value: "escaped \\\\ and \\" # inside" # outside\n',
                CanonicalYamlScalar('escaped \\ and " # inside', "outside", 1),
            ),
            (
                "value: '' # empty single\n",
                CanonicalYamlScalar("", "empty single", 1),
            ),
            (
                'value: "" # empty double\n',
                CanonicalYamlScalar("", "empty double", 1),
            ),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                document = parse_canonical_yaml_document(text, "fixture")
                self.assertEqual(expected, document["value"])

    def test_invalid_quoted_scalars_are_rejected(self):
        cases = (
            "value: 'unterminated\n",
            'value: "unterminated\n',
            "value: 'closed' unexpected-tail\n",
            'value: "closed" unexpected-tail\n',
            "value: 'a''\n",
            "value: '''\n",
        )
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(CanonicalYamlError, "quoted scalar"):
                    parse_canonical_yaml_document(text, "fixture:invalid")

    def test_noncanonical_line_surfaces_stay_rejected(self):
        cases = (
            ("value: plain\r\n", "LF line endings"),
            ("value:\n\tchild: plain\n", "must not contain tabs"),
            ("value: plain \n", "must not contain trailing spaces"),
            ("value: plain\n---\nother: value\n", "multiple YAML documents"),
            ("value: plain\n...\n", "multiple YAML documents"),
        )
        for text, expected_error in cases:
            with self.subTest(text=text):
                with self.assertRaisesRegex(CanonicalYamlError, expected_error):
                    parse_canonical_yaml_document(text, "fixture:policy")


if __name__ == "__main__":
    unittest.main()
