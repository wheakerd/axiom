"""Focused tests for draft Release evidence validation and immutable publication."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from axiom_validation.context import RELEASE_VERSION
from axiom_validation.release_evidence import (
    assert_release_absent_from_collection,
    check_publish_workflow_contract,
    classify_publication_state,
    prepare_release_plan,
    render_release_body,
    select_release_from_collection,
    validate_downloaded_observation,
    verify_remote_release_preflight,
    verify_release_snapshot,
)
from axiom_validation.release_versions import PRODUCTION_RELEASE_VERSION_CASES
from tests.test_routing_evals import external_current_observation


COMMIT = "b" * 40
TREE = "c" * 40
TAG = f"v{RELEASE_VERSION}"


def current_observation() -> dict:
    record = external_current_observation()
    record["runId"] = f"codex-v{RELEASE_VERSION.replace('.', '-')}-release-evidence-test"
    record["axiom"] = {
        "version": RELEASE_VERSION,
        "tag": TAG,
        "commit": COMMIT,
        "tree": TREE,
    }
    return record


def write_observation(directory: Path, record: dict) -> tuple[Path, str]:
    payload = (json.dumps(record, indent=2) + "\n").encode("ascii")
    digest = hashlib.sha256(payload).hexdigest()
    path = directory / f"axiom-v{RELEASE_VERSION}-codex-core-v2-{digest}.json"
    path.write_bytes(payload)
    return path, digest


def asset_metadata(path: Path, digest: str, *, asset_id: int = 101) -> dict:
    return {
        "id": asset_id,
        "name": path.name,
        "size": path.stat().st_size,
        "state": "uploaded",
        "digest": f"sha256:{digest}",
        "created_at": "2026-08-26T08:00:00Z",
        "updated_at": "2026-08-26T08:00:00Z",
    }


def release_metadata(
    observation: dict,
    *,
    draft: bool = True,
    immutable: bool = False,
    attestation: dict | None = None,
) -> dict:
    body_failures: list[str] = []
    body = render_release_body(RELEASE_VERSION, body_failures)
    if body is None or body_failures:
        raise AssertionError(body_failures)
    assets = [observation]
    if attestation is not None:
        assets.append(attestation)
    return {
        "id": 501,
        "tag_name": TAG,
        "target_commitish": COMMIT,
        "name": f"Axiom {TAG}",
        "body": body,
        "draft": draft,
        "prerelease": False,
        "immutable": immutable,
        "assets": assets,
    }


def write_json(path: Path, document: object) -> None:
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


class ReleaseEvidenceTests(unittest.TestCase):
    def prepare(self, directory: Path, record: dict | None = None):
        observation_path, digest = write_observation(
            directory, record if record is not None else current_observation()
        )
        observation_asset = asset_metadata(observation_path, digest)
        metadata_path = directory / "release-before.json"
        write_json(metadata_path, release_metadata(observation_asset))
        failures: list[str] = []
        plan = prepare_release_plan(
            metadata_path,
            expected_version=RELEASE_VERSION,
            expected_tag=TAG,
            expected_commit=COMMIT,
            expected_tree=TREE,
            failures=failures,
        )
        self.assertEqual([], failures)
        self.assertIsNotNone(plan)
        return plan, observation_path, observation_asset

    def test_checked_in_publish_workflow_is_narrow_and_pinned(self):
        failures: list[str] = []
        self.assertIsNotNone(check_publish_workflow_contract(failures))
        self.assertEqual([], failures)

    def test_release_body_is_rendered_from_changelog_not_version_notes(self):
        failures: list[str] = []
        body = render_release_body(RELEASE_VERSION, failures)
        self.assertEqual([], failures)
        self.assertIsNotNone(body)
        assert body is not None
        version_notes = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "releases"
            / f"v{RELEASE_VERSION}.md"
        ).read_text(encoding="utf-8")
        self.assertNotEqual(version_notes, body)
        self.assertNotIn("unreleased candidate", body.casefold())
        self.assertIn(
            f"https://github.com/wheakerd/axiom/blob/v{RELEASE_VERSION}/"
            f"docs/releases/v{RELEASE_VERSION}.md",
            body,
        )

    def test_render_body_cli_emits_exact_current_body(self):
        failures: list[str] = []
        expected = render_release_body(RELEASE_VERSION, failures)
        self.assertEqual([], failures)
        result = subprocess.run(
            [
                sys.executable,
                "scripts/check-release-evidence.py",
                "render-body",
                "--expected-version",
                RELEASE_VERSION,
            ],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(expected, result.stdout)

    def test_fix_forward_release_body_contract_rejects_missing_or_candidate_text(self):
        valid = """# Changelog

