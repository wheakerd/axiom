"""Verify one Draft against its independently derived subject and publish its evidence.

The immutable publisher derives the release subject from the tag with
``.ci/scripts/release.py subject``: the tag object, tagged commit and tree, the
``release`` branch commit and its stamped tree, the plugin zip, the runtime
digest, the previous release, and the notes digest. This validator binds the
Draft and its plugin zip to that subject, and writes the one evidence asset
that records every derived fact once. It checks the Release and both assets
again before publication and after GitHub reports the Release immutable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from .context import REPOSITORY_ROOT, display_path
from .release import REQUIRED_CHECKS, zip_name
from .release_versions import (
    PRODUCTION_RELEASE_TAG_ERE_PATTERN,
    PRODUCTION_RELEASE_VERSION_CASES,
    parse_production_release_tag,
    parse_production_release_version,
)
from .yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "publish-immutable-release.yml"
EVIDENCE_KIND = "axiom-release-evidence"
EVIDENCE_SCHEMA_VERSION = "3"
EVIDENCE_SCOPE = "release-policy-and-artifact-integrity"
EVIDENCE_VALIDATOR = ".ci/scripts/check-release-evidence.py"
PLAN_SCHEMA_VERSION = "4"
OID_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
RUNTIME_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
PUBLISH_WORKFLOW_SHA256 = "95cd8660632c009b1c8c7e571c488d6acb380d26a884835caa5e4929cae9b6be"
SUBJECT_KEYS = frozenset(
    {
        "bootstrap",
        "version",
        "tag",
        "tagObject",
        "commit",
        "tree",
        "releaseCommit",
        "releaseTree",
        "zip",
        "runtimeDigest",
        "previousTag",
        "notesSha256",
    }
)
ASSET_KEYS = frozenset({"id", "name", "size", "state", "digest", "createdAt", "updatedAt"})


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON object repeats a key."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        document[key] = value
    return document


def _load_json_value(path: Path, label: str, failures: list[str]) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None


def _load_json_object(path: Path, label: str, failures: list[str]) -> dict[str, Any] | None:
    document = _load_json_value(path, label, failures)
    if document is None:
        return None
    if type(document) is not dict:
        failures.append(f"{label} must contain one top-level object")
        return None
    return document


def _canonical_json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, document: dict[str, Any], failures: list[str]) -> bool:
    try:
        path.write_bytes(_canonical_json_bytes(document))
    except OSError as error:
        failures.append(f"cannot write {path}: {error}")
        return False
    return True


def _oid(value: Any) -> bool:
    return type(value) is str and OID_PATTERN.fullmatch(value) is not None


def validate_subject(subject: Any, failures: list[str]) -> bool:
    """Require one complete, internally consistent release subject."""
    if type(subject) is not dict or set(subject) != SUBJECT_KEYS:
        failures.append("release subject has unexpected or missing fields")
        return False
    if type(subject["bootstrap"]) is not bool:
        failures.append("release subject bootstrap must be a boolean")
    version = subject["version"]
    if parse_production_release_version(version) is None:
        failures.append("release subject version must be one strict SemVer release version")
        return False
    if subject["tag"] != f"v{version}":
        failures.append("release subject tag must be v<version>")
    tag_object = subject["tagObject"]
    if (
        type(tag_object) is not dict
        or set(tag_object) != {"type", "sha"}
        or tag_object.get("type") not in {"tag", "commit"}
        or not _oid(tag_object.get("sha"))
    ):
        failures.append("release subject tagObject must name one tag or commit object")
    elif tag_object["type"] == "commit" and tag_object["sha"] != subject["commit"]:
        failures.append("a lightweight release tag must point at the subject commit")
    for field in ("commit", "tree", "releaseCommit", "releaseTree"):
        if not _oid(subject[field]):
            failures.append(f"release subject {field} must be a lowercase 40-character Git SHA")
    archive = subject["zip"]
    if (
        type(archive) is not dict
        or set(archive) != {"name", "sha256", "size"}
        or archive.get("name") != zip_name(version)
        or type(archive.get("sha256")) is not str
        or DIGEST_PATTERN.fullmatch(archive["sha256"]) is None
        or type(archive.get("size")) is not int
        or archive["size"] <= 0
    ):
        failures.append("release subject zip must name the plugin zip with its SHA-256 and size")
    if type(subject["runtimeDigest"]) is not str or RUNTIME_DIGEST_PATTERN.fullmatch(
        subject["runtimeDigest"]
    ) is None:
        failures.append("release subject runtimeDigest must be one sha256 digest")
    previous = subject["previousTag"]
    if previous is not None:
        previous_version = parse_production_release_tag(previous)
        if previous_version is None or previous_version >= parse_production_release_version(version):
            failures.append("release subject previousTag must name an older release tag")
    if type(subject["notesSha256"]) is not str or DIGEST_PATTERN.fullmatch(subject["notesSha256"]) is None:
        failures.append("release subject notesSha256 must be one SHA-256 digest")
    return not failures


def load_subject(path: Path, failures: list[str]) -> dict[str, Any] | None:
    subject = _load_json_object(path, "release subject", failures)
    if subject is None or not validate_subject(subject, failures):
        return None
    return subject


def _evidence_prefix(tag: str) -> str:
    return f"axiom-{tag}-release-evidence-"


def _normalize_asset(asset: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    if type(asset) is not dict:
        failures.append(f"{label} must be an object")
        return None
    asset_id = asset.get("id")
    if type(asset_id) is not int or asset_id <= 0:
        failures.append(f"{label}.id must be a positive integer")
        asset_id = None
    name = asset.get("name")
    if type(name) is not str or not name:
        failures.append(f"{label}.name must be a non-empty string")
        name = None
    size = asset.get("size")
    if type(size) is not int or size < 0:
        failures.append(f"{label}.size must be a non-negative integer")
        size = None
    if asset.get("state") != "uploaded":
        failures.append(f"{label}.state must be 'uploaded'")
    digest = asset.get("digest")
    if (
        type(digest) is not str
        or not digest.startswith("sha256:")
        or DIGEST_PATTERN.fullmatch(digest.removeprefix("sha256:")) is None
    ):
        failures.append(f"{label}.digest must be one exposed lowercase SHA-256 digest")
        digest = None
    for field in ("created_at", "updated_at"):
        if type(asset.get(field)) is not str or not asset.get(field):
            failures.append(f"{label}.{field} must be a non-empty string")
    if asset_id is None or name is None or size is None:
        return None
    return {
        "id": asset_id,
        "name": name,
        "size": size,
        "state": asset.get("state"),
        "digest": digest,
        "createdAt": asset.get("created_at"),
        "updatedAt": asset.get("updated_at"),
    }


def _inspect_release(
    document: dict[str, Any], subject: dict[str, Any], *, expected_phase: str, failures: list[str]
) -> dict[str, Any] | None:
    release_id = document.get("id")
    if type(release_id) is not int or release_id <= 0:
        failures.append("release.id must be a positive integer")
        release_id = None
    expected_fields = {
        "tag_name": subject["tag"],
        "target_commitish": subject["commit"],
        "name": subject["tag"],
        "draft": expected_phase == "draft",
        "prerelease": False,
    }
    for field, expected in expected_fields.items():
        if document.get(field) != expected:
            failures.append(f"release.{field} must equal {expected!r}")
    body = document.get("body")
    if type(body) is not str or hashlib.sha256(body.encode("utf-8")).hexdigest() != subject["notesSha256"]:
        failures.append("release.body must be exactly the notes the tag renders")
    immutable = document.get("immutable")
    if type(immutable) is not bool:
        failures.append("release.immutable must be a boolean")
    elif expected_phase == "final" and immutable is not True:
        failures.append("final GitHub Release must report immutable=true")
    elif expected_phase != "final" and immutable is not False:
        failures.append("non-final GitHub Release must not report immutable=true")
    if release_id is None:
        return None
    return {
        "id": release_id,
        "tag": subject["tag"],
        "targetCommit": subject["commit"],
        "name": subject["tag"],
        "notesSha256": subject["notesSha256"],
    }


def _select_assets(
    document: dict[str, Any], subject: dict[str, Any], *, evidence: str, failures: list[str]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Select the zip and evidence assets; ``evidence`` is required, optional, or absent."""
    assets = document.get("assets")
    if type(assets) is not list:
        failures.append("release.assets must be an array")
        return None, None
    tag = subject["tag"]
    named = [asset for asset in assets if type(asset) is dict and type(asset.get("name")) is str]
    zips = [asset for asset in named if asset["name"] == subject["zip"]["name"]]
    evidences = [asset for asset in named if asset["name"].startswith(_evidence_prefix(tag))]
    if len(zips) + len(evidences) != len(assets):
        failures.append("release contains an unrecognized asset")
    archive: dict[str, Any] | None = None
    if len(zips) != 1:
        failures.append("release must contain exactly one zip asset")
    else:
        archive = _normalize_asset(zips[0], "release zip asset", failures)
    evidence_asset: dict[str, Any] | None = None
    if evidence == "absent" and evidences:
        failures.append("the release already contains an evidence asset")
    elif len(evidences) > 1 or (evidence == "required" and len(evidences) != 1):
        failures.append("release must contain exactly one evidence asset")
    elif evidences and evidence != "absent":
        evidence_asset = _normalize_asset(evidences[0], "release evidence asset", failures)
        if evidence_asset is not None and re.fullmatch(
            re.escape(_evidence_prefix(tag)) + r"[0-9a-f]{64}\.json", evidence_asset["name"]
        ) is None:
            failures.append("release evidence asset name must contain one full lowercase SHA-256")
    return archive, evidence_asset


