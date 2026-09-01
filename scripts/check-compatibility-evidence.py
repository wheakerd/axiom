#!/usr/bin/env python3
"""Validate Axiom compatibility evidence without third-party dependencies."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import stat
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.no_hook_bundle import check_no_hook_bundle  # noqa: E402
from axiom_validation.runtime_identity import check_runtime_identity  # noqa: E402


EVIDENCE_ROOT = REPOSITORY_ROOT / "evidence"
SCHEMA_V1_PATH = EVIDENCE_ROOT / "schema-v1.json"
SCHEMA_V2_PATH = EVIDENCE_ROOT / "schema-v2.json"
STATUS_PATH = EVIDENCE_ROOT / "release-status.json"
RUNTIME_IDENTITY_PATH = EVIDENCE_ROOT / "runtime-identity.json"
RUNTIME_HISTORY_PATH = EVIDENCE_ROOT / "runtime-contract-history-v1.json"
POLICY_REVISIONS_PATH = EVIDENCE_ROOT / "repository-policy-revisions-v1.json"
PROFILE_STATIC_EVIDENCE_PATH = (
    EVIDENCE_ROOT / "profiles/openai-hook-independent-v1/bundle-v1.json"
)
MANIFEST_PATHS = (
    REPOSITORY_ROOT / ".codex-plugin" / "plugin.json",
    REPOSITORY_ROOT / ".claude-plugin" / "plugin.json",
)
MAX_JSON_BYTES = 256 * 1024

RECORD_KEYS = frozenset(
    {
        "schemaVersion",
        "release",
        "host",
        "installation",
        "hook",
        "reporter",
        "recordedAt",
        "cases",
    }
)
RECORD_V2_KEYS = frozenset((*RECORD_KEYS, "runtimeIdentity", "observationSubject"))
RUNTIME_IDENTITY_KEYS = frozenset(
    {"pluginVersion", "runtimeContractSchemaVersion", "runtimeContractDigest"}
)
RELEASE_KEYS = frozenset({"version", "tag", "commit"})
HOST_KEYS = frozenset(
    {"name", "version", "operatingSystem", "architecture", "shell"}
)
INSTALLATION_KEYS = frozenset(
    {"method", "targetPluginVersion", "installedSnapshotVerified"}
)
HOOK_KEYS = frozenset(
    {
        "event",
        "matcher",
        "expectedCommandSha256",
        "installedCommandSha256",
        "installedCommandVerified",
    }
)
REPORTER_KEYS = frozenset({"identity", "anonymous"})
CASE_KEYS = frozenset(
    {
        "id",
        "sessionKind",
        "lifecycleSource",
        "compactionMode",
        "request",
        "expectedRoute",
        "observedRoute",
        "noRouteControl",
        "inspected",
        "mutationAttempted",
        "mutationObserved",
        "result",
        "limitations",
        "supportingOutput",
    }
)
CASE_CONTRACTS = {
    "startup-routed": ("fresh", "startup", "not-applicable", False, "agents-architect"),
    "startup-no-route": ("fresh", "startup", "not-applicable", True, "none"),
    "manual-compaction-routed": (
        "post-compaction",
        "compact",
        "manual",
        False,
        "agents-architect",
    ),
    "manual-compaction-no-route": (
        "post-compaction",
        "compact",
        "manual",
        True,
        "none",
    ),
    "automatic-compaction-routed": (
        "post-compaction",
        "compact",
        "automatic",
        False,
        "agents-architect",
    ),
    "automatic-compaction-no-route": (
        "post-compaction",
        "compact",
        "automatic",
        True,
        "none",
    ),
}
RESULTS = frozenset({"pass", "fail", "not-run", "unavailable"})
HOST_NAMES = frozenset({"codex", "claude-code"})
SEMVER_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
PREFIXED_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
PRIVATE_PATTERNS = (
    (re.compile(r"/(?:home|Users|tmp)/"), "absolute private path"),
    (re.compile(r"[A-Za-z]:\\Users\\"), "absolute Windows user path"),
    (re.compile(r"https?://", re.IGNORECASE), "URL"),
    (
        re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,})"),
        "token-like value",
    ),
    (
        re.compile(
            r"(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|bearer)\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        "credential-like value",
    ),
    (re.compile(r"\bthread[_ -]?id\b", re.IGNORECASE), "session identifier"),
)


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return path.name


def load_json(path: Path, failures: list[str]) -> dict[str, Any] | None:
    try:
        metadata = path.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {display_path(path)}: {error}")
        return None
    if stat.S_ISLNK(metadata.st_mode):
        failures.append(f"{display_path(path)} must not be a symbolic link")
        return None
    if not stat.S_ISREG(metadata.st_mode):
        failures.append(f"{display_path(path)} must be a regular file")
        return None
    if metadata.st_size > MAX_JSON_BYTES:
        failures.append(
            f"{display_path(path)} exceeds the {MAX_JSON_BYTES}-byte evidence limit"
        )
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {display_path(path)}: {error}")
        return None
    if type(value) is not dict:
        failures.append(f"{display_path(path)} must contain a top-level object")
        return None
    return value


def exact_object(
    value: Any,
    expected_keys: frozenset[str],
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(expected_keys - set(value))
    unknown = sorted(set(value) - expected_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def require_string(
    value: Any,
    label: str,
    failures: list[str],
    *,
    maximum: int = 500,
) -> str | None:
    if type(value) is not str or not value:
        failures.append(f"{label} must be a non-empty string")
        return None
    if len(value) > maximum:
        failures.append(f"{label} exceeds {maximum} characters")
    return value


def require_bool(value: Any, label: str, failures: list[str]) -> bool | None:
    if type(value) is not bool:
        failures.append(f"{label} must be a boolean")
        return None
    return value


def require_string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    maximum_items: int = 8,
    maximum_length: int = 300,
) -> list[str] | None:
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return None
    if len(value) > maximum_items:
        failures.append(f"{label} exceeds {maximum_items} items")
    for index, item in enumerate(value):
        require_string(
            item,
            f"{label}[{index}]",
            failures,
            maximum=maximum_length,
        )
    return value


def check_privacy(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is dict:
        for key, child in value.items():
            check_privacy(child, f"{label}.{key}", failures)
        return
    if type(value) is list:
        for index, child in enumerate(value):
            check_privacy(child, f"{label}[{index}]", failures)
        return
    if type(value) is not str:
        return
    if len(value) > 500:
        failures.append(f"{label} exceeds the privacy-safe 500-character limit")
    for pattern, description in PRIVATE_PATTERNS:
        if pattern.search(value):
            failures.append(f"{label} contains a prohibited {description}")


def check_schema_v1_contract(schema: dict[str, Any], failures: list[str]) -> None:
    if schema.get("$id") != "urn:axiom:compatibility-evidence:schema:v1":
        failures.append("evidence/schema-v1.json has the wrong immutable schema identifier")
    if schema.get("additionalProperties") is not False:
        failures.append("evidence/schema-v1.json must reject unknown top-level fields")
    if set(schema.get("required", [])) != RECORD_KEYS:
        failures.append("evidence/schema-v1.json top-level required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != RECORD_KEYS:
        failures.append("evidence/schema-v1.json top-level properties drifted")
    definitions = schema.get("$defs")
    expected_definitions = {
        "release": RELEASE_KEYS,
        "host": HOST_KEYS,
        "installation": INSTALLATION_KEYS,
        "hook": HOOK_KEYS,
        "reporter": REPORTER_KEYS,
        "case": CASE_KEYS,
    }
    if type(definitions) is not dict:
        failures.append("evidence/schema-v1.json must define owned nested objects")
        return
    if set(definitions) != set(expected_definitions):
        failures.append("evidence/schema-v1.json nested definitions drifted")
    for name, keys in expected_definitions.items():
        definition = definitions.get(name)
        if type(definition) is not dict:
            failures.append(f"evidence/schema-v1.json is missing the {name} definition")
            continue
        if definition.get("additionalProperties") is not False:
            failures.append(f"evidence/schema-v1.json {name} must reject unknown fields")
        if set(definition.get("required", [])) != keys:
            failures.append(f"evidence/schema-v1.json {name} required fields drifted")
        nested_properties = definition.get("properties")
        if type(nested_properties) is not dict or set(nested_properties) != keys:
            failures.append(f"evidence/schema-v1.json {name} properties drifted")


def check_schema_v2_contract(schema: dict[str, Any], failures: list[str]) -> None:
    if schema.get("$id") != "urn:axiom:compatibility-evidence:schema:v2":
        failures.append("evidence/schema-v2.json has the wrong immutable schema identifier")
    if schema.get("additionalProperties") is not False:
        failures.append("evidence/schema-v2.json must reject unknown top-level fields")
    if set(schema.get("required", [])) != RECORD_V2_KEYS:
        failures.append("evidence/schema-v2.json top-level required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != RECORD_V2_KEYS:
        failures.append("evidence/schema-v2.json top-level properties drifted")
    else:
        if properties.get("schemaVersion", {}).get("const") != "2":
            failures.append("evidence/schema-v2.json schemaVersion must remain '2'")
        if (
            properties.get("observationSubject", {}).get("const")
            != "installed-runtime-contract"
        ):
            failures.append("evidence/schema-v2.json observationSubject drifted")
        expected_references = {
            "release": "schema-v1.json#/$defs/release",
            "runtimeIdentity": "#/$defs/runtimeIdentity",
            "host": "schema-v1.json#/$defs/host",
            "installation": "schema-v1.json#/$defs/installation",
            "hook": "schema-v1.json#/$defs/hook",
            "reporter": "schema-v1.json#/$defs/reporter",
        }
        for name, reference in expected_references.items():
            if properties.get(name) != {"$ref": reference}:
                failures.append(f"evidence/schema-v2.json {name} reference drifted")
        cases = properties.get("cases")
        if type(cases) is not dict or cases.get("items") != {
            "$ref": "schema-v1.json#/$defs/case"
        }:
            failures.append("evidence/schema-v2.json cases reference drifted")
    definitions = schema.get("$defs")
    runtime = definitions.get("runtimeIdentity") if type(definitions) is dict else None
    if type(runtime) is not dict:
        failures.append("evidence/schema-v2.json must define runtimeIdentity")
        return
    if runtime.get("additionalProperties") is not False:
        failures.append("evidence/schema-v2.json runtimeIdentity must reject unknown fields")
    if set(runtime.get("required", [])) != RUNTIME_IDENTITY_KEYS:
        failures.append("evidence/schema-v2.json runtimeIdentity required fields drifted")
    runtime_properties = runtime.get("properties")
    if type(runtime_properties) is not dict or set(runtime_properties) != RUNTIME_IDENTITY_KEYS:
        failures.append("evidence/schema-v2.json runtimeIdentity properties drifted")


def validate_case(case: Any, label: str, hook_verified: bool, failures: list[str]) -> None:
    document = exact_object(case, CASE_KEYS, label, failures)
    if document is None:
        return
    case_id = require_string(document.get("id"), f"{label}.id", failures, maximum=80)
    require_string(document.get("request"), f"{label}.request", failures)
    expected_route = require_string(
        document.get("expectedRoute"), f"{label}.expectedRoute", failures, maximum=80
    )
    observed_route = document.get("observedRoute")
    if observed_route is not None:
        require_string(observed_route, f"{label}.observedRoute", failures, maximum=80)
    no_route = require_bool(
        document.get("noRouteControl"), f"{label}.noRouteControl", failures
    )
    require_string_list(
        document.get("inspected"), f"{label}.inspected", failures, maximum_length=160
    )
    attempted = require_bool(
        document.get("mutationAttempted"), f"{label}.mutationAttempted", failures
    )
    observed_mutation = require_bool(
        document.get("mutationObserved"), f"{label}.mutationObserved", failures
    )
    result = document.get("result")
    if result not in RESULTS:
        failures.append(f"{label}.result must be one of {', '.join(sorted(RESULTS))}")
    limitations = require_string_list(
        document.get("limitations"), f"{label}.limitations", failures
    )
    supporting = require_string_list(
        document.get("supportingOutput"),
        f"{label}.supportingOutput",
        failures,
        maximum_length=200,
    )
    if case_id is not None:
        if not CASE_ID_PATTERN.fullmatch(case_id):
            failures.append(f"{label}.id is not lowercase kebab-case")
        contract = CASE_CONTRACTS.get(case_id)
        if contract is None:
            failures.append(f"{label}.id is not an owned evidence case")
        else:
            session_kind, lifecycle, compaction, control, route = contract
            expected_values = {
                "sessionKind": session_kind,
                "lifecycleSource": lifecycle,
                "compactionMode": compaction,
                "noRouteControl": control,
                "expectedRoute": route,
            }
            for field, expected in expected_values.items():
                if document.get(field) != expected:
                    failures.append(
                        f"{label}.{field} must be {expected!r} for case {case_id!r}"
                    )
    if no_route is True and expected_route != "none":
        failures.append(f"{label} marks a no-route control but expects a route")
    if no_route is False and expected_route == "none":
        failures.append(f"{label} is routed but expects no route")
    if observed_mutation is True and attempted is not True:
        failures.append(f"{label} observes a mutation without recording an attempt")
    if result != "fail" and (attempted is True or observed_mutation is True):
        failures.append(f"{label} records mutation without a failing result")
    if result == "pass":
        if observed_route != expected_route:
            failures.append(f"{label} passes without observing its expected route")
        if not supporting:
            failures.append(f"{label} passes without sanitized supporting output")
        if not hook_verified:
            failures.append(f"{label} passes without a verified installed hook")
    elif result in {"not-run", "unavailable"}:
        if observed_route is not None:
            failures.append(f"{label} has an observed route despite result {result!r}")
        if supporting:
            failures.append(f"{label} has supporting output despite result {result!r}")
        if not limitations:
            failures.append(f"{label} must explain result {result!r}")
    elif result == "fail" and not (limitations or supporting):
        failures.append(f"{label} must preserve evidence for a failure")
def validate_record(
    record: dict[str, Any],
    path: Path | None,
    failures: list[str],
) -> None:
    label = display_path(path) if path is not None else "record"
    schema_version = record.get("schemaVersion")
    expected_keys = RECORD_KEYS if schema_version == "1" else RECORD_V2_KEYS
    exact_object(record, expected_keys, label, failures)
    if schema_version not in {"1", "2"}:
        failures.append(f"{label}.schemaVersion must be '1' or '2'")

    release = exact_object(record.get("release"), RELEASE_KEYS, f"{label}.release", failures)
    version = tag = commit = None
    if release is not None:
        version = require_string(release.get("version"), f"{label}.release.version", failures)
        tag = require_string(release.get("tag"), f"{label}.release.tag", failures)
        commit = require_string(release.get("commit"), f"{label}.release.commit", failures)
        if version is not None and not SEMVER_PATTERN.fullmatch(version):
            failures.append(f"{label}.release.version must be strict SemVer")
        if version is not None and tag != f"v{version}":
            failures.append(f"{label}.release.tag does not match its version")
        if commit is not None and not COMMIT_PATTERN.fullmatch(commit):
            failures.append(f"{label}.release.commit must be a 40-character lowercase Git SHA")

    if schema_version == "2":
        runtime = exact_object(
            record.get("runtimeIdentity"),
            RUNTIME_IDENTITY_KEYS,
            f"{label}.runtimeIdentity",
            failures,
        )
        if runtime is not None:
            runtime_version = require_string(
                runtime.get("pluginVersion"),
                f"{label}.runtimeIdentity.pluginVersion",
                failures,
            )
            if runtime_version != version:
                failures.append(
                    f"{label}.runtimeIdentity.pluginVersion must match release.version"
                )
            if runtime.get("runtimeContractSchemaVersion") != "1":
                failures.append(
                    f"{label}.runtimeIdentity.runtimeContractSchemaVersion must be '1'"
                )
            runtime_digest = require_string(
                runtime.get("runtimeContractDigest"),
                f"{label}.runtimeIdentity.runtimeContractDigest",
                failures,
            )
            if (
                runtime_digest is not None
                and PREFIXED_DIGEST_PATTERN.fullmatch(runtime_digest) is None
            ):
                failures.append(
                    f"{label}.runtimeIdentity.runtimeContractDigest must be a SHA-256 identity"
                )
        if record.get("observationSubject") != "installed-runtime-contract":
            failures.append(f"{label}.observationSubject drifted")

    host = exact_object(record.get("host"), HOST_KEYS, f"{label}.host", failures)
    host_name = operating_system = None
    if host is not None:
        host_name = require_string(host.get("name"), f"{label}.host.name", failures)
        operating_system = require_string(
            host.get("operatingSystem"), f"{label}.host.operatingSystem", failures
        )
        require_string(host.get("version"), f"{label}.host.version", failures, maximum=80)
        require_string(
            host.get("architecture"), f"{label}.host.architecture", failures, maximum=80
        )
        require_string(host.get("shell"), f"{label}.host.shell", failures, maximum=80)
        if host_name not in HOST_NAMES:
            failures.append(f"{label}.host.name is not a supported evidence host")
        if operating_system is not None and operating_system != operating_system.lower():
            failures.append(f"{label}.host.operatingSystem must be lowercase")

    installation = exact_object(
        record.get("installation"), INSTALLATION_KEYS, f"{label}.installation", failures
    )
    snapshot_verified = None
    if installation is not None:
        require_string(
            installation.get("method"), f"{label}.installation.method", failures, maximum=240
        )
        target_version = require_string(
            installation.get("targetPluginVersion"),
            f"{label}.installation.targetPluginVersion",
            failures,
        )
        snapshot_verified = require_bool(
            installation.get("installedSnapshotVerified"),
            f"{label}.installation.installedSnapshotVerified",
            failures,
        )
        if target_version != version:
            failures.append(f"{label}.installation.targetPluginVersion must match release.version")

    hook = exact_object(record.get("hook"), HOOK_KEYS, f"{label}.hook", failures)
    hook_verified = False
    if hook is not None:
        if hook.get("event") != "SessionStart":
            failures.append(f"{label}.hook.event must be 'SessionStart'")
        if hook.get("matcher") != "startup|resume|clear|compact":
            failures.append(f"{label}.hook.matcher must cover the exact lifecycle sources")
        expected_digest = require_string(
            hook.get("expectedCommandSha256"),
            f"{label}.hook.expectedCommandSha256",
            failures,
        )
        installed_digest = hook.get("installedCommandSha256")
        if installed_digest is not None:
            require_string(
                installed_digest, f"{label}.hook.installedCommandSha256", failures
            )
        hook_verified_value = require_bool(
            hook.get("installedCommandVerified"),
            f"{label}.hook.installedCommandVerified",
            failures,
        )
        hook_verified = hook_verified_value is True
        if expected_digest is not None and not DIGEST_PATTERN.fullmatch(expected_digest):
            failures.append(f"{label}.hook.expectedCommandSha256 is not a SHA-256 digest")
        if installed_digest is not None and not DIGEST_PATTERN.fullmatch(installed_digest):
            failures.append(f"{label}.hook.installedCommandSha256 is not a SHA-256 digest")
        if hook_verified and installed_digest != expected_digest:
            failures.append(f"{label}.hook verified digest does not match the expected command")
        if not hook_verified and installed_digest is not None:
            failures.append(f"{label}.hook has an installed digest without verification")
        if snapshot_verified is not None and hook_verified != snapshot_verified:
            failures.append(f"{label} snapshot and installed-hook verification disagree")

    reporter = exact_object(
        record.get("reporter"), REPORTER_KEYS, f"{label}.reporter", failures
    )
    if reporter is not None:
        if reporter.get("identity") != "anonymous" or reporter.get("anonymous") is not True:
            failures.append(f"{label}.reporter must remain anonymous")

    recorded_at = require_string(record.get("recordedAt"), f"{label}.recordedAt", failures)
    if recorded_at is not None:
        try:
            datetime.strptime(recorded_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            failures.append(f"{label}.recordedAt must be a UTC second-precision timestamp")

    cases = record.get("cases")
    if type(cases) is not list:
        failures.append(f"{label}.cases must be an array")
    else:
        if len(cases) != len(CASE_CONTRACTS):
            failures.append(f"{label}.cases must contain exactly six lifecycle cases")
        case_ids = [case.get("id") for case in cases if type(case) is dict]
        if len(case_ids) != len(set(case_ids)):
            failures.append(f"{label}.cases repeats a case id")
        if set(case_ids) != set(CASE_CONTRACTS):
            failures.append(f"{label}.cases does not cover the owned lifecycle matrix")
        for index, case in enumerate(cases):
            validate_case(case, f"{label}.cases[{index}]", hook_verified, failures)

    if path is not None and version and host_name and operating_system:
        expected_path = EVIDENCE_ROOT / f"v{version}" / host_name / f"{operating_system}.json"
        if path.resolve() != expected_path.resolve():
            failures.append(
                f"{label} path must be {expected_path.relative_to(REPOSITORY_ROOT).as_posix()}"
            )
    check_privacy(record, label, failures)


STATUS_KEYS = frozenset(
    {
        "schemaVersion",
        "targetRelease",
        "runtimeIdentity",
        "status",
        "currentHostEvidence",
        "priorReleaseEvidence",
        "rules",
    }
)
TARGET_RELEASE_KEYS = frozenset({"version", "tag", "commit", "binding"})
STATUS_RUNTIME_KEYS = frozenset(
    {
        "pluginVersion",
        "repositoryPolicyRevision",
        "runtimeContractSchemaVersion",
        "runtimeContractDigest",
        "inputManifest",
        "history",
    }
)
CURRENT_HOST_KEYS = frozenset(
    {
        "host",
        "hostVersion",
        "lifecycleSource",
        "observationSubject",
        "observedAt",
        "pluginVersion",
        "runtimeContractDigest",
        "status",
        "reason",
    }
)
PRIOR_EVIDENCE_KEYS = frozenset(
    {
        "path",
        "tag",
        "commit",
        "host",
        "hostVersion",
        "recordedAt",
        "lifecycleSources",
        "observationSubject",
        "runtimeContractDigest",
        "status",
    }
)
RULE_KEYS = frozenset(
    {
        "priorEvidenceIsCurrent",
        "hostPassRequiresImmutableBinding",
        "postTagReleaseAssetMaySupplementStatus",
        "checkedInStatusMayBePromotedByAsset",
        "futureEvidenceRequiresRuntimeIdentity",
        "identicalRuntimeDigestDoesNotClaimNewObservation",
    }
)


def manifest_version(failures: list[str]) -> str | None:
    versions: list[str] = []
    for path in MANIFEST_PATHS:
        document = load_json(path, failures)
        if document is None:
            continue
        version = require_string(document.get("version"), f"{display_path(path)}.version", failures)
        if version is not None:
            if not SEMVER_PATTERN.fullmatch(version):
                failures.append(f"{display_path(path)}.version must be strict SemVer")
            versions.append(version)
    if len(set(versions)) > 1:
        failures.append("plugin manifest versions disagree")
    return versions[0] if len(versions) == len(MANIFEST_PATHS) else None


def validate_status(
    status: dict[str, Any],
    records: dict[str, dict[str, Any]],
    current_version: str | None,
    runtime_identity: dict[str, Any],
    runtime_history: dict[str, Any],
    failures: list[str],
) -> None:
    label = "evidence/release-status.json"
    exact_object(status, STATUS_KEYS, label, failures)
    if status.get("schemaVersion") != "2":
        failures.append(f"{label}.schemaVersion must be '2'")
    target = exact_object(
        status.get("targetRelease"), TARGET_RELEASE_KEYS, f"{label}.targetRelease", failures
    )
    target_version = None
    if target is not None:
        target_version = require_string(
            target.get("version"), f"{label}.targetRelease.version", failures
        )
        target_tag = require_string(target.get("tag"), f"{label}.targetRelease.tag", failures)
        if target_version is not None and not SEMVER_PATTERN.fullmatch(target_version):
            failures.append(f"{label}.targetRelease.version must be strict SemVer")
        if target_version is not None and target_tag != f"v{target_version}":
            failures.append(f"{label}.targetRelease.tag does not match its version")
        if target_version != current_version:
            failures.append(f"{label}.targetRelease.version must match both plugin manifests")
        if target.get("commit") is not None:
            failures.append(f"{label}.targetRelease.commit must remain null in a checked-in status")
        if target.get("binding") != "pending-immutable-tag":
            failures.append(f"{label}.targetRelease.binding must expose the unresolved self-binding")

    status_runtime = exact_object(
        status.get("runtimeIdentity"),
        STATUS_RUNTIME_KEYS,
        f"{label}.runtimeIdentity",
        failures,
    )
    canonical_runtime = runtime_identity.get("runtimeContract", {})
    if status_runtime is not None:
        expected_runtime = {
            "pluginVersion": runtime_identity.get("pluginVersion"),
            "repositoryPolicyRevision": runtime_identity.get("repositoryPolicyRevision"),
            "runtimeContractSchemaVersion": canonical_runtime.get("schemaVersion"),
            "runtimeContractDigest": canonical_runtime.get("digest"),
            "inputManifest": canonical_runtime.get("inputManifest"),
            "history": "evidence/runtime-contract-history-v1.json",
        }
        for field, expected in expected_runtime.items():
            if status_runtime.get(field) != expected:
                failures.append(f"{label}.runtimeIdentity.{field} drifted")
        if status_runtime.get("pluginVersion") != target_version:
            failures.append(f"{label}.runtimeIdentity.pluginVersion must match targetRelease")
        digest = status_runtime.get("runtimeContractDigest")
        if type(digest) is not str or PREFIXED_DIGEST_PATTERN.fullmatch(digest) is None:
            failures.append(f"{label}.runtimeIdentity.runtimeContractDigest is invalid")
    if status.get("status") != "STATIC-ONLY":
        failures.append(f"{label}.status must remain STATIC-ONLY before immutable publication")

    current = status.get("currentHostEvidence")
    current_hosts: set[str] = set()
    if type(current) is not list:
        failures.append(f"{label}.currentHostEvidence must be an array")
    else:
        for index, item in enumerate(current):
            item_label = f"{label}.currentHostEvidence[{index}]"
            document = exact_object(item, CURRENT_HOST_KEYS, item_label, failures)
            if document is None:
                continue
            host = document.get("host")
            if host not in HOST_NAMES:
                failures.append(f"{item_label}.host is unsupported")
            else:
                current_hosts.add(host)
            if document.get("status") not in {"not-run", "unknown", "unavailable"}:
                failures.append(f"{item_label}.status cannot imply a current host pass")
            if document.get("hostVersion") is not None:
                failures.append(f"{item_label}.hostVersion must remain null without a current run")
            if document.get("lifecycleSource") is not None:
                failures.append(f"{item_label}.lifecycleSource must remain null without a current run")
            if document.get("observedAt") is not None:
                failures.append(f"{item_label}.observedAt must remain null without a current run")
            if document.get("observationSubject") != "installed-runtime-contract":
                failures.append(f"{item_label}.observationSubject drifted")
            if document.get("pluginVersion") != target_version:
                failures.append(f"{item_label}.pluginVersion must match targetRelease")
            if status_runtime is not None and document.get("runtimeContractDigest") != status_runtime.get(
                "runtimeContractDigest"
            ):
                failures.append(f"{item_label}.runtimeContractDigest must match current identity")
            require_string(document.get("reason"), f"{item_label}.reason", failures, maximum=300)
        if current_hosts != HOST_NAMES:
            failures.append(f"{label}.currentHostEvidence must name both hosts exactly once")
        if len(current) != len(current_hosts):
            failures.append(f"{label}.currentHostEvidence repeats a host")

    prior = status.get("priorReleaseEvidence")
    referenced_paths: set[str] = set()
    history_by_tag = {
        item.get("tag"): item
        for item in runtime_history.get("entries", [])
        if type(item) is dict and type(item.get("tag")) is str
    }
    if type(prior) is not list:
        failures.append(f"{label}.priorReleaseEvidence must be an array")
    else:
        for index, item in enumerate(prior):
            item_label = f"{label}.priorReleaseEvidence[{index}]"
            document = exact_object(item, PRIOR_EVIDENCE_KEYS, item_label, failures)
            if document is None:
                continue
            path_value = require_string(
                document.get("path"), f"{item_label}.path", failures, maximum=200
            )
            tag = require_string(document.get("tag"), f"{item_label}.tag", failures)
            commit = require_string(document.get("commit"), f"{item_label}.commit", failures)
            if document.get("status") not in {"partial-host-observed", "unavailable", "not-run"}:
                failures.append(f"{item_label}.status is not a prior-evidence state")
            if document.get("observationSubject") != "installed-runtime-contract":
                failures.append(f"{item_label}.observationSubject drifted")
            if path_value is None:
                continue
            if path_value.startswith("/") or ".." in Path(path_value).parts:
                failures.append(f"{item_label}.path must be repository-relative")
                continue
            referenced_paths.add(path_value)
            record = records.get(path_value)
            if record is None:
                failures.append(f"{item_label}.path does not identify a checked-in record")
                continue
            release = record.get("release", {})
            if release.get("tag") != tag or release.get("commit") != commit:
                failures.append(f"{item_label} binding disagrees with its evidence record")
            host = record.get("host", {})
            if document.get("host") != host.get("name"):
                failures.append(f"{item_label}.host disagrees with its evidence record")
            if document.get("hostVersion") != host.get("version"):
                failures.append(f"{item_label}.hostVersion disagrees with its evidence record")
            if document.get("recordedAt") != record.get("recordedAt"):
                failures.append(f"{item_label}.recordedAt disagrees with its evidence record")
            lifecycle_sources = sorted(
                {
                    case.get("lifecycleSource")
                    for case in record.get("cases", [])
                    if type(case) is dict and type(case.get("lifecycleSource")) is str
                }
            )
            if document.get("lifecycleSources") != lifecycle_sources:
                failures.append(f"{item_label}.lifecycleSources disagree with its evidence record")
            history_entry = history_by_tag.get(tag)
            if history_entry is None:
                failures.append(f"{item_label} has no derived runtime history entry")
            elif document.get("runtimeContractDigest") != history_entry.get(
                "runtimeContractDigest"
            ):
                failures.append(f"{item_label}.runtimeContractDigest disagrees with tag history")
            if release.get("version") == target_version:
                failures.append(f"{item_label} carries current-release evidence into STATIC-ONLY status")
        if referenced_paths != set(records):
            failures.append(f"{label}.priorReleaseEvidence must enumerate every checked-in record")

    rules = exact_object(status.get("rules"), RULE_KEYS, f"{label}.rules", failures)
    if rules is not None:
        expected_rules = {
            "priorEvidenceIsCurrent": False,
            "hostPassRequiresImmutableBinding": True,
            "postTagReleaseAssetMaySupplementStatus": True,
            "checkedInStatusMayBePromotedByAsset": False,
            "futureEvidenceRequiresRuntimeIdentity": True,
            "identicalRuntimeDigestDoesNotClaimNewObservation": True,
        }
        for key, expected in expected_rules.items():
            if rules.get(key) is not expected:
                failures.append(f"{label}.rules.{key} must be {expected!r}")
    check_privacy(status, label, failures)


def collect_records(failures: list[str]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(EVIDENCE_ROOT.glob("v*/*/*.json")):
        document = load_json(path, failures)
        if document is None:
            continue
        validate_record(document, path, failures)
        records[path.relative_to(REPOSITORY_ROOT).as_posix()] = document
    expected_json = {
        SCHEMA_V1_PATH.resolve(),
        SCHEMA_V2_PATH.resolve(),
        STATUS_PATH.resolve(),
        RUNTIME_IDENTITY_PATH.resolve(),
        RUNTIME_HISTORY_PATH.resolve(),
        POLICY_REVISIONS_PATH.resolve(),
        PROFILE_STATIC_EVIDENCE_PATH.resolve(),
    }
    expected_json.update((REPOSITORY_ROOT / path).resolve() for path in records)
    unexpected_json = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in EVIDENCE_ROOT.rglob("*.json")
        if path.resolve() not in expected_json
    )
    if unexpected_json:
        failures.append("unowned evidence JSON files: " + ", ".join(unexpected_json))
    if not records:
        failures.append("no version-bound compatibility evidence records were found")
    return records


def expect_fixture_failure(
    name: str,
    document: dict[str, Any],
    validator: Callable[[dict[str, Any], list[str]], None],
    failures: list[str],
) -> None:
    fixture_failures: list[str] = []
    validator(document, fixture_failures)
    if not fixture_failures:
        failures.append(f"negative evidence fixture {name!r} was accepted")


def check_negative_fixtures(
    records: dict[str, dict[str, Any]],
    status: dict[str, Any],
    current_version: str | None,
    runtime_identity: dict[str, Any],
    runtime_history: dict[str, Any],
    failures: list[str],
) -> int:
    codex_path = "evidence/v0.7.4/codex/linux.json"
    source = records.get(codex_path)
    if source is None:
        failures.append("negative fixtures require the version-bound Codex record")
        return 0

    fixtures: list[tuple[str, dict[str, Any]]] = []
    missing_commit = copy.deepcopy(source)
    del missing_commit["release"]["commit"]
    fixtures.append(("missing immutable commit", missing_commit))
    missing_tag = copy.deepcopy(source)
    del missing_tag["release"]["tag"]
    fixtures.append(("missing immutable tag", missing_tag))
    wrong_tag = copy.deepcopy(source)
    wrong_tag["release"]["tag"] = "v0.7.5"
    fixtures.append(("version and tag mismatch", wrong_tag))
    unobserved_pass = copy.deepcopy(source)
    unobserved_pass["cases"][0]["observedRoute"] = None
    fixtures.append(("pass without observed route", unobserved_pass))
    sensitive_path = copy.deepcopy(source)
    sensitive_path["cases"][0]["supportingOutput"][0] = "/home/example/private"
    fixtures.append(("private path", sensitive_path))
    output_on_not_run = copy.deepcopy(source)
    output_on_not_run["cases"][2]["supportingOutput"] = ["claimed output"]
    fixtures.append(("not-run with claimed output", output_on_not_run))
    mutating_pass = copy.deepcopy(source)
    mutating_pass["cases"][0]["mutationAttempted"] = True
    fixtures.append(("passing case with mutation", mutating_pass))

    history_entry = next(
        (
            item
            for item in runtime_history.get("entries", [])
            if type(item) is dict and item.get("tag") == source["release"]["tag"]
        ),
        None,
    )
    if history_entry is None:
        failures.append("schema-v2 fixtures require the v0.7.4 runtime history entry")
    else:
        v2_control = copy.deepcopy(source)
        v2_control["schemaVersion"] = "2"
        v2_control["runtimeIdentity"] = {
            "pluginVersion": source["release"]["version"],
            "runtimeContractSchemaVersion": "1",
            "runtimeContractDigest": history_entry["runtimeContractDigest"],
        }
        v2_control["observationSubject"] = "installed-runtime-contract"
        control_failures: list[str] = []
        validate_record(v2_control, None, control_failures)
        if control_failures:
            failures.append(
                "schema-v2 positive evidence fixture failed: "
                + "; ".join(control_failures)
            )
        missing_runtime_digest = copy.deepcopy(v2_control)
        del missing_runtime_digest["runtimeIdentity"]["runtimeContractDigest"]
        fixtures.append(("v2 record without runtime digest", missing_runtime_digest))
        unprefixed_runtime_digest = copy.deepcopy(v2_control)
        unprefixed_runtime_digest["runtimeIdentity"]["runtimeContractDigest"] = (
            history_entry["runtimeContractDigest"].removeprefix("sha256:")
        )
        fixtures.append(("v2 record with unprefixed runtime digest", unprefixed_runtime_digest))

    for name, document in fixtures:
        expect_fixture_failure(
            name,
            document,
            lambda candidate, candidate_failures: validate_record(
                candidate, None, candidate_failures
            ),
            failures,
        )

    promoted_prior = copy.deepcopy(status)
    promoted_prior["rules"]["priorEvidenceIsCurrent"] = True
    expect_fixture_failure(
        "prior evidence promoted to current",
        promoted_prior,
        lambda candidate, candidate_failures: validate_status(
            candidate,
            records,
            current_version,
            runtime_identity,
            runtime_history,
            candidate_failures,
        ),
        failures,
    )
    current_version_reuse = copy.deepcopy(status)
    current_version_reuse["targetRelease"]["version"] = "0.7.4"
    current_version_reuse["targetRelease"]["tag"] = "v0.7.4"
    expect_fixture_failure(
        "old release status reused as current",
        current_version_reuse,
        lambda candidate, candidate_failures: validate_status(
            candidate,
            records,
            current_version,
            runtime_identity,
            runtime_history,
            candidate_failures,
        ),
        failures,
    )
    current_host_pass = copy.deepcopy(status)
    current_host_pass["currentHostEvidence"][0]["status"] = "pass"
    expect_fixture_failure(
        "current host pass embedded before immutable publication",
        current_host_pass,
        lambda candidate, candidate_failures: validate_status(
            candidate,
            records,
            current_version,
            runtime_identity,
            runtime_history,
            candidate_failures,
        ),
        failures,
    )
    return len(fixtures) + 3


def validate_repository(run_self_tests: bool) -> tuple[list[str], int, int, str | None]:
    failures: list[str] = []
    schema_v1 = load_json(SCHEMA_V1_PATH, failures)
    if schema_v1 is not None:
        check_schema_v1_contract(schema_v1, failures)
    schema_v2 = load_json(SCHEMA_V2_PATH, failures)
    if schema_v2 is not None:
        check_schema_v2_contract(schema_v2, failures)
    records = collect_records(failures)
    check_no_hook_bundle(failures, REPOSITORY_ROOT)
    current_version = manifest_version(failures)
    runtime_identity = load_json(RUNTIME_IDENTITY_PATH, failures) or {}
    runtime_history = load_json(RUNTIME_HISTORY_PATH, failures) or {}
    status = load_json(STATUS_PATH, failures)
    if status is not None:
        validate_status(
            status,
            records,
            current_version,
            runtime_identity,
            runtime_history,
            failures,
        )
    fixture_count = 0
    if run_self_tests and status is not None:
        fixture_count = check_negative_fixtures(
            records,
            status,
            current_version,
            runtime_identity,
            runtime_history,
            failures,
        )
    return failures, len(records), fixture_count, current_version


def validate_external_record(
    path: Path,
    expected_tag: str,
    expected_commit: str,
) -> list[str]:
    failures, _, _, _ = validate_repository(False)
    check_runtime_identity(failures)
    record = load_json(path, failures)
    if record is None:
        return failures
    validate_record(record, None, failures)
    if record.get("schemaVersion") != "2":
        failures.append("new external observations must use evidence/schema-v2.json")
    release = record.get("release", {})
    if release.get("tag") != expected_tag:
        failures.append("external record tag does not match --expected-tag")
    if release.get("commit") != expected_commit:
        failures.append("external record commit does not match --expected-commit")

    runtime_identity = load_json(RUNTIME_IDENTITY_PATH, failures) or {}
    runtime_history = load_json(RUNTIME_HISTORY_PATH, failures) or {}
    expected_version = expected_tag.removeprefix("v")
    expected_digest = None
    if runtime_identity.get("pluginVersion") == expected_version:
        runtime = runtime_identity.get("runtimeContract")
        if type(runtime) is dict:
            expected_digest = runtime.get("digest")
    if expected_digest is None:
        for entry in runtime_history.get("entries", []):
            if type(entry) is dict and entry.get("tag") == expected_tag:
                expected_digest = entry.get("runtimeContractDigest")
                break
    if type(expected_digest) is not str:
        failures.append("external record release has no canonical runtime digest binding")
    else:
        runtime = record.get("runtimeIdentity")
        observed_digest = runtime.get("runtimeContractDigest") if type(runtime) is dict else None
        if observed_digest != expected_digest:
            failures.append("external record runtime digest disagrees with canonical identity")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run in-memory negative fixtures after repository validation",
    )
    parser.add_argument(
        "--record",
        type=Path,
        help="validate one post-tag evidence record outside the checked-in matrix",
    )
    parser.add_argument("--expected-tag", help="immutable tag required by --record")
    parser.add_argument("--expected-commit", help="immutable commit required by --record")
    args = parser.parse_args()
    if args.record is not None:
        if args.self_test:
            parser.error("--self-test cannot be combined with --record")
        if args.expected_tag is None or args.expected_commit is None:
            parser.error("--record requires --expected-tag and --expected-commit")
        if not re.fullmatch(r"v" + SEMVER_PATTERN.pattern, args.expected_tag):
            parser.error("--expected-tag must be a strict v-prefixed SemVer tag")
        if not COMMIT_PATTERN.fullmatch(args.expected_commit):
            parser.error("--expected-commit must be a 40-character lowercase Git SHA")
    elif args.expected_tag is not None or args.expected_commit is not None:
        parser.error("--expected-tag and --expected-commit require --record")
    return args


def report_failures(failures: list[str]) -> int:
    print("Compatibility evidence validation failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


def main() -> int:
    args = parse_args()
    if args.record is not None:
        failures = validate_external_record(
            args.record.resolve(), args.expected_tag, args.expected_commit
        )
        if failures:
            return report_failures(failures)
        digest = hashlib.sha256(args.record.read_bytes()).hexdigest()
        print(
            "Compatibility evidence record passed: "
            f"{args.expected_tag} at {args.expected_commit}, sha256 {digest}."
        )
        return 0

    failures, record_count, fixture_count, current_version = validate_repository(
        args.self_test
    )
    if failures:
        return report_failures(failures)
    fixture_text = f", {fixture_count} negative fixtures" if args.self_test else ""
    print(
        "Compatibility evidence validation passed: "
        f"{record_count} records{fixture_text}, current release v{current_version} STATIC-ONLY."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
