"""Focused tests for platform-specific hook policy."""

import unittest

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.hooks import (
    CODEX_HOOK_TIMEOUT_SECONDS,
    CODEX_WINDOWS_COMMAND,
    CODEX_WINDOWS_WRAPPER_PATH,
    CODEX_WINDOWS_WRAPPER_TEXT,
    PACKAGED_WRAPPERS,
    PROMPT_TEXT,
    STOP_TEXT,
    check_codex_windows_hook_security,
    check_declared_hook_paths,
    check_exact_hook_shapes,
)
from axiom_validation.manifests import JSON_FILES, load_json
from axiom_validation.cases.hooks import check_hook_lifecycle_fixtures


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
        check_codex_windows_hook_security(documents, failures)
        self.assertEqual([], failures)

    def test_lifecycle_mutations_are_rejected(self):
        failures = []
        count = check_hook_lifecycle_fixtures(self.documents(), failures)
        self.assertEqual(13, count)
        self.assertEqual([], failures)

    def test_windows_hook_uses_packaged_wrapper_with_bounded_timeout(self):
        handler = self.documents()["plugin/hooks/codex-hooks.json"]["hooks"]["SessionStart"][0][
            "hooks"
        ][0]
        self.assertEqual(CODEX_WINDOWS_COMMAND, handler["commandWindows"])
        self.assertEqual(CODEX_HOOK_TIMEOUT_SECONDS, handler["timeout"])
        self.assertNotIn("powershell", handler["commandWindows"].casefold())
        self.assertNotIn("pwsh", handler["commandWindows"].casefold())
        self.assertEqual(
            CODEX_WINDOWS_WRAPPER_TEXT,
            (REPOSITORY_ROOT / CODEX_WINDOWS_WRAPPER_PATH).read_text(encoding="utf-8"),
        )

    def test_every_packaged_script_is_pinned_and_present(self):
        for relative_path, approved_text in PACKAGED_WRAPPERS.items():
            with self.subTest(script=relative_path):
                path = REPOSITORY_ROOT / relative_path
                self.assertTrue(path.is_file(), relative_path)
                self.assertEqual(approved_text, path.read_text(encoding="utf-8"))
                self.assertNotIn("powershell", approved_text.casefold())
                self.assertNotIn("curl", approved_text.casefold())

    def test_lifecycle_texts_are_plain_json_safe_ascii(self):
        for text in (PROMPT_TEXT, STOP_TEXT):
            with self.subTest(text=text[:24]):
                self.assertTrue(text.isascii())
                for forbidden in ('"', "\\", "&", "|", "<", ">", "^", "%", "!", "(", ")"):
                    self.assertNotIn(forbidden, text)
                self.assertLess(len(text), 600)
        for document_path in ("plugin/hooks/codex-hooks.json", "plugin/hooks/claude-hooks.json"):
            hooks = self.documents()[document_path]["hooks"]
            self.assertEqual({"SessionStart", "UserPromptSubmit", "Stop"}, set(hooks))
            for event in ("UserPromptSubmit", "Stop"):
                self.assertNotIn("matcher", hooks[event][0])


if __name__ == "__main__":
    unittest.main()
