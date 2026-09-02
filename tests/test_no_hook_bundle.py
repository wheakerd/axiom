"""Focused negative and deterministic tests for the no-Hook bundle builder."""

from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import axiom_validation.no_hook_bundle as bundle_module
from axiom_validation.no_hook_bundle import (
    BUNDLE_ENVELOPE_NAME,
    BUNDLE_MANIFEST_NAME,
    BundleContractError,
    GitEntry,
    GitObjectSource,
    _load_json_bytes,
    _validate_reference_closure,
    _validate_runtime_text,
    build_bundle,
    check_no_hook_bundle,
    inspect_source,
    validate_archive_bytes,
    validate_bundle_manifest,
    validate_derived_plugin_manifest,
    validate_envelope,
    validate_path_set,
    validate_portable_path,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GIT_COMMAND = shutil.which("git")
if GIT_COMMAND is None:
    raise RuntimeError("focused no-Hook bundle tests require Git")
GIT_EXECUTABLE = Path(GIT_COMMAND).resolve()
SOURCE_FILES = (
    ".codex-plugin/plugin.json",
    "evidence/runtime-identity.json",
    "evals/no-hook/profile-v1.json",
    "evals/no-hook/benchmark-v1.json",
    "evals/no-hook/golden-set-v1.jsonl",
    "evals/no-hook/host-response-schema-v1.json",
)


class SourceFixture:
    """Small self-contained Git source with the exact frozen runtime payload."""

    def __init__(self, parent: Path) -> None:
        self.root = parent / "source"
        self.root.mkdir()
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        for relative in SOURCE_FILES:
            source = REPOSITORY_ROOT / relative
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        source_identity_path = self.root / "evidence/runtime-identity.json"
        source_identity = json.loads(source_identity_path.read_text(encoding="utf-8"))
        source_identity["repositoryPolicyRevision"] = 5
        source_identity_path.write_text(
            json.dumps(source_identity, indent=2) + "\n", encoding="utf-8"
        )
        self.git("init", "--quiet")
        self.git("config", "user.name", "Axiom Test")
        self.git("config", "user.email", "axiom-test@example.invalid")
        self.commit("fixture")

    def git(
        self,
        *arguments: str,
        input_bytes: bytes | None = None,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [str(GIT_EXECUTABLE), "-C", str(self.root), *arguments],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            env=env,
        )

    def commit(self, message: str) -> None:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)

    @property
    def commit_oid(self) -> str:
        return self.git("rev-parse", "HEAD").stdout.decode("ascii").strip()

    @property
    def tree_oid(self) -> str:
        return self.git("rev-parse", "HEAD^{tree}").stdout.decode("ascii").strip()

    def destination(self, name: str) -> Path:
        path = self.root.parent / name
        path.mkdir()
        return path


def _build(fixture: SourceFixture, destination: Path):
    return build_bundle(
        fixture.root,
        fixture.commit_oid,
        fixture.tree_oid,
        destination,
        git_executable=GIT_EXECUTABLE,
        schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
        entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
        module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
    )


