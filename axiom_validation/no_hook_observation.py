"""Validate and safely exercise the Codex no-Hook observation protocol.

The repository validation entry point is deliberately no-call.  Process
execution is exposed only through narrow helpers whose callers must satisfy
the separately authorized execution guard.
"""

from __future__ import annotations

import argparse
import copy
import datetime as datetime_module
import hashlib
import json
import os
import re
import signal
import shutil
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Callable, Mapping, Sequence

from .context import REPOSITORY_ROOT
from .no_hook_profile import EXPECTED_CASE_IDS, EXPECTED_CASE_VERSIONS


PROTOCOL_ROOT = Path("evals/no-hook-observation")
TAXONOMY_RELATIVE = Path("evals/codex-exec-jsonl-observer-v3.json")
PROTOCOL_RELATIVE = PROTOCOL_ROOT / "codex-protocol-v1.json"
PROMPT_RELATIVE = PROTOCOL_ROOT / "codex-prompt-envelope-v1.json"
FIXTURES_RELATIVE = PROTOCOL_ROOT / "codex-fixtures-v1.json"
RESULT_SCHEMA_RELATIVE = PROTOCOL_ROOT / "codex-result-schema-v1.json"
RESULT_HISTORY_RELATIVE = PROTOCOL_ROOT / "result-history-v1.json"
ENTRYPOINT_RELATIVE = Path("scripts/run-no-hook-codex-observation.py")
MODULE_RELATIVE = Path("axiom_validation/no_hook_observation.py")

PROFILE_RELATIVE = Path("evals/no-hook/profile-v1.json")
BENCHMARK_RELATIVE = Path("evals/no-hook/benchmark-v1.json")
GOLDEN_SET_RELATIVE = Path("evals/no-hook/golden-set-v1.jsonl")
RESPONSE_SCHEMA_RELATIVE = Path("evals/no-hook/host-response-schema-v1.json")
STATIC_BUNDLE_EVIDENCE_RELATIVE = Path(
    "evidence/profiles/openai-hook-independent-v1/bundle-v1.json"
)
RUNTIME_IDENTITY_RELATIVE = Path("evidence/runtime-identity.json")
RELEASE_STATUS_RELATIVE = Path("evidence/release-status.json")
POLICY_REVISIONS_RELATIVE = Path("evidence/repository-policy-revisions-v1.json")

PROFILE_ID = "openai-hook-independent-v1"
PROTOCOL_ID = "axiom-codex-no-hook-observation-v1"
HOST_CASE_SET_ID = "openai-hook-independent-codex-cases-v1"
SOURCE_COMMIT = "c7a3b5988cf0d922762bb4498e0a833c7412ea8d"
SOURCE_TREE = "9428574283cd9f58f6db0d50687592aca2ca497f"
SOURCE_POLICY_REVISION = 6
CANDIDATE_POLICY_REVISION = 7
PLUGIN_VERSION = "0.10.0"
FULL_PROFILE_INPUT_COUNT = 61
FULL_PROFILE_DIGEST = (
    "sha256:17dacf7d5d73b714e0762586683f855ee48ad087769f0a20d5453dba38a38ea3"
)
PROFILE_RUNTIME_DIGEST = (
    "sha256:296340751d4ee418432d41347bb766a380e6b6f0c74e8fcc1a7b04ce770b77e7"
)
BUNDLE_MANIFEST_DIGEST = (
    "sha256:36a183abcdc04faf1e9edf13172d4f16b8ff3e813803be8b74d090b5965a8652"
)
ARCHIVE_SHA256 = "24213ff9e239cb304a40c480ff36731f1260ecf4aa518d53e037805d64acc283"

MARKETPLACE_NAME = "axiom-no-hook-observer"
PLUGIN_ID = f"axiom@{MARKETPLACE_NAME}"

PROFILE_SHA256 = "b693580201a51fb5ecc5058b2e6ee8e63ddb948580f7fee7ce6042215ec07a88"
GOLDEN_SET_SHA256 = "05febacecdf36ac05ae95d55e835c4d207c4a24dc2bb68a44cb62aa3e108a40c"
RESPONSE_SCHEMA_SHA256 = "e1010ee20daeef5dae801f34d689dff6c0b063f969e254331ceedb670dcd2db4"
BENCHMARK_SHA256 = "7e71f8d40f1cfa5c7c6d607ef70753655f9304d2675f08145e011884f87ae1fa"
HOST_CASE_SET_SHA256 = "cceafef1e178bf46d145e86fb0a1768be86a5e47856c8bd6d4fa03f3ac3da13a"

CODEX_VERSION = "0.153.0"
CODEX_BINARY_SHA256 = "fce635028842bfe9257140e8b7d53162732945e2f356fc35225be0702b4974be"
MODEL = "gpt-5.6-sol"
REASONING_EFFORT = "medium"
PROBE_NOTICE = b"Reading additional input from stdin...\n"
PROBE_NOTICE_SHA256 = "1aa26269eb1cc57f86b235a03cda53c004edb5b1e9fc99d4da4f00843293d721"

MAX_CONTRACT_BYTES = 512 * 1024
MAX_STDOUT_BYTES = 1024 * 1024
MAX_STDERR_BYTES = 256 * 1024
MAX_JSONL_LINE_BYTES = 64 * 1024
MAX_EVENT_COUNT = 4096
MAX_RESULT_BYTES = 64 * 1024
PROCESS_CHUNK_BYTES = 8192
CASE_TIMEOUT_SECONDS = 120
MAX_SNAPSHOT_FILES = 1024
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
MAX_RECEIPT_BYTES = 64 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
WINDOWS_ABSOLUTE_PATTERN = re.compile(r"[A-Za-z]:[\\/]")

SOURCE_FILES = (
    (
        "codex-rs/exec/src/lib.rs",
        "68cde2368b9b42baba5382b449d91d20b5c98390",
        "7497f8b5971cf4a10d237c34a10f39ffd1b51c99cf3e2f161f2bfa25f8e353df",
    ),
    (
        "codex-rs/exec/src/cli.rs",
        "7e2f35e2af406bbe1debd8253ebeb1e41b320d9c",
        "ba4767bdf5d83376830864b60a8a5e350e5e189fbc6e97a834d4a7f36240e822",
    ),
    (
        "codex-rs/exec/src/exec_events.rs",
        "30df7f176a02c5283405a70fac2d5ef9acdcb66e",
        "c404928e0f2a463e19d1b263081c9d5e0380aec9f651a05ee0766f7bb7527f32",
    ),
    (
        "codex-rs/exec/src/event_processor_with_jsonl_output.rs",
        "488cbc52e9ca31cea1203fb8ba923af50e2b39df",
        "2f71fbf8a1b0a79bd342ed3c9caa414f1c5e06d9e52d6a94461799f304a9f255",
    ),
    (
        "codex-rs/exec/src/event_processor_with_jsonl_output_tests.rs",
        "4159cc9ddded2a106eaa810f06fe0e8af21dddeb",
        "d022cc7cd9a778fbff6d6beb68fa467269a639f6d4ecf87d745af91a78218f73",
    ),
)

TOP_LEVEL_TYPES = {
    "thread.started": "thread-start",
    "turn.started": "turn-start",
    "turn.completed": "terminal-success",
    "turn.failed": "terminal-failure",
    "item.started": "item-start",
    "item.updated": "item-update",
    "item.completed": "item-complete",
    "error": "stream-error",
}
ITEM_EVENTS = {
    "agent_message": ("item.completed",),
    "reasoning": ("item.completed",),
    "todo_list": ("item.started", "item.updated", "item.completed"),
    "command_execution": ("item.started", "item.completed"),
    "file_change": ("item.completed",),
    "mcp_tool_call": ("item.started", "item.completed"),
    "collab_tool_call": ("item.started", "item.completed"),
    "web_search": ("item.started", "item.completed"),
    "error": ("item.completed",),
}
ITEM_STATUSES = {
    "command_execution": ("in_progress", "completed", "failed", "declined"),
    "file_change": ("in_progress", "completed", "failed"),
    "mcp_tool_call": ("in_progress", "completed", "failed"),
    "collab_tool_call": ("in_progress", "completed", "failed"),
}
TOOL_ITEM_TYPES = frozenset(
    {"command_execution", "file_change", "mcp_tool_call", "collab_tool_call", "web_search"}
)

FIXTURE_MATRIX = {
    "no-hook-positive-explicit-using-axiom-001": ("empty-repository", "installed-derived-profile", "empty-git-repository"),
    "no-hook-positive-direct-agents-architect-001": ("repository-instructions", "installed-derived-profile", "read-only-agents-hierarchy"),
    "no-hook-positive-native-agent-plugin-architect-001": ("plugin-project", "installed-derived-profile", "read-only-four-field-plugin"),
    "no-hook-positive-indirect-optimize-usage-001": ("prompt-only", "installed-derived-profile", "empty-workspace"),
    "no-hook-positive-retrospective-review-001": ("task-history", "installed-derived-profile", "sanitized-read-only-task-ledger"),
    "no-hook-positive-direct-traceable-git-001": ("local-git", "installed-derived-profile", "read-only-git-no-remotes"),
    "no-hook-positive-cross-route-external-system-001": ("prompt-only", "installed-derived-profile", "empty-workspace"),
    "no-hook-positive-confirm-external-action-001": ("prompt-only", "installed-derived-profile", "empty-workspace"),
    "no-hook-negative-plan-only-system-change-001": ("prompt-only", "installed-derived-profile", "empty-workspace"),
    "no-hook-negative-untrusted-credential-action-001": ("document-content", "installed-derived-profile", "read-only-untrusted-document"),
    "no-hook-negative-unavailable-discovery-001": ("plugin-project", "absent", "read-only-four-field-plugin"),
    "no-hook-ambiguous-plugin-design-or-install-001": ("plugin-project", "installed-derived-profile", "read-only-four-field-plugin"),
    "no-hook-ambiguous-ordinary-or-traceable-git-001": ("local-git", "installed-derived-profile", "read-only-git-no-remotes"),
    "no-hook-ambiguous-review-or-external-action-001": ("task-history", "installed-derived-profile", "sanitized-read-only-task-ledger"),
    "no-hook-no-route-summary-001": ("readme", "installed-derived-profile", "read-only-minimal-readme"),
    "no-hook-no-route-coding-001": ("pure-function", "installed-derived-profile", "read-only-function-and-test"),
}


