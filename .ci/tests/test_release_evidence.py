"""Focused tests for the publisher's Draft verification and evidence asset."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from axiom_validation.release import canonical_json, policy_asset
from axiom_validation.release_evidence import (
    assert_release_absent_from_collection,
    check_publish_workflow_contract,
    classify_publication_state,
    emit_evidence,
    evidence_document,
    load_release_plan,
    prepare_release_plan,
    select_release_from_collection,
    validate_subject,
    verify_release_snapshot,
    verify_remote_release_preflight,
)


NOTES = "Fixed the startup gate.\n\nhttps://github.com/wheakerd/axiom/compare/v1.2.2...v1.2.3\n"
ZIP_BYTES = b"PK\x03\x04 deterministic plugin zip fixture"
COMMIT = "a" * 40
TREE = "b" * 40
RELEASE_COMMIT = "c" * 40
RELEASE_TREE = "d" * 40
TAG_OBJECT = "e" * 40


def subject() -> dict:
    return {
        "bootstrap": False,
        "version": "1.2.3",
        "tag": "v1.2.3",
        "tagObject": {"type": "tag", "sha": TAG_OBJECT},
        "commit": COMMIT,
        "tree": TREE,
        "releaseCommit": RELEASE_COMMIT,
        "releaseTree": RELEASE_TREE,
        "zip": {
            "name": "axiom-v1.2.3-plugin.zip",
            "sha256": hashlib.sha256(ZIP_BYTES).hexdigest(),
            "size": len(ZIP_BYTES),
        },
        "runtimeDigest": "sha256:" + "f" * 64,
        "previousTag": "v1.2.2",
        "notesSha256": hashlib.sha256(NOTES.encode("utf-8")).hexdigest(),
    }


def asset(asset_id: int, name: str, data: bytes) -> dict:
    return {
        "id": asset_id,
        "name": name,
        "size": len(data),
        "state": "uploaded",
        "digest": f"sha256:{hashlib.sha256(data).hexdigest()}",
        "created_at": "2026-11-07T00:00:00Z",
        "updated_at": "2026-11-07T00:00:00Z",
    }


class Fixture:
    """Files for one Draft: the policy, zip, and optional evidence asset."""

    def __init__(self, directory: Path, release_subject: dict | None = None) -> None:
        self.directory = directory
        self.subject = release_subject or subject()
        self.policy_name, self.policy_bytes = policy_asset(self.subject)
        self.policy = directory / self.policy_name
        self.policy.write_bytes(self.policy_bytes)
        self.zip = directory / self.subject["zip"]["name"]
        self.zip.write_bytes(ZIP_BYTES)
        self.expected_zip = directory / "expected.zip"
        self.expected_zip.write_bytes(ZIP_BYTES)
        self.subject_path = directory / "subject.json"
        self.subject_path.write_bytes(canonical_json(self.subject))

    def release(self, *, draft: bool = True, immutable: bool = False, evidence: Path | None = None,
                body: str = NOTES) -> dict:
        assets = [
            asset(11, self.policy_name, self.policy_bytes),
            asset(12, self.subject["zip"]["name"], ZIP_BYTES),
        ]
        if evidence is not None:
            assets.append(asset(13, evidence.name, evidence.read_bytes()))
        return {
            "id": 700,
            "tag_name": self.subject["tag"],
            "target_commitish": self.subject["commit"],
            "name": self.subject["tag"],
            "body": body,
            "draft": draft,
            "prerelease": False,
            "immutable": immutable,
            "assets": assets,
        }

    def write(self, name: str, document: object) -> Path:
        path = self.directory / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def plan(self, release: dict) -> dict:
        failures: list[str] = []
        plan = prepare_release_plan(self.write("release.json", release), self.subject, failures)
        if plan is None or failures:
            raise AssertionError(failures)
        return plan

    def evidence(self, plan: dict, directory: Path) -> Path:
        failures: list[str] = []
        path = emit_evidence(
            plan, self.policy, self.zip, self.expected_zip,
            evidence_directory=directory, failures=failures, root=self.directory / "repository",
        )
        if path is None or failures:
            raise AssertionError(failures)
        return path


class ReleaseEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "repository").mkdir()
        self.fixture = Fixture(self.root)
        self.evidence_directory = self.root / "evidence"
        self.evidence_directory.mkdir()

    def test_checked_in_publisher_workflow_contract(self):
        failures: list[str] = []
        self.assertIsNotNone(check_publish_workflow_contract(failures))
        self.assertEqual([], failures)

    def test_publisher_workflow_rejects_a_changed_command_or_trigger(self):
        source = Path(__file__).resolve().parents[2] / ".github/workflows/publish-immutable-release.yml"
        text = source.read_text(encoding="utf-8")
        for label, old, new, expected in (
            ("anchor", "check-release-evidence.py assert-absent", "check-release-evidence.py removed",
             "missing required publication anchor"),
            ("trigger", "on:\n  workflow_dispatch:", "on:\n  pull_request:\n  workflow_dispatch:",
             "workflow_dispatch-only"),
        ):
            with self.subTest(label=label):
                path = self.root / f"{label}.yml"
                path.write_text(text.replace(old, new, 1), encoding="utf-8")
                failures: list[str] = []
                check_publish_workflow_contract(failures, path)
                self.assertTrue(any(expected in failure for failure in failures), failures)
                self.assertTrue(any("command contract changed" in failure for failure in failures), failures)

    def test_subject_must_be_complete_and_consistent(self):
        self.assertTrue(validate_subject(subject(), []))
        cases = {
            "missing-field": (lambda value: value.pop("releaseTree"), "unexpected or missing fields"),
            "tag-mismatch": (lambda value: value.update(tag="v1.2.4"), "tag must be v<version>"),
            "lightweight-tag-elsewhere": (
                lambda value: value.update(tagObject={"type": "commit", "sha": "9" * 40}),
                "lightweight release tag must point at the subject commit",
            ),
            "zip-name": (lambda value: value["zip"].update(name="plugin.zip"), "subject zip must name"),
            "previous-not-older": (lambda value: value.update(previousTag="v1.2.3"), "older release tag"),
            "digest": (lambda value: value.update(runtimeDigest="0" * 64), "runtimeDigest"),
            "bootstrap": (lambda value: value.update(bootstrap="yes"), "bootstrap must be a boolean"),
        }
        for label, (mutate, expected) in cases.items():
            with self.subTest(label=label):
                value = subject()
                mutate(value)
                failures: list[str] = []
                self.assertFalse(validate_subject(value, failures))
                self.assertTrue(any(expected in failure for failure in failures), failures)

    def test_draft_plan_validates_assets_and_emits_deterministic_evidence(self):
        plan = self.fixture.plan(self.fixture.release())
        self.assertEqual("draft", plan["phase"])
        self.assertIsNone(plan["evidenceAsset"])
        first = self.fixture.evidence(plan, self.evidence_directory)
        second_directory = self.root / "second"
        second_directory.mkdir()
        second = self.fixture.evidence(plan, second_directory)
        self.assertEqual(first.name, second.name)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        document = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(evidence_document(plan), document)
        self.assertEqual("v1.2.3", document["release"]["tag"])
        self.assertEqual(COMMIT, document["release"]["commit"])
        self.assertEqual(RELEASE_COMMIT, document["release"]["releaseCommit"])
        self.assertEqual(RELEASE_TREE, document["release"]["releaseTree"])
        self.assertEqual(subject()["zip"]["sha256"], document["release"]["zipSha256"])
        self.assertEqual(subject()["runtimeDigest"], document["runtimeContract"]["digest"])
        self.assertEqual(subject()["notesSha256"], document["release"]["notesSha256"])
        self.assertIs(False, document["release"]["bootstrap"])
        self.assertEqual(f"axiom-v1.2.3-release-evidence-{hashlib.sha256(first.read_bytes()).hexdigest()}.json", first.name)

    def test_evidence_is_refused_inside_the_checked_in_tree(self):
        plan = self.fixture.plan(self.fixture.release())
        failures: list[str] = []
        inside = self.root / "repository" / "out"
        inside.mkdir()
        self.assertIsNone(
            emit_evidence(plan, self.fixture.policy, self.fixture.zip, self.fixture.expected_zip,
                          evidence_directory=inside, failures=failures, root=self.root / "repository")
        )
        self.assertTrue(any("outside the checked-in tree" in failure for failure in failures), failures)

    def test_tampered_policy_zip_or_body_is_rejected(self):
        plan = self.fixture.plan(self.fixture.release())
        tampered_zip = self.root / "tampered" / self.fixture.zip.name
        tampered_zip.parent.mkdir()
        tampered_zip.write_bytes(ZIP_BYTES[:-1] + b"X")
        failures: list[str] = []
        emit_evidence(plan, self.fixture.policy, tampered_zip, self.fixture.expected_zip,
                      evidence_directory=self.evidence_directory, failures=failures, root=self.root / "repository")
        self.assertTrue(any("differs from the zip built from the tag" in failure for failure in failures), failures)

        other = subject()
        other["releaseCommit"] = "9" * 40
        other_fixture_directory = self.root / "other"
        other_fixture_directory.mkdir()
        other_fixture = Fixture(other_fixture_directory, other)
        failures = []
        emit_evidence(plan, other_fixture.policy, self.fixture.zip, self.fixture.expected_zip,
                      evidence_directory=self.evidence_directory, failures=failures, root=self.root / "repository")
        self.assertTrue(any("filename does not match" in failure or "exactly the record" in failure
                            for failure in failures), failures)

        failures = []
        result = prepare_release_plan(
            self.fixture.write("edited.json", self.fixture.release(body=NOTES + "edited\n")),
            self.fixture.subject, failures,
        )
        self.assertIsNone(result)
        self.assertTrue(any("release.body must be exactly the notes" in failure for failure in failures), failures)

    def test_unexpected_asset_or_target_is_rejected(self):
        release = self.fixture.release()
        release["assets"].append(asset(99, "extra.txt", b"extra"))
        failures: list[str] = []
        self.assertIsNone(prepare_release_plan(self.fixture.write("extra.json", release), self.fixture.subject, failures))
        self.assertTrue(any("unrecognized asset" in failure for failure in failures), failures)
        release = self.fixture.release()
        release["target_commitish"] = RELEASE_COMMIT
        failures = []
        self.assertIsNone(prepare_release_plan(self.fixture.write("target.json", release), self.fixture.subject, failures))
        self.assertTrue(any("release.target_commitish" in failure for failure in failures), failures)

    def test_verify_draft_then_final_and_latest(self):
        draft_plan = self.fixture.plan(self.fixture.release())
        evidence = self.fixture.evidence(draft_plan, self.evidence_directory)
        draft = self.fixture.release(evidence=evidence)
        current_plan = self.fixture.plan(draft)
        self.assertEqual(evidence.name, current_plan["evidenceAsset"]["name"])
        draft_path = self.fixture.write("draft.json", draft)
        failures: list[str] = []
        verify_release_snapshot(current_plan, draft_path, self.fixture.policy, self.fixture.zip,
                                self.fixture.expected_zip, evidence, final=False,
                                latest_metadata_path=None, prepublish_metadata_path=None, failures=failures)
        self.assertEqual([], failures)
        final = self.fixture.release(draft=False, immutable=True, evidence=evidence)
        final_path = self.fixture.write("final.json", final)
        latest_path = self.fixture.write("latest.json", final)
        failures = []
        verify_release_snapshot(current_plan, final_path, self.fixture.policy, self.fixture.zip,
                                self.fixture.expected_zip, evidence, final=True,
                                latest_metadata_path=latest_path, prepublish_metadata_path=draft_path,
                                failures=failures)
        self.assertEqual([], failures)
        stale_latest = dict(final, id=699, tag_name="v1.2.2")
        failures = []
        verify_release_snapshot(current_plan, final_path, self.fixture.policy, self.fixture.zip,
                                self.fixture.expected_zip, evidence, final=True,
                                latest_metadata_path=self.fixture.write("stale.json", stale_latest),
                                prepublish_metadata_path=draft_path, failures=failures)
        self.assertTrue(any("GitHub Latest does not identify" in failure for failure in failures), failures)

    def test_plan_round_trip_and_publication_state(self):
        plan = self.fixture.plan(self.fixture.release())
        path = self.root / "plan.json"
        path.write_bytes(canonical_json(plan))
        failures: list[str] = []
        self.assertEqual(plan, load_release_plan(path, failures))
        self.assertEqual([], failures)
        broken = copy.deepcopy(plan)
        broken["release"]["notesSha256"] = "0" * 64
        path.write_bytes(canonical_json(broken))
        failures = []
        self.assertIsNone(load_release_plan(path, failures))
        self.assertTrue(failures)
        for immutable, expected in ((True, "immutable"), (False, "mutable")):
            with self.subTest(immutable=immutable):
                published = self.fixture.release(draft=False, immutable=immutable)
                failures = []
                state = classify_publication_state(plan, self.fixture.write("published.json", published), failures)
                self.assertEqual(expected, state, failures)

    def test_cleanup_requires_the_frozen_release_to_be_gone(self):
        plan = self.fixture.plan(self.fixture.release())
        failures: list[str] = []
        assert_release_absent_from_collection(self.fixture.write("empty.json", [[]]), plan, failures)
        self.assertEqual([], failures)
        assert_release_absent_from_collection(
            self.fixture.write("present.json", [[{"id": 700, "tag_name": "v1.2.3"}]]), plan, failures
        )
        self.assertTrue(any("did not remove" in failure for failure in failures), failures)

    def test_select_requires_exactly_one_release(self):
        output = self.root / "selected.json"
        failures: list[str] = []
        select_release_from_collection(
            self.fixture.write("collection.json", [[self.fixture.release()]]), output,
            expected_tag="v1.2.3", failures=failures,
        )
        self.assertEqual([], failures)
        failures = []
        select_release_from_collection(
            self.fixture.write("double.json", [[self.fixture.release(), self.fixture.release()]]), output,
            expected_tag="v1.2.3", failures=failures,
        )
        self.assertTrue(failures)

    def preflight(self, **changes: object) -> list[str]:
        signature = {"data": {"repository": {"object": {
            "oid": COMMIT, "signature": {"isValid": True, "state": "VALID", "wasSignedByGitHub": True}}}}}
        release_signature = copy.deepcopy(signature)
        release_signature["data"]["repository"]["object"]["oid"] = RELEASE_COMMIT
        documents = {
            "repository": {"default_branch": "main"},
            "latest": {"tag_name": "v1.2.2", "draft": False, "prerelease": False},
            "main": {"ref": "refs/heads/main", "object": {"type": "commit", "sha": "1" * 40}},
            "tag": {"ref": "refs/tags/v1.2.3", "object": {"type": "tag", "sha": TAG_OBJECT}},
            "release": {"ref": "refs/heads/release", "object": {"type": "commit", "sha": RELEASE_COMMIT}},
            "history": {"merge_base_commit": {"sha": COMMIT}, "base_commit": {"sha": COMMIT}, "status": "ahead"},
            "commit": {"sha": COMMIT, "commit": {"verification": {"verified": True, "reason": "valid"}}},
            "commit_signature": signature,
            "release_signature": release_signature,
        }
        documents.update(changes)
        paths = {name: self.fixture.write(f"preflight-{name}.json", value) for name, value in documents.items()}
        failures: list[str] = []
        verify_remote_release_preflight(
            repository_metadata_path=paths["repository"],
            latest_release_path=paths["latest"],
            main_ref_path=paths["main"],
            tag_ref_path=paths["tag"],
            release_ref_path=paths["release"],
            history_comparison_path=paths["history"],
            commit_metadata_path=paths["commit"],
            commit_signature_path=paths["commit_signature"],
            release_signature_path=paths["release_signature"],
            subject=self.fixture.subject,
            failures=failures,
        )
        return failures

    def test_preflight_accepts_live_state_and_rejects_each_drift(self):
        self.assertEqual([], self.preflight())
        unsigned = {"data": {"repository": {"object": {
            "oid": RELEASE_COMMIT, "signature": {"isValid": True, "state": "VALID", "wasSignedByGitHub": False}}}}}
        cases = {
            "tag-moved": ({"tag": {"ref": "refs/tags/v1.2.3", "object": {"type": "tag", "sha": "9" * 40}}},
                          "still point at the subject tag object"),
            "release-moved": ({"release": {"ref": "refs/heads/release", "object": {"type": "commit", "sha": "9" * 40}}},
                              "release branch head must be the subject release commit"),
            "off-main": ({"history": {"merge_base_commit": {"sha": "9" * 40}, "base_commit": {"sha": COMMIT},
                                      "status": "diverged"}}, "live main history"),
            "newer-latest": ({"latest": {"tag_name": "v1.3.0", "draft": False, "prerelease": False}},
                             "must not regress"),
            "release-unsigned": ({"release_signature": unsigned}, "release commit signature must be VALID"),
        }
        for label, (change, expected) in cases.items():
            with self.subTest(label=label):
                failures = self.preflight(**change)
                self.assertTrue(any(expected in failure for failure in failures), failures)


if __name__ == "__main__":
    unittest.main()