def _flatten_collection(document: Any, failures: list[str]) -> list[Any] | None:
    if type(document) is not list:
        failures.append("release collection must be an array")
        return None
    releases: list[Any] = []
    for item in document:
        releases.extend(item if type(item) is list else [item])
    return releases


def select_release_from_collection(
    collection_path: Path, output_path: Path, *, expected_tag: str, failures: list[str]
) -> dict[str, Any] | None:
    """Select one exact Release for the tag from a listing."""
    releases = _flatten_collection(_load_json_value(collection_path, "release collection", failures), failures)
    if releases is None:
        return None
    candidates = [
        release for release in releases if type(release) is dict and release.get("tag_name") == expected_tag
    ]
    if len(candidates) != 1:
        failures.append(f"release collection must contain exactly one {expected_tag!r} Release")
        return None
    if not _write_json(output_path, candidates[0], failures):
        return None
    return candidates[0]


def prepare_release_plan(
    metadata_path: Path, subject: dict[str, Any], failures: list[str]
) -> dict[str, Any] | None:
    """Freeze one exact draft, mutable published, or immutable Release and its assets."""
    document = _load_json_object(metadata_path, "release metadata", failures)
    if document is None:
        return None
    if document.get("draft") is True and document.get("immutable") is False:
        phase = "draft"
    elif document.get("draft") is False and document.get("immutable") is False:
        phase = "published-mutable"
    elif document.get("draft") is False and document.get("immutable") is True:
        phase = "final"
    else:
        failures.append(
            "release must be a mutable draft, published mutable Release, or immutable final Release"
        )
        return None
    release = _inspect_release(document, subject, expected_phase=phase, failures=failures)
    archive, evidence = _select_assets(
        document,
        subject,
        evidence="optional" if phase == "draft" else "required",
        failures=failures,
    )
    if release is None or archive is None or failures:
        return None
    return {
        "schemaVersion": PLAN_SCHEMA_VERSION,
        "phase": phase,
        "release": release,
        "subject": subject,
        "zipAsset": archive,
        "evidenceAsset": evidence,
    }


