"""Focused negative and deterministic tests for the no-Hook bundle builder."""

from __future__ import annotations

import ast
import copy
import io
import json
import os
import shutil
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
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
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
            source = GitObjectSource(fixture.root)

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
                GitObjectSource(fixture.root).list_files(fixture.commit_oid, "skills")

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.git("update-index", "--chmod=+x", "skills/using-axiom/SKILL.md")
            fixture.git("commit", "--quiet", "-m", "executable tree")
            with self.assertRaisesRegex(BundleContractError, "100644 blob"):
                GitObjectSource(fixture.root).list_files(fixture.commit_oid, "skills")

    def test_dirty_untracked_and_ignored_runtime_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            (fixture.root / "skills/using-axiom/untracked.md").write_text(
                "untracked\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(BundleContractError, "dirty, untracked, or ignored"):
                _build(fixture, fixture.destination("output"))

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            (fixture.root / ".gitignore").write_text("skills/using-axiom/ignored.md\n", encoding="utf-8")
            fixture.commit("ignore policy")
            (fixture.root / "skills/using-axiom/ignored.md").write_text(
                "ignored\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(BundleContractError, "dirty, untracked, or ignored"):
                _build(fixture, fixture.destination("output"))

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
                )
            with mock.patch.dict(os.environ, {"GIT_DIR": str(fixture.root / ".git")}):
                with self.assertRaisesRegex(BundleContractError, "dangerous ambient Git"):
                    GitObjectSource(fixture.root)

    def test_replace_refs_and_object_alternates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.git(
                "update-ref",
                f"refs/replace/{fixture.commit_oid}",
                fixture.commit_oid,
            )
            with self.assertRaisesRegex(BundleContractError, "replace refs"):
                GitObjectSource(fixture.root)

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            alternates = fixture.root / ".git/objects/info/alternates"
            alternates.parent.mkdir(parents=True, exist_ok=True)
            alternates.write_text(str(fixture.root / ".git/objects") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(BundleContractError, "object alternates"):
                GitObjectSource(fixture.root)

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
                schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
            )
            skill = fixture.root / "skills/using-axiom/SKILL.md"
            skill.write_bytes(skill.read_bytes() + b"changed\n")
            with self.assertRaisesRegex(BundleContractError, "working-tree state changed"):
                inputs.verify_source_unchanged()

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
