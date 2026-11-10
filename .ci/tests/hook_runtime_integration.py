"""Native runtime integration for the checked-in lifecycle hook commands.

This module is intentionally outside the ``test_*.py`` discovery pattern. The
dedicated cross-platform workflow runs it on each native host while the normal
unit suite keeps structural hook policy separate from host execution.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / ".ci"))
from axiom_validation.hooks import PACKAGED_WRAPPERS, PROMPT_TEXT  # noqa: E402
# The repository keeps the installed plugin under plugin/; the paths below are
# relative to that plugin root, as each host resolves them after installation.
PLUGIN_SOURCE_ROOT = REPOSITORY_ROOT / "plugin"
CODEX_HOOK_PATH = PLUGIN_SOURCE_ROOT / "hooks" / "codex-hooks.json"
CLAUDE_HOOK_PATH = PLUGIN_SOURCE_ROOT / "hooks" / "claude-hooks.json"
WINDOWS_WRAPPER = Path("hooks/codex-session-start.cmd")
PACKAGED_SCRIPTS = tuple(
    Path(relative_path.removeprefix("plugin/")) for relative_path in PACKAGED_WRAPPERS
)
PROMPT_EVENT_CANARY = b"prompt-canary-7f3a"
PROMPT_EVENT_INPUT = (
    b'{"session_id":"s","hook_event_name":"UserPromptSubmit","prompt":"'
    + PROMPT_EVENT_CANARY
    + b'"}'
)
SKILL_PATH = Path("skills/using-axiom/SKILL.md")
HEADING = (
    "You have Axiom. Load this startup front door before deciding whether any "
    "Axiom skill applies:"
)
CLAUDE_HEADING = (
    "You have Axiom in Claude Code. Load this startup front door before deciding "
    "whether any Axiom skill applies:"
)
UTF8_SENTINEL = "Runtime UTF-8 sentinel: caf\u00e9 \u0394\n".encode()
TIMEOUT_FIXTURE_SECONDS = 0.25


@dataclass(frozen=True)
class HookInvocation:
    """One exact declared command and the native shell that owns it."""

    name: str
    command: str
    shell: str
    plugin_root_variable: str
    heading_bytes: bytes


@dataclass(frozen=True)
class HookResult:
    returncode: int
    stdout: bytes
    stderr: bytes


class HookCommandTimedOut(TimeoutError):
    """Raised only after the timed-out command's process tree is terminated."""

    def __init__(self, stdout: bytes, stderr: bytes) -> None:
        super().__init__("hook command exceeded its bounded runtime")
        self.stdout = stdout
        self.stderr = stderr


def _load_handlers(path: Path) -> dict[str, dict[str, object]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    handlers: dict[str, dict[str, object]] = {}
    for event_name, groups in document["hooks"].items():
        handler = groups[0]["hooks"][0]
        if not isinstance(handler, dict) or handler.get("type") != "command":
            raise AssertionError(
                f"{path.relative_to(REPOSITORY_ROOT)} {event_name} has no command hook"
            )
        handlers[event_name] = handler
    return handlers


def _absolute_program(name: str, candidates: tuple[Path, ...] = ()) -> str:
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())
    resolved = shutil.which(name)
    if resolved is not None:
        return str(Path(resolved).resolve())
    raise RuntimeError(f"required host runtime {name!r} is unavailable")


def _bash_program() -> str:
    candidates: tuple[Path, ...] = ()
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        candidates = tuple(
            Path(root) / "Git" / "bin" / "bash.exe"
            for root in (program_files, program_files_x86)
            if root
        )
    return _absolute_program("bash", candidates)


def _cmd_program() -> str:
    comspec = os.environ.get("COMSPEC")
    system_root = os.environ.get("SystemRoot")
    candidates = tuple(
        candidate
        for candidate in (
            Path(comspec) if comspec else None,
            Path(system_root) / "System32" / "cmd.exe" if system_root else None,
        )
        if candidate is not None
    )
    return _absolute_program("cmd.exe", candidates)