def _validate_plan(plan: Any, failures: list[str]) -> bool:
    if type(plan) is not dict or set(plan) != {
        "schemaVersion",
        "phase",
        "release",
        "subject",
        "zipAsset",
        "evidenceAsset",
    }:
        failures.append("release evidence plan has unexpected or missing fields")
        return False
    if plan["schemaVersion"] != PLAN_SCHEMA_VERSION:
        failures.append("release evidence plan schemaVersion is unsupported")
    if plan["phase"] not in {"draft", "published-mutable", "final"}:
        failures.append("release evidence plan phase is unsupported")
    if not validate_subject(plan["subject"], failures):
        return False
    subject = plan["subject"]
    release = plan["release"]
    if type(release) is not dict or release != {
        "id": release.get("id") if type(release) is dict else None,
        "tag": subject["tag"],
        "targetCommit": subject["commit"],
        "name": subject["tag"],
        "notesSha256": subject["notesSha256"],
    } or type(release.get("id")) is not int or release["id"] <= 0:
        failures.append("release evidence plan release binding is malformed")
    for field in ("zipAsset", "evidenceAsset"):
        asset = plan[field]
        if asset is None and field == "evidenceAsset":
            continue
        if type(asset) is not dict or set(asset) != ASSET_KEYS:
            failures.append(f"release evidence plan {field} binding is malformed")
    if plan["phase"] != "draft" and plan["evidenceAsset"] is None:
        failures.append("published release evidence plan requires one evidence binding")
    return not failures


def load_release_plan(path: Path, failures: list[str]) -> dict[str, Any] | None:
    plan = _load_json_object(path, "release evidence plan", failures)
    if plan is None or not _validate_plan(plan, failures):
        return None
    return plan


def exact_ref_object(
    document: dict[str, Any], expected_ref: str, label: str, failures: list[str]
) -> tuple[str, str] | None:
    """Return the object type and ID of one exact GitHub Git reference."""
    if document.get("ref") != expected_ref:
        failures.append(f"{label} must equal {expected_ref!r}")
    target = document.get("object")
    if type(target) is not dict or target.get("type") not in {"commit", "tag"} or not _oid(target.get("sha")):
        failures.append(f"{label} must point at one commit or tag object")
        return None
    return target["type"], target["sha"]


