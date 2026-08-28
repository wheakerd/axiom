"""Focused tests for platform-specific hook policy."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.hooks import (
    CODEX_HOOK_TIMEOUT_SECONDS,
    CODEX_WINDOWS_COMMAND,
    CODEX_WINDOWS_WRAPPER_PATH,
    CODEX_WINDOWS_WRAPPER_TEXT,
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
        self.assertEqual(9, count)
        self.assertEqual([], failures)

    def test_windows_hook_uses_packaged_wrapper_with_bounded_timeout(self):
        handler = self.documents()["hooks/codex-hooks.json"]["hooks"]["SessionStart"][0][
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

    @unittest.skipUnless(os.name == "nt", "requires a real Windows command shell")
    def test_checked_in_windows_hook_ignores_workspace_executable_canaries(self):
        handler = self.documents()["hooks/codex-hooks.json"]["hooks"]["SessionStart"][0][
            "hooks"
        ][0]
        heading = (
            b"You have Axiom. Load this startup front door before deciding whether any "
            b"Axiom skill applies:\r\n\r\n"
        )
        skill_bytes = (REPOSITORY_ROOT / "skills/using-axiom/SKILL.md").read_bytes()

        with tempfile.TemporaryDirectory(prefix="axiom-hook-") as temporary:
            root = Path(temporary)
            plugin_root = root / "plugin root !% & (trusted)"
            workspace = root / "workspace !% & (untrusted)"
            skill_path = plugin_root / "skills" / "using-axiom" / "SKILL.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_bytes(skill_bytes)
            wrapper_path = plugin_root / CODEX_WINDOWS_WRAPPER_PATH
            wrapper_path.parent.mkdir(parents=True)
            wrapper_path.write_bytes(
                (REPOSITORY_ROOT / CODEX_WINDOWS_WRAPPER_PATH).read_bytes()
            )
            workspace.mkdir()

            marker = workspace / "workspace-program-ran"
            canary = b'@echo hijacked>"%~dp0workspace-program-ran"\r\n'
            for name in (
                "codex-session-start.cmd",
                "echo.cmd",
                "setlocal.cmd",
                "type.cmd",
                "powershell.cmd",
                "pwsh.cmd",
            ):
                (workspace / name).write_bytes(canary)
            (workspace / "cmd.exe").write_bytes(b"not a Windows executable")
            (workspace / "powershell.exe").write_bytes(b"not a Windows executable")

            environment = os.environ.copy()
            environment["PLUGIN_ROOT"] = str(plugin_root)
            comspec = environment.get("COMSPEC", "cmd.exe")
            codex_raw_command_line = (
                f'{subprocess.list2cmdline([comspec])} /C '
                f'"{handler["commandWindows"]}"'
            )
            result = subprocess.run(
                codex_raw_command_line,
                executable=comspec,
                cwd=workspace,
                env=environment,
                input=b"{}",
                capture_output=True,
                check=False,
                timeout=handler["timeout"],
            )

            self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))
            self.assertEqual(heading + skill_bytes, result.stdout)
            self.assertEqual(b"", result.stderr)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