def _bash_path(path: Path, bash: str) -> str:
    if os.name != "nt":
        return str(path)
    completed = subprocess.run(
        [bash, "--noprofile", "--norc", "-c", 'cygpath -u -- "$1"', "axiom", str(path)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=5,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Git Bash could not translate a Windows path: {detail}")
    return completed.stdout.decode("utf-8", errors="strict").strip()


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        system_root = os.environ.get("SystemRoot")
        taskkill = (
            Path(system_root) / "System32" / "taskkill.exe"
            if system_root
            else Path("taskkill.exe")
        )
        subprocess.run(
            [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
        if process.poll() is None:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _run_hook(
    invocation: HookInvocation,
    *,
    cwd: Path,
    environment: dict[str, str],
    timeout: float,
    stdin_bytes: bytes | None = None,
) -> HookResult:
    if invocation.shell == "cmd":
        cmd = _cmd_program()
        argv: str | list[str] = (
            f'{subprocess.list2cmdline([cmd])} /D /S /C "{invocation.command}"'
        )
    elif invocation.shell == "bash":
        argv = [_bash_program(), "--noprofile", "--norc", "-c", invocation.command]
    else:
        raise AssertionError(f"unsupported integration shell {invocation.shell!r}")

    popen_arguments: dict[str, object] = {}
    if os.name == "nt":
        popen_arguments["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        if invocation.shell == "cmd":
            popen_arguments["executable"] = cmd
    else:
        popen_arguments["start_new_session"] = True

    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL if stdin_bytes is None else subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_arguments,
    )
    try:
        stdout, stderr = process.communicate(input=stdin_bytes, timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        raise HookCommandTimedOut(stdout, stderr) from None
    return HookResult(process.returncode, stdout, stderr)


def _tool_version(label: str, argv: list[str]) -> str:
    completed = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=10,
    )
    output = completed.stdout.decode("utf-8", errors="replace").strip()
    if completed.returncode != 0 or not output:
        raise RuntimeError(f"could not report {label}: {output or 'no output'}")
    return output.splitlines()[0]


def report_environment() -> None:
    """Print the exact native runtime identities used by the workflow."""

    print(f"os.system={platform.system()}")
    print(f"os.release={platform.release()}")
    print(f"os.version={platform.version()}")
    print(f"os.machine={platform.machine()}")
    print(f"python={platform.python_version()} ({sys.executable})")
    print(f"node={_tool_version('Node.js', ['node', '--version'])}")
    print(f"git={_tool_version('Git', ['git', '--version'])}")
    bash = _bash_program()
    print(f"bash={_tool_version('Bash', [bash, '--noprofile', '--norc', '--version'])} ({bash})")
    if os.name == "nt":
        cmd = _cmd_program()
        print(f"cmd={_tool_version('cmd.exe', [cmd, '/D', '/C', 'ver'])} ({cmd})")


class HookRuntimeIntegrationTests(unittest.TestCase):
    """Execute every applicable checked-in lifecycle hook command natively."""

    @classmethod
    def setUpClass(cls) -> None:
        if not sys.dont_write_bytecode:
            raise AssertionError("hook runtime integration must run Python with -B")
        cls.codex_handlers = _load_handlers(CODEX_HOOK_PATH)
        cls.claude_handlers = _load_handlers(CLAUDE_HOOK_PATH)
        cls.codex_handler = cls.codex_handlers["SessionStart"]
        cls.claude_handler = cls.claude_handlers["SessionStart"]
        cls.bash = _bash_program()
        if os.name == "nt":
            _cmd_program()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="axiom hook runtime ")
        self.root = Path(self.temporary.name)
        self.plugin_root = self.root / "plugin root with spaces"
        self.workspace = self.root / "workspace path with spaces"
        self.home = self.root / "empty home with spaces"
        self.workspace.mkdir()
        self.home.mkdir()

        self.source_skill_bytes = (PLUGIN_SOURCE_ROOT / SKILL_PATH).read_bytes()
        self.source_wrapper_bytes = (PLUGIN_SOURCE_ROOT / WINDOWS_WRAPPER).read_bytes()
        self.source_script_bytes = {
            script: (PLUGIN_SOURCE_ROOT / script).read_bytes() for script in PACKAGED_SCRIPTS
        }
        self.skill_bytes = self.source_skill_bytes
        self.skill_path = self.plugin_root / SKILL_PATH
        self.skill_path.parent.mkdir(parents=True)
        self.skill_path.write_bytes(self.skill_bytes)
        self.wrapper_path = self.plugin_root / WINDOWS_WRAPPER
        self.wrapper_path.parent.mkdir(parents=True)
        for script, content in self.source_script_bytes.items():
            (self.plugin_root / script).write_bytes(content)

        profile_script = 'printf "%s\\n" profile-ran > "$HOME/profile-ran"; exit 71\n'
        for name in (".bash_profile", ".bashrc", ".profile"):
            (self.home / name).write_text(profile_script, encoding="utf-8")

    def tearDown(self) -> None:
        try:
            self.assertEqual(
                self.source_skill_bytes,
                (PLUGIN_SOURCE_ROOT / SKILL_PATH).read_bytes(),
            )
            self.assertEqual(
                self.source_wrapper_bytes,
                (PLUGIN_SOURCE_ROOT / WINDOWS_WRAPPER).read_bytes(),
            )
            for script, content in self.source_script_bytes.items():
                self.assertEqual(content, (PLUGIN_SOURCE_ROOT / script).read_bytes())
        finally:
            self.temporary.cleanup()

    def _invocations(self) -> tuple[HookInvocation, ...]:
        codex_command = self.codex_handler.get("command")
        claude_command = self.claude_handler.get("command")
        if not isinstance(codex_command, str) or not isinstance(claude_command, str):
            raise AssertionError("checked-in POSIX hook commands must be strings")
        claude = HookInvocation(
            "claude-windows-git-bash" if os.name == "nt" else "claude-posix",
            claude_command,
            "bash",
            "CLAUDE_PLUGIN_ROOT",
            (CLAUDE_HEADING + "\n\n").encode("utf-8"),
        )

        if os.name == "nt":
            windows_command = self.codex_handler.get("commandWindows")
            if not isinstance(windows_command, str):
                raise AssertionError("checked-in Codex Windows hook command must be a string")
            return (
                HookInvocation(
                    "codex-windows",
                    windows_command,
                    "cmd",
                    "PLUGIN_ROOT",
                    (HEADING + "\r\n\r\n").encode("utf-8"),
                ),
                claude,
            )
        return (
            HookInvocation(
                "codex-posix",
                codex_command,
                "bash",
                "PLUGIN_ROOT",
                (HEADING + "\n\n").encode("utf-8"),
            ),
            claude,
        )

    def _environment(self, invocation: HookInvocation) -> dict[str, str]:
        environment = os.environ.copy()
        for key in ("BASH_ENV", "CDPATH", "ENV", "PROMPT_COMMAND"):
            environment.pop(key, None)
        environment["HOME"] = str(self.home)
        plugin_root = (
            _bash_path(self.plugin_root, self.bash)
            if os.name == "nt" and invocation.shell == "bash"
            else str(self.plugin_root)
        )
        environment[invocation.plugin_root_variable] = plugin_root
        environment["AXIOM_TEST_PYTHON"] = sys.executable
        return environment

    def _run(
        self,
        invocation: HookInvocation,
        timeout: float = 5,
        stdin_bytes: bytes | None = None,
    ) -> HookResult:
        return _run_hook(
            invocation,
            cwd=self.workspace,
            environment=self._environment(invocation),
            timeout=timeout,
            stdin_bytes=stdin_bytes,
        )

    def _lifecycle_invocations(self, event_name: str) -> tuple[HookInvocation, ...]:
        """The exact checked-in commands for one lifecycle event on this host."""
        codex_handler = self.codex_handlers[event_name]
        claude_handler = self.claude_handlers[event_name]
        claude_command = claude_handler.get("command")
        if not isinstance(claude_command, str):
            raise AssertionError(f"checked-in Claude Code {event_name} command must be a string")
        claude = HookInvocation(
            f"claude-{event_name}", claude_command, "bash", "CLAUDE_PLUGIN_ROOT", b""
        )
        if os.name == "nt":
            windows_command = codex_handler.get("commandWindows")
            if not isinstance(windows_command, str):
                raise AssertionError(f"checked-in Codex Windows {event_name} command must be a string")
            return (
                HookInvocation(f"codex-windows-{event_name}", windows_command, "cmd", "PLUGIN_ROOT", b""),
                claude,
            )
        codex_command = codex_handler.get("command")
        if not isinstance(codex_command, str):
            raise AssertionError(f"checked-in Codex {event_name} command must be a string")
        return (
            HookInvocation(f"codex-posix-{event_name}", codex_command, "bash", "PLUGIN_ROOT", b""),
            claude,
        )

    def test_prompt_hooks_print_exactly_the_static_text(self) -> None:
        for invocation in self._lifecycle_invocations("UserPromptSubmit"):
            with self.subTest(hook=invocation.name):
                result = self._run(invocation)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(b"", result.stderr)
                lines = result.stdout.decode("utf-8", errors="strict").splitlines()
                self.assertEqual([PROMPT_TEXT], lines)
                self.assertFalse((self.home / "profile-ran").exists())
                self.assertEqual([], list(self.workspace.iterdir()))

    def test_prompt_hooks_ignore_the_host_event_on_standard_input(self) -> None:
        for invocation in self._lifecycle_invocations("UserPromptSubmit"):
            with self.subTest(hook=invocation.name):
                result = self._run(invocation, stdin_bytes=PROMPT_EVENT_INPUT)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(b"", result.stderr)
                self.assertNotIn(PROMPT_EVENT_CANARY, result.stdout)
                lines = result.stdout.decode("utf-8", errors="strict").splitlines()
                self.assertEqual([PROMPT_TEXT], lines)
                self.assertEqual([], list(self.workspace.iterdir()))

    def test_no_stop_event_is_declared_on_either_host(self) -> None:
        self.assertNotIn("Stop", self.codex_handlers)
        self.assertNotIn("Stop", self.claude_handlers)
        self.assertEqual({"SessionStart", "UserPromptSubmit"}, set(self.codex_handlers))
        self.assertEqual({"SessionStart", "UserPromptSubmit"}, set(self.claude_handlers))

    def test_exact_commands_expand_spaced_roots_and_preserve_skill_bytes(self) -> None:
        for invocation in self._invocations():
            with self.subTest(hook=invocation.name):
                result = self._run(invocation)
                expected = invocation.heading_bytes + self.skill_bytes
                self.assertEqual(0, result.returncode)
                self.assertEqual(expected, result.stdout)
                self.assertEqual(expected.decode("utf-8"), result.stdout.decode("utf-8"))
                self.assertEqual(b"", result.stderr)
                self.assertFalse((self.home / "profile-ran").exists())
                self.assertEqual([], list(self.workspace.iterdir()))

    def test_utf8_output_and_native_newlines_are_explicit(self) -> None:
        self.skill_path.write_bytes(UTF8_SENTINEL)
        for invocation in self._invocations():
            with self.subTest(hook=invocation.name):
                result = self._run(invocation)
                expected = invocation.heading_bytes + UTF8_SENTINEL
                self.assertEqual(0, result.returncode)
                self.assertEqual(expected, result.stdout)
                self.assertEqual(expected.decode("utf-8"), result.stdout.decode("utf-8"))
                self.assertEqual(b"", result.stderr)

    def test_missing_skill_is_nonzero_with_independent_stdout_and_stderr(self) -> None:
        self.skill_path.unlink()
        for invocation in self._invocations():
            with self.subTest(hook=invocation.name):
                result = self._run(invocation)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(invocation.heading_bytes, result.stdout)
                self.assertNotEqual(b"", result.stderr)
                result.stdout.decode("utf-8", errors="strict")
                result.stderr.decode("utf-8", errors="strict")

    @unittest.skipIf(os.name == "nt", "Windows does not enforce POSIX mode bits")
    def test_unreadable_skill_is_rejected_when_permissions_are_enforceable(self) -> None:
        original_mode = stat.S_IMODE(self.skill_path.stat().st_mode)
        self.skill_path.chmod(0)
        try:
            if os.access(self.skill_path, os.R_OK):
                self.skipTest("current host identity can read a mode-000 fixture")
            for invocation in self._invocations():
                with self.subTest(hook=invocation.name):
                    result = self._run(invocation)
                    self.assertNotEqual(0, result.returncode)
                    self.assertEqual(invocation.heading_bytes, result.stdout)
                    self.assertNotEqual(b"", result.stderr)
        finally:
            self.skill_path.chmod(original_mode)

    def test_runtime_enforces_a_bounded_timeout(self) -> None:
        if os.name == "nt":
            self.wrapper_path.write_bytes(
                b'@echo off\r\n"%AXIOM_TEST_PYTHON%" -c "import time; time.sleep(30)"\r\n'
            )
            invocations = (self._invocations()[0],)
        else:
            self.skill_path.unlink()
            os.mkfifo(self.skill_path)
            invocations = self._invocations()

        for invocation in invocations:
            with self.subTest(hook=invocation.name):
                started = time.monotonic()
                with self.assertRaises(HookCommandTimedOut):
                    self._run(invocation, timeout=TIMEOUT_FIXTURE_SECONDS)
                self.assertLess(time.monotonic() - started, 5)

    @unittest.skipUnless(os.name == "nt", "requires the native Windows command shell")
    def test_windows_wrapper_ignores_workspace_executable_canaries(self) -> None:
        """The checked-in cmd wrapper must not run same-named programs from the workspace."""
        marker = self.workspace / "workspace-program-ran"
        canary = b'@echo hijacked>"%~dp0workspace-program-ran"\r\n'
        for name in (
            "codex-session-start.cmd",
            "echo.cmd",
            "setlocal.cmd",
            "type.cmd",
            "powershell.cmd",
            "pwsh.cmd",
        ):
            (self.workspace / name).write_bytes(canary)
        for name in ("cmd.exe", "powershell.exe"):
            (self.workspace / name).write_bytes(b"not a Windows executable")

        invocation = self._invocations()[0]
        self.assertEqual("codex-windows", invocation.name)
        result = self._run(invocation)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8", errors="replace"))
        self.assertEqual(invocation.heading_bytes + self.skill_bytes, result.stdout)
        self.assertEqual(b"", result.stderr)
        self.assertFalse(marker.exists())


def main() -> int:
    if sys.argv[1:] == ["--report-environment"]:
        report_environment()
        return 0
    raise SystemExit(
        "usage: python -B .ci/check.py hook-runtime --report-environment"
    )


if __name__ == "__main__":
    raise SystemExit(main())