def _directory_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _rebind_manifest(document: dict[str, object]) -> None:
    digest_input = dict(document)
    digest_input.pop("bundleManifestDigest", None)
    payload = json.dumps(
        digest_input,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    document["bundleManifestDigest"] = "sha256:" + hashlib.sha256(payload).hexdigest()


def _marker_command(parent: Path, name: str, marker: Path) -> Path:
    if os.name == "nt":
        command = parent / f"{name}.cmd"
        command.write_text(f'@echo executed>"{marker}"\n', encoding="utf-8")
    else:
        command = parent / name
        command.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('executed\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        command.chmod(0o755)
    return command


def _object_database_inventory(root: Path) -> dict[str, tuple[int, int, str]]:
    objects = root / ".git/objects"
    inventory: dict[str, tuple[int, int, str]] = {}
    for path in sorted(objects.rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        inventory[path.relative_to(objects).as_posix()] = (
            stat.S_IMODE(path.stat().st_mode),
            len(data),
            hashlib.sha256(data).hexdigest(),
        )
    return inventory


def _changed_stat(metadata: os.stat_result, **changes: int) -> mock.Mock:
    result = mock.Mock(wraps=metadata)
    for name, value in changes.items():
        setattr(result, name, value)
    return result


class TrackingPipe:
    """A finite fake pipe that rejects unbounded reads and records consumption."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0
        self.bytes_read = 0
        self.maximum_request = 0
        self.closed = False

    def read(self, length: int = -1) -> bytes:
        if length < 0:
            raise AssertionError("production code attempted an unbounded pipe read")
        self.maximum_request = max(self.maximum_request, length)
        end = min(len(self._data), self._offset + length)
        result = self._data[self._offset:end]
        self._offset = end
        self.bytes_read += len(result)
        return result

    def close(self) -> None:
        self.closed = True


class ScriptedProcess:
    """Minimal Popen-compatible process for bounded-reader regressions."""

    def __init__(
        self,
        stdout: bytes,
        *,
        stderr: bytes = b"",
        returncode: int = 0,
    ) -> None:
        self.stdout = TrackingPipe(stdout)
        self.stderr = TrackingPipe(stderr)
        self.stdin = io.BytesIO()
        self._planned_returncode = returncode
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False
        self.wait_count = 0

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -15

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: int | None = None) -> int:
        del timeout
        self.wait_count += 1
        if self.returncode is None:
            self.returncode = self._planned_returncode
        return self.returncode


class NoHookBundleTests(unittest.TestCase):
    def test_checked_in_static_evidence_reproduces_without_output(self):
        failures: list[str] = []
        self.assertEqual((50, 2), check_no_hook_bundle(failures))
        self.assertEqual([], failures)

    def test_two_independent_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            first_destination = fixture.destination("first")
            second_destination = fixture.destination("second")
            source_status_before = fixture.git(
                "status", "--porcelain=v1", "--untracked-files=all"
            ).stdout

            first = _build(fixture, first_destination)
            second = _build(fixture, second_destination)

            self.assertEqual(first.summary(), second.summary())
            self.assertEqual(
                _directory_files(first_destination / "plugin"),
                _directory_files(second_destination / "plugin"),
            )
            first_zip = first_destination / first.archive_filename
            second_zip = second_destination / second.archive_filename
            self.assertEqual(first_zip.read_bytes(), second_zip.read_bytes())
            self.assertEqual(
                (first_destination / BUNDLE_ENVELOPE_NAME).read_bytes(),
                (second_destination / BUNDLE_ENVELOPE_NAME).read_bytes(),
            )
            self.assertEqual(
                source_status_before,
                fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
            )
            self.assertEqual(52, first.directory_file_count)
            self.assertNotEqual(
                "sha256:17dacf7d5d73b714e0762586683f855ee48ad087769f0a20d5453dba38a38ea3",
                first.profile_runtime_digest,
            )

            expected_manifest = (
                b'{\n'
                b'  "name": "axiom",\n'
                b'  "version": "0.10.0",\n'
                b'  "description": "Think before AI thinks.",\n'
                b'  "skills": "./skills/"\n'
                b'}\n'
            )
            self.assertEqual(
                expected_manifest,
                (first_destination / "plugin/.codex-plugin/plugin.json").read_bytes(),
            )
            with zipfile.ZipFile(first_zip) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names, key=lambda item: item.encode("utf-8")))
                self.assertFalse(any(name.startswith("plugin/") for name in names))
                self.assertNotIn(BUNDLE_ENVELOPE_NAME, names)
                self.assertFalse(any(name.endswith("/") for name in names))
                self.assertEqual(expected_manifest, archive.read(".codex-plugin/plugin.json"))

    def test_destination_must_be_existing_empty_external_and_not_symlinked(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            absent = Path(directory) / "absent"
            with self.assertRaisesRegex(BundleContractError, "cannot inspect destination"):
                _build(fixture, absent)

            nonempty = fixture.destination("nonempty")
            (nonempty / "owned-by-caller.txt").write_text("keep\n", encoding="utf-8")
            with self.assertRaisesRegex(BundleContractError, "destination must be empty"):
                _build(fixture, nonempty)

            inside = fixture.root / "output"
            inside.mkdir()
            with self.assertRaisesRegex(BundleContractError, "outside the source repository"):
                _build(fixture, inside)

            real_parent = Path(directory) / "real-parent"
            real_parent.mkdir()
            (real_parent / "output").mkdir()
            linked_parent = Path(directory) / "linked-parent"
            try:
                linked_parent.symlink_to(real_parent, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"directory symlink unavailable: {error}")
            with self.assertRaisesRegex(BundleContractError, "must not be a symbolic link"):
                _build(fixture, linked_parent / "output")

    def test_runtime_path_policy_rejects_unsafe_names_and_collisions(self):
        invalid = (
            "../escape.md",
            "/absolute.md",
            "skills\\backslash.md",
            "skills/control\x01.md",
            "skills/CON.md",
            "skills/trailing. ",
            "skills/colon:name.md",
            "skills/e\u0301.md",
        )
        for path in invalid:
            with self.subTest(path=repr(path)), self.assertRaises(BundleContractError):
                validate_portable_path(path)
        for paths in (
            ("skills/a.md", "skills/a.md"),
            ("skills/A.md", "skills/a.md"),
        ):
            with self.subTest(paths=paths), self.assertRaises(BundleContractError):
                validate_path_set(tuple(sorted(paths, key=lambda item: item.encode("utf-8"))))

    def test_runtime_text_policy_rejects_encoding_and_newline_drift(self):
        mutations = {
            "bom": b"\xef\xbb\xbftext\n",
            "nul": b"text\x00\n",
            "crlf": b"text\r\n",
            "non-utf8": b"\xff\n",
            "missing-final-lf": b"text",
        }
        for name, data in mutations.items():
            with self.subTest(name=name), self.assertRaises(BundleContractError):
                _validate_runtime_text(data, "skills/example/SKILL.md")

    def test_missing_reference_resource_is_rejected(self):
        entries = (
            GitEntry(
                "skills/example/SKILL.md",
                "100644",
                "blob",
                "0" * 40,
                47,
                b"# Example\n\nRead `references/missing.md`.\n",
            ),
            GitEntry(
                "skills/example/agents/openai.yaml",
                "100644",
                "blob",
                "0" * 40,
                15,
                b"name: example\n",
            ),
        )
        with self.assertRaisesRegex(BundleContractError, "referenced resource"):
            _validate_reference_closure(entries, ("example",))

    def test_source_symlink_submodule_and_executable_modes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)

            link_blob = fixture.git("hash-object", "-w", "--stdin", input_bytes=b"SKILL.md").stdout.decode("ascii").strip()
            fixture.git(
                "update-index",
                "--add",
                "--cacheinfo",
                f"120000,{link_blob},skills/using-axiom/bad-link",
            )
            fixture.git("commit", "--quiet", "-m", "symlink tree")
            with self.assertRaises(BundleContractError):
                source.list_files(fixture.commit_oid, "skills")

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.git(
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{fixture.commit_oid},skills/using-axiom/submodule",
            )
            fixture.git("commit", "--quiet", "-m", "submodule tree")
            with self.assertRaises(BundleContractError):
                GitObjectSource(fixture.root, GIT_EXECUTABLE).list_files(
                    fixture.commit_oid, "skills"
                )

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.git("update-index", "--chmod=+x", "skills/using-axiom/SKILL.md")
            fixture.git("commit", "--quiet", "-m", "executable tree")
            with self.assertRaisesRegex(BundleContractError, "100644 blob"):
                GitObjectSource(fixture.root, GIT_EXECUTABLE).list_files(
                    fixture.commit_oid, "skills"
                )

    def test_fsmonitor_is_not_executed_and_python_snapshot_rejects_runtime_drift(self):
        for mutation in ("clean", "dirty", "untracked", "ignored"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                fixture = SourceFixture(parent)
                marker = parent / "fsmonitor-executed.txt"
                command = _marker_command(parent, "fsmonitor-marker", marker)
                fixture.git("config", "core.fsmonitor", str(command))

                if mutation == "dirty":
                    skill = fixture.root / "skills/using-axiom/SKILL.md"
                    skill.write_bytes(skill.read_bytes() + b"dirty\n")
                elif mutation == "untracked":
                    (fixture.root / "skills/using-axiom/untracked.md").write_text(
                        "untracked\n", encoding="utf-8"
                    )
                elif mutation == "ignored":
                    exclude = fixture.root / ".git/info/exclude"
                    exclude.write_text(
                        exclude.read_text(encoding="utf-8")
                        + "skills/using-axiom/ignored.md\n",
                        encoding="utf-8",
                    )
                    (fixture.root / "skills/using-axiom/ignored.md").write_text(
                        "ignored\n", encoding="utf-8"
                    )

                destination = fixture.destination("output")
                if mutation == "clean":
                    self.assertEqual(52, _build(fixture, destination).directory_file_count)
                else:
                    with self.assertRaisesRegex(
                        BundleContractError,
                        "dirty, untracked, or ignored",
                    ):
                        _build(fixture, destination)
                self.assertFalse(marker.exists())

    def test_explicit_git_executable_ignores_path_shadowing(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            fixture = SourceFixture(parent)
            shadow = parent / "shadow"
            shadow.mkdir()
            marker = parent / "fake-git-executed.txt"
            _marker_command(shadow, "git", marker)
            environment_path = str(shadow) + os.pathsep + os.environ.get("PATH", "")
            with mock.patch.dict(os.environ, {"PATH": environment_path}):
                result = _build(fixture, fixture.destination("output"))
            self.assertEqual(52, result.directory_file_count)
            self.assertFalse(marker.exists())
            with self.assertRaisesRegex(BundleContractError, "explicit absolute path"):
                GitObjectSource(fixture.root, Path("git"))

    def test_git_requires_no_lazy_fetch_capability_before_object_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            unsupported = ScriptedProcess(
                b"",
                stderr=b"unknown option: --no-lazy-fetch\n",
                returncode=129,
            )
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                return_value=unsupported,
            ) as invoked:
                with self.assertRaisesRegex(
                    BundleContractError,
                    "lacks required --no-lazy-fetch capability",
                ):
                    GitObjectSource(fixture.root, GIT_EXECUTABLE)
            invoked.assert_called_once()
            command = invoked.call_args.args[0]
            self.assertIn("--no-lazy-fetch", command)
            self.assertEqual("--version", command[-1])
            self.assertEqual(1, unsupported.wait_count)

    def test_each_git_invocation_requires_both_no_lazy_fetch_defenses(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            source.git_global_options = tuple(
                option
                for option in source.git_global_options
                if option != "--no-lazy-fetch"
            )
            with mock.patch.object(bundle_module.subprocess, "Popen") as invoked:
                with self.assertRaisesRegex(
                    BundleContractError,
                    "every Git invocation requires --no-lazy-fetch",
                ):
                    source.run(("rev-parse", "HEAD"))
            invoked.assert_not_called()

            source.git_global_options = bundle_module.REQUIRED_GIT_GLOBAL_OPTIONS
            source.environment.pop("GIT_NO_LAZY_FETCH")
            with mock.patch.object(bundle_module.subprocess, "Popen") as invoked:
                with self.assertRaisesRegex(
                    BundleContractError,
                    "every Git invocation requires --no-lazy-fetch",
                ):
                    source.run(("rev-parse", "HEAD"))
            invoked.assert_not_called()

    def test_partial_promisor_missing_blob_never_runs_remote_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            fixture = SourceFixture(parent)
            relative = "skills/using-axiom/SKILL.md"
            blob_oid = fixture.git("rev-parse", f"HEAD:{relative}").stdout.decode(
                "ascii"
            ).strip()
            object_path = fixture.root / ".git/objects" / blob_oid[:2] / blob_oid[2:]
            self.assertTrue(object_path.is_file())

            fixture.git("config", "core.repositoryformatversion", "1")
            fixture.git("config", "extensions.partialClone", "origin")
            fixture.git("config", "remote.origin.promisor", "true")
            fixture.git("config", "remote.origin.partialclonefilter", "blob:none")
            fixture.git("config", "remote.origin.url", "marker::missing")
            fixture.git("config", "protocol.marker.allow", "always")
            helper_directory = parent / "helpers"
            helper_directory.mkdir()
            marker = parent / "promisor-helper-executed.txt"
            _marker_command(helper_directory, "git-remote-marker", marker)
            environment = dict(os.environ)
            environment["PATH"] = (
                str(helper_directory)
                + os.pathsep
                + environment.get("PATH", "")
            )

            object_path.unlink()
            object_inventory = _object_database_inventory(fixture.root)
            source_files = _directory_files(fixture.root / "skills")

            control = fixture.git(
                "cat-file",
                "blob",
                blob_oid,
                check=False,
                env=environment,
            )
            self.assertNotEqual(0, control.returncode)
            self.assertTrue(marker.is_file(), "fixture must prove the helper is observable")
            marker.unlink()
            self.assertEqual(object_inventory, _object_database_inventory(fixture.root))

            destination = fixture.destination("output")
            with mock.patch.dict(os.environ, {"PATH": environment["PATH"]}):
                with self.assertRaisesRegex(
                    BundleContractError,
                    "unavailable while lazy fetching is disabled",
                ):
                    _build(fixture, destination)

            self.assertFalse(marker.exists())
            self.assertFalse(object_path.exists())
            self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
            self.assertEqual(source_files, _directory_files(fixture.root / "skills"))
            self.assertEqual([], list(destination.iterdir()))
            self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())

    def test_committed_runtime_blob_limits_are_enforced_before_blob_reads(self):
        for mutation in ("oversized", "sparse"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                target = fixture.root / "skills/using-axiom/SKILL.md"
                if mutation == "oversized":
                    target.write_bytes(b"x" * (bundle_module.MAX_RUNTIME_FILE_BYTES + 1))
                else:
                    with target.open("r+b") as handle:
                        handle.truncate(bundle_module.MAX_RUNTIME_FILE_BYTES + 1)
                fixture.commit(f"{mutation} committed blob")
                object_inventory = _object_database_inventory(fixture.root)
                source_status = fixture.git(
                    "status", "--porcelain=v1", "--untracked-files=all"
                ).stdout
                source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
                with mock.patch.object(source, "_read_blob", wraps=source._read_blob) as read_blob:
                    with self.assertRaisesRegex(BundleContractError, "pre-read limit"):
                        source.list_files(fixture.commit_oid, "skills")
                read_blob.assert_not_called()

                destination = fixture.destination("output")
                with self.assertRaisesRegex(BundleContractError, "pre-read limit"):
                    _build(fixture, destination)
                self.assertEqual([], list(destination.iterdir()))
                self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
                self.assertEqual(
                    source_status,
                    fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
                )

    def test_committed_runtime_tree_count_total_and_path_limits_precede_blob_reads(self):
        for mutation in ("count", "total", "path"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                if mutation == "count":
                    current_count = sum(
                        1 for path in (fixture.root / "skills").rglob("*") if path.is_file()
                    )
                    for index in range(
                        bundle_module.MAX_RUNTIME_FILES - current_count + 1
                    ):
                        (fixture.root / f"skills/using-axiom/count-{index:03d}.md").write_bytes(
                            b"x\n"
                        )
                    diagnostic = "file count exceeds"
                elif mutation == "total":
                    runtime_paths = sorted(
                        path for path in (fixture.root / "skills").rglob("*") if path.is_file()
                    )
                    for path in runtime_paths[:8]:
                        path.write_bytes(
                            b"x" * (bundle_module.MAX_RUNTIME_FILE_BYTES - 1) + b"\n"
                        )
                    diagnostic = "cumulative pre-read limit"
                else:
                    long_name = "p" * 220 + ".md"
                    (fixture.root / "skills/using-axiom" / long_name).write_bytes(b"x\n")
                    diagnostic = "240-byte path limit"
                fixture.commit(f"{mutation} runtime tree")
                object_inventory = _object_database_inventory(fixture.root)
                source_status = fixture.git(
                    "status", "--porcelain=v1", "--untracked-files=all"
                ).stdout
                source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
                with mock.patch.object(source, "_read_blob", wraps=source._read_blob) as read_blob:
                    with self.assertRaisesRegex(BundleContractError, diagnostic):
                        source.list_files(fixture.commit_oid, "skills")
                read_blob.assert_not_called()

                destination = fixture.destination("output")
                build_diagnostic = (
                    "frozen inventory" if mutation == "total" else diagnostic
                )
                with self.assertRaisesRegex(BundleContractError, build_diagnostic):
                    _build(fixture, destination)
                self.assertEqual([], list(destination.iterdir()))
                self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
                self.assertEqual(
                    source_status,
                    fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
                )

    def test_source_json_limits_are_enforced_before_oversized_blob_reads(self):
        for relative in (
            "evals/no-hook/profile-v1.json",
            ".codex-plugin/plugin.json",
            "evidence/runtime-identity.json",
        ):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                target = fixture.root / relative
                target.write_bytes(
                    b'{"padding":"'
                    + b"x" * bundle_module.MAX_BUNDLE_MANIFEST_BYTES
                    + b'"}\n'
                )
                fixture.commit("oversized source JSON")
                object_inventory = _object_database_inventory(fixture.root)
                source_status = fixture.git(
                    "status", "--porcelain=v1", "--untracked-files=all"
                ).stdout
                destination = fixture.destination("output")
                with self.assertRaisesRegex(BundleContractError, "pre-read limit"):
                    _build(fixture, destination)
                self.assertEqual([], list(destination.iterdir()))
                self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
                self.assertEqual(
                    source_status,
                    fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
                )

    def test_streamed_ls_tree_rejects_truncation_and_bounds_partial_records(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            commit_oid = fixture.commit_oid
            oid = "a" * 40
            truncated = ScriptedProcess(
                f"100644 blob {oid} 1\tskills/example.md".encode("ascii")
            )
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                return_value=truncated,
            ):
                with self.assertRaisesRegex(BundleContractError, "NUL record terminator"):
                    source.list_files(
                        commit_oid,
                        "skills",
                        maximum_files=1,
                        maximum_file_bytes=1,
                        maximum_total_bytes=1,
                    )
            self.assertTrue(truncated.terminated)
            self.assertEqual(1, truncated.wait_count)

            partial = ScriptedProcess(
                f"100644 blob {oid} 1\t".encode("ascii")
                + b"p" * (bundle_module.MAX_GIT_LS_TREE_RECORD_BYTES + 100)
            )
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                return_value=partial,
            ):
                with self.assertRaisesRegex(BundleContractError, "partial record"):
                    source.list_files(
                        commit_oid,
                        "skills",
                        maximum_files=1,
                        maximum_file_bytes=1,
                        maximum_total_bytes=1,
                    )
            self.assertEqual(
                bundle_module.MAX_GIT_LS_TREE_RECORD_BYTES + 1,
                partial.stdout.bytes_read,
            )
            self.assertEqual(1, partial.stdout.maximum_request)
            self.assertTrue(partial.terminated)
            self.assertEqual(1, partial.wait_count)

    def test_declared_blob_size_bounds_actual_pipe_consumption_and_reaps_process(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            commit_oid = fixture.commit_oid
            oid = "b" * 40
            tree = ScriptedProcess(
                f"100644 blob {oid} 1\tskills/example.md\0".encode("ascii")
            )
            blob = ScriptedProcess(b"x" * (bundle_module.MAX_RUNTIME_FILE_BYTES + 1))
            object_inventory = _object_database_inventory(fixture.root)
            source_status = fixture.git(
                "status", "--porcelain=v1", "--untracked-files=all"
            ).stdout
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                side_effect=(tree, blob),
            ) as invoked:
                with self.assertRaisesRegex(BundleContractError, "tree-declared size"):
                    source.list_files(
                        commit_oid,
                        "skills",
                        maximum_files=1,
                        maximum_file_bytes=bundle_module.MAX_RUNTIME_FILE_BYTES,
                        maximum_total_bytes=bundle_module.MAX_RUNTIME_BYTES,
                    )
            self.assertEqual(2, len(invoked.call_args_list))
            self.assertEqual(2, blob.stdout.bytes_read)
            self.assertEqual(1, blob.stdout.maximum_request)
            self.assertTrue(blob.terminated)
            self.assertEqual(1, blob.wait_count)
            self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
            self.assertEqual(
                source_status,
                fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
            )

            maximum = bundle_module.MAX_RUNTIME_FILE_BYTES
            maximum_tree = ScriptedProcess(
                f"100644 blob {oid} {maximum}\tskills/example.md\0".encode("ascii")
            )
            maximum_blob = ScriptedProcess(b"x" * (maximum + 4096))
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                side_effect=(maximum_tree, maximum_blob),
            ):
                with self.assertRaisesRegex(BundleContractError, "tree-declared size"):
                    source.list_files(
                        commit_oid,
                        "skills",
                        maximum_files=1,
                        maximum_file_bytes=maximum,
                        maximum_total_bytes=maximum,
                    )
            self.assertEqual(maximum + 1, maximum_blob.stdout.bytes_read)
            self.assertLessEqual(
                maximum_blob.stdout.maximum_request,
                bundle_module.GIT_PIPE_CHUNK_BYTES,
            )
            self.assertTrue(maximum_blob.terminated)
            self.assertEqual(1, maximum_blob.wait_count)

    def test_oversized_first_tree_record_stops_before_later_objects(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            commit_oid = fixture.commit_oid
            oid = "c" * 40
            first = (
                f"100644 blob {oid} {bundle_module.MAX_RUNTIME_FILE_BYTES + 1}"
                "\tskills/first.md\0"
            ).encode("ascii")
            second = f"100644 blob {oid} 1\tskills/second.md\0".encode("ascii")
            tree = ScriptedProcess(first + second)
            with mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                return_value=tree,
            ) as invoked:
                with self.assertRaisesRegex(BundleContractError, "pre-read limit"):
                    source.list_files(
                        commit_oid,
                        "skills",
                        maximum_files=2,
                        maximum_file_bytes=bundle_module.MAX_RUNTIME_FILE_BYTES,
                        maximum_total_bytes=bundle_module.MAX_RUNTIME_BYTES,
                    )
            self.assertEqual(1, len(invoked.call_args_list))
            self.assertEqual(len(first), tree.stdout.bytes_read)
            self.assertLess(tree.stdout.bytes_read, len(first + second))
            self.assertTrue(tree.terminated)
            self.assertEqual(1, tree.wait_count)

    def test_snapshot_rejects_oversized_sparse_and_same_size_drift_before_output(self):
        for mutation in ("oversized", "sparse", "same-size"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                target = fixture.root / "skills/using-axiom/SKILL.md"
                original = target.read_bytes()
                if mutation == "oversized":
                    target.write_bytes(b"x" * (bundle_module.MAX_RUNTIME_FILE_BYTES + 1))
                elif mutation == "sparse":
                    with target.open("r+b") as handle:
                        handle.truncate(bundle_module.MAX_RUNTIME_FILE_BYTES + 1)
                else:
                    changed = bytearray(original)
                    changed[0] = ord("X") if changed[0] != ord("X") else ord("Y")
                    target.write_bytes(changed)

                destination = fixture.destination("output")
                diagnostic = "per-file safety limit" if mutation != "same-size" else "bytes drifted"
                with self.assertRaisesRegex(BundleContractError, diagnostic):
                    _build(fixture, destination)
                self.assertEqual([], list(destination.iterdir()))

    def test_snapshot_file_rejects_growth_after_open(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            entries = source.list_files(fixture.commit_oid, "skills")
            entry = next(item for item in entries if item.path == "skills/using-axiom/SKILL.md")
            target = fixture.root / entry.path
            metadata = target.lstat()
            original_read = os.read
            grew = False

            def read_then_grow(descriptor: int, length: int) -> bytes:
                nonlocal grew
                data = original_read(descriptor, length)
                if data and not grew:
                    with target.open("ab") as handle:
                        handle.write(b"growth\n")
                    grew = True
                return data

            with mock.patch.object(bundle_module.os, "read", side_effect=read_then_grow):
                with self.assertRaisesRegex(
                    BundleContractError,
                    "changed size or did not end at the expected EOF",
                ):
                    source._read_snapshot_file(
                        target,
                        metadata,
                        entry.path,
                        entry.size,
                        entry.data,
                    )

    def test_snapshot_file_rechecks_identity_and_size_after_read(self):
        for mutation in ("identity", "size"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
                entries = source.list_files(fixture.commit_oid, "skills")
                entry = next(
                    item for item in entries if item.path == "skills/using-axiom/SKILL.md"
                )
                target = fixture.root / entry.path
                metadata = target.lstat()
                original_fstat = os.fstat
                calls = 0

                def changed_after_read(descriptor: int):
                    nonlocal calls
                    calls += 1
                    current = original_fstat(descriptor)
                    if calls == 1:
                        return current
                    if mutation == "identity":
                        return _changed_stat(current, st_ino=current.st_ino + 1)
                    return _changed_stat(current, st_size=current.st_size + 1)

                with mock.patch.object(
                    bundle_module.os,
                    "fstat",
                    side_effect=changed_after_read,
                ):
                    with self.assertRaises(BundleContractError):
                        source._read_snapshot_file(
                            target,
                            metadata,
                            entry.path,
                            entry.size,
                            entry.data,
                        )

    def test_snapshot_streaming_stops_at_first_unknown_child(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            source = GitObjectSource(fixture.root, GIT_EXECUTABLE)
            entries = source.list_files(fixture.commit_oid, "skills")
            target_directory = fixture.root / "skills/using-axiom"
            for index in range(300):
                (target_directory / f"unexpected-{index:03d}.txt").write_text(
                    "unexpected\n",
                    encoding="utf-8",
                )
            destination = fixture.destination("output")
            real_scandir = os.scandir
            observed = 0

            class CountingScandir:
                def __init__(self, path: os.PathLike[str] | str) -> None:
                    self.iterator = real_scandir(path)

                def __enter__(self):
                    return self

                def __exit__(self, *unused: object) -> None:
                    self.iterator.close()

                def __iter__(self):
                    return self

                def __next__(self):
                    nonlocal observed
                    observed += 1
                    return next(self.iterator)

            def bounded_scandir(path: os.PathLike[str] | str):
                if Path(path) == target_directory:
                    return CountingScandir(path)
                return real_scandir(path)

            with mock.patch.object(bundle_module.os, "scandir", side_effect=bounded_scandir):
                with self.assertRaisesRegex(BundleContractError, "entry set drifted"):
                    _build(fixture, destination)
            self.assertLess(observed, 300)
            self.assertEqual([], list(destination.iterdir()))

    def test_snapshot_observed_entry_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "source"
            skills = root / "skills"
            skills.mkdir(parents=True)
            expected: list[GitEntry] = []
            for index in range(bundle_module.MAX_RUNTIME_FILES):
                relative = f"skills/file-{index:03d}.txt"
                (root / relative).write_bytes(b"x")
                expected.append(GitEntry(relative, "100644", "blob", "0" * 40, 1, b"x"))
            overflow = skills / "overflow.txt"
            overflow.write_bytes(b"x")
            source = object.__new__(GitObjectSource)
            source.repository = root
            real_scandir = os.scandir
            ordered = list(real_scandir(skills))
            ordered.sort(key=lambda child: (child.name == overflow.name, child.name))

            class OrderedScandir:
                def __init__(self) -> None:
                    self.iterator = iter(ordered)

                def __enter__(self):
                    return self

                def __exit__(self, *unused: object) -> None:
                    return None

                def __iter__(self):
                    return self

                def __next__(self):
                    return next(self.iterator)

            with mock.patch.object(bundle_module.os, "scandir", return_value=OrderedScandir()):
                with self.assertRaisesRegex(
                    BundleContractError,
                    "observed entry count exceeds",
                ):
                    source.runtime_snapshot(tuple(expected))

    def test_source_commit_tree_object_and_environment_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            output = fixture.destination("wrong-tree")
            with self.assertRaisesRegex(BundleContractError, "source tree mismatch"):
                build_bundle(
                    fixture.root,
                    fixture.commit_oid,
                    "0" * 40,
                    output,
                    git_executable=GIT_EXECUTABLE,
                    schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                    entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                    module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                )
            with self.assertRaisesRegex(BundleContractError, "source commit must be"):
                build_bundle(
                    fixture.root,
                    "HEAD",
                    fixture.tree_oid,
                    fixture.destination("short-ref"),
                    git_executable=GIT_EXECUTABLE,
                )
            with mock.patch.dict(os.environ, {"GIT_DIR": str(fixture.root / ".git")}):
                with self.assertRaisesRegex(BundleContractError, "dangerous ambient Git"):
                    GitObjectSource(fixture.root, GIT_EXECUTABLE)

    def test_replace_refs_and_object_alternates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.git(
                "update-ref",
                f"refs/replace/{fixture.commit_oid}",
                fixture.commit_oid,
            )
            with self.assertRaisesRegex(BundleContractError, "replace refs"):
                GitObjectSource(fixture.root, GIT_EXECUTABLE)

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            alternates = fixture.root / ".git/objects/info/alternates"
            alternates.parent.mkdir(parents=True, exist_ok=True)
            alternates.write_text(str(fixture.root / ".git/objects") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(BundleContractError, "object alternates"):
                GitObjectSource(fixture.root, GIT_EXECUTABLE)

    def test_stale_contract_and_host_case_set_bindings_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            profile = fixture.root / "evals/no-hook/profile-v1.json"
            document = json.loads(profile.read_text(encoding="utf-8"))
            document["status"] = "drifted"
            profile.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            fixture.commit("stale profile")
            with self.assertRaisesRegex(BundleContractError, "stale profileContract"):
                _build(fixture, fixture.destination("output"))

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            benchmark_path = fixture.root / "evals/no-hook/benchmark-v1.json"
            benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
            benchmark["hostCaseSets"][0]["sha256"] = "0" * 64
            benchmark_path.write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")
            fixture.commit("stale host set")
            schema_path = Path(directory) / "schema.json"
            schema = json.loads(
                (REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json").read_text(
                    encoding="utf-8"
                )
            )
            schema["x-axiom-contract"]["contractBindings"]["benchmark"]["sha256"] = __import__(
                "hashlib"
            ).sha256(benchmark_path.read_bytes()).hexdigest()
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(BundleContractError, "stale hostCaseSet"):
                build_bundle(
                    fixture.root,
                    fixture.commit_oid,
                    fixture.tree_oid,
                    fixture.destination("output"),
                    git_executable=GIT_EXECUTABLE,
                    schema_path=schema_path,
                    entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                    module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                )

    def test_source_change_after_inspection_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            inputs = inspect_source(
                fixture.root,
                fixture.commit_oid,
                fixture.tree_oid,
                git_executable=GIT_EXECUTABLE,
                schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
            )
            skill = fixture.root / "skills/using-axiom/SKILL.md"
            skill.write_bytes(skill.read_bytes() + b"changed\n")
            with self.assertRaisesRegex(
                BundleContractError,
                "skills/using-axiom/SKILL.md size drifted",
            ):
                inputs.verify_source_unchanged()

    def test_physical_mode_policy_is_posix_exact_and_windows_logical(self):
        file_metadata = mock.Mock(st_mode=stat.S_IFREG | 0o600)
        directory_metadata = mock.Mock(st_mode=stat.S_IFDIR | 0o700)

        with self.assertRaisesRegex(BundleContractError, "mode must be 0644"):
            bundle_module._validate_physical_mode(
                file_metadata,
                0o644,
                "generated file",
                platform_name="posix",
            )
        with self.assertRaisesRegex(BundleContractError, "mode must be 0755"):
            bundle_module._validate_physical_mode(
                directory_metadata,
                0o755,
                "generated directory",
                platform_name="posix",
            )

        bundle_module._validate_physical_mode(
            file_metadata,
            0o644,
            "generated file",
            platform_name="nt",
        )
        bundle_module._validate_physical_mode(
            directory_metadata,
            0o755,
            "generated directory",
            platform_name="nt",
        )
        with mock.patch.object(bundle_module.os, "chmod") as chmod:
            bundle_module._set_posix_mode(
                Path("unused"), 0o644, platform_name="nt"
            )
            chmod.assert_not_called()
            bundle_module._set_posix_mode(
                Path("unused"), 0o644, platform_name="posix"
            )
            chmod.assert_called_once_with(Path("unused"), 0o644)

        reparse_metadata = mock.Mock(st_file_attributes=0x0400)
        self.assertTrue(bundle_module._is_reparse_point(reparse_metadata))

    def test_derived_manifest_forbids_full_profile_and_unknown_fields(self):
        valid = {
            "name": "axiom",
            "version": "0.10.0",
            "description": "Think before AI thinks.",
            "skills": "./skills/",
        }
        self.assertEqual(valid, validate_derived_plugin_manifest(valid))
        for field in ("hooks", "apps", "mcpServers", "interface", "assets", "unknown"):
            with self.subTest(field=field):
                mutated = dict(valid)
                mutated[field] = "forbidden"
                with self.assertRaises(BundleContractError):
                    validate_derived_plugin_manifest(mutated)

    def test_manifest_self_reference_full_digest_and_envelope_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("output")
            result = _build(fixture, destination)
            manifest = result.bundle_manifest

            mutated = copy.deepcopy(manifest)
            mutated["bundleManifestDigest"] = "sha256:" + "0" * 64
            with self.assertRaisesRegex(BundleContractError, "self-reference"):
                validate_bundle_manifest(mutated)

            mutated = copy.deepcopy(manifest)
            full_digest = "sha256:17dacf7d5d73b714e0762586683f855ee48ad087769f0a20d5453dba38a38ea3"
            mutated["profileRuntimeDigest"] = full_digest
            with self.assertRaisesRegex(BundleContractError, "must not reuse"):
                validate_bundle_manifest(mutated, full_profile_runtime_digest=full_digest)

            files = _directory_files(destination / "plugin")
            archive_bytes = (destination / result.archive_filename).read_bytes()
            envelope = copy.deepcopy(result.envelope)
            envelope["archive"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(BundleContractError, "exact completed archive"):
                validate_envelope(
                    envelope,
                    manifest=manifest,
                    files=files,
                    archive_bytes=archive_bytes,
                )

    def test_manifest_semantic_mutations_fail_after_digest_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            result = _build(fixture, fixture.destination("output"))
            manifest = result.bundle_manifest

            mutations = (
                (
                    "contract-binding",
                    lambda value: value["contractBindings"]["profileContract"].__setitem__(
                        "sha256", "0" * 64
                    ),
                    "contract bindings drifted",
                ),
                (
                    "canonicalization",
                    lambda value: value["runtimeCanonicalization"].__setitem__(
                        "pathOrder", "locale-order"
                    ),
                    "runtime canonicalization drifted",
                ),
                (
                    "included-surface",
                    lambda value: value["includedSurfaces"][0].__setitem__(
                        "rationale", "drifted"
                    ),
                    "included surfaces drifted",
                ),
                (
                    "excluded-surface",
                    lambda value: value["excludedSurfaces"][0].__setitem__(
                        "rationale", "drifted"
                    ),
                    "excluded surfaces drifted",
                ),
                (
                    "transport-compression",
                    lambda value: value["transport"].__setitem__(
                        "compression", "deflate"
                    ),
                    "transport contract drifted",
                ),
                (
                    "transport-timestamp",
                    lambda value: value["transport"].__setitem__(
                        "timestamp", "1981-01-01T00:00:00"
                    ),
                    "transport contract drifted",
                ),
                (
                    "transport-mode",
                    lambda value: value["transport"].__setitem__(
                        "fileMode", "100755"
                    ),
                    "transport contract drifted",
                ),
                (
                    "transport-archive-name",
                    lambda value: value["transport"].__setitem__(
                        "archiveFilename", "drifted.zip"
                    ),
                    "transport contract drifted",
                ),
                (
                    "dependency-path",
                    lambda value: value["builder"]["behaviorDependencies"][0].__setitem__(
                        "path", "scripts/other.py"
                    ),
                    "path, role, or order drifted",
                ),
                (
                    "dependency-size",
                    lambda value: value["builder"]["behaviorDependencies"][0].__setitem__(
                        "size",
                        value["builder"]["behaviorDependencies"][0]["size"] + 1,
                    ),
                    "dependency identity drifted",
                ),
                (
                    "dependency-sha",
                    lambda value: value["builder"]["behaviorDependencies"][0].__setitem__(
                        "sha256", "0" * 64
                    ),
                    "dependency identity drifted",
                ),
                (
                    "dependency-order",
                    lambda value: value["builder"]["behaviorDependencies"].__setitem__(
                        slice(0, 2),
                        list(reversed(value["builder"]["behaviorDependencies"][:2])),
                    ),
                    "path, role, or order drifted",
                ),
            )
            for label, mutate, diagnostic in mutations:
                with self.subTest(label=label):
                    mutated = copy.deepcopy(manifest)
                    mutate(mutated)
                    _rebind_manifest(mutated)
                    with self.assertRaisesRegex(BundleContractError, diagnostic):
                        validate_bundle_manifest(mutated)

    def test_schema_closure_and_consts_fail_after_manifest_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            result = _build(fixture, fixture.destination("output"))
            original_schema = json.loads(
                (REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json").read_text(
                    encoding="utf-8"
                )
            )

            for label in ("closure", "const"):
                with self.subTest(label=label):
                    schema = copy.deepcopy(original_schema)
                    if label == "closure":
                        schema["$defs"]["transport"]["additionalProperties"] = True
                    elif label == "const":
                        schema["$defs"]["transport"]["properties"]["compression"][
                            "const"
                        ] = "deflate"
                    schema_bytes = (
                        json.dumps(schema, indent=2, ensure_ascii=True) + "\n"
                    ).encode("ascii")
                    dependencies = copy.deepcopy(
                        result.bundle_manifest["builder"]["behaviorDependencies"]
                    )
                    dependencies[2]["size"] = len(schema_bytes)
                    dependencies[2]["sha256"] = hashlib.sha256(schema_bytes).hexdigest()
                    mutated = copy.deepcopy(result.bundle_manifest)
                    mutated["contractBindings"]["bundleSchema"]["sha256"] = hashlib.sha256(
                        schema_bytes
                    ).hexdigest()
                    mutated["builder"]["behaviorDependencies"] = dependencies
                    _rebind_manifest(mutated)
                    with self.assertRaisesRegex(
                        BundleContractError,
                        "bundle schema .* drifted",
                    ):
                        validate_bundle_manifest(
                            mutated,
                            schema=schema,
                            schema_bytes=schema_bytes,
                            behavior_dependencies=tuple(dependencies),
                        )

    def test_zip_timestamp_order_mode_extra_and_member_bytes_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("output")
            result = _build(fixture, destination)
            files = _directory_files(destination / "plugin")

            def altered_zip(kind: str) -> bytes:
                output = io.BytesIO()
                items = list(files.items())
                if kind == "order":
                    items.reverse()
                with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
                    for index, (name, data) in enumerate(items):
                        timestamp = (1981, 1, 1, 0, 0, 0) if kind == "timestamp" and index == 0 else (1980, 1, 1, 0, 0, 0)
                        info = zipfile.ZipInfo(name, timestamp)
                        info.create_system = 3
                        info.compress_type = zipfile.ZIP_STORED
                        info.external_attr = (0o100755 if kind == "mode" and index == 0 else 0o100644) << 16
                        info.extra = b"\x0a\x00\x00\x00" if kind == "extra" and index == 0 else b""
                        archive.writestr(info, data + (b"drift" if kind == "bytes" and index == 0 else b""))
                return output.getvalue()

            for kind in ("timestamp", "order", "mode", "extra", "bytes"):
                with self.subTest(kind=kind), self.assertRaises(BundleContractError):
                    validate_archive_bytes(altered_zip(kind), files)

    def test_failure_cleanup_preserves_unknown_caller_path(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("output")

            def fail_after_unknown(*args, **kwargs):
                (destination / "caller-arrived.txt").write_text("keep\n", encoding="utf-8")
                raise BundleContractError("injected verification failure")

            with mock.patch.object(
                bundle_module,
                "_validate_published_outputs",
                side_effect=fail_after_unknown,
            ):
                with self.assertRaisesRegex(BundleContractError, "injected"):
                    _build(fixture, destination)
            self.assertEqual("keep\n", (destination / "caller-arrived.txt").read_text(encoding="utf-8"))
            self.assertFalse((destination / "plugin").exists())
            self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())
            self.assertFalse((destination / ".axiom-no-hook-bundle-staging").exists())

    def test_output_code_has_no_unbound_repository_python_dependency(self):
        entrypoint = ast.parse(
            (REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py").read_text(encoding="utf-8")
        )
        module = ast.parse(
            (REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py").read_text(encoding="utf-8")
        )
        entrypoint_repo_imports = []
        for node in ast.walk(entrypoint):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("axiom_validation"):
                entrypoint_repo_imports.append(node.module)
        self.assertEqual(["axiom_validation.no_hook_bundle"], entrypoint_repo_imports)

        module_repo_imports = []
        for node in ast.walk(module):
            names = []
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
            module_repo_imports.extend(
                name for name in names if name == "axiom_validation" or name.startswith("axiom_validation.")
            )
        self.assertEqual([], module_repo_imports)

    def test_compatibility_scanner_owns_profile_evidence_without_legacy_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_repository(Path(directory))
            before = _directory_files(root)

            result = self._run_compatibility_scanner(root)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                "Compatibility evidence validation passed: 2 records, "
                "current release v0.10.0 STATIC-ONLY.\n",
                result.stdout,
            )
            self_test = self._run_compatibility_scanner(root, "--self-test")
            self.assertEqual(0, self_test.returncode, self_test.stderr)
            self.assertEqual(
                "Compatibility evidence validation passed: 2 records, "
                "12 negative fixtures, current release v0.10.0 STATIC-ONLY.\n",
                self_test.stdout,
            )

            release_status = json.loads(
                (root / "evidence/release-status.json").read_text(encoding="utf-8")
            )
            legacy_paths = {
                item["path"] for item in release_status["priorReleaseEvidence"]
            }
            self.assertEqual(
                {
                    "evidence/v0.7.4/codex/linux.json",
                    "evidence/v0.7.4/claude-code/linux.json",
                },
                legacy_paths,
            )
            self.assertEqual(before, _directory_files(root))
            self.assertFalse((root / "plugin").exists())
            self.assertFalse((root / BUNDLE_ENVELOPE_NAME).exists())

            scanner_tree = ast.parse(
                (root / "scripts/check-compatibility-evidence.py").read_text(
                    encoding="utf-8"
                )
            )
            scanner_imports = {
                node.module
                for node in ast.walk(scanner_tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            self.assertIn("axiom_validation.no_hook_bundle", scanner_imports)

    def test_compatibility_scanner_rejects_missing_symlink_and_nonregular_profile_evidence(self):
        for mutation in ("missing", "symlink", "nonregular"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                evidence = (
                    root
                    / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
                )
                if mutation == "missing":
                    evidence.unlink()
                elif mutation == "symlink":
                    evidence.unlink()
                    try:
                        evidence.symlink_to(root / "evidence/runtime-identity.json")
                    except OSError as error:
                        self.skipTest(f"file symlink unavailable: {error}")
                else:
                    evidence.unlink()
                    evidence.mkdir()

                result = self._run_compatibility_scanner(root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("no-Hook bundle validation failed", result.stderr)

    def test_compatibility_scanner_rejects_profile_content_and_digest_drift(self):
        mutations = {
            "content": lambda document: document.__setitem__("profileId", "drifted"),
            "profile-runtime": lambda document: document["builds"].__setitem__(
                "profileRuntimeDigest", "sha256:" + "0" * 64
            ),
            "bundle-manifest": lambda document: document["bundleManifest"].__setitem__(
                "bundleManifestDigest", "sha256:" + "0" * 64
            ),
            "archive": lambda document: document["builds"].__setitem__(
                "archiveSha256", "0" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                evidence = (
                    root
                    / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
                )
                document = json.loads(evidence.read_text(encoding="utf-8"))
                mutate(document)
                evidence.write_text(
                    json.dumps(document, indent=2) + "\n", encoding="utf-8"
                )
                result = self._run_compatibility_scanner(root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("no-Hook bundle validation failed", result.stderr)

    def test_compatibility_scanner_rejects_every_other_unowned_evidence_json(self):
        mutations = (
            "evidence/profiles/other-profile/bundle-v1.json",
            "evidence/unowned-root.json",
        )
        for relative in mutations:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
                result = self._run_compatibility_scanner(root)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(
                    f"unowned evidence JSON files: {relative}", result.stderr
                )

    @staticmethod
    def _copy_repository(parent: Path) -> Path:
        return Path(
            shutil.copytree(
                REPOSITORY_ROOT,
                parent / "repository",
                symlinks=True,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
        )

    @staticmethod
    def _run_compatibility_scanner(
        root: Path, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(root / "scripts/check-compatibility-evidence.py"),
                *arguments,
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

    def test_manifest_rejects_hidden_or_undeclared_runtime_record(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            result = _build(fixture, fixture.destination("output"))
            mutated = copy.deepcopy(result.bundle_manifest)
            mutated["runtimeFiles"].append(
                {
                    "path": "skills/using-axiom/.hidden.md",
                    "kind": "resource",
                    "mode": "100644",
                    "size": 1,
                    "sha256": "0" * 64,
                }
            )
            with self.assertRaisesRegex(BundleContractError, "exactly 50"):
                validate_bundle_manifest(mutated)


if __name__ == "__main__":
    unittest.main()
