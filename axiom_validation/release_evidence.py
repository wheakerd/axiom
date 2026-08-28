"""Validate and bind GitHub Release routing evidence before publication."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from .context import RELEASE_VERSION, REPOSITORY_ROOT, display_path
from .release_versions import (
    PRODUCTION_RELEASE_TAG_ERE_PATTERN,
    PRODUCTION_RELEASE_VERSION_CASES,
    parse_production_release_tag,
    parse_production_release_version,
)
from .routing_evals import validate_external_routing_observation
from .yaml_subset import CanonicalYamlError, CanonicalYamlScalar, parse_canonical_yaml_document


WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "publish-immutable-release.yml"
ATTESTATION_KIND = "axiom-release-evidence-attestation"
ATTESTATION_SCHEMA_VERSION = "1"
PLAN_SCHEMA_VERSION = "2"
OID_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
PUBLISH_WORKFLOW_SHA256 = "571181a832014bddf3088bca27eb02ce9ec5a03104f3244d6ad4b9224447d252"


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON object repeats a key."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        document[key] = value
    return document


def _load_json_object(path: Path, label: str, failures: list[str]) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None
    try:
        document = json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)
    except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None
    if type(document) is not dict:
        failures.append(f"{label} must contain one top-level object")
        return None
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


def _canonical_json_bytes(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, document: dict[str, Any], failures: list[str]) -> bool:
    try:
        path.write_bytes(_canonical_json_bytes(document))
    except OSError as error:
        failures.append(f"cannot write {path}: {error}")
        return False
    return True


def _require_positive_int(value: Any, label: str, failures: list[str]) -> int | None:
    if type(value) is not int or value <= 0:
        failures.append(f"{label} must be a positive integer")
        return None
    return value


def _validate_subject(
    version: str,
    tag: str,
    commit: str,
    tree: str,
    failures: list[str],
) -> None:
    if parse_production_release_version(version) is None:
        failures.append(
            "expected release version must be one stable numeric production release version"
        )
    if type(version) is str and version != RELEASE_VERSION:
        failures.append("expected release version must match both current manifests")
    if type(tag) is not str or tag != f"v{version}":
        failures.append("expected release tag must match the exact version")
    if type(commit) is not str or OID_PATTERN.fullmatch(commit) is None:
        failures.append("expected release commit must be a lowercase 40-character Git SHA")
    if type(tree) is not str or OID_PATTERN.fullmatch(tree) is None:
        failures.append("expected release tree must be a lowercase 40-character Git SHA")


def _asset_prefix(version: str) -> str:
    return f"axiom-v{version}-codex-core-v2-"


def _attestation_prefix(version: str) -> str:
    return f"axiom-v{version}-release-evidence-"


def _normalize_asset(asset: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    if type(asset) is not dict:
        failures.append(f"{label} must be an object")
        return None
    asset_id = _require_positive_int(asset.get("id"), f"{label}.id", failures)
    name = asset.get("name")
    if type(name) is not str or not name:
        failures.append(f"{label}.name must be a non-empty string")
        name = None
    size = asset.get("size")
    if type(size) is not int or size < 0:
        failures.append(f"{label}.size must be a non-negative integer")
        size = None
    state = asset.get("state")
    if state != "uploaded":
        failures.append(f"{label}.state must be 'uploaded'")
    digest = asset.get("digest")
    if (
        type(digest) is not str
        or not digest.startswith("sha256:")
        or DIGEST_PATTERN.fullmatch(digest.removeprefix("sha256:")) is None
    ):
        failures.append(f"{label}.digest must be one exposed lowercase SHA-256 digest")
        digest = None
    created_at = asset.get("created_at")
    updated_at = asset.get("updated_at")
    for field, value in (("created_at", created_at), ("updated_at", updated_at)):
        if type(value) is not str or not value:
            failures.append(f"{label}.{field} must be a non-empty string")
    if asset_id is None or name is None or size is None:
        return None
    return {
        "id": asset_id,
        "name": name,
        "size": size,
        "state": state,
        "digest": digest,
        "createdAt": created_at,
        "updatedAt": updated_at,
    }


def _inspect_release(
    document: dict[str, Any],
    *,
    version: str,
    tag: str,
    commit: str,
    expected_phase: str,
    failures: list[str],
) -> dict[str, Any] | None:
    release_id = _require_positive_int(document.get("id"), "release.id", failures)
    expected_fields = {
        "tag_name": tag,
        "target_commitish": commit,
        "name": f"Axiom {tag}",
        "draft": expected_phase == "draft",
        "prerelease": False,
    }
    for field, expected in expected_fields.items():
        if document.get(field) != expected:
            failures.append(f"release.{field} must equal {expected!r}")
    notes_path = REPOSITORY_ROOT / "docs" / "releases" / f"v{version}.md"
    try:
        expected_notes = notes_path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read exact release notes {display_path(notes_path)}: {error}")
        expected_notes = None
    if expected_notes is not None and document.get("body") != expected_notes:
        failures.append(
            f"release.body must exactly match {display_path(notes_path)} at the release commit"
        )
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
        "tag": tag,
        "targetCommit": commit,
        "name": f"Axiom {tag}",
        "notesSha256": (
            hashlib.sha256(expected_notes.encode("utf-8")).hexdigest()
            if expected_notes is not None
            else None
        ),
    }


def _select_assets(
    document: dict[str, Any],
    *,
    version: str,
    attestation_requirement: str,
    failures: list[str],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    assets = document.get("assets")
    if type(assets) is not list:
        failures.append("release.assets must be an array")
        return None, None
    allowed_counts = {1, 2} if attestation_requirement == "optional" else {
        2 if attestation_requirement == "required" else 1
    }
    if len(assets) not in allowed_counts:
        expected = (
            "one or two"
            if attestation_requirement == "optional"
            else "two" if allowed_counts == {2} else "one"
        )
        failures.append(
            f"release must contain exactly {expected} evidence asset"
            f"{'s' if allowed_counts != {1} else ''} at this phase"
        )
    observation_candidates = [
        asset
        for asset in assets
        if type(asset) is dict
        and type(asset.get("name")) is str
        and asset["name"].startswith(_asset_prefix(version))
        and asset["name"].endswith(".json")
    ]
    if len(observation_candidates) != 1:
        failures.append("release must contain exactly one routing-observation candidate")
        observation = None
    else:
        observation = _normalize_asset(
            observation_candidates[0], "release routing-observation asset", failures
        )
        if observation is not None:
            expected_pattern = re.compile(
                re.escape(_asset_prefix(version)) + r"[0-9a-f]{64}\.json"
            )
            if expected_pattern.fullmatch(observation["name"]) is None:
                failures.append(
                    "release routing-observation asset name must contain one full lowercase SHA-256"
                )

    attestation_candidates = [
        asset
        for asset in assets
        if type(asset) is dict
        and type(asset.get("name")) is str
        and asset["name"].startswith(_attestation_prefix(version))
        and asset["name"].endswith(".json")
    ]
    if len(observation_candidates) + len(attestation_candidates) != len(assets):
        failures.append("release contains an unrecognized evidence asset")
    attestation: dict[str, Any] | None = None
    if attestation_requirement in {"required", "optional"}:
        if len(attestation_candidates) != 1:
            if attestation_requirement == "required" or len(attestation_candidates) > 1:
                failures.append("release must contain exactly one release-evidence attestation")
        else:
            attestation = _normalize_asset(
                attestation_candidates[0], "release evidence-attestation asset", failures
            )
            if attestation is not None:
                expected_pattern = re.compile(
                    re.escape(_attestation_prefix(version)) + r"[0-9a-f]{64}\.json"
                )
                if expected_pattern.fullmatch(attestation["name"]) is None:
                    failures.append(
                        "release evidence-attestation asset name must contain one full lowercase SHA-256"
                    )
    elif attestation_candidates:
        failures.append("draft release already contains a release-evidence attestation")
    return observation, attestation


def select_release_from_collection(
    collection_path: Path,
    output_path: Path,
    *,
    expected_tag: str,
    failures: list[str],
) -> dict[str, Any] | None:
    """Select one exact draft, mutable final, or immutable Release from a listing."""
    document = _load_json_value(collection_path, "release collection", failures)
    if type(document) is not list:
        failures.append("release collection must be an array")
        return None
    releases: list[Any] = []
    for item in document:
        if type(item) is list:
            releases.extend(item)
        else:
            releases.append(item)
    candidates = [
        release
        for release in releases
        if type(release) is dict and release.get("tag_name") == expected_tag
    ]
    if len(candidates) != 1:
        failures.append(f"release collection must contain exactly one {expected_tag!r} Release")
        return None
    selected = candidates[0]
    if not _write_json(output_path, selected, failures):
        return None
    return selected


def assert_release_absent_from_collection(
    collection_path: Path,
    plan: dict[str, Any],
    failures: list[str],
) -> None:
    """Fail closed unless the frozen mutable Release disappeared after cleanup."""
    if not _validate_plan(plan, failures):
        return
    document = _load_json_value(collection_path, "release collection", failures)
    if type(document) is not list:
        failures.append("release collection must be an array")
        return
    releases: list[Any] = []
    for item in document:
        if type(item) is list:
            releases.extend(item)
        else:
            releases.append(item)
    frozen_id = plan["release"]["id"]
    frozen_tag = plan["subject"]["tag"]
    for release in releases:
        if type(release) is not dict:
            failures.append("release collection contains a malformed entry")
            continue
        if release.get("id") == frozen_id or release.get("tag_name") == frozen_tag:
            failures.append("compensating cleanup did not remove the frozen mutable Release")


def prepare_release_plan(
    metadata_path: Path,
    *,
    expected_version: str,
    expected_tag: str,
    expected_commit: str,
    expected_tree: str,
    failures: list[str],
) -> dict[str, Any] | None:
    """Freeze one exact draft, mutable published, or immutable Release and its evidence."""
    _validate_subject(
        expected_version, expected_tag, expected_commit, expected_tree, failures
    )
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
    release = _inspect_release(
        document,
        version=expected_version,
        tag=expected_tag,
        commit=expected_commit,
        expected_phase=phase,
        failures=failures,
    )
    observation, attestation = _select_assets(
        document,
        version=expected_version,
        attestation_requirement="optional" if phase == "draft" else "required",
        failures=failures,
    )
    if release is None or observation is None or failures:
        return None
    return {
        "schemaVersion": PLAN_SCHEMA_VERSION,
        "phase": phase,
        "release": release,
        "subject": {
            "version": expected_version,
            "tag": expected_tag,
            "commit": expected_commit,
            "tree": expected_tree,
        },
        "observationAsset": observation,
        "attestationAsset": attestation,
    }


def _validate_plan(plan: dict[str, Any], failures: list[str]) -> bool:
    if set(plan) != {
        "schemaVersion",
        "phase",
        "release",
        "subject",
        "observationAsset",
        "attestationAsset",
    }:
        failures.append("release evidence plan has unexpected or missing fields")
        return False
    if plan.get("schemaVersion") != PLAN_SCHEMA_VERSION:
        failures.append("release evidence plan schemaVersion is unsupported")
    release = plan.get("release")
    subject = plan.get("subject")
    asset = plan.get("observationAsset")
    attestation = plan.get("attestationAsset")
    if plan.get("phase") not in {"draft", "published-mutable", "final"}:
        failures.append("release evidence plan phase is unsupported")
    if type(release) is not dict or set(release) != {
        "id",
        "tag",
        "targetCommit",
        "name",
        "notesSha256",
    }:
        failures.append("release evidence plan release binding is malformed")
    if type(subject) is not dict or set(subject) != {"version", "tag", "commit", "tree"}:
        failures.append("release evidence plan subject binding is malformed")
    if type(asset) is not dict or set(asset) != {
        "id",
        "name",
        "size",
        "state",
        "digest",
        "createdAt",
        "updatedAt",
    }:
        failures.append("release evidence plan asset binding is malformed")
    if failures:
        return False
    _validate_subject(
        subject["version"], subject["tag"], subject["commit"], subject["tree"], failures
    )
    if release["tag"] != subject["tag"] or release["targetCommit"] != subject["commit"]:
        failures.append("release evidence plan release and subject bindings disagree")
    if _require_positive_int(release.get("id"), "plan.release.id", failures) is None:
        pass
    if release.get("name") != f"Axiom {subject.get('tag')}":
        failures.append("release evidence plan title does not match its tag")
    if type(release.get("notesSha256")) is not str or DIGEST_PATTERN.fullmatch(
        release["notesSha256"]
    ) is None:
        failures.append("release evidence plan notesSha256 is malformed")
    normalized_asset = _normalize_asset(
        {
            "id": asset.get("id"),
            "name": asset.get("name"),
            "size": asset.get("size"),
            "state": asset.get("state"),
            "digest": asset.get("digest"),
            "created_at": asset.get("createdAt"),
            "updated_at": asset.get("updatedAt"),
        },
        "plan.observationAsset",
        failures,
    )
    if normalized_asset is not None and normalized_asset != asset:
        failures.append("release evidence plan asset binding is not canonical")
    if attestation is not None:
        if type(attestation) is not dict or set(attestation) != {
            "id",
            "name",
            "size",
            "state",
            "digest",
            "createdAt",
            "updatedAt",
        }:
            failures.append("release evidence plan attestation binding is malformed")
        else:
            normalized_attestation = _normalize_asset(
                {
                    "id": attestation.get("id"),
                    "name": attestation.get("name"),
                    "size": attestation.get("size"),
                    "state": attestation.get("state"),
                    "digest": attestation.get("digest"),
                    "created_at": attestation.get("createdAt"),
                    "updated_at": attestation.get("updatedAt"),
                },
                "plan.attestationAsset",
                failures,
            )
            if normalized_attestation is not None and normalized_attestation != attestation:
                failures.append("release evidence plan attestation binding is not canonical")
    if plan.get("phase") in {"published-mutable", "final"} and attestation is None:
        failures.append("published release evidence plan requires one attestation binding")
    return not failures


def load_release_plan(path: Path, failures: list[str]) -> dict[str, Any] | None:
    plan = _load_json_object(path, "release evidence plan", failures)
    if plan is None or not _validate_plan(plan, failures):
        return None
    return plan


def verify_remote_release_preflight(
    repository_metadata_path: Path,
    latest_release_path: Path,
    main_ref_path: Path,
    tag_ref_path: Path,
    history_comparison_path: Path,
    commit_metadata_path: Path,
    graphql_signature_path: Path,
    *,
    expected_commit: str,
    expected_tag: str,
    require_main_tip: bool,
    failures: list[str],
) -> None:
    """Fail closed unless exact live refs and GitHub signature still match."""
    if OID_PATTERN.fullmatch(expected_commit) is None:
        failures.append("preflight expected commit must be one lowercase 40-character Git SHA")
        return
    repository = _load_json_object(repository_metadata_path, "repository metadata", failures)
    latest = _load_json_object(latest_release_path, "current GitHub Latest Release", failures)
    main_ref = _load_json_object(main_ref_path, "live main ref", failures)
    tag_ref = _load_json_object(tag_ref_path, "live release tag ref", failures)
    comparison = _load_json_object(
        history_comparison_path, "release-to-main history comparison", failures
    )
    commit_metadata = _load_json_object(
        commit_metadata_path, "live release commit", failures
    )
    graphql = _load_json_object(
        graphql_signature_path, "GraphQL commit signature", failures
    )
    if repository is not None and repository.get("default_branch") != "main":
        failures.append("repository default branch must remain main")
    target_version = parse_production_release_tag(expected_tag)
    if target_version is None:
        failures.append(
            "preflight expected tag must be one stable numeric production release tag"
        )
    if latest is not None:
        latest_tag = latest.get("tag_name")
        latest_version = parse_production_release_tag(latest_tag)
        if latest.get("draft") is not False or latest.get("prerelease") is not False:
            failures.append("GitHub Latest must be one published stable Release")
        if latest_version is None:
            failures.append("GitHub Latest must use one stable numeric production release tag")
        elif target_version is not None:
            if latest_tag != expected_tag and latest_version >= target_version:
                failures.append("publication must not regress the GitHub Latest release version")
    main_commit = (
        exact_ref_commit(main_ref, "refs/heads/main", "live main ref", failures)
        if main_ref is not None
        else None
    )
    tag_commit = (
        exact_ref_commit(
            tag_ref, f"refs/tags/{expected_tag}", "live release tag ref", failures
        )
        if tag_ref is not None
        else None
    )
    if tag_commit is not None and tag_commit != expected_commit:
        failures.append("live release tag ref must target the exact release commit")
    if require_main_tip and main_commit is not None and main_commit != expected_commit:
        failures.append("live main tip must equal the release commit before publication mutation")
    if comparison is not None and main_commit is not None:
        merge_base = comparison.get("merge_base_commit")
        base = comparison.get("base_commit")
        if (
            type(merge_base) is not dict
            or merge_base.get("sha") != expected_commit
            or type(base) is not dict
            or base.get("sha") != expected_commit
            or comparison.get("status") not in {"ahead", "identical"}
        ):
            failures.append("release commit must remain on the exact live main history")
    if commit_metadata is not None:
        if commit_metadata.get("sha") != expected_commit:
            failures.append("live release commit metadata must match the exact release commit")
        commit_document = commit_metadata.get("commit")
        verification = (
            commit_document.get("verification") if type(commit_document) is dict else None
        )
        if type(verification) is not dict:
            failures.append("REST release commit signature verification is missing")
        elif verification.get("verified") is not True or verification.get("reason") != "valid":
            failures.append("REST release commit signature must be verified with reason 'valid'")
    if graphql is not None:
        try:
            commit = graphql["data"]["repository"]["object"]
            signature = commit["signature"]
        except (KeyError, TypeError):
            failures.append("GraphQL tag target signature response is malformed")
        else:
            if commit.get("oid") != expected_commit:
                failures.append("GraphQL signature target must equal the exact release commit")
            if (
                type(signature) is not dict
                or signature.get("isValid") is not True
                or signature.get("state") != "VALID"
                or signature.get("wasSignedByGitHub") is not True
            ):
                failures.append("GraphQL signature must be VALID and made by GitHub")


def exact_ref_commit(
    document: dict[str, Any],
    expected_ref: str,
    label: str,
    failures: list[str],
) -> str | None:
    """Return the commit for one exact lightweight GitHub Git-reference object."""
    if document.get("ref") != expected_ref:
        failures.append(f"{label} must equal {expected_ref!r}")
    ref_object = document.get("object")
    if type(ref_object) is not dict:
        failures.append(f"{label} object is missing")
        return None
    sha = ref_object.get("sha")
    if ref_object.get("type") != "commit" or type(sha) is not str or OID_PATTERN.fullmatch(sha) is None:
        failures.append(f"{label} must be one lightweight ref to a lowercase commit SHA")
        return None
    return sha


def classify_publication_state(
    plan: dict[str, Any],
    metadata_path: Path,
    failures: list[str],
) -> str | None:
    """Classify only an exact frozen, newly published Release as immutable or mutable."""
    if not _validate_plan(plan, failures):
        return None
    document = _load_json_object(metadata_path, "post-publication release metadata", failures)
    if document is None:
        return None
    release = plan["release"]
    subject = plan["subject"]
    expected_fields = {
        "id": release["id"],
        "tag_name": subject["tag"],
        "target_commitish": subject["commit"],
        "draft": False,
        "prerelease": False,
    }
    for field, expected in expected_fields.items():
        if document.get(field) != expected:
            failures.append(f"post-publication release.{field} must equal {expected!r}")
    immutable = document.get("immutable")
    if type(immutable) is not bool:
        failures.append("post-publication release.immutable must be a boolean")
    if failures:
        return None
    return "immutable" if immutable else "mutable"


def _validate_local_asset(
    path: Path,
    metadata: dict[str, Any],
    label: str,
    failures: list[str],
) -> str | None:
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
    filename_digest = metadata["name"].removesuffix(".json").rsplit("-", 1)[-1]
    if filename_digest != digest:
        failures.append(f"{label} filename SHA-256 does not match downloaded bytes")
    github_digest = metadata["digest"]
    if github_digest is not None and github_digest != f"sha256:{digest}":
        failures.append(f"{label} GitHub digest does not match downloaded bytes")
    return digest


def _attestation_document(plan: dict[str, Any], digest: str) -> dict[str, Any]:
    subject = plan["subject"]
    asset = plan["observationAsset"]
    return {
        "asset": {
            "githubDigest": asset["digest"],
            "id": asset["id"],
            "name": asset["name"],
            "sha256": digest,
            "size": asset["size"],
        },
        "kind": ATTESTATION_KIND,
        "release": {
            "commit": subject["commit"],
            "id": plan["release"]["id"],
            "notesSha256": plan["release"]["notesSha256"],
            "tag": subject["tag"],
            "tree": subject["tree"],
            "version": subject["version"],
        },
        "schemaVersion": ATTESTATION_SCHEMA_VERSION,
        "validation": {
            "status": "pass",
            "validator": "scripts/check-release-evidence.py",
        },
    }


def validate_downloaded_observation(
    plan: dict[str, Any],
    asset_path: Path,
    *,
    attestation_directory: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> Path | None:
    """Validate exact downloaded bytes and emit one deterministic attestation."""
    if not _validate_plan(plan, failures):
        return None
    subject = plan["subject"]
    digest = _validate_local_asset(
        asset_path, plan["observationAsset"], "downloaded routing-observation asset", failures
    )
    validate_external_routing_observation(
        asset_path,
        expected_version=subject["version"],
        expected_tag=subject["tag"],
        expected_commit=subject["commit"],
        expected_tree=subject["tree"],
        failures=failures,
        root=root,
    )
    if digest is None or failures:
        return None
    try:
        canonical_directory = attestation_directory.resolve(strict=True)
        canonical_directory.relative_to(root.resolve())
    except ValueError:
        pass
    except OSError as error:
        failures.append(f"cannot resolve attestation directory: {error}")
        return None
    else:
        failures.append("release attestation must be generated outside the checked-in tree")
        return None
    document = _attestation_document(plan, digest)
    payload = _canonical_json_bytes(document)
    attestation_digest = hashlib.sha256(payload).hexdigest()
    path = canonical_directory / (
        f"{_attestation_prefix(subject['version'])}{attestation_digest}.json"
    )
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except OSError as error:
        failures.append(f"cannot write release attestation: {error}")
        return None
    return path


def verify_release_snapshot(
    plan: dict[str, Any],
    metadata_path: Path,
    asset_path: Path,
    attestation_path: Path,
    *,
    final: bool,
    latest_metadata_path: Path | None,
    prepublish_metadata_path: Path | None,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> None:
    """Revalidate the exact asset set before publication and after immutability."""
    if not _validate_plan(plan, failures):
        return
    subject = plan["subject"]
    document = _load_json_object(metadata_path, "current release metadata", failures)
    if document is None:
        return
    release = _inspect_release(
        document,
        version=subject["version"],
        tag=subject["tag"],
        commit=subject["commit"],
        expected_phase="final" if final else "draft",
        failures=failures,
    )
    observation, attestation = _select_assets(
        document,
        version=subject["version"],
        attestation_requirement="required",
        failures=failures,
    )
    if release is not None and release != plan["release"]:
        failures.append("release identity changed after draft evidence was frozen")
    if observation is not None and observation != plan["observationAsset"]:
        failures.append("routing-observation asset identity or metadata changed after validation")
    if (
        plan["attestationAsset"] is not None
        and attestation is not None
        and attestation != plan["attestationAsset"]
    ):
        failures.append("release-attestation asset identity or metadata changed after validation")
    digest = _validate_local_asset(
        asset_path, plan["observationAsset"], "downloaded routing-observation asset", failures
    )
    validate_external_routing_observation(
        asset_path,
        expected_version=subject["version"],
        expected_tag=subject["tag"],
        expected_commit=subject["commit"],
        expected_tree=subject["tree"],
        failures=failures,
        root=root,
    )
    if digest is not None:
        expected_attestation = _attestation_document(plan, digest)
        actual_attestation = _load_json_object(
            attestation_path, "local release attestation", failures
        )
        if actual_attestation is not None and actual_attestation != expected_attestation:
            failures.append("local release attestation does not match the validated binding")
        if attestation is not None:
            _validate_local_asset(
                attestation_path, attestation, "release evidence-attestation asset", failures
            )
    if final:
        if prepublish_metadata_path is None:
            if plan["phase"] != "final":
                failures.append("initial final verification requires pre-publication metadata")
        else:
            prepublish_document = _load_json_object(
                prepublish_metadata_path, "pre-publication release metadata", failures
            )
            if prepublish_document is not None:
                prepublish_release = _inspect_release(
                    prepublish_document,
                    version=subject["version"],
                    tag=subject["tag"],
                    commit=subject["commit"],
                    expected_phase="draft",
                    failures=failures,
                )
                prepublish_observation, prepublish_attestation = _select_assets(
                    prepublish_document,
                    version=subject["version"],
                    attestation_requirement="required",
                    failures=failures,
                )
                if prepublish_release is not None and prepublish_release != plan["release"]:
                    failures.append("pre-publication release identity differs from the frozen draft")
                if prepublish_observation != observation:
                    failures.append("routing-observation asset changed during final publication")
                if prepublish_attestation != attestation:
                    failures.append("release attestation asset changed during final publication")
        if latest_metadata_path is None:
            failures.append("final verification requires latest-release metadata")
        else:
            latest = _load_json_object(
                latest_metadata_path, "latest release metadata", failures
            )
            if latest is not None and (
                latest.get("id") != plan["release"]["id"]
                or latest.get("tag_name") != subject["tag"]
            ):
                failures.append("GitHub Latest does not identify the immutable release")


def _scalar(value: Any) -> str | None:
    return value.value if isinstance(value, CanonicalYamlScalar) else None


def _check_publish_version_gate(text: str, label: str, failures: list[str]) -> None:
    owners = re.findall(
        r'^\s*\[\[ "\$RELEASE_TAG" =~ (?P<pattern>\S+) \]\]\s*$',
        text,
        flags=re.MULTILINE,
    )
    if owners != [PRODUCTION_RELEASE_TAG_ERE_PATTERN]:
        failures.append(
            f"{label} must contain one canonical stable production release tag gate"
        )
        return
    pattern = re.compile(owners[0])
    for case_id, version, accepted in PRODUCTION_RELEASE_VERSION_CASES:
        observed = pattern.fullmatch(f"v{version}") is not None
        if observed != accepted:
            failures.append(
                f"{label} publication version gate disagrees with canonical case "
                f"{case_id!r}"
            )


def check_publish_workflow_contract(
    failures: list[str], workflow_path: Path = WORKFLOW_PATH
) -> dict[str, Any] | None:
    """Validate the narrow manually authorized draft-to-immutable workflow."""
    try:
        payload = workflow_path.read_bytes()
        text = payload.decode("utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(workflow_path)}: {error}")
        return None
    except UnicodeDecodeError as error:
        failures.append(f"invalid UTF-8 in {display_path(workflow_path)}: {error}")
        return None
    label = display_path(workflow_path)
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None
    if set(document) != {"name", "on", "permissions", "concurrency", "jobs"}:
        failures.append(
            f"{label} must contain only name, on, permissions, concurrency, and jobs"
        )
    if _scalar(document.get("name")) != "Publish immutable release":
        failures.append(f"{label} must keep its exact public workflow name")
    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {"workflow_dispatch"}:
        failures.append(f"{label} must be workflow_dispatch-only")
    else:
        dispatch = triggers.get("workflow_dispatch")
        inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
        tag_input = inputs.get("tag") if isinstance(inputs, dict) else None
        if not isinstance(inputs, dict) or set(inputs) != {"tag"}:
            failures.append(f"{label} must accept only one tag input")
        if not isinstance(tag_input, dict) or {
            key: _scalar(value) for key, value in tag_input.items()
        } != {
            "description": "Existing stable numeric release tag on signed main history",
            "required": "true",
            "type": "string",
        }:
            failures.append(f"{label} tag input contract changed")
    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"contents"}:
        failures.append(f"{label} must grant only contents permission")
    elif _scalar(permissions.get("contents")) != "write":
        failures.append(f"{label} requires exactly contents: write")
    concurrency = document.get("concurrency")
    if not isinstance(concurrency, dict) or {
        key: _scalar(value) for key, value in concurrency.items()
    } != {
        "group": "publish-immutable-release",
        "cancel-in-progress": "false",
    }:
        failures.append(f"{label} must serialize all Latest publication without cancellation")
    jobs = document.get("jobs")
    job = jobs.get("publish-immutable-release") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"publish-immutable-release"}:
        failures.append(f"{label} must declare only publish-immutable-release")
    if not isinstance(job, dict):
        failures.append(f"{label} publish-immutable-release job is malformed")
    else:
        if set(job) != {"if", "runs-on", "timeout-minutes", "env", "steps"}:
            failures.append(f"{label} publication job contains unexpected fields")
        if _scalar(job.get("runs-on")) != "ubuntu-24.04":
            failures.append(f"{label} must use the fixed ubuntu-24.04 runner")
        if _scalar(job.get("timeout-minutes")) != "15":
            failures.append(f"{label} must keep the 15-minute timeout")
        if _scalar(job.get("if")) != "github.ref == format('refs/tags/{0}', inputs.tag)":
            failures.append(f"{label} must run only when dispatched from the exact input tag")
        env = job.get("env")
        if not isinstance(env, dict) or {
            key: _scalar(value) for key, value in env.items()
        } != {
            "GH_TOKEN": "${{ github.token }}",
            "RELEASE_TAG": "${{ inputs.tag }}",
            "GITHUB_API_VERSION": "2026-03-10",
        }:
            failures.append(f"{label} publication environment changed")
        steps = job.get("steps")
        if not isinstance(steps, list) or len(steps) != 3:
            failures.append(f"{label} must contain exactly checkout, Python, and publication steps")
        else:
            expected_steps = (
                {
                    "name": "Check out the authorized release tag commit",
                    "uses": "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                    "with": {
                        "ref": "${{ github.sha }}",
                        "persist-credentials": "false",
                        "fetch-depth": "0",
                    },
                },
                {
                    "name": "Set up Python",
                    "uses": "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
                    "with": {"python-version": "3.14.7"},
                },
            )
            for step, expected in zip(steps[:2], expected_steps):
                if not isinstance(step, dict) or {
                    key: (
                        {nested: _scalar(value) for nested, value in current.items()}
                        if isinstance(current, dict)
                        else _scalar(current)
                    )
                    for key, current in step.items()
                } != expected:
                    failures.append(f"{label} pinned setup step contract changed")
            publication_step = steps[2]
            if not isinstance(publication_step, dict) or {
                key: _scalar(value) for key, value in publication_step.items()
            } != {
                "name": "Validate evidence and publish the immutable release",
                "shell": "bash",
                "run": "|",
            }:
                failures.append(f"{label} publication step envelope changed")
    required_anchors = (
        "uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
        "ref: ${{ github.sha }}",
        "persist-credentials: false",
        "fetch-depth: 0",
        "uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
        'python-version: "3.14.7"',
        '[[ "$RELEASE_TAG" =~ ^v',
        'git rev-parse "refs/tags/${RELEASE_TAG}^{commit}"',
        "git/ref/heads/main",
        "git/ref/tags/$RELEASE_TAG",
        "scripts/check-release-evidence.py ref-commit",
        "compare/$commit...$main_sha",
        "commits/$commit",
        "scripts/check-release-evidence.py preflight",
        "scripts/check-release-evidence.py select",
        "scripts/check-release-evidence.py prepare",
        "releases/assets/$observation_id",
        "scripts/check-release-evidence.py validate",
        "https://uploads.github.com/repos/$GITHUB_REPOSITORY/releases/$release_id/assets",
        "scripts/check-release-evidence.py verify",
        'draft=false',
        'make_latest=true',
        "scripts/check-release-evidence.py publication-state",
        'test "$release_phase" = "published-mutable"',
        "remote_preflight draft-mutation true",
        "gh api --method DELETE",
        "scripts/check-release-evidence.py assert-absent",
        "releases/latest",
        "--final",
    )
    for anchor in required_anchors:
        if anchor not in text:
            failures.append(f"{label} is missing required publication anchor {anchor!r}")
    _check_publish_version_gate(text, label, failures)
    if 'GITHUB_API_VERSION: "2026-03-10"' not in text:
        failures.append(f"{label} must pin GitHub REST API version 2026-03-10")
    if hashlib.sha256(payload).hexdigest() != PUBLISH_WORKFLOW_SHA256:
        failures.append(f"{label} complete publication command contract changed")
    for forbidden in (
        "pull_request:",
        "pull_request_target:",
        "schedule:",
        "${{ secrets.",
        "immutable-releases",
        "--clobber",
        "force",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden publication surface {forbidden!r}")
    return document


def _add_subject_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-tag", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-tree", required=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    select = commands.add_parser("select", help="select one exact Release from a listing")
    select.add_argument("--release-collection", type=Path, required=True)
    select.add_argument("--release-output", type=Path, required=True)
    select.add_argument("--expected-tag", required=True)
    preflight = commands.add_parser("preflight", help="verify exact live release refs and target")
    preflight.add_argument("--repository-metadata", type=Path, required=True)
    preflight.add_argument("--latest-release-metadata", type=Path, required=True)
    preflight.add_argument("--main-ref-metadata", type=Path, required=True)
    preflight.add_argument("--tag-ref-metadata", type=Path, required=True)
    preflight.add_argument("--history-comparison", type=Path, required=True)
    preflight.add_argument("--commit-metadata", type=Path, required=True)
    preflight.add_argument("--graphql-signature", type=Path, required=True)
    preflight.add_argument("--expected-commit", required=True)
    preflight.add_argument("--expected-tag", required=True)
    preflight.add_argument("--require-main-tip", action="store_true")
    ref_commit = commands.add_parser(
        "ref-commit", help="emit the commit for one exact lightweight GitHub ref"
    )
    ref_commit.add_argument("--ref-metadata", type=Path, required=True)
    ref_commit.add_argument("--expected-ref", required=True)
    prepare = commands.add_parser("prepare", help="freeze one exact Release and its assets")
    prepare.add_argument("--release-metadata", type=Path, required=True)
    prepare.add_argument("--plan-output", type=Path, required=True)
    _add_subject_arguments(prepare)
    emit = commands.add_parser("emit", help="emit one allowlisted plan field")
    emit.add_argument("--plan", type=Path, required=True)
    emit.add_argument(
        "--field",
        choices=(
            "release-id",
            "phase",
            "asset-id",
            "asset-name",
            "attestation-present",
            "attestation-id",
            "attestation-name",
        ),
        required=True,
    )
    validate = commands.add_parser("validate", help="validate downloaded asset bytes")
    validate.add_argument("--plan", type=Path, required=True)
    validate.add_argument("--asset", type=Path, required=True)
    validate.add_argument("--attestation-directory", type=Path, required=True)
    verify = commands.add_parser("verify", help="verify pre-publish or final release state")
    verify.add_argument("--plan", type=Path, required=True)
    verify.add_argument("--release-metadata", type=Path, required=True)
    verify.add_argument("--asset", type=Path, required=True)
    verify.add_argument("--attestation", type=Path, required=True)
    verify.add_argument("--final", action="store_true")
    verify.add_argument("--latest-release-metadata", type=Path)
    verify.add_argument("--prepublish-release-metadata", type=Path)
    publication_state = commands.add_parser(
        "publication-state",
        help="classify one exact post-publication Release for bounded compensation",
    )
    publication_state.add_argument("--plan", type=Path, required=True)
    publication_state.add_argument("--release-metadata", type=Path, required=True)
    absent = commands.add_parser(
        "assert-absent", help="verify bounded cleanup removed the frozen mutable Release"
    )
    absent.add_argument("--plan", type=Path, required=True)
    absent.add_argument("--release-collection", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures: list[str] = []
    if args.command == "select":
        select_release_from_collection(
            args.release_collection,
            args.release_output,
            expected_tag=args.expected_tag,
            failures=failures,
        )
    elif args.command == "preflight":
        verify_remote_release_preflight(
            args.repository_metadata,
            args.latest_release_metadata,
            args.main_ref_metadata,
            args.tag_ref_metadata,
            args.history_comparison,
            args.commit_metadata,
            args.graphql_signature,
            expected_commit=args.expected_commit,
            expected_tag=args.expected_tag,
            require_main_tip=args.require_main_tip,
            failures=failures,
        )
    elif args.command == "ref-commit":
        document = _load_json_object(args.ref_metadata, "GitHub ref metadata", failures)
        if document is not None:
            commit = exact_ref_commit(
                document,
                args.expected_ref,
                "GitHub ref metadata",
                failures,
            )
            if commit is not None and not failures:
                print(commit)
    elif args.command == "prepare":
        plan = prepare_release_plan(
            args.release_metadata,
            expected_version=args.expected_version,
            expected_tag=args.expected_tag,
            expected_commit=args.expected_commit,
            expected_tree=args.expected_tree,
            failures=failures,
        )
        if plan is not None and not failures:
            _write_json(args.plan_output, plan, failures)
    elif args.command == "emit":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            values = {
                "release-id": plan["release"]["id"],
                "phase": plan["phase"],
                "asset-id": plan["observationAsset"]["id"],
                "asset-name": plan["observationAsset"]["name"],
                "attestation-present": (
                    "true" if plan["attestationAsset"] is not None else "false"
                ),
            }
            if args.field in {"attestation-id", "attestation-name"}:
                attestation = plan["attestationAsset"]
                if attestation is None:
                    failures.append("release evidence plan has no attestation asset")
                else:
                    print(attestation[args.field.removeprefix("attestation-")])
            else:
                print(values[args.field])
    elif args.command == "validate":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            path = validate_downloaded_observation(
                plan,
                args.asset,
                attestation_directory=args.attestation_directory,
                failures=failures,
            )
            if path is not None and not failures:
                print(path)
    elif args.command == "verify":
        plan = load_release_plan(args.plan, failures)
        if plan is not None:
            verify_release_snapshot(
                plan,
                args.release_metadata,
                args.asset,
                args.attestation,
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
            assert_release_absent_from_collection(
                args.release_collection,
                plan,
                failures,
            )
    if failures:
        print("Release evidence validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
