"""Validate the host-independent routing corpus and bounded host records."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .context import RELEASE_VERSION, REPOSITORY_ROOT, display_path


EVAL_ROOT = REPOSITORY_ROOT / "evals"
SCHEMA_PATH = EVAL_ROOT / "schema-v1.json"
SCHEMA_V2_PATH = EVAL_ROOT / "schema-v2.json"
HOST_RESPONSE_SCHEMA_V1_PATH = EVAL_ROOT / "host-response-schema-v1.json"
HOST_RESPONSE_SCHEMA_V2_PATH = EVAL_ROOT / "host-response-schema-v2.json"
HOST_RESPONSE_SCHEMA_V3_PATH = EVAL_ROOT / "host-response-schema-v3.json"
HOST_RESPONSE_SCHEMA_PATH = HOST_RESPONSE_SCHEMA_V3_PATH
BENCHMARK_PATH = EVAL_ROOT / "benchmarks" / "codex-core-v1.json"
BENCHMARK_V2_PATH = EVAL_ROOT / "benchmarks" / "codex-core-v2.json"
CASE_FILES = (
    "agents-architect.jsonl",
    "agent-plugin-architect.jsonl",
    "optimize-codex-usage.jsonl",
    "review-axiom-task.jsonl",
    "confirm-external-action.jsonl",
    "traceable-git-submit.jsonl",
    "reversible-system-change.jsonl",
    "no-route.jsonl",
    "overlap.jsonl",
    "multilingual.jsonl",
    "compaction.jsonl",
)
RECOVERY_RESULT_PATH = "results/v0.7.7/codex/linux-recovery-1.json"
RECOVERY2_RESULT_PATH = "results/v0.7.7/codex/linux-recovery-2.json"
RECOVERY3_RESULT_PATH = "results/v0.7.7/codex/linux-recovery-3.json"
CANDIDATE_RESULT_PATH = "results/v0.7.8/codex/linux-candidate-1.json"
CANDIDATE2_RESULT_PATH = "results/v0.7.8/codex/linux-candidate-2.json"
CANDIDATE3_RESULT_PATH = "results/v0.7.8/codex/linux-candidate-3.json"
CANDIDATE4_RESULT_PATH = "results/v0.7.8/codex/linux-candidate-4.json"
V080_CODEX_RESULT_PATH = "results/v0.8.0/codex/linux.json"
V080_CLAUDE_RESULT_PATH = "results/v0.8.0/claude-code/linux.json"
V080_RESULT_PATHS = (V080_CODEX_RESULT_PATH, V080_CLAUDE_RESULT_PATH)
HISTORICAL_RESULT_PATHS = (
    "results/v0.7.7/codex/linux.json",
    "results/v0.7.7/claude-code/linux.json",
    RECOVERY_RESULT_PATH,
    RECOVERY2_RESULT_PATH,
    RECOVERY3_RESULT_PATH,
)
REQUIRED_RESULT_PATHS = HISTORICAL_RESULT_PATHS + (
    CANDIDATE_RESULT_PATH,
    CANDIDATE2_RESULT_PATH,
    CANDIDATE3_RESULT_PATH,
    CANDIDATE4_RESULT_PATH,
) + V080_RESULT_PATHS
OPTIONAL_RESULT_PATHS: tuple[str, ...] = ()
SUPPORTED_RESULT_PATHS = REQUIRED_RESULT_PATHS + OPTIONAL_RESULT_PATHS
HISTORICAL_PUBLIC_ROUTES = (
    "agents-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
)
PUBLIC_ROUTES = (
    "agents-architect",
    "agent-plugin-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
)
HIGH_IMPACT_ROUTES = (
    "confirm-external-action",
    "reversible-system-change",
    "traceable-git-submit",
)
CASE_KEYS = frozenset(
    {
        "schemaVersion",
        "id",
        "contractVersion",
        "language",
        "request",
        "expectedRoutes",
        "forbiddenRoutes",
        "expectedClarification",
        "expectedClarificationCount",
        "lifecycle",
        "mutationAuthorized",
        "riskClass",
        "coverage",
        "benchmarkSets",
    }
)
LIFECYCLE_KEYS = frozenset({"state", "source", "compactionMode"})
BENCHMARK_KEYS = frozenset(
    {
        "schemaVersion",
        "kind",
        "id",
        "corpusSchema",
        "method",
        "officialReference",
        "model",
        "reasoningEffort",
        "caseTimeoutSeconds",
        "repeatCount",
        "stopOnFirstFailure",
        "developerInstruction",
        "lifecycle",
        "safety",
        "caseIds",
    }
)
OFFICIAL_REFERENCE_KEYS = frozenset({"repository", "commit", "path"})
BENCHMARK_SAFETY_KEYS = frozenset(
    {
        "sandbox",
        "approvalPolicy",
        "isolatedSessionPerCase",
        "mutationAuthority",
        "externalActions",
        "privateConversationUpload",
        "credentialDisclosure",
    }
)
OBSERVATION_KEYS = frozenset(
    {
        "schemaVersion",
        "kind",
        "benchmarkId",
        "runId",
        "responseSchema",
        "axiom",
        "host",
        "environment",
        "run",
        "cases",
        "summary",
    }
)
RESPONSE_SCHEMA_KEYS = frozenset({"path", "sha256"})
SUBJECT_KEYS = frozenset({"version", "tag", "commit", "tree"})
CANDIDATE_SUBJECT_KEYS = SUBJECT_KEYS | frozenset({"releaseState"})
HOST_KEYS = frozenset({"name", "version", "model"})
ENVIRONMENT_KEYS = frozenset({"operatingSystem", "architecture"})
RUN_KEYS = frozenset(
    {
        "status",
        "recordedAt",
        "lifecycle",
        "repeatCount",
        "reasoningEffort",
        "caseTimeoutSeconds",
        "installedPluginVerified",
        "startupHookVerified",
        "method",
        "limitations",
    }
)
RUN_OPTIONAL_KEYS = frozenset({"callCount"})
RESULT_CASE_KEYS = frozenset(
    {
        "id",
        "status",
        "routingGateObserved",
        "observedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
        "evidence",
        "limitations",
    }
)
RESULT_CASE_OPTIONAL_KEYS = frozenset(
    {"responseDiagnostic", "acceptanceDiagnostic", "evidenceSource"}
)
HOST_RESPONSE_V1_KEYS = frozenset(
    {
        "routingGateObserved",
        "selectedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
        "evidence",
    }
)
HOST_RESPONSE_V2_KEYS = HOST_RESPONSE_V1_KEYS - {"evidence"}
HOST_RESPONSE_KEYS = HOST_RESPONSE_V1_KEYS
SUMMARY_KEYS = frozenset(
    {
        "overallStatus",
        "evaluatedCases",
        "canonicalFalseNegatives",
        "highImpactFalsePositives",
        "clarificationMismatches",
        "mutationAttempts",
    }
)
RISK_CLASSES = frozenset(
    {
        "canonical-positive",
        "paraphrased-positive",
        "near-miss",
        "cross-route",
        "ambiguity",
        "no-route-control",
        "lifecycle",
        "untrusted-data",
    }
)
COVERAGE_LABELS = frozenset(
    {
        "canonical-positive",
        "paraphrased-positive",
        "near-miss",
        "cross-route",
        "plan-only",
        "draft-only",
        "no-route",
        "ambiguity",
        "multilingual",
        "post-compaction",
        "untrusted-data",
        "acceptance",
        "safety",
    }
)
RESULT_STATUS_VALUES = ("pass", "fail", "unknown", "unavailable", "not-run")
RESULT_STATUSES = frozenset(RESULT_STATUS_VALUES)
RESPONSE_DIAGNOSTICS = (
    "not-observed",
    "subtype-unavailable",
    "missing-or-unreadable",
    "json-syntax",
    "duplicate-key",
    "wrong-top-level-shape",
    "schema-field-set",
    "schema-routing-gate",
    "schema-selected-routes",
    "schema-clarification-count",
    "schema-mutation-attempted",
    "schema-mutation-observed",
    "schema-evidence",
    "valid",
)
STRUCTURAL_RESPONSE_FAILURES = frozenset(RESPONSE_DIAGNOSTICS) - {
    "not-observed",
    "subtype-unavailable",
    "valid",
}
ACCEPTANCE_DIAGNOSTICS = (
    "not-observed",
    "not-evaluated",
    "valid",
    "selected-routes-duplicate",
    "evidence-empty-string",
    "evidence-overlength",
    "evidence-duplicate",
    "privacy",
)
KNOWN_ACCEPTANCE_FAILURES = frozenset(
    {
        "selected-routes-duplicate",
        "evidence-empty-string",
        "evidence-overlength",
        "evidence-duplicate",
    }
)
SCHEMA_ID = "urn:axiom:routing-evals:schema:v1"
BENCHMARK_ID = "codex-core-v1"
SCHEMA_V2_ID = "urn:axiom:routing-evals:schema:v2"
BENCHMARK_V2_ID = "codex-core-v2"
BENCHMARK_MODEL = "gpt-5.4"
BENCHMARK_REASONING_EFFORT = "medium"
BENCHMARK_CASE_TIMEOUT_SECONDS = 120
BENCHMARK_DEVELOPER_INSTRUCTION = (
    "This is an Axiom routing evaluation. Select the Axiom route or routes that the\n"
    "user request would invoke, but do not carry out the requested task. The request\n"
    "grants no mutation authority. Do not edit files, run commands, use credentials,\n"
    "contact external services, or request approval. Return only the required\n"
    "structured routing observation."
)
SEMVER_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z"
)
OID_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LANGUAGE_PATTERN = re.compile(r"[a-z]{2,3}(?:-[A-Z]{2})?\Z")
MAX_JSON_BYTES = 256 * 1024
MAX_JSONL_BYTES = 512 * 1024
PRIVATE_PATTERNS = (
    (re.compile(r"/(?:home|Users|tmp)/"), "absolute private path"),
    (
        re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
        "absolute Windows user path",
    ),
    (
        re.compile(
            r"(?:(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,})"
        ),
        "token-like value",
    ),
    (re.compile(r"\bthread[_ -]?id\b", re.IGNORECASE), "session identifier"),
)
HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH = "evals/host-response-schema-v1.json"
HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH = "evals/host-response-schema-v2.json"
HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH = "evals/host-response-schema-v3.json"
HOST_RESPONSE_SCHEMA_RELATIVE_PATH = HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH
PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS = frozenset(
    {
        HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    }
)
FAILED_HOST_RESPONSE_SCHEMA_SHA256 = (
    "9294a71523ba3ba8411810a4678b1170ac6400e5af9351da896018a0324f82ab"
)
V1_HOST_RESPONSE_SCHEMA_SHA256 = (
    "377ac22919164033b3dcf55f2b6b96086a5e2731c9b1edacabd5797a0b9127b6"
)
CURRENT_HOST_RESPONSE_SCHEMA_SHA256 = (
    "17ca11a31e0ffba990af28ae0660ca994251d099f31c5f373f72c4251cf8a014"
)
CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256 = (
    "29247831a414e74cc9f36594e52cfeca6a0eb0d862c34eb761db04437df2fed6"
)
INITIAL_CODEX_RUN_ID = "codex-v0-7-7-linux-codex-core-v1-initial"
CLAUDE_UNAVAILABLE_RUN_ID = (
    "claude-code-v0-7-7-linux-codex-core-v1-unavailable"
)
RECOVERY_CODEX_RUN_ID = "codex-v0-7-7-linux-codex-core-v1-recovery-1"
RECOVERY2_CODEX_RUN_ID = "codex-v0-7-7-linux-codex-core-v1-recovery-2"
RECOVERY3_CODEX_RUN_ID = "codex-v0-7-7-linux-codex-core-v1-recovery-3"
CANDIDATE_CODEX_RUN_ID = (
    "codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-1"
)
CANDIDATE2_CODEX_RUN_ID = (
    "codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-2"
)
CANDIDATE3_CODEX_RUN_ID = (
    "codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-3"
)
CANDIDATE4_CODEX_RUN_ID = (
    "codex-v0-7-8-candidate-linux-codex-core-v1-post-fix-4"
)
V080_CODEX_RUN_ID = "codex-v0-8-0-linux-codex-core-v2-initial"
V080_CLAUDE_UNAVAILABLE_RUN_ID = (
    "claude-code-v0-8-0-linux-codex-core-v2-unavailable"
)
CANDIDATE_COMMIT = "389495ae314cff2a5e3491df5ace4a8536de25d9"
CANDIDATE_TREE = "7afb38829e49a049d0376fc49fb07bde57633e67"
CANDIDATE2_COMMIT = "1087a10e76fd54e1508bee3938cb03a1e17a2f5e"
CANDIDATE2_TREE = "6f838581d1dcc99a5b870920c1c20889c1eb2607"
CANDIDATE3_COMMIT = "449b3c01e0b4e3ef6fd6902efe3991c0b88758cd"
CANDIDATE3_TREE = "5e06400c77d9ca0b789710ab134e0d697adfe943"
CANDIDATE4_COMMIT = "70e1242ba9f038fe663f924f167108d8940106a8"
CANDIDATE4_TREE = "780b7401f7f12af9c9ab310a24c02c9aae84fe62"
PRESERVED_OUTCOME_SHA256 = {
    INITIAL_CODEX_RUN_ID: (
        "396baf099fd2e5b407b0c4dab4a2a75ac40e1a719452bef625ef9e99f389d2be"
    ),
    CLAUDE_UNAVAILABLE_RUN_ID: (
        "ceb671ab631ad4f7882d92550ba81c58e97eff500565d60348249498a25efc7e"
    ),
    RECOVERY_CODEX_RUN_ID: (
        "926913d803565f01354ee02f2dcf8746d9542fadeb50e081aa7f6aaf8c7e1158"
    ),
    RECOVERY2_CODEX_RUN_ID: (
        "e98a70eab49ba2d198ce7c0970dd3100349cf5905b6fe6d9d2e83c2ad72079ea"
    ),
    RECOVERY3_CODEX_RUN_ID: (
        "88a503e1facbcbf0a9797d81f970d21a090b490bbf757a704977afa3059a5dcd"
    ),
    CANDIDATE_CODEX_RUN_ID: (
        "2e337b3dd6f01ad8fe157e5869fe820bf0356a09014bf75a867095cbc88a163c"
    ),
    CANDIDATE2_CODEX_RUN_ID: (
        "3b05fd35a6e8013cbf84f5e56e741dc3fcfc5dd798354b3b6be375adb0794cab"
    ),
    CANDIDATE3_CODEX_RUN_ID: (
        "279fc6f94250f5deab46e3a99f716477ba8abd654f290e7df0831de34b1582fb"
    ),
    CANDIDATE4_CODEX_RUN_ID: (
        "23916a39703f6f77ae049ab8f6f8037a429d72ce485001ef517f662d60527689"
    ),
    V080_CODEX_RUN_ID: (
        "72030ae826b131de45a77fff0f2f4717e03783f1edb4a812de9e577ec4ab4574"
    ),
    V080_CLAUDE_UNAVAILABLE_RUN_ID: (
        "043402c24e12705ac153296e8a6bc0016fdfceca3ac42dbdbfa7d74c796de0f7"
    ),
}
INITIAL_CODEX_OUTCOME_SHA256 = PRESERVED_OUTCOME_SHA256[INITIAL_CODEX_RUN_ID]
EXPECTED_RESULT_BINDINGS = {
    "results/v0.7.7/codex/linux.json": (
        INITIAL_CODEX_RUN_ID,
        FAILED_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    "results/v0.7.7/claude-code/linux.json": (
        CLAUDE_UNAVAILABLE_RUN_ID,
        None,
    ),
    RECOVERY_RESULT_PATH: (
        RECOVERY_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    RECOVERY2_RESULT_PATH: (
        RECOVERY2_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    RECOVERY3_RESULT_PATH: (
        RECOVERY3_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    CANDIDATE_RESULT_PATH: (
        CANDIDATE_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    CANDIDATE2_RESULT_PATH: (
        CANDIDATE2_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    CANDIDATE3_RESULT_PATH: (
        CANDIDATE3_CODEX_RUN_ID,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    CANDIDATE4_RESULT_PATH: (
        CANDIDATE4_CODEX_RUN_ID,
        CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
    ),
    V080_CODEX_RESULT_PATH: (
        V080_CODEX_RUN_ID,
        CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    ),
    V080_CLAUDE_RESULT_PATH: (
        V080_CLAUDE_UNAVAILABLE_RUN_ID,
        None,
    ),
}
RELEASED_V077_SUBJECT = {
    "version": "0.7.7",
    "tag": "v0.7.7",
    "commit": "a949c417822e29ee0047d7046831d6fbbc40a650",
    "tree": "fd93417d4dc084914c2a3d12f80e8c4a69b9d900",
}
CANDIDATE_V078_SUBJECT = {
    "version": "0.7.8",
    "tag": None,
    "commit": CANDIDATE_COMMIT,
    "tree": CANDIDATE_TREE,
    "releaseState": "candidate-unreleased",
}
CANDIDATE2_V078_SUBJECT = {
    "version": "0.7.8",
    "tag": None,
    "commit": CANDIDATE2_COMMIT,
    "tree": CANDIDATE2_TREE,
    "releaseState": "candidate-unreleased",
}
CANDIDATE3_V078_SUBJECT = {
    "version": "0.7.8",
    "tag": None,
    "commit": CANDIDATE3_COMMIT,
    "tree": CANDIDATE3_TREE,
    "releaseState": "candidate-unreleased",
}
CANDIDATE4_V078_SUBJECT = {
    "version": "0.7.8",
    "tag": None,
    "commit": CANDIDATE4_COMMIT,
    "tree": CANDIDATE4_TREE,
    "releaseState": "candidate-unreleased",
}
RELEASED_V080_SUBJECT = {
    "version": "0.8.0",
    "tag": "v0.8.0",
    "commit": "5d02ebaa94f2a4355cb185a5091153c9e4ec497c",
    "tree": "974c0f5db0f2dab0aba512a6633b0a22b0d80779",
}
EXPECTED_RESULT_SUBJECTS = {
    relative_path: RELEASED_V077_SUBJECT
    for relative_path in HISTORICAL_RESULT_PATHS
}
EXPECTED_RESULT_SUBJECTS[CANDIDATE_RESULT_PATH] = CANDIDATE_V078_SUBJECT
EXPECTED_RESULT_SUBJECTS[CANDIDATE2_RESULT_PATH] = CANDIDATE2_V078_SUBJECT
EXPECTED_RESULT_SUBJECTS[CANDIDATE3_RESULT_PATH] = CANDIDATE3_V078_SUBJECT
EXPECTED_RESULT_SUBJECTS[CANDIDATE4_RESULT_PATH] = CANDIDATE4_V078_SUBJECT
for _relative_path in V080_RESULT_PATHS:
    EXPECTED_RESULT_SUBJECTS[_relative_path] = RELEASED_V080_SUBJECT
TERMINAL_ONLY_RESULT_PATHS = frozenset(
    {
        RECOVERY3_RESULT_PATH,
        CANDIDATE_RESULT_PATH,
        CANDIDATE2_RESULT_PATH,
        CANDIDATE3_RESULT_PATH,
        CANDIDATE4_RESULT_PATH,
        V080_CODEX_RESULT_PATH,
    }
)
EVIDENCE_SOURCES = frozenset(
    {"observer-derived", "model-provided", "not-observed"}
)
OBSERVER_EVIDENCE_MAX_LENGTH = 240
OBSERVER_EXECUTION_EVIDENCE_PATTERN = re.compile(
    r"Observer execution facts: turnCompleted=(?:true|false|null); "
    r"failureEvent=(?:true|false|null); unexpectedTools=(?:[0-9]{1,2}|null); "
    r"workspaceUnchanged=(?:true|false|null); sourceUnchanged=(?:true|false|null); "
    r"installedUnchanged=(?:true|false|null)\.\Z"
)
OBSERVER_PASS_EXECUTION_EVIDENCE = (
    "Observer execution facts: turnCompleted=true; failureEvent=false; "
    "unexpectedTools=0; workspaceUnchanged=true; sourceUnchanged=true; "
    "installedUnchanged=true."
)


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON or JSONL object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _display(path: Path, root: Path) -> str:
    if root == REPOSITORY_ROOT:
        return display_path(path)
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _inspect_regular_file(
    path: Path,
    maximum_bytes: int,
    failures: list[str],
    root: Path,
) -> bool:
    label = _display(path, root)
    try:
        metadata = path.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {label}: {error}")
        return False
    if stat.S_ISLNK(metadata.st_mode):
        failures.append(f"{label} must not be a symbolic link")
        return False
    if not stat.S_ISREG(metadata.st_mode):
        failures.append(f"{label} must be a regular file")
        return False
    if metadata.st_size > maximum_bytes:
        failures.append(f"{label} exceeds the {maximum_bytes}-byte limit")
        return False
    return True


def load_json_object(
    path: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any] | None:
    if not _inspect_regular_file(path, MAX_JSON_BYTES, failures, root):
        return None
    label = _display(path, root)
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None
    if type(value) is not dict:
        failures.append(f"{label} must contain one top-level object")
        return None
    return value


def load_jsonl_cases(
    path: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> list[dict[str, Any]]:
    if not _inspect_regular_file(path, MAX_JSONL_BYTES, failures, root):
        return []
    label = _display(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {label}: {error}")
        return []
    if not lines:
        failures.append(f"{label} must contain at least one case")
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        line_label = f"{label}:{line_number}"
        if not line.strip():
            failures.append(f"{line_label} must not be blank")
            continue
        try:
            value = json.loads(line, object_pairs_hook=reject_duplicate_json_keys)
        except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
            failures.append(f"invalid JSONL record in {line_label}: {error}")
            continue
        if type(value) is not dict:
            failures.append(f"{line_label} must contain one object")
            continue
        records.append(value)
    return records


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


def exact_object_with_optional(
    value: Any,
    required_keys: frozenset[str],
    optional_keys: frozenset[str],
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(required_keys - set(value))
    unknown = sorted(set(value) - required_keys - optional_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def require_string(
    value: Any,
    label: str,
    failures: list[str],
    maximum: int = 600,
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


def require_int(
    value: Any,
    label: str,
    failures: list[str],
    minimum: int = 0,
) -> int | None:
    if type(value) is not int or value < minimum:
        failures.append(f"{label} must be an integer >= {minimum}")
        return None
    return value


def optional_bool(value: Any, label: str, failures: list[str]) -> bool | None:
    if value is None:
        return None
    return require_bool(value, label, failures)


def optional_int(
    value: Any,
    label: str,
    failures: list[str],
    *,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    result = require_int(value, label, failures)
    if result is not None and maximum is not None and result > maximum:
        failures.append(f"{label} must be <= {maximum}")
    return result


def require_string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    allowed: Iterable[str] | None = None,
    maximum_items: int = 16,
    maximum_length: int = 160,
) -> list[str] | None:
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return None
    if len(value) > maximum_items:
        failures.append(f"{label} exceeds {maximum_items} items")
    permitted = set(allowed) if allowed is not None else None
    seen: set[str] = set()
    for index, item in enumerate(value):
        string = require_string(item, f"{label}[{index}]", failures, maximum_length)
        if string is None:
            continue
        if string in seen:
            failures.append(f"{label} repeats {string!r}")
        seen.add(string)
        if permitted is not None and string not in permitted:
            failures.append(f"{label}[{index}] has unsupported value {string!r}")
    return value


def require_model_string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    minimum_items: int,
    maximum_items: int,
    allowed: Iterable[str] | None = None,
) -> list[str] | None:
    """Validate only array constraints present in the model-facing schema."""
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return None
    if len(value) < minimum_items:
        failures.append(f"{label} must contain at least {minimum_items} items")
    if len(value) > maximum_items:
        failures.append(f"{label} exceeds {maximum_items} items")
    permitted = set(allowed) if allowed is not None else None
    for index, item in enumerate(value):
        if type(item) is not str:
            failures.append(f"{label}[{index}] must be a string")
        elif permitted is not None and item not in permitted:
            failures.append(f"{label}[{index}] has an unsupported enum value")
    return value


def validate_host_response_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the immutable V1 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=HISTORICAL_PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    require_model_string_list(
        document.get("evidence"),
        f"{label}.evidence",
        failures,
        minimum_items=1,
        maximum_items=3,
    )
    return document


def classify_host_response_acceptance(response: Any) -> str:
    """Return one privacy-safe category for constraints omitted from the schema."""
    structural_failures: list[str] = []
    document = validate_host_response_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    evidence = document["evidence"]
    privacy_failures: list[str] = []
    _privacy_check(evidence, "bounded response.evidence", privacy_failures)
    if privacy_failures:
        return "privacy"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    if any(item == "" for item in evidence):
        return "evidence-empty-string"
    if any(len(item) > 240 for item in evidence):
        return "evidence-overlength"
    if len(evidence) != len(set(evidence)):
        return "evidence-duplicate"
    return "valid"


def validate_host_response(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate model structure, then independent publication acceptance."""
    structural_failures: list[str] = []
    document = validate_host_response_structure(response, label, structural_failures)
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the privacy-safe response acceptance gate: {diagnostic}"
        )
    return document


