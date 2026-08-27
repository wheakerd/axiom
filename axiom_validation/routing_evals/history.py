"""Strict loader and compatibility bindings for immutable routing history."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from ..context import REPOSITORY_ROOT


HISTORY_INDEX_RELATIVE_PATH = "validation_data/routing-history-v1.json"
HISTORY_INDEX_PATH = REPOSITORY_ROOT / HISTORY_INDEX_RELATIVE_PATH
HISTORY_INDEX_SHA256 = (
    "9b1f28cdc004af83d1ec37a892de62b273975ec8c919aa11c15745df49c12e21"
)
MAX_HISTORY_INDEX_BYTES = 64 * 1024
ROOT_KEYS = frozenset({"schemaVersion", "kind", "schemaDigests", "entries"})
SCHEMA_DIGEST_KEYS = frozenset(
    {
        "failedHostResponseV1",
        "hostResponseV1",
        "hostResponseV2",
        "hostResponseV3",
    }
)
ENTRY_KEYS = frozenset(
    {
        "key",
        "group",
        "path",
        "runId",
        "responseSchemaSha256",
        "outcomeSha256",
        "subject",
        "terminalOnly",
    }
)
RELEASED_SUBJECT_KEYS = frozenset({"version", "tag", "commit", "tree"})
CANDIDATE_SUBJECT_KEYS = RELEASED_SUBJECT_KEYS | frozenset({"releaseState"})
ID_PATTERN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*\Z")
RUN_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SEMVER_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z"
)
OID_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class HistoryIndexError(ValueError):
    """Raised when immutable routing history is malformed or has drifted."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise HistoryIndexError(f"duplicate JSON key {key!r}")
        document[key] = value
    return document


def _exact_keys(value: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise HistoryIndexError(f"{label} must be an object")
    actual = set(value)
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        unknown = sorted(actual - set(expected))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise HistoryIndexError(f"{label} fields must be exact ({'; '.join(details)})")
    return value


def _require_id(value: Any, label: str, pattern: re.Pattern[str]) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise HistoryIndexError(f"{label} must be a strict lowercase identifier")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if type(value) is not str or SHA256_PATTERN.fullmatch(value) is None:
        raise HistoryIndexError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_result_path(value: Any, label: str, repository_root: Path) -> str:
    if type(value) is not str or not value:
        raise HistoryIndexError(f"{label} must be a non-empty relative path")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure.as_posix() != value
        or any(part in {"", ".", ".."} for part in pure.parts)
        or len(pure.parts) < 4
        or pure.parts[0] != "results"
        or pure.suffix != ".json"
    ):
        raise HistoryIndexError(f"{label} must remain under evals/results as JSON")
    result_root = (repository_root / "evals" / "results").resolve()
    candidate = (repository_root / "evals" / pure).resolve()
    try:
        candidate.relative_to(result_root)
    except ValueError as error:
        raise HistoryIndexError(f"{label} escapes evals/results") from error
    return value


