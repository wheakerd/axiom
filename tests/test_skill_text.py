"""Tests for the bundled skill readability contract."""

import tempfile
import unittest
from pathlib import Path

from axiom_validation.skill_text import (
    INVARIANT_MAX,
    SENTENCE_MAX_CHARS,
    check_skill_text,
    invariant_items,
    long_sentences,
    sentences,
    text_units,
)

PASSING_SKILL = """---
name: sample
description: Use when the sample applies. Not for anything else.
---

# Sample

Direction in one idea per sentence.

## Invariants

These bind in every phase. Everything else is a default you may adapt, saying so.

1. **Consent.** The user agrees before any subagent starts.
2. **No silent pick.** A material choice is the user's.
3. **Evidence.** A claim rests on a current observation.

## Direction

- Read the request. Then act.
"""


def write_skill(root: Path, name: str, text: str) -> Path:
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


class SkillTextTests(unittest.TestCase):
    def test_units_join_wrapped_lines_and_skip_code_and_tables(self):
        text = (
            "# Title\n\n- first item\n  continues here.\n- second item.\n\n"
            "| a | b |\n| --- | --- |\n\n```\nnot. prose. here\n```\n\nA paragraph\nwrapped twice.\n"
        )
        self.assertEqual(
            ["Title", "first item continues here.", "second item.", "A paragraph wrapped twice."],
            text_units(text),
        )

    def test_sentences_split_at_terminator_and_whitespace_only(self):
        self.assertEqual(["One.", "Two `v2.1.277.` Three?"], sentences("One. Two `v2.1.277.` Three?"))
        self.assertEqual(["One!", "Two."], sentences("One!   Two."))
        self.assertEqual([], long_sentences("x. " * 100))
        self.assertEqual(1, len(long_sentences("y" * (SENTENCE_MAX_CHARS + 1) + ".")))

    def test_invariant_items_are_read_from_their_section_only(self):
        self.assertIsNone(invariant_items("# No section\n\n1. not an invariant\n"))
        self.assertEqual(3, len(invariant_items(PASSING_SKILL)))
        self.assertEqual([], invariant_items("## Invariants\n\nProse only.\n\n## Next\n\n1. later list\n"))

    def test_repository_skills_pass(self):
        failures: list[str] = []
        self.assertEqual(14, check_skill_text(failures))
        self.assertEqual([], failures)

    def test_negative_fixtures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_skill(root, "good", PASSING_SKILL)
            write_skill(root, "no-section", PASSING_SKILL.replace("## Invariants", "## Rules"))
            write_skill(
                root, "too-many", PASSING_SKILL.replace(
                    "3. **Evidence.**", "".join(f"{n}. **Rule {n}.** Item.\n" for n in range(3, INVARIANT_MAX + 2)) + "9. **Evidence.**"
                ),
            )
            write_skill(root, "blanket", PASSING_SKILL + "\nEvery other rule here binds.\n")
            write_skill(root, "long", PASSING_SKILL + "\n" + "word " * 80 + "end.\n")
            reference = root / "good" / "references" / "detail.md"
            reference.parent.mkdir()
            reference.write_text("# Detail\n\n" + "word " * 80 + "end.\n", encoding="utf-8")
            failures: list[str] = []
            self.assertEqual(5, check_skill_text(failures, root))
            joined = "\n".join(failures)
            self.assertIn("no-section/SKILL.md lacks", joined)
            self.assertIn("too-many/SKILL.md lists", joined)
            self.assertIn("blanket binding clause", joined)
            self.assertIn("long/SKILL.md has a sentence", joined)
            self.assertIn("good/references/detail.md has a sentence", joined)
            self.assertNotIn("good/SKILL.md", joined.replace("good/references", ""))


if __name__ == "__main__":
    unittest.main()
