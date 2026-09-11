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
from pathlib import Path, PurePosixPath
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
    build_bundle_to_directory_fd,
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
        schema = json.loads((REPOSITORY_ROOT / bundle_module.SCHEMA_RELATIVE).read_text(encoding="utf-8"))
        source_identity["repositoryPolicyRevision"] = schema["x-axiom-contract"]["sourceRepositoryPolicyRevision"]
        source_identity_path.write_text(
            json.dumps(source_identity, indent=2) + "\n", encoding="utf-8"
        )
        self.git("init", "--quiet")
        self.git("config", "user.name", "Axiom Test")
        self.git("config", "user.email", "axiom-test@example.invalid")
        self.git("config", "gc.auto", "0")
        self.git("config", "gc.autoPackLimit", "0")
        self.git("config", "maintenance.auto", "false")
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


def _static_runtime_inputs() -> tuple[dict[str, object], list[dict[str, object]]]:
    schema = json.loads(
        (REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json").read_text(
            encoding="utf-8"
        )
    )
    evidence = json.loads(
        (
            REPOSITORY_ROOT
            / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
        ).read_text(encoding="utf-8")
    )
    return (
        copy.deepcopy(schema["x-axiom-contract"]["runtimeInventory"]),
        copy.deepcopy(evidence["bundleManifest"]["runtimeFiles"]),
    )


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
    def test_frozen_local_objects_build_identical_archive_without_runtime_backend(self):
        """Read existing history only; no fixture commit or isolation backend."""
        from axiom_validation import no_hook_linux_isolation as isolation

        evidence = json.loads((REPOSITORY_ROOT / bundle_module.EVIDENCE_RELATIVE).read_text(encoding="utf-8"))
        source = evidence["source"]
        expected_manifest = evidence["bundleManifest"]
        with tempfile.TemporaryDirectory() as directory, (
            mock.patch.object(isolation, "detect_process_domain_capabilities", side_effect=AssertionError("runtime detector called"))
        ), mock.patch.object(isolation.LinuxProcessDomainSupervisor, "open", side_effect=AssertionError("runtime backend called")):
            parent = Path(directory)
            outputs = []
            for name in ("first", "second"):
                destination = parent / name
                destination.mkdir()
                result = build_bundle(
                    REPOSITORY_ROOT,
                    source["commit"],
                    source["tree"],
                    destination,
                    git_executable=GIT_EXECUTABLE,
                    schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                    entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                    module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                )
                self.assertEqual(expected_manifest["bundleManifestDigest"], result.bundle_manifest_digest)
                self.assertEqual(evidence["builds"]["archiveSha256"], result.archive_sha256)
                self.assertEqual(expected_manifest["profileRuntimeDigest"], result.profile_runtime_digest)
                outputs.append(_directory_files(destination))
            self.assertEqual(outputs[0], outputs[1])

    def test_checked_in_static_evidence_reproduces_without_output(self):
        failures: list[str] = []
        self.assertEqual((50, 2), check_no_hook_bundle(failures))
        self.assertEqual([], failures)

    def test_schema_revision_migration_preserves_legacy_pair_and_rejects_mixed_pairs(self):
        current = json.loads((REPOSITORY_ROOT / bundle_module.SCHEMA_RELATIVE).read_text(encoding="utf-8"))
        contract = bundle_module._schema_contract(current)
        self.assertEqual((13, 14), (
            contract["sourceRepositoryPolicyRevision"],
            contract["candidateRepositoryPolicyRevision"],
        ))
        recorded = json.loads((REPOSITORY_ROOT /
            "evals/no-hook-observation/historical-protocols/clarification-round-2/bundle-manifest-schema-v1.json").read_text())
        self.assertEqual(recorded["x-axiom-contract"], bundle_module._schema_contract(recorded))
        prior = copy.deepcopy(current)
        prior["properties"]["repositoryPolicyRevision"] = {"const": 9}
        prior["$defs"]["source"]["properties"]["repositoryPolicyRevision"] = {"const": 8}
        prior["x-axiom-contract"].update(sourceRepositoryPolicyRevision=8, candidateRepositoryPolicyRevision=9)
        self.assertEqual(prior["x-axiom-contract"], bundle_module._schema_contract(prior))
        legacy = copy.deepcopy(current)
        legacy["properties"]["repositoryPolicyRevision"] = {"const": 6}
        legacy["$defs"]["source"]["properties"]["repositoryPolicyRevision"] = {"const": 5}
        legacy_contract = legacy["x-axiom-contract"]
        legacy_contract["sourceRepositoryPolicyRevision"] = 5
        legacy_contract["candidateRepositoryPolicyRevision"] = 6
        legacy_contract["runtimeInventory"]["runtimeBytes"] = 230826
        del legacy_contract["fullProfileRuntimeDigest"]
        self.assertEqual(legacy_contract, bundle_module._schema_contract(legacy))

        for source_revision, owner_revision in ((5, 9), (8, 6), (7, 8), (True, 9), (8, 12), (11, 9), (12, 13), (11, 14), (13, 12), (14, 15)):
            with self.subTest(source=source_revision, owner=owner_revision):
                bad = copy.deepcopy(current)
                bad["x-axiom-contract"]["sourceRepositoryPolicyRevision"] = source_revision
                bad["x-axiom-contract"]["candidateRepositoryPolicyRevision"] = owner_revision
                with self.assertRaisesRegex(BundleContractError, "revision pair is unsupported"):
                    bundle_module._schema_contract(bad)

        for label, mutate, diagnostic in (
            ("owner-const", lambda value: value["properties"]["repositoryPolicyRevision"].update(const=6), "top-level property"),
            ("source-const", lambda value: value["$defs"]["source"]["properties"]["repositoryPolicyRevision"].update(const=5), "source definition"),
            ("missing-runtime-binding", lambda value: value["x-axiom-contract"].pop("fullProfileRuntimeDigest"), "x-axiom-contract"),
            ("invalid-runtime-binding", lambda value: value["x-axiom-contract"].update(fullProfileRuntimeDigest="unknown"), "runtime digest is invalid"),
        ):
            with self.subTest(label=label):
                bad = copy.deepcopy(current)
                mutate(bad)
                with self.assertRaisesRegex(BundleContractError, diagnostic):
                    bundle_module._schema_contract(bad)

        legacy_contract["runtimeInventory"]["runtimeBytes"] += 1
        with self.assertRaisesRegex(BundleContractError, "runtime inventory contract drifted"):
            bundle_module._schema_contract(legacy)
        for byte_count in (False, 0, bundle_module.MAX_RUNTIME_BYTES + 1):
            with self.subTest(runtime_bytes=byte_count):
                bad = copy.deepcopy(current)
                bad["x-axiom-contract"]["runtimeInventory"]["runtimeBytes"] = byte_count
                with self.assertRaisesRegex(BundleContractError, "runtime inventory contract drifted"):
                    bundle_module._schema_contract(bad)

    def test_new_source_runtime_inventory_and_full_profile_binding_are_checked(self):
        for field in ("digest", "repositoryPolicyRevision"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                identity_path = fixture.root / "evidence/runtime-identity.json"
                identity = json.loads(identity_path.read_text(encoding="utf-8"))
                if field == "digest":
                    identity["runtimeContract"]["digest"] = "sha256:" + "0" * 64
                    expected = "full-profile runtime digest differs from bundle schema"
                else:
                    identity["repositoryPolicyRevision"] = 5
                    expected = "source repositoryPolicyRevision does not match bundle schema"
                identity_path.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
                fixture.commit("mismatched source identity")
                with self.assertRaisesRegex(BundleContractError, expected):
                    _build(fixture, fixture.destination("output"))

        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            schema = json.loads((REPOSITORY_ROOT / bundle_module.SCHEMA_RELATIVE).read_text(encoding="utf-8"))
            schema["x-axiom-contract"]["runtimeInventory"]["runtimeBytes"] += 1
            schema_path = Path(directory) / "wrong-inventory-schema.json"
            schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(BundleContractError, "byte count drifted from the frozen inventory"):
                inspect_source(
                    fixture.root, fixture.commit_oid, fixture.tree_oid,
                    git_executable=GIT_EXECUTABLE,
                    schema_path=schema_path,
                    entrypoint_path=REPOSITORY_ROOT / bundle_module.ENTRYPOINT_RELATIVE,
                    module_path=REPOSITORY_ROOT / bundle_module.MODULE_RELATIVE,
                )

    def test_static_evidence_keeps_declared_owner_after_later_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self._copy_repository(Path(directory))
            revision_path = root / "evidence/repository-policy-revisions-v1.json"
            revision_document = json.loads(
                revision_path.read_text(
                    encoding="utf-8"
                )
            )
            revisions = revision_document["revisions"]
            evidence = json.loads(
                (
                    root
                    / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
                ).read_text(encoding="utf-8")
            )
            manifest = evidence["bundleManifest"]
            schema = json.loads((root / bundle_module.SCHEMA_RELATIVE).read_text(encoding="utf-8"))
            contract = schema["x-axiom-contract"]
            later_revision = copy.deepcopy(revisions[-1])
            later_revision["revision"] = max(item["revision"] for item in revisions) + 1
            later_revision["baselineCommit"] = "0" * 40
            later_revision["runtimeContractDigest"] = "sha256:" + "0" * 64
            revisions.append(later_revision)
            revision_path.write_text(json.dumps(revision_document, indent=2) + "\n", encoding="utf-8")
            before = _directory_files(root)

            self.assertGreater(revisions[-1]["revision"], contract["candidateRepositoryPolicyRevision"])
            self.assertEqual(contract["candidateRepositoryPolicyRevision"], evidence["candidateRepositoryPolicyRevision"])
            self.assertEqual(contract["candidateRepositoryPolicyRevision"], manifest["repositoryPolicyRevision"])
            failures: list[str] = []
            self.assertEqual((50, 2), check_no_hook_bundle(failures, root))
            self.assertEqual([], failures)
            self.assertEqual(before, _directory_files(root))
            self.assertFalse((root / "plugin").exists())
            self.assertFalse((root / BUNDLE_ENVELOPE_NAME).exists())
            self.assertEqual(8, len({record["path"].split("/", 2)[1] for record in manifest["runtimeFiles"]}))
            self.assertEqual(50, len(manifest["runtimeFiles"]))
            self.assertEqual(contract["runtimeInventory"]["runtimeBytes"], sum(record["size"] for record in manifest["runtimeFiles"]))
            full_manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "name": "axiom",
                    "version": full_manifest["version"],
                    "description": "Think before AI thinks.",
                    "skills": "./skills/",
                },
                manifest["derivedPluginManifest"]["fields"],
            )
            self.assertEqual(evidence["builds"]["profileRuntimeDigest"], manifest["profileRuntimeDigest"])

    def test_static_evidence_rejects_invalid_bundle_owner_revision_binding(self):
        schema = json.loads((REPOSITORY_ROOT / bundle_module.SCHEMA_RELATIVE).read_text(encoding="utf-8"))
        owner = schema["x-axiom-contract"]["candidateRepositoryPolicyRevision"]

        def mutate_missing(
            evidence: dict[str, object], revisions: list[dict[str, object]]
        ) -> None:
            del evidence
            revisions[:] = [revision for revision in revisions if revision["revision"] != owner]

        def mutate_duplicate(
            evidence: dict[str, object], revisions: list[dict[str, object]]
        ) -> None:
            del evidence
            revision = next(item for item in revisions if item["revision"] == owner)
            revisions.insert(-1, copy.deepcopy(revision))

        def mutate_revision_field(
            field: str, value: object
        ):
            def mutate(
                evidence: dict[str, object], revisions: list[dict[str, object]]
            ) -> None:
                del evidence
                revision = next(item for item in revisions if item["revision"] == owner)
                revision[field] = value

            return mutate

        def mutate_candidate(
            evidence: dict[str, object], revisions: list[dict[str, object]]
        ) -> None:
            del revisions
            evidence["candidateRepositoryPolicyRevision"] = owner + 1

        cases = (
            (
                "missing-owner-later-revision-not-owner",
                mutate_missing,
                f"bundle owner revision {owner} is missing",
            ),
            (
                "duplicate-owner-revision",
                mutate_duplicate,
                f"bundle owner revision {owner} is duplicated",
            ),
            (
                "baseline",
                mutate_revision_field("baselineCommit", "0" * 40),
                f"revision {owner} baselineCommit does not bind",
            ),
            (
                "source-issue",
                mutate_revision_field("sourceIssue", 999),
                f"revision {owner} sourceIssue must be 117",
            ),
            (
                "runtime-digest",
                mutate_revision_field("runtimeContractDigest", "sha256:" + "0" * 64),
                f"revision {owner} runtimeContractDigest does not bind",
            ),
            (
                "candidate-manifest-mismatch",
                mutate_candidate,
                "candidate repositoryPolicyRevision differs from its bundle manifest",
            ),
        )
        for label, mutate, diagnostic in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                evidence_path = (
                    root
                    / "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
                )
                revisions_path = root / "evidence/repository-policy-revisions-v1.json"
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                revision_document = json.loads(revisions_path.read_text(encoding="utf-8"))
                revisions = revision_document["revisions"]
                mutate(evidence, revisions)
                evidence_path.write_text(
                    json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
                )
                revisions_path.write_text(
                    json.dumps(revision_document, indent=2) + "\n", encoding="utf-8"
                )

                failures: list[str] = []
                self.assertEqual((0, 0), check_no_hook_bundle(failures, root))
                self.assertEqual(1, len(failures))
                self.assertIn(diagnostic, failures[0])
                self.assertFalse((root / "plugin").exists())
                self.assertFalse((root / BUNDLE_ENVELOPE_NAME).exists())

    def test_regular_file_reader_bounds_extra_short_growth_and_identity_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "bounded.json"
            target.write_bytes(b"x")
            metadata = target.lstat()

            for label, payload, diagnostic in (
                ("extra", b"xy", "exceeds its expected bounded size"),
                ("short", b"", "ended before its expected bounded size"),
            ):
                with self.subTest(label=label):
                    offset = 0
                    consumed = 0
                    maximum_request = 0

                    def bounded_read(unused_descriptor: int, length: int) -> bytes:
                        nonlocal offset, consumed, maximum_request
                        maximum_request = max(maximum_request, length)
                        result = payload[offset : offset + length]
                        offset += len(result)
                        consumed += len(result)
                        return result

                    with (
                        mock.patch.object(bundle_module.os, "open", return_value=91),
                        mock.patch.object(bundle_module.os, "fstat", return_value=metadata),
                        mock.patch.object(bundle_module.os, "read", side_effect=bounded_read),
                        mock.patch.object(bundle_module.os, "close") as close,
                    ):
                        with self.assertRaisesRegex(BundleContractError, diagnostic):
                            bundle_module._read_regular_file(
                                target,
                                "bounded fixture",
                                maximum=1,
                                expected_size=1,
                            )
                    self.assertLessEqual(consumed, 2)
                    self.assertLessEqual(maximum_request, 1)
                    close.assert_called_once_with(91)

            target.write_bytes(b"x")
            original_read = os.read
            consumed = 0
            grew = False

            def read_then_grow(descriptor: int, length: int) -> bytes:
                nonlocal consumed, grew
                data = original_read(descriptor, length)
                consumed += len(data)
                if data and not grew:
                    with target.open("ab") as handle:
                        handle.write(b"y")
                    grew = True
                return data

            with mock.patch.object(bundle_module.os, "read", side_effect=read_then_grow):
                with self.assertRaisesRegex(BundleContractError, "expected bounded size"):
                    bundle_module._read_regular_file(
                        target,
                        "growing fixture",
                        maximum=1,
                        expected_size=1,
                    )
            self.assertLessEqual(consumed, 2)

            target.write_bytes(b"identity")
            original_fstat = os.fstat
            for mutation in ("identity", "size"):
                with self.subTest(mutation=mutation):
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
                        with self.assertRaisesRegex(BundleContractError, "changed (identity|size)"):
                            bundle_module._read_regular_file(
                                target,
                                "changing fixture",
                                maximum=len(b"identity"),
                                expected_size=len(b"identity"),
                            )

    def test_static_replay_streaming_stops_at_first_extra_without_reading_bodies(self):
        inventory, records = _static_runtime_inputs()
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            skills_root = fixture.root / "skills"
            for index in range(300):
                (skills_root / f"unexpected-{index:03d}.md").write_text(
                    "unexpected\n",
                    encoding="utf-8",
                )
            destination = fixture.destination("output")
            object_inventory = _object_database_inventory(fixture.root)
            source_status = fixture.git(
                "status", "--porcelain=v1", "--untracked-files=all"
            ).stdout
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
                    child = next(self.iterator)
                    observed += 1
                    return child

            def counting_scandir(path: os.PathLike[str] | str):
                if Path(path) == skills_root:
                    return CountingScandir(path)
                return real_scandir(path)

            with (
                mock.patch.object(bundle_module.os, "scandir", side_effect=counting_scandir),
                mock.patch.object(
                    bundle_module,
                    "_read_regular_file",
                    wraps=bundle_module._read_regular_file,
                ) as read_file,
            ):
                with self.assertRaisesRegex(BundleContractError, "entry set differs"):
                    bundle_module._filesystem_runtime(fixture.root, inventory, records)
            expected_root_children = {
                PurePosixPath(record["path"]).parts[1] for record in records
            }
            self.assertLessEqual(observed, len(expected_root_children) + 1)
            read_file.assert_not_called()
            self.assertEqual(object_inventory, _object_database_inventory(fixture.root))
            self.assertEqual(
                source_status,
                fixture.git("status", "--porcelain=v1", "--untracked-files=all").stdout,
            )
            self.assertEqual([], list(destination.iterdir()))

    def test_static_replay_rejects_untrusted_count_and_aggregate_before_enumeration(self):
        def record(index: int, size: int) -> dict[str, object]:
            return {
                "path": f"skills/example/file-{index:03d}.md",
                "kind": "resource",
                "mode": "100644",
                "size": size,
                "sha256": "0" * 64,
            }

        cases = (
            (
                "file count",
                bundle_module.MAX_RUNTIME_FILES + 1,
                1,
                None,
                "file count exceeds",
            ),
            (
                "aggregate bytes",
                9,
                bundle_module.MAX_RUNTIME_FILE_BYTES,
                None,
                "runtime bytes exceed",
            ),
            ("frozen byte total", 1, 1, 2, "differ from the frozen byte total"),
        )
        for label, count, size, total_override, diagnostic in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                records = [record(index, size) for index in range(count)]
                inventory = {
                    "directSkillRoots": 1,
                    "runtimeFiles": count,
                    "runtimeBytes": count * size if total_override is None else total_override,
                    "allowedExtensions": [".md"],
                }
                with mock.patch.object(bundle_module.os, "scandir") as scandir:
                    with self.assertRaisesRegex(BundleContractError, diagnostic):
                        bundle_module._filesystem_runtime(Path(directory), inventory, records)
                scandir.assert_not_called()

    def test_static_replay_rejects_physical_size_before_file_body_read(self):
        inventory, records = _static_runtime_inputs()
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            target = fixture.root / "skills/using-axiom/SKILL.md"
            target.write_bytes(target.read_bytes() + b"drift\n")
            read_paths: list[Path] = []
            original = bundle_module._read_regular_file

            def record_read(path: Path, *args: object, **kwargs: object) -> bytes:
                read_paths.append(path)
                return original(path, *args, **kwargs)

            with mock.patch.object(
                bundle_module,
                "_read_regular_file",
                side_effect=record_read,
            ):
                with self.assertRaisesRegex(BundleContractError, "size differs"):
                    bundle_module._filesystem_runtime(fixture.root, inventory, records)
            self.assertNotIn(target, read_paths)

    def test_static_replay_bounds_all_json_inputs_and_rejects_bound_links(self):
        oversized_paths = (
            "evals/no-hook/bundle-manifest-schema-v1.json",
            "evidence/profiles/openai-hook-independent-v1/bundle-v1.json",
            "evals/no-hook/benchmark-v1.json",
            "evals/no-hook/golden-set-v1.jsonl",
        )
        for relative in oversized_paths:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                target = root / relative
                with target.open("r+b") as handle:
                    handle.truncate(bundle_module.MAX_BUNDLE_MANIFEST_BYTES + 1)
                failures: list[str] = []
                self.assertEqual((0, 0), check_no_hook_bundle(failures, root))
                self.assertEqual(1, len(failures))
                self.assertIn("524288-byte", failures[0])
                self.assertFalse((root / "plugin").exists())
                self.assertFalse((root / BUNDLE_ENVELOPE_NAME).exists())

        for relative in (
            "evals/no-hook/benchmark-v1.json",
            "evals/no-hook/golden-set-v1.jsonl",
        ):
            with self.subTest(relative=f"symlink:{relative}"), tempfile.TemporaryDirectory() as directory:
                root = self._copy_repository(Path(directory))
                target = root / relative
                target.unlink()
                try:
                    target.symlink_to(root / "evals/no-hook/profile-v1.json")
                except OSError as error:
                    self.skipTest(f"file symlink unavailable: {error}")
                failures = []
                self.assertEqual((0, 0), check_no_hook_bundle(failures, root))
                self.assertEqual(1, len(failures))
                self.assertIn("must not be a symbolic link", failures[0])

    def test_static_replay_module_has_no_unbounded_path_reads(self):
        tree = ast.parse(
            (REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py").read_text(
                encoding="utf-8"
            )
        )
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "read_bytes"
        ]
        self.assertEqual([], calls)

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
                b'  "version": "0.10.1",\n'
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

    def test_descriptor_destination_builds_and_path_api_delegates(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("fd-output")
            descriptor = os.open(
                destination,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                metadata = os.fstat(descriptor)
                publications: list[str] = []

                def hook(phase: str, facts: dict[str, object]) -> None:
                    if phase in {"builder-after-publish", "builder-before-completion-publish"}:
                        publications.append(str(facts["destination"]))
                        self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())

                result = build_bundle_to_directory_fd(
                    fixture.root,
                    fixture.commit_oid,
                    fixture.tree_oid,
                    descriptor,
                    git_executable=GIT_EXECUTABLE,
                    schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                    entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                    module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                    expected_destination_identity=(metadata.st_dev, metadata.st_ino),
                    _test_hook=hook,
                )
            finally:
                os.close(descriptor)
            self.assertGreater(len(result.creation_records), result.directory_file_count)
            self.assertEqual("2", result.output_lifecycle_version)
            self.assertTrue(all(
                record.creation_phase.startswith("builder-output-v2:")
                for record in result.creation_records
            ))
            self.assertEqual(
                ["plugin", result.archive_filename, BUNDLE_ENVELOPE_NAME],
                publications,
            )
            self.assertFalse((destination / bundle_module.STAGING_DIRECTORY_NAME).exists())
            self.assertEqual(
                {"plugin", result.archive_filename, BUNDLE_ENVELOPE_NAME},
                {path.name for path in destination.iterdir()},
            )

            delegated = fixture.destination("delegated")
            real_core = bundle_module.build_bundle_to_directory_fd
            with mock.patch.object(
                bundle_module,
                "build_bundle_to_directory_fd",
                wraps=real_core,
            ) as core:
                _build(fixture, delegated)
            core.assert_called_once()

            alias = Path(f"/proc/self/fd/{os.open(delegated, os.O_RDONLY)}")
            try:
                with self.assertRaisesRegex(
                    BundleContractError, "symbolic link"
                ):
                    build_bundle(
                        fixture.root,
                        fixture.commit_oid,
                        fixture.tree_oid,
                        alias,
                        git_executable=GIT_EXECUTABLE,
                    )
            finally:
                os.close(int(alias.name))

    def test_descriptor_destination_rejects_identity_nonempty_and_non_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("fd-errors")
            descriptor = os.open(destination, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                metadata = os.fstat(descriptor)
                with self.assertRaisesRegex(BundleContractError, "identity does not match"):
                    build_bundle_to_directory_fd(
                        fixture.root,
                        fixture.commit_oid,
                        fixture.tree_oid,
                        descriptor,
                        git_executable=GIT_EXECUTABLE,
                        expected_destination_identity=(metadata.st_dev, metadata.st_ino + 1),
                    )
                (destination / "unknown").write_text("keep\n", encoding="utf-8")
                with self.assertRaisesRegex(BundleContractError, "destination must be empty"):
                    build_bundle_to_directory_fd(
                        fixture.root,
                        fixture.commit_oid,
                        fixture.tree_oid,
                        descriptor,
                        git_executable=GIT_EXECUTABLE,
                    )
            finally:
                os.close(descriptor)
            regular = Path(directory) / "regular"
            regular.write_text("not a directory\n", encoding="utf-8")
            file_fd = os.open(regular, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                with self.assertRaisesRegex(BundleContractError, "ordinary directory"):
                    build_bundle_to_directory_fd(
                        fixture.root,
                        fixture.commit_oid,
                        fixture.tree_oid,
                        file_fd,
                        git_executable=GIT_EXECUTABLE,
                    )
            finally:
                os.close(file_fd)

            if hasattr(os, "O_PATH"):
                target = Path(directory) / "symlink-target"
                target.mkdir()
                linked = Path(directory) / "symlink-destination"
                try:
                    linked.symlink_to(target, target_is_directory=True)
                except OSError as error:
                    self.skipTest(f"directory symlink unavailable: {error}")
                link_fd = os.open(
                    linked,
                    os.O_PATH | getattr(os, "O_NOFOLLOW", 0),
                )
                try:
                    with self.assertRaisesRegex(
                        BundleContractError, "ordinary directory"
                    ):
                        build_bundle_to_directory_fd(
                            fixture.root,
                            fixture.commit_oid,
                            fixture.tree_oid,
                            link_fd,
                            git_executable=GIT_EXECUTABLE,
                        )
                finally:
                    os.close(link_fd)

    def test_builder_creation_and_cleanup_races_preserve_unknown_objects(self):
        # Lifecycle v2 removes quarantine deletion. Its successor negative case
        # checks replacement during failed validation and preserves both objects.
        for scenario in ("before-ledger", "after-ledger", "failure-retention"):
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                destination = fixture.destination("race-output")
                mutated = False

                def hook(phase: str, facts: dict[str, object]) -> None:
                    nonlocal mutated
                    parent_fd = int(facts.get("parentDescriptor", -1))
                    if mutated or parent_fd < 0:
                        return
                    if (
                        scenario == "before-ledger"
                        and phase == "builder-after-create-before-ledger"
                        and facts["relativePath"] == "plugin"
                    ):
                        name = str(facts["basename"])
                        os.rename(name, "moved-original", src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                        os.mkdir(name, 0o700, dir_fd=parent_fd)
                        mutated = True
                    elif (
                        scenario == "after-ledger"
                        and phase == "builder-after-publish"
                        and facts["destination"] == "plugin"
                    ):
                        os.rename("plugin", "moved-original", src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                        os.mkdir("plugin", 0o755, dir_fd=parent_fd)
                        mutated = True
                def failed_validation(*args, **kwargs):
                    nonlocal mutated
                    (destination / "plugin").rename(destination / "moved-original")
                    (destination / "plugin").mkdir()
                    (destination / "plugin/caller.txt").write_bytes(b"preserve caller object\n")
                    mutated = True
                    raise BundleContractError("injected validation failure")

                if scenario == "failure-retention":
                    verifier = mock.patch.object(
                        bundle_module,
                        "_validate_published_outputs_fd",
                        side_effect=failed_validation,
                    )
                else:
                    verifier = mock.patch.object(
                        bundle_module,
                        "_validate_published_outputs_fd",
                        wraps=bundle_module._validate_published_outputs_fd,
                    )
                with verifier, self.assertRaisesRegex(
                    bundle_module.BuilderCleanupError, "manual cleanup required"
                ):
                    build_bundle(
                        fixture.root,
                        fixture.commit_oid,
                        fixture.tree_oid,
                        destination,
                        git_executable=GIT_EXECUTABLE,
                        schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                        entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                        module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                        _test_hook=hook,
                    )
                self.assertTrue(mutated)
                self.assertTrue((destination / "moved-original").exists())
                self.assertTrue((destination / "plugin").exists())
                self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())
                self.assertFalse((destination / bundle_module.STAGING_DIRECTORY_NAME).exists())
                if scenario == "failure-retention":
                    self.assertEqual(
                        b"preserve caller object\n",
                        (destination / "plugin/caller.txt").read_bytes(),
                    )

    def test_lifecycle_v2_registration_failure_retains_created_file_and_cause(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("registration-failure")
            original_error = BundleContractError("injected registration failure")
            original = bundle_module._BuilderCreationLedger._record_created

            def reject_file(ledger, relative, parent_fd, name, descriptor, kind, phase):
                if kind == "file":
                    raise original_error
                return original(ledger, relative, parent_fd, name, descriptor, kind, phase)

            with mock.patch.object(
                bundle_module._BuilderCreationLedger, "_record_created", reject_file,
            ), self.assertRaises(bundle_module.BuilderBuildIncompleteError) as caught:
                _build(fixture, destination)
            failure = caught.exception
            self.assertIs(original_error, failure.__cause__)
            unregistered = [
                item for item in failure.creation_attempts
                if item.created and not item.registered
            ]
            self.assertEqual(1, len(unregistered))
            attempt = unregistered[0]
            self.assertEqual("file", attempt.kind)
            retained = destination / attempt.relative_path
            self.assertTrue(retained.is_file())
            self.assertEqual(
                (attempt.device, attempt.inode),
                (retained.stat().st_dev, retained.stat().st_ino),
            )
            self.assertEqual(b"", retained.read_bytes())
            self.assertTrue(failure.manual_cleanup_required)
            self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())

    def test_lifecycle_v2_mkdir_open_failure_preserves_unbound_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("open-failure")
            original_error = OSError("injected directory open failure")
            original_open = os.open

            def reject_plugin_open(path, flags, *args, **kwargs):
                if path == "plugin" and flags & getattr(os, "O_DIRECTORY", 0):
                    raise original_error
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(bundle_module.os, "open", reject_plugin_open):
                with self.assertRaises(bundle_module.BuilderBuildIncompleteError) as caught:
                    _build(fixture, destination)
            failure = caught.exception
            self.assertIs(original_error, failure.__cause__)
            self.assertEqual(1, len(failure.creation_attempts))
            attempt = failure.creation_attempts[0]
            self.assertEqual("plugin", attempt.relative_path)
            self.assertTrue(attempt.created)
            self.assertFalse(attempt.registered)
            self.assertIsNone(attempt.device)
            self.assertIsNone(attempt.inode)
            self.assertEqual((), failure.output_records)
            self.assertTrue((destination / "plugin").is_dir())
            self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())

    def test_lifecycle_v2_existing_name_is_not_claimed_or_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("preexisting-output")
            injected = False

            def hook(phase, facts):
                nonlocal injected
                if phase == "builder-before-create" and facts["relativePath"] == "plugin":
                    (destination / "plugin").mkdir()
                    (destination / "plugin/caller.txt").write_bytes(b"caller\n")
                    injected = True

            with self.assertRaisesRegex(BundleContractError, "already exists") as caught:
                build_bundle(
                    fixture.root, fixture.commit_oid, fixture.tree_oid, destination,
                    git_executable=GIT_EXECUTABLE, _test_hook=hook,
                )
            self.assertTrue(injected)
            self.assertNotIsInstance(caught.exception, bundle_module.BuilderBuildIncompleteError)
            self.assertEqual(b"caller\n", (destination / "plugin/caller.txt").read_bytes())
            self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())

    def test_lifecycle_v2_fallible_preconditions_precede_completion_marker(self):
        patches = (
            (bundle_module, "_validate_published_outputs_fd"),
            (bundle_module.BundleInputs, "verify_source_unchanged"),
            (bundle_module._BuilderCreationLedger, "exported_records"),
        )
        for owner, name in patches:
            with self.subTest(check=name), tempfile.TemporaryDirectory() as directory:
                fixture = SourceFixture(Path(directory))
                destination = fixture.destination("precondition-failure")
                original_error = BundleContractError(f"injected {name}")

                def reject(*args, **kwargs):
                    self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())
                    raise original_error

                with mock.patch.object(owner, name, side_effect=reject):
                    with self.assertRaises(bundle_module.BuilderBuildIncompleteError) as caught:
                        _build(fixture, destination)
                self.assertIs(original_error, caught.exception.__cause__)
                self.assertTrue((destination / "plugin").is_dir())
                self.assertFalse((destination / BUNDLE_ENVELOPE_NAME).exists())
                self.assertFalse((destination / bundle_module.STAGING_DIRECTORY_NAME).exists())

    def test_lifecycle_v2_completion_collision_preserves_existing_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("completion-collision")
            original_publish = bundle_module._BuilderCompletionFile.publish

            def collide(completion):
                (destination / BUNDLE_ENVELOPE_NAME).write_bytes(b"caller marker\n")
                return original_publish(completion)

            with mock.patch.object(bundle_module._BuilderCompletionFile, "publish", collide):
                with self.assertRaisesRegex(
                    bundle_module.BuilderBuildIncompleteError, "already exists",
                ):
                    _build(fixture, destination)
            self.assertEqual(b"caller marker\n", (destination / BUNDLE_ENVELOPE_NAME).read_bytes())
            self.assertTrue((destination / "plugin").is_dir())
            self.assertFalse((destination / bundle_module.STAGING_DIRECTORY_NAME).exists())

    def test_lifecycle_v2_unsupported_completion_file_leaves_destination_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("unsupported-completion")
            original_open = os.open
            original_error = OSError("injected unsupported unnamed completion")

            def reject_tmpfile(path, flags, *args, **kwargs):
                if flags & os.O_TMPFILE == os.O_TMPFILE:
                    raise original_error
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(bundle_module.os, "open", reject_tmpfile):
                with self.assertRaises(OSError) as caught:
                    _build(fixture, destination)
            self.assertIs(original_error, caught.exception)
            self.assertEqual([], list(destination.iterdir()))

    def test_lifecycle_v2_success_never_deletes_or_renames_named_output(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("no-named-cleanup")
            with mock.patch.object(bundle_module.os, "unlink", side_effect=AssertionError("unlink")), \
                 mock.patch.object(bundle_module.os, "rmdir", side_effect=AssertionError("rmdir")), \
                 mock.patch.object(bundle_module.os, "rename", side_effect=AssertionError("rename")):
                result = _build(fixture, destination)
            self.assertEqual(
                {"plugin", result.archive_filename, BUNDLE_ENVELOPE_NAME},
                {item.name for item in destination.iterdir()},
            )
            marker = json.loads((destination / BUNDLE_ENVELOPE_NAME).read_bytes())
            self.assertTrue(marker["complete"])
            self.assertEqual(result.archive_sha256, marker["archive"]["sha256"])

    def test_lifecycle_v2_cli_build_and_repeated_destination_preserve_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("cli-output")
            command = [
                sys.executable, "-I", "-B", "scripts/build-no-hook-bundle.py",
                "--git-executable", str(GIT_EXECUTABLE),
                "--source-repository", str(fixture.root),
                "--source-commit", fixture.commit_oid,
                "--expected-source-tree", fixture.tree_oid,
                "--destination", str(destination),
            ]
            completed = subprocess.run(
                command, cwd=REPOSITORY_ROOT.resolve(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr.decode("utf-8"))
            self.assertEqual(b"", completed.stderr)
            summary = json.loads(completed.stdout)
            envelope = json.loads((destination / BUNDLE_ENVELOPE_NAME).read_bytes())
            self.assertTrue(envelope["complete"])
            self.assertEqual(
                {
                    "profileRuntimeDigest": envelope["profileRuntimeDigest"],
                    "bundleManifestDigest": envelope["bundleManifestDigest"],
                    "archiveSha256": envelope["archive"]["sha256"],
                    "archiveSize": envelope["archive"]["size"],
                    "archiveFilename": envelope["archive"]["filename"],
                    "directoryFileCount": envelope["directory"]["fileCount"],
                    "directoryTotalBytes": envelope["directory"]["totalBytes"],
                },
                summary,
            )
            archive = (destination / summary["archiveFilename"]).read_bytes()
            self.assertEqual(summary["archiveSize"], len(archive))
            self.assertEqual(summary["archiveSha256"], hashlib.sha256(archive).hexdigest())
            before = _directory_files(destination)
            identities = {
                path.relative_to(destination).as_posix(): (
                    path.stat().st_dev, path.stat().st_ino, path.stat().st_mode,
                )
                for path in destination.rglob("*")
            }
            repeated = subprocess.run(
                command, cwd=REPOSITORY_ROOT.resolve(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
                check=False,
            )
            self.assertEqual(1, repeated.returncode)
            self.assertEqual(b"", repeated.stdout)
            self.assertIn(b"destination must be empty", repeated.stderr)
            self.assertEqual(before, _directory_files(destination))
            self.assertEqual(
                identities,
                {
                    path.relative_to(destination).as_posix(): (
                        path.stat().st_dev, path.stat().st_ino, path.stat().st_mode,
                    )
                    for path in destination.rglob("*")
                },
            )

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

    def test_git_children_receive_only_the_credential_free_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            destination = fixture.destination("credential-free-git")
            commit_oid = fixture.commit_oid
            tree_oid = fixture.tree_oid
            observed_environment_names: list[frozenset[str]] = []
            real_popen = subprocess.Popen

            def recording_popen(*args: object, **kwargs: object):
                environment = kwargs.get("env")
                self.assertIsInstance(environment, dict)
                observed_environment_names.append(frozenset(environment))
                return real_popen(*args, **kwargs)

            synthetic_parent = {
                "CODEX_API_KEY": "sentinel-not-a-real-secret",
                "OPENAI_API_KEY": "second-synthetic-value",
                "AXIOM_TEST_TOKEN": "third-synthetic-value",
                "AXIOM_TEST_SECRET": "fourth-synthetic-value",
                "CODEX_HOME": "/synthetic/codex-home",
                "XDG_CONFIG_HOME": "/synthetic/xdg-config",
            }
            with mock.patch.object(bundle_module.os, "environ", synthetic_parent), mock.patch.object(
                bundle_module.subprocess,
                "Popen",
                side_effect=recording_popen,
            ):
                result = build_bundle(
                    fixture.root,
                    commit_oid,
                    tree_oid,
                    destination,
                    git_executable=GIT_EXECUTABLE,
                    schema_path=REPOSITORY_ROOT / "evals/no-hook/bundle-manifest-schema-v1.json",
                    entrypoint_path=REPOSITORY_ROOT / "scripts/build-no-hook-bundle.py",
                    module_path=REPOSITORY_ROOT / "axiom_validation/no_hook_bundle.py",
                )
            self.assertEqual(52, result.directory_file_count)
            self.assertTrue(observed_environment_names)
            allowed = {
                "LANG", "LC_ALL", "NO_COLOR", "GIT_CONFIG_GLOBAL",
                "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_NO_LAZY_FETCH",
                "GIT_OPTIONAL_LOCKS", "GIT_PROTOCOL_FROM_USER", "GIT_TERMINAL_PROMPT",
            }
            self.assertTrue(
                all(names == allowed for names in observed_environment_names)
            )

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
                "_validate_published_outputs_fd",
                side_effect=fail_after_unknown,
            ):
                with self.assertRaisesRegex(BundleContractError, "injected"):
                    _build(fixture, destination)
            self.assertEqual("keep\n", (destination / "caller-arrived.txt").read_text(encoding="utf-8"))
            # Version 2 intentionally retains partial output on failure. This
            # does not delegate normal successful cleanup to the caller: no
            # staging directory or other named temporary artifact is created.
            self.assertTrue((destination / "plugin").is_dir())
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
                "current release v0.10.1 STATIC-ONLY.\n",
                result.stdout,
            )
            self_test = self._run_compatibility_scanner(root, "--self-test")
            self.assertEqual(0, self_test.returncode, self_test.stderr)
            self.assertEqual(
                "Compatibility evidence validation passed: 2 records, "
                "12 negative fixtures, current release v0.10.1 STATIC-ONLY.\n",
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