def exact_ref_commit(
    document: dict[str, Any], expected_ref: str, label: str, failures: list[str]
) -> str | None:
    """Return the commit of one exact lightweight branch reference."""
    target = exact_ref_object(document, expected_ref, label, failures)
    if target is None:
        return None
    if target[0] != "commit":
        failures.append(f"{label} must point at a commit")
        return None
    return target[1]


def _signature_valid(document: dict[str, Any] | None, commit: str, label: str, failures: list[str]) -> None:
    if document is None:
        return
    try:
        target = document["data"]["repository"]["object"]
        signature = target["signature"]
    except (KeyError, TypeError):
        failures.append(f"GraphQL {label} signature response is malformed")
        return
    if target.get("oid") != commit:
        failures.append(f"GraphQL {label} signature target must equal {commit}")
    if (
        type(signature) is not dict
        or signature.get("isValid") is not True
        or signature.get("state") != "VALID"
        or signature.get("wasSignedByGitHub") is not True
    ):
        failures.append(f"GraphQL {label} signature must be VALID and made by GitHub")


def verify_remote_release_preflight(
    *,
    repository_metadata_path: Path,
    latest_release_path: Path,
    main_ref_path: Path,
    tag_ref_path: Path,
    release_ref_path: Path,
    history_comparison_path: Path,
    commit_metadata_path: Path,
    commit_signature_path: Path,
    release_signature_path: Path,
    subject: dict[str, Any],
    failures: list[str],
) -> None:
    """Fail closed unless the live tag, release branch, history, and signatures match the subject."""
    commit = subject["commit"]
    tag = subject["tag"]
    repository = _load_json_object(repository_metadata_path, "repository metadata", failures)
    latest = _load_json_object(latest_release_path, "current GitHub Latest Release", failures)
    main_ref = _load_json_object(main_ref_path, "live main ref", failures)
    tag_ref = _load_json_object(tag_ref_path, "live release tag ref", failures)
    release_ref = _load_json_object(release_ref_path, "live release branch ref", failures)
    comparison = _load_json_object(history_comparison_path, "tag-to-main history comparison", failures)
    commit_metadata = _load_json_object(commit_metadata_path, "live tagged commit", failures)
    commit_signature = _load_json_object(commit_signature_path, "tagged commit signature", failures)
    release_signature = _load_json_object(release_signature_path, "release commit signature", failures)
    if repository is not None and repository.get("default_branch") != "main":
        failures.append("repository default branch must remain main")
    if latest is not None:
        latest_tag = latest.get("tag_name")
        latest_version = parse_production_release_tag(latest_tag)
        if latest.get("draft") is not False or latest.get("prerelease") is not False:
            failures.append("GitHub Latest must be one published stable Release")
        if latest_version is None:
            failures.append("GitHub Latest must use one strict SemVer release tag")
        elif latest_tag != tag and latest_version >= parse_production_release_tag(tag):
            failures.append("publication must not regress the GitHub Latest release version")
    if main_ref is not None:
        exact_ref_commit(main_ref, "refs/heads/main", "live main ref", failures)
    if tag_ref is not None:
        target = exact_ref_object(tag_ref, f"refs/tags/{tag}", "live release tag ref", failures)
        if target is not None and {"type": target[0], "sha": target[1]} != subject["tagObject"]:
            failures.append("live release tag ref must still point at the subject tag object")
    if release_ref is not None:
        head = exact_ref_commit(release_ref, "refs/heads/release", "live release branch ref", failures)
        if head is not None and head != subject["releaseCommit"]:
            failures.append("live release branch head must be the subject release commit")
    if comparison is not None:
        merge_base = comparison.get("merge_base_commit")
        base = comparison.get("base_commit")
        if (
            type(merge_base) is not dict
            or merge_base.get("sha") != commit
            or type(base) is not dict
            or base.get("sha") != commit
            or comparison.get("status") not in {"ahead", "identical"}
        ):
            failures.append("tagged commit must remain on the live main history")
    if commit_metadata is not None:
        if commit_metadata.get("sha") != commit:
            failures.append("live tagged commit metadata must match the subject commit")
        commit_document = commit_metadata.get("commit")
        verification = commit_document.get("verification") if type(commit_document) is dict else None
        if type(verification) is not dict:
            failures.append("REST tagged commit signature verification is missing")
        elif verification.get("verified") is not True or verification.get("reason") != "valid":
            failures.append("REST tagged commit signature must be verified with reason 'valid'")
    _signature_valid(commit_signature, commit, "tagged commit", failures)
    _signature_valid(release_signature, subject["releaseCommit"], "release commit", failures)