def _validate_subject(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise HistoryIndexError(f"{label} must be an object")
    candidate = value.get("tag") is None
    expected = CANDIDATE_SUBJECT_KEYS if candidate else RELEASED_SUBJECT_KEYS
    subject = _exact_keys(value, expected, label)
    version = subject.get("version")
    if type(version) is not str or SEMVER_PATTERN.fullmatch(version) is None:
        raise HistoryIndexError(f"{label}.version must be strict SemVer")
    tag = subject.get("tag")
    if candidate:
        if subject.get("releaseState") != "candidate-unreleased":
            raise HistoryIndexError(
                f"{label}.releaseState must be candidate-unreleased for a null tag"
            )
    elif tag != f"v{version}":
        raise HistoryIndexError(f"{label}.tag must match its version")
    for field in ("commit", "tree"):
        oid = subject.get(field)
        if type(oid) is not str or OID_PATTERN.fullmatch(oid) is None:
            raise HistoryIndexError(f"{label}.{field} must be a lowercase Git OID")
    return subject


def load_history_index(
    path: Path = HISTORY_INDEX_PATH,
    *,
    expected_sha256: str | None = HISTORY_INDEX_SHA256,
) -> dict[str, Any]:
    """Load one byte-protected, strictly shaped routing-history index."""
    try:
        file_stat = path.lstat()
    except OSError as error:
        raise HistoryIndexError(f"cannot inspect routing history: {error}") from error
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise HistoryIndexError("routing history must be one regular non-symlink file")
    if file_stat.st_size > MAX_HISTORY_INDEX_BYTES:
        raise HistoryIndexError("routing history exceeds its byte limit")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise HistoryIndexError(f"cannot read routing history: {error}") from error
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise HistoryIndexError(
            "routing history digest drifted; deletion, reassignment, or non-append edit detected"
        )
    try:
        document = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except UnicodeDecodeError as error:
        raise HistoryIndexError("routing history must be strict UTF-8") from error
    except json.JSONDecodeError as error:
        raise HistoryIndexError(f"routing history is invalid JSON: {error}") from error
    root = _exact_keys(document, ROOT_KEYS, "routing history")
    if root.get("schemaVersion") != "1":
        raise HistoryIndexError("routing history schemaVersion must be '1'")
    if root.get("kind") != "routing-history-index":
        raise HistoryIndexError("routing history kind must be routing-history-index")
    schema_digests = _exact_keys(
        root.get("schemaDigests"), SCHEMA_DIGEST_KEYS, "routing history.schemaDigests"
    )
    for key, value in schema_digests.items():
        _require_sha256(value, f"routing history.schemaDigests.{key}")
    entries = root.get("entries")
    if type(entries) is not list or not entries:
        raise HistoryIndexError("routing history.entries must be a non-empty array")
    seen_keys: set[str] = set()
    seen_paths: set[str] = set()
    seen_run_ids: set[str] = set()
    repository_root = path.parent.parent
    for index, raw_entry in enumerate(entries):
        label = f"routing history.entries[{index}]"
        entry = _exact_keys(raw_entry, ENTRY_KEYS, label)
        key = _require_id(entry.get("key"), f"{label}.key", ID_PATTERN)
        group = _require_id(entry.get("group"), f"{label}.group", ID_PATTERN)
        result_path = _validate_result_path(
            entry.get("path"), f"{label}.path", repository_root
        )
        run_id = _require_id(entry.get("runId"), f"{label}.runId", RUN_ID_PATTERN)
        response_digest = entry.get("responseSchemaSha256")
        if response_digest is not None:
            _require_sha256(response_digest, f"{label}.responseSchemaSha256")
        elif not run_id.endswith("-unavailable"):
            raise HistoryIndexError(
                f"{label}.responseSchemaSha256 may be null only for unavailable runs"
            )
        _require_sha256(entry.get("outcomeSha256"), f"{label}.outcomeSha256")
        _validate_subject(entry.get("subject"), f"{label}.subject")
        if type(entry.get("terminalOnly")) is not bool:
            raise HistoryIndexError(f"{label}.terminalOnly must be boolean")
        for value, seen, field in (
            (key, seen_keys, "key"),
            (result_path, seen_paths, "path"),
            (run_id, seen_run_ids, "runId"),
        ):
            if value in seen:
                raise HistoryIndexError(f"{label}.{field} duplicates {value!r}")
            seen.add(value)
        if group == "v0.7.8-candidate" and entry["subject"].get("tag") is not None:
            raise HistoryIndexError(f"{label} candidate group requires a null-tag subject")
    return root


def validate_history_index(root: Path, failures: list[str]) -> None:
    """Append a stable domain failure when a repository history index drifts."""
    try:
        load_history_index(root / HISTORY_INDEX_RELATIVE_PATH)
    except HistoryIndexError as error:
        failures.append(f"{HISTORY_INDEX_RELATIVE_PATH}: {error}")


HISTORY_INDEX = load_history_index()
_SCHEMA_DIGESTS = HISTORY_INDEX["schemaDigests"]
FAILED_HOST_RESPONSE_SCHEMA_SHA256 = _SCHEMA_DIGESTS["failedHostResponseV1"]
V1_HOST_RESPONSE_SCHEMA_SHA256 = _SCHEMA_DIGESTS["hostResponseV1"]
CURRENT_HOST_RESPONSE_SCHEMA_SHA256 = _SCHEMA_DIGESTS["hostResponseV2"]
CURRENT_HOST_RESPONSE_SCHEMA_V3_SHA256 = _SCHEMA_DIGESTS["hostResponseV3"]

_ENTRIES = tuple(HISTORY_INDEX["entries"])
_ENTRIES_BY_KEY = {entry["key"]: entry for entry in _ENTRIES}


def _entry(key: str) -> dict[str, Any]:
    return _ENTRIES_BY_KEY[key]


RECOVERY_RESULT_PATH = _entry("recovery-1")["path"]
RECOVERY2_RESULT_PATH = _entry("recovery-2")["path"]
RECOVERY3_RESULT_PATH = _entry("recovery-3")["path"]
CANDIDATE_RESULT_PATH = _entry("candidate-1")["path"]
CANDIDATE2_RESULT_PATH = _entry("candidate-2")["path"]
CANDIDATE3_RESULT_PATH = _entry("candidate-3")["path"]
CANDIDATE4_RESULT_PATH = _entry("candidate-4")["path"]
V080_CODEX_RESULT_PATH = _entry("v0-8-0-codex")["path"]
V080_CLAUDE_RESULT_PATH = _entry("v0-8-0-claude-unavailable")["path"]
V080_RESULT_PATHS = (V080_CODEX_RESULT_PATH, V080_CLAUDE_RESULT_PATH)
HISTORICAL_RESULT_PATHS = tuple(
    entry["path"] for entry in _ENTRIES if entry["group"] == "v0.7.7"
)
REQUIRED_RESULT_PATHS = tuple(entry["path"] for entry in _ENTRIES)
OPTIONAL_RESULT_PATHS: tuple[str, ...] = ()
SUPPORTED_RESULT_PATHS = REQUIRED_RESULT_PATHS + OPTIONAL_RESULT_PATHS

INITIAL_CODEX_RUN_ID = _entry("initial-codex")["runId"]
CLAUDE_UNAVAILABLE_RUN_ID = _entry("initial-claude-unavailable")["runId"]
RECOVERY_CODEX_RUN_ID = _entry("recovery-1")["runId"]
RECOVERY2_CODEX_RUN_ID = _entry("recovery-2")["runId"]
RECOVERY3_CODEX_RUN_ID = _entry("recovery-3")["runId"]
CANDIDATE_CODEX_RUN_ID = _entry("candidate-1")["runId"]
CANDIDATE2_CODEX_RUN_ID = _entry("candidate-2")["runId"]
CANDIDATE3_CODEX_RUN_ID = _entry("candidate-3")["runId"]
CANDIDATE4_CODEX_RUN_ID = _entry("candidate-4")["runId"]
V080_CODEX_RUN_ID = _entry("v0-8-0-codex")["runId"]
V080_CLAUDE_UNAVAILABLE_RUN_ID = _entry("v0-8-0-claude-unavailable")["runId"]

EXPECTED_RESULT_BINDINGS = {
    entry["path"]: (entry["runId"], entry["responseSchemaSha256"])
    for entry in _ENTRIES
}
EXPECTED_RESULT_SUBJECTS = {
    entry["path"]: dict(entry["subject"]) for entry in _ENTRIES
}
PRESERVED_OUTCOME_SHA256 = {
    entry["runId"]: entry["outcomeSha256"] for entry in _ENTRIES
}
INITIAL_CODEX_OUTCOME_SHA256 = PRESERVED_OUTCOME_SHA256[INITIAL_CODEX_RUN_ID]
TERMINAL_ONLY_RESULT_PATHS = frozenset(
    entry["path"] for entry in _ENTRIES if entry["terminalOnly"]
)

RELEASED_V077_SUBJECT = dict(_entry("initial-codex")["subject"])
CANDIDATE_V078_SUBJECT = dict(_entry("candidate-1")["subject"])
CANDIDATE2_V078_SUBJECT = dict(_entry("candidate-2")["subject"])
CANDIDATE3_V078_SUBJECT = dict(_entry("candidate-3")["subject"])
CANDIDATE4_V078_SUBJECT = dict(_entry("candidate-4")["subject"])
RELEASED_V080_SUBJECT = dict(_entry("v0-8-0-codex")["subject"])
CANDIDATE_COMMIT = CANDIDATE_V078_SUBJECT["commit"]
CANDIDATE_TREE = CANDIDATE_V078_SUBJECT["tree"]
CANDIDATE2_COMMIT = CANDIDATE2_V078_SUBJECT["commit"]
CANDIDATE2_TREE = CANDIDATE2_V078_SUBJECT["tree"]
CANDIDATE3_COMMIT = CANDIDATE3_V078_SUBJECT["commit"]
CANDIDATE3_TREE = CANDIDATE3_V078_SUBJECT["tree"]
CANDIDATE4_COMMIT = CANDIDATE4_V078_SUBJECT["commit"]
CANDIDATE4_TREE = CANDIDATE4_V078_SUBJECT["tree"]