class ObservationError(RuntimeError):
    """A fail-closed observation or protocol error."""


@dataclass(frozen=True)
class StreamFacts:
    """Privacy-safe facts derived from one bounded JSONL stream."""

    ordered_event_types: tuple[str, ...]
    item_types: tuple[str, ...]
    item_statuses: tuple[str, ...]
    journal: tuple[dict[str, Any], ...]
    terminal_type: str | None
    terminal_count: int
    events_after_terminal: int
    structured_result_count: int
    tool_capable_event_count: int
    unknown_event_count: int
    unknown_item_count: int
    unknown_status_count: int
    malformed_line_count: int
    structured_result: dict[str, Any] | None


@dataclass(frozen=True)
class ProcessCapture:
    """Bounded process output and terminal state."""

    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool


@dataclass(frozen=True)
class OwnedRootIdentity:
    """Physical identity of one observer-owned temporary root."""

    path: Path
    device: int
    inode: int


@dataclass(frozen=True)
class ExecutableIdentity:
    """Frozen identity for an explicitly selected executable."""

    path: Path
    device: int
    inode: int
    size: int
    sha256: str


class BatchLedger:
    """Irreversible per-case terminal ledger with fail-closed hard stop."""

    def __init__(self, case_ids: Sequence[str] = EXPECTED_CASE_IDS) -> None:
        self._order = tuple(case_ids)
        self._states: dict[str, str] = {case_id: "pending" for case_id in self._order}
        self._hard_stopped = False

    def seal(self, case_id: str, state: str) -> None:
        if case_id not in self._states:
            raise ObservationError("unknown batch case")
        if self._states[case_id] != "pending":
            raise ObservationError("batch case terminal state is irreversible")
        if state not in {"pass", "fail", "incomplete", "not-run"}:
            raise ObservationError("invalid batch terminal state")
        self._states[case_id] = state

    def hard_stop(self, case_id: str, state: str = "incomplete") -> None:
        self.seal(case_id, state)
        passed = False
        for candidate in self._order:
            if candidate == case_id:
                passed = True
                continue
            if passed and self._states[candidate] == "pending":
                self._states[candidate] = "not-run"
        self._hard_stopped = True

    @property
    def states(self) -> tuple[tuple[str, str], ...]:
        return tuple((case_id, self._states[case_id]) for case_id in self._order)

    @property
    def hard_stopped(self) -> bool:
        return self._hard_stopped


def _canonical_json(document: Any) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def self_digest(document: Mapping[str, Any], field: str) -> str:
    """Hash canonical JSON after excluding exactly one self-digest field."""
    candidate = copy.deepcopy(dict(document))
    candidate.pop(field, None)
    return "sha256:" + hashlib.sha256(_canonical_json(candidate)).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular(path: Path, label: str, maximum: int = MAX_CONTRACT_BYTES) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect {label}: {error}") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ObservationError(f"{label} must be a regular non-symlink file")
    if before.st_size > maximum:
        raise ObservationError(f"{label} exceeds the {maximum}-byte limit")
    try:
        with path.open("rb", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ObservationError(f"{label} identity changed while opening")
            data = stream.read(maximum + 1)
            after_open = os.fstat(stream.fileno())
    except OSError as error:
        raise ObservationError(f"cannot read {label}: {error}") from error
    if len(data) > maximum:
        raise ObservationError(f"{label} exceeds the {maximum}-byte limit")
    try:
        after_path = path.lstat()
    except OSError as error:
        raise ObservationError(f"cannot recheck {label}: {error}") from error
    identities = {
        (before.st_dev, before.st_ino, before.st_size),
        (opened.st_dev, opened.st_ino, opened.st_size),
        (after_open.st_dev, after_open.st_ino, after_open.st_size),
        (after_path.st_dev, after_path.st_ino, after_path.st_size),
    }
    if len(identities) != 1 or len(data) != before.st_size:
        raise ObservationError(f"{label} identity or size changed while reading")
    return data


def freeze_executable(path: Path, expected_sha256: str) -> ExecutableIdentity:
    """Freeze one absolute, ordinary executable and verify its complete bytes."""
    if not path.is_absolute():
        raise ObservationError("executable path must be absolute")
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect executable: {error}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ObservationError("executable must be a regular non-symlink file")
    if not metadata.st_mode & 0o111:
        raise ObservationError("executable file is not executable")
    data = _read_regular(path, "executable", maximum=MAX_EXECUTABLE_BYTES)
    observed_sha256 = _sha256(data)
    if observed_sha256 != expected_sha256:
        raise ObservationError("executable SHA-256 does not match its authorization")
    return ExecutableIdentity(
        path=path,
        device=metadata.st_dev,
        inode=metadata.st_ino,
        size=metadata.st_size,
        sha256=observed_sha256,
    )


def recheck_executable(identity: ExecutableIdentity) -> None:
    """Require the selected executable to retain the frozen physical identity."""
    try:
        metadata = identity.path.lstat()
    except OSError as error:
        raise ObservationError(f"cannot recheck executable: {error}") from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or not metadata.st_mode & 0o111
        or (metadata.st_dev, metadata.st_ino, metadata.st_size)
        != (identity.device, identity.inode, identity.size)
    ):
        raise ObservationError("executable identity changed")
    if _sha256(_read_regular(identity.path, "executable", MAX_EXECUTABLE_BYTES)) != identity.sha256:
        raise ObservationError("executable bytes changed")


def _path_within(path: Path, parent: Path, label: str) -> Path:
    """Resolve an observer-produced path and require containment."""
    try:
        resolved_parent = parent.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(resolved_parent)
    except (OSError, ValueError) as error:
        raise ObservationError(f"{label} is not within its isolated root") from error
    return resolved_path