def classify_publication_state(plan: dict[str, Any], metadata_path: Path, failures: list[str]) -> str | None:
    """Classify only the exact frozen, newly published Release as immutable or mutable."""
    if not _validate_plan(plan, failures):
        return None
    document = _load_json_object(metadata_path, "post-publication release metadata", failures)
    if document is None:
        return None
    subject = plan["subject"]
    for field, expected in {
        "id": plan["release"]["id"],
        "tag_name": subject["tag"],
        "target_commitish": subject["commit"],
        "draft": False,
        "prerelease": False,
    }.items():
        if document.get(field) != expected:
            failures.append(f"post-publication release.{field} must equal {expected!r}")
    immutable = document.get("immutable")
    if type(immutable) is not bool:
        failures.append("post-publication release.immutable must be a boolean")
    if failures:
        return None
    return "immutable" if immutable else "mutable"


def assert_release_absent_from_collection(
    collection_path: Path, plan: dict[str, Any], failures: list[str]
) -> None:
    """Fail closed unless the frozen mutable Release disappeared after cleanup."""
    if not _validate_plan(plan, failures):
        return
    releases = _flatten_collection(_load_json_value(collection_path, "release collection", failures), failures)
    if releases is None:
        return
    for release in releases:
        if type(release) is not dict:
            failures.append("release collection contains a malformed entry")
        elif release.get("id") == plan["release"]["id"] or release.get("tag_name") == plan["subject"]["tag"]:
            failures.append("compensating cleanup did not remove the frozen mutable Release")


def _validate_downloaded_asset(
    path: Path, metadata: dict[str, Any], label: str, failures: list[str], *, named_digest: bool
) -> bytes | None:
    try:
        payload = path.read_bytes()
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None
    digest = hashlib.sha256(payload).hexdigest()
    if path.name != metadata["name"]:
        failures.append(f"{label} filename does not match the GitHub asset name")
    if len(payload) != metadata["size"]:
        failures.append(f"{label} byte count does not match the GitHub asset size")
    if named_digest and metadata["name"].removesuffix(".json").rsplit("-", 1)[-1] != digest:
        failures.append(f"{label} filename SHA-256 does not match downloaded bytes")
    if metadata["digest"] is not None and metadata["digest"] != f"sha256:{digest}":
        failures.append(f"{label} GitHub digest does not match downloaded bytes")
    return payload


def _validate_artifacts(
    plan: dict[str, Any], zip_path: Path, expected_zip_path: Path, failures: list[str]
) -> None:
    subject = plan["subject"]
    archive = _validate_downloaded_asset(
        zip_path, plan["zipAsset"], "downloaded plugin zip", failures, named_digest=False
    )
    try:
        expected = expected_zip_path.read_bytes()
    except OSError as error:
        failures.append(f"cannot read the locally built plugin zip: {error}")
        return
    if archive is not None and archive != expected:
        failures.append("the plugin zip asset differs from the zip built from the tag")
    if hashlib.sha256(expected).hexdigest() != subject["zip"]["sha256"] or len(expected) != subject["zip"]["size"]:
        failures.append("the locally built plugin zip does not match the subject")


def evidence_document(subject: dict[str, Any]) -> dict[str, Any]:
    """Return the evidence record: every fact the publisher derived from the tag, once.

    The runtime digest is recorded under ``runtimeContract.digest``, where the
    next release reads it, and nowhere else.
    """
    return {
        "evidenceScope": EVIDENCE_SCOPE,
        "kind": EVIDENCE_KIND,
        "runtimeContract": {"digest": subject["runtimeDigest"]},
        "schemaVersion": EVIDENCE_SCHEMA_VERSION,
        "subject": {key: value for key, value in subject.items() if key != "runtimeDigest"},
        "verification": {
            "requiredChecks": list(REQUIRED_CHECKS),
            "status": "pass",
            "validator": EVIDENCE_VALIDATOR,
        },
    }