## 0.10.1 - unreleased

### Fixed

- Fixed the [guide](docs/guides/getting-started.md).

### Behavioral impact

- Existing behavior is unchanged.

### Required action

- None.
"""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            changelog = root / "CHANGELOG.md"
            for case_id, payload, expected_failure in (
                (
                    "missing-action",
                    valid.replace("### Required action\n\n- None.\n", ""),
                    "missing required sections",
                ),
                (
                    "candidate-state",
                    valid.replace("- None.", "- GitHub Release does not exist."),
                    "candidate-only publication text",
                ),
                (
                    "candidate-word",
                    valid.replace("- None.", "- This candidate needs no action."),
                    "pre-publication text",
                ),
            ):
                with self.subTest(case_id=case_id):
                    changelog.write_text(payload, encoding="utf-8")
                    failures: list[str] = []
                    self.assertIsNone(
                        render_release_body("0.10.1", failures, root=root)
                    )
                    self.assertTrue(
                        any(expected_failure in failure for failure in failures),
                        failures,
                    )

            changelog.write_text(valid, encoding="utf-8")
            failures = []
            body = render_release_body("0.10.1", failures, root=root)
            self.assertEqual([], failures)
            self.assertIsNotNone(body)
            assert body is not None
            self.assertIn("## Fixed", body)
            self.assertIn(
                "https://github.com/wheakerd/axiom/blob/v0.10.1/"
                "docs/guides/getting-started.md",
                body,
            )

    def test_publish_workflow_contract_rejects_an_appended_command(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "publish-immutable-release.yml"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            modified = Path(temporary_directory) / "publish.yml"
            modified.write_text(
                workflow.read_text(encoding="utf-8") + "          curl https://example.invalid\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            check_publish_workflow_contract(failures, modified)
            self.assertTrue(any("complete publication command" in item for item in failures))

    def test_publish_workflow_contract_rejects_a_broader_version_gate(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "publish-immutable-release.yml"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            modified = Path(temporary_directory) / "publish.yml"
            modified.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    '[[ "$RELEASE_TAG" =~ ^v(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$ ]]',
                    '[[ "$RELEASE_TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+.*$ ]]',
                    1,
                ),
                encoding="utf-8",
            )
            failures: list[str] = []
            check_publish_workflow_contract(failures, modified)
            self.assertTrue(any("canonical stable" in item for item in failures))

    def test_release_subject_rejects_every_unsupported_production_version(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            observation_path, digest = write_observation(directory, current_observation())
            metadata_path = directory / "release-before.json"
            write_json(
                metadata_path,
                release_metadata(asset_metadata(observation_path, digest)),
            )
            for case_id, version, accepted in PRODUCTION_RELEASE_VERSION_CASES:
                if accepted:
                    continue
                with self.subTest(case_id=case_id):
                    failures: list[str] = []
                    plan = prepare_release_plan(
                        metadata_path,
                        expected_version=version,
                        expected_tag=f"v{version}",
                        expected_commit=COMMIT,
                        expected_tree=TREE,
                        failures=failures,
                    )
                    self.assertIsNone(plan)
                    self.assertTrue(
                        any("stable numeric production" in item for item in failures),
                        failures,
                    )

    def test_publish_workflow_avoids_admin_only_settings_endpoint(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "publish-immutable-release.yml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("/immutable-releases", workflow)
        self.assertIn("git/ref/tags/$RELEASE_TAG", workflow)
        self.assertIn("publication-state", workflow)
        self.assertIn("assert-absent", workflow)

    def test_release_collection_selection_and_remote_preflight(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            observation_path, digest = write_observation(directory, current_observation())
            release = release_metadata(asset_metadata(observation_path, digest))
            collection = directory / "collection.json"
            selected = directory / "selected.json"
            write_json(collection, [[{"tag_name": "v0.0.1"}, release]])
            failures: list[str] = []
            self.assertEqual(
                release,
                select_release_from_collection(
                    collection, selected, expected_tag=TAG, failures=failures
                ),
            )
            self.assertEqual([], failures)

            repository = directory / "repository.json"
            latest_release = directory / "latest.json"
            main_ref = directory / "main-ref.json"
            tag_ref = directory / "tag-ref.json"
            history = directory / "history.json"
            commit_metadata = directory / "commit.json"
            signature = directory / "signature.json"
            write_json(repository, {"default_branch": "main"})
            write_json(
                latest_release,
                {"tag_name": "v0.8.5", "draft": False, "prerelease": False},
            )
            commit = {
                "sha": COMMIT,
                "commit": {"verification": {"verified": True, "reason": "valid"}},
            }
            write_json(
                main_ref,
                {"ref": "refs/heads/main", "object": {"type": "commit", "sha": COMMIT}},
            )
            write_json(
                tag_ref,
                {"ref": f"refs/tags/{TAG}", "object": {"type": "commit", "sha": COMMIT}},
            )
            write_json(
                history,
                {
                    "status": "identical",
                    "merge_base_commit": {"sha": COMMIT},
                    "base_commit": {"sha": COMMIT},
                },
            )
            write_json(commit_metadata, commit)
            write_json(
                signature,
                {
                    "data": {
                        "repository": {
                            "object": {
                                "oid": COMMIT,
                                "signature": {
                                    "isValid": True,
                                    "state": "VALID",
                                    "wasSignedByGitHub": True,
                                },
                            }
                        }
                    }
                },
            )
            failures = []
            verify_remote_release_preflight(
                repository,
                latest_release,
                main_ref,
                tag_ref,
                history,
                commit_metadata,
                signature,
                expected_commit=COMMIT,
                expected_tag=TAG,
                require_main_tip=True,
                failures=failures,
            )
            self.assertEqual([], failures)

            ahead_commit = "d" * 40
            write_json(
                main_ref,
                {
                    "ref": "refs/heads/main",
                    "object": {"type": "commit", "sha": ahead_commit},
                },
            )
            write_json(
                history,
                {
                    "status": "ahead",
                    "merge_base_commit": {"sha": COMMIT},
                    "base_commit": {"sha": COMMIT},
                },
            )
            failures = []
            verify_remote_release_preflight(
                repository,
                latest_release,
                main_ref,
                tag_ref,
                history,
                commit_metadata,
                signature,
                expected_commit=COMMIT,
                expected_tag=TAG,
                require_main_tip=False,
                failures=failures,
            )
            self.assertEqual([], failures)
            failures = []
            verify_remote_release_preflight(
                repository,
                latest_release,
                main_ref,
                tag_ref,
                history,
                commit_metadata,
                signature,
                expected_commit=COMMIT,
                expected_tag=TAG,
                require_main_tip=True,
                failures=failures,
            )
            self.assertTrue(any("main tip" in item for item in failures), failures)
            write_json(
                main_ref,
                {"ref": "refs/heads/main", "object": {"type": "commit", "sha": COMMIT}},
            )
            write_json(
                history,
                {
                    "status": "identical",
                    "merge_base_commit": {"sha": COMMIT},
                    "base_commit": {"sha": COMMIT},
                },
            )

            write_json(
                tag_ref,
                {"ref": f"refs/tags/{TAG}", "object": {"type": "tag", "sha": COMMIT}},
            )
            failures = []
            verify_remote_release_preflight(
                repository,
                latest_release,
                main_ref,
                tag_ref,
                history,
                commit_metadata,
                signature,
                expected_commit=COMMIT,
                expected_tag=TAG,
                require_main_tip=True,
                failures=failures,
            )
            self.assertTrue(any("lightweight ref" in item for item in failures), failures)

            write_json(
                tag_ref,
                {"ref": f"refs/tags/{TAG}", "object": {"type": "commit", "sha": COMMIT}},
            )
            major, minor, patch = (int(part) for part in RELEASE_VERSION.split("."))
            write_json(
                latest_release,
                {
                    "tag_name": f"v{major}.{minor}.{patch + 1}",
                    "draft": False,
                    "prerelease": False,
                },
            )
            failures = []
            verify_remote_release_preflight(
                repository,
                latest_release,
                main_ref,
                tag_ref,
                history,
                commit_metadata,
                signature,
                expected_commit=COMMIT,
                expected_tag=TAG,
                require_main_tip=True,
                failures=failures,
            )
            self.assertTrue(any("must not regress" in item for item in failures), failures)

    def test_publication_state_and_bounded_cleanup_identity(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            plan, observation_path, observation_asset = self.prepare(directory)
            failures: list[str] = []
            attestation_path = validate_downloaded_observation(
                plan,
                observation_path,
                attestation_directory=directory,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertIsNotNone(attestation_path)
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(
                attestation_path, attestation_digest, asset_id=102
            )
            published = directory / "published.json"
            write_json(
                published,
                release_metadata(
                    observation_asset,
                    draft=False,
                    immutable=False,
                    attestation=attestation_asset,
                ),
            )
            failures = []
            self.assertEqual(
                "mutable",
                classify_publication_state(plan, published, failures),
            )
            self.assertEqual([], failures)

            failures = []
            mutable_plan = prepare_release_plan(
                published,
                expected_version=RELEASE_VERSION,
                expected_tag=TAG,
                expected_commit=COMMIT,
                expected_tree=TREE,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertIsNotNone(mutable_plan)
            self.assertEqual("published-mutable", mutable_plan["phase"])

            immutable_document = release_metadata(
                observation_asset,
                draft=False,
                immutable=True,
                attestation=attestation_asset,
            )
            write_json(published, immutable_document)
            failures = []
            self.assertEqual(
                "immutable",
                classify_publication_state(plan, published, failures),
            )
            self.assertEqual([], failures)

            wrong_release = dict(immutable_document)
            wrong_release["id"] = 999
            write_json(published, wrong_release)
            failures = []
            self.assertIsNone(classify_publication_state(plan, published, failures))
            self.assertTrue(any("release.id" in item for item in failures), failures)

            collection = directory / "after-cleanup.json"
            write_json(collection, [[{"id": 400, "tag_name": "v0.8.5"}]])
            failures = []
            assert_release_absent_from_collection(collection, plan, failures)
            self.assertEqual([], failures)

            write_json(collection, [[{"id": 501, "tag_name": TAG}]])
            failures = []
            assert_release_absent_from_collection(collection, plan, failures)
            self.assertTrue(any("did not remove" in item for item in failures), failures)

    def test_stable_cli_prepares_emits_validates_and_verifies(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            observation_path, digest = write_observation(directory, current_observation())
            observation_asset = asset_metadata(observation_path, digest)
            before = directory / "release-before.json"
            plan = directory / "plan.json"
            write_json(before, release_metadata(observation_asset))
            script = Path(__file__).resolve().parents[1] / "scripts" / "check-release-evidence.py"

            def run(*arguments: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(script), *arguments],
                    check=False,
                    capture_output=True,
                    text=True,
                )

            prepared = run(
                "prepare",
                "--release-metadata",
                str(before),
                "--plan-output",
                str(plan),
                "--expected-version",
                RELEASE_VERSION,
                "--expected-tag",
                TAG,
                "--expected-commit",
                COMMIT,
                "--expected-tree",
                TREE,
            )
            self.assertEqual(0, prepared.returncode, prepared.stderr)
            emitted = run("emit", "--plan", str(plan), "--field", "asset-id")
            self.assertEqual(0, emitted.returncode, emitted.stderr)
            self.assertEqual("101", emitted.stdout.strip())
            validated = run(
                "validate",
                "--plan",
                str(plan),
                "--asset",
                str(observation_path),
                "--attestation-directory",
                str(directory),
            )
            self.assertEqual(0, validated.returncode, validated.stderr)
            attestation_path = Path(validated.stdout.strip())
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(attestation_path, attestation_digest, asset_id=102)
            after_upload = directory / "release-after-upload.json"
            write_json(after_upload, release_metadata(observation_asset, attestation=attestation_asset))
            verified = run(
                "verify",
                "--plan",
                str(plan),
                "--release-metadata",
                str(after_upload),
                "--asset",
                str(observation_path),
                "--attestation",
                str(attestation_path),
            )
            self.assertEqual(0, verified.returncode, verified.stderr)

            final = directory / "release-final.json"
            latest = directory / "release-latest.json"
            final_document = release_metadata(
                observation_asset,
                draft=False,
                immutable=True,
                attestation=attestation_asset,
            )
            write_json(final, final_document)
            write_json(latest, final_document)
            finalized = run(
                "verify",
                "--plan",
                str(plan),
                "--release-metadata",
                str(final),
                "--asset",
                str(observation_path),
                "--attestation",
                str(attestation_path),
                "--prepublish-release-metadata",
                str(after_upload),
                "--latest-release-metadata",
                str(latest),
                "--final",
            )
            self.assertEqual(0, finalized.returncode, finalized.stderr)

    def test_draft_asset_attestation_and_final_immutable_snapshot_pass(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            plan, observation_path, observation_asset = self.prepare(directory)
            failures: list[str] = []
            attestation_path = validate_downloaded_observation(
                plan,
                observation_path,
                attestation_directory=directory,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertIsNotNone(attestation_path)
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(
                attestation_path, attestation_digest, asset_id=102
            )

            after_upload = directory / "release-after-upload.json"
            write_json(
                after_upload,
                release_metadata(observation_asset, attestation=attestation_asset),
            )
            failures = []
            verify_release_snapshot(
                plan,
                after_upload,
                observation_path,
                attestation_path,
                final=False,
                latest_metadata_path=None,
                prepublish_metadata_path=None,
                failures=failures,
            )
            self.assertEqual([], failures)

            final = directory / "release-final.json"
            latest = directory / "release-latest.json"
            final_document = release_metadata(
                observation_asset,
                draft=False,
                immutable=True,
                attestation=attestation_asset,
            )
            write_json(final, final_document)
            write_json(latest, final_document)
            failures = []
            verify_release_snapshot(
                plan,
                final,
                observation_path,
                attestation_path,
                final=True,
                latest_metadata_path=latest,
                prepublish_metadata_path=after_upload,
                failures=failures,
            )
            self.assertEqual([], failures)

    def test_existing_draft_attestation_and_final_only_recovery_pass(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            initial_plan, observation_path, observation_asset = self.prepare(directory)
            failures: list[str] = []
            attestation_path = validate_downloaded_observation(
                initial_plan,
                observation_path,
                attestation_directory=directory,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertIsNotNone(attestation_path)
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(
                attestation_path, attestation_digest, asset_id=102
            )

            resumed_draft = directory / "resumed-draft.json"
            write_json(
                resumed_draft,
                release_metadata(observation_asset, attestation=attestation_asset),
            )
            failures = []
            resumed_plan = prepare_release_plan(
                resumed_draft,
                expected_version=RELEASE_VERSION,
                expected_tag=TAG,
                expected_commit=COMMIT,
                expected_tree=TREE,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertEqual("draft", resumed_plan["phase"])
            self.assertEqual(attestation_asset["id"], resumed_plan["attestationAsset"]["id"])

            final = directory / "final-recovery.json"
            final_document = release_metadata(
                observation_asset,
                draft=False,
                immutable=True,
                attestation=attestation_asset,
            )
            write_json(final, final_document)
            failures = []
            final_plan = prepare_release_plan(
                final,
                expected_version=RELEASE_VERSION,
                expected_tag=TAG,
                expected_commit=COMMIT,
                expected_tree=TREE,
                failures=failures,
            )
            self.assertEqual([], failures)
            self.assertEqual("final", final_plan["phase"])
            failures = []
            verify_release_snapshot(
                final_plan,
                final,
                observation_path,
                attestation_path,
                final=True,
                latest_metadata_path=final,
                prepublish_metadata_path=None,
                failures=failures,
            )
            self.assertEqual([], failures)

    def test_missing_duplicate_malformed_and_digest_mismatched_assets_fail(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            observation_path, digest = write_observation(directory, current_observation())
            valid_asset = asset_metadata(observation_path, digest)
            fixtures = []
            missing = release_metadata(valid_asset)
            missing["assets"] = []
            fixtures.append(("missing", missing, "exactly one"))
            duplicate = release_metadata(valid_asset)
            duplicate["assets"].append({**valid_asset, "id": 102})
            fixtures.append(("duplicate", duplicate, "exactly one"))
            malformed = release_metadata({**valid_asset, "name": f"axiom-v{RELEASE_VERSION}-codex-core-v2-bad.json"})
            fixtures.append(("malformed", malformed, "full lowercase SHA-256"))
            mismatched = release_metadata({**valid_asset, "digest": f"sha256:{'0' * 64}"})
            fixtures.append(("digest", mismatched, "GitHub digest"))
            unexposed = release_metadata({**valid_asset, "digest": None})
            fixtures.append(("unexposed-digest", unexposed, "exposed lowercase SHA-256"))
            unrecognized = release_metadata(valid_asset)
            unrecognized["assets"].append(
                {**valid_asset, "id": 777, "name": "unexpected-evidence.json"}
            )
            fixtures.append(("unrecognized", unrecognized, "unrecognized evidence asset"))
            wrong_body = release_metadata(valid_asset)
            wrong_body["body"] = ""
            fixtures.append(("release-body", wrong_body, "release.body"))

            for name, metadata, expected in fixtures:
                with self.subTest(name=name):
                    metadata_path = directory / f"{name}.json"
                    write_json(metadata_path, metadata)
                    failures: list[str] = []
                    plan = prepare_release_plan(
                        metadata_path,
                        expected_version=RELEASE_VERSION,
                        expected_tag=TAG,
                        expected_commit=COMMIT,
                        expected_tree=TREE,
                        failures=failures,
                    )
                    if name == "digest":
                        self.assertIsNotNone(plan)
                        failures = []
                        validate_downloaded_observation(
                            plan,
                            observation_path,
                            attestation_directory=directory,
                            failures=failures,
                        )
                    else:
                        self.assertIsNone(plan)
                    self.assertTrue(any(expected in failure for failure in failures), failures)

    def test_modified_download_and_replaced_release_asset_fail(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            plan, observation_path, observation_asset = self.prepare(directory)
            observation_path.write_bytes(observation_path.read_bytes() + b" ")
            failures: list[str] = []
            self.assertIsNone(
                validate_downloaded_observation(
                    plan,
                    observation_path,
                    attestation_directory=directory,
                    failures=failures,
                )
            )
            self.assertTrue(any("SHA-256" in failure for failure in failures), failures)

            observation_path, _ = write_observation(directory, current_observation())
            failures = []
            attestation_path = validate_downloaded_observation(
                plan,
                observation_path,
                attestation_directory=directory,
                failures=failures,
            )
            self.assertEqual([], failures)
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(
                attestation_path, attestation_digest, asset_id=102
            )
            replaced_asset = {**observation_asset, "id": 999}
            current = directory / "release-replaced.json"
            write_json(
                current,
                release_metadata(replaced_asset, attestation=attestation_asset),
            )
            failures = []
            verify_release_snapshot(
                plan,
                current,
                observation_path,
                attestation_path,
                final=False,
                latest_metadata_path=None,
                prepublish_metadata_path=None,
                failures=failures,
            )
            self.assertTrue(any("metadata changed" in failure for failure in failures), failures)

    def test_incomplete_failed_retrying_mutating_and_wrong_subject_observations_fail(self):
        mutations = []
        incomplete = current_observation()
        incomplete["cases"].pop()
        mutations.append(("incomplete", incomplete))
        failed = current_observation()
        failed["cases"][0]["status"] = "fail"
        mutations.append(("failed", failed))
        retrying = current_observation()
        retrying["run"]["repeatCount"] = 2
        mutations.append(("retrying", retrying))
        mutating = current_observation()
        mutating["cases"][0]["mutationAttempted"] = True
        mutating["summary"]["mutationAttempts"] = 1
        mutations.append(("mutating", mutating))
        wrong_subject = current_observation()
        wrong_subject["axiom"]["tree"] = "d" * 40
        mutations.append(("wrong-subject", wrong_subject))

        for name, record in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary_directory:
                directory = Path(temporary_directory)
                plan, observation_path, _ = self.prepare(directory, record)
                failures: list[str] = []
                self.assertIsNone(
                    validate_downloaded_observation(
                        plan,
                        observation_path,
                        attestation_directory=directory,
                        failures=failures,
                    )
                )
                self.assertTrue(failures, name)

    def test_final_release_must_be_immutable_and_latest(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            plan, observation_path, observation_asset = self.prepare(directory)
            failures: list[str] = []
            attestation_path = validate_downloaded_observation(
                plan,
                observation_path,
                attestation_directory=directory,
                failures=failures,
            )
            attestation_digest = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
            attestation_asset = asset_metadata(attestation_path, attestation_digest, asset_id=102)
            final = directory / "release-final.json"
            latest = directory / "release-latest.json"
            write_json(
                final,
                release_metadata(
                    observation_asset,
                    draft=False,
                    immutable=False,
                    attestation=attestation_asset,
                ),
            )
            wrong_latest = release_metadata(
                observation_asset,
                draft=False,
                immutable=True,
                attestation=attestation_asset,
            )
            wrong_latest["id"] = 999
            write_json(latest, wrong_latest)
            prepublish = directory / "release-prepublish.json"
            write_json(
                prepublish,
                release_metadata(observation_asset, attestation=attestation_asset),
            )
            failures = []
            verify_release_snapshot(
                plan,
                final,
                observation_path,
                attestation_path,
                final=True,
                latest_metadata_path=latest,
                prepublish_metadata_path=prepublish,
                failures=failures,
            )
            self.assertTrue(any("immutable=true" in failure for failure in failures), failures)
            self.assertTrue(any("GitHub Latest" in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