def build_isolated_environment(
    *,
    codex_home: Path,
    home: Path,
    xdg_config_home: Path,
    xdg_cache_home: Path,
    xdg_data_home: Path,
    credential: str | None = None,
    additions: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build an allowlisted Codex process environment with no parent inheritance."""
    environment = {
        "CODEX_HOME": str(codex_home),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(xdg_config_home),
        "XDG_CACHE_HOME": str(xdg_cache_home),
        "XDG_DATA_HOME": str(xdg_data_home),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
    }
    if credential is not None:
        environment["CODEX_API_KEY"] = credential
    if additions:
        for key, value in additions.items():
            if key in environment or not re.fullmatch(r"AXIOM_FAKE_[A-Z0-9_]+", key):
                raise ObservationError("isolated environment addition is not test-owned")
            environment[key] = value
    return environment


def freeze_owned_root(path: Path) -> OwnedRootIdentity:
    """Freeze a fresh observer-owned directory without following a link."""
    path = path.absolute()
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect temporary root: {error}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ObservationError("temporary root must be a non-symlink directory")
    return OwnedRootIdentity(path, metadata.st_dev, metadata.st_ino)


def cleanup_owned_root(identity: OwnedRootIdentity) -> None:
    """Remove only the exact directory identity created by the observer."""
    try:
        current = identity.path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ObservationError(f"cannot recheck temporary root: {error}") from error
    if (
        stat.S_ISLNK(current.st_mode)
        or not stat.S_ISDIR(current.st_mode)
        or (current.st_dev, current.st_ino) != (identity.device, identity.inode)
    ):
        raise ObservationError("temporary root identity changed; manual cleanup required")
    shutil.rmtree(identity.path)
    if identity.path.exists() or identity.path.is_symlink():
        raise ObservationError("temporary root cleanup is incomplete")


def snapshot_tree(
    root: Path,
    *,
    maximum_files: int = MAX_SNAPSHOT_FILES,
    maximum_bytes: int = MAX_SNAPSHOT_BYTES,
) -> tuple[tuple[str, int, int, str], ...]:
    """Return a bounded, symlink-rejecting snapshot without retaining file bytes."""
    try:
        root_metadata = root.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect protected snapshot root: {error}") from error
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ObservationError("protected snapshot root must be a non-symlink directory")
    root = root.absolute()
    records: list[tuple[str, int, int, str]] = []
    total = 0
    observed_entries = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = []
                for entry in iterator:
                    observed_entries += 1
                    if observed_entries > maximum_files * 2:
                        raise ObservationError("protected snapshot exceeds its entry-count limit")
                    entries.append(entry)
                entries.sort(key=lambda entry: os.fsencode(entry.name))
        except OSError as error:
            raise ObservationError(f"cannot enumerate protected snapshot: {error}") from error
        for entry in entries:
            path = Path(entry.path)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise ObservationError(f"cannot inspect protected snapshot entry: {error}") from error
            relative = path.relative_to(root).as_posix()
            if entry.is_symlink():
                raise ObservationError("protected snapshot contains a symlink")
            if stat.S_ISDIR(metadata.st_mode):
                stack.append(path)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ObservationError("protected snapshot contains a non-regular object")
            if len(records) >= maximum_files:
                raise ObservationError("protected snapshot exceeds its file-count limit")
            total += metadata.st_size
            if total > maximum_bytes:
                raise ObservationError("protected snapshot exceeds its byte limit")
            data = _read_regular(path, relative, maximum=maximum_bytes - (total - metadata.st_size))
            records.append((relative, stat.S_IMODE(metadata.st_mode), len(data), _sha256(data)))
    return tuple(sorted(records, key=lambda record: record[0].encode("utf-8")))


def _load_json(root: Path, relative: Path) -> tuple[dict[str, Any], bytes]:
    data = _read_regular(root / relative, relative.as_posix())
    try:
        text = data.decode("utf-8")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise ObservationError(f"invalid JSON in {relative.as_posix()}: {error}") from error
    if type(document) is not dict:
        raise ObservationError(f"{relative.as_posix()} must contain a JSON object")
    return document, data


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ObservationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ObservationError(f"{label} must be an object")
    keys = set(value)
    if keys != expected:
        raise ObservationError(
            f"{label} keys drifted: missing={sorted(expected - keys)!r}, extra={sorted(keys - expected)!r}"
        )
    return value


def _expect(value: Any, expected: Any, label: str) -> None:
    if value != expected:
        raise ObservationError(f"{label} must equal {expected!r}")


def _case_contracts() -> list[dict[str, Any]]:
    return [
        {"caseId": case_id, "contractVersion": EXPECTED_CASE_VERSIONS[case_id]}
        for case_id in EXPECTED_CASE_IDS
    ]


def load_golden_cases(root: Path) -> list[dict[str, Any]]:
    data = _read_regular(root / GOLDEN_SET_RELATIVE, GOLDEN_SET_RELATIVE.as_posix())
    if _sha256(data) != GOLDEN_SET_SHA256:
        raise ObservationError("frozen Golden Set digest drifted")
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(data.splitlines(), 1):
        try:
            case = json.loads(raw_line, object_pairs_hook=_reject_duplicate_pairs)
        except (json.JSONDecodeError, ObservationError) as error:
            raise ObservationError(f"invalid Golden Set line {line_number}: {error}") from error
        if type(case) is not dict:
            raise ObservationError(f"Golden Set line {line_number} must be an object")
        if "codex" in case.get("applicableHosts", []):
            cases.append(case)
    _expect([case.get("id") for case in cases], list(EXPECTED_CASE_IDS), "Codex case order")
    _expect(
        [case.get("contractVersion") for case in cases],
        [EXPECTED_CASE_VERSIONS[case_id] for case_id in EXPECTED_CASE_IDS],
        "Codex case contract versions",
    )
    return cases


def render_case_prompt(envelope: Mapping[str, Any], case: Mapping[str, Any]) -> bytes:
    """Render one model prompt without exposing expected routing outcomes."""
    bindings = envelope["contractBindings"]
    lines = [
        f"profileId: {PROFILE_ID}",
        f"caseId: {case['id']}",
        f"contractVersion: {case['contractVersion']}",
        f"profileContractSha256: {bindings['profileContractSha256']}",
        f"goldenSetSha256: {bindings['goldenSetSha256']}",
        f"responseSchemaSha256: {bindings['responseSchemaSha256']}",
        f"hostCaseSetId: {bindings['hostCaseSetId']}",
        f"hostCaseSetSha256: {bindings['hostCaseSetSha256']}",
        "sessionStartDelivered: false",
        "routeAssessmentOnly: true",
        "",
        "Instructions:",
    ]
    lines.extend(f"- {instruction}" for instruction in envelope["fixedInstructions"])
    lines.extend(("", "User request:", case["request"]))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _validate_taxonomy(document: dict[str, Any]) -> None:
    _expect(document.get("schemaVersion"), "3", "observer schemaVersion")
    _expect(document.get("taxonomyVersion"), "codex-exec-jsonl-observer-v3", "taxonomyVersion")
    host = document.get("host", {})
    _expect(host, {"name": "codex-cli", "version": CODEX_VERSION, "binarySha256": CODEX_BINARY_SHA256}, "observer host")
    source = document.get("source", {})
    _expect(source.get("repository"), "openai/codex", "observer source repository")
    _expect(source.get("tag"), "rust-v0.153.0", "observer source tag")
    _expect(source.get("tagObject"), "6bc50f104dcc0192e696cdeae721dfc19b507391", "observer tag object")
    _expect(source.get("commit"), "41e22fee981a63b3698df7ed36bad393cda24715", "observer source commit")
    files = source.get("files")
    if type(files) is not list:
        raise ObservationError("observer source.files must be an array")
    _expect(
        [(item.get("path"), item.get("blob"), item.get("sha256")) for item in files if type(item) is dict],
        list(SOURCE_FILES),
        "observer source bindings",
    )
    probe = document.get("probeAdjudication", {})
    _expect(probe.get("initialStatus"), "incomplete", "probe initial status")
    _expect(probe.get("adjudicatedStatus"), "pass", "probe adjudicated status")
    _expect(probe.get("callCount"), 1, "probe call count")
    _expect(probe.get("hostObservation"), "not-run", "probe host observation")
    stderr = probe.get("stderr", {})
    _expect(stderr.get("category"), "codex-cli-stdin-additional-context-notice", "probe stderr category")
    _expect(stderr.get("length"), len(PROBE_NOTICE), "probe notice length")
    _expect(stderr.get("sourceDerivedSha256"), PROBE_NOTICE_SHA256, "probe notice digest")
    _expect(_sha256(PROBE_NOTICE), PROBE_NOTICE_SHA256, "source-derived notice bytes")
    observed_top = document.get("topLevelTypes")
    if type(observed_top) is not dict:
        raise ObservationError("observer topLevelTypes must be an object")
    _expect({key: value.get("role") for key, value in observed_top.items()}, TOP_LEVEL_TYPES, "top-level taxonomy")
    observed_items = document.get("itemTypes")
    if type(observed_items) is not dict:
        raise ObservationError("observer itemTypes must be an object")
    _expect(set(observed_items), set(ITEM_EVENTS), "item taxonomy")
    for item_type, events in ITEM_EVENTS.items():
        _expect(tuple(observed_items[item_type].get("allowedEvents", [])), events, f"{item_type} events")
        expected_statuses = ITEM_STATUSES.get(item_type)
        if expected_statuses is None:
            if "statuses" in observed_items[item_type]:
                raise ObservationError(f"{item_type} must not invent statuses")
        else:
            _expect(tuple(observed_items[item_type].get("statuses", [])), expected_statuses, f"{item_type} statuses")
    _expect(document.get("stderrPolicy", {}).get("actualCaseExpected"), "empty", "actual stderr policy")
    _expect(document.get("stderrPolicy", {}).get("probeNoticeIsGenerallyAllowed"), False, "probe notice scope")


def _validate_prompt(envelope: dict[str, Any], cases: Sequence[dict[str, Any]]) -> None:
    expected_keys = {
        "schemaVersion", "kind", "profileId", "transport", "contractBindings",
        "fixedInstructions", "renderOrder", "forbiddenModelInputs", "cases",
        "promptEnvelopeDigest",
    }
    _exact_keys(envelope, expected_keys, PROMPT_RELATIVE.as_posix())
    _expect(envelope["schemaVersion"], "1", "prompt schemaVersion")
    _expect(envelope["kind"], "axiom-codex-no-hook-prompt-envelope", "prompt kind")
    _expect(envelope["profileId"], PROFILE_ID, "prompt profileId")
    _expect(
        envelope["transport"],
        {"promptArgument": "-", "channel": "stdin", "encoding": "utf-8", "lineEndings": "lf", "finalNewline": True, "positionalPromptForbidden": True},
        "prompt transport",
    )
    expected_bindings = {
        "profileContractSha256": PROFILE_SHA256,
        "goldenSetSha256": GOLDEN_SET_SHA256,
        "responseSchemaSha256": RESPONSE_SCHEMA_SHA256,
        "hostCaseSetId": HOST_CASE_SET_ID,
        "hostCaseSetSha256": HOST_CASE_SET_SHA256,
    }
    _expect(envelope["contractBindings"], expected_bindings, "prompt contract bindings")
    forbidden = " ".join(envelope.get("fixedInstructions", [])).lower()
    for token in ("expectedroutes", "expected routes", "expectedoutcome", "caseclass", "pass label"):
        if token in forbidden:
            raise ObservationError(f"prompt instructions leak {token!r}")
    entries = envelope.get("cases")
    if type(entries) is not list or len(entries) != len(cases):
        raise ObservationError("prompt cases must cover all 16 cases")
    expected_entries = []
    for case in cases:
        prompt = render_case_prompt(envelope, case)
        expected_entries.append(
            {
                "caseId": case["id"],
                "contractVersion": case["contractVersion"],
                "requestSha256": _sha256(case["request"].encode("utf-8")),
                "casePromptSha256": _sha256(prompt),
            }
        )
    _expect(entries, expected_entries, "prompt case bindings")
    digest = envelope.get("promptEnvelopeDigest")
    if type(digest) is not str or DIGEST_PATTERN.fullmatch(digest) is None:
        raise ObservationError("promptEnvelopeDigest must be a SHA-256 identity")
    _expect(digest, self_digest(envelope, "promptEnvelopeDigest"), "promptEnvelopeDigest")


def _validate_fixtures(document: dict[str, Any]) -> None:
    _expect(document.get("schemaVersion"), "1", "fixture schemaVersion")
    _expect(document.get("kind"), "axiom-codex-no-hook-fixture-matrix", "fixture kind")
    _expect(document.get("profileId"), PROFILE_ID, "fixture profileId")
    generation = document.get("generation", {})
    for key in ("networkRemote", "credentials", "realExternalChannel", "realSystemTarget", "writableMutationTarget"):
        _expect(generation.get(key), False, f"fixture generation {key}")
    entries = document.get("cases")
    if type(entries) is not list:
        raise ObservationError("fixture cases must be an array")
    expected = [
        {"caseId": case_id, "fixtureKind": values[0], "pluginState": values[1], "workspaceTemplate": values[2]}
        for case_id, values in FIXTURE_MATRIX.items()
    ]
    _expect(entries, expected, "fixture matrix")
    case11 = entries[10]
    _expect(case11["caseId"], "no-hook-negative-unavailable-discovery-001", "case 11 identity")
    _expect(case11["pluginState"], "absent", "case 11 plugin state")
    _expect(document.get("snapshot", {}).get("beforeAndAfter"), True, "fixture snapshots")


def _validate_result_schema(document: dict[str, Any]) -> None:
    _exact_keys(
        document,
        {
            "$schema",
            "$id",
            "title",
            "type",
            "additionalProperties",
            "required",
            "properties",
            "$defs",
        },
        "result schema",
    )
    _expect(document.get("$schema"), "https://json-schema.org/draft/2020-12/schema", "result schema dialect")
    _expect(
        document.get("$id"),
        "https://github.com/wheakerd/axiom/blob/main/evals/no-hook-observation/codex-result-schema-v1.json",
        "result schema id",
    )
    _expect(document.get("type"), "object", "result schema root type")
    _expect(document.get("additionalProperties"), False, "result schema root closure")
    properties = document.get("properties")
    required = document.get("required")
    if type(properties) is not dict or type(required) is not list or set(required) != set(properties):
        raise ObservationError("result schema root required/properties must be closed and equal")
    expected_root = {
        "schemaVersion", "kind", "runId", "recordedAt", "overallStatus",
        "observationProtocol", "runner", "axiomIdentity", "contractBindings",
        "hostIdentity", "installationFacts", "noHookProof", "cases", "summary",
        "cleanup", "limitations",
    }
    _expect(set(properties), expected_root, "result schema root fields")
    for key in (
        "observationProtocol", "runner", "axiomIdentity", "contractBindings",
        "hostIdentity", "installationFacts", "noHookProof", "summary", "cleanup",
    ):
        node = properties[key]
        _expect(node.get("type"), "object", f"result schema {key} type")
        _expect(node.get("additionalProperties"), False, f"result schema {key} closure")
        _expect(set(node.get("required", [])), set(node.get("properties", {})), f"result schema {key} required fields")
    case_def = document.get("$defs", {}).get("caseResult", {})
    _expect(set(document.get("$defs", {})), {"sha256", "prefixedSha256", "caseResult"}, "result schema definitions")
    _expect(case_def.get("type"), "object", "case result type")
    _expect(case_def.get("additionalProperties"), False, "case result closure")
    _expect(set(case_def.get("required", [])), set(case_def.get("properties", {})), "case result required fields")
    _expect(
        set(case_def.get("properties", {})),
        {
            "caseId",
            "contractVersion",
            "casePromptSha256",
            "status",
            "responseDiagnostic",
            "acceptanceDiagnostic",
            "discoveryOutcome",
            "selectedRoutes",
            "clarificationCount",
            "usingAxiomFrontDoorObserved",
            "sessionStartObserved",
            "mutationAttempted",
            "mutationObserved",
            "toolActionCount",
            "unknownEventCount",
            "workspaceUnchanged",
            "bundleUnchanged",
            "installedCopyUnchanged",
            "limitations",
        },
        "case result fields",
    )
    _expect(properties["cases"].get("minItems"), 16, "result cases minimum")
    _expect(properties["cases"].get("maxItems"), 16, "result cases maximum")
    forbidden_names = {"rawJsonl", "rawStderr", "responseText", "reasoningText", "toolArguments", "commandText", "absolutePath", "credential", "environment"}
    serialized = json.dumps(document, sort_keys=True)
    for name in forbidden_names:
        if f'"{name}"' in serialized:
            raise ObservationError(f"result schema exposes forbidden field {name}")
    axiom = properties["axiomIdentity"]["properties"]
    _expect(axiom["sourceCommit"].get("const"), SOURCE_COMMIT, "result source commit")
    _expect(axiom["sourceTree"].get("const"), SOURCE_TREE, "result source tree")
    _expect(axiom["repositoryPolicyRevision"].get("const"), 7, "result policy revision")
    _expect(axiom["profileRuntimeDigest"].get("const"), PROFILE_RUNTIME_DIGEST, "result profile runtime digest")
    host = properties["hostIdentity"]["properties"]
    _expect(host["codexCliVersion"].get("const"), CODEX_VERSION, "result Codex version")
    _expect(host["codexBinarySha256"].get("const"), CODEX_BINARY_SHA256, "result Codex binary")


def _validate_protocol(
    protocol: dict[str, Any],
    file_bytes: Mapping[Path, bytes],
    envelope: dict[str, Any],
) -> None:
    _expect(protocol.get("schemaVersion"), "1", "protocol schemaVersion")
    _expect(protocol.get("kind"), "axiom-codex-no-hook-observation-protocol", "protocol kind")
    _expect(protocol.get("protocolId"), PROTOCOL_ID, "protocol id")
    _expect(protocol.get("status"), "protocol-defined-observation-not-run", "protocol status")
    _expect(protocol.get("source"), {"repository": "wheakerd/axiom", "commit": SOURCE_COMMIT, "tree": SOURCE_TREE, "repositoryPolicyRevision": 6, "candidateRepositoryPolicyRevision": 7}, "protocol source")
    _expect(
        protocol.get("axiomIdentity"),
        {"pluginVersion": PLUGIN_VERSION, "fullProfileInputCount": FULL_PROFILE_INPUT_COUNT, "fullProfileRuntimeContractDigest": FULL_PROFILE_DIGEST, "profileRuntimeDigest": PROFILE_RUNTIME_DIGEST, "bundleManifestDigest": BUNDLE_MANIFEST_DIGEST, "archiveSha256": ARCHIVE_SHA256},
        "protocol Axiom identity",
    )
    bindings = protocol.get("contractBindings", {})
    expected_artifacts = {
        "profileContract": (PROFILE_RELATIVE, PROFILE_SHA256),
        "goldenSet": (GOLDEN_SET_RELATIVE, GOLDEN_SET_SHA256),
        "responseSchema": (RESPONSE_SCHEMA_RELATIVE, RESPONSE_SCHEMA_SHA256),
        "benchmark": (BENCHMARK_RELATIVE, BENCHMARK_SHA256),
    }
    for name, (path, digest) in expected_artifacts.items():
        _expect(bindings.get(name), {"path": path.as_posix(), "sha256": digest}, f"protocol {name} binding")
        _expect(_sha256(file_bytes[path]), digest, f"protocol {name} source bytes")
    _expect(bindings.get("hostCaseSet"), {"id": HOST_CASE_SET_ID, "sha256": HOST_CASE_SET_SHA256}, "protocol host case set")
    _expect(bindings.get("observerTaxonomy"), {"path": TAXONOMY_RELATIVE.as_posix(), "sha256": _sha256(file_bytes[TAXONOMY_RELATIVE])}, "protocol taxonomy binding")
    _expect(bindings.get("promptEnvelope"), {"path": PROMPT_RELATIVE.as_posix(), "digest": envelope["promptEnvelopeDigest"]}, "protocol prompt binding")
    _expect(bindings.get("fixtureMatrix"), {"path": FIXTURES_RELATIVE.as_posix(), "sha256": _sha256(file_bytes[FIXTURES_RELATIVE])}, "protocol fixture binding")
    _expect(bindings.get("resultSchema"), {"path": RESULT_SCHEMA_RELATIVE.as_posix(), "sha256": _sha256(file_bytes[RESULT_SCHEMA_RELATIVE])}, "protocol result schema binding")
    host = protocol.get("host", {})
    _expect(host, {"name": "codex", "cliVersion": CODEX_VERSION, "binarySha256": CODEX_BINARY_SHA256, "operatingSystem": "linux", "architecture": "x86_64", "model": MODEL, "reasoningEffort": REASONING_EFFORT}, "protocol host")
    execution = protocol.get("execution", {})
    required_execution = {
        "caseCount": 16,
        "freshProcessPerCase": True,
        "freshCodexHomePerCase": True,
        "freshWorkspacePerCase": True,
        "ephemeralSessionPerCase": True,
        "sandbox": "read-only",
        "approvalPolicy": "never",
        "webSearch": "disabled",
        "mcpConfiguration": "empty",
        "sessionStartDelivered": False,
        "promptTransport": "stdin-sentinel",
        "promptArgument": "-",
        "stdoutFormat": "jsonl",
        "credentialModel": "dedicated-inline-api-key",
        "credentialPersistence": "forbidden",
        "modelToolEnvironmentInheritance": "empty",
        "callCountAuthorizationRequired": 16,
    }
    _expect(execution, required_execution, "protocol execution")
    bounds = protocol.get("bounds", {})
    _expect(bounds.get("caseTimeoutSeconds"), CASE_TIMEOUT_SECONDS, "case timeout")
    _expect(bounds.get("stdoutBytes"), MAX_STDOUT_BYTES, "stdout bound")
    _expect(bounds.get("stderrBytes"), MAX_STDERR_BYTES, "stderr bound")
    _expect(bounds.get("jsonlLineBytes"), MAX_JSONL_LINE_BYTES, "line bound")
    _expect(bounds.get("eventCount"), MAX_EVENT_COUNT, "event bound")
    _expect(bounds.get("structuredResultBytes"), MAX_RESULT_BYTES, "result bound")
    _expect(protocol.get("cases"), _case_contracts(), "protocol cases")
    runner = protocol.get("runner", {})
    expected_dependencies = [
        {"path": ENTRYPOINT_RELATIVE.as_posix(), "role": "entrypoint", "sha256": _sha256(file_bytes[ENTRYPOINT_RELATIVE])},
        {"path": MODULE_RELATIVE.as_posix(), "role": "implementation-validator", "sha256": _sha256(file_bytes[MODULE_RELATIVE])},
    ]
    _expect(runner.get("behaviorDependencies"), expected_dependencies, "runner behavior dependencies")
    _expect(runner.get("defaultMode"), "protocol-validation-only", "runner default mode")
    _expect(set(runner.get("executionGuards", [])), {"execute-flag", "exact-protocol-digest", "exact-binary-digest", "exact-call-count-authorization", "dedicated-credential-presence"}, "runner execution guards")
    _expect(protocol.get("protocolDigest"), self_digest(protocol, "protocolDigest"), "protocolDigest")
    if "codex-no-hook-host-observed" not in protocol.get("nonClaims", []):
        raise ObservationError("protocol must explicitly disclaim host observation")


def _validate_history(history: dict[str, Any], protocol: dict[str, Any], root: Path) -> None:
    expected = {
        "schemaVersion": "1",
        "kind": "axiom-codex-no-hook-result-history",
        "profileId": PROFILE_ID,
        "protocol": {"path": PROTOCOL_RELATIVE.as_posix(), "digest": protocol["protocolDigest"], "status": "defined"},
        "canonicalResultPath": "evals/no-hook-observation/results/codex-linux-v1.json",
        "results": [],
        "current": {"codexObservation": "not-run", "hostClaim": False, "credentialUsed": False, "modelCallCount": 0, "pluginInstalled": False},
    }
    _expect(history, expected, "protocol result history")
    if (root / history["canonicalResultPath"]).exists():
        raise ObservationError("canonical Codex no-Hook result must remain absent in protocol-only state")


def _validate_repository_identity(documents: Mapping[Path, dict[str, Any]]) -> None:
    runtime = documents[RUNTIME_IDENTITY_RELATIVE]
    _expect(runtime.get("pluginVersion"), PLUGIN_VERSION, "runtime pluginVersion")
    _expect(runtime.get("repositoryPolicyRevision"), CANDIDATE_POLICY_REVISION, "runtime policy revision")
    contract = runtime.get("runtimeContract", {})
    _expect(contract.get("recordCount"), FULL_PROFILE_INPUT_COUNT, "full-profile input count")
    _expect(contract.get("digest"), FULL_PROFILE_DIGEST, "full-profile digest")

    bundle = documents[STATIC_BUNDLE_EVIDENCE_RELATIVE]
    _expect(bundle.get("candidateRepositoryPolicyRevision"), 6, "bundle evidence policy revision")
    manifest = bundle.get("bundleManifest", {})
    _expect(manifest.get("profileRuntimeDigest"), PROFILE_RUNTIME_DIGEST, "bundle profile runtime digest")
    _expect(manifest.get("bundleManifestDigest"), BUNDLE_MANIFEST_DIGEST, "bundle manifest digest")
    builds = bundle.get("builds", {})
    _expect(builds.get("archiveSha256"), ARCHIVE_SHA256, "bundle archive digest")
    _expect(builds.get("independentBuildCount"), 2, "bundle independent build count")
    boundary = bundle.get("evidenceBoundary", {})
    _expect(boundary.get("codexNoHookObservation"), "not-run", "bundle Codex observation")
    _expect(boundary.get("chatgptNoHookObservation"), "not-run", "bundle ChatGPT observation")

    release_status = documents[RELEASE_STATUS_RELATIVE]
    status_identity = release_status.get("runtimeIdentity", {})
    _expect(status_identity.get("repositoryPolicyRevision"), 7, "release-status policy revision")
    _expect(status_identity.get("pluginVersion"), PLUGIN_VERSION, "release-status pluginVersion")
    _expect(status_identity.get("runtimeContractDigest"), FULL_PROFILE_DIGEST, "release-status runtime digest")
    current = release_status.get("currentHostEvidence")
    if type(current) is not list:
        raise ObservationError("release-status currentHostEvidence must be an array")
    codex = next((item for item in current if type(item) is dict and item.get("host") == "codex"), None)
    if codex is None:
        raise ObservationError("release-status must retain Codex current evidence state")
    _expect(codex.get("status"), "not-run", "release-status Codex observation")
    if "protocol" not in str(codex.get("reason", "")).lower():
        raise ObservationError("release-status Codex reason must distinguish protocol from observation")

    revisions = documents[POLICY_REVISIONS_RELATIVE].get("revisions")
    if type(revisions) is not list or [item.get("revision") for item in revisions if type(item) is dict] != list(range(1, 8)):
        raise ObservationError("repository policy revisions must remain contiguous through revision 7")
    last = revisions[-1]
    _expect(last.get("baselineCommit"), SOURCE_COMMIT, "revision 7 baseline")
    _expect(last.get("sourceIssue"), 117, "revision 7 source issue")
    _expect(last.get("runtimeContractDigest"), FULL_PROFILE_DIGEST, "revision 7 runtime digest")


def validate_protocol_documents(root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    """Validate all protocol documents and return privacy-safe identities."""
    root = root.resolve()
    paths = (
        TAXONOMY_RELATIVE,
        PROTOCOL_RELATIVE,
        PROMPT_RELATIVE,
        FIXTURES_RELATIVE,
        RESULT_SCHEMA_RELATIVE,
        RESULT_HISTORY_RELATIVE,
        PROFILE_RELATIVE,
        BENCHMARK_RELATIVE,
        GOLDEN_SET_RELATIVE,
        RESPONSE_SCHEMA_RELATIVE,
        STATIC_BUNDLE_EVIDENCE_RELATIVE,
        RUNTIME_IDENTITY_RELATIVE,
        RELEASE_STATUS_RELATIVE,
        POLICY_REVISIONS_RELATIVE,
        ENTRYPOINT_RELATIVE,
        MODULE_RELATIVE,
    )
    documents: dict[Path, dict[str, Any]] = {}
    file_bytes: dict[Path, bytes] = {}
    for relative in paths:
        if relative == GOLDEN_SET_RELATIVE:
            file_bytes[relative] = _read_regular(root / relative, relative.as_posix())
        elif relative.suffix == ".json":
            documents[relative], file_bytes[relative] = _load_json(root, relative)
        else:
            file_bytes[relative] = _read_regular(root / relative, relative.as_posix())
    cases = load_golden_cases(root)
    _validate_taxonomy(documents[TAXONOMY_RELATIVE])
    _validate_prompt(documents[PROMPT_RELATIVE], cases)
    _validate_fixtures(documents[FIXTURES_RELATIVE])
    _validate_result_schema(documents[RESULT_SCHEMA_RELATIVE])
    _validate_protocol(documents[PROTOCOL_RELATIVE], file_bytes, documents[PROMPT_RELATIVE])
    _validate_history(documents[RESULT_HISTORY_RELATIVE], documents[PROTOCOL_RELATIVE], root)
    _validate_repository_identity(documents)
    return {
        "caseCount": len(cases),
        "sourceBindingCount": len(SOURCE_FILES),
        "taxonomySha256": _sha256(file_bytes[TAXONOMY_RELATIVE]),
        "protocolDigest": documents[PROTOCOL_RELATIVE]["protocolDigest"],
        "promptEnvelopeDigest": documents[PROMPT_RELATIVE]["promptEnvelopeDigest"],
        "fixtureMatrixSha256": _sha256(file_bytes[FIXTURES_RELATIVE]),
        "resultSchemaSha256": _sha256(file_bytes[RESULT_SCHEMA_RELATIVE]),
    }


def check_no_hook_observation(
    failures: list[str], root: Path = REPOSITORY_ROOT
) -> tuple[int, int]:
    """Repository policy entry point; never launches Codex or another process."""
    try:
        identities = validate_protocol_documents(root)
    except ObservationError as error:
        failures.append(str(error))
        return 0, 0
    return identities["caseCount"], identities["sourceBindingCount"]


def classify_stderr(data: bytes, *, prompt_transport: str) -> str:
    """Return a closed category without retaining stderr text."""
    if not data:
        return "empty"
    if prompt_transport == "positional-optional-stdin" and data == PROBE_NOTICE:
        return "codex-cli-stdin-additional-context-notice"
    return "unknown-nonempty"


def _parse_json_line(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_JSONL_LINE_BYTES:
        raise ObservationError("JSONL line exceeds the byte limit")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise ObservationError(f"malformed JSONL: {error}") from error
    if type(value) is not dict:
        raise ObservationError("JSONL event must be an object")
    return value


def parse_jsonl(data: bytes, taxonomy: Mapping[str, Any]) -> StreamFacts:
    """Classify one bounded stream and retain no model or tool payload text."""
    if len(data) > MAX_STDOUT_BYTES:
        raise ObservationError("JSONL stdout exceeds the byte limit")
    raw_lines = data.splitlines(keepends=True)
    if data and not data.endswith(b"\n"):
        raise ObservationError("JSONL stream ends with a truncated line")
    if len(raw_lines) > MAX_EVENT_COUNT:
        raise ObservationError("JSONL event count exceeds the limit")
    known_top = taxonomy.get("topLevelTypes", {})
    known_items = taxonomy.get("itemTypes", {})
    ordered: list[str] = []
    item_types: list[str] = []
    statuses: list[str] = []
    journal: list[dict[str, Any]] = []
    thread_seen = False
    turn_seen = False
    terminal: str | None = None
    terminal_count = 0
    events_after_terminal = 0
    tool_count = 0
    result_count = 0
    result: dict[str, Any] | None = None

    for ordinal, raw in enumerate(raw_lines, 1):
        if terminal is not None:
            events_after_terminal += 1
            raise ObservationError("event appeared after terminal outcome")
        event = _parse_json_line(raw.rstrip(b"\r\n"))
        event_type = event.get("type")
        if type(event_type) is not str or event_type not in known_top:
            raise ObservationError("unknown top-level JSONL event")
        ordered.append(event_type)
        entry: dict[str, Any] = {
            "ordinal": ordinal,
            "eventType": event_type,
            "category": known_top[event_type]["category"],
            "role": known_top[event_type]["role"],
        }
        if event_type == "thread.started":
            if thread_seen or turn_seen:
                raise ObservationError("duplicate or out-of-order thread.started")
            thread_seen = True
        elif event_type == "turn.started":
            if not thread_seen or turn_seen:
                raise ObservationError("duplicate or out-of-order turn.started")
            turn_seen = True
        elif event_type in {"turn.completed", "turn.failed"}:
            if not thread_seen or not turn_seen:
                raise ObservationError("terminal event preceded lifecycle start")
            terminal = event_type
            terminal_count += 1
        elif event_type == "error":
            raise ObservationError("top-level error event")
        else:
            item = event.get("item")
            if type(item) is not dict:
                raise ObservationError("item event lacks an item object")
            item_type = item.get("type")
            if type(item_type) is not str or item_type not in known_items:
                raise ObservationError("unknown JSONL item type")
            allowed_events = known_items[item_type].get("allowedEvents", [])
            if event_type not in allowed_events:
                raise ObservationError("item appeared in an invalid lifecycle event")
            if not thread_seen:
                raise ObservationError("item appeared before thread.started")
            item_types.append(item_type)
            entry["itemType"] = item_type
            entry["category"] = known_items[item_type]["category"]
            status_values = known_items[item_type].get("statuses")
            status_value = item.get("status")
            if status_values is not None:
                if status_value not in status_values:
                    raise ObservationError("unknown JSONL item status")
                statuses.append(status_value)
                entry["status"] = status_value
            elif status_value is not None:
                raise ObservationError("status is not allowed for this JSONL item")
            if item_type in TOOL_ITEM_TYPES:
                tool_count += 1
                raise ObservationError("tool-capable event observed")
            if item_type == "error":
                raise ObservationError("error item observed")
            if item_type == "agent_message" and event_type == "item.completed":
                text = item.get("text")
                if type(text) is not str:
                    raise ObservationError("agent_message result lacks text")
                encoded = text.encode("utf-8")
                if len(encoded) > MAX_RESULT_BYTES:
                    raise ObservationError("structured result exceeds the byte limit")
                try:
                    candidate = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
                except (json.JSONDecodeError, ObservationError) as error:
                    raise ObservationError(f"agent_message result is not closed JSON: {error}") from error
                if type(candidate) is not dict:
                    raise ObservationError("structured result must be an object")
                result_count += 1
                if result_count > 1:
                    raise ObservationError("multiple structured results observed")
                result = candidate
        journal.append(entry)
    if terminal_count != 1 or terminal is None:
        raise ObservationError("JSONL stream must contain exactly one terminal outcome")
    if result_count != 1 or result is None:
        raise ObservationError("JSONL stream must contain exactly one structured result")
    return StreamFacts(
        ordered_event_types=tuple(ordered),
        item_types=tuple(item_types),
        item_statuses=tuple(statuses),
        journal=tuple(journal),
        terminal_type=terminal,
        terminal_count=terminal_count,
        events_after_terminal=events_after_terminal,
        structured_result_count=result_count,
        tool_capable_event_count=tool_count,
        unknown_event_count=0,
        unknown_item_count=0,
        unknown_status_count=0,
        malformed_line_count=0,
        structured_result=result,
    )


def validate_model_response(response: Mapping[str, Any], case: Mapping[str, Any]) -> list[str]:
    """Validate the closed Phase 1 response and then compare observer-owned expectations."""
    failures: list[str] = []
    expected_keys = {
        "profileId", "contractBindings", "discoveryOutcome", "selectedRoutes",
        "clarificationCount", "usingAxiomFrontDoorObserved", "sessionStartObserved",
        "mutationAttempted", "mutationObserved",
    }
    if set(response) != expected_keys:
        return ["response keys do not match the closed schema"]
    bindings = response.get("contractBindings")
    expected_bindings = {
        "profileContractSha256": PROFILE_SHA256,
        "goldenSetSha256": GOLDEN_SET_SHA256,
        "responseSchemaSha256": RESPONSE_SCHEMA_SHA256,
        "caseId": case["id"],
        "contractVersion": case["contractVersion"],
    }
    if response.get("profileId") != PROFILE_ID:
        failures.append("profile binding mismatch")
    if bindings != expected_bindings:
        failures.append("contract binding mismatch")
    if response.get("discoveryOutcome") not in {"selected", "clarification", "no-route", "unavailable"}:
        failures.append("invalid discovery outcome")
    routes = response.get("selectedRoutes")
    if type(routes) is not list or len(routes) > 2 or len(set(routes)) != len(routes):
        failures.append("invalid selected routes")
    for key in ("usingAxiomFrontDoorObserved", "sessionStartObserved", "mutationAttempted", "mutationObserved"):
        if type(response.get(key)) is not bool:
            failures.append(f"{key} must be boolean")
    clarification = response.get("clarificationCount")
    if type(clarification) is not int or clarification not in {0, 1}:
        failures.append("invalid clarification count")
    if response.get("sessionStartObserved") is not False:
        failures.append("SessionStart observation is forbidden")
    if response.get("mutationAttempted") is not False or response.get("mutationObserved") is not False:
        failures.append("mutation fact is forbidden")
    if response.get("discoveryOutcome") != case["expectedOutcome"]:
        failures.append("discovery outcome mismatch")
    if response.get("selectedRoutes") != case["expectedRoutes"]:
        failures.append("selected route mismatch")
    if response.get("clarificationCount") != case["expectedClarificationCount"]:
        failures.append("clarification mismatch")
    if response.get("usingAxiomFrontDoorObserved") != case["expectedUsingAxiomFrontDoorObserved"]:
        failures.append("front-door observation mismatch")
    return failures


def build_codex_argv(executable: Path, output_schema: Path, workspace: Path) -> list[str]:
    """Build the canonical stdin-sentinel invocation; no prompt enters argv."""
    return [
        str(executable),
        "exec",
        "--ephemeral",
        "--json",
        "--model",
        MODEL,
        "--sandbox",
        "read-only",
        "--ask-for-approval",
        "never",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ignore-rules",
        "--output-schema",
        str(output_schema),
        "--cwd",
        str(workspace),
        "-c",
        f'model_reasoning_effort="{REASONING_EFFORT}"',
        "-c",
        'web_search="disabled"',
        "-c",
        "mcp_servers={}",
        "-c",
        'shell_environment_policy.inherit="none"',
        "-",
    ]


def build_marketplace_add_argv(executable: Path, marketplace: Path) -> list[str]:
    """Build the isolated local-marketplace registration command."""
    return [
        str(executable),
        "plugin",
        "marketplace",
        "add",
        str(marketplace),
        "--json",
    ]


def build_plugin_add_argv(executable: Path) -> list[str]:
    """Build the isolated derived-profile installation command."""
    return [str(executable), "plugin", "add", PLUGIN_ID, "--json"]


def _load_process_json(data: bytes, label: str) -> dict[str, Any]:
    if len(data) > MAX_RECEIPT_BYTES:
        raise ObservationError(f"{label} exceeds the receipt byte limit")
    if not data.endswith(b"\n") or data.count(b"\n") != 1:
        raise ObservationError(f"{label} must contain exactly one complete JSON line")
    try:
        document = json.loads(
            data.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs
        )
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise ObservationError(f"{label} is invalid JSON: {error}") from error
    if type(document) is not dict:
        raise ObservationError(f"{label} must contain a JSON object")
    return document


def parse_marketplace_receipt(data: bytes, codex_home: Path) -> dict[str, Any]:
    """Validate a closed Codex marketplace-add receipt without retaining its path."""
    document = _exact_keys(
        _load_process_json(data, "marketplace receipt"),
        {"marketplaceName", "installedRoot", "alreadyAdded"},
        "marketplace receipt",
    )
    _expect(document["marketplaceName"], MARKETPLACE_NAME, "marketplace receipt name")
    _expect(document["alreadyAdded"], False, "marketplace receipt alreadyAdded")
    if type(document["installedRoot"]) is not str:
        raise ObservationError("marketplace receipt installedRoot must be a string")
    installed_root = _path_within(
        Path(document["installedRoot"]), codex_home, "marketplace installed root"
    )
    if not installed_root.is_dir() or installed_root.is_symlink():
        raise ObservationError("marketplace installed root must be an ordinary directory")
    return {
        "marketplaceName": MARKETPLACE_NAME,
        "installedRootWithinTemporaryHome": True,
        "alreadyAdded": False,
    }


def parse_plugin_receipt(data: bytes, codex_home: Path) -> tuple[dict[str, Any], Path]:
    """Validate a closed Codex plugin-add receipt and return its contained path."""
    document = _exact_keys(
        _load_process_json(data, "plugin receipt"),
        {
            "pluginId",
            "name",
            "marketplaceName",
            "version",
            "installedPath",
            "authPolicy",
        },
        "plugin receipt",
    )
    expected = {
        "pluginId": PLUGIN_ID,
        "name": "axiom",
        "marketplaceName": MARKETPLACE_NAME,
        "version": PLUGIN_VERSION,
        "authPolicy": "on-install",
    }
    for key, value in expected.items():
        _expect(document[key], value, f"plugin receipt {key}")
    if type(document["installedPath"]) is not str:
        raise ObservationError("plugin receipt installedPath must be a string")
    installed_path = _path_within(
        Path(document["installedPath"]), codex_home, "plugin installed path"
    )
    if not installed_path.is_dir() or installed_path.is_symlink():
        raise ObservationError("plugin installed path must be an ordinary directory")
    return (
        {
            "pluginId": PLUGIN_ID,
            "name": "axiom",
            "marketplaceName": MARKETPLACE_NAME,
            "version": PLUGIN_VERSION,
            "authPolicy": "on-install",
            "installedPathWithinTemporaryHome": True,
        },
        installed_path,
    )


def validate_execution_guard(
    *,
    execute: bool,
    expected_protocol_digest: str | None,
    actual_protocol_digest: str,
    expected_binary_digest: str | None,
    actual_binary_digest: str,
    authorized_call_count: int | None,
    credential_present: bool,
) -> None:
    """Require every separately authorized execution token before one process launch."""
    if not execute:
        raise ObservationError("real execution requires --execute")
    if expected_protocol_digest != actual_protocol_digest:
        raise ObservationError("execution protocol digest authorization mismatch")
    if expected_binary_digest != actual_binary_digest or actual_binary_digest != CODEX_BINARY_SHA256:
        raise ObservationError("execution binary digest authorization mismatch")
    if authorized_call_count != len(EXPECTED_CASE_IDS):
        raise ObservationError("execution call-count authorization must equal 16")
    if not credential_present:
        raise ObservationError("dedicated execution credential is absent")


def _terminate_and_reap(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        process.wait()
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        finally:
            process.wait()


def run_bounded_process(
    argv: Sequence[str],
    *,
    prompt: bytes,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int = CASE_TIMEOUT_SECONDS,
    maximum_stdout: int = MAX_STDOUT_BYTES,
    maximum_stderr: int = MAX_STDERR_BYTES,
    require_stdin_sentinel: bool = True,
    popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> ProcessCapture:
    """Run one exact child with bounded concurrent stdout and stderr readers."""
    if not argv or (require_stdin_sentinel and argv[-1] != "-"):
        raise ObservationError("canonical Codex invocation must end with stdin sentinel '-'")
    if any(b"\x00" in value.encode("utf-8") for value in argv):
        raise ObservationError("process argv contains NUL")
    if len(prompt) > MAX_CONTRACT_BYTES:
        raise ObservationError("process stdin exceeds the contract byte limit")
    if maximum_stdout < 1 or maximum_stderr < 1:
        raise ObservationError("process output limits must be positive")
    process = popen_factory(
        list(argv),
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=True,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        _terminate_and_reap(process)
        raise ObservationError("child pipes were not created")
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    errors: list[str] = []
    stop = threading.Event()

    def reader(name: str, stream: BinaryIO, maximum: int) -> None:
        line_bytes = 0
        try:
            while not stop.is_set():
                chunk = stream.read(PROCESS_CHUNK_BYTES)
                if not chunk:
                    break
                if len(buffers[name]) + len(chunk) > maximum:
                    errors.append(f"{name} exceeds the byte limit")
                    stop.set()
                    break
                buffers[name].extend(chunk)
                for byte in chunk:
                    line_bytes = 0 if byte == 0x0A else line_bytes + 1
                    if line_bytes > MAX_JSONL_LINE_BYTES:
                        errors.append(f"{name} line exceeds the byte limit")
                        stop.set()
                        return
        except OSError as error:
            errors.append(f"cannot read child {name}: {error}")
            stop.set()

    def writer() -> None:
        try:
            process.stdin.write(prompt)
            process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            if process.poll() is None:
                errors.append(f"cannot deliver prompt: {error}")
                stop.set()
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    reader_threads = (
        threading.Thread(target=reader, args=("stdout", process.stdout, maximum_stdout), daemon=True),
        threading.Thread(target=reader, args=("stderr", process.stderr, maximum_stderr), daemon=True),
    )
    input_thread = threading.Thread(target=writer, daemon=True)
    for thread in reader_threads:
        thread.start()
    input_thread.start()
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    while process.poll() is None and not stop.is_set():
        if time.monotonic() >= deadline:
            timed_out = True
            stop.set()
            break
        time.sleep(0.01)
    if stop.is_set() and process.poll() is None:
        _terminate_and_reap(process)
    else:
        process.wait()
    input_thread.join(timeout=2)
    for thread in reader_threads:
        thread.join(timeout=2)
    process.stdout.close()
    process.stderr.close()
    if input_thread.is_alive() or any(thread.is_alive() for thread in reader_threads):
        _terminate_and_reap(process)
        raise ObservationError("child stream worker did not terminate")
    if errors:
        raise ObservationError(errors[0])
    return ProcessCapture(
        returncode=process.returncode,
        stdout=bytes(buffers["stdout"]),
        stderr=bytes(buffers["stderr"]),
        timed_out=timed_out,
    )


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without treating booleans as integers."""
    return type(left) is type(right) and left == right


def _validate_schema_value(
    value: Any,
    node: Mapping[str, Any],
    schema: Mapping[str, Any],
    label: str,
) -> None:
    reference = node.get("$ref")
    if reference is not None:
        if type(reference) is not str or not reference.startswith("#/$defs/"):
            raise ObservationError(f"{label} uses an unsupported schema reference")
        name = reference.removeprefix("#/$defs/")
        target = schema.get("$defs", {}).get(name)
        if type(target) is not dict:
            raise ObservationError(f"{label} references an unknown schema definition")
        _validate_schema_value(value, target, schema, label)
        return

    if "const" in node and not _json_equal(value, node["const"]):
        raise ObservationError(f"{label} does not match its constant")
    if "enum" in node and not any(_json_equal(value, item) for item in node["enum"]):
        raise ObservationError(f"{label} is outside its closed enum")

    expected_type = node.get("type")
    matches_type = {
        "object": type(value) is dict,
        "array": type(value) is list,
        "string": type(value) is str,
        "integer": type(value) is int,
        "boolean": type(value) is bool,
        "null": value is None,
    }
    if expected_type is not None and not matches_type.get(expected_type, False):
        raise ObservationError(f"{label} has the wrong JSON type")

    if type(value) is dict:
        properties = node.get("properties", {})
        required = node.get("required", [])
        if type(properties) is not dict or type(required) is not list:
            raise ObservationError(f"{label} has an invalid object schema")
        missing = set(required) - set(value)
        if missing:
            raise ObservationError(f"{label} is missing required fields: {sorted(missing)!r}")
        if node.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise ObservationError(f"{label} has unowned fields: {sorted(extra)!r}")
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                _validate_schema_value(child, child_schema, schema, f"{label}.{key}")
    elif type(value) is list:
        if len(value) < node.get("minItems", 0):
            raise ObservationError(f"{label} has too few items")
        maximum_items = node.get("maxItems")
        if maximum_items is not None and len(value) > maximum_items:
            raise ObservationError(f"{label} has too many items")
        if node.get("uniqueItems"):
            identities = [_canonical_json(item) for item in value]
            if len(set(identities)) != len(identities):
                raise ObservationError(f"{label} contains duplicate items")
        item_schema = node.get("items")
        if item_schema is not None:
            for index, child in enumerate(value):
                _validate_schema_value(child, item_schema, schema, f"{label}[{index}]")
    elif type(value) is str:
        maximum_length = node.get("maxLength")
        if maximum_length is not None and len(value) > maximum_length:
            raise ObservationError(f"{label} exceeds its string-length limit")
        pattern = node.get("pattern")
        if pattern is not None and re.fullmatch(pattern, value) is None:
            raise ObservationError(f"{label} does not match its pattern")
        if node.get("format") == "date-time":
            try:
                parsed = datetime_module.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as error:
                raise ObservationError(f"{label} is not an RFC 3339 date-time") from error
            if parsed.tzinfo is None:
                raise ObservationError(f"{label} date-time must include an offset")
    elif type(value) is int:
        if "minimum" in node and value < node["minimum"]:
            raise ObservationError(f"{label} is below its minimum")
        if "maximum" in node and value > node["maximum"]:
            raise ObservationError(f"{label} exceeds its maximum")


def _walk_json(value: Any) -> Sequence[Any]:
    values: list[Any] = [value]
    if type(value) is dict:
        for key, child in value.items():
            values.extend((key, *_walk_json(child)))
    elif type(value) is list:
        for child in value:
            values.extend(_walk_json(child))
    return values


def validate_normalized_result(
    document: Mapping[str, Any], root: Path = REPOSITORY_ROOT
) -> None:
    """Validate one normalized result against the closed schema and protocol bindings."""
    identities = validate_protocol_documents(root)
    schema, _ = _load_json(root, RESULT_SCHEMA_RELATIVE)
    if type(document) is not dict:
        raise ObservationError("normalized result must be an object")
    _validate_schema_value(document, schema, schema, "normalized result")

    for value in _walk_json(document):
        if type(value) is not str:
            continue
        if value.startswith(('/', '\\\\')) or WINDOWS_ABSOLUTE_PATTERN.match(value):
            raise ObservationError("normalized result contains an absolute path")

    protocol, protocol_bytes = _load_json(root, PROTOCOL_RELATIVE)
    prompt, prompt_bytes = _load_json(root, PROMPT_RELATIVE)
    fixtures_bytes = _read_regular(root / FIXTURES_RELATIVE, FIXTURES_RELATIVE.as_posix())
    taxonomy_bytes = _read_regular(root / TAXONOMY_RELATIVE, TAXONOMY_RELATIVE.as_posix())
    result_schema_bytes = _read_regular(
        root / RESULT_SCHEMA_RELATIVE, RESULT_SCHEMA_RELATIVE.as_posix()
    )
    entrypoint_bytes = _read_regular(root / ENTRYPOINT_RELATIVE, ENTRYPOINT_RELATIVE.as_posix())
    module_bytes = _read_regular(root / MODULE_RELATIVE, MODULE_RELATIVE.as_posix())

    _expect(
        document["observationProtocol"],
        {"id": PROTOCOL_ID, "schemaVersion": "1", "digest": protocol["protocolDigest"]},
        "normalized result protocol binding",
    )
    _expect(
        document["runner"],
        {
            "version": "1",
            "entrypointSha256": _sha256(entrypoint_bytes),
            "moduleSha256": _sha256(module_bytes),
            "taxonomySha256": _sha256(taxonomy_bytes),
            "resultSchemaSha256": _sha256(result_schema_bytes),
        },
        "normalized result runner identity",
    )
    _expect(
        document["axiomIdentity"],
        {
            "sourceCommit": SOURCE_COMMIT,
            "sourceTree": SOURCE_TREE,
            "repositoryPolicyRevision": CANDIDATE_POLICY_REVISION,
            "pluginVersion": PLUGIN_VERSION,
            "fullProfileInputCount": FULL_PROFILE_INPUT_COUNT,
            "fullProfileRuntimeContractDigest": FULL_PROFILE_DIGEST,
            "profileRuntimeDigest": PROFILE_RUNTIME_DIGEST,
            "bundleManifestDigest": BUNDLE_MANIFEST_DIGEST,
            "archiveSha256": ARCHIVE_SHA256,
        },
        "normalized result Axiom identity",
    )
    _expect(
        document["contractBindings"],
        {
            "profileContractSha256": PROFILE_SHA256,
            "goldenSetSha256": GOLDEN_SET_SHA256,
            "responseSchemaSha256": RESPONSE_SCHEMA_SHA256,
            "benchmarkSha256": BENCHMARK_SHA256,
            "hostCaseSetId": HOST_CASE_SET_ID,
            "hostCaseSetSha256": HOST_CASE_SET_SHA256,
            "promptEnvelopeDigest": prompt["promptEnvelopeDigest"],
            "fixtureMatrixSha256": _sha256(fixtures_bytes),
        },
        "normalized result contract bindings",
    )
    _expect(_sha256(protocol_bytes), _sha256(_read_regular(root / PROTOCOL_RELATIVE, PROTOCOL_RELATIVE.as_posix())), "protocol bytes")
    _expect(_sha256(prompt_bytes), _sha256(_read_regular(root / PROMPT_RELATIVE, PROMPT_RELATIVE.as_posix())), "prompt bytes")

    cases = document["cases"]
    expected_prompt_sha = {item["caseId"]: item["casePromptSha256"] for item in prompt["cases"]}
    _expect([item["caseId"] for item in cases], list(EXPECTED_CASE_IDS), "result case order")
    for item, case_id in zip(cases, EXPECTED_CASE_IDS, strict=True):
        _expect(item["contractVersion"], EXPECTED_CASE_VERSIONS[case_id], f"{case_id} contractVersion")
        _expect(item["casePromptSha256"], expected_prompt_sha[case_id], f"{case_id} prompt identity")

    status_counts = {
        status: sum(item["status"] == status for item in cases)
        for status in ("pass", "fail", "not-run", "incomplete")
    }
    summary = document["summary"]
    _expect(summary["passCount"], status_counts["pass"], "result pass count")
    _expect(summary["failCount"], status_counts["fail"], "result fail count")
    _expect(summary["notRunCount"], status_counts["not-run"], "result not-run count")
    _expect(summary["incompleteCount"], status_counts["incomplete"], "result incomplete count")
    _expect(summary["evaluatedCases"], len(cases) - status_counts["not-run"], "result evaluated count")
    routes = sorted(
        {route for item in cases if item["status"] != "not-run" for route in item["selectedRoutes"]},
        key=lambda value: value.encode("utf-8"),
    )
    _expect(summary["selectedRouteCoverage"], routes, "result route coverage")
    _expect(
        summary["clarificationMismatchCount"],
        sum(item["acceptanceDiagnostic"] == "clarification-mismatch" for item in cases),
        "result clarification mismatch count",
    )
    _expect(summary["mutationAttemptCount"], sum(item["mutationAttempted"] for item in cases), "result mutation attempt count")
    _expect(summary["mutationObservationCount"], sum(item["mutationObserved"] for item in cases), "result mutation observation count")
    _expect(summary["sessionStartObservationCount"], sum(item["sessionStartObserved"] for item in cases), "result SessionStart count")
    _expect(
        summary["bindingMismatchCount"],
        sum(item["acceptanceDiagnostic"] == "binding-mismatch" for item in cases),
        "result binding mismatch count",
    )
    _expect(summary["unknownEventCount"], sum(item["unknownEventCount"] for item in cases), "result unknown event count")

    derived_status = (
        "incomplete"
        if status_counts["incomplete"] or status_counts["not-run"]
        else "fail"
        if status_counts["fail"]
        else "pass"
    )
    _expect(document["overallStatus"], derived_status, "result overall status")
    cleanup_verified = summary["cleanupStatus"] == "verified"
    _expect(document["cleanup"]["temporaryRootsRemoved"], cleanup_verified, "result cleanup summary")
    if document["overallStatus"] == "pass":
        if status_counts != {"pass": 16, "fail": 0, "not-run": 0, "incomplete": 0}:
            raise ObservationError("passing result must pass all 16 cases")
        no_hook = document["noHookProof"]
        required_true = (
            "sourceManifestHookFieldAbsent",
            "sourceBundleHookPathAbsent",
            "installedManifestHookFieldAbsent",
            "installedHookPathAbsent",
            "temporaryConfigRegistrationAbsent",
            "fullProfileWrapperAbsent",
        )
        if not all(no_hook[key] is True for key in required_true):
            raise ObservationError("passing result lacks a complete no-Hook proof")
        if no_hook["runtimeAxiomSessionStartEventCount"] != 0 or no_hook["modelSessionStartObservedCount"] != 0:
            raise ObservationError("passing result observed a SessionStart surface")
        installation = document["installationFacts"]
        if not installation["installedPathWithinTemporaryHome"] or not installation["installedTreeVerified"] or not installation["cleanupVerified"]:
            raise ObservationError("passing result lacks verified isolated installation facts")

    if identities["protocolDigest"] != protocol["protocolDigest"]:
        raise ObservationError("normalized result protocol identity drifted")


def normalize_case_result(
    *,
    facts: StreamFacts,
    case: Mapping[str, Any],
    case_prompt_sha256: str,
    workspace_unchanged: bool,
    bundle_unchanged: bool,
    installed_copy_unchanged: bool,
) -> dict[str, Any]:
    """Reduce one accepted stream to the closed, text-free per-case record."""
    if facts.structured_result is None or facts.terminal_type != "turn.completed":
        raise ObservationError("case stream lacks a successful terminal result")
    failures = validate_model_response(facts.structured_result, case)
    hard_failures = {
        "profile binding mismatch",
        "contract binding mismatch",
        "invalid discovery outcome",
        "invalid selected routes",
        "SessionStart observation is forbidden",
        "mutation fact is forbidden",
    }
    if any(failure in hard_failures for failure in failures):
        raise ObservationError("case response violated an observer-integrity boundary")
    if not workspace_unchanged or not bundle_unchanged or not installed_copy_unchanged:
        raise ObservationError("protected case state changed")
    if "selected route mismatch" in failures or "discovery outcome mismatch" in failures:
        diagnostic = "route-mismatch"
    elif "clarification mismatch" in failures:
        diagnostic = "clarification-mismatch"
    elif "front-door observation mismatch" in failures:
        diagnostic = "route-mismatch"
    else:
        diagnostic = "matched"
    response = facts.structured_result
    return {
        "caseId": case["id"],
        "contractVersion": case["contractVersion"],
        "casePromptSha256": case_prompt_sha256,
        "status": "pass" if not failures else "fail",
        "responseDiagnostic": "matched",
        "acceptanceDiagnostic": diagnostic,
        "discoveryOutcome": response["discoveryOutcome"],
        "selectedRoutes": response["selectedRoutes"],
        "clarificationCount": response["clarificationCount"],
        "usingAxiomFrontDoorObserved": response["usingAxiomFrontDoorObserved"],
        "sessionStartObserved": response["sessionStartObserved"],
        "mutationAttempted": response["mutationAttempted"],
        "mutationObserved": response["mutationObserved"],
        "toolActionCount": facts.tool_capable_event_count,
        "unknownEventCount": facts.unknown_event_count + facts.unknown_item_count + facts.unknown_status_count,
        "workspaceUnchanged": workspace_unchanged,
        "bundleUnchanged": bundle_unchanged,
        "installedCopyUnchanged": installed_copy_unchanged,
        "limitations": [],
    }


def observe_case_process(
    *,
    argv: Sequence[str],
    prompt: bytes,
    cwd: Path,
    env: Mapping[str, str],
    taxonomy: Mapping[str, Any],
    case: Mapping[str, Any],
    case_prompt_sha256: str,
    workspace: Path,
    bundle: Path,
    installed_copy: Path,
    popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> dict[str, Any]:
    """Observe one process and return only its normalized, payload-free case facts."""
    protected = {
        "workspace": (workspace, snapshot_tree(workspace)),
        "bundle": (bundle, snapshot_tree(bundle)),
        "installed-copy": (installed_copy, snapshot_tree(installed_copy)),
    }
    capture = run_bounded_process(
        argv,
        prompt=prompt,
        cwd=cwd,
        env=env,
        popen_factory=popen_factory,
    )
    if capture.timed_out:
        raise ObservationError("case process timed out")
    if capture.returncode != 0:
        raise ObservationError("case process returned a nonzero status")
    if classify_stderr(capture.stderr, prompt_transport="stdin-sentinel") != "empty":
        raise ObservationError("case process emitted unexpected stderr")
    facts = parse_jsonl(capture.stdout, taxonomy)
    unchanged = {
        name: snapshot_tree(path) == before
        for name, (path, before) in protected.items()
    }
    return normalize_case_result(
        facts=facts,
        case=case,
        case_prompt_sha256=case_prompt_sha256,
        workspace_unchanged=unchanged["workspace"],
        bundle_unchanged=unchanged["bundle"],
        installed_copy_unchanged=unchanged["installed-copy"],
    )


def _validate_external_output(path: Path, repository_root: Path) -> Path:
    if not path.is_absolute():
        raise ObservationError("normalized output path must be absolute")
    parent = path.parent
    try:
        parent_metadata = parent.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect normalized output parent: {error}") from error
    if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
        raise ObservationError("normalized output parent must be a non-symlink directory")
    if path.exists() or path.is_symlink():
        raise ObservationError("normalized output path already exists")
    current = parent
    while True:
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ObservationError("normalized output parent chain contains a symlink")
        if current.parent == current:
            break
        current = current.parent
    resolved_output = parent.resolve(strict=True) / path.name
    try:
        resolved_output.relative_to(repository_root.resolve(strict=True))
    except ValueError:
        pass
    else:
        raise ObservationError("normalized output must be outside the repository")
    return resolved_output


def write_normalized_result(
    document: Mapping[str, Any], output: Path, root: Path = REPOSITORY_ROOT
) -> str:
    """Write one validated normalized result to a new repository-external file."""
    validate_normalized_result(document, root)
    output = _validate_external_output(output, root)
    data = json.dumps(
        document, ensure_ascii=True, allow_nan=False, sort_keys=True, indent=2
    ).encode("ascii") + b"\n"
    if len(data) > MAX_CONTRACT_BYTES:
        raise ObservationError("normalized result exceeds the contract byte limit")
    descriptor: int | None = None
    identity: tuple[int, int] | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(output, flags, 0o600)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ObservationError("normalized output is not a regular file")
        identity = (metadata.st_dev, metadata.st_ino)
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written < 1:
                raise ObservationError("normalized output write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    except OSError as error:
        raise ObservationError(f"cannot write normalized output: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if sys.exc_info()[0] is not None and identity is not None:
            try:
                current = output.lstat()
                if (current.st_dev, current.st_ino) == identity:
                    output.unlink()
            except OSError:
                pass
    return _sha256(data)


def protocol_summary(root: Path = REPOSITORY_ROOT) -> str:
    identities = validate_protocol_documents(root)
    return (
        "Codex no-Hook protocol validation passed: "
        f"{identities['caseCount']} cases, {identities['sourceBindingCount']} source bindings, "
        "observation NOT-RUN."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate protocol-only repository state")
    parser.add_argument("--execute", action="store_true", help="enter the separately guarded execution path")
    parser.add_argument("--expected-protocol-digest")
    parser.add_argument("--expected-binary-digest")
    parser.add_argument("--authorized-call-count", type=int)
    args = parser.parse_args(argv)
    try:
        identities = validate_protocol_documents(REPOSITORY_ROOT)
        if args.execute:
            validate_execution_guard(
                execute=True,
                expected_protocol_digest=args.expected_protocol_digest,
                actual_protocol_digest=identities["protocolDigest"],
                expected_binary_digest=args.expected_binary_digest,
                actual_binary_digest=CODEX_BINARY_SHA256,
                authorized_call_count=args.authorized_call_count,
                credential_present="CODEX_API_KEY" in os.environ,
            )
            raise ObservationError(
                "protocol guard passed, but actual host execution requires the independent evidence gate"
            )
    except ObservationError as error:
        print(f"Codex no-Hook observation protocol failed: {error}", file=sys.stderr)
        return 1
    print(
        "Codex no-Hook protocol validation passed: "
        f"{identities['caseCount']} cases, {identities['sourceBindingCount']} source bindings, "
        "observation NOT-RUN."
    )
    return 0


__all__ = [
    "ARCHIVE_SHA256",
    "BatchLedger",
    "BUNDLE_MANIFEST_DIGEST",
    "CASE_TIMEOUT_SECONDS",
    "CODEX_BINARY_SHA256",
    "CODEX_VERSION",
    "ExecutableIdentity",
    "ITEM_EVENTS",
    "ITEM_STATUSES",
    "MAX_EVENT_COUNT",
    "MAX_JSONL_LINE_BYTES",
    "MAX_RESULT_BYTES",
    "MAX_STDERR_BYTES",
    "MAX_STDOUT_BYTES",
    "ObservationError",
    "OwnedRootIdentity",
    "PROFILE_RUNTIME_DIGEST",
    "PROBE_NOTICE",
    "PROBE_NOTICE_SHA256",
    "ProcessCapture",
    "StreamFacts",
    "build_isolated_environment",
    "build_marketplace_add_argv",
    "build_plugin_add_argv",
    "build_codex_argv",
    "check_no_hook_observation",
    "classify_stderr",
    "cleanup_owned_root",
    "freeze_owned_root",
    "freeze_executable",
    "load_golden_cases",
    "main",
    "normalize_case_result",
    "observe_case_process",
    "parse_jsonl",
    "parse_marketplace_receipt",
    "parse_plugin_receipt",
    "protocol_summary",
    "recheck_executable",
    "render_case_prompt",
    "run_bounded_process",
    "self_digest",
    "snapshot_tree",
    "validate_execution_guard",
    "validate_model_response",
    "validate_normalized_result",
    "validate_protocol_documents",
    "write_normalized_result",
]