def emit_evidence(
    plan: dict[str, Any],
    zip_path: Path,
    expected_zip_path: Path,
    *,
    evidence_directory: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> Path | None:
    """Validate the downloaded plugin zip and write the deterministic evidence asset."""
    if not _validate_plan(plan, failures):
        return None
    _validate_artifacts(plan, zip_path, expected_zip_path, failures)
    if failures:
        return None
    try:
        directory = evidence_directory.resolve(strict=True)
    except OSError as error:
        failures.append(f"cannot resolve evidence directory: {error}")
        return None
    if directory.is_relative_to(root.resolve()):
        failures.append("release evidence must be generated outside the checked-in tree")
        return None
    payload = _canonical_json_bytes(evidence_document(plan["subject"]))
    path = directory / f"{_evidence_prefix(plan['subject']['tag'])}{hashlib.sha256(payload).hexdigest()}.json"
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except OSError as error:
        failures.append(f"cannot write release evidence: {error}")
        return None
    return path


def verify_release_snapshot(
    plan: dict[str, Any],
    metadata_path: Path,
    zip_path: Path,
    expected_zip_path: Path,
    evidence_path: Path,
    *,
    final: bool,
    latest_metadata_path: Path | None,
    prepublish_metadata_path: Path | None,
    failures: list[str],
) -> None:
    """Revalidate the exact Release and asset set before publication and after immutability."""
    if not _validate_plan(plan, failures):
        return
    subject = plan["subject"]
    document = _load_json_object(metadata_path, "current release metadata", failures)
    if document is None:
        return
    release = _inspect_release(document, subject, expected_phase="final" if final else "draft", failures=failures)
    archive, evidence = _select_assets(document, subject, evidence="required", failures=failures)
    if release is not None and release != plan["release"]:
        failures.append("release identity changed after the draft was frozen")
    if archive is not None and archive != plan["zipAsset"]:
        failures.append("plugin zip asset identity or metadata changed after validation")
    if plan["evidenceAsset"] is not None and evidence is not None and evidence != plan["evidenceAsset"]:
        failures.append("evidence asset identity or metadata changed after validation")
    _validate_artifacts(plan, zip_path, expected_zip_path, failures)
    local = _load_json_object(evidence_path, "local release evidence", failures)
    if local is not None and local != evidence_document(subject):
        failures.append("the evidence asset does not match the validated binding")
    if evidence is not None:
        _validate_downloaded_asset(evidence_path, evidence, "release evidence asset", failures, named_digest=True)
    if not final:
        return
    if prepublish_metadata_path is None:
        if plan["phase"] != "final":
            failures.append("initial final verification requires pre-publication metadata")
    else:
        prepublish = _load_json_object(prepublish_metadata_path, "pre-publication release metadata", failures)
        if prepublish is not None:
            if _inspect_release(prepublish, subject, expected_phase="draft", failures=failures) != plan["release"]:
                failures.append("pre-publication release identity differs from the frozen draft")
            if _select_assets(prepublish, subject, evidence="required", failures=failures) != (
                archive,
                evidence,
            ):
                failures.append("the asset set changed during final publication")
    if latest_metadata_path is None:
        failures.append("final verification requires latest-release metadata")
    else:
        latest = _load_json_object(latest_metadata_path, "latest release metadata", failures)
        if latest is not None and (
            latest.get("id") != plan["release"]["id"] or latest.get("tag_name") != subject["tag"]
        ):
            failures.append("GitHub Latest does not identify the immutable release")


def render_summary(plan: dict[str, Any]) -> str:
    subject = plan["subject"]
    return (
        f"## Published immutable {subject['tag']}\n\n"
        "| Field | Value |\n| --- | --- |\n"
        f"| Release | `{plan['release']['id']}` |\n"
        f"| Tagged commit | `{subject['commit']}` |\n"
        f"| `release` commit | `{subject['releaseCommit']}` |\n"
        f"| Installed tree | `{subject['releaseTree']}` |\n"
        f"| Plugin zip sha256 | `{subject['zip']['sha256']}` |\n"
        f"| Runtime digest | `{subject['runtimeDigest']}` |\n"
        f"| Bootstrap release | `{str(subject['bootstrap']).lower()}` |\n"
        f"| Notes sha256 | `{subject['notesSha256']}` |\n\n"
        "Both marketplace catalogs select the `release` branch, so hosts see this "
        "version on their next marketplace refresh.\n"
    )


def _scalar(value: Any) -> str | None:
    return value.value if isinstance(value, CanonicalYamlScalar) else None


def _check_publish_version_gate(text: str, label: str, failures: list[str]) -> None:
    owners = re.findall(r'^\s*\[\[ "\$RELEASE_TAG" =~ (?P<pattern>\S+) \]\]\s*$', text, flags=re.MULTILINE)
    if owners != [PRODUCTION_RELEASE_TAG_ERE_PATTERN]:
        failures.append(f"{label} must contain one canonical strict SemVer release tag gate")
        return
    pattern = re.compile(owners[0])
    for case_id, version, accepted in PRODUCTION_RELEASE_VERSION_CASES:
        if (pattern.fullmatch(f"v{version}") is not None) != accepted:
            failures.append(f"{label} publication version gate disagrees with canonical case {case_id!r}")


def check_publish_workflow_contract(
    failures: list[str], workflow_path: Path = WORKFLOW_PATH
) -> dict[str, Any] | None:
    """Validate the narrow dispatched draft-to-immutable workflow."""
    label = display_path(workflow_path)
    try:
        payload = workflow_path.read_bytes()
        text = payload.decode("utf-8")
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None
    except UnicodeDecodeError as error:
        failures.append(f"invalid UTF-8 in {label}: {error}")
        return None
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None
    if set(document) != {"name", "on", "permissions", "concurrency", "jobs"}:
        failures.append(f"{label} must contain only name, on, permissions, concurrency, and jobs")
    if _scalar(document.get("name")) != "Publish immutable release":
        failures.append(f"{label} must keep its exact public workflow name")
    triggers = document.get("on")
    dispatch = triggers.get("workflow_dispatch") if isinstance(triggers, dict) else None
    inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
    tag_input = inputs.get("tag") if isinstance(inputs, dict) else None
    if not isinstance(triggers, dict) or set(triggers) != {"workflow_dispatch"}:
        failures.append(f"{label} must be workflow_dispatch-only")
    elif not isinstance(inputs, dict) or set(inputs) != {"tag"} or not isinstance(tag_input, dict) or {
        key: _scalar(value) for key, value in tag_input.items()
    } != {
        "description": "Existing strict SemVer release tag whose release branch commit is staged",
        "required": "true",
        "type": "string",
    }:
        failures.append(f"{label} must accept exactly one tag input")
    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or {key: _scalar(value) for key, value in permissions.items()} != {
        "contents": "write"
    }:
        failures.append(f"{label} must grant exactly contents: write")
    concurrency = document.get("concurrency")
    if not isinstance(concurrency, dict) or {key: _scalar(value) for key, value in concurrency.items()} != {
        "group": "publish-immutable-release",
        "cancel-in-progress": "false",
    }:
        failures.append(f"{label} must serialize all Latest publication without cancellation")
    jobs = document.get("jobs")
    job = jobs.get("publish-immutable-release") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"publish-immutable-release"} or not isinstance(job, dict):
        failures.append(f"{label} must declare only the publish-immutable-release job")
    else:
        if set(job) != {"if", "runs-on", "timeout-minutes", "env", "steps"}:
            failures.append(f"{label} publication job contains unexpected fields")
        if _scalar(job.get("runs-on")) != "ubuntu-24.04":
            failures.append(f"{label} must use the fixed ubuntu-24.04 runner")
        if _scalar(job.get("if")) != "github.ref == format('refs/tags/{0}', inputs.tag)":
            failures.append(f"{label} must run only when dispatched from the exact input tag")
        env = job.get("env")
        if not isinstance(env, dict) or {key: _scalar(value) for key, value in env.items()} != {
            "GH_TOKEN": "${{ github.token }}",
            "RELEASE_TAG": "${{ inputs.tag }}",
            "GITHUB_API_VERSION": "2026-03-10",
        }:
            failures.append(f"{label} publication environment changed")
        steps = job.get("steps")
        if not isinstance(steps, list) or len(steps) != 3:
            failures.append(f"{label} must contain exactly checkout, Python, and publication steps")
    required_anchors = (
        "uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "ref: ${{ github.sha }}",
        "persist-credentials: false",
        "fetch-depth: 0",
        "uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        'python3 -B .ci/scripts/release.py subject',
        "git/ref/heads/main",
        "git/ref/heads/release",
        "git/ref/tags/$RELEASE_TAG",
        ".ci/scripts/check-release-evidence.py preflight",
        ".ci/scripts/check-release-evidence.py select",
        ".ci/scripts/check-release-evidence.py prepare",
        ".ci/scripts/check-release-evidence.py validate",
        "https://uploads.github.com/repos/$GITHUB_REPOSITORY/releases/$release_id/assets",
        ".ci/scripts/check-release-evidence.py verify",
        "draft=false",
        "make_latest=true",
        ".ci/scripts/check-release-evidence.py publication-state",
        "gh api --method DELETE",
        ".ci/scripts/check-release-evidence.py assert-absent",
        "--final",
        ".ci/scripts/check-release-evidence.py summary",
    )
    for anchor in required_anchors:
        if anchor not in text:
            failures.append(f"{label} is missing required publication anchor {anchor!r}")
    _check_publish_version_gate(text, label, failures)
    if hashlib.sha256(payload).hexdigest() != PUBLISH_WORKFLOW_SHA256:
        failures.append(f"{label} complete publication command contract changed")
    for forbidden in ("pull_request", "schedule:", "${{ secrets.", "--clobber", "force"):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden publication surface {forbidden!r}")
    return document


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ref_commit = commands.add_parser("ref-commit", help="emit the commit of one exact branch ref")
    ref_commit.add_argument("--ref-metadata", type=Path, required=True)
    ref_commit.add_argument("--expected-ref", required=True)
    preflight = commands.add_parser("preflight", help="verify the live refs, history, and signatures")
    for option in (
        "--repository-metadata",
        "--latest-release-metadata",
        "--main-ref-metadata",
        "--tag-ref-metadata",
        "--release-ref-metadata",
        "--history-comparison",
        "--commit-metadata",
        "--commit-signature",
        "--release-signature",
        "--subject",
    ):
        preflight.add_argument(option, type=Path, required=True)
    select = commands.add_parser("select", help="select one exact Release from a listing")
    select.add_argument("--release-collection", type=Path, required=True)
    select.add_argument("--release-output", type=Path, required=True)
    select.add_argument("--expected-tag", required=True)
    prepare = commands.add_parser("prepare", help="freeze one exact Release and its assets")
    prepare.add_argument("--release-metadata", type=Path, required=True)
    prepare.add_argument("--plan-output", type=Path, required=True)
    prepare.add_argument("--subject", type=Path, required=True)
    emit = commands.add_parser("emit", help="emit one allowlisted plan field")
    emit.add_argument("--plan", type=Path, required=True)
    emit.add_argument(
        "--field",
        choices=(
            "release-id",
            "phase",
            "zip-id",
            "zip-name",
            "evidence-present",
            "evidence-id",
            "evidence-name",
        ),
        required=True,
    )
    for name in ("validate", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--zip", type=Path, required=True)
        command.add_argument("--expected-zip", type=Path, required=True)
        if name == "validate":
            command.add_argument("--evidence-directory", type=Path, required=True)
        else:
            command.add_argument("--release-metadata", type=Path, required=True)
            command.add_argument("--evidence", type=Path, required=True)
            command.add_argument("--final", action="store_true")
            command.add_argument("--latest-release-metadata", type=Path)
            command.add_argument("--prepublish-release-metadata", type=Path)
    state = commands.add_parser("publication-state", help="classify one exact post-publication Release")
    state.add_argument("--plan", type=Path, required=True)
    state.add_argument("--release-metadata", type=Path, required=True)
    absent = commands.add_parser("assert-absent", help="verify cleanup removed the frozen mutable Release")
    absent.add_argument("--plan", type=Path, required=True)
    absent.add_argument("--release-collection", type=Path, required=True)
    summary = commands.add_parser("summary", help="render the publication job summary")
    summary.add_argument("--plan", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures: list[str] = []
    if args.command == "ref-commit":
        document = _load_json_object(args.ref_metadata, "GitHub ref metadata", failures)
        if document is not None:
            commit = exact_ref_commit(document, args.expected_ref, "GitHub ref metadata", failures)
            if commit is not None and not failures:
                print(commit)
    elif args.command == "preflight":
        subject = load_subject(args.subject, failures)
        if subject is not None:
            verify_remote_release_preflight(
                repository_metadata_path=args.repository_metadata,
                latest_release_path=args.latest_release_metadata,
                main_ref_path=args.main_ref_metadata,
                tag_ref_path=args.tag_ref_metadata,
                release_ref_path=args.release_ref_metadata,
                history_comparison_path=args.history_comparison,
                commit_metadata_path=args.commit_metadata,
                commit_signature_path=args.commit_signature,
                release_signature_path=args.release_signature,
                subject=subject,
                failures=failures,
            )
    elif args.command == "select":
        select_release_from_collection(
            args.release_collection, args.release_output, expected_tag=args.expected_tag, failures=failures
        )
    elif args.command == "prepare":
        subject = load_subject(args.subject, failures)
        if subject is not None:
            plan = prepare_release_plan(args.release_metadata, subject, failures)
            if plan is not None and not failures:
                _write_json(args.plan_output, plan, failures)
    elif args.command == "emit":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            field = args.field
            if field == "release-id":
                print(plan["release"]["id"])
            elif field == "phase":
                print(plan["phase"])
            elif field == "evidence-present":
                print("true" if plan["evidenceAsset"] is not None else "false")
            else:
                kind, attribute = field.split("-", 1)
                binding = plan[f"{kind}Asset"]
                if binding is None:
                    failures.append(f"release evidence plan has no {kind} asset")
                else:
                    print(binding[attribute])
    elif args.command == "validate":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            path = emit_evidence(
                plan, args.zip, args.expected_zip,
                evidence_directory=args.evidence_directory, failures=failures,
            )
            if path is not None and not failures:
                print(path)
    elif args.command == "verify":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            verify_release_snapshot(
                plan,
                args.release_metadata,
                args.zip,
                args.expected_zip,
                args.evidence,
                final=args.final,
                latest_metadata_path=args.latest_release_metadata,
                prepublish_metadata_path=args.prepublish_release_metadata,
                failures=failures,
            )
    elif args.command == "publication-state":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            state = classify_publication_state(plan, args.release_metadata, failures)
            if state is not None and not failures:
                print(state)
    elif args.command == "assert-absent":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            assert_release_absent_from_collection(args.release_collection, plan, failures)
    elif args.command == "summary":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            sys.stdout.write(render_summary(plan))
    if failures:
        print("Release evidence validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
