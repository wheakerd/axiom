"""Static contract for the in-session routing sequence suites (Issue #249).

The fresh-session benchmark measures a request that is the first turn after the
gate. These suites measure the same corpus requests after scripted prior turns
in one isolated session per case: conversation turns, tool-reading turns, a
task-notification turn, an ongoing multi-step task, and a host-native
compaction. The suites are data for a host-executed measurement whose results
are published as counts only; no runner, transcript, or result record belongs to
the repository.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from ..context import REPOSITORY_ROOT
from .constants import (
    CURRENT_CORPUS_RELATIVE_PATH,
    CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256,
    HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH,
    PRIVATE_PATTERNS,
)
from .jsonio import exact_object, load_json_object, load_jsonl_cases, require_bool, require_int, require_string


IN_SESSION_SUITE_RELATIVE_PATH = "evals/in-session-routing-v1.json"
CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH = "evals/in-session-routing-claude-code-v1.json"
IN_SESSION_SUITE_SHA256 = "e321454b9b399ac50691a8b23accf4804990fca3fa3ac7ccd6cae154870637a6"
CLAUDE_CODE_IN_SESSION_SUITE_SHA256 = "f409ce24aa35e8eaec1d64b489311acf3b7fd7ea35687e249559f75168cdece0"
IN_SESSION_MEASURED_TURN_MARKER = "[routing-observation]"
IN_SESSION_DEVELOPER_INSTRUCTION = (
    "This is an Axiom in-session routing evaluation. Every turn ends with the structured routing observation for that "
    "turn's request. A turn whose request begins with [routing-observation] is a measured turn: select the Axiom route or "
    "routes that the request after the marker would invoke, and do not carry it out. Every other turn is a setup turn: "
    "carry it out with read-only means inside this workspace before reporting its own observation. No turn grants mutation "
    "authority: do not edit files, use credentials, contact external services, or request approval. Return no prose inside "
    "the structured output."
)
# One family per in-session condition, in the order the suites list them; the
# fresh family has no prior turn and is the baseline the other families compare with.
IN_SESSION_FAMILY_IDS = (
    "fresh",
    "prior-turns",
    "tool-results",
    "non-request-turn",
    "continuation",
    "compaction",
)
IN_SESSION_TURN_KINDS = ("setup", "non-request", "compact")
IN_SESSION_TURN_FACT_KEYS = frozenset({"setup", "non-request", "compact", "measured"})
# Everything but the host profile must be byte-identical across the two suites.
IN_SESSION_SHARED_KEYS = (
    "schemaVersion",
    "kind",
    "corpusSchema",
    "corpus",
    "responseSchema",
    "turnTimeoutSeconds",
    "repeatCount",
    "developerInstruction",
    "measuredTurnMarker",
    "measuredCaseIds",
    "workspaceFixture",
    "families",
    "turnFacts",
    "measurement",
)
IN_SESSION_TOP_KEYS = frozenset(
    {*IN_SESSION_SHARED_KEYS, "id", "method", "model", "reasoningEffort", "hostMechanics", "safety"}
)
IN_SESSION_HOST_PROFILES = {
    IN_SESSION_SUITE_RELATIVE_PATH: {
        "id": "in-session-routing-v1",
        "method": "documented-codex-app-server-thread-sequence",
        "model": "gpt-6-astra",
        "reasoningEffort": "max",
        "safety": {
            "sandbox": "read-only",
            "approvalPolicy": "never",
            "webSearch": "disabled",
            "freshSessionPerCase": True,
            "sameSessionWithinCase": True,
            "mutationAuthority": False,
            "externalActions": False,
            "privateTranscriptRetention": False,
            "credentialDisclosure": False,
        },
    },
    CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH: {
        "id": "in-session-routing-claude-code-v1",
        "method": "documented-claude-code-stream-json-input-sequence",
        "model": "claude-opus-5-5",
        "reasoningEffort": "max",
        "safety": {
            "permissionMode": "dontAsk",
            "sessionPersistence": False,
            "autoMemory": False,
            "freshSessionPerCase": True,
            "sameSessionWithinCase": True,
            "mutationAuthority": False,
            "externalActions": False,
            "privateTranscriptRetention": False,
            "credentialDisclosure": False,
        },
    },
}
_SUITE_DIGESTS = {
    IN_SESSION_SUITE_RELATIVE_PATH: IN_SESSION_SUITE_SHA256,
    CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH: CLAUDE_CODE_IN_SESSION_SUITE_SHA256,
}
_FIXTURE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*$")
_KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
_MAX_FIXTURE_FILES = 8
_MAX_FIXTURE_BYTES = 4096
_MAX_FAMILY_TURNS = 6


def _safe_text(value: Any, label: str, failures: list[str], maximum: int = 600) -> str | None:
    text = require_string(value, label, failures, maximum)
    if text is None:
        return None
    if not text.isascii():
        failures.append(f"{label} must use canonical English ASCII")
    for pattern, private_label in PRIVATE_PATTERNS:
        if pattern.search(text):
            failures.append(f"{label} contains {private_label}")
    return text


def _check_setup_request(text: str, label: str, failures: list[str]) -> None:
    if text.startswith(IN_SESSION_MEASURED_TURN_MARKER):
        failures.append(f"{label} must not carry the measured-turn marker")
    if "axiom" in text.lower():
        failures.append(f"{label} must not name Axiom; a setup turn is ordinary work, not an invocation")


def _check_families(value: Any, label: str, failures: list[str]) -> int:
    """Return the number of setup turns across the families, or 0 on a shape failure."""
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return 0
    ids = []
    setup_turns = 0
    for index, family in enumerate(value):
        family_label = f"{label}[{index}]"
        shape = exact_object(family, frozenset({"id", "condition", "setupTurns"}), family_label, failures)
        if shape is None:
            continue
        family_id = _safe_text(shape.get("id"), f"{family_label}.id", failures, 40)
        if family_id is not None:
            ids.append(family_id)
            if not _KEBAB.match(family_id):
                failures.append(f"{family_label}.id must be lowercase kebab-case")
        _safe_text(shape.get("condition"), f"{family_label}.condition", failures)
        turns = shape.get("setupTurns")
        if type(turns) is not list:
            failures.append(f"{family_label}.setupTurns must be an array")
            continue
        if len(turns) > _MAX_FAMILY_TURNS:
            failures.append(f"{family_label}.setupTurns exceeds {_MAX_FAMILY_TURNS} turns")
        if family_id == "fresh" and turns:
            failures.append(f"{family_label} must have no setup turn; it is the baseline")
        for turn_index, turn in enumerate(turns):
            turn_label = f"{family_label}.setupTurns[{turn_index}]"
            if type(turn) is not dict:
                failures.append(f"{turn_label} must be an object")
                continue
            kind = turn.get("kind")
            if kind not in IN_SESSION_TURN_KINDS:
                failures.append(f"{turn_label}.kind must be one of {', '.join(IN_SESSION_TURN_KINDS)}")
                continue
            if kind == "compact":
                exact_object(turn, frozenset({"kind"}), turn_label, failures)
                if turn_index != len(turns) - 1:
                    failures.append(f"{turn_label} compaction must be the last setup turn before the measured turn")
                continue
            exact_object(turn, frozenset({"kind", "request"}), turn_label, failures)
            request = _safe_text(turn.get("request"), f"{turn_label}.request", failures)
            if request is not None:
                _check_setup_request(request, f"{turn_label}.request", failures)
            setup_turns += 1
    if tuple(ids) != IN_SESSION_FAMILY_IDS:
        failures.append(f"{label} must list exactly the families {', '.join(IN_SESSION_FAMILY_IDS)} in that order")
    return setup_turns


def _check_fixture(value: Any, label: str, failures: list[str]) -> None:
    shape = exact_object(value, frozenset({"location", "files"}), label, failures)
    if shape is None:
        return
    location = _safe_text(shape.get("location"), f"{label}.location", failures)
    if location is not None and "no host instruction file" not in location:
        failures.append(f"{label}.location must require a workspace with no host instruction file in itself or any ancestor")
    files = shape.get("files")
    if type(files) is not dict or not files:
        failures.append(f"{label}.files must be a non-empty object")
        return
    if len(files) > _MAX_FIXTURE_FILES:
        failures.append(f"{label}.files exceeds {_MAX_FIXTURE_FILES} files")
    for name, content in files.items():
        file_label = f"{label}.files[{name!r}]"
        if not _FIXTURE_PATH.match(name) or ".." in name.split("/"):
            failures.append(f"{file_label} must be a portable relative path without dot segments")
        if type(content) is not str or not content:
            failures.append(f"{file_label} must be a non-empty string")
            continue
        if len(content.encode("utf-8")) > _MAX_FIXTURE_BYTES:
            failures.append(f"{file_label} exceeds {_MAX_FIXTURE_BYTES} bytes")
        if not content.isascii():
            failures.append(f"{file_label} must use ASCII")
        for pattern, private_label in PRIVATE_PATTERNS:
            if pattern.search(content):
                failures.append(f"{file_label} contains {private_label}")


def _check_measurement(value: Any, label: str, failures: list[str]) -> None:
    shape = exact_object(
        value,
        frozenset({"stopOnFirstFailure", "hostFailureRerun", "missConfirmation", "comparison", "publication"}),
        label,
        failures,
    )
    if shape is None:
        return
    if require_bool(shape.get("stopOnFirstFailure"), f"{label}.stopOnFirstFailure", failures) is True:
        failures.append(f"{label}.stopOnFirstFailure must be false; a measurement judges every family on the same cases")
    for field in ("hostFailureRerun", "missConfirmation"):
        count = require_int(shape.get(field), f"{label}.{field}", failures)
        if count is not None and count > 2:
            failures.append(f"{label}.{field} must not exceed 2 repeats")
    _safe_text(shape.get("comparison"), f"{label}.comparison", failures)
    _safe_text(shape.get("publication"), f"{label}.publication", failures)


def _check_suite(
    suite: dict[str, Any],
    relative_path: str,
    cases: dict[str, dict[str, Any]],
    response_digest: str | None,
    failures: list[str],
) -> tuple[int, int]:
    exact_object(suite, IN_SESSION_TOP_KEYS, relative_path, failures)
    profile = IN_SESSION_HOST_PROFILES[relative_path]
    expected_scalars = {
        "schemaVersion": "1",
        "kind": "in-session-routing-sequence-suite",
        "id": profile["id"],
        "method": profile["method"],
        "corpusSchema": "urn:axiom:routing-evals:schema:v8",
        "model": profile["model"],
        "reasoningEffort": profile["reasoningEffort"],
        "turnTimeoutSeconds": 300,
        "repeatCount": 1,
        "developerInstruction": IN_SESSION_DEVELOPER_INSTRUCTION,
        "measuredTurnMarker": IN_SESSION_MEASURED_TURN_MARKER,
    }
    for field, expected in expected_scalars.items():
        if suite.get(field) != expected:
            failures.append(f"{relative_path}.{field} drifted")
    corpus = exact_object(suite.get("corpus"), frozenset({"path"}), f"{relative_path}.corpus", failures)
    if corpus is not None and corpus.get("path") != CURRENT_CORPUS_RELATIVE_PATH:
        failures.append(f"{relative_path} binds the wrong corpus")
    binding = exact_object(
        suite.get("responseSchema"), frozenset({"path", "sha256"}), f"{relative_path}.responseSchema", failures
    )
    if binding is not None:
        if binding.get("path") != HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH:
            failures.append(f"{relative_path} binds the wrong response schema")
        if binding.get("sha256") != CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256 or (
            response_digest is not None and binding.get("sha256") != response_digest
        ):
            failures.append(f"{relative_path} response-schema digest drifted")
    measured = suite.get("measuredCaseIds")
    case_count = 0
    if type(measured) is not list or not measured:
        failures.append(f"{relative_path}.measuredCaseIds must be a non-empty array")
    else:
        seen: set[str] = set()
        for index, case_id in enumerate(measured):
            label = f"{relative_path}.measuredCaseIds[{index}]"
            text = require_string(case_id, label, failures, 120)
            if text is None:
                continue
            if text in seen:
                failures.append(f"{label} repeats {text!r}")
            seen.add(text)
            case = cases.get(text)
            if case is None:
                failures.append(f"{label} names no case in the current corpus")
            elif case.get("schemaVersion") != "8":
                failures.append(f"{label} must name a schema v8 case")
        case_count = len(seen)
    _check_fixture(suite.get("workspaceFixture"), f"{relative_path}.workspaceFixture", failures)
    _check_families(suite.get("families"), f"{relative_path}.families", failures)
    facts = exact_object(suite.get("turnFacts"), IN_SESSION_TURN_FACT_KEYS, f"{relative_path}.turnFacts", failures)
    if facts is not None:
        for field, text in facts.items():
            _safe_text(text, f"{relative_path}.turnFacts.{field}", failures)
    _check_measurement(suite.get("measurement"), f"{relative_path}.measurement", failures)
    mechanics = exact_object(
        suite.get("hostMechanics"),
        frozenset({"session", "turn", "compaction", "tools"}),
        f"{relative_path}.hostMechanics",
        failures,
    )
    if mechanics is not None:
        for field, text in mechanics.items():
            _safe_text(text, f"{relative_path}.hostMechanics.{field}", failures)
    safety = exact_object(
        suite.get("safety"), frozenset(profile["safety"]), f"{relative_path}.safety", failures
    )
    if safety is not None and safety != profile["safety"]:
        failures.append(f"{relative_path}.safety drifted from the host profile")
    families = suite.get("families")
    family_count = len(families) if type(families) is list else 0
    return family_count, case_count


def check_in_session_sequence_contracts(
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> tuple[int, int]:
    """Validate both in-session suites and return (family count, measured case count)."""
    response_path = root / HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH
    response_digest: str | None = None
    if response_path.is_file():
        response_digest = hashlib.sha256(response_path.read_bytes()).hexdigest()
    cases: dict[str, dict[str, Any]] = {}
    corpus_path = root / CURRENT_CORPUS_RELATIVE_PATH
    if corpus_path.is_file():
        for record in load_jsonl_cases(corpus_path, failures, root):
            case_id = record.get("id")
            if type(case_id) is str:
                cases[case_id] = record
    else:
        failures.append(f"{CURRENT_CORPUS_RELATIVE_PATH} is missing")
    suites: dict[str, dict[str, Any]] = {}
    counts: tuple[int, int] = (0, 0)
    for relative_path, expected_digest in _SUITE_DIGESTS.items():
        suite_path = root / relative_path
        suite = load_json_object(suite_path, failures, root)
        if suite is None:
            continue
        try:
            digest = hashlib.sha256(suite_path.read_bytes()).hexdigest()
        except OSError as error:
            failures.append(f"cannot hash {relative_path}: {error}")
        else:
            if digest != expected_digest:
                failures.append(f"{relative_path} digest drifted from the frozen in-session suite")
        suites[relative_path] = suite
        suite_counts = _check_suite(suite, relative_path, cases, response_digest, failures)
        if relative_path == IN_SESSION_SUITE_RELATIVE_PATH:
            counts = suite_counts
    codex = suites.get(IN_SESSION_SUITE_RELATIVE_PATH)
    claude = suites.get(CLAUDE_CODE_IN_SESSION_SUITE_RELATIVE_PATH)
    if codex is not None and claude is not None:
        for field in IN_SESSION_SHARED_KEYS:
            if codex.get(field) != claude.get(field):
                failures.append(f"in-session suites differ in shared field {field}; only the host profile may differ")
    return counts