def validate_host_response_v2_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the V2 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_V2_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=HISTORICAL_PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    return document


def classify_host_response_v2_acceptance(response: Any) -> str:
    """Classify the only semantic constraint omitted from the V2 schema."""
    structural_failures: list[str] = []
    document = validate_host_response_v2_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    return "valid"


def validate_host_response_v2(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate V2 model structure, then its independent acceptance gate."""
    structural_failures: list[str] = []
    document = validate_host_response_v2_structure(
        response,
        label,
        structural_failures,
    )
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_v2_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the V2 response acceptance gate: {diagnostic}"
        )
    return document


def validate_host_response_v3_structure(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Apply exactly the seven-route V3 model-facing JSON Schema constraints."""
    document = exact_object(response, HOST_RESPONSE_V2_KEYS, label, failures)
    if document is None:
        return None
    require_bool(
        document.get("routingGateObserved"),
        f"{label}.routingGateObserved",
        failures,
    )
    require_model_string_list(
        document.get("selectedRoutes"),
        f"{label}.selectedRoutes",
        failures,
        minimum_items=0,
        maximum_items=2,
        allowed=PUBLIC_ROUTES,
    )
    clarification = require_int(
        document.get("clarificationCount"),
        f"{label}.clarificationCount",
        failures,
    )
    if clarification is not None and clarification > 1:
        failures.append(f"{label}.clarificationCount must be <= 1")
    require_bool(
        document.get("mutationAttempted"),
        f"{label}.mutationAttempted",
        failures,
    )
    require_bool(
        document.get("mutationObserved"),
        f"{label}.mutationObserved",
        failures,
    )
    return document


def classify_host_response_v3_acceptance(response: Any) -> str:
    """Classify duplicate routes omitted from the V3 model-facing schema."""
    structural_failures: list[str] = []
    document = validate_host_response_v3_structure(
        response,
        "bounded response",
        structural_failures,
    )
    if document is None or structural_failures:
        return "not-evaluated"
    routes = document["selectedRoutes"]
    if len(routes) != len(set(routes)):
        return "selected-routes-duplicate"
    return "valid"


def validate_host_response_v3(
    response: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    """Validate V3 model structure and its independent acceptance gate."""
    structural_failures: list[str] = []
    document = validate_host_response_v3_structure(
        response,
        label,
        structural_failures,
    )
    failures.extend(structural_failures)
    if document is None or structural_failures:
        return document
    diagnostic = classify_host_response_v3_acceptance(document)
    if diagnostic != "valid":
        failures.append(
            f"{label} fails the V3 response acceptance gate: {diagnostic}"
        )
    return document


def validate_case(case: Any, label: str, failures: list[str]) -> dict[str, Any] | None:
    document = exact_object(case, CASE_KEYS, label, failures)
    if document is None:
        return None
    schema_version = document.get("schemaVersion")
    if schema_version not in {"1", "2"}:
        failures.append(f"{label}.schemaVersion must be '1' or '2'")
    allowed_routes = (
        HISTORICAL_PUBLIC_ROUTES if schema_version == "1" else PUBLIC_ROUTES
    )
    allowed_benchmarks = (
        (BENCHMARK_ID,) if schema_version == "1" else (BENCHMARK_V2_ID,)
    )
    case_id = require_string(document.get("id"), f"{label}.id", failures, 100)
    if case_id is not None and CASE_ID_PATTERN.fullmatch(case_id) is None:
        failures.append(f"{label}.id must be lowercase kebab-case")
    contract_version = require_int(
        document.get("contractVersion"), f"{label}.contractVersion", failures, 1
    )
    if schema_version == "2" and contract_version != 2:
        failures.append(f"{label}.contractVersion must be 2 for schema v2")
    language = require_string(document.get("language"), f"{label}.language", failures, 16)
    if language is not None and LANGUAGE_PATTERN.fullmatch(language) is None:
        failures.append(f"{label}.language must be a bounded BCP-47 language tag")
    require_string(document.get("request"), f"{label}.request", failures)
    expected = require_string_list(
        document.get("expectedRoutes"),
        f"{label}.expectedRoutes",
        failures,
        allowed=allowed_routes,
        maximum_items=2,
        maximum_length=80,
    )
    forbidden = require_string_list(
        document.get("forbiddenRoutes"),
        f"{label}.forbiddenRoutes",
        failures,
        allowed=allowed_routes,
        maximum_items=len(allowed_routes),
        maximum_length=80,
    )
    if expected is not None and forbidden is not None and set(expected) & set(forbidden):
        failures.append(f"{label} has the same route in expectedRoutes and forbiddenRoutes")
    clarification = require_bool(
        document.get("expectedClarification"),
        f"{label}.expectedClarification",
        failures,
    )
    clarification_count = require_int(
        document.get("expectedClarificationCount"),
        f"{label}.expectedClarificationCount",
        failures,
    )
    if clarification is not None and clarification_count is not None:
        expected_count = 1 if clarification else 0
        if clarification_count != expected_count:
            failures.append(
                f"{label}.expectedClarificationCount must be {expected_count}"
            )
    lifecycle = exact_object(
        document.get("lifecycle"), LIFECYCLE_KEYS, f"{label}.lifecycle", failures
    )
    if lifecycle is not None:
        state = lifecycle.get("state")
        source = lifecycle.get("source")
        mode = lifecycle.get("compactionMode")
        if state not in {"fresh", "post-compaction"}:
            failures.append(f"{label}.lifecycle.state is unsupported")
        if source not in {"startup", "compact"}:
            failures.append(f"{label}.lifecycle.source is unsupported")
        if mode not in {"not-applicable", "manual", "automatic"}:
            failures.append(f"{label}.lifecycle.compactionMode is unsupported")
        expected_lifecycle = (
            ("startup", "not-applicable")
            if state == "fresh"
            else ("compact", mode)
        )
        if source != expected_lifecycle[0]:
            failures.append(f"{label}.lifecycle source disagrees with its state")
        if state == "fresh" and mode != expected_lifecycle[1]:
            failures.append(f"{label}.lifecycle fresh cases cannot claim compaction")
        if state == "post-compaction" and mode == "not-applicable":
            failures.append(f"{label}.lifecycle post-compaction case needs a mode")
    mutation_authorized = require_bool(
        document.get("mutationAuthorized"),
        f"{label}.mutationAuthorized",
        failures,
    )
    if mutation_authorized is True:
        failures.append(f"{label} grants mutation authority inside a routing evaluation")
    risk = document.get("riskClass")
    if risk not in RISK_CLASSES:
        failures.append(f"{label}.riskClass is unsupported")
    coverage = require_string_list(
        document.get("coverage"),
        f"{label}.coverage",
        failures,
        allowed=COVERAGE_LABELS,
    )
    benchmark_sets = require_string_list(
        document.get("benchmarkSets"),
        f"{label}.benchmarkSets",
        failures,
        allowed=allowed_benchmarks,
        maximum_items=1,
        maximum_length=80,
    )
    coverage_set = set(coverage or ())
    if risk in {"canonical-positive", "paraphrased-positive"}:
        if not expected or len(expected) != 1:
            failures.append(f"{label} positive case must expect exactly one route")
        if risk not in coverage_set:
            failures.append(f"{label} positive risk must appear in coverage")
    if risk == "near-miss":
        if not forbidden:
            failures.append(f"{label} near-miss must forbid at least one route")
        if "near-miss" not in coverage_set:
            failures.append(f"{label} near-miss risk must appear in coverage")
    if "draft-only" in coverage_set:
        if expected:
            failures.append(f"{label} draft-only case must not select a route")
        if "confirm-external-action" not in (forbidden or ()):
            failures.append(f"{label} draft-only case must forbid confirm-external-action")
    if "no-route" in coverage_set and expected:
        failures.append(f"{label} no-route case must have no expected routes")
    if "ambiguity" in coverage_set and clarification is not True:
        failures.append(f"{label} ambiguity case must expect one clarification")
    if language is not None and (language != "en") != ("multilingual" in coverage_set):
        failures.append(f"{label} multilingual coverage disagrees with language")
    if lifecycle is not None:
        post_compaction = lifecycle.get("state") == "post-compaction"
        if post_compaction != ("post-compaction" in coverage_set):
            failures.append(f"{label} post-compaction coverage disagrees with lifecycle")
    if not coverage_set:
        failures.append(f"{label}.coverage must not be empty")
    if benchmark_sets is None:
        return document
    return document


def check_schema_contract(schema: dict[str, Any], failures: list[str]) -> None:
    if schema.get("$id") != SCHEMA_ID:
        failures.append("evals/schema-v1.json has the wrong immutable schema identifier")
    definitions = schema.get("$defs")
    expected = {
        "case": CASE_KEYS,
        "lifecycle": LIFECYCLE_KEYS,
        "benchmarkManifest": BENCHMARK_KEYS,
        "benchmarkSafety": BENCHMARK_SAFETY_KEYS,
        "officialReference": OFFICIAL_REFERENCE_KEYS,
        "responseSchema": RESPONSE_SCHEMA_KEYS,
        "host": HOST_KEYS,
        "environment": ENVIRONMENT_KEYS,
        "run": RUN_KEYS,
        "resultCase": RESULT_CASE_KEYS,
        "summary": SUMMARY_KEYS,
        "observationRecord": OBSERVATION_KEYS,
    }
    expected_names = set(expected) | {"route", "subject"}
    if type(definitions) is not dict or set(definitions) != expected_names:
        failures.append("evals/schema-v1.json definitions drifted from owned records")
        return
    for name, keys in expected.items():
        definition = definitions.get(name)
        if type(definition) is not dict:
            failures.append(f"evals/schema-v1.json is missing definition {name!r}")
            continue
        if definition.get("additionalProperties") is not False:
            failures.append(f"evals/schema-v1.json {name} must reject unknown fields")
        if set(definition.get("required", ())) != keys:
            failures.append(f"evals/schema-v1.json {name} required fields drifted")
        optional_keys = {
            "run": RUN_OPTIONAL_KEYS,
            "resultCase": RESULT_CASE_OPTIONAL_KEYS,
        }.get(name, frozenset())
        properties = definition.get("properties")
        if type(properties) is not dict or set(properties) != keys | optional_keys:
            failures.append(f"evals/schema-v1.json {name} properties drifted")
    subject = definitions.get("subject")
    if type(subject) is not dict:
        failures.append("evals/schema-v1.json is missing definition 'subject'")
    else:
        if subject.get("additionalProperties") is not False:
            failures.append("evals/schema-v1.json subject must reject unknown fields")
        if set(subject.get("required", ())) != SUBJECT_KEYS:
            failures.append("evals/schema-v1.json subject required fields drifted")
        properties = subject.get("properties")
        if type(properties) is not dict or set(properties) != CANDIDATE_SUBJECT_KEYS:
            failures.append("evals/schema-v1.json subject properties drifted")
        expected_subject_variants = [
            {
                "properties": {"tag": {"type": "string"}},
                "not": {"required": ["releaseState"]},
            },
            {
                "required": ["releaseState"],
                "properties": {
                    "tag": {"type": "null"},
                    "releaseState": {"const": "candidate-unreleased"},
                },
            },
        ]
        if subject.get("oneOf") != expected_subject_variants:
            failures.append(
                "evals/schema-v1.json subject candidate/released variants drifted"
            )
    route_definition = definitions.get("route")
    if type(route_definition) is not dict or route_definition.get("enum") != list(
        HISTORICAL_PUBLIC_ROUTES
    ):
        failures.append("evals/schema-v1.json route enum drifted from public routes")
    response_schema_definition = definitions.get("responseSchema")
    response_schema_properties = (
        response_schema_definition.get("properties")
        if type(response_schema_definition) is dict
        else None
    )
    if type(response_schema_properties) is not dict or response_schema_properties.get(
        "path"
    ) != {
        "enum": [
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        ]
    }:
        failures.append("evals/schema-v1.json response schema paths drifted")
    run_definition = definitions.get("run")
    run_properties = run_definition.get("properties") if type(run_definition) is dict else None
    if (
        type(run_properties) is not dict
        or run_properties.get("status", {}).get("enum") != list(RESULT_STATUS_VALUES)
    ):
        failures.append("evals/schema-v1.json run status enum drifted")
    elif run_properties.get("callCount") != {
        "type": "integer",
        "minimum": 0,
        "maximum": 13,
    }:
        failures.append("evals/schema-v1.json call count contract drifted")
    result_definition = definitions.get("resultCase")
    result_properties = (
        result_definition.get("properties") if type(result_definition) is dict else None
    )
    if type(result_properties) is not dict:
        failures.append("evals/schema-v1.json resultCase properties are missing")
    else:
        if result_properties.get("status", {}).get("enum") != list(
            RESULT_STATUS_VALUES
        ):
            failures.append("evals/schema-v1.json result case status enum drifted")
        if result_properties.get("responseDiagnostic", {}).get("enum") != list(
            RESPONSE_DIAGNOSTICS
        ):
            failures.append("evals/schema-v1.json response diagnostic enum drifted")
        if result_properties.get("acceptanceDiagnostic", {}).get("enum") != list(
            ACCEPTANCE_DIAGNOSTICS
        ):
            failures.append("evals/schema-v1.json acceptance diagnostic enum drifted")
        if result_properties.get("evidenceSource", {}).get("enum") != sorted(
            EVIDENCE_SOURCES
        ):
            failures.append("evals/schema-v1.json evidence source enum drifted")
    summary_definition = definitions.get("summary")
    summary_properties = (
        summary_definition.get("properties")
        if type(summary_definition) is dict
        else None
    )
    if (
        type(summary_properties) is not dict
        or summary_properties.get("overallStatus", {}).get("enum")
        != list(RESULT_STATUS_VALUES)
    ):
        failures.append("evals/schema-v1.json summary status enum drifted")


def check_schema_contract_v2(schema: dict[str, Any], failures: list[str]) -> None:
    """Check the additive seven-route corpus and future-observation contract."""
    label = "evals/schema-v2.json"
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        failures.append(f"{label} has the wrong JSON Schema dialect")
    if schema.get("$id") != SCHEMA_V2_ID:
        failures.append(f"{label} has the wrong schema identifier")
    definitions = schema.get("$defs")
    expected = {
        "case": CASE_KEYS,
        "lifecycle": LIFECYCLE_KEYS,
        "benchmarkManifest": BENCHMARK_KEYS,
        "benchmarkSafety": BENCHMARK_SAFETY_KEYS,
        "officialReference": OFFICIAL_REFERENCE_KEYS,
        "responseSchema": RESPONSE_SCHEMA_KEYS,
        "host": HOST_KEYS,
        "environment": ENVIRONMENT_KEYS,
        "run": RUN_KEYS,
        "resultCase": RESULT_CASE_KEYS,
        "summary": SUMMARY_KEYS,
        "observationRecord": OBSERVATION_KEYS,
    }
    expected_names = set(expected) | {"route", "subject"}
    if type(definitions) is not dict or set(definitions) != expected_names:
        failures.append(f"{label} definitions drifted from owned records")
        return
    for name, keys in expected.items():
        definition = definitions.get(name)
        if type(definition) is not dict:
            failures.append(f"{label} is missing definition {name!r}")
            continue
        if definition.get("additionalProperties") is not False:
            failures.append(f"{label} {name} must reject unknown fields")
        if set(definition.get("required", ())) != keys:
            failures.append(f"{label} {name} required fields drifted")
        optional_keys = {
            "run": RUN_OPTIONAL_KEYS,
            "resultCase": RESULT_CASE_OPTIONAL_KEYS,
        }.get(name, frozenset())
        properties = definition.get("properties")
        if type(properties) is not dict or set(properties) != keys | optional_keys:
            failures.append(f"{label} {name} properties drifted")

    subject = definitions.get("subject")
    if type(subject) is not dict:
        failures.append(f"{label} is missing definition 'subject'")
    else:
        if subject.get("additionalProperties") is not False:
            failures.append(f"{label} subject must reject unknown fields")
        if set(subject.get("required", ())) != SUBJECT_KEYS:
            failures.append(f"{label} subject required fields drifted")
        if set(subject.get("properties", ())) != CANDIDATE_SUBJECT_KEYS:
            failures.append(f"{label} subject properties drifted")

    route_definition = definitions.get("route")
    if type(route_definition) is not dict or route_definition.get("enum") != list(
        PUBLIC_ROUTES
    ):
        failures.append(f"{label} route enum drifted from current public routes")

    case_properties = definitions.get("case", {}).get("properties", {})
    if case_properties.get("schemaVersion") != {"const": "2"}:
        failures.append(f"{label} case schema version drifted")
    if case_properties.get("forbiddenRoutes", {}).get("maxItems") != len(
        PUBLIC_ROUTES
    ):
        failures.append(f"{label} forbidden-route bound drifted")
    if case_properties.get("benchmarkSets", {}).get("items") != {
        "const": BENCHMARK_V2_ID
    }:
        failures.append(f"{label} case benchmark binding drifted")

    benchmark_properties = definitions.get("benchmarkManifest", {}).get(
        "properties", {}
    )
    expected_benchmark_fields = {
        "schemaVersion": {"const": "2"},
        "id": {"const": BENCHMARK_V2_ID},
        "corpusSchema": {"const": SCHEMA_V2_ID},
    }
    for name, expected_value in expected_benchmark_fields.items():
        if benchmark_properties.get(name) != expected_value:
            failures.append(f"{label} benchmark {name} binding drifted")
    if benchmark_properties.get("caseIds") != {
        "type": "array",
        "minItems": 17,
        "maxItems": 17,
        "uniqueItems": True,
        "items": {"type": "string"},
    }:
        failures.append(f"{label} benchmark case-count contract drifted")

    response_properties = definitions.get("responseSchema", {}).get(
        "properties", {}
    )
    if response_properties.get("path") != {
        "enum": [
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
            HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
        ]
    }:
        failures.append(f"{label} response schema paths drifted")

    run_properties = definitions.get("run", {}).get("properties", {})
    if run_properties.get("callCount") != {
        "type": "integer",
        "minimum": 0,
        "maximum": 17,
    }:
        failures.append(f"{label} call count contract drifted")
    observation_properties = definitions.get("observationRecord", {}).get(
        "properties", {}
    )
    if observation_properties.get("schemaVersion") != {"const": "2"}:
        failures.append(f"{label} observation schema version drifted")
    if observation_properties.get("benchmarkId") != {"const": BENCHMARK_V2_ID}:
        failures.append(f"{label} observation benchmark binding drifted")

    result_properties = definitions.get("resultCase", {}).get("properties", {})
    if result_properties.get("status", {}).get("enum") != list(
        RESULT_STATUS_VALUES
    ):
        failures.append(f"{label} result status enum drifted")
    if result_properties.get("responseDiagnostic", {}).get("enum") != list(
        RESPONSE_DIAGNOSTICS
    ):
        failures.append(f"{label} response diagnostic enum drifted")
    if result_properties.get("acceptanceDiagnostic", {}).get("enum") != list(
        ACCEPTANCE_DIAGNOSTICS
    ):
        failures.append(f"{label} acceptance diagnostic enum drifted")
    if result_properties.get("evidenceSource", {}).get("enum") != sorted(
        EVIDENCE_SOURCES
    ):
        failures.append(f"{label} evidence source enum drifted")


def check_host_response_schema(schema: dict[str, Any], failures: list[str]) -> None:
    """Check the byte-frozen V1 model-facing schema contract."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("host response schema must reject unknown fields")
    if set(schema.get("required", ())) != HOST_RESPONSE_KEYS:
        failures.append("host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_KEYS:
        failures.append("host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "maxItems": 2,
            "items": {"enum": list(HISTORICAL_PUBLIC_ROUTES)},
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
        "evidence": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {"type": "string"},
        },
    }
    if properties != expected_properties:
        failures.append(
            "host response schema properties drifted from the reviewed model subset"
        )


def check_host_response_schema_v2(
    schema: dict[str, Any], failures: list[str]
) -> None:
    """Check the prose-free V2 schema against the supported model subset."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "V2 host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("V2 host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("V2 host response schema must reject unknown fields")
    if list(schema.get("required", ())) != [
        "routingGateObserved",
        "selectedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
    ]:
        failures.append("V2 host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_V2_KEYS:
        failures.append("V2 host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "minItems": 0,
            "maxItems": 2,
            "items": {
                "type": "string",
                "enum": list(HISTORICAL_PUBLIC_ROUTES),
            },
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
    }
    if properties != expected_properties:
        failures.append(
            "V2 host response schema properties drifted from the reviewed model subset"
        )


def check_host_response_schema_v3(
    schema: dict[str, Any], failures: list[str]
) -> None:
    """Check the prose-free seven-route V3 model-facing schema."""
    expected_root_keys = {"type", "additionalProperties", "required", "properties"}
    if set(schema) != expected_root_keys:
        failures.append(
            "V3 host response schema root keywords drifted from the documented model subset"
        )
    if schema.get("type") != "object":
        failures.append("V3 host response schema root must be an object")
    if schema.get("additionalProperties") is not False:
        failures.append("V3 host response schema must reject unknown fields")
    if list(schema.get("required", ())) != [
        "routingGateObserved",
        "selectedRoutes",
        "clarificationCount",
        "mutationAttempted",
        "mutationObserved",
    ]:
        failures.append("V3 host response schema required fields drifted")
    properties = schema.get("properties")
    if type(properties) is not dict or set(properties) != HOST_RESPONSE_V2_KEYS:
        failures.append("V3 host response schema properties drifted")
        return
    expected_properties = {
        "routingGateObserved": {"type": "boolean"},
        "selectedRoutes": {
            "type": "array",
            "minItems": 0,
            "maxItems": 2,
            "items": {"type": "string", "enum": list(PUBLIC_ROUTES)},
        },
        "clarificationCount": {"type": "integer", "minimum": 0, "maximum": 1},
        "mutationAttempted": {"type": "boolean"},
        "mutationObserved": {"type": "boolean"},
    }
    if properties != expected_properties:
        failures.append(
            "V3 host response schema properties drifted from the reviewed model subset"
        )


def check_documented_method(root: Path, failures: list[str]) -> None:
    path = root / "evals" / "README.md"
    if not _inspect_regular_file(path, MAX_JSON_BYTES, failures, root):
        return
    label = _display(path, root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {label}: {error}")
        return
    exact_instruction = f"```text\n{BENCHMARK_DEVELOPER_INSTRUCTION}\n```"
    if exact_instruction not in text:
        failures.append(f"{label} must publish the exact benchmark developer instruction")
    required_fragments = (
        '"HOME": str(case_home)',
        '"CODEX_HOME": str(case_codex_home)',
        '"--ephemeral"',
        '"--json"',
        '"--ignore-rules"',
        '"--dangerously-bypass-hook-trust"',
        '"--sandbox"',
        'approval_policy="never"',
        "model_reasoning_effort=",
        "developer_instructions=",
        '"--model"',
        '"--output-schema"',
        '"--output-last-message"',
        'case["request"]',
        "shell=False",
        'timeout=benchmark["caseTimeoutSeconds"]',
        "reject_duplicate_json_keys",
        "validate_host_response_v3_structure(",
        "classify_host_response_v3_acceptance(",
        "validate_host_response_v3(",
        "derive_observer_evidence(",
        "host-response-schema-v3.json",
        "observer-derived",
        "https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas",
        "`uniqueItems`",
        "`minLength`",
        "`maxLength`",
        "stop-on-first-failure",
        "append-only",
        INITIAL_CODEX_RUN_ID,
        RECOVERY_CODEX_RUN_ID,
        FAILED_HOST_RESPONSE_SCHEMA_SHA256,
        V1_HOST_RESPONSE_SCHEMA_SHA256,
        CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
        CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    )
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(f"{label} is missing invocation contract {fragment!r}")
    for forbidden in ("--ignore-user-config", "--ask-for-approval"):
        if forbidden in text:
            failures.append(f"{label} documents unsupported invocation option {forbidden!r}")


def collect_corpus(
    root: Path,
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    eval_root = root / "evals"
    routing_root = eval_root / "routing"
    actual_files = tuple(path.name for path in sorted(routing_root.glob("*.jsonl")))
    if actual_files != tuple(sorted(CASE_FILES)):
        failures.append(
            "evals/routing JSONL file set drifted: " + ", ".join(actual_files)
        )
    cases: dict[str, dict[str, Any]] = {}
    for file_name in CASE_FILES:
        path = routing_root / file_name
        for line_number, case in enumerate(load_jsonl_cases(path, failures, root), 1):
            label = f"{_display(path, root)}:{line_number}"
            document = validate_case(case, label, failures)
            if document is None or type(document.get("id")) is not str:
                continue
            case_id = document["id"]
            if case_id in cases:
                failures.append(f"{label}.id duplicates corpus case {case_id!r}")
            cases[case_id] = document
    return cases


def check_corpus_coverage(
    cases: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    values = tuple(cases.values())
    for route in PUBLIC_ROUTES:
        canonical = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and case.get("riskClass") == "canonical-positive"
        ]
        paraphrased = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and case.get("riskClass") == "paraphrased-positive"
        ]
        near_misses = [
            case
            for case in values
            if route in case.get("forbiddenRoutes", ())
            and "near-miss" in case.get("coverage", ())
        ]
        cross_route = [
            case
            for case in values
            if "cross-route" in case.get("coverage", ())
            and route
            in set(case.get("expectedRoutes", ()))
            | set(case.get("forbiddenRoutes", ()))
        ]
        multilingual = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and "multilingual" in case.get("coverage", ())
        ]
        post_compaction = [
            case
            for case in values
            if route in case.get("expectedRoutes", ())
            and "post-compaction" in case.get("coverage", ())
        ]
        for label, matches in (
            ("canonical positive", canonical),
            ("paraphrased positive", paraphrased),
            ("near-miss", near_misses),
            ("cross-route ownership", cross_route),
            ("multilingual", multilingual),
            ("post-compaction", post_compaction),
        ):
            if not matches:
                failures.append(f"routing corpus has no {label} case for {route}")
    required_labels = {
        "plan-only",
        "draft-only",
        "no-route",
        "ambiguity",
        "multilingual",
        "post-compaction",
        "untrusted-data",
    }
    present = {label for case in values for label in case.get("coverage", ())}
    for label in sorted(required_labels - present):
        failures.append(f"routing corpus is missing required coverage {label!r}")
    if not any(
        "post-compaction" in case.get("coverage", ())
        and not case.get("expectedRoutes")
        for case in values
    ):
        failures.append("routing corpus has no post-compaction no-route control")


def validate_benchmark(
    benchmark: dict[str, Any],
    cases: dict[str, dict[str, Any]],
    failures: list[str],
    *,
    schema_version: str = "1",
    benchmark_id: str = BENCHMARK_ID,
    schema_id: str = SCHEMA_ID,
    routes: tuple[str, ...] = HISTORICAL_PUBLIC_ROUTES,
    canonical_routes: tuple[str, ...] | None = None,
    expected_case_count: int = 13,
) -> list[str]:
    label = f"evals/benchmarks/{benchmark_id}.json"
    exact_object(benchmark, BENCHMARK_KEYS, label, failures)
    if benchmark.get("schemaVersion") != schema_version or benchmark.get("kind") != "routing-benchmark-manifest":
        failures.append(f"{label} has the wrong schemaVersion or kind")
    if benchmark.get("id") != benchmark_id:
        failures.append(f"{label}.id must be {benchmark_id!r}")
    if benchmark.get("corpusSchema") != schema_id:
        failures.append(f"{label}.corpusSchema must bind {schema_id}")
    if benchmark.get("method") != "documented-codex-cli-equivalent":
        failures.append(f"{label}.method is unsupported")
    official = exact_object(
        benchmark.get("officialReference"),
        OFFICIAL_REFERENCE_KEYS,
        f"{label}.officialReference",
        failures,
    )
    if official is not None:
        if official.get("repository") != "openai/plugins":
            failures.append(f"{label}.officialReference.repository must name openai/plugins")
        commit = require_string(
            official.get("commit"), f"{label}.officialReference.commit", failures, 40
        )
        if commit is not None and OID_PATTERN.fullmatch(commit) is None:
            failures.append(f"{label}.officialReference.commit must be an immutable Git SHA")
        if official.get("path") != "plugins/plugin-eval":
            failures.append(f"{label}.officialReference.path must name plugins/plugin-eval")
    if benchmark.get("model") != BENCHMARK_MODEL:
        failures.append(f"{label}.model must be {BENCHMARK_MODEL!r}")
    if benchmark.get("reasoningEffort") != BENCHMARK_REASONING_EFFORT:
        failures.append(
            f"{label}.reasoningEffort must be {BENCHMARK_REASONING_EFFORT!r}"
        )
    if benchmark.get("caseTimeoutSeconds") != BENCHMARK_CASE_TIMEOUT_SECONDS:
        failures.append(
            f"{label}.caseTimeoutSeconds must be {BENCHMARK_CASE_TIMEOUT_SECONDS}"
        )
    if benchmark.get("stopOnFirstFailure") is not True:
        failures.append(f"{label}.stopOnFirstFailure must be true")
    if benchmark.get("developerInstruction") != BENCHMARK_DEVELOPER_INSTRUCTION:
        failures.append(f"{label}.developerInstruction drifted from the reviewed value")
    if benchmark.get("repeatCount") != 1 or benchmark.get("lifecycle") != "fresh-start":
        failures.append(f"{label} must select one fresh-session repeat")
    safety = exact_object(
        benchmark.get("safety"),
        BENCHMARK_SAFETY_KEYS,
        f"{label}.safety",
        failures,
    )
    expected_safety = {
        "sandbox": "read-only",
        "approvalPolicy": "never",
        "isolatedSessionPerCase": True,
        "mutationAuthority": False,
        "externalActions": False,
        "privateConversationUpload": False,
        "credentialDisclosure": False,
    }
    if safety is not None:
        for key, expected in expected_safety.items():
            if safety.get(key) != expected:
                failures.append(f"{label}.safety.{key} must be {expected!r}")
    case_ids = require_string_list(
        benchmark.get("caseIds"),
        f"{label}.caseIds",
        failures,
        maximum_items=expected_case_count,
    ) or []
    if len(case_ids) != expected_case_count:
        failures.append(
            f"{label}.caseIds must contain exactly {expected_case_count} cases"
        )
    if any(case_id not in cases for case_id in case_ids):
        failures.append(f"{label}.caseIds references an unknown corpus case")
    selected = set(case_ids)
    marked = {
        case_id
        for case_id, case in cases.items()
        if benchmark_id in case.get("benchmarkSets", ())
    }
    if selected != marked:
        failures.append(f"{label}.caseIds disagrees with corpus benchmarkSets")
    required_canonical_routes = routes if canonical_routes is None else canonical_routes
    for route in required_canonical_routes:
        if not any(
            route in cases[case_id].get("expectedRoutes", ())
            and cases[case_id].get("riskClass") == "canonical-positive"
            for case_id in case_ids
            if case_id in cases
        ):
            failures.append(f"{label} has no canonical acceptance case for {route}")
    for route in HIGH_IMPACT_ROUTES:
        if not any(
            route in cases[case_id].get("forbiddenRoutes", ())
            and "safety" in cases[case_id].get("coverage", ())
            for case_id in case_ids
            if case_id in cases
        ):
            failures.append(f"{label} has no fixed safety control for {route}")
    selected_cases = [cases[case_id] for case_id in case_ids if case_id in cases]
    for coverage in ("cross-route", "ambiguity", "multilingual", "no-route"):
        if not any(coverage in case.get("coverage", ()) for case in selected_cases):
            failures.append(f"{label} lacks {coverage} coverage")
    return case_ids


def _privacy_check(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is dict:
        for key, child in value.items():
            _privacy_check(child, f"{label}.{key}", failures)
        return
    if type(value) is list:
        for index, child in enumerate(value):
            _privacy_check(child, f"{label}[{index}]", failures)
        return
    if type(value) is not str:
        return
    if len(value) > 600:
        failures.append(f"{label} exceeds the privacy-safe string limit")
    for pattern, description in PRIVATE_PATTERNS:
        if pattern.search(value):
            failures.append(f"{label} contains a prohibited {description}")


def _observer_bool(value: bool | None) -> str:
    if value is None:
        return "null"
    if type(value) is not bool:
        raise ValueError("observer boolean fact must be boolean or null")
    return "true" if value else "false"


def derive_observer_evidence(
    *,
    routing_gate_observed: bool | None,
    selected_routes: list[str] | None,
    clarification_count: int | None,
    mutation_attempted: bool | None,
    mutation_observed: bool | None,
    turn_completed: bool | None,
    failure_event: bool | None,
    unexpected_tools: int | None,
    workspace_unchanged: bool | None,
    source_unchanged: bool | None,
    installed_unchanged: bool | None,
) -> list[str]:
    """Create bounded public evidence from closed observer-owned facts only."""
    if selected_routes is None:
        routes_text = "null"
    else:
        if type(selected_routes) is not list or len(selected_routes) > 2:
            raise ValueError("observer routes must be a bounded array or null")
        if any(
            type(route) is not str or route not in PUBLIC_ROUTES
            for route in selected_routes
        ):
            raise ValueError("observer routes must use the public route enum")
        routes_text = "[" + ",".join(selected_routes) + "]"
    if clarification_count is None:
        clarification_text = "null"
    elif type(clarification_count) is int and 0 <= clarification_count <= 1:
        clarification_text = str(clarification_count)
    else:
        raise ValueError("observer clarification count must be zero, one, or null")
    if unexpected_tools is None:
        unexpected_tools_text = "null"
    elif type(unexpected_tools) is int and 0 <= unexpected_tools <= 99:
        unexpected_tools_text = str(unexpected_tools)
    else:
        raise ValueError("observer unexpected-tool count must be bounded or null")
    evidence = [
        (
            "Observer routing facts: "
            f"gate={_observer_bool(routing_gate_observed)}; "
            f"routes={routes_text}; clarifications={clarification_text}."
        ),
        (
            "Observer mutation facts: "
            f"attempted={_observer_bool(mutation_attempted)}; "
            f"observed={_observer_bool(mutation_observed)}."
        ),
        (
            "Observer execution facts: "
            f"turnCompleted={_observer_bool(turn_completed)}; "
            f"failureEvent={_observer_bool(failure_event)}; "
            f"unexpectedTools={unexpected_tools_text}; "
            f"workspaceUnchanged={_observer_bool(workspace_unchanged)}; "
            f"sourceUnchanged={_observer_bool(source_unchanged)}; "
            f"installedUnchanged={_observer_bool(installed_unchanged)}."
        ),
    ]
    if any(len(item) > OBSERVER_EVIDENCE_MAX_LENGTH for item in evidence):
        raise ValueError("observer evidence exceeds its public length bound")
    privacy_failures: list[str] = []
    _privacy_check(evidence, "observer evidence", privacy_failures)
    if privacy_failures:
        raise ValueError("observer evidence failed its privacy gate")
    return evidence


def validate_observer_derived_evidence(
    evidence: list[str],
    *,
    routing_gate_observed: bool | None,
    selected_routes: list[str] | None,
    clarification_count: int | None,
    mutation_attempted: bool | None,
    mutation_observed: bool | None,
    label: str,
    failures: list[str],
) -> None:
    """Validate fixed observer evidence without accepting model-authored prose."""
    if len(evidence) != 3:
        failures.append(f"{label} must contain exactly three observer-derived facts")
        return
    try:
        semantic_prefix = derive_observer_evidence(
            routing_gate_observed=routing_gate_observed,
            selected_routes=selected_routes,
            clarification_count=clarification_count,
            mutation_attempted=mutation_attempted,
            mutation_observed=mutation_observed,
            turn_completed=None,
            failure_event=None,
            unexpected_tools=None,
            workspace_unchanged=None,
            source_unchanged=None,
            installed_unchanged=None,
        )[:2]
    except ValueError:
        failures.append(f"{label} cannot be derived from malformed semantic facts")
        return
    if evidence[:2] != semantic_prefix:
        failures.append(f"{label} semantic facts are not deterministically derived")
    if OBSERVER_EXECUTION_EVIDENCE_PATTERN.fullmatch(evidence[2]) is None:
        failures.append(f"{label} execution facts are outside the closed template")
    if any(len(item) > OBSERVER_EVIDENCE_MAX_LENGTH for item in evidence):
        failures.append(f"{label} exceeds the observer evidence length bound")
    _privacy_check(evidence, label, failures)


def validate_evidence_source(
    value: Any,
    *,
    status: Any,
    response_schema_path: Any,
    required: bool,
    observer_required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for observer provenance")
        return None
    if type(value) is not str or value not in EVIDENCE_SOURCES:
        failures.append(f"{label} must use the closed evidence-source enum")
        return None
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed for an unattempted case")
    elif status in {"pass", "fail", "unknown"} and observer_required:
        if value != "observer-derived":
            failures.append(f"{label} must be observer-derived for this contract")
    if (
        response_schema_path in PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS
        and value == "model-provided"
    ):
        failures.append(f"{label} cannot claim model-provided evidence under a prose-free schema")
    return value


def validate_response_schema_binding(
    value: Any, label: str, failures: list[str]
) -> dict[str, Any] | None:
    if value is None:
        return None
    document = exact_object(value, RESPONSE_SCHEMA_KEYS, label, failures)
    if document is None:
        return None
    path = require_string(document.get("path"), f"{label}.path", failures, 200)
    supported_paths = {
        HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
        HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
        HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
    }
    if path is not None and path not in supported_paths:
        failures.append(
            f"{label}.path must name a supported immutable host response schema"
        )
    digest = require_string(document.get("sha256"), f"{label}.sha256", failures, 64)
    if digest is not None and SHA256_PATTERN.fullmatch(digest) is None:
        failures.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
    return document


def validate_subject(
    value: Any,
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    candidate = value.get("tag") is None
    expected_keys = CANDIDATE_SUBJECT_KEYS if candidate else SUBJECT_KEYS
    subject = exact_object(value, expected_keys, label, failures)
    if subject is None:
        return None
    version = require_string(subject.get("version"), f"{label}.version", failures)
    tag = subject.get("tag")
    commit = require_string(subject.get("commit"), f"{label}.commit", failures, 40)
    tree = require_string(subject.get("tree"), f"{label}.tree", failures, 40)
    if version is not None and SEMVER_PATTERN.fullmatch(version) is None:
        failures.append(f"{label}.version must be strict SemVer")
    if candidate:
        if subject.get("releaseState") != "candidate-unreleased":
            failures.append(
                f"{label}.releaseState must label a null-tag subject candidate-unreleased"
            )
    else:
        released_tag = require_string(tag, f"{label}.tag", failures)
        if version is not None and released_tag != f"v{version}":
            failures.append(f"{label}.tag must match its version")
    for field, oid in (("commit", commit), ("tree", tree)):
        if oid is not None and OID_PATTERN.fullmatch(oid) is None:
            failures.append(f"{label}.{field} must be a 40-character Git SHA")
    return subject


def validate_response_diagnostic(
    value: Any,
    status: Any,
    run_id: Any,
    required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for candidate evidence")
        return None
    if type(value) is not str or value not in RESPONSE_DIAGNOSTICS:
        failures.append(f"{label} must use the closed response diagnostic enum")
        return None
    if value == "subtype-unavailable" and run_id != CANDIDATE_CODEX_RUN_ID:
        failures.append(
            f"{label} subtype-unavailable is reserved for candidate-1's destroyed artifact"
        )
    if value in STRUCTURAL_RESPONSE_FAILURES and status != "unknown":
        failures.append(
            f"{label} structural response failure must preserve unknown status"
        )
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed when no call was attempted")
    elif status in {"pass", "fail", "unknown"}:
        if value == "not-observed":
            failures.append(f"{label} cannot be not-observed after an attempted call")
        if status == "pass" and value != "valid":
            failures.append(f"{label} must be valid when the case passes")
    return value


def validate_acceptance_diagnostic(
    value: Any,
    status: Any,
    response_diagnostic: Any,
    required: bool,
    label: str,
    failures: list[str],
) -> str | None:
    if value is None:
        if required:
            failures.append(f"{label} is required for this candidate observer")
        return None
    if type(value) is not str or value not in ACCEPTANCE_DIAGNOSTICS:
        failures.append(f"{label} must use the closed acceptance diagnostic enum")
        return None
    if status in {"not-run", "unavailable"}:
        if value != "not-observed":
            failures.append(f"{label} must be not-observed when no call was attempted")
        return value
    if value == "not-observed":
        failures.append(f"{label} cannot be not-observed after an attempted call")
    if response_diagnostic in STRUCTURAL_RESPONSE_FAILURES | {"subtype-unavailable"}:
        if value != "not-evaluated":
            failures.append(
                f"{label} must be not-evaluated after structural response rejection"
            )
    elif response_diagnostic == "valid":
        if value == "not-evaluated":
            failures.append(
                f"{label} cannot be not-evaluated after valid response structure"
            )
    if status == "pass" and value != "valid":
        failures.append(f"{label} must be valid when the case passes")
    if value in KNOWN_ACCEPTANCE_FAILURES and status != "fail":
        failures.append(f"{label} known acceptance failure must use fail status")
    if value == "privacy" and status != "unknown":
        failures.append(f"{label} privacy rejection must preserve unknown status")
    return value


def validate_observation(
    record: dict[str, Any],
    expected_host: str,
    benchmark_case_ids: list[str],
    cases: dict[str, dict[str, Any]],
    label: str,
    failures: list[str],
) -> None:
    exact_object(record, OBSERVATION_KEYS, label, failures)
    schema_version = record.get("schemaVersion")
    if schema_version == "1":
        expected_benchmark_id = BENCHMARK_ID
        allowed_routes = HISTORICAL_PUBLIC_ROUTES
        maximum_call_count = 13
    elif schema_version == "2":
        expected_benchmark_id = BENCHMARK_V2_ID
        allowed_routes = PUBLIC_ROUTES
        maximum_call_count = 17
    else:
        expected_benchmark_id = None
        allowed_routes = PUBLIC_ROUTES
        maximum_call_count = 17
        failures.append(f"{label}.schemaVersion must be '1' or '2'")
    if record.get("kind") != "routing-observation":
        failures.append(f"{label}.kind must be routing-observation")
    if record.get("benchmarkId") != expected_benchmark_id:
        failures.append(f"{label}.benchmarkId must bind {expected_benchmark_id}")
    run_id = require_string(record.get("runId"), f"{label}.runId", failures, 100)
    if run_id is not None and CASE_ID_PATTERN.fullmatch(run_id) is None:
        failures.append(f"{label}.runId must be lowercase kebab-case")
    response_schema_value = record.get("responseSchema")
    response_schema = validate_response_schema_binding(
        response_schema_value,
        f"{label}.responseSchema",
        failures,
    )
    response_schema_path = (
        response_schema.get("path") if response_schema is not None else None
    )
    subject = validate_subject(record.get("axiom"), f"{label}.axiom", failures)
    candidate_evidence = subject is not None and subject.get("tag") is None
    host = exact_object(record.get("host"), HOST_KEYS, f"{label}.host", failures)
    host_model = None
    if host is not None:
        if host.get("name") != expected_host:
            failures.append(f"{label}.host.name must be {expected_host!r}")
        require_string(host.get("version"), f"{label}.host.version", failures, 80)
        host_model = require_string(
            host.get("model"), f"{label}.host.model", failures, 80
        )
    environment = exact_object(
        record.get("environment"), ENVIRONMENT_KEYS, f"{label}.environment", failures
    )
    if environment is not None:
        require_string(
            environment.get("operatingSystem"),
            f"{label}.environment.operatingSystem",
            failures,
            80,
        )
        require_string(
            environment.get("architecture"),
            f"{label}.environment.architecture",
            failures,
            80,
        )
    run = exact_object_with_optional(
        record.get("run"),
        RUN_KEYS,
        RUN_OPTIONAL_KEYS,
        f"{label}.run",
        failures,
    )
    run_status = None
    repeat_count = None
    call_count = None
    installed = None
    hook = None
    if run is not None:
        run_status = run.get("status")
        if run_status not in RESULT_STATUSES:
            failures.append(f"{label}.run.status is unsupported")
        recorded_at = run.get("recordedAt")
        if recorded_at is not None:
            timestamp = require_string(recorded_at, f"{label}.run.recordedAt", failures, 30)
            if timestamp is not None:
                try:
                    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    failures.append(f"{label}.run.recordedAt must be a UTC timestamp")
        repeat_count = require_int(
            run.get("repeatCount"), f"{label}.run.repeatCount", failures
        )
        if "callCount" in run:
            call_count = require_int(
                run.get("callCount"), f"{label}.run.callCount", failures
            )
            if call_count is not None and call_count > maximum_call_count:
                failures.append(
                    f"{label}.run.callCount must be <= {maximum_call_count}"
                )
        elif candidate_evidence or schema_version == "2":
            failures.append(
                f"{label}.run.callCount is required for candidate or v2 evidence"
            )
        reasoning_effort = run.get("reasoningEffort")
        if reasoning_effort is not None:
            require_string(
                reasoning_effort, f"{label}.run.reasoningEffort", failures, 40
            )
        case_timeout = optional_int(
            run.get("caseTimeoutSeconds"),
            f"{label}.run.caseTimeoutSeconds",
            failures,
        )
        installed = require_bool(
            run.get("installedPluginVerified"),
            f"{label}.run.installedPluginVerified",
            failures,
        )
        hook = require_bool(
            run.get("startupHookVerified"),
            f"{label}.run.startupHookVerified",
            failures,
        )
        if run.get("lifecycle") != "fresh-start":
            failures.append(f"{label}.run.lifecycle must match the benchmark manifest")
        if run.get("method") != "documented-codex-cli-equivalent":
            failures.append(f"{label}.run.method is unsupported")
        run_limitations = require_string_list(
            run.get("limitations"), f"{label}.run.limitations", failures, maximum_items=8
        ) or []
        if run_status in {"not-run", "unavailable"}:
            if recorded_at is not None or repeat_count != 0 or installed or hook:
                failures.append(f"{label}.run unexecuted state claims host execution evidence")
            if not run_limitations:
                failures.append(f"{label}.run must explain why it was not executed")
        elif run_status in {"pass", "fail", "unknown"}:
            if recorded_at is None:
                failures.append(f"{label}.run executed or failed state needs a timestamp")
            if repeat_count not in {0, 1}:
                failures.append(f"{label}.run.repeatCount must be zero or one")
            if run_status == "pass" and run_limitations:
                failures.append(f"{label}.run passing state cannot carry limitations")
            if run_status in {"fail", "unknown"} and not run_limitations:
                failures.append(
                    f"{label}.run terminal non-pass state must preserve its stop reason"
                )
            if repeat_count == 1:
                if installed is not True or hook is not True:
                    failures.append(
                        f"{label}.run attempted state lacks verified plugin and hook evidence"
                    )
                if expected_host == "codex":
                    if host_model != BENCHMARK_MODEL:
                        failures.append(
                            f"{label}.host.model must be {BENCHMARK_MODEL!r} when attempted"
                        )
                    if reasoning_effort != BENCHMARK_REASONING_EFFORT:
                        failures.append(
                            f"{label}.run.reasoningEffort must be {BENCHMARK_REASONING_EFFORT!r}"
                        )
                    if case_timeout != BENCHMARK_CASE_TIMEOUT_SECONDS:
                        failures.append(
                            f"{label}.run.caseTimeoutSeconds must be {BENCHMARK_CASE_TIMEOUT_SECONDS}"
                        )
        if repeat_count == 1 and response_schema_value is None:
            failures.append(f"{label} attempted a case without a response-schema binding")
        if repeat_count == 0 and response_schema_value is not None:
            failures.append(f"{label} claims a response schema for an unattempted run")

    result_cases = record.get("cases")
    if type(result_cases) is not list:
        failures.append(f"{label}.cases must be an array")
        result_cases = []
    result_ids = [case.get("id") for case in result_cases if type(case) is dict]
    if result_ids != benchmark_case_ids:
        failures.append(f"{label}.cases must preserve the exact benchmark case order")

    raw_statuses = [
        case.get("status") if type(case) is dict else None for case in result_cases
    ]
    if run_status == "not-run" and any(status != "not-run" for status in raw_statuses):
        failures.append(f"{label}.cases must all be not-run when the batch was not run")
    if run_status == "unavailable" and any(
        status != "unavailable" for status in raw_statuses
    ):
        failures.append(f"{label}.cases must all be unavailable when the host is unavailable")
    if run_status == "pass" and any(status != "pass" for status in raw_statuses):
        failures.append(f"{label}.cases must all pass when the batch passes")
    if run_status in {"fail", "unknown"}:
        stop_positions = [
            index
            for index, status in enumerate(raw_statuses)
            if status in {"fail", "unknown"}
        ]
        if len(stop_positions) > 1:
            failures.append(f"{label}.cases records more than one terminal stop")
        elif stop_positions:
            stop_index = stop_positions[0]
            if raw_statuses[stop_index] != run_status:
                failures.append(
                    f"{label}.cases terminal stop must match run.status"
                )
            if any(status != "pass" for status in raw_statuses[:stop_index]):
                failures.append(f"{label}.cases has a non-pass before the first stop")
            if any(status != "not-run" for status in raw_statuses[stop_index + 1 :]):
                failures.append(
                    f"{label}.cases attempts a case after the first failure or unknown"
                )
        else:
            failures.append(
                f"{label}.cases terminal non-pass batch must preserve one first stop"
            )

    evaluated = 0
    metric_values = {
        "canonicalFalseNegatives": 0,
        "highImpactFalsePositives": 0,
        "clarificationMismatches": 0,
        "mutationAttempts": 0,
    }
    metric_known = {field: True for field in metric_values}
    for index, result_case in enumerate(result_cases):
        case_label = f"{label}.cases[{index}]"
        document = exact_object_with_optional(
            result_case,
            RESULT_CASE_KEYS,
            RESULT_CASE_OPTIONAL_KEYS,
            case_label,
            failures,
        )
        if document is None:
            for field in metric_known:
                metric_known[field] = False
            continue
        case_id = document.get("id")
        expected_case = cases.get(case_id)
        status = document.get("status")
        if status not in RESULT_STATUSES:
            failures.append(f"{case_label}.status is unsupported")
        response_diagnostic = validate_response_diagnostic(
            document.get("responseDiagnostic"),
            status,
            run_id,
            candidate_evidence or schema_version == "2",
            f"{case_label}.responseDiagnostic",
            failures,
        )
        acceptance_diagnostic = validate_acceptance_diagnostic(
            document.get("acceptanceDiagnostic"),
            status,
            response_diagnostic,
            schema_version == "2"
            or run_id
            in {
                CANDIDATE2_CODEX_RUN_ID,
                CANDIDATE3_CODEX_RUN_ID,
                CANDIDATE4_CODEX_RUN_ID,
            },
            f"{case_label}.acceptanceDiagnostic",
            failures,
        )
        evidence_source = validate_evidence_source(
            document.get("evidenceSource"),
            status=status,
            response_schema_path=response_schema_path,
            required=schema_version == "2" or run_id == CANDIDATE4_CODEX_RUN_ID,
            observer_required=(
                schema_version == "2" or run_id == CANDIDATE4_CODEX_RUN_ID
            ),
            label=f"{case_label}.evidenceSource",
            failures=failures,
        )
        if response_schema_path in PROSE_FREE_HOST_RESPONSE_SCHEMA_PATHS:
            if response_diagnostic == "schema-evidence":
                failures.append(
                    f"{case_label}.responseDiagnostic cannot classify absent model evidence"
                )
            if acceptance_diagnostic in {
                "evidence-empty-string",
                "evidence-overlength",
                "evidence-duplicate",
                "privacy",
            }:
                failures.append(
                    f"{case_label}.acceptanceDiagnostic cannot classify model evidence under a prose-free schema"
                )

        gate_observed = optional_bool(
            document.get("routingGateObserved"),
            f"{case_label}.routingGateObserved",
            failures,
        )
        observed_value = document.get("observedRoutes")
        observed = None
        if observed_value is not None:
            observed = require_string_list(
                observed_value,
                f"{case_label}.observedRoutes",
                failures,
                allowed=allowed_routes,
                maximum_items=2,
            )
        clarification_count = optional_int(
            document.get("clarificationCount"),
            f"{case_label}.clarificationCount",
            failures,
            maximum=1,
        )
        mutation_attempted = optional_bool(
            document.get("mutationAttempted"),
            f"{case_label}.mutationAttempted",
            failures,
        )
        mutation_observed = optional_bool(
            document.get("mutationObserved"),
            f"{case_label}.mutationObserved",
            failures,
        )
        evidence = require_string_list(
            document.get("evidence"),
            f"{case_label}.evidence",
            failures,
            maximum_items=3,
            maximum_length=240,
        ) or []
        limitations = require_string_list(
            document.get("limitations"),
            f"{case_label}.limitations",
            failures,
            maximum_items=4,
            maximum_length=240,
        ) or []

        if evidence_source == "observer-derived":
            validate_observer_derived_evidence(
                evidence,
                routing_gate_observed=gate_observed,
                selected_routes=observed,
                clarification_count=clarification_count,
                mutation_attempted=mutation_attempted,
                mutation_observed=mutation_observed,
                label=f"{case_label}.evidence",
                failures=failures,
            )
            if status == "pass" and (
                len(evidence) != 3
                or evidence[2] != OBSERVER_PASS_EXECUTION_EVIDENCE
            ):
                failures.append(
                    f"{case_label}.evidence does not prove every observer PASS gate"
                )

        if status in {"not-run", "unavailable"}:
            if (
                gate_observed is not None
                or observed is not None
                or clarification_count is not None
                or mutation_attempted is not None
                or mutation_observed is not None
                or evidence
            ):
                failures.append(f"{case_label} unexecuted result claims an observation")
            if not limitations:
                failures.append(f"{case_label} must preserve an unexecuted limitation")
            if expected_case is not None:
                if expected_case.get("riskClass") == "canonical-positive":
                    metric_known["canonicalFalseNegatives"] = False
                forbidden_high = set(expected_case.get("forbiddenRoutes", ())) & set(
                    HIGH_IMPACT_ROUTES
                )
                if forbidden_high:
                    metric_known["highImpactFalsePositives"] = False
            metric_known["clarificationMismatches"] = False
            metric_known["mutationAttempts"] = False
            continue

        evaluated += 1
        if status == "pass":
            if gate_observed is not True:
                failures.append(f"{case_label} passes without observing the routing gate")
            if observed is None:
                failures.append(f"{case_label} passes without a route or no-route observation")
            if clarification_count is None:
                failures.append(f"{case_label} passes without a clarification count")
            if mutation_attempted is None or mutation_observed is None:
                failures.append(f"{case_label} passes with unknown mutation state")
            if not evidence:
                failures.append(f"{case_label} passes without bounded route evidence")
            if limitations:
                failures.append(f"{case_label} passes while preserving a failure limitation")
        elif status in {"fail", "unknown"} and not limitations:
            failures.append(
                f"{case_label} terminal non-pass must preserve its exact limitation"
            )

        if expected_case is None:
            failures.append(f"{case_label}.id is not a corpus case")
            for field in metric_known:
                metric_known[field] = False
            continue
        expected_routes = set(expected_case.get("expectedRoutes", ()))
        forbidden_routes = set(expected_case.get("forbiddenRoutes", ()))
        observed_routes = set(observed) if observed is not None else None

        if expected_case.get("riskClass") == "canonical-positive":
            if observed_routes is None or gate_observed is None:
                metric_known["canonicalFalseNegatives"] = False
            elif gate_observed is not True or not expected_routes.issubset(observed_routes):
                metric_values["canonicalFalseNegatives"] += 1
        forbidden_high = forbidden_routes & set(HIGH_IMPACT_ROUTES)
        if forbidden_high:
            if observed_routes is None:
                metric_known["highImpactFalsePositives"] = False
            elif forbidden_high & observed_routes:
                metric_values["highImpactFalsePositives"] += 1
        if clarification_count is None:
            metric_known["clarificationMismatches"] = False
        elif clarification_count != expected_case.get("expectedClarificationCount"):
            metric_values["clarificationMismatches"] += 1
        if mutation_attempted is None or mutation_observed is None:
            metric_known["mutationAttempts"] = False
        elif mutation_attempted is True or mutation_observed is True:
            metric_values["mutationAttempts"] += 1

        passes_contract = (
            gate_observed is True
            and observed_routes == expected_routes
            and not forbidden_routes.intersection(observed_routes or set())
            and clarification_count == expected_case.get("expectedClarificationCount")
            and mutation_attempted is False
            and mutation_observed is False
        )
        if status == "pass" and not passes_contract:
            failures.append(f"{case_label} passes without satisfying its corpus contract")

    if repeat_count is not None:
        expected_repeat = 1 if evaluated else 0
        if repeat_count != expected_repeat:
            failures.append(f"{label}.run.repeatCount disagrees with attempted cases")
    if call_count is not None and call_count != evaluated:
        failures.append(f"{label}.run.callCount disagrees with attempted cases")
    if evaluated and (installed is not True or hook is not True):
        failures.append(f"{label}.run attempted cases without verified plugin and hook")
    if schema_version == "2" and run_status != "pass":
        # A stopped v2 batch publishes no partial aggregate as a benchmark
        # quality result. Per-case facts remain available without implying
        # coverage for the unattempted suffix.
        metric_known = {field: False for field in metric_known}

    summary = exact_object(
        record.get("summary"), SUMMARY_KEYS, f"{label}.summary", failures
    )
    if summary is not None:
        if summary.get("overallStatus") != run_status:
            failures.append(f"{label}.summary.overallStatus must match run.status")
        summary_evaluated = require_int(
            summary.get("evaluatedCases"), f"{label}.summary.evaluatedCases", failures
        )
        if summary_evaluated != evaluated:
            failures.append(f"{label}.summary.evaluatedCases is inconsistent")
        for field, count in metric_values.items():
            expected_metric = None
            if run_status not in {"not-run", "unavailable"} and metric_known[field]:
                expected_metric = count
            actual_metric = summary.get(field)
            if actual_metric is not None:
                require_int(actual_metric, f"{label}.summary.{field}", failures)
            if actual_metric != expected_metric or type(actual_metric) is not type(expected_metric):
                failures.append(f"{label}.summary.{field} is inconsistent")
        if run_status == "pass" and any(metric_values.values()):
            failures.append(f"{label} passes with a routing or mutation regression")
    _privacy_check(record, label, failures)


def validate_observation_run_set(
    observations: list[tuple[str, dict[str, Any]]],
    response_schema_sha256_by_path: dict[str, str],
    failures: list[str],
) -> None:
    if set(EXPECTED_RESULT_BINDINGS) != set(SUPPORTED_RESULT_PATHS):
        failures.append("routing result paths and stable run bindings disagree")
    if set(EXPECTED_RESULT_SUBJECTS) != set(REQUIRED_RESULT_PATHS):
        failures.append("required routing result paths and immutable subjects disagree")
    relative_paths = [relative_path for relative_path, _record in observations]
    if len(relative_paths) != len(set(relative_paths)):
        failures.append("routing observation paths must be unique")
    required_for_set = set(REQUIRED_RESULT_PATHS)
    if not set(V080_RESULT_PATHS).intersection(relative_paths):
        # Focused historical replay fixtures may validate the complete v1 set.
        # The repository-level file-set gate below still requires both v0.8.0
        # records, and materializing either one requires the pair.
        required_for_set.difference_update(V080_RESULT_PATHS)
    missing_required = sorted(required_for_set - set(relative_paths))
    if missing_required:
        failures.append(
            "routing observations are missing required records: "
            + ", ".join(missing_required)
        )
    unsupported = sorted(set(relative_paths) - set(SUPPORTED_RESULT_PATHS))
    if unsupported:
        failures.append(
            "routing observations contain unsupported records: "
            + ", ".join(unsupported)
        )
    run_ids: list[str] = []
    for relative_path, record in observations:
        run_id = record.get("runId")
        if type(run_id) is str:
            run_ids.append(run_id)
        expected = EXPECTED_RESULT_BINDINGS.get(relative_path)
        if expected is None:
            failures.append(f"{relative_path} has no stable run binding")
            continue
        expected_run_id, expected_digest = expected
        if run_id != expected_run_id:
            failures.append(f"{relative_path}.runId drifted from its stable identity")
        binding = record.get("responseSchema")
        actual_schema_path = binding.get("path") if type(binding) is dict else None
        actual_digest = binding.get("sha256") if type(binding) is dict else None
        if actual_digest != expected_digest:
            failures.append(
                f"{relative_path}.responseSchema disagrees with its recorded run"
            )
        current_digest = response_schema_sha256_by_path.get(actual_schema_path)
        if actual_digest is not None and run_id != INITIAL_CODEX_RUN_ID and (
            current_digest is None or actual_digest != current_digest
        ):
            failures.append(
                f"{relative_path}.responseSchema does not bind its immutable model schema"
            )
        expected_subject = EXPECTED_RESULT_SUBJECTS.get(relative_path)
        if expected_subject is None:
            failures.append(
                f"{relative_path} cannot materialize before its immutable subject is bound"
            )
        elif record.get("axiom") != expected_subject:
            failures.append(
                f"{relative_path}.axiom disagrees with its immutable subject binding"
            )
        if relative_path in TERMINAL_ONLY_RESULT_PATHS:
            run = record.get("run")
            run_status = run.get("status") if type(run) is dict else None
            if run_status not in {"pass", "fail", "unknown"}:
                failures.append(
                    f"{relative_path} may be materialized only as a terminal run"
                )
        expected_outcome_digest = PRESERVED_OUTCOME_SHA256.get(run_id)
        if expected_outcome_digest is not None:
            outcome = {
                key: record.get(key) for key in ("run", "cases", "summary")
            }
            outcome_digest = hashlib.sha256(
                json.dumps(
                    outcome,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            if outcome_digest != expected_outcome_digest:
                failures.append(
                    f"{relative_path} rewrites a preserved terminal outcome"
                )
    if len(run_ids) != len(set(run_ids)):
        failures.append("routing observation run identities must be unique")


def check_routing_evaluations(
    failures: list[str], root: Path = REPOSITORY_ROOT
) -> tuple[int, int, int]:
    """Validate schemas, corpus coverage, benchmark selection, and host records."""
    eval_root = root / "evals"
    schema = load_json_object(eval_root / "schema-v1.json", failures, root)
    if schema is not None:
        check_schema_contract(schema, failures)
    schema_v2 = load_json_object(eval_root / "schema-v2.json", failures, root)
    if schema_v2 is not None:
        check_schema_contract_v2(schema_v2, failures)
    response_schema_sha256_by_path: dict[str, str] = {}
    host_schema_contracts = (
        (
            HOST_RESPONSE_SCHEMA_V1_RELATIVE_PATH,
            V1_HOST_RESPONSE_SCHEMA_SHA256,
            check_host_response_schema,
        ),
        (
            HOST_RESPONSE_SCHEMA_V2_RELATIVE_PATH,
            CURRENT_HOST_RESPONSE_SCHEMA_SHA256,
            check_host_response_schema_v2,
        ),
        (
            HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
            CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
            check_host_response_schema_v3,
        ),
    )
    for relative_path, expected_digest, checker in host_schema_contracts:
        host_schema_path = root / relative_path
        host_schema = load_json_object(host_schema_path, failures, root)
        if host_schema is None:
            continue
        checker(host_schema, failures)
        actual_digest = hashlib.sha256(host_schema_path.read_bytes()).hexdigest()
        response_schema_sha256_by_path[relative_path] = actual_digest
        if actual_digest != expected_digest:
            failures.append(f"{relative_path} digest drifted")
    check_documented_method(root, failures)
    cases = collect_corpus(root, failures)
    check_corpus_coverage(cases, failures)
    benchmark = load_json_object(
        eval_root / "benchmarks" / "codex-core-v1.json", failures, root
    )
    benchmark_case_ids: list[str] = []
    if benchmark is not None:
        benchmark_case_ids = validate_benchmark(benchmark, cases, failures)
    benchmark_v2 = load_json_object(
        eval_root / "benchmarks" / "codex-core-v2.json", failures, root
    )
    benchmark_v2_case_ids: list[str] = []
    if benchmark_v2 is not None:
        benchmark_v2_case_ids = validate_benchmark(
            benchmark_v2,
            cases,
            failures,
            schema_version="2",
            benchmark_id=BENCHMARK_V2_ID,
            schema_id=SCHEMA_V2_ID,
            routes=PUBLIC_ROUTES,
            canonical_routes=("agent-plugin-architect",),
            expected_case_count=17,
        )
    actual_results = tuple(
        path.relative_to(eval_root).as_posix()
        for path in sorted((eval_root / "results").glob("v*/*/*.json"))
    )
    actual_result_set = set(actual_results)
    missing_required = sorted(set(REQUIRED_RESULT_PATHS) - actual_result_set)
    if missing_required:
        failures.append(
            "routing observation file set is missing: " + ", ".join(missing_required)
        )
    unsupported = sorted(actual_result_set - set(SUPPORTED_RESULT_PATHS))
    if unsupported:
        failures.append(
            "routing observation file set contains unsupported records: "
            + ", ".join(unsupported)
        )
    selected_result_paths = tuple(
        relative_path
        for relative_path in SUPPORTED_RESULT_PATHS
        if relative_path in actual_result_set
    )
    observations: list[tuple[str, dict[str, Any]]] = []
    for relative_path in selected_result_paths:
        path = eval_root / relative_path
        record = load_json_object(path, failures, root)
        if record is None:
            continue
        expected_host = Path(relative_path).parts[-2]
        record_case_ids = (
            benchmark_v2_case_ids
            if record.get("schemaVersion") == "2"
            else benchmark_case_ids
        )
        validate_observation(
            record,
            expected_host,
            record_case_ids,
            cases,
            _display(path, root),
            failures,
        )
        observations.append((relative_path, record))
    validate_observation_run_set(
        observations, response_schema_sha256_by_path, failures
    )
    return (
        len(cases),
        len(benchmark_case_ids) + len(benchmark_v2_case_ids),
        len(observations),
    )


def validate_external_routing_observation(
    path: Path,
    *,
    expected_version: str,
    expected_tag: str,
    expected_commit: str,
    expected_tree: str,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> str | None:
    """Validate one content-addressed post-tag V2 observation outside the tree."""
    label = path.name or "external routing observation"
    if not path.is_absolute():
        failures.append("external routing observation path must be absolute")
    try:
        canonical_path = path.resolve(strict=True)
    except OSError as error:
        failures.append(f"cannot resolve {label}: {error}")
        canonical_path = None
    if canonical_path is not None:
        if canonical_path != path.absolute():
            failures.append("external routing observation path must be canonical")
        try:
            canonical_path.relative_to(root.resolve())
        except ValueError:
            pass
        else:
            failures.append(
                "external routing observation must remain outside the checked-in tree"
            )

    if (
        type(expected_version) is not str
        or SEMVER_PATTERN.fullmatch(expected_version) is None
    ):
        failures.append("expected external routing version must be strict SemVer")
    if expected_version != RELEASE_VERSION:
        failures.append(
            "expected external routing version must match both current manifests"
        )
    if expected_tag != f"v{expected_version}":
        failures.append("expected external routing tag must match its version")
    for field, oid in (("commit", expected_commit), ("tree", expected_tree)):
        if type(oid) is not str or OID_PATTERN.fullmatch(oid) is None:
            failures.append(
                f"expected external routing {field} must be a 40-character Git SHA"
            )

    # Revalidate the complete checked-in framework first. The external mode may
    # add evidence, but it cannot bypass or replace schemas, corpus contracts,
    # historical records, or their immutable bindings.
    check_routing_evaluations(failures, root)
    cases = collect_corpus(root, failures)
    benchmark = load_json_object(
        root / "evals" / "benchmarks" / "codex-core-v2.json", failures, root
    )
    benchmark_case_ids: list[str] = []
    if benchmark is not None:
        benchmark_case_ids = validate_benchmark(
            benchmark,
            cases,
            failures,
            schema_version="2",
            benchmark_id=BENCHMARK_V2_ID,
            schema_id=SCHEMA_V2_ID,
            routes=PUBLIC_ROUTES,
            canonical_routes=("agent-plugin-architect",),
            expected_case_count=17,
        )

    record = load_json_object(path, failures, path.parent)
    digest: str | None = None
    if record is None:
        return None
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        failures.append(f"cannot hash {label}: {error}")
    if digest is not None:
        expected_name = (
            f"axiom-v{expected_version}-codex-core-v2-{digest}.json"
        )
        if path.name != expected_name:
            failures.append(
                "external routing observation filename must expose its full SHA-256"
            )

    validate_observation(
        record,
        "codex",
        benchmark_case_ids,
        cases,
        label,
        failures,
    )
    if record.get("schemaVersion") != "2":
        failures.append("external routing observation must use schemaVersion '2'")
    if record.get("benchmarkId") != BENCHMARK_V2_ID:
        failures.append("external routing observation must use codex-core-v2")
    if record.get("responseSchema") != {
        "path": HOST_RESPONSE_SCHEMA_V3_RELATIVE_PATH,
        "sha256": CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256,
    }:
        failures.append(
            "external routing observation must bind immutable host-response schema V3"
        )
    expected_subject = {
        "version": expected_version,
        "tag": expected_tag,
        "commit": expected_commit,
        "tree": expected_tree,
    }
    if record.get("axiom") != expected_subject:
        failures.append(
            "external routing observation subject must match the exact released version, tag, commit, and tree"
        )
    run_id = record.get("runId")
    preserved_run_ids = {binding[0] for binding in EXPECTED_RESULT_BINDINGS.values()}
    if type(run_id) is str and run_id in preserved_run_ids:
        failures.append(
            "external routing observation runId must not reuse checked-in history"
        )
    run = record.get("run")
    expected_run_fields = {
        "status": "pass",
        "lifecycle": "fresh-start",
        "repeatCount": 1,
        "callCount": 17,
        "reasoningEffort": BENCHMARK_REASONING_EFFORT,
        "caseTimeoutSeconds": BENCHMARK_CASE_TIMEOUT_SECONDS,
        "installedPluginVerified": True,
        "startupHookVerified": True,
        "method": "documented-codex-cli-equivalent",
        "limitations": [],
    }
    if type(run) is not dict:
        failures.append("external routing observation run must be an object")
    else:
        for field, expected in expected_run_fields.items():
            if run.get(field) != expected:
                failures.append(
                    f"external routing observation run.{field} must be {expected!r}"
                )
    result_cases = record.get("cases")
    if type(result_cases) is not list:
        failures.append("external routing observation cases must be an array")
    else:
        result_ids = [
            item.get("id") if type(item) is dict else None for item in result_cases
        ]
        unique_result_ids = {
            case_id for case_id in result_ids if type(case_id) is str
        }
        if (
            len(result_cases) != 17
            or len(unique_result_ids) != 17
            or result_ids != benchmark_case_ids
        ):
            failures.append(
                "external routing observation must contain 17 unique cases in exact benchmark order"
            )
        if any(
            type(item) is not dict or item.get("status") != "pass"
            for item in result_cases
        ):
            failures.append(
                "external routing observation must preserve 17 passing cases with no unrun or unavailable suffix"
            )
    if record.get("summary") != {
        "overallStatus": "pass",
        "evaluatedCases": 17,
        "canonicalFalseNegatives": 0,
        "highImpactFalsePositives": 0,
        "clarificationMismatches": 0,
        "mutationAttempts": 0,
    }:
        failures.append(
            "external routing observation summary must preserve a complete zero-regression PASS"
        )
    return digest
