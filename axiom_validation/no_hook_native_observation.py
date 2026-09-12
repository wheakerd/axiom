"""Source-bound native CLI observation, independent of the retired v1 backend.

The operator owns a dedicated, non-concurrently-modified test root. Authentication
is performed only by the official client in each case's separate CODEX_HOME.
Only explicitly authorized test-auth reuse copies the official file as opaque
bytes between registered homes; it never parses, hashes or exposes it. Its
ordinary process timeout is not a claim of adversarial descendant containment.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
import re
from pathlib import Path
import selectors
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time
import tomllib
from typing import Any, Callable, Mapping, Sequence

from . import no_hook_observation as legacy
from .context import REPOSITORY_ROOT
from .yaml_subset import parse_skill_frontmatter_document


PROTOCOL_RELATIVE = Path("evals/no-hook-observation/codex-native-protocol-v2.json")
RESULT_SCHEMA_RELATIVE = Path("evals/no-hook-observation/codex-native-result-schema-v2.json")
HISTORY_RELATIVE = Path("evals/no-hook-observation/result-history-v2.json")
PROTOCOL_ID = "axiom-codex-native-observation-v2"
DISCOVERY_MECHANISM = "host-user-skills-from-installed-package"
STATE_NAME = "native-preparation.json"
CASE_COUNT = 16
PLUGIN_VERSION = "0.10.1"
STATIC_BUNDLE_EVIDENCE_RELATIVE = Path("evidence/profiles/openai-hook-independent-v1/bundle-v1.json")
MODEL_RESPONSE_SCHEMA_RELATIVE = Path("evals/no-hook-observation/codex-model-response-schema-v2.json")
ASSESSMENT_PRIOR_SHA256 = "e6c19c4324da9a40c074f2c0503a4b58a08fd6df6e58f747c7e41ba59248e64d"
ASSESSMENT_PRIOR_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-" + ASSESSMENT_PRIOR_SHA256 + ".json",
    "sha256": ASSESSMENT_PRIOR_SHA256,
    "implementationCommit": "04c7de8e972d64e1d15d4d40eb0a7081dca23407",
    "implementationTree": "0a9ce3fba5914684abf6cfe9e7dad3c851a143ad",
}
ASSESSMENT_PROTOCOL_DIGEST = "sha256:5dda0101d4558a899b3ed8600d615bbbfc461034dac56e12f9f496538f201a7e"
ASSESSMENT_PARTIAL_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-9880ebdd844f2469ab07c136d75e1561b4553cc4ff99cfe6b4de564d05f48fd9.json",
    "sha256": "9880ebdd844f2469ab07c136d75e1561b4553cc4ff99cfe6b4de564d05f48fd9",
    "implementationCommit": "a29b9503920a8798509407f40645a0efee14b474",
    "implementationTree": "a5289b6a8e787b82bd1a73ba06a0447e619fb855",
}
ASSESSMENT_REMAINDER = {
    "priorResult": ASSESSMENT_PARTIAL_BINDING, "firstNewOrdinal": 11,
    "lastOrdinal": 16, "priorAttemptCount": 30, "maximumNewAttempts": 6,
    "maximumCumulativeAttempts": 36, "authenticationSourceOrdinal": 9,
    "priorStop": "preserved; independent unstarted cases only",
    "stderrReview": "same-attempt only; all existing eligibility conditions required",
}
ASSESSMENT_REMAINDER_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-e1504982697cc3a20f93a66245983362d2ecc7ddb60534681f9bdc53b65f29b3.json",
    "sha256": "e1504982697cc3a20f93a66245983362d2ecc7ddb60534681f9bdc53b65f29b3",
    "implementationCommit": "34376415079fc59c5caf6614fd85e18e3beea030",
    "implementationTree": "a73078150ac03b91db99dc04657d13fc5e757074",
}
MATERIAL_DELIVERY = {
    "revision": 1, "source": "fixtureMatrix.files[].path",
    "pathBase": "case-workspace", "order": "utf8-byte-order",
    "scope": "task-data-only; not-installed-skills; empty-list-is-not-discovery-evidence",
}
MATERIAL_SEGMENT = {
    "priorResult": ASSESSMENT_REMAINDER_BINDING, "firstNewOrdinal": 10,
    "lastOrdinal": 16, "priorAttemptCount": 31, "maximumNewAttempts": 7,
    "maximumCumulativeAttempts": 38, "authenticationSourceOrdinal": 9,
    "inputRevision": 2, "history": "references only; no inherited observations or sessions",
    "stop": "any policy rejection or reliability failure stops remaining cases",
}
MATERIAL_OBSERVATION_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-3b10da277aea213ba5bcecc8bfeac486a5a1fdb0339c3a4fd2d7aef066a32360.json",
    "sha256": "3b10da277aea213ba5bcecc8bfeac486a5a1fdb0339c3a4fd2d7aef066a32360",
    "implementationCommit": "12720d103a0b46b6223ad2a41b562c1ec2935b87",
    "implementationTree": "bde5a0d2f36ade6c6fa3bfbc0d951d1ab7054bf4",
    "protocolDigest": "sha256:23b888e9dc090027b939b525c34ca12884769ee7ecb52aa5418ef2e88b7b7e4b"
}
ASSESSMENT_REVISION_THREE = {
    "path": "evals/no-hook-observation/results/codex-native-c74da98c54d0f4dae9fda4252fcff5ed7b341f3c3b56f38c71c1a4feb0477ff1.json",
    "sha256": "c74da98c54d0f4dae9fda4252fcff5ed7b341f3c3b56f38c71c1a4feb0477ff1",
    "implementationCommit": "1cb076f4d54cb63e24ae097ccb728d67c614e1fd",
    "implementationTree": "5438670d41b75c88779f6749f652746f544e9cc9",
    "protocolDigest": "sha256:80e8de41f54ca3a3316dc17f1f2857ac980c8979c808bf8143e06a2cdb9824e9",
}
CURRENT_ASSESSMENT = {
    "priorResult": ASSESSMENT_REVISION_THREE, "firstNewOrdinal": 1,
    "lastOrdinal": 16, "maximumNewAttempts": 16, "maximumCumulativeAttempts": 70,
    "authenticationSourceOrdinal": 16, "assessmentRevision": 3, "explicitInvocationRevision": 1,
    "history": "deduplicate ordinal and materialization commitment; no inherited sessions",
    "stop": "any policy rejection or reliability failure stops remaining cases",
    "stderrReview": "same-attempt only; all existing eligibility conditions required",
}
CURRENT_PRIOR_RESULTS = [ASSESSMENT_REVISION_THREE["sha256"]]
FIXED_ROUTING_PRIOR = "0307ab9a45698a3f4176f21bd30113307c9d3867c0bad069abd87e1c1a98c43a"
FIXED_REPLY_PRIORS = [
    "5b6c943d2b68be63d2b6a08cbc29783935efa57cab818ba08d2da4015e4e37ae",
    "2567ec1a73043a0275f8574928ca875950515a1f356af83ca8cff05d79248449",
]
FIXED_PRIOR_RESULTS = [FIXED_ROUTING_PRIOR, *FIXED_REPLY_PRIORS]
FIXED_ACCEPTANCE = {
    "windowId": "pending-choice-fixed-1", "state": "authorized-once",
    "candidateCommit": "1f0362d18fc281b251387a357bb6ad4a7eb5c661",
    "candidateTree": "795c08276f56f1096a1fe9878ecab53febfd24e6",
    "sourceCommit": "8a593026285d285d95f7a9e0c6ec0793738c3707",
    "sourceTree": "fb1ecd9b605f3e928fd958da2333f66d3018c0f3",
    "fullRuntimeDigest": "sha256:88060c3c90ed3a4b3c2d603afc6bd06d441dbae186c5a6f5886b7f3764c9e5f2",
    "profileRuntimeDigest": "sha256:6965d7c3590f3f3b03cf800d8b5ec638446a9b260b3f55e10d2565d754ac75e3",
    "priorResultSha256s": FIXED_PRIOR_RESULTS, "priorAttempts": 76, "priorCliLaunches": 76,
    "routingOrdinals": list(range(1, 17)), "clarificationOrdinals": [12, 13, 14],
    "maximumNewAttempts": 19, "maximumCumulativeAttempts": 95,
    "routingRunName": "cases-pending-choice-routing-1",
    "clarificationRunName": "cases-pending-choice-clarification-1",
    "order": "complete routing before clarification; semantic failures do not resample",
    "stop": "reliability, identity or policy failure stops all remaining observations",
}
FIXED_REGISTRATION = "pending-choice-fixed-1.json"
FIXED_RESULT_SHA256 = "3cf0c1c795cac5db32d39ecc1d1932b83e49c6ade902db3f4603b850c7ab648d"
REVISION_FOUR_PRIOR_RESULTS = [FIXED_RESULT_SHA256]
REVISION_FOUR_ACCEPTANCE = {
    **FIXED_ACCEPTANCE,
    "windowId": "assessment-revision-4-fixed-1",
    "candidateCommit": "303e5b9e984d3647b06b84bf8ebc794887af698e",
    "candidateTree": "2469367551b4ebe41d04a571ff162c3e77731edc",
    "priorResultSha256s": REVISION_FOUR_PRIOR_RESULTS,
    "priorAttempts": 87, "priorCliLaunches": 87,
    "maximumCumulativeAttempts": 106,
    "routingRunName": "cases-assessment-revision-4-fixed-1",
    "clarificationRunName": "cases-assessment-revision-4-clarification-1",
    "authenticationSourceOrdinal": 10,
    "assessmentRevision": 4,
}


def _fixed_contract(revision_four: bool = False) -> dict[str, Any]:
    return REVISION_FOUR_ACCEPTANCE if revision_four else FIXED_ACCEPTANCE


def _fixed_history_key(revision_four: bool = False) -> str:
    return "revisionFourAcceptance" if revision_four else "fixedAcceptance"


def _fixed_kind(revision_four: bool = False) -> str:
    return "assessment-revision-4-fixed-1" if revision_four else "fixed-candidate-acceptance-1"

EXPLICIT_INVOCATION = {
    "revision": 1, "transport": "codex-exec-stdin-namespaced-dollar-mention",
    "sourceCommit": "41e22fee981a63b3698df7ed36bad393cda24715",
    "sourcePaths": ["codex-rs/exec/src/lib.rs", "codex-rs/ext/skills/src/provider/host.rs",
                    "codex-rs/ext/skills/src/loader/host.rs", "codex-rs/ext/skills/src/loader/namespace.rs",
                    "codex-rs/ext/skills/src/selection.rs", "codex-rs/skills/src/mentions.rs",
                    "codex-rs/skills/src/selection.rs"],
    "source": "inner-request-leading-Invoke-name-to-or-explicitly-to; Use-the-name-Skill-to",
    "catalog": "bound-package-frontmatter-and-nearest-plugin-namespace",
    "matching": "exact-case-sensitive-unique-enabled-name; no-display-name-or-route-inference",
    "connectorCondition": "existing apps=false and mcp_servers={} configuration; no connector-name collision",
    "noInstallation": "no-selection-added", "evidence": "selection-representation; not-observed-native-body-load",
    "supportChange": "explicit-invocation-adaptation; not-unchanged-natural-language-discovery",
}
MODEL = "gpt-5.5"
REASONING_EFFORT = "medium"
AUTH_FILE_NAME = "auth.json"
AUTH_COPY_STATE = "test-auth-copy-state.json"
NativeObservationError = legacy.ObservationError
HISTORICAL_RESULT_SHA256 = "5a7b9965820612204138f140b404a9fb7fb018c7f07ada14e2e09ccc514ad4ef"
HISTORICAL_PROTOCOL_DIGEST = "sha256:735ad73170d6d1f3b4b6a21a4dfdc4dc280100a07e47bead22b2af9562a577dc"
RETRY_RESULT_SHA256 = "8b6e4a93f6b2edd8c4f4c89f275e3ed023b47ea74b44835cfbf97d77f948c6df"
RETRY_PROTOCOL_DIGEST = "sha256:0990cdc1ff099e4cdd06f4a9c5f085b050df4adea3a081d19f47533124e0ae35"
THIRD_RESULT_SHA256 = "bfdd8b8569750d5797caf3e19c1e1acb55e190043b8dbdfdd2f48f47bd93fc79"
THIRD_PROTOCOL_DIGEST = "sha256:f3debf395d3f03e1bd34a7b62a4b07a3be3f23a77109d9449f1e175993c7b640"
FOURTH_RESULT_SHA256 = "ef51fd26305e11ae7f844172326e5f4cf0b7c20f8701dafe34ea87778228ed0b"
FOURTH_PROTOCOL_DIGEST = "sha256:91e5e56969c25e10477880935fe78af3825cd6f436126adc4e0d179f31855a4b"
PRIOR_RESULTS = [HISTORICAL_RESULT_SHA256, RETRY_RESULT_SHA256, THIRD_RESULT_SHA256, FOURTH_RESULT_SHA256]
PRIVATE_DIAGNOSTIC_LIMIT = 16384
EVENT_TYPES = ("thread.started", "turn.started", "turn.completed", "turn.failed", "error",
               "item.started", "item.updated", "item.completed", "unknown")
DIRECT_TOOLS_FALLBACK_NOTICE = (
    "Code Mode is unavailable because code-mode host is disabled. Falling back to direct tools; "
    "enable `features.code_mode_host` and install `codex-code-mode-host`."
)
CODE_MODE_FAIL_CLOSED_NOTICE = (
    "Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; "
    "enable `features.code_mode_host` and install `codex-code-mode-host`."
)
FIFTH_RESULT_SHA256 = "7edd7ab7068f85525074b10f874b325c066a35de183048b037f78f5a9286b018"
FIFTH_PROTOCOL_DIGEST = "sha256:59170c119dca1de340c286c5502d2176c222deb0c34784b5c19d30cc091d4b6d"
MODEL_PRIOR_RESULTS = [*PRIOR_RESULTS, FIFTH_RESULT_SHA256]
SIXTH_RESULT_SHA256 = "b5c112f41836e34e869fd067cb18ae29f812e42dd1d933337fa6d64e912f202a"
SIXTH_PROTOCOL_DIGEST = "sha256:7e157a874983131fcbcc2f48d399dfc540eefd7941b23f01c641567d137f6c99"
STDERR_PRIOR_RESULTS = [*MODEL_PRIOR_RESULTS, SIXTH_RESULT_SHA256]
SEVENTH_RESULT_SHA256 = "c66d47ac18377a2ff202c6dcbfa36f07c0e68ca2dbd200d8c8685e0c9f8b8ca0"
SEVENTH_PROTOCOL_DIGEST = "sha256:60565e21524e334a029b72846cd68a22b705236064a3e26dffd1354f5fba0ad2"
READ_PRIOR_RESULTS = [*STDERR_PRIOR_RESULTS, SEVENTH_RESULT_SHA256]
ASSESSMENT_PRIOR_RESULTS = [*READ_PRIOR_RESULTS, ASSESSMENT_PRIOR_SHA256]
PREVIOUS_PARTIAL_SHA256 = "ccf99c208c1131e6fb9c31d65077138602dd7abc5f803bd50c0bdcaea783dd4b"
PREVIOUS_PARTIAL_PROTOCOL = "sha256:5ce454ebaf368fd11884f3e91c50bd7ecbcc2d755b21ce0554fe786db94e3a97"
PREVIOUS_REVIEW_RELATIVE = Path("evals/no-hook-observation/case-05-catalog-review-v2.json")
PREVIOUS_PARTIAL_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-" + PREVIOUS_PARTIAL_SHA256 + ".json",
    "sha256": PREVIOUS_PARTIAL_SHA256,
    "implementationCommit": "7c4c2c8aa01cde728976d1047e8801852a7e2485",
    "implementationTree": "fcd7e72c576321b77742ba5d341f66ef817682f7",
}
REVIEWED_PARTIAL_SHA256 = "72ab78c4eae4ff40a99098480033ffa98966991028316730a19d84f37545c3dd"
REVIEWED_PARTIAL_PROTOCOL = "sha256:795610bb36b81bed4d52aa887b055de94de964b9167c7ee7437982ed2544e551"
REVIEW_RELATIVE = Path("evals/no-hook-observation/case-06-catalog-review-v2.json")
PREVIOUS_REVIEW_SHA256 = "b0b88827ee9f4fbe47f98e277b335b6a33c96b02c5cf84d82b6727309591d564"
REVIEWED_PREFIX_COUNT = 6
REVIEWED_PARTIAL_BINDING = {
    "path": "evals/no-hook-observation/results/codex-native-" + REVIEWED_PARTIAL_SHA256 + ".json",
    "sha256": REVIEWED_PARTIAL_SHA256,
    "implementationCommit": "92e8e435d3c39041ff2c86a0fa8c039c4996a121",
    "implementationTree": "208af3be62f98c91b576b3259b325bb929457596",
}
READ_REJECTIONS = (
    "event-shape", "read-command-syntax", "read-target-unbound", "read-lifecycle",
    "read-output-mismatch", "read-prefix-mismatch",
)
EVENT_REJECTIONS = (*READ_REJECTIONS, "event-unsupported", "item-unsupported", "item-lifecycle")
STREAM_ASSERTIONS = (
    "none", "framing-or-size", "event-count", "event-after-terminal", "event-shape",
    "thread-start-order", "turn-start-order", "terminal-active-items", "error-before-thread",
    "item-outside-lifecycle", "item-id-sequence", "item-id-reused", "command-start-duplicate",
    "command-start-mismatch", "content-id-reused", "agent-message-size", "missing-terminal",
    "final-message-missing", "final-message-invalid-json", "final-message-not-object",
    "final-output-unavailable", "final-output-mismatch",
    *EVENT_REJECTIONS[1:],
)


class NativeEventError(NativeObservationError):
    """A closed event predicate, never host text or a raw exception."""

    def __init__(self, code: str):
        if code not in EVENT_REJECTIONS:
            raise ValueError("invalid native event rejection")
        self.code = code
        super().__init__("native event assertion: " + code)


class NativeReadError(NativeEventError):
    """A read predicate failure without command, path, or output content."""

    def __init__(self, code: str):
        if code not in READ_REJECTIONS:
            raise ValueError("invalid native read rejection")
        super().__init__(code)


class NativeStreamError(NativeObservationError):
    """A stable assertion location, never an exception message from host data."""

    def __init__(self, code: str, event_ordinal: int | None, phase: str = "stream"):
        if code not in STREAM_ASSERTIONS[1:] or phase not in {"stream", "response"}:
            raise ValueError("invalid native assertion identifier")
        self.code, self.event_ordinal, self.phase = code, event_ordinal, phase
        self.closed_terminal = None
        self.completed_commands = None
        super().__init__("native " + phase + " assertion: " + code)


def _diagnostics() -> dict[str, Any]:
    return {"phase": "none", "category": "none", "returnCode": None, "signal": None,
            "timedOut": False, "observerTerminated": False, "cleanupFailed": False,
            "inputBytesSent": 0, "inputFullyDelivered": None, "stdoutBytes": 0,
            "stderrBytes": 0, "eventCount": 0, "eventTypes": [],
            "stderrClassification": "not-observed", "officialErrorCode": "unknown",
            "itemTypes": [], "policyReason": "none", "diagnosticItemCount": 0,
            "preTurnDiagnosticCount": 0, "hostDiagnosticClasses": [],
            "streamAssertion": "none", "streamEventOrdinal": None,
            "finalOutputVerified": False}


def _first_failure(facts: dict[str, Any], phase: str, category: str) -> None:
    if facts["category"] == "none":
        facts.update(phase=phase, category=category)


def _first_assertion(facts: dict[str, Any], code: str, ordinal: int | None) -> None:
    if facts["streamAssertion"] == "none":
        facts.update(streamAssertion=code, streamEventOrdinal=ordinal)


class NativeDiagnosticError(NativeObservationError):
    """Only closed facts cross the capture boundary; never retain raw exceptions."""

    def __init__(self, facts: Mapping[str, Any], *, capture: Mapping[str, Any] | None = None):
        self.facts = dict(facts)
        # Bounded raw capture is ephemeral and never serialized or displayed.
        self.capture = capture
        super().__init__("native " + self.facts["category"])


class PrivateDiagnostics:
    """Opt-in finite summaries, not a general sanitizer of arbitrary host text.

    Only frozen template names and predeclared public values are emitted.
    Unknown dynamic text is omitted, rather than claiming regex redaction
    proves it secret-free. Raw diagnostics stay in bounded process memory.
    """

    def __init__(self, ledger: Path):
        self.directory = ledger / "private-diagnostics"
        self.directory.mkdir(mode=0o700)
        self.remaining = PRIVATE_DIAGNOSTIC_LIMIT
        self.pending: list[bytes] = []
        self.ordinal = 0

    def message(self, ordinal: int, message: str) -> None:
        _require(type(ordinal) is int and 1 <= ordinal <= 16, "invalid diagnostic ordinal")
        self.ordinal = ordinal
        summary = "unclassified host diagnostic; dynamic content omitted"
        if message == "invalid global instructions":
            summary = "invalid-global-instructions; instruction context not established"
        elif message == (f"Model metadata for `{MODEL}` not found. Defaulting to fallback metadata; "
                         "this can degrade performance and cause issues."):
            summary = f"model-metadata-fallback; configured model {MODEL}; context/tool metadata not established"
        elif re.fullmatch(r"Model metadata for `[^`\r\n]+` not found\. Defaulting to fallback metadata; "
                          r"this can degrade performance and cause issues\.", message):
            summary = "model-metadata-fallback; unretained model identifier; context/tool metadata not established"
        elif re.fullmatch(r"model rerouted: [^\r\n]+ -> [^\r\n]+ \([^\r\n]+\)", message):
            summary = "model-rerouted; fixed model requirement violated; dynamic identifiers omitted"
        elif re.fullmatch(r"in-process app-server event stream lagged; dropped [0-9]+ events", message):
            summary = "event-stream-lag; dropped events; evidence incomplete"
        elif message.startswith("Under-development features enabled: ") and (
                ". Under-development features are incomplete and may behave unpredictably. "
                "To suppress this warning, set `suppress_unstable_features_warning = true` in " in message):
            summary = "under-development-features; effective configuration contains experimental features; values omitted"
        elif message.startswith("Code Mode is enabled in configuration, but model `") and message.endswith(
                "Disable `features.code_mode` and `features.code_mode_only`, or select a model whose metadata enables Code Mode."):
            summary = "code-mode-model-mismatch; features.code_mode; features.code_mode_only"
        elif message.startswith("Configured value for `") and "is disallowed by requirements; falling back" in message:
            for key in ("windows.sandbox", "approval_policy", "approvals_reviewer", "permission_profile", "web_search_mode"):
                if message.startswith(f"Configured value for `{key}` is disallowed by requirements; falling back"):
                    summary = "required-config-fallback; " + key + "; required value and details omitted"
                    break
        elif message.startswith("Error parsing rules; custom rules not applied."):
            summary = "rules-parse-failure; custom rules not applied; details omitted"
        self._add("case-" + str(ordinal) + ": " + summary)

    def _add(self, text: str) -> None:
        data = (text + "\n").encode("ascii")
        if len(data) <= self.remaining:
            self.pending.append(data)
            self.remaining -= len(data)

    def event(self, ordinal: int, raw: bytes) -> None:
        if len(raw) > legacy.MAX_JSONL_LINE_BYTES:
            return
        try:
            event = legacy._parse_json_line(raw)
            payload = (event if event.get("type") == "error" else
                       event.get("error") if event.get("type") == "turn.failed" else
                       event.get("item") if event.get("type") == "item.completed" else None)
            if type(payload) is dict and (event.get("type") != "item.completed" or payload.get("type") == "error"):
                message = payload.get("message")
                if type(message) is str:
                    self.message(ordinal, message)
        except (ValueError, NativeObservationError):
            pass  # The normal receiver still rejects malformed events.

    def stderr(self, ordinal: int, data: bytes) -> None:
        self.ordinal = ordinal
        for raw in data[:legacy.MAX_STDERR_BYTES].splitlines():
            if not raw:
                continue
            if raw in {b"Reading prompt from stdin...", b"Reading additional input from stdin..."}:
                summary = "stdin informational notice"
            elif raw.startswith(b"Could not create otel exporter: "):
                summary = "otel exporter initialization failed; dynamic details omitted"
            elif raw.startswith(b"WARNING: proceeding, even though we could not create PATH aliases: "):
                summary = "PATH alias creation failed; dynamic details omitted"
            elif raw.startswith(b"WARNING: failed to clean up stale arg0 temp dirs: "):
                summary = "stale arg0 temporary directory cleanup failed; dynamic details omitted"
            else:
                summary = "unclassified stderr; dynamic content omitted"
            self._add("case-" + str(ordinal) + " stderr: " + summary)

    def save(self) -> None:
        if self.pending:
            _exclusive(self.directory / f"case-{self.ordinal:02d}.txt", b"".join(self.pending))
            self.pending.clear()


def _private_capture() -> dict[str, Any]:
    return {"status": "not-requested", "bytes": 0, "truncated": False}


def _stderr_capture() -> dict[str, Any]:
    return {"status": "not-requested", "bytes": 0, "truncated": False,
            "encoding": "not-observed"}


class OperatorDiagnostics:
    """Explicit human-only exception for three host message fields.

    Never read these files back in production, hash them, attach them to a
    result, or expose them to either model. Permissions are ordinary local
    protection, not isolation from another process running as the same user.
    Item notices share only 4 KiB of the batch budget, reserving capacity for
    final error/turn.failed messages. JSON framing counts toward the 16 KiB cap.
    """

    def __init__(self, ledger: Path, *, reviewed_prefix: Sequence[Mapping[str, Any]] = ()):
        self.directory = ledger / "operator-only-diagnostics"
        if reviewed_prefix:
            # Only closed public capture metadata is consumed, never old raw files.
            metadata = self.directory.lstat()
            _require(stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == os.getuid() and
                     stat.S_IMODE(metadata.st_mode) == 0o700, "operator directory ownership changed")
            _require(len(reviewed_prefix) in (REVIEWED_PREFIX_COUNT, 10) and all(item["privateCapture"]["bytes"] == 0
                     for item in reviewed_prefix), "unsupported prior event capture budget")
        else:
            self.directory.mkdir(mode=0o700)
        self.used = 0
        self.category_used = {"item.completed": 0, "error": 0, "turn.failed": 0}
        self.pending: list[bytes] = []
        self.truncated = False
        self.stderr_used = sum(item["operatorStderrCapture"]["bytes"] for item in reviewed_prefix)
        _require(0 <= self.stderr_used <= PRIVATE_DIAGNOSTIC_LIMIT, "prior stderr budget invalid")
        self.stderr_pending: bytes | None = None
        self.stderr_facts = _stderr_capture()
        self.command_pending: bytes | None = None
        self.command_facts = _private_capture()

    def rejected_command(self, raw: bytes) -> None:
        """One already-emitted rejected command, human-only; never read its target."""
        if self.command_pending is not None or len(raw) > legacy.MAX_JSONL_LINE_BYTES:
            return
        try:
            event = legacy._parse_json_line(raw)
        except (ValueError, NativeObservationError):
            return
        item = event.get("item")
        if not (type(item) is dict and item.get("type") == "command_execution" and
                type(item.get("command")) is str):
            return
        def encode(text: str) -> bytes:
            return (json.dumps({"command": text}, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
        text = item["command"]
        data = encode(text)
        truncated = len(data) > 4096
        if truncated:
            low, high = 0, len(text)
            while low < high:
                middle = (low + high + 1) // 2
                if len(encode(text[:middle])) <= 4096:
                    low = middle
                else:
                    high = middle - 1
            data = encode(text[:low])
        self.command_pending = data
        self.command_facts = {"status": "pending", "bytes": 0, "truncated": truncated}

    def save_command(self, ordinal: int) -> dict[str, Any]:
        _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "invalid diagnostic ordinal")
        facts = self.command_facts
        if self.command_pending is not None:
            descriptor = None
            try:
                descriptor = os.open(self.directory / f"case-{ordinal:02d}-read-rejection.json",
                                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.fchmod(descriptor, 0o600)
                view = memoryview(self.command_pending)
                while view:
                    count = os.write(descriptor, view)
                    if count <= 0:
                        raise OSError("short private command write")
                    facts["bytes"] += count
                    view = view[count:]
                os.fsync(descriptor)
                facts["status"] = "saved"
            except OSError:
                facts["status"] = "write-failed"
            finally:
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError:
                        facts["status"] = "write-failed"
        self.command_pending = None
        self.command_facts = _private_capture()
        return facts

    def stderr(self, raw: bytes) -> None:
        """Retain only this canonical invocation's stderr, never return text.

        JSON escaping preserves controls as data. Invalid UTF-8 bytes become
        escaped surrogate code points and are explicitly reported; no claim of
        clean text is made. The serialized batch budget is separate from events.
        """
        facts = {"status": "empty", "bytes": 0, "truncated": False, "encoding": "utf-8"}
        self.stderr_facts = facts
        if not raw:
            return
        try:
            message = raw.decode("utf-8")
        except UnicodeDecodeError:
            message = raw.decode("utf-8", errors="surrogateescape")
            facts["encoding"] = "invalid-utf-8"
        def encode(text: str) -> bytes:
            return (json.dumps({"stderr": text}, ensure_ascii=True,
                               separators=(",", ":")) + "\n").encode("ascii")
        remaining = PRIVATE_DIAGNOSTIC_LIMIT - self.stderr_used
        data = encode(message)
        if len(data) > remaining:
            facts["truncated"] = True
            if len(encode("")) > remaining:
                facts["status"] = "omitted"
                return
            low, high = 0, len(message)
            while low < high:
                middle = (low + high + 1) // 2
                if len(encode(message[:middle])) <= remaining:
                    low = middle
                else:
                    high = middle - 1
            data = encode(message[:low])
        self.stderr_pending = data

    def save_stderr(self, ordinal: int) -> dict[str, Any]:
        _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "invalid diagnostic ordinal")
        facts = self.stderr_facts
        descriptor = None
        try:
            if self.stderr_pending is not None:
                descriptor = os.open(self.directory / f"case-{ordinal:02d}-stderr.json",
                                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.fchmod(descriptor, 0o600)
                view = memoryview(self.stderr_pending)
                while view:
                    count = os.write(descriptor, view)
                    if count <= 0:
                        raise OSError("short private stderr write")
                    facts["bytes"] += count
                    view = view[count:]
                os.fsync(descriptor)
                facts["status"] = "saved"
        except OSError:
            facts["status"] = "write-failed"
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    facts["status"] = "write-failed"
            self.stderr_used += facts["bytes"]
            self.stderr_pending = None
            self.stderr_facts = _stderr_capture()
        return facts

    def event(self, raw: bytes) -> None:
        if len(raw) > legacy.MAX_JSONL_LINE_BYTES:
            return  # The ordinary receiver enforces framing and output limits.
        try:
            event = legacy._parse_json_line(raw)
        except (ValueError, NativeObservationError):
            return
        kind = event.get("type")
        payload = (event if kind == "error" else event.get("error") if kind == "turn.failed" else
                   event.get("item") if kind == "item.completed" else None)
        if not (type(payload) is dict and type(payload.get("message")) is str and
                (kind != "item.completed" or payload.get("type") == "error")):
            return
        # Each final message gets up to 6 KiB, so one cannot consume the other's
        # reservation. Nothing from reasoning, agent messages or stderr enters.
        remaining = PRIVATE_DIAGNOSTIC_LIMIT - self.used - sum(map(len, self.pending))
        limit = min(remaining, (4096 if kind == "item.completed" else 6144) - self.category_used[kind])
        def encode(message: str) -> bytes:
            return (json.dumps({"event": kind, "message": message}, ensure_ascii=True,
                               separators=(",", ":")) + "\n").encode("ascii")
        message = payload["message"]
        data = encode(message)
        if len(data) > limit:
            self.truncated = True
            if len(encode("")) > limit:
                return
            low, high = 0, len(message)
            while low < high:
                middle = (low + high + 1) // 2
                if len(encode(message[:middle])) <= limit:
                    low = middle
                else:
                    high = middle - 1
            data = encode(message[:low])
        self.pending.append(data)
        self.category_used[kind] += len(data)

    def save(self, ordinal: int) -> dict[str, Any]:
        _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "invalid diagnostic ordinal")
        facts = {"status": "omitted" if self.truncated else "no-diagnostics", "bytes": 0, "truncated": self.truncated}
        descriptor = None
        try:
            if self.pending:
                descriptor = os.open(self.directory / f"case-{ordinal:02d}.jsonl",
                                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.fchmod(descriptor, 0o600)
                for data in self.pending:
                    view = memoryview(data)
                    while view:
                        count = os.write(descriptor, view)
                        if count <= 0:
                            raise OSError("short private diagnostic write")
                        facts["bytes"] += count
                        view = view[count:]
                os.fsync(descriptor)
                facts["status"] = "saved"
        except OSError:
            facts["status"] = "write-failed"
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    facts["status"] = "write-failed"
            self.used += facts["bytes"]
            self.pending.clear()
            self.truncated = False
        return facts


def _stderr_classification(data: bytes) -> str:
    if not data:
        return "empty"
    # Frozen exec reads '-' from stdin with this informational notice. Unknown
    # stderr is retained only as a classification and cannot establish success.
    fixed = {b"Reading prompt from stdin...", b"Reading additional input from stdin...",
             b"Could not create otel exporter: panicked during initialization"}
    prefixes = (b"Could not create otel exporter: ",
                b"WARNING: proceeding, even though we could not create PATH aliases: ",
                b"WARNING: failed to clean up stale arg0 temp dirs: ")
    catalog_timeout = re.compile(
        rb"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{1,9}Z "
        rb"ERROR codex_models_manager::manager: failed to refresh available models: "
        rb"timeout waiting for child process to exit")
    # Frozen models_endpoint.rs maps its bounded catalog timeout to the generic
    # Timeout display. manager.rs keeps the prior catalog. This classification
    # cannot bypass the full input, final-output, model and postcheck gates.
    if data.endswith(b"\n") and all(line in fixed or catalog_timeout.fullmatch(line) is not None or any(
            line.startswith(prefix) and len(line) > len(prefix) for prefix in prefixes)
            for line in data.splitlines()):
        return "known-nonfatal"
    return "unknown"


def _capture_facts(capture: Mapping[str, Any]) -> dict[str, Any]:
    facts = dict(capture.get("diagnostics", _diagnostics()))
    code = capture["returncode"]
    facts.update(returnCode=code, signal=-code if code is not None and code < 0 else None,
                 stdoutBytes=len(capture["stdout"]), stderrBytes=len(capture["stderr"]),
                 stderrClassification=_stderr_classification(capture["stderr"]))
    if code != 0:
        _first_failure(facts, "exit", "process-exit")
    if facts["stderrClassification"] == "unknown":
        _first_failure(facts, "exit", "unknown-stderr")
    return facts
IMPLEMENTATION_PATHS = (
    "axiom_validation/context.py", "axiom_validation/no_hook_bundle.py",
    "axiom_validation/no_hook_clarification.py",
    "axiom_validation/no_hook_linux_isolation.py", "axiom_validation/no_hook_native_observation.py",
    "axiom_validation/no_hook_observation.py", "axiom_validation/no_hook_profile.py",
    "axiom_validation/release_versions.py", "axiom_validation/routing_evals/jsonio.py",
    "axiom_validation/yaml_subset.py",
    "scripts/run-no-hook-native-observation.py",
)
INPUT_PATHS = {
    "goldenSet": legacy.GOLDEN_SET_RELATIVE.as_posix(),
    "modelResponseSchema": MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix(),
    "promptEnvelope": "evals/no-hook-observation/codex-native-prompt-envelope-v2.json",
    "taxonomy": legacy.TAXONOMY_RELATIVE.as_posix(), "fixtureMatrix": legacy.FIXTURES_RELATIVE.as_posix(),
    "profile": legacy.PROFILE_RELATIVE.as_posix(), "benchmark": legacy.BENCHMARK_RELATIVE.as_posix(),
    "bundleSchema": "evals/no-hook/bundle-manifest-schema-v1.json",
    "staticBundleEvidence": STATIC_BUNDLE_EVIDENCE_RELATIVE.as_posix(),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NativeObservationError(message)


def _json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=legacy._reject_duplicate_pairs)


def _bytes(document: Any) -> bytes:
    return legacy._canonical_json(document) + b"\n"


def _read(path: Path, maximum: int = legacy.MAX_CONTRACT_BYTES) -> bytes:
    return legacy._read_regular(path, "native non-sensitive input", maximum=maximum)


def _exclusive(path: Path, data: bytes, mode: int = 0o600) -> None:
    """Never overwrite a prior attempt, user object, or partial preparation."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        view = memoryview(data)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise OSError("short native-state write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ordinary_directory(path: Path) -> Path:
    _require(path.is_absolute(), "native paths must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        _require(stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
                 "native directory contains a non-directory or symlink")
    return path


def _protocol(root: Path) -> dict[str, Any]:
    document = _json(_read(root / PROTOCOL_RELATIVE))
    _require(type(document) is dict, "native protocol must be an object")
    _require(document.get("schemaVersion") == "2" and document.get("protocolId") == PROTOCOL_ID,
             "native protocol identity mismatch")
    _require(document.get("protocolDigest") == legacy.self_digest(document, "protocolDigest"),
             "native protocol digest mismatch")
    _require(document.get("caseIds") == list(legacy.EXPECTED_CASE_IDS), "native case order mismatch")
    _require(document.get("discovery") == {
        "mechanism": DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
        "root": "HOME/.agents/skills", "target": "installed-package/skills",
        "noPluginControlOrdinal": 11,
    }, "native discovery contract mismatch")
    _require(document.get("authentication") == {
        "modes": ["independent-official-login", "serial-test-auth-copy"],
        "fileName": AUTH_FILE_NAME, "sourceOrdinal": 1,
        "refreshHandoff": "after-successful-client-exit", "contentRecorded": False,
    }, "native authentication contract mismatch")
    _require(document.get("cli") == {
        "version": legacy.CODEX_VERSION, "sha256": legacy.CODEX_BINARY_SHA256,
        "model": MODEL, "reasoningEffort": REASONING_EFFORT,
    }, "native CLI/model identity mismatch")
    _require(document.get("limits") == {
        "maxCaseLaunches": 16, "timeoutSeconds": 120,
        "stdoutBytes": 1048576, "stderrBytes": 262144,
    }, "native execution limits mismatch")
    _require(document.get("diagnosticRevision") == 11 and document.get("followup") == {
        "priorResultSha256s": ASSESSMENT_PRIOR_RESULTS, "priorAttempts": 20,
        "maximumCumulativeAttempts": 36, "maximumCaseOneAttempts": 9,
        "remainingCaseAttempts": 1,
    }, "native diagnostic migration or retry budget mismatch")
    _require(document.get("diagnostics", {}).get("readRejections", {}).get("codes") == list(EVENT_REJECTIONS),
             "native read rejection vocabulary mismatch")
    _require(document.get("responseTransport") == {
        "revision": 1, "stringConstants": "explicit-type-and-singleton-enum",
        "uniqueRoutes": "local-strict-validation", "annotations": "not-transmitted",
        "preflight": "all-16-derived-files; not-server-acceptance",
    }, "native response transport contract mismatch")
    _require(document.get("toolMode") == {
        "codeModeHost": False, "inProcessFallbackDisabled": False,
        "effectiveRoute": "requires-official-direct-mode; no-code-mode-only-fallback",
        "acceptedNotice": DIRECT_TOOLS_FALLBACK_NOTICE,
        "rejectedNotice": CODE_MODE_FAIL_CLOSED_NOTICE,
        "evidence": "bound-shell-reads; not-code-mode-or-plugin-runtime-observation",
    }, "native direct tool mode contract mismatch")
    _require(document.get("modelMetadata") == {
        "sourceCommit": "41e22fee981a63b3698df7ed36bad393cda24715",
        "embeddedPath": "codex-rs/models-manager/models.json", "model": MODEL,
        "embeddedToolMode": None, "supportsMedium": True,
        "cache": "registered CODEX_HOME/models_cache.json; read only; no explicit refresh",
        "selection": "official cache when present; frozen embedded entry otherwise",
        "checks": "before launch and after exit; inferred Direct under bound feature settings",
        "scope": "new observation combination; not equivalent to historical Sol context",
    }, "native model metadata contract mismatch")
    _require(document.get("executionWindow") == {
        "state": "closed", "lastResultSha256": FIXED_ROUTING_PRIOR,
        "reason": "the original explicit-invocation window is consumed; no reopening",
    }, "native execution window differs from consumed attempt evidence")
    _require(document.get("fixedAcceptance") == FIXED_ACCEPTANCE,
             "fixed candidate acceptance window changed")
    _require(document.get("revisionFourAcceptance") == REVISION_FOUR_ACCEPTANCE,
             "assessment revision 4 acceptance window changed")
    _require(document.get("explicitInvocation") == EXPLICIT_INVOCATION,
             "native explicit invocation contract mismatch")
    _require(document.get("currentAssessment") == CURRENT_ASSESSMENT,
             "current assessment execution contract mismatch")
    _require(document.get("assessmentRemainder") == ASSESSMENT_REMAINDER, "assessment remainder contract mismatch")
    _require(document.get("materialSegment") == MATERIAL_SEGMENT, "material segment contract mismatch")
    _require(document.get("materialDelivery") == MATERIAL_DELIVERY, "native material delivery contract mismatch")
    bindings = list(document.get("implementationBindings", []))
    _require([item.get("path") for item in bindings] == list(IMPLEMENTATION_PATHS),
             "native implementation binding owner set changed")
    inputs = document.get("inputs", {})
    _require(set(inputs) == set(INPUT_PATHS), "native input binding owner set changed")
    for key, relative in INPUT_PATHS.items():
        _require(inputs[key].get("path") == relative, "native input owner changed")
    _require(document.get("resultSchema", {}).get("path") == RESULT_SCHEMA_RELATIVE.as_posix(),
             "native result schema owner changed")
    bindings += list(inputs.values())
    bindings.append(document.get("resultSchema", {}))
    _require(document.get("sameAttemptReview", {}).get("path") == REVIEW_RELATIVE.as_posix(),
             "same-attempt review owner changed")
    bindings.append(document["sameAttemptReview"])
    for binding in bindings:
        _require(type(binding) is dict and set(binding) == {"path", "sha256"},
                 "native file binding must be closed")
        relative = Path(binding["path"])
        _require(not relative.is_absolute() and ".." not in relative.parts,
                 "native binding is not repository-relative")
        _require(hashlib.sha256(_read(root / relative)).hexdigest() == binding["sha256"],
                 "native bound input changed")
    envelope = _json(_read(root / inputs["promptEnvelope"]["path"]))
    _require(envelope.get("assessmentRevision") == 4 and document.get("assessmentRevision") == 4 and
             envelope.get("contractBindings", {}).get("modelResponseSchemaSha256") ==
             inputs["modelResponseSchema"]["sha256"] and
             envelope.get("explicitInvocation") == EXPLICIT_INVOCATION and
             envelope.get("materialDelivery") == MATERIAL_DELIVERY and
             envelope.get("fixtureMatrix") == inputs["fixtureMatrix"] and
             envelope.get("promptEnvelopeDigest") == legacy.self_digest(envelope, "promptEnvelopeDigest"),
             "native material envelope binding mismatch")
    evidence = _json(_read(root / STATIC_BUNDLE_EVIDENCE_RELATIVE))
    bundle = document.get("bundle", {})
    _require(bundle.get("manifestDigest") == evidence["bundleManifest"]["bundleManifestDigest"] and
             bundle.get("archiveSha256") == evidence["builds"]["archiveSha256"] and
             bundle.get("profileRuntimeDigest") == evidence["bundleManifest"]["profileRuntimeDigest"],
             "native bundle references differ from static evidence")
    _require(type(bundle.get("packageSha256")) is str and
             legacy.SHA256_PATTERN.fullmatch(bundle["packageSha256"]) is not None,
             "native package identity is invalid")
    return document


MERGED_ROUTING_SHA256 = "0307ab9a45698a3f4176f21bd30113307c9d3867c0bad069abd87e1c1a98c43a"
MERGED_PROTOCOL_DIGEST = "sha256:756bca702e0ae300407df30324636d27cada3f46c4d9b780661b0eeb171b6bb3"
MERGED_PROTOCOL_FILE_SHA256 = "c6e29b80b64bf50aa7a0424ad99936e493254f3fff464e41b8ed90ca63f26feb"
FIXED_PROTOCOL_FILE_SHA256 = "a3baaf529729f3da8d024536bfb29ef4e28363f17c68b1b75b9ee07cd7c4c674"
FIXED_PROTOCOL_ARCHIVE = Path("evals/no-hook-observation/historical-protocols/fixed-acceptance-1")
REVISION_FOUR_PROTOCOL_ARCHIVE = Path("evals/no-hook-observation/historical-protocols/assessment-revision-4-fixed-1")
REVISION_FOUR_RESULT_SHA256 = "50589ff34c708f77ec119ba456100aa0cbfcfe965f7d85eddfe785c7ee5c023b"


def _merged_protocol(root: Path) -> dict[str, Any]:
    data = _read(root / "evals/no-hook-observation/historical-protocols/codex-native-protocol-v2.json")
    _require(hashlib.sha256(data).hexdigest() == MERGED_PROTOCOL_FILE_SHA256,
             "merged routing protocol bytes changed")
    return _json(data)


def _fixed_protocol(root: Path) -> dict[str, Any]:
    data = _read(root / FIXED_PROTOCOL_ARCHIVE / PROTOCOL_RELATIVE.name)
    _require(hashlib.sha256(data).hexdigest() == FIXED_PROTOCOL_FILE_SHA256,
             "recorded fixed routing protocol bytes changed")
    return _json(data)


def _revision_four_protocol(root: Path) -> dict[str, Any]:
    data = _read(root / REVISION_FOUR_PROTOCOL_ARCHIVE / PROTOCOL_RELATIVE.name)
    _require(hashlib.sha256(data).hexdigest() ==
             "0732cea5d3587f226454f7b3153405ae097d0ae67f758daf6ae5713969b7c97a",
             "recorded revision 4 routing protocol bytes changed")
    return _json(data)


def validate_native_protocol(root: Path = REPOSITORY_ROOT) -> list[str]:
    """Read-only default validation; no detector, process, install or login."""
    try:
        protocol = _protocol(root)
        legacy.load_golden_cases(root)
        legacy.load_codex_benchmark_contract(root)
        _require(protocol["inputs"]["goldenSet"]["path"] == legacy.GOLDEN_SET_RELATIVE.as_posix(),
                 "native Golden Set owner changed")
        _require(protocol["inputs"]["modelResponseSchema"]["path"] ==
                 MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix(), "native model schema owner changed")
        _require(protocol["inputs"]["fixtureMatrix"]["path"] == legacy.FIXTURES_RELATIVE.as_posix(),
                 "native fixture owner changed")
        for ordinal, case in enumerate(legacy.load_golden_cases(root), 1):
            materialize_native_case_contract(root=root, materialization_seed=bytes(32), ordinal=ordinal,
                protocol_digest=protocol["protocolDigest"], model_schema=_input(root, protocol, "modelResponseSchema"),
                prompt_envelope=_input(root, protocol, "promptEnvelope"), request=case["request"])
        history = _json(_read(root / HISTORY_RELATIVE))
        _require(set(history) == {"schemaVersion", "kind", "protocol", "results", "current", "historicalResults", "reviewedPartial", "previousPartial", "historicalBatch", "assessmentPartial", "assessmentRemainder", "materialObservation", "assessmentRevision3", "fixedAcceptance", "revisionFourAcceptance"} and
                 history["schemaVersion"] == "2" and history["kind"] == "axiom-codex-native-result-history" and
                 history["protocol"] == {"path": PROTOCOL_RELATIVE.as_posix(), "digest": MERGED_PROTOCOL_DIGEST},
                 "native history identity is inconsistent")
        historical = history["historicalResults"]
        expected_historical = {"path": "evals/no-hook-observation/results/codex-native-" + HISTORICAL_RESULT_SHA256 + ".json",
            "sha256": HISTORICAL_RESULT_SHA256, "protocolDigest": HISTORICAL_PROTOCOL_DIGEST,
            "implementationCommit": "f7a590ad58e2a1200f64009e48556fa7448f2f86",
            "resultCommit": "5ac4c2b197bd4f3a32a9d50ca2de4814aefcf2c3", "attemptCount": 1}
        retry_sha = "8b6e4a93f6b2edd8c4f4c89f275e3ed023b47ea74b44835cfbf97d77f948c6df"
        expected_retry = {"path": "evals/no-hook-observation/results/codex-native-" + retry_sha + ".json",
            "sha256": retry_sha,
            "protocolDigest": "sha256:0990cdc1ff099e4cdd06f4a9c5f085b050df4adea3a081d19f47533124e0ae35",
            "implementationCommit": "039faf3cc46bebae6823dd21c01bf023d1e2d0e0",
            "resultCommit": "c64b9989bb620807011222f5680e0fd3060406c1", "attemptCount": 1}
        expected_third = {"path": "evals/no-hook-observation/results/codex-native-" + THIRD_RESULT_SHA256 + ".json",
            "sha256": THIRD_RESULT_SHA256, "protocolDigest": THIRD_PROTOCOL_DIGEST,
            "implementationCommit": "07e92135a85523c774cc3cb32499be6d98eee31f",
            "implementationTree": "82d09603eaa18acd415e8972729b5e429255781e",
            "resultCommit": "0e036ed2c34864b85fd6536b2ff5eec9fbcfc813", "attemptCount": 1}
        expected_fourth = {"path": "evals/no-hook-observation/results/codex-native-" + FOURTH_RESULT_SHA256 + ".json",
            "sha256": FOURTH_RESULT_SHA256, "protocolDigest": FOURTH_PROTOCOL_DIGEST,
            "implementationCommit": "23d2d9d3a2e98bc67e74cbcf865cb53a929202eb",
            "implementationTree": "b7ba3d8383f0c25e1af0b76d52a0756bb1acc14b",
            "resultCommit": "5a359ae6e4226fb7ad45935be878bfe871cb0a4f", "attemptCount": 1}
        expected_fifth = {"path": "evals/no-hook-observation/results/codex-native-" + FIFTH_RESULT_SHA256 + ".json",
            "sha256": FIFTH_RESULT_SHA256, "protocolDigest": FIFTH_PROTOCOL_DIGEST,
            "implementationCommit": "c3ce63d789394f60e93687ec34db05be199fbc19",
            "implementationTree": "be21ad749edb25e4fb832bce7debe9e0fa75175b",
            "resultCommit": "cf7c58eeef159a7899fb2a6a2421cd3446bc0c07", "attemptCount": 1}
        expected_sixth = {"path": "evals/no-hook-observation/results/codex-native-" + SIXTH_RESULT_SHA256 + ".json",
            "sha256": SIXTH_RESULT_SHA256, "protocolDigest": SIXTH_PROTOCOL_DIGEST,
            "implementationCommit": "a469930ac2c7a0598f44ed7aee62bcf532220c6a",
            "implementationTree": "8538c2f63771569046540f91dcff7a9f73732fe6",
            "resultCommit": "5fe04cbe7d742096023868150795e2e3580ea67b", "attemptCount": 1}
        expected_seventh = {"path": "evals/no-hook-observation/results/codex-native-" + SEVENTH_RESULT_SHA256 + ".json",
            "sha256": SEVENTH_RESULT_SHA256, "protocolDigest": SEVENTH_PROTOCOL_DIGEST,
            "implementationCommit": "795b70d9bed5be841b03c58a3de31a38d708398b",
            "implementationTree": "5fc888ee4253b6f7824c298ff2c22ae8742b6eeb", "attemptCount": 1}
        _require(historical == [expected_historical, expected_retry, expected_third, expected_fourth, expected_fifth, expected_sixth, expected_seventh],
                 "historical native evidence migration changed")
        for binding in historical:
            _require(hashlib.sha256(_read(root / binding["path"])).hexdigest() == binding["sha256"],
                     "historical native result bytes changed")
        # The exact previously validated bytes retain their old contract. They
        # are not interpreted under the new schema or filled with new facts.
        _require(history["reviewedPartial"] == REVIEWED_PARTIAL_BINDING and
                 history["previousPartial"] == PREVIOUS_PARTIAL_BINDING, "reviewed prefix identity changed")
        _reviewed_partial(root)
        _require(history["historicalBatch"] == ASSESSMENT_PRIOR_BINDING,
                 "historical completed prefix identity changed")
        prior_batch = _assessment_prior(root)
        _require(history["assessmentPartial"] == ASSESSMENT_PARTIAL_BINDING, "assessment prefix binding changed")
        _assessment_partial(root)
        _require(history["assessmentRemainder"] == ASSESSMENT_REMAINDER_BINDING,
                 "stopped assessment remainder binding changed")
        _assessment_remainder_result(root)
        _require(history["materialObservation"] == MATERIAL_OBSERVATION_BINDING,
                 "historical material observation binding changed")
        material_bytes = _read(root / MATERIAL_OBSERVATION_BINDING["path"])
        _require(hashlib.sha256(material_bytes).hexdigest() == MATERIAL_OBSERVATION_BINDING["sha256"],
                 "historical material observation bytes changed")
        material_result = _json(material_bytes)
        _require(material_result["protocolDigest"] == MATERIAL_OBSERVATION_BINDING["protocolDigest"] and
                 material_result["attemptCount"] == material_result["cliLaunchCount"] == 7 and
                 material_result["cumulativeAttemptCount"] == 38,
                 "historical material observation accounting changed")
        _require(history["assessmentRevision3"] == ASSESSMENT_REVISION_THREE,
                 "historical revision-three binding changed")
        revision_three = _read(root / ASSESSMENT_REVISION_THREE["path"])
        _require(hashlib.sha256(revision_three).hexdigest() == ASSESSMENT_REVISION_THREE["sha256"],
                 "historical revision-three result bytes changed")
        prior = _json(revision_three)
        _require(prior["protocolDigest"] == ASSESSMENT_REVISION_THREE["protocolDigest"] and
                 prior["attemptCount"] == prior["cliLaunchCount"] == 16 and
                 prior["cumulativeAttemptCount"] == _attempt_history(root)["attempts"] == 54,
                 "historical revision-three attempt accounting changed")
        # Accepted historical bytes retain their own input meanings and scoring;
        # this no-model wording migration cannot regrade or refund any attempt.
        records = history["results"]
        _require(type(records) is list and len(records) <= 1, "native history permits one current observation")
        current = {"codexObservation": "not-run", "hostClaim": False, "credentialUsed": False,
                   "cliLaunchCount": 0, "modelRequestCount": None, "pluginInstalled": False}
        if records:
            binding = records[0]
            _require(type(binding) is dict and set(binding) == {"path", "sha256", "implementationCommit", "implementationTree"},
                     "native history result reference is not closed")
            for field in ("implementationCommit", "implementationTree"):
                _require(type(binding[field]) is str and re.fullmatch(r"[0-9a-f]{40}", binding[field]) is not None,
                         "native execution implementation identity is invalid")
            relative = Path(binding["path"])
            _require(relative.parent == Path("evals/no-hook-observation/results") and
                     relative.name.startswith("codex-native-") and relative.suffix == ".json",
                     "native history result owner is invalid")
            data = _read(root / relative)
            _require(hashlib.sha256(data).hexdigest() == binding["sha256"], "native history result bytes changed")
            result = _json(data)
            _require(not validate_native_result(result, root), "native history result is invalid")
            _require(result["priorResultSha256s"] == CURRENT_PRIOR_RESULTS,
                     "result does not continue the historical budget")
            _require(result.get("executionSegment", {}).get("kind") == "explicit-invocation-revision-1" and
                     result["cumulativeAttemptCount"] == _attempt_history(root)["attempts"] + result["attemptCount"],
                     "current assessment budget differs from deduplicated history")
            _require(result["runMode"] == "actual", "simulated result is not a host-history observation")
            current = {"codexObservation": result["status"].lower(), "hostClaim": result["hostClaim"],
                       "credentialUsed": result["cliLaunchCount"] > 0, "cliLaunchCount": result["cliLaunchCount"],
                       "modelRequestCount": None, "pluginInstalled": any(
                           item["installation"] == "verified" for item in result["caseResults"])}
        _require(history["current"] == current, "native history summary differs from its result")
        _fixed_result_binding(root)
        _fixed_result_binding(root, revision_four=True)
        return []
    except (OSError, ValueError, KeyError, TypeError, NativeObservationError) as error:
        return [str(error)]


def _assessment_prior(root: Path) -> dict[str, Any]:
    data = _read(root / ASSESSMENT_PRIOR_BINDING["path"])
    _require(hashlib.sha256(data).hexdigest() == ASSESSMENT_PRIOR_SHA256,
             "historical assessment result changed")
    result = _json(data)
    _require(result["priorResultSha256s"] == READ_PRIOR_RESULTS and result["attemptCount"] == 13 and
             result["cumulativeAttemptCount"] == 20 and result["cliLaunchCount"] == 13,
             "historical assessment budget invalid")
    return result  # Exact historical bytes, not reinterpreted by the new inputs.


def _assessment_partial(root: Path) -> dict[str, Any]:
    data = _read(root / ASSESSMENT_PARTIAL_BINDING["path"])
    _require(hashlib.sha256(data).hexdigest() == ASSESSMENT_PARTIAL_BINDING["sha256"],
             "assessment partial result bytes changed")
    result = _json(data)
    _require(result["protocolDigest"] == ASSESSMENT_PROTOCOL_DIGEST and
             result["priorResultSha256s"] == ASSESSMENT_PRIOR_RESULTS and
             result["attemptCount"] == result["cliLaunchCount"] == 10 and
             result["cumulativeAttemptCount"] == 30, "assessment partial budget changed")
    return result  # Previously accepted exact bytes; never regrade under the new protocol.


def _assessment_remainder_result(root: Path) -> dict[str, Any]:
    """Preserve the validated old input/implementation, without regrading it."""
    data = _read(root / ASSESSMENT_REMAINDER_BINDING["path"])
    _require(hashlib.sha256(data).hexdigest() == ASSESSMENT_REMAINDER_BINDING["sha256"],
             "stopped assessment remainder bytes changed")
    result = _json(data)
    _require(result["caseResults"][:10] == _assessment_partial(root)["caseResults"][:10] and
             result["attemptCount"] == result["cliLaunchCount"] == 11 and
             result["cumulativeAttemptCount"] == 31 and
             result["caseResults"][10]["status"] == "INCOMPLETE" and
             all(item["status"] == "NOT-RUN" for item in result["caseResults"][11:]),
             "stopped assessment remainder evidence changed")
    return result


def _verify_assessment_remainder(root: Path, run_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    partial = _assessment_partial(root)
    _ordinary_directory(run_root)
    _require(_read(run_root / "normalized-result.json") == _read(root / ASSESSMENT_PARTIAL_BINDING["path"]),
             "registered assessment partial changed")
    _require(_json(_read(run_root / "batch-started.json")) == {"protocolDigest": ASSESSMENT_PROTOCOL_DIGEST},
             "original assessment stop marker changed")
    for ordinal in range(1, 17):
        marker = run_root / f"attempt-{ordinal:02d}.json"
        if ordinal <= 10:
            _require(_json(_read(marker)) == {"ordinal": ordinal,
                "caseId": legacy.EXPECTED_CASE_IDS[ordinal - 1], "protocolDigest": ASSESSMENT_PROTOCOL_DIGEST},
                "original assessment attempt changed")
        else:
            _require(not marker.exists() and not marker.is_symlink(), "remainder case already attempted")
    for name in ("assessment-remainder-started.json", "normalized-assessment-remainder-result.json"):
        path = run_root / name
        _require(not path.exists() and not path.is_symlink(), "assessment remainder already started")
    binding = _json(_read(run_root / "execution-binding.json"))
    _require(binding == {"implementationCommit": ASSESSMENT_PARTIAL_BINDING["implementationCommit"],
        "implementationTree": ASSESSMENT_PARTIAL_BINDING["implementationTree"],
        "protocolDigest": ASSESSMENT_PROTOCOL_DIGEST, "lifetimeAttemptLimit": 36,
        "modelRequestCount": None, "newAttemptLimit": 16, "priorAttemptCount": 20,
        "priorResultSha256s": ASSESSMENT_PRIOR_RESULTS}, "assessment execution identity changed")
    old = _json(_read(run_root / STATE_NAME))
    _require(old["protocolDigest"] == ASSESSMENT_PROTOCOL_DIGEST and
             old["materializationSeed"] == partial["materializationSeed"], "assessment preparation changed")
    stopped, source = partial["caseResults"][9], partial["caseResults"][8]
    _require(stopped["executionDiagnostics"]["returnCode"] == -9 and
             not stopped["executionDiagnostics"]["cleanupFailed"] and
             stopped["evidenceExtraction"]["postcheck"] == "valid", "prior ordinary cleanup is incomplete")
    facts = source["executionDiagnostics"]
    _require(source["status"] in {"PASS", "FAIL"} and facts["returnCode"] == 0 and
             not any(facts[k] for k in ("cleanupFailed", "observerTerminated", "timedOut")) and
             facts["inputFullyDelivered"] and facts["finalOutputVerified"] and
             source["evidenceExtraction"]["postcheck"] == "valid", "last normal authentication source invalid")
    return partial, old


def prepare_assessment_remainder(root: Path, run_root: Path) -> None:
    """Same retained ledger, only six unstarted independent states; no model or login."""
    partial, old = _verify_assessment_remainder(root, run_root)
    protocol = _protocol(root)
    legacy.freeze_executable(Path(old["executable"]), protocol["cli"]["sha256"])
    materials = []
    fixtures, schema, envelope = (_input(root, protocol, name) for name in
                                  ("fixtureMatrix", "modelResponseSchema", "promptEnvelope"))
    # Preserve old input files; derive all sixteen new bindings without changing their semantics.
    for ordinal, case in enumerate(legacy.load_golden_cases(root), 1):
        paths = _case_paths(run_root, ordinal)
        previous = materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=ASSESSMENT_PROTOCOL_DIGEST, model_schema=schema,
            prompt_envelope=envelope, request=case["request"])
        _require(_read(paths["case"] / "response-schema.json") == previous.schema_bytes,
                 "assessment input schema changed")
        if ordinal >= 11 or ordinal in (9, 10):
            _verify_config(paths, run_root / "marketplace", ordinal != 11)
            _verify_discovery(paths, ordinal != 11)
            _model_metadata(paths)
            fixture = fixture_identity(paths["workspace"], _definition(fixtures, ordinal))
            package = package_identity(paths["package"]) if ordinal != 11 else None
            _require(old["cases"][ordinal - 1] == {"ordinal": ordinal,
                     "fixtureSha256": fixture, "packageSha256": package}, "prepared assessment inputs changed")
        materials.append(materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=protocol["protocolDigest"], model_schema=schema,
            prompt_envelope=envelope, request=case["request"]))
    for ordinal, material in enumerate(materials, 1):
        _exclusive(run_root / f"assessment-remainder-response-schema-{ordinal:02d}.json", material.schema_bytes)
    _exclusive(run_root / "assessment-remainder-preparation.json",
               _bytes({**old, "protocolDigest": protocol["protocolDigest"]}))


def _attempt_history(root: Path) -> dict[str, Any]:
    """Count immutable attempt identities, never add overlapping cumulative snapshots."""
    shas = [*READ_PRIOR_RESULTS, PREVIOUS_PARTIAL_SHA256, REVIEWED_PARTIAL_SHA256,
            ASSESSMENT_PRIOR_SHA256, ASSESSMENT_PARTIAL_BINDING["sha256"],
            ASSESSMENT_REMAINDER_BINDING["sha256"], MATERIAL_OBSERVATION_BINDING["sha256"],
            ASSESSMENT_REVISION_THREE["sha256"]]
    identities: dict[tuple[int, str], tuple[int, int]] = {}
    for digest in shas:
        data = _read(root / ("evals/no-hook-observation/results/codex-native-" + digest + ".json"))
        _require(hashlib.sha256(data).hexdigest() == digest, "attempt history bytes changed")
        document = _json(data)
        for item in document["caseResults"]:
            # This exact pre-attempt-field legacy result has one recorded launch.
            attempts = (int(item["ordinal"] == 1) if digest == HISTORICAL_RESULT_SHA256
                        else item["attemptCount"])
            launches = item["cliLaunchCount"]
            _require(attempts in (0, 1) and 0 <= launches <= attempts, "historical attempt count invalid")
            if not attempts:
                continue
            key = (item["ordinal"], item["materializationCommitmentSha256"])
            counts = (attempts, launches)
            _require(key not in identities or identities[key] == counts, "overlapping attempt counts differ")
            identities[key] = counts
    return {"attempts": sum(item[0] for item in identities.values()),
            "cliLaunches": sum(item[1] for item in identities.values()),
            "identities": [list(key) for key in sorted(identities)], "resultSha256s": shas}


def fixed_attempt_history(root: Path) -> dict[str, Any]:
    """The fixed window inherits every historical attempt, including both replies."""
    old = _attempt_history(root)
    identities = {tuple(key): (1, 1) for key in old["identities"]}
    _require(old["attempts"] == old["cliLaunches"] == len(identities) == 54,
             "routing predecessor accounting changed")
    for index, sha in enumerate(FIXED_PRIOR_RESULTS):
        stem = "codex-native-" if index == 0 else "clarification-"
        data = _read(root / ("evals/no-hook-observation/results/" + stem + sha + ".json"))
        _require(hashlib.sha256(data).hexdigest() == sha, "fixed predecessor bytes changed")
        document = _json(data)
        expected = 16 if index == 0 else 3
        _require(document["attemptCount"] == document["cliLaunchCount"] == expected and
                 document["cumulativeAttemptCount"] == 70 + 3 * index,
                 "fixed predecessor totals changed")
        for item in document["caseResults"]:
            key = (item["ordinal"], item["materializationCommitmentSha256"] if index == 0 else sha)
            _require(key not in identities and item["attemptCount"] == item["cliLaunchCount"] == 1,
                     "fixed predecessor overlaps or is incomplete")
            identities[key] = (1, 1)
    _require(len(identities) == FIXED_ACCEPTANCE["priorAttempts"] == 76,
             "fixed acceptance historical count is not 76")
    return {"attempts": 76, "cliLaunches": 76, "identities": [list(k) for k in sorted(identities)],
            "resultSha256s": FIXED_PRIOR_RESULTS}


def _execution_source(root: Path) -> dict[str, str]:
    """Bind actual committed implementation bytes; never assign a future SHA."""
    env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
    def git(*args):
        owner = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], env=env).decode().strip()
        _require(Path(owner).resolve() == root.resolve(), "execution Git owner changed")
        return subprocess.check_output(["git", "-C", str(root), *args], env=env)
    values = git("rev-parse", "HEAD", "HEAD^{tree}").decode().splitlines()
    protocol = _protocol(root)
    bindings = [*protocol["implementationBindings"], *protocol["inputs"].values(), protocol["resultSchema"]]
    for binding in bindings:
        _require(hashlib.sha256(git("show", values[0] + ":" + binding["path"])).hexdigest() == binding["sha256"],
                 "fixed execution implementation is not committed")
    for relative in (PROTOCOL_RELATIVE, Path("evals/no-hook-observation/clarification-protocol-v1.json")):
        _require(git("show", values[0] + ":" + relative.as_posix()) == _read(root / relative),
                 "fixed execution protocol is not committed")
    return {"commit": values[0], "tree": values[1]}


def _fixed_result_binding(root: Path, *, revision_four: bool = False) -> dict[str, Any] | None:
    history = _json(_read(root / HISTORY_RELATIVE))[_fixed_history_key(revision_four)]
    recorded = _protocol(root) if revision_four else _fixed_protocol(root)
    if revision_four and history["protocolDigest"] != recorded["protocolDigest"]:
        recorded = _revision_four_protocol(root)
    _require(set(history) == {"windowId", "protocolDigest", "results"} and
             history["windowId"] == _fixed_contract(revision_four)["windowId"] and
             history["protocolDigest"] == recorded["protocolDigest"] and
             type(history["results"]) is list and len(history["results"]) <= 1,
             "fixed routing result registration changed")
    if not history["results"]:
        return None
    binding = history["results"][0]
    _require(set(binding) == {"path", "sha256", "implementationCommit", "implementationTree"} and
             binding["path"] == "evals/no-hook-observation/results/codex-native-" + binding["sha256"] + ".json",
             "fixed routing result owner changed")
    data = _read(root / binding["path"])
    _require(hashlib.sha256(data).hexdigest() == binding["sha256"], "fixed routing result bytes changed")
    result = _json(data)
    _require(not validate_native_result(result, root) and result["runMode"] == "actual" and
             result.get("executionSegment", {}).get("kind") == _fixed_kind(revision_four) and
             result["executionSource"] == {"commit": binding["implementationCommit"], "tree": binding["implementationTree"]},
             "fixed routing result is not its actual execution")
    return binding


def revision_four_attempt_history(root: Path) -> dict[str, Any]:
    """Count the stopped eleven-case batch once; its unused slots stay closed."""
    old = fixed_attempt_history(root)
    binding = _fixed_result_binding(root)
    _require(binding is not None and binding["sha256"] == FIXED_RESULT_SHA256,
             "revision 4 predecessor must be the retained stopped batch")
    result = _json(_read(root / binding["path"]))
    identities = {tuple(k): (1, 1) for k in old["identities"]}
    for item in result["caseResults"]:
        if not item["attemptCount"]:
            _require(item["cliLaunchCount"] == 0, "unattempted predecessor launched")
            continue
        key = (item["ordinal"], item["materializationCommitmentSha256"])
        _require(key not in identities and item["attemptCount"] == item["cliLaunchCount"] == 1,
                 "revision 4 predecessor overlaps or changed counts")
        identities[key] = (1, 1)
    _require(len(identities) == result["cumulativeAttemptCount"] == 87,
             "revision 4 historical total is not 87")
    return {"attempts": 87, "cliLaunches": 87, "identities": [list(k) for k in sorted(identities)],
            "resultSha256s": REVISION_FOUR_PRIOR_RESULTS}


def _fixed_attempt_history(root: Path, revision_four: bool) -> dict[str, Any]:
    return revision_four_attempt_history(root) if revision_four else fixed_attempt_history(root)


def _revision_four_auth_source(root: Path, previous: Path, *, revision_four: bool = False) -> dict[str, Any]:
    """Verify only the registered, normally completed source; never inspect auth."""
    binding = _fixed_result_binding(root, revision_four=revision_four)
    expected = REVISION_FOUR_RESULT_SHA256 if revision_four else FIXED_RESULT_SHA256
    _require(binding is not None and binding["sha256"] == expected and
             previous.name == _fixed_contract(revision_four)["routingRunName"], "revision 4 authentication predecessor changed")
    data = _read(root / binding["path"])
    _require(_read(previous / "normalized-result.json") == data, "authentication predecessor result changed")
    result, state = _json(data), _json(_read(previous / STATE_NAME))
    _require(state["protocolDigest"] == result["protocolDigest"] and state["runMode"] == "actual" and
             state["materializationSeed"] == result["materializationSeed"] and
             _json(_read(previous / "batch-started.json")) == {"protocolDigest": result["protocolDigest"]},
             "authentication predecessor preparation changed")
    ordinal = REVISION_FOUR_ACCEPTANCE["authenticationSourceOrdinal"]
    item = result["caseResults"][ordinal - 1]
    _require(_json(_read(previous / f"attempt-{ordinal:02d}.json")) == {
        "ordinal": ordinal, "caseId": item["caseId"], "protocolDigest": result["protocolDigest"]},
        "authentication predecessor attempt changed")
    facts = item["executionDiagnostics"]
    _require(item["status"] in {"PASS", "FAIL"} and facts["category"] == "none" and facts["returnCode"] == 0 and
             facts["inputFullyDelivered"] and facts["finalOutputVerified"] and
             not any(facts[k] for k in ("cleanupFailed", "timedOut", "observerTerminated")) and
             item["evidenceExtraction"]["postcheck"] == "valid", "authentication source did not close normally")
    paths = _case_paths(previous, ordinal)
    _verify_config(paths, previous / "marketplace", True)
    _verify_discovery(paths, True)
    fixtures = _input(root, _protocol(root), "fixtureMatrix")
    _require(fixture_identity(paths["workspace"], _definition(fixtures, ordinal)) == item["fixtureAfterSha256"] and
             package_identity(paths["package"]) == item["packageAfterSha256"], "authentication source public inputs changed")
    _require(not (previous / f"final-message-{ordinal:02d}.json").exists(), "authentication source output remains")
    _model_metadata(paths)
    return state


def _fixed_registration(root: Path, parent: Path, *, revision_four: bool = False) -> dict[str, Any]:
    from . import no_hook_clarification as replies
    contract = _fixed_contract(revision_four)
    record = _json(_read(parent / ("assessment-revision-4-fixed-1.json" if revision_four else FIXED_REGISTRATION)))
    _require(set(record) == {"contract", "nativeProtocolDigest", "clarificationProtocolDigest",
                            "attemptHistory", "executionSource", "previousRunRoot"} and
             record["contract"] == contract and record["attemptHistory"] == _fixed_attempt_history(root, revision_four) and
             record["nativeProtocolDigest"] == _protocol(root)["protocolDigest"] and
             record["clarificationProtocolDigest"] == replies.protocol(root)["protocolDigest"] and
             Path(record["previousRunRoot"]).parent == parent and
             Path(record["previousRunRoot"]).name == (FIXED_ACCEPTANCE["routingRunName"] if revision_four else "cases-clarification-2"),
             "fixed 16-plus-3 registration changed")
    return record


def prepare_fixed_acceptance(root: Path, run_root: Path, previous: Path, bundle_root: Path, *,
                             authorize_install: bool = False, authorize_copy: bool = False,
                             revision_four: bool = False, runner=None) -> None:
    from . import no_hook_clarification as replies
    _require(authorize_install and authorize_copy, "fixed preparation and test-auth copy require authorization")
    contract = _fixed_contract(revision_four)
    _require(_fixed_result_binding(root, revision_four=revision_four) is None, "fixed routing window already recorded")
    replies._unrecorded(root, replies.protocol(root), fixed_acceptance=True, revision_four=revision_four)
    chain = _fixed_attempt_history(root, revision_four)
    old = (_revision_four_auth_source(root, previous) if revision_four else
           replies._prior_state(root, previous, fixed_acceptance=True))
    _require(run_root.parent == previous.parent and run_root.name == contract["routingRunName"] and
             not run_root.exists() and not run_root.is_symlink(), "fixed routing requires its fresh registered sibling")
    source = _execution_source(root) if runner is None else None
    executable = Path(old["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    _require(package_identity(bundle_root) == _protocol(root)["bundle"]["packageSha256"], "fixed package differs")
    invoke = bounded_process if runner is None else runner
    source_ordinal = contract["authenticationSourceOrdinal"] if revision_four else 14
    replies._login(executable, _case_paths(previous, source_ordinal), invoke)
    _exclusive(run_root.parent / ("assessment-revision-4-fixed-1.json" if revision_four else FIXED_REGISTRATION), _bytes({
        "contract": contract, "nativeProtocolDigest": _protocol(root)["protocolDigest"],
        "clarificationProtocolDigest": replies.protocol(root)["protocolDigest"],
        "attemptHistory": chain, "executionSource": source, "previousRunRoot": str(previous)}))
    prepare_native_run(root, run_root, bundle_root, executable, authorize_install=True, runner=runner)
    _exclusive(run_root / "fixed-acceptance-preparation.json", _bytes(_fixed_registration(root, run_root.parent, revision_four=revision_four)))
    _copy_test_auth(run_root, source_ordinal, 1, create=True, source_root=previous)


def _verify_fixed_acceptance(root: Path, run_root: Path, *, revision_four: bool = False) -> dict[str, Any]:
    record = _fixed_registration(root, run_root.parent, revision_four=revision_four)
    _require(run_root.name == _fixed_contract(revision_four)["routingRunName"] and
             _json(_read(run_root / "fixed-acceptance-preparation.json")) == record and
             _fixed_result_binding(root, revision_four=revision_four) is None, "fixed routing preparation changed or window consumed")
    for name in ["batch-started.json", "normalized-result.json", *[f"attempt-{i:02d}.json" for i in range(1, 17)]]:
        _require(not (run_root / name).exists() and not (run_root / name).is_symlink(),
                 "fixed routing already attempted")
    return record["attemptHistory"]


def completed_fixed_routing(root: Path, previous: Path, *, simulated: bool = False, revision_four: bool = False) -> tuple[dict, dict]:
    """Only a fully closed A batch may transfer authentication to B."""
    registration = _fixed_registration(root, previous.parent, revision_four=revision_four)
    contract = _fixed_contract(revision_four)
    _require(previous.name == contract["routingRunName"], "clarification predecessor is not fixed routing")
    data = _read(previous / "normalized-result.json")
    result = _json(data)
    _require(not validate_native_result(result, root) and
             result["runMode"] == ("simulated" if simulated else "actual") and
             result["status"] in ({"INCOMPLETE"} if simulated else {"PASS", "FAIL"}) and
             result.get("executionSegment", {}).get("kind") == _fixed_kind(revision_four) and
             result["attemptCount"] == result["cliLaunchCount"] == 16 and result["cumulativeAttemptCount"] == contract["priorAttempts"] + 16 and
             result["executionSource"] == registration["executionSource"],
             "routing reliability or complete-set prerequisite failed")
    state = _json(_read(previous / STATE_NAME))
    _require(state["protocolDigest"] == result["protocolDigest"] and
             state["materializationSeed"] == result["materializationSeed"] and state["runMode"] == result["runMode"] and
             _json(_read(previous / "batch-started.json")) == {"protocolDigest": result["protocolDigest"]},
             "fixed routing execution markers changed")
    fixtures = _input(root, _protocol(root), "fixtureMatrix")
    for item in result["caseResults"]:
        ordinal = item["ordinal"]
        _require(_json(_read(previous / f"attempt-{ordinal:02d}.json")) == {
            "ordinal": ordinal, "caseId": item["caseId"], "protocolDigest": result["protocolDigest"]},
            "fixed routing attempt marker changed")
        facts = item["executionDiagnostics"]
        _require(item["status"] in {"PASS", "FAIL"} and facts["returnCode"] == 0 and
                 facts["inputFullyDelivered"] and facts["finalOutputVerified"] and
                 not any(facts[k] for k in ("cleanupFailed", "timedOut", "observerTerminated")) and
                 item["evidenceExtraction"]["postcheck"] == "valid", "routing did not close normally")
        paths = _case_paths(previous, ordinal)
        _verify_config(paths, previous / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        _require(fixture_identity(paths["workspace"], _definition(fixtures, ordinal)) == item["fixtureAfterSha256"] and
                 (package_identity(paths["package"]) if ordinal != 11 else None) == item["packageAfterSha256"],
                 "fixed predecessor public inputs changed")
        _require(not (previous / f"final-message-{ordinal:02d}.json").exists(), "routing final output remains")
    chain = {"attempts": contract["priorAttempts"] + 16, "cliLaunches": contract["priorCliLaunches"] + 16,
             "historical": _fixed_attempt_history(root, revision_four),
             "routingResultSha256": hashlib.sha256(data).hexdigest()}
    return state, chain


def _current_assessment_history(root: Path, previous: Path) -> dict[str, Any]:
    """Check the registered normal predecessor without reading client state or secrets."""
    _ordinary_directory(previous)
    data = _read(root / ASSESSMENT_REVISION_THREE["path"])
    _require(hashlib.sha256(data).hexdigest() == ASSESSMENT_REVISION_THREE["sha256"] and
             _read(previous / "normalized-result.json") == data, "registered assessment history changed")
    prior = _json(data)
    old = _json(_read(previous / STATE_NAME))
    _require(old["protocolDigest"] == prior["protocolDigest"] == ASSESSMENT_REVISION_THREE["protocolDigest"] and
             old["materializationSeed"] == prior["materializationSeed"], "historical preparation changed")
    _require(_json(_read(previous / "batch-started.json")) == {"protocolDigest": prior["protocolDigest"]},
             "historical batch marker changed")
    fixtures = _input(root, _protocol(root), "fixtureMatrix")
    for ordinal in range(1, 17):
        marker = previous / f"attempt-{ordinal:02d}.json"
        _require(_json(_read(marker)) == {"ordinal": ordinal,
                 "caseId": legacy.EXPECTED_CASE_IDS[ordinal - 1], "protocolDigest": prior["protocolDigest"]},
                 "historical attempt marker changed")
        record = prior["caseResults"][ordinal - 1]
        facts = record["executionDiagnostics"]
        _require(record["status"] in {"PASS", "FAIL"} and facts["returnCode"] == 0 and
                 not any(facts[k] for k in ("observerTerminated", "timedOut", "cleanupFailed")) and
                 facts["inputFullyDelivered"] and facts["finalOutputVerified"] and
                 record["evidenceExtraction"]["postcheck"] == "valid", "historical ordinary completion incomplete")
        paths = _case_paths(previous, ordinal)
        _verify_config(paths, previous / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        _require(fixture_identity(paths["workspace"], _definition(fixtures, ordinal)) == record["fixtureAfterSha256"] and
                 (package_identity(paths["package"]) if ordinal != 11 else None) == record["packageAfterSha256"],
                 "registered historical inputs changed")
        final = previous / f"final-message-{ordinal:02d}.json"
        _require(not final.exists() and not final.is_symlink(), "historical final output remains")
    return old


def prepare_current_assessment(root: Path, run_root: Path, previous: Path, *,
                               authorize_install: bool = False, authorize_copy: bool = False,
                               runner: Callable[..., Mapping[str, Any]] | None = None) -> None:
    _require(authorize_install and authorize_copy, "explicit assessment install and test-auth copy authorization required")
    _require(runner is not None or _protocol(root)["executionWindow"]["state"] != "closed",
             "actual execution window closed")
    old = _current_assessment_history(root, previous)
    chain = _attempt_history(root)
    _require(chain["attempts"] + CASE_COUNT <= CURRENT_ASSESSMENT["maximumCumulativeAttempts"],
             "assessment cumulative budget exhausted")
    _require(run_root.parent == previous.parent and run_root != previous,
             "assessment must use a fresh registered root under the same owner")
    executable = Path(old["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    source_paths = _case_paths(previous, 16)
    _model_metadata(source_paths)
    invoke = bounded_process if runner is None else runner
    login = invoke([str(executable), "-c", 'cli_auth_credentials_store="file"', "login", "status"],
                   cwd=source_paths["workspace"], env=case_environment(source_paths))
    _require(login["returncode"] == 0 and (login["stdout"] + login["stderr"]).strip() == b"Logged in using ChatGPT",
             "official source login status unavailable")
    prepare_native_run(root, run_root, previous / "marketplace/plugin", executable,
                       authorize_install=True, runner=runner)
    _exclusive(run_root / "current-assessment-preparation.json", _bytes({
        "protocolDigest": _protocol(root)["protocolDigest"], "previousRunRoot": str(previous),
        "contract": CURRENT_ASSESSMENT, "attemptHistory": chain}))
    _copy_test_auth(run_root, 16, 1, create=True, source_root=previous)


def _verify_current_assessment(root: Path, run_root: Path) -> dict[str, Any]:
    record = _json(_read(run_root / "current-assessment-preparation.json"))
    chain = _attempt_history(root)
    _require(set(record) == {"protocolDigest", "previousRunRoot", "contract", "attemptHistory"} and
             record["protocolDigest"] == _protocol(root)["protocolDigest"] and
             record["contract"] == CURRENT_ASSESSMENT and record["attemptHistory"] == chain,
             "current assessment preparation changed")
    previous = Path(record["previousRunRoot"])
    _require(run_root.parent == previous.parent and run_root != previous, "assessment owner changed")
    _current_assessment_history(root, previous)
    for name in ["batch-started.json", "normalized-result.json", *[f"attempt-{i:02d}.json" for i in range(1, 17)]]:
        marker = run_root / name
        _require(not marker.exists() and not marker.is_symlink(), "current assessment already attempted")
    return chain


def _material_history(root: Path, previous: Path) -> dict[str, Any]:
    """Only registered public records and normal input checks; no client internals."""
    _ordinary_directory(previous)
    prior = _assessment_remainder_result(root)
    _require(_read(previous / "normalized-result.json") == _read(root / ASSESSMENT_PARTIAL_BINDING["path"]) and
             _read(previous / "normalized-assessment-remainder-result.json") == _read(root / ASSESSMENT_REMAINDER_BINDING["path"]),
             "registered material history changed")
    for ordinal in range(1, 17):
        marker = previous / f"attempt-{ordinal:02d}.json"
        if ordinal <= 11:
            digest = ASSESSMENT_PROTOCOL_DIGEST if ordinal <= 10 else prior["protocolDigest"]
            _require(_json(_read(marker)) == {"ordinal": ordinal,
                     "caseId": legacy.EXPECTED_CASE_IDS[ordinal - 1], "protocolDigest": digest},
                     "historical attempt marker changed")
        else:
            _require(not marker.exists() and not marker.is_symlink(), "historical later attempt exists")
    for name, digest in (("batch-started.json", ASSESSMENT_PROTOCOL_DIGEST),
                         ("assessment-remainder-started.json", prior["protocolDigest"])):
        _require(_json(_read(previous / name)) == {"protocolDigest": digest}, "historical batch marker changed")
    old = _json(_read(previous / STATE_NAME))
    _require(old["protocolDigest"] == ASSESSMENT_PROTOCOL_DIGEST and
             old["materializationSeed"] == prior["materializationSeed"], "historical preparation changed")
    fixtures = _input(root, _protocol(root), "fixtureMatrix")
    for ordinal in (9, 10, 11):
        record = prior["caseResults"][ordinal - 1]
        facts = record["executionDiagnostics"]
        _require(facts["returnCode"] is not None and not facts["cleanupFailed"] and
                 record["evidenceExtraction"]["postcheck"] == "valid", "historical ordinary cleanup incomplete")
        paths = _case_paths(previous, ordinal)
        _verify_config(paths, previous / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        _require(fixture_identity(paths["workspace"], _definition(fixtures, ordinal)) == record["fixtureAfterSha256"] and
                 (package_identity(paths["package"]) if ordinal != 11 else None) == record["packageAfterSha256"],
                 "registered historical inputs changed")
        final = previous / f"final-message-{ordinal:02d}.json"
        _require(not final.exists() and not final.is_symlink(), "historical final-output cleanup incomplete")
    source = prior["caseResults"][8]
    facts = source["executionDiagnostics"]
    _require(source["status"] in {"PASS", "FAIL"} and facts["returnCode"] == 0 and
             not any(facts[k] for k in ("observerTerminated", "timedOut", "cleanupFailed")) and
             facts["inputFullyDelivered"] and facts["finalOutputVerified"], "authentication source did not exit normally")
    return old


def prepare_material_segment(root: Path, run_root: Path, previous: Path, *,
                             authorize_install: bool = False, authorize_copy: bool = False,
                             runner: Callable[..., Mapping[str, Any]] | None = None) -> None:
    """Fresh case states; reference the stopped ledger without resuming its sessions."""
    _require(authorize_install and authorize_copy, "explicit material preparation and test-auth copy authorization required")
    old = _material_history(root, previous)
    _require(run_root.parent == previous.parent and run_root != previous,
             "material segment must be separately registered under the same test owner")
    executable = Path(old["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    source_paths = _case_paths(previous, 9)
    _model_metadata(source_paths)
    invoke = bounded_process if runner is None else runner
    login = invoke([str(executable), "-c", 'cli_auth_credentials_store="file"', "login", "status"],
                   cwd=source_paths["workspace"], env=case_environment(source_paths))
    _require(login["returncode"] == 0 and (login["stdout"] + login["stderr"]).strip() == b"Logged in using ChatGPT",
             "official source login status unavailable")
    prepare_native_run(root, run_root, previous / "marketplace/plugin", executable,
                       authorize_install=True, runner=runner, material_segment=True)
    _exclusive(run_root / "material-segment-preparation.json", _bytes({
        "protocolDigest": _protocol(root)["protocolDigest"], "previousRunRoot": str(previous),
        "contract": MATERIAL_SEGMENT}))
    _copy_test_auth(run_root, 9, 10, create=True, source_root=previous)


def _verify_material_segment(root: Path, run_root: Path) -> None:
    record = _json(_read(run_root / "material-segment-preparation.json"))
    _require(set(record) == {"protocolDigest", "previousRunRoot", "contract"} and
             record["protocolDigest"] == _protocol(root)["protocolDigest"] and
             record["contract"] == MATERIAL_SEGMENT, "material segment preparation changed")
    previous = Path(record["previousRunRoot"])
    _require(run_root.parent == previous.parent and run_root != previous, "material segment owner changed")
    _material_history(root, previous)
    for ordinal in range(1, 17):
        marker = run_root / f"attempt-{ordinal:02d}.json"
        _require(not marker.exists() and not marker.is_symlink(), "material case already attempted")
    for name in ("batch-started.json", "normalized-result.json"):
        marker = run_root / name
        _require(not marker.exists() and not marker.is_symlink(), "material segment already started")


def _input(root: Path, protocol: Mapping[str, Any], name: str) -> Any:
    binding = protocol["inputs"][name]
    relative = Path(binding["path"])
    # The retained assessment revision shares logical input names with the
    # current measurement. Resolve only its exact, immutable input bindings.
    if name in {"modelResponseSchema", "promptEnvelope"}:
        frozen = _fixed_protocol(root)["inputs"][name]
        if binding == frozen:
            relative = FIXED_PROTOCOL_ARCHIVE / relative.name
    data = _read(root / relative)
    _require(hashlib.sha256(data).hexdigest() == binding["sha256"], "native input bytes changed")
    return _json(data)


def _case_paths(run_root: Path, ordinal: int) -> dict[str, Path]:
    case = run_root / f"case-{ordinal:02d}"
    return {"case": case, "home": case / "client-home", "user": case / "empty-user",
            "workspace": case / "workspace", "state": case / "state", "tmp": case / "tmp",
            "discovery": case / "empty-user/.agents/skills",
            "package": case / "client-home" / "plugins/cache" / legacy.MARKETPLACE_NAME /
            legacy.PLUGIN_NAME / PLUGIN_VERSION}


def _model_metadata(paths: Mapping[str, Path]) -> dict[str, Any]:
    """Read only the registered public model catalog; never refresh or alter it.

    Frozen models.json supplies gpt-5.5/null/medium when no cache exists. With
    CodeMode and CodeModeOnly features disabled, requested_tool_mode resolves
    null to Direct. This is a source-derived mode, not a runtime memory probe.
    The official client may refresh its catalog during execution; check again
    after exit and do not accept a conflicting post-execution catalog.
    """
    cache = paths["home"] / "models_cache.json"
    source, tool_mode = "frozen-embedded", None
    if cache.exists() or cache.is_symlink():
        document = _json(_read(cache, maximum=4 * 1024 * 1024))
        _require(type(document) is dict and document.get("client_version") == legacy.CODEX_VERSION and
                 type(document.get("models")) is list, "official model cache version or shape changed")
        matches = [item for item in document["models"] if type(item) is dict and item.get("slug") == MODEL]
        _require(len(matches) == 1, "official cache does not uniquely describe the fixed model")
        entry = matches[0]
        # Frozen ModelInfo.tool_mode has serde(default) and omits None on write.
        _require(entry.get("tool_mode") in (None, "direct"),
                 "official model metadata does not select Direct")
        levels = entry.get("supported_reasoning_levels")
        _require(type(levels) is list and any(type(level) is dict and
                 level.get("effort") == REASONING_EFFORT for level in levels),
                 "official model metadata does not support the fixed reasoning effort")
        source, tool_mode = "official-cache", entry.get("tool_mode")
    return {"model": MODEL, "metadataSource": source, "toolMode": tool_mode,
            "supportsMedium": True, "derivedEffectiveToolMode": "direct"}


def case_environment(paths: Mapping[str, Path]) -> dict[str, str]:
    """An allowlist, never a filtered copy of the operator's environment."""
    return {"HOME": str(paths["user"]), "CODEX_HOME": str(paths["home"]),
            "XDG_CONFIG_HOME": str(paths["user"] / "config"),
            "XDG_CACHE_HOME": str(paths["user"] / "cache"),
            "XDG_DATA_HOME": str(paths["user"] / "data"),
            "TMPDIR": str(paths["tmp"]), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8", "NO_COLOR": "1", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null", "PYTHONDONTWRITEBYTECODE": "1"}


def _config_args(paths: Mapping[str, Path], executable: Path, marketplace: Path,
                 installed: bool) -> list[str]:
    # Restricted profiles deny everything outside explicit read roots. A deny
    # on client-home itself is a final backend mask, not an overridable parent
    # rule: it would also hide the deliberately allowed installed package.
    filesystem = {":root": "deny", ":minimal": "read", str(executable): "read",
                  str(paths["workspace"]): "read"}
    if installed:
        filesystem[str(paths["package"])] = "read"
    quote = lambda value: json.dumps(value, ensure_ascii=True)
    fs_table = ",".join(f"{quote(key)}={quote(value)}" for key, value in filesystem.items())
    overrides = [
        'cli_auth_credentials_store="file"', 'history.persistence="none"',
        f'sqlite_home={quote(str(paths["state"]))}', f'log_dir={quote(str(paths["state"]))}',
        'model_reasoning_effort="medium"', 'web_search="disabled"', 'mcp_servers={}',
        'skills.bundled.enabled=false',
        'shell_environment_policy.inherit="none"',
        'shell_environment_policy.set={PATH="/usr/bin:/bin",LANG="C.UTF-8",LC_ALL="C.UTF-8"}',
        f'permissions={{native-case={{filesystem={{{fs_table}}},network={{enabled=false}}}}}}',
        'default_permissions="native-case"',
    ]
    for feature in legacy.ACTUAL_CASE_FEATURE_OVERRIDES:
        if feature.split("=", 1)[0] in {"features.web_search_cached", "features.web_search_request"}:
            continue  # Frozen CLI deprecations; top-level web_search stays disabled.
        if feature.startswith("features.shell_tool="):
            feature = "features.shell_tool=true"
        elif feature.startswith("features.skip_host_skill_discovery="):
            feature = "features.skip_host_skill_discovery=false"
        elif feature.startswith("features.plugins="):
            feature = "features.plugins=false"
        overrides.append(feature)
    # remote_plugin=false controls the catalog, not account-installed plugin
    # synchronization. Native user Skill discovery does not need that subsystem.
    overrides.extend(["marketplaces={}", "plugins={}"])
    return [part for override in overrides for part in ("-c", override)]


def validate_response_transport(schema: Mapping[str, Any]) -> None:
    """Check the small Structured Outputs subset this response actually uses.

    This is local preflight, not a claim of server acceptance. No $ref, schema
    combinators or arbitrary schema compilation are needed for this contract.
    """
    allowed = {"object": {"type", "properties", "required", "additionalProperties"},
               "array": {"type", "items", "minItems", "maxItems"},
               "string": {"type", "enum"}, "integer": {"type", "minimum", "maximum"},
               "boolean": {"type"}}
    def check(node: Any) -> None:
        _require(type(node) is dict and type(node.get("type")) is str and node["type"] in allowed,
                 "response transport node requires an explicit supported type")
        kind = node["type"]
        _require(set(node) <= allowed[kind], "unsupported response transport keyword")
        if kind == "object":
            props, required = node.get("properties"), node.get("required")
            _require(type(props) is dict and type(required) is list and
                     all(type(key) is str for key in required) and
                     len(required) == len(set(required)) and set(required) == set(props) and
                     node.get("additionalProperties") is False, "response transport object is not closed")
            for child in props.values():
                check(child)
        elif kind == "array":
            check(node.get("items"))
            _require(type(node.get("minItems")) is int and type(node.get("maxItems")) is int and
                     0 <= node["minItems"] <= node["maxItems"], "invalid transport array bounds")
        elif kind == "integer":
            _require(type(node.get("minimum")) is int and type(node.get("maximum")) is int and
                     node["minimum"] <= node["maximum"], "invalid transport integer bounds")
        elif kind == "string":
            values = node.get("enum")
            _require(type(values) is list and len(values) > 0 and all(type(value) is str for value in values) and
                     len(values) == len(set(values)), "invalid transport string enumeration")
    check(schema)
    _require(schema["type"] == "object", "response transport root must be an object")


def bound_native_skill_catalog(root: Path) -> list[dict[str, Any]]:
    """Reconstruct names only for this bound, single-package user discovery root.

    Frozen loader/host.rs canonicalizes the discovery root, and namespace.rs
    uses the nearest package manifest. Do not use interface.display_name or
    the no-Hook output vocabulary as host names. Installation and the alias
    are separately checked before any client execution.
    """
    manifest = _json(_read(root / STATIC_BUNDLE_EVIDENCE_RELATIVE))["bundleManifest"]
    namespace = manifest["derivedPluginManifest"]["fields"]["name"]
    _require(type(namespace) is str and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", namespace),
             "unsupported bound Skill namespace")
    records = []
    for item in manifest["runtimeFiles"]:
        if item["kind"] != "skill":
            continue
        relative = item["path"]
        _require(re.fullmatch(r"skills/[a-z0-9-]+/SKILL\.md", relative), "unsupported bound Skill path")
        raw = _read(root / relative)
        _require(hashlib.sha256(raw).hexdigest() == item["sha256"], "bound Skill source bytes changed")
        name = parse_skill_frontmatter_document(raw.decode("utf-8"), relative)["name"]
        _require(name == Path(relative).parent.name, "bound Skill basename differs from its path")
        records.append({"name": namespace + ":" + name, "localName": name,
                        "path": relative, "sha256": item["sha256"], "enabled": True})
    _require(len({item["name"] for item in records}) == len(records), "ambiguous bound host Skill names")
    return records


def explicit_skill_selection(request: str, catalog: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Translate only a literal invocation at the start of the inner request.

    This deliberately small English invocation grammar does not route intent.
    It neither searches fixture/assessment text nor examines expected results.
    Skill names stay case-sensitive even though the leading command words are
    case-insensitive. Unrecognized sentence forms receive no added selection.
    """
    match = re.match(r"\A(?:(?i:Invoke) (?P<invoke>[A-Za-z0-9_:-]+) (?:(?i:explicitly) )?(?i:to)\b|"
                     r"(?i:Use the) (?P<use>[A-Za-z0-9_:-]+) (?i:Skill to)\b)", request)
    if match is None or not catalog:
        return None
    name = match.group("invoke") or match.group("use")
    matches = [item for item in catalog if item.get("enabled") is True and
               name in (item.get("name"), item.get("localName"))]
    _require(len(matches) == 1, "explicit Skill name is not uniquely bound")
    item = matches[0]
    _require(re.fullmatch(r"[a-z0-9-]+:[a-z0-9-]+", item["name"]) is not None and
             sum(entry.get("enabled") is True and entry.get("name") == item["name"] for entry in catalog) == 1,
             "explicit host Skill name is not uniquely selectable")
    mention = "$" + item["name"]
    return {"revision": 1, "requestSha256": hashlib.sha256(request.encode("utf-8")).hexdigest(),
            "hostName": item["name"], "skillPath": item["path"], "skillSha256": item["sha256"],
            "mentionSha256": hashlib.sha256(mention.encode("utf-8")).hexdigest()}


def _case_explicit_selection(root: Path, request: str, ordinal: int, *,
                             protocol_digest: str | None = None) -> dict[str, Any] | None:
    # Availability comes from the independently bound fixture/discovery mode,
    # not the ordinal, expected route or expected discovery outcome.
    fixtures = _json(_read(root / legacy.FIXTURES_RELATIVE))
    _definition(fixtures, ordinal)  # Validate the same bound fixture/discovery record as production.
    installed = fixtures["cases"][ordinal - 1]["pluginState"] == "installed-derived-profile"
    if installed and protocol_digest == MERGED_PROTOCOL_DIGEST:
        # Reconstruct the completed assessment's selection identity from its
        # immutable package inventory, never the revised candidate's Skill hash.
        prior = _merged_protocol(root)
        data = _read(root / "evidence/profiles/openai-hook-independent-v1/bundle-revision-9.json")
        _require(hashlib.sha256(data).hexdigest() == prior["inputs"]["staticBundleEvidence"]["sha256"],
                 "historical selection package evidence changed")
        manifest = _json(data)["bundleManifest"]
        namespace = manifest["derivedPluginManifest"]["fields"]["name"]
        catalog = [{"name": namespace + ":" + Path(item["path"]).parent.name,
                    "localName": Path(item["path"]).parent.name, "path": item["path"],
                    "sha256": item["sha256"], "enabled": True}
                   for item in manifest["runtimeFiles"] if item["kind"] == "skill"]
    else:
        catalog = bound_native_skill_catalog(root) if installed else []
    return explicit_skill_selection(request, catalog)


def materialize_native_case_contract(*, root: Path = REPOSITORY_ROOT, **arguments: Any) -> legacy.CaseMaterialization:
    """Adapt only known response fields; retain the frozen local acceptance schema.

    Explicit string types and singleton enums carry the same values. uniqueItems
    has no supported transport representation and remains mandatory in the local
    strict validator. Material delivery is a separately versioned input layer;
    old envelopes without it retain their original prompt bytes.
    """
    envelope = arguments["prompt_envelope"]
    if envelope.get("assessmentRevision") in {3, 4}:
        fields = ("selectedRoutes", "discoveryOutcome", "clarificationCount")
        if envelope["assessmentRevision"] == 4:
            fields += ("usingAxiomFrontDoorObserved",)
        for field in fields:
            definition = arguments["model_schema"]["properties"][field].get("description")
            _require(type(definition) is str and definition and
                     envelope["fixedInstructions"].count(definition) == 1,
                     "native assessment field definitions are not uniformly delivered")
    material = legacy.materialize_case_contract(**arguments)
    delivery = envelope.get("materialDelivery")
    if delivery is not None:
        _require(delivery == MATERIAL_DELIVERY and envelope.get("assessmentRevision") in {2, 3, 4},
                 "unsupported material delivery revision")
        binding = envelope["fixtureMatrix"]
        _require(set(binding) == {"path", "sha256"} and
                 binding["path"] == legacy.FIXTURES_RELATIVE.as_posix(),
                 "material fixture owner changed")
        fixture_bytes = _read(root / legacy.FIXTURES_RELATIVE)
        _require(hashlib.sha256(fixture_bytes).hexdigest() == binding["sha256"],
                 "material fixture binding changed")
        definition = _definition(_json(fixture_bytes), arguments["ordinal"])
        paths = sorted((record["path"] for record in definition["files"]), key=lambda value: value.encode("utf-8"))
        # Only explicit task data is listed. No generated .git metadata, package
        # inventory, client state, absolute roots, file contents or answer facts.
        location = ("\nTask materials:\n"
                    "Paths are relative to the current working directory and identify supplied task data only, "
                    "not installed Skills or the host discovery catalog. An empty list says nothing about Skill installation.\n"
                    "taskMaterialPaths: " + json.dumps(paths, ensure_ascii=True) + "\n")
        prefix, marker, request = material.prompt_bytes.partition(b"\nUser request:\n")
        _require(bool(marker), "native request boundary missing")
        prompt = prefix + location.encode("utf-8") + marker + request
        material = replace(material, prompt_bytes=prompt, prompt_sha256=hashlib.sha256(prompt).hexdigest())
    invocation = envelope.get("explicitInvocation")
    if invocation is not None:
        _require(invocation == EXPLICIT_INVOCATION, "unsupported explicit invocation transport")
        selection = _case_explicit_selection(root, arguments["request"], arguments["ordinal"],
                                             protocol_digest=arguments["protocol_digest"])
        if selection is not None:
            prefix, marker, request = material.prompt_bytes.partition(b"\nUser request:\n")
            _require(bool(marker), "native request boundary missing")
            transport = ("\nHost explicit Skill selection from the inner request: $" + selection["hostName"] +
                         "\nThis transports the user's named invocation; it grants no task execution authority.\n")
            prompt = prefix + transport.encode("utf-8") + marker + request
            material = replace(material, prompt_bytes=prompt, prompt_sha256=hashlib.sha256(prompt).hexdigest())
    schema = _json(material.schema_bytes)
    for annotation in ("$schema", "$id", "title"):
        schema.pop(annotation, None)
    props = schema["properties"]
    string_nodes = [props["profileId"], props["opaqueCaseBinding"], props["discoveryOutcome"],
                    props["selectedRoutes"]["items"],
                    *(props["contractBindings"]["properties"][key] for key in
                      ("profileContractSha256", "goldenSetSha256", "hostCaseSetSha256"))]
    for node in string_nodes:
        _require(node.get("type", "string") == "string", "known response field changed type")
        node["type"] = "string"
        if "const" in node:
            _require(type(node["const"]) is str and "enum" not in node, "invalid response string constant")
            node["enum"] = [node.pop("const")]
    _require(props["selectedRoutes"].pop("uniqueItems") is True, "local route uniqueness changed")
    # Model-side definitions are uniformly delivered by the bound envelope;
    # these local schema annotations are documentation, not API keywords.
    for field in ("selectedRoutes", "discoveryOutcome", "clarificationCount", "usingAxiomFrontDoorObserved"):
        props[field].pop("description", None)
    validate_response_transport(schema)
    data = _bytes(schema)
    return replace(material, schema_bytes=data, schema_sha256=hashlib.sha256(data).hexdigest())


def _validate_native_response(value: Any, source_schema: Mapping[str, Any], token: str) -> None:
    strict = _json(legacy.materialize_model_response_schema(source_schema, token))
    legacy._validate_schema_value(value, strict, strict, "native structured response")


def build_native_argv(executable: Path, run_root: Path, ordinal: int, *,
                      response_schema: Path | None = None, final_output: Path | None = None) -> list[str]:
    _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "unknown native case ordinal")
    paths = _case_paths(run_root, ordinal)
    return [str(executable), "--ask-for-approval", "never", "exec", "--ephemeral", "--json", "--model", MODEL,
            "--skip-git-repo-check", "--ignore-user-config",
            "--ignore-rules", "--cd", str(paths["workspace"]),
            "--output-schema", str(response_schema if response_schema is not None else paths["case"] / "response-schema.json"),
            *(["--output-last-message", str(final_output)] if final_output is not None else []),
            *_config_args(paths, executable, run_root / "marketplace", ordinal != 11), "-"]


def _close_process(process: subprocess.Popen, *, terminate: bool, facts: dict[str, Any]) -> None:
    """Ordinary process-group cleanup; record failure separately from first cause."""
    if process.poll() is None or terminate:
        try:
            os.killpg(process.pid, signal.SIGINT)
            facts["observerTerminated"] = True
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                facts["observerTerminated"] = True
            except ProcessLookupError:
                pass
            process.wait(timeout=2)


def bounded_process(argv: Sequence[str], *, cwd: Path, env: Mapping[str, str],
                    stdin: bytes = b"", line_callback: Callable[[bytes], None] | None = None,
                    started_callback: Callable[[], None] | None = None,
                    timeout: int = 120) -> dict[str, Any]:
    """Capture bounded facts before discarding buffers, including on failure."""
    output, errors, pending = bytearray(), bytearray(), bytearray()
    facts = _diagnostics()
    sent = 0
    try:
        process = subprocess.Popen(list(argv), cwd=cwd, env=dict(env), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True, close_fds=True)
    except OSError:
        _first_failure(facts, "launch", "process-start")
        raise NativeDiagnosticError(facts) from None
    selector = None
    try:
        if started_callback is not None:
            started_callback()
        selector = selectors.DefaultSelector()
        assert process.stdin is not None and process.stdout is not None and process.stderr is not None
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        if stdin:
            selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
        else:
            process.stdin.close()
        deadline = time.monotonic() + timeout
        while selector.get_map():
            if time.monotonic() >= deadline:
                raise TimeoutError()
            for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                if key.data == "stdin":
                    sent += os.write(key.fd, stdin[sent:sent + 8192])
                    if sent == len(stdin):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                target = output if key.data == "stdout" else errors
                limit = legacy.MAX_STDOUT_BYTES if key.data == "stdout" else legacy.MAX_STDERR_BYTES
                target.extend(chunk)
                if len(target) > limit:
                    _first_failure(facts, "io", "output-limit")
                    raise NativeDiagnosticError(facts)
                if key.data == "stdout" and line_callback is not None:
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending[:] = rest
                        try:
                            line_callback(bytes(line))
                        except NativeDiagnosticError as error:
                            _first_failure(facts, error.facts["phase"], error.facts["category"])
                            for field in ("eventCount", "eventTypes", "itemTypes", "policyReason",
                                          "diagnosticItemCount", "preTurnDiagnosticCount", "hostDiagnosticClasses",
                                          "streamAssertion", "streamEventOrdinal"):
                                facts[field] = error.facts[field]
                            raise
                        except Exception:
                            _first_failure(facts, "event", "policy-rejected")
                            raise NativeDiagnosticError(facts) from None
                    if len(pending) > legacy.MAX_JSONL_LINE_BYTES:
                        _first_failure(facts, "io", "output-limit")
                        raise NativeDiagnosticError(facts)
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if sent != len(stdin):
            _first_failure(facts, "io", "input-incomplete")
    except (TimeoutError, subprocess.TimeoutExpired):
        facts["timedOut"] = True
        _first_failure(facts, "io", "timeout")
    except NativeDiagnosticError:
        pass
    except (OSError, ValueError, NativeObservationError):
        _first_failure(facts, "io", "io-failed")
    finally:
        if process.poll() is not None and process.returncode != 0:
            _first_failure(facts, "exit", "process-exit")
        try:
            _close_process(process, terminate=facts["category"] != "none", facts=facts)
        except (OSError, subprocess.SubprocessError):
            facts["cleanupFailed"] = True
            _first_failure(facts, "cleanup", "cleanup-failed")
        try:
            if selector is not None:
                selector.close()
        except OSError:
            facts["cleanupFailed"] = True
            _first_failure(facts, "cleanup", "cleanup-failed")
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                facts["cleanupFailed"] = True
                _first_failure(facts, "cleanup", "cleanup-failed")
    facts.update(inputBytesSent=sent, inputFullyDelivered=sent == len(stdin))
    capture = {"returncode": process.returncode, "stdout": bytes(output), "stderr": bytes(errors),
               "diagnostics": facts}
    closed = _capture_facts(capture)
    # Nonzero exits and stderr are classified by the caller (login has its own
    # exact status grammar); capture/cleanup failures cannot lose their facts.
    if facts["category"] != "none":
        raise NativeDiagnosticError(closed, capture={**capture, "diagnostics": closed}) from None
    capture["diagnostics"] = facts
    return capture


def _definition(fixtures: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    case = fixtures["cases"][ordinal - 1]
    _require(case["caseId"] == legacy.EXPECTED_CASE_IDS[ordinal - 1], "fixture case order changed")
    definition = next(item for item in fixtures["definitions"] if item["templateId"] == case["workspaceTemplate"])
    legacy._validate_fixture_definition(definition)
    return definition


def materialize_fixture(workspace: Path, definition: Mapping[str, Any]) -> str:
    _require(not any(workspace.iterdir()), "native fixture workspace must be empty")
    files = {record["path"]: record["contentUtf8"].encode("utf-8") for record in definition["files"]}
    if definition["git"]["repository"]:
        for relative in (".git", ".git/objects", ".git/refs", ".git/refs/heads", ".git/info"):
            (workspace / relative).mkdir(exist_ok=True)
        files.update({".git/HEAD": b"ref: refs/heads/main\n",
                      ".git/config": b"[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tfilemode = true\n",
                      ".git/info/exclude": b"*\n"})
    for relative, data in files.items():
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _exclusive(path, data, 0o444)
    return fixture_identity(workspace, definition)


def fixture_identity(workspace: Path, definition: Mapping[str, Any]) -> str:
    legacy._fixture_observed_records(workspace, definition)
    legacy._observe_inert_git_facts(workspace, definition["git"]["repository"])
    return legacy._expected_realized_fixture_digest(definition)


def package_identity(package: Path) -> str:
    """Inspect only the selected public package, never its containing home."""
    _ordinary_directory(package)
    expected = _json(_read(REPOSITORY_ROOT / STATIC_BUNDLE_EVIDENCE_RELATIVE))["bundleManifest"]
    runtime = _json(_read(REPOSITORY_ROOT / "evidence/runtime-identity.json"))
    records = legacy._verify_bundle_surface(package, fake_only=False, expected_identity={
        "pluginVersion": PLUGIN_VERSION, "fullProfileDigest": runtime["runtimeContract"]["digest"],
        "profileRuntimeDigest": expected["profileRuntimeDigest"],
        "bundleManifestDigest": expected["bundleManifestDigest"],
        "runtimeBytes": sum(item["size"] for item in expected["runtimeFiles"]),
    })
    manifest = _json(_read(package / "BUNDLE-MANIFEST.json"))
    by_path = {path: (mode, size, digest) for path, mode, size, digest in records}
    for expected in manifest["runtimeFiles"]:
        _require(by_path[expected["path"]] == (0o644, expected["size"], expected["sha256"]),
                 "installed runtime bytes differ from the source-bound manifest")
    return hashlib.sha256(legacy._canonical_json(records)).hexdigest()


def _successful(capture: Mapping[str, Any], purpose: str) -> bytes:
    facts = _capture_facts(capture)
    if facts["category"] != "none":
        raise NativeDiagnosticError(facts)
    return capture["stdout"]


def _verify_config(paths: Mapping[str, Path], marketplace: Path, installed: bool) -> None:
    """This one non-sensitive TOML file is the only client-home config read."""
    config_path = paths["home"] / "config.toml"
    if not installed:
        _require(not config_path.exists() and not (paths["home"] / "plugins").exists(),
                 "no-plugin control has unexpected discovery configuration")
        return
    document = tomllib.loads(_read(config_path).decode("utf-8"))
    _require(set(document) <= {"marketplaces", "plugins"}, "test config contains unowned settings")
    _require(document.get("marketplaces") == {
        legacy.MARKETPLACE_NAME: {"source_type": "local", "source": str(marketplace)}
    }, "test config marketplace differs from verified source")
    plugins = document.get("plugins", {})
    _require(set(plugins) == {legacy.PLUGIN_ID} and plugins[legacy.PLUGIN_ID] == {"enabled": True},
             "test config contains an unverified plugin")


def _verify_discovery(paths: Mapping[str, Path], installed: bool) -> None:
    """Bind the standard user Skill root to public installed bytes, not auth."""
    alias = paths["discovery"]
    if not installed:
        _require(not alias.exists() and not alias.is_symlink(),
                 "no-plugin control has an unexpected Skill discovery root")
        return
    _ordinary_directory(alias.parent)
    _require(alias.is_symlink() and os.readlink(alias) == str(paths["package"] / "skills") and
             alias.resolve(strict=True) == paths["package"] / "skills",
             "native Skill discovery no longer names the verified installed package")


def prepare_native_run(root: Path, run_root: Path, bundle_root: Path, executable: Path, *,
                       authorize_install: bool = False,
                       runner: Callable[..., Mapping[str, Any]] | None = None,
                       material_segment: bool = False) -> dict[str, Any]:
    """Prepare once, before login. Failed preparations are retained, never retried."""
    _require(authorize_install is True, "explicit local-install authorization is required")
    protocol = _protocol(root)
    executable_identity = legacy.freeze_executable(executable, protocol["cli"]["sha256"])
    expected_package = package_identity(bundle_root)
    _require(expected_package == protocol["bundle"]["packageSha256"], "native package identity is not protocol-bound")
    _ordinary_directory(run_root.parent)
    _require(not run_root.exists() and not run_root.is_symlink(), "native test root already exists")
    _require(not run_root.is_relative_to(root.resolve()), "native test root must be repository-external")
    run_root.mkdir(mode=0o700)
    actual = runner is None
    invoke = bounded_process if runner is None else runner
    _exclusive(run_root / "preparation-started.json", _bytes({"protocolDigest": protocol["protocolDigest"]}))
    marketplace = run_root / "marketplace"
    (marketplace / ".agents/plugins").mkdir(parents=True)
    # The frozen client's local-source contract requires a normalized path
    # within this marketplace, not an absolute path to the build output.
    shutil.copytree(bundle_root, marketplace / "plugin")
    _require(package_identity(marketplace / "plugin") == expected_package,
             "marketplace copy differs from the verified bundle")
    _exclusive(marketplace / ".agents/plugins/marketplace.json", _bytes({
        "name": legacy.MARKETPLACE_NAME, "interface": {"displayName": "Axiom no-Hook observer"},
        "plugins": [{"name": legacy.PLUGIN_NAME,
                     "source": {"source": "local", "path": "./plugin"},
                     "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     "category": "Productivity"}],
    }))
    seed = legacy.create_materialization_seed()
    cases = legacy.load_golden_cases(root)
    fixtures = _input(root, protocol, "fixtureMatrix")
    model_schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    prepared = []
    for ordinal, case in enumerate(cases, 1):
        paths = _case_paths(run_root, ordinal)
        for name in ("case", "home", "user", "workspace", "state", "tmp"):
            paths[name].mkdir(mode=0o700)
        for name in ("config", "cache", "data"):
            (paths["user"] / name).mkdir(mode=0o700)
        fixture = materialize_fixture(paths["workspace"], _definition(fixtures, ordinal))
        materialized = materialize_native_case_contract(
            root=root,
            materialization_seed=seed, ordinal=ordinal, protocol_digest=protocol["protocolDigest"],
            model_schema=model_schema, prompt_envelope=envelope, request=case["request"])
        _exclusive(paths["case"] / "response-schema.json", materialized.schema_bytes)
        installed = ordinal != 11 and (not material_segment or ordinal >= 10)
        if installed:
            legacy.recheck_executable(executable_identity)
            receipt = _json(_successful(invoke(legacy.build_marketplace_add_argv(executable, marketplace),
                cwd=paths["workspace"], env=case_environment(paths)), "marketplace registration"))
            _require(receipt == {"marketplaceName": legacy.MARKETPLACE_NAME,
                                "installedRoot": str(marketplace), "alreadyAdded": False},
                     "marketplace receipt does not bind the selected local source")
            receipt = _json(_successful(invoke(legacy.build_plugin_add_argv(executable),
                cwd=paths["workspace"], env=case_environment(paths)), "plugin installation"))
            _require(set(receipt) == {"pluginId", "name", "marketplaceName", "version", "installedPath", "authPolicy"},
                     "plugin receipt is not closed")
            for key, expected in {"pluginId": legacy.PLUGIN_ID, "name": legacy.PLUGIN_NAME,
                                  "marketplaceName": legacy.MARKETPLACE_NAME,
                                  "version": PLUGIN_VERSION,
                                  "installedPath": str(paths["package"])}.items():
                _require(receipt[key] == expected, "plugin receipt differs from expected cache object")
            _require(receipt["authPolicy"] in {"ON_INSTALL", "ON_USE"}, "unknown plugin authentication policy")
            _require(package_identity(paths["package"]) == expected_package, "installed plugin differs from verified bundle")
            paths["discovery"].parent.mkdir(mode=0o700)
            paths["discovery"].symlink_to(paths["package"] / "skills", target_is_directory=True)
        _verify_config(paths, marketplace, installed)
        _verify_discovery(paths, installed)
        prepared.append({"ordinal": ordinal, "fixtureSha256": fixture,
                         "packageSha256": expected_package if installed else None})
    state = {"schemaVersion": "2", "protocolDigest": protocol["protocolDigest"],
             "runMode": "actual" if actual else "simulated", "executable": str(executable),
             "materializationSeed": seed.hex(), "cases": prepared}
    _exclusive(run_root / STATE_NAME, _bytes(state))
    return state


def _state(root: Path, run_root: Path, *, followup: bool = False, continuation: bool = False, operator_diagnostics: bool = False, schema_followup: bool = False, model_followup: bool = False, stderr_followup: bool = False, read_followup: bool = False, resume_stderr_review: bool = False, assessment_remainder: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    _ordinary_directory(run_root)
    protocol = _protocol(root)
    state = _json(_read(_ledger(run_root, followup, continuation, operator_diagnostics, schema_followup, model_followup, stderr_followup, read_followup) / ("catalog-preparation.json" if resume_stderr_review else "preparation.json")
                        if followup or continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup else run_root / ("assessment-remainder-preparation.json" if assessment_remainder else STATE_NAME)))
    _require(set(state) == {"schemaVersion", "protocolDigest", "runMode", "executable", "materializationSeed", "cases"},
             "native preparation record is not closed")
    _require(state["schemaVersion"] == "2" and state["protocolDigest"] == protocol["protocolDigest"],
             "prepared input identity changed")
    _require(state["runMode"] in {"actual", "simulated"}, "unknown preparation source")
    _require(type(state["cases"]) is list and len(state["cases"]) == 16, "incomplete preparation")
    for ordinal, item in enumerate(state["cases"], 1):
        _require(set(item) == {"ordinal", "fixtureSha256", "packageSha256"} and item["ordinal"] == ordinal,
                 "prepared case records are not canonical")
    _require(len(bytes.fromhex(state["materializationSeed"])) == 32, "invalid materialization seed")
    return protocol, state


def _verify_prior_attempt(run_root: Path) -> None:
    """Only the explicitly authorized, immutable first failure is retryable."""
    _require(hashlib.sha256(_read(run_root / "normalized-result.json")).hexdigest() ==
             HISTORICAL_RESULT_SHA256, "followup requires the original incomplete result")
    _require(_json(_read(run_root / "batch-started.json")) ==
             {"protocolDigest": HISTORICAL_PROTOCOL_DIGEST}, "historical batch marker changed")
    _require(_json(_read(run_root / "attempt-01.json")) == {
        "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0],
        "protocolDigest": HISTORICAL_PROTOCOL_DIGEST}, "historical attempt marker changed")
    for ordinal in range(2, 17):
        path = run_root / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _ledger(run_root: Path, followup: bool, continuation: bool, operator_diagnostics: bool = False, schema_followup: bool = False, model_followup: bool = False, stderr_followup: bool = False, read_followup: bool = False) -> Path:
    _require(sum((followup, continuation, operator_diagnostics, schema_followup, model_followup, stderr_followup, read_followup)) <= 1, "select exactly one continuation ledger")
    if read_followup:
        return run_root / "read-contract-continuation"
    if stderr_followup:
        return run_root / "stderr-diagnostic-continuation"
    if model_followup:
        return run_root / "model-migration-continuation"
    if schema_followup:
        return run_root / "schema-correction-continuation"
    if operator_diagnostics:
        return run_root / "operator-diagnostic-continuation"
    return run_root / "diagnostic-continuation" if continuation else (
        run_root / "diagnostic-followup" if followup else run_root)


def _verify_two_prior_attempts(run_root: Path) -> None:
    _verify_prior_attempt(run_root)
    prior = run_root / "diagnostic-followup"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             RETRY_RESULT_SHA256, "continuation requires the second immutable incomplete result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": RETRY_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": RETRY_PROTOCOL_DIGEST},
             "second historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _verify_three_prior_attempts(run_root: Path) -> None:
    _verify_two_prior_attempts(run_root)
    prior = run_root / "diagnostic-continuation"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             THIRD_RESULT_SHA256, "operator continuation requires the third immutable incomplete result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": THIRD_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": THIRD_PROTOCOL_DIGEST},
             "third historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _verify_four_prior_attempts(run_root: Path) -> None:
    _verify_three_prior_attempts(run_root)
    prior = run_root / "operator-diagnostic-continuation"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             FOURTH_RESULT_SHA256, "schema followup requires the fourth immutable result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": FOURTH_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": FOURTH_PROTOCOL_DIGEST},
             "fourth historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _verify_five_prior_attempts(run_root: Path) -> None:
    _verify_four_prior_attempts(run_root)
    prior = run_root / "schema-correction-continuation"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             FIFTH_RESULT_SHA256, "model migration requires the fifth immutable result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": FIFTH_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": FIFTH_PROTOCOL_DIGEST},
             "fifth historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _verify_six_prior_attempts(run_root: Path) -> None:
    _verify_five_prior_attempts(run_root)
    prior = run_root / "model-migration-continuation"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             SIXTH_RESULT_SHA256, "stderr followup requires the sixth immutable result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": SIXTH_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": SIXTH_PROTOCOL_DIGEST},
             "sixth historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _verify_seven_prior_attempts(run_root: Path) -> None:
    _verify_six_prior_attempts(run_root)
    prior = run_root / "stderr-diagnostic-continuation"
    _require(hashlib.sha256(_read(prior / "normalized-result.json")).hexdigest() ==
             SEVENTH_RESULT_SHA256, "read followup requires the seventh immutable result")
    _require(_json(_read(prior / "batch-started.json")) == {"protocolDigest": SEVENTH_PROTOCOL_DIGEST} and
             _json(_read(prior / "attempt-01.json")) == {
                 "ordinal": 1, "caseId": legacy.EXPECTED_CASE_IDS[0], "protocolDigest": SEVENTH_PROTOCOL_DIGEST},
             "seventh historical attempt markers changed")
    for ordinal in range(2, 17):
        path = prior / f"attempt-{ordinal:02d}.json"
        _require(not path.exists() and not path.is_symlink(), "later case already consumed its attempt")


def _reviewed_partial(root: Path) -> dict[str, Any]:
    data = _read(root / REVIEWED_PARTIAL_BINDING["path"])
    _require(hashlib.sha256(data).hexdigest() == REVIEWED_PARTIAL_SHA256,
             "same-attempt partial result changed")
    partial = _json(data)
    previous = _read(root / PREVIOUS_PARTIAL_BINDING["path"])
    _require(hashlib.sha256(previous).hexdigest() == PREVIOUS_PARTIAL_SHA256 and
             hashlib.sha256(_read(root / PREVIOUS_REVIEW_RELATIVE)).hexdigest() == PREVIOUS_REVIEW_SHA256 and
             partial["caseResults"][:5] == _json(previous)["caseResults"][:5] and
             partial["executionSegment"] == {"firstNewOrdinal": 6, "newAttemptCount": 1,
                 "newCliLaunchCount": 1, "priorPartialSha256": PREVIOUS_PARTIAL_SHA256,
                 "reviewSha256": PREVIOUS_REVIEW_SHA256}, "earlier reviewed segment changed")
    review = _json(_read(root / REVIEW_RELATIVE))
    _require(review["previousReviewSha256"] == PREVIOUS_REVIEW_SHA256 and
             review["partialResultSha256"] == REVIEWED_PARTIAL_SHA256 and review["ordinal"] == REVIEWED_PREFIX_COUNT and
             review["source"] == "user-provided-decoded-stderr" and
             review["decision"] == "catalog-refresh-timeout-does-not-invalidate-fixed-case-conditions" and
             review["originalStatus"] == "INCOMPLETE" and review["officialErrorCode"] == "unknown",
             "same-attempt review lacks the specific authorized assessment")
    record = partial["caseResults"][REVIEWED_PREFIX_COUNT - 1]
    facts = record["executionDiagnostics"]
    _require(partial["protocolDigest"] == REVIEWED_PARTIAL_PROTOCOL and
             partial["priorResultSha256s"] == READ_PRIOR_RESULTS and
             (partial["attemptCount"], partial["cumulativeAttemptCount"], partial["cliLaunchCount"]) == (6, 13, 6) and
             all(item["status"] == "PASS" for item in partial["caseResults"][:4]) and
             all(item["status"] == "NOT-RUN" for item in partial["caseResults"][REVIEWED_PREFIX_COUNT:]),
             "reviewed partial has a different attempt prefix")
    _require(record["status"] == "INCOMPLETE" and record["diagnostic"] == "unknown-stderr" and
             facts["category"] == "unknown-stderr" and facts["stderrClassification"] == "unknown" and
             facts["returnCode"] == 0 and facts["inputFullyDelivered"] is True and
             facts["finalOutputVerified"] and facts["streamAssertion"] == "none" and
             facts["policyReason"] == "none" and not facts["observerTerminated"] and
             not facts["timedOut"] and not facts["cleanupFailed"] and
             _diagnostic_outcome(facts) is None and record["terminal"] == "turn.completed" and
             all(value == "valid" for value in record["evidenceExtraction"].values()),
             "review cannot waive another incomplete condition")
    _require(record["operatorStderrCapture"] == {"status": "saved", "bytes": 158,
             "truncated": False, "encoding": "utf-8"}, "review lacks complete retained stderr metadata")
    for metadata in (record["modelMetadataBefore"], record["modelMetadataAfter"]):
        _require(metadata["model"] == MODEL and metadata["toolMode"] is None and
                 metadata["supportsMedium"] is True and metadata["derivedEffectiveToolMode"] == "direct",
                 "review lacks the fixed model and Direct conditions")
    case = legacy.load_golden_cases(root)[REVIEWED_PREFIX_COUNT - 1]
    schema = _json(_read(root / legacy.MODEL_RESPONSE_SCHEMA_RELATIVE))
    # Historical scoring needs its original opaque token, not a prompt rebuilt
    # with the current assessment wording and a different response schema.
    token = legacy.derive_opaque_case_binding(bytes.fromhex(partial["materializationSeed"]),
                                             REVIEWED_PREFIX_COUNT, REVIEWED_PARTIAL_PROTOCOL)
    response = {**record["observed"], "opaqueCaseBinding": token}
    _validate_native_response(response, schema, token)
    _require(not legacy.validate_model_response(response, case, token, schema),
             "reviewed response does not meet the original case semantics")
    return partial


def _verify_review_resume(root: Path, run_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _verify_seven_prior_attempts(run_root)
    partial = _reviewed_partial(root)
    ledger = _ledger(run_root, False, False, read_followup=True)
    _ordinary_directory(ledger)
    for filename, binding in (("normalized-result.json", PREVIOUS_PARTIAL_BINDING),
                              ("normalized-remainder-result.json", REVIEWED_PARTIAL_BINDING)):
        _require(_read(ledger / filename) == _read(root / binding["path"]), "registered partial result changed")
    _require(_json(_read(ledger / "batch-started.json")) == {"protocolDigest": PREVIOUS_PARTIAL_PROTOCOL} and
             _json(_read(ledger / "remainder-started.json")) == {"protocolDigest": REVIEWED_PARTIAL_PROTOCOL},
             "reviewed batch marker changed")
    for ordinal in range(1, 17):
        marker = ledger / f"attempt-{ordinal:02d}.json"
        if ordinal <= REVIEWED_PREFIX_COUNT:
            _require(_json(_read(marker)) == {"ordinal": ordinal, "caseId": legacy.EXPECTED_CASE_IDS[ordinal - 1],
                     "protocolDigest": PREVIOUS_PARTIAL_PROTOCOL if ordinal <= 5 else REVIEWED_PARTIAL_PROTOCOL},
                     "reviewed attempt marker changed")
        else:
            _require(not marker.exists() and not marker.is_symlink(), "remaining case already attempted")
    _require(not (ledger / "catalog-remainder-started.json").exists() and
             not (ledger / "catalog-remainder-started.json").is_symlink(), "remainder already started")
    _require(_json(_read(ledger / "execution-implementation.json")) == {
        "implementationCommit": PREVIOUS_PARTIAL_BINDING["implementationCommit"],
        "implementationTree": PREVIOUS_PARTIAL_BINDING["implementationTree"],
        "protocolDigest": PREVIOUS_PARTIAL_PROTOCOL, "priorAttempts": 7,
        "maximumCumulativeAttempts": 23, "maximumCaseOneAttempts": 8}, "partial execution identity changed")
    _require(_json(_read(ledger / "remainder-execution-implementation.json")) == {
        "implementationCommit": REVIEWED_PARTIAL_BINDING["implementationCommit"],
        "implementationTree": REVIEWED_PARTIAL_BINDING["implementationTree"],
        "protocolDigest": REVIEWED_PARTIAL_PROTOCOL, "priorPartialSha256": PREVIOUS_PARTIAL_SHA256,
        "firstNewOrdinal": 6, "priorAttempts": 12, "maximumCumulativeAttempts": 23,
        "maximumCaseOneAttempts": 8}, "remainder execution identity changed")
    _require(_read(ledger / "same-attempt-review.json") == _read(root / PREVIOUS_REVIEW_RELATIVE),
             "previous prepared review changed")
    # Metadata only: human-only text is never reopened.
    for ordinal in (5, 6):
        metadata = (ledger / f"operator-only-diagnostics/case-{ordinal:02d}-stderr.json").lstat()
        _require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid() and
                 stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_size == 158,
                 "reviewed operator file metadata changed")
    state = _json(_read(ledger / "remainder-preparation.json"))
    initial = _json(_read(run_root / STATE_NAME))
    _require(state == {**initial, "protocolDigest": REVIEWED_PARTIAL_PROTOCOL} and
             _json(_read(ledger / "preparation.json")) == {**initial, "protocolDigest": PREVIOUS_PARTIAL_PROTOCOL} and
             state["materializationSeed"] == partial["materializationSeed"], "reviewed preparation changed")
    _require(state["runMode"] == "actual", "reviewed preparation was not actual")
    return partial, state


def prepare_stderr_review_resume(root: Path, run_root: Path) -> None:
    """Prepare only unstarted cases under the same ledger and operator budget."""
    partial, old = _verify_review_resume(root, run_root)
    protocol = _protocol(root)
    ledger = _ledger(run_root, False, False, read_followup=True)
    legacy.freeze_executable(Path(old["executable"]), protocol["cli"]["sha256"])
    schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    fixtures = _input(root, protocol, "fixtureMatrix")
    materials = []
    for ordinal, case in enumerate(legacy.load_golden_cases(root), 1):
        paths = _case_paths(run_root, ordinal)
        _verify_config(paths, run_root / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        _model_metadata(paths)
        fixture = fixture_identity(paths["workspace"], _definition(fixtures, ordinal))
        package = package_identity(paths["package"]) if ordinal != 11 else None
        _require(old["cases"][ordinal - 1] == {"ordinal": ordinal, "fixtureSha256": fixture,
                 "packageSha256": package} and (ordinal == 11 or package == protocol["bundle"]["packageSha256"]),
                 "reviewed installed inputs changed")
        previous = materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=REVIEWED_PARTIAL_PROTOCOL, model_schema=schema,
            prompt_envelope=envelope, request=case["request"])
        _require(_read(ledger / f"remainder-response-schema-{ordinal:02d}.json") == previous.schema_bytes,
                 "reviewed response schema changed")
        materials.append(materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=protocol["protocolDigest"], model_schema=schema,
            prompt_envelope=envelope, request=case["request"]))
    _exclusive(ledger / "catalog-case-06-review.json", _read(root / REVIEW_RELATIVE))
    for ordinal, material in enumerate(materials, 1):
        _exclusive(ledger / f"catalog-response-schema-{ordinal:02d}.json", material.schema_bytes)
    _exclusive(ledger / "catalog-preparation.json", _bytes({**old, "protocolDigest": protocol["protocolDigest"]}))


def prepare_diagnostic_followup(root: Path, run_root: Path, *, continuation: bool = False,
                                operator_diagnostics: bool = False, schema_followup: bool = False, model_followup: bool = False, stderr_followup: bool = False, read_followup: bool = False) -> None:
    """Add one explicit ledger; preserve all prior preparation, auth and events."""
    _ordinary_directory(run_root)
    (_verify_seven_prior_attempts if read_followup else
     _verify_six_prior_attempts if stderr_followup else
     _verify_five_prior_attempts if model_followup else
     _verify_four_prior_attempts if schema_followup else
     _verify_three_prior_attempts if operator_diagnostics else
     _verify_two_prior_attempts if continuation else _verify_prior_attempt)(run_root)
    protocol = _protocol(root)
    old = _json(_read(run_root / STATE_NAME))
    _require(old["protocolDigest"] == HISTORICAL_PROTOCOL_DIGEST and old["runMode"] == "actual",
             "followup preparation does not name the historical execution")
    prior = _json(_read(run_root / "normalized-result.json"))
    _require(old["materializationSeed"] == prior["materializationSeed"], "historical seed changed")
    legacy.freeze_executable(Path(old["executable"]), protocol["cli"]["sha256"])
    fixtures = _input(root, protocol, "fixtureMatrix")
    schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    cases = legacy.load_golden_cases(root)
    prepared = []
    for ordinal, case in enumerate(cases, 1):
        paths = _case_paths(run_root, ordinal)
        _verify_config(paths, run_root / "marketplace", ordinal != 11)
        _verify_discovery(paths, ordinal != 11)
        fixture = fixture_identity(paths["workspace"], _definition(fixtures, ordinal))
        package = package_identity(paths["package"]) if ordinal != 11 else None
        _require(old["cases"][ordinal - 1] == {
            "ordinal": ordinal, "fixtureSha256": fixture, "packageSha256": package},
            "historical prepared inputs changed")
        _require(ordinal == 11 or package == protocol["bundle"]["packageSha256"], "followup package changed")
        previous = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=HISTORICAL_PROTOCOL_DIGEST, model_schema=schema,
            prompt_envelope=envelope, request=case["request"])
        _require(_read(paths["case"] / "response-schema.json") == previous.schema_bytes,
                 "historical materialization changed")
        prepared.append(materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
            ordinal=ordinal, protocol_digest=protocol["protocolDigest"], model_schema=schema,
            prompt_envelope=envelope, request=case["request"]))
    if continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup:
        previous_state = _json(_read(run_root / "diagnostic-followup/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": RETRY_PROTOCOL_DIGEST},
                 "second preparation no longer matches the original installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=RETRY_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"diagnostic-followup/response-schema-{ordinal:02d}.json") == previous.schema_bytes,
                     "second historical materialization changed")
    if operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup:
        previous_state = _json(_read(run_root / "diagnostic-continuation/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": THIRD_PROTOCOL_DIGEST},
                 "third preparation no longer matches the original installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=THIRD_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"diagnostic-continuation/response-schema-{ordinal:02d}.json") == previous.schema_bytes,
                     "third historical materialization changed")
    if schema_followup or model_followup or stderr_followup or read_followup:
        previous_state = _json(_read(run_root / "operator-diagnostic-continuation/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": FOURTH_PROTOCOL_DIGEST},
                 "fourth preparation no longer matches the installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = legacy.materialize_case_contract(materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=FOURTH_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"operator-diagnostic-continuation/response-schema-{ordinal:02d}.json") ==
                     previous.schema_bytes, "fourth historical materialization changed")
    if model_followup or stderr_followup or read_followup:
        previous_state = _json(_read(run_root / "schema-correction-continuation/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": FIFTH_PROTOCOL_DIGEST},
                 "fifth preparation no longer matches the installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=FIFTH_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"schema-correction-continuation/response-schema-{ordinal:02d}.json") ==
                     previous.schema_bytes, "fifth historical materialization changed")
            _model_metadata(_case_paths(run_root, ordinal))
    if stderr_followup or read_followup:
        previous_state = _json(_read(run_root / "model-migration-continuation/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": SIXTH_PROTOCOL_DIGEST},
                 "sixth preparation no longer matches the installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=SIXTH_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"model-migration-continuation/response-schema-{ordinal:02d}.json") ==
                     previous.schema_bytes, "sixth historical materialization changed")
    if read_followup:
        previous_state = _json(_read(run_root / "stderr-diagnostic-continuation/preparation.json"))
        _require(previous_state == {**old, "protocolDigest": SEVENTH_PROTOCOL_DIGEST},
                 "seventh preparation no longer matches the installed inputs")
        for ordinal, case in enumerate(cases, 1):
            previous = materialize_native_case_contract(root=root, materialization_seed=bytes.fromhex(old["materializationSeed"]),
                ordinal=ordinal, protocol_digest=SEVENTH_PROTOCOL_DIGEST, model_schema=schema,
                prompt_envelope=envelope, request=case["request"])
            _require(_read(run_root / f"stderr-diagnostic-continuation/response-schema-{ordinal:02d}.json") ==
                     previous.schema_bytes, "seventh historical materialization changed")
    ledger = _ledger(run_root, not (continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup),
                     continuation, operator_diagnostics, schema_followup, model_followup, stderr_followup, read_followup)
    prior_count = 7 if read_followup else 6 if stderr_followup else 5 if model_followup else 4 if schema_followup else 3 if operator_diagnostics else 2 if continuation else 1
    ledger.mkdir(mode=0o700)  # exclusive; a partial migration is retained, not retried
    _exclusive(ledger / "migration.json", _bytes({"priorResultSha256": HISTORICAL_RESULT_SHA256,
        "priorProtocolDigest": HISTORICAL_PROTOCOL_DIGEST, "protocolDigest": protocol["protocolDigest"],
        "priorResultSha256s": READ_PRIOR_RESULTS[:prior_count],
        "priorAttempts": prior_count, "maximumCumulativeAttempts": 16 + prior_count}))
    for ordinal, material in enumerate(prepared, 1):
        _exclusive(ledger / f"response-schema-{ordinal:02d}.json", material.schema_bytes)
    _exclusive(ledger / "preparation.json", _bytes({**old, "protocolDigest": protocol["protocolDigest"]}))



def _auth_metadata(descriptor: int) -> dict[str, int]:
    metadata = os.fstat(descriptor)
    _require(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.getuid() and
             stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_nlink == 1,
             "test authentication must be a single-link private regular file")
    return {"device": metadata.st_dev, "inode": metadata.st_ino}


def _auth_owner(run_root: Path, ordinal: int) -> Path:
    return run_root / f"test-auth-owner-{ordinal:02d}.json"


def _open_test_auth(run_root: Path, ordinal: int, flags: int) -> int:
    _require(type(ordinal) is int and 1 <= ordinal <= CASE_COUNT, "invalid test-auth case")
    home = _ordinary_directory(_case_paths(run_root, ordinal)["home"])
    descriptor = os.open(home / AUTH_FILE_NAME, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        identity = _auth_metadata(descriptor)
        owner = _json(_read(_auth_owner(run_root, ordinal)))
        _require(owner == {"ordinal": ordinal, **identity}, "test-auth object ownership changed")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _copy_test_auth(run_root: Path, source_ordinal: int, target_ordinal: int, *, create: bool,
                    source_root: Path | None = None) -> None:
    """Copy only the official credential file; bytes never enter any report/hash/parser.

    Supported only without concurrent operators/clients. The frozen client writes
    this file in place. After abnormal client termination the batch stops, so no
    subsequent case receives a possibly partial refresh.
    """
    _require(1 <= source_ordinal <= CASE_COUNT and source_ordinal != target_ordinal and
             (2 <= target_ordinal <= CASE_COUNT or
              (target_ordinal == 1 and create and source_root is not None and source_root != run_root)),
             "invalid test-auth handoff")
    source = _open_test_auth(source_root or run_root, source_ordinal, os.O_RDONLY)
    target = None
    try:
        if create:
            home = _ordinary_directory(_case_paths(run_root, target_ordinal)["home"])
            target = os.open(home / AUTH_FILE_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            # Registration failure preserves the newly created file; it is never
            # silently retried or mistaken for a caller-owned object.
            _exclusive(_auth_owner(run_root, target_ordinal),
                       _bytes({"ordinal": target_ordinal, **_auth_metadata(target)}))
        else:
            target = _open_test_auth(run_root, target_ordinal, os.O_WRONLY)
            os.ftruncate(target, 0)
        with os.fdopen(os.dup(source), "rb") as reader, os.fdopen(os.dup(target), "wb") as writer:
            shutil.copyfileobj(reader, writer, length=64 * 1024)
            writer.flush()
        os.fsync(target)
    finally:
        os.close(source)
        if target is not None:
            os.close(target)


def share_test_authentication(root: Path, run_root: Path, *, authorize_copy: bool = False,
                              preserve_existing: Sequence[int] = ()) -> None:
    """An explicit one-time copy from the registered Case 1 test login only."""
    _require(authorize_copy is True, "explicit test-auth copy authorization is required")
    protocol, _ = _state(root, run_root)
    _require(not (run_root / AUTH_COPY_STATE).exists(), "test-auth copy state already exists")
    _require(not (run_root / "batch-started.json").exists() and all(
        not (run_root / f"attempt-{i:02d}.json").exists() for i in range(1, 17)),
        "test-auth preparation cannot reset an attempted batch")
    _require(len(set(preserve_existing)) == len(preserve_existing) and all(
        type(i) is int and 2 <= i <= CASE_COUNT for i in preserve_existing),
        "invalid explicitly retained test-auth set")
    retained = {}
    for ordinal in range(1, 17):
        paths = _case_paths(run_root, ordinal)
        home = _ordinary_directory(paths["home"])
        _require(not _auth_owner(run_root, ordinal).exists(), "test-auth ownership already registered")
        if ordinal != 1:
            destination = home / AUTH_FILE_NAME
            if ordinal in preserve_existing:
                backup = paths["case"] / "retained-auth-before-reuse"
                _require(not backup.exists() and not backup.is_symlink(), "test-auth retention destination exists")
                descriptor = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    retained[ordinal] = _auth_metadata(descriptor)
                finally:
                    os.close(descriptor)
            else:
                _require(not destination.exists() and not destination.is_symlink(),
                         "refusing to overwrite an unowned test-auth destination")
    # Only explicitly identified test logins are moved, without reading their
    # contents. They remain private and are never used as a refresh source.
    for ordinal, identity in retained.items():
        paths = _case_paths(run_root, ordinal)
        backup = paths["case"] / "retained-auth-before-reuse"
        backup.mkdir(mode=0o700)
        os.rename(paths["home"] / AUTH_FILE_NAME, backup / AUTH_FILE_NAME)
        descriptor = os.open(backup / AUTH_FILE_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            _require(_auth_metadata(descriptor) == identity, "retained test-auth object changed")
        finally:
            os.close(descriptor)
        _exclusive(backup / "ownership.json", _bytes({"ordinal": ordinal, **identity}))
    source = os.open(_case_paths(run_root, 1)["home"] / AUTH_FILE_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        _exclusive(_auth_owner(run_root, 1), _bytes({"ordinal": 1, **_auth_metadata(source)}))
    finally:
        os.close(source)
    for ordinal in range(2, 17):
        _copy_test_auth(run_root, 1, ordinal, create=True)
    _exclusive(run_root / AUTH_COPY_STATE, _bytes({
        "protocolDigest": protocol["protocolDigest"], "sourceOrdinal": 1, "copiedOrdinals": list(range(2, 17)),
    }))


def _require_test_auth_copy_state(run_root: Path, protocol: Mapping[str, Any]) -> None:
    _require(_json(_read(run_root / AUTH_COPY_STATE)) == {
        "protocolDigest": protocol["protocolDigest"], "sourceOrdinal": 1, "copiedOrdinals": list(range(2, 17)),
    }, "test-auth copy preparation is incomplete or stale")


def login_commands(root: Path, run_root: Path) -> list[dict[str, Any]]:
    """Return commands for an attended terminal; never start or inspect login."""
    _, state = _state(root, run_root)
    executable = Path(state["executable"])
    legacy.freeze_executable(executable, legacy.CODEX_BINARY_SHA256)
    commands = []
    for ordinal in range(1, 17):
        paths = _case_paths(run_root, ordinal)
        commands.append({"ordinal": ordinal, "cwd": str(paths["workspace"]),
                         "env": case_environment(paths), "argv": [str(executable), "-c",
                         'cli_auth_credentials_store="file"', "-c",
                         f'log_dir={json.dumps(str(paths["state"]))}', "login"],
                         "completion": "Official login status: Logged in using ChatGPT"})
    return commands


def _read_command(command: str, readable: Mapping[str, bytes], cwd: Path, *, reference: dict[str, Any] | None = None) -> bytes:
    """Recognize a finite source-visible read grammar, with exact output bytes."""
    if type(command) is not str:
        raise NativeReadError("event-shape")
    try:
        words = shlex.split(command)
        if len(words) == 3 and Path(words[0]).name in {"bash", "sh"} and words[1] in {"-c", "-lc"}:
            words = shlex.split(words[2])
    except ValueError:
        raise NativeReadError("read-command-syntax") from None
    def syntax(condition: bool) -> None:
        if not condition:
            raise NativeReadError("read-command-syntax")
    syntax(bool(words))
    syntax(not any(char in " ".join(words) for char in "\n\r;&|<>`$\0"))
    name = Path(words[0]).name
    if name == "cat" and len(words) in {2, 3}:
        syntax(len(words) == 2 or words[1] == "--")
        selected = words[-1]
        bounds = None
    elif name == "sed" and len(words) == 4 and words[1] == "-n":
        import re
        match = re.fullmatch(r"([1-9][0-9]*),([1-9][0-9]*)p", words[2])
        syntax(match is not None)
        # Bound the decimal conversion too; arbitrary host text must not escape
        # into a generic ValueError (or an unbounded integer conversion).
        syntax(len(match[1]) <= 6 and len(match[2]) <= 6)
        bounds = (int(match[1]), int(match[2]))
        syntax(bounds[0] <= bounds[1] <= 100000)
        selected = words[3]
    else:
        raise NativeReadError("read-command-syntax")
    path = Path(selected)
    if not path.is_absolute():
        path = cwd / path
    if ".." in path.parts or str(path) not in readable:
        raise NativeReadError("read-target-unbound")
    data = readable[str(path)]
    if bounds is not None:
        # sed counts LF-delimited lines. A bare CR is content, and a final
        # unterminated line must not acquire a newline in the expectation.
        pieces = data.split(b"\n")
        lines = [piece + b"\n" for piece in pieces[:-1]]
        if pieces[-1]:
            lines.append(pieces[-1])
        data = b"".join(lines[bounds[0] - 1:bounds[1]])
    if reference is not None:
        reference.update(path=str(path), bytes=len(data), range=list(bounds) if bounds else None)
    return data


def _public_reads(data: bytes, readable: Mapping[str, bytes], paths: Mapping[str, Path]) -> list[dict[str, Any]]:
    """Called only after the entire strict stream validated; expose bound IDs only."""
    result = []
    for ordinal, raw in enumerate(data.splitlines(), 1):
        event = legacy._parse_json_line(raw)
        item = event.get("item", {})
        if event["type"] != "item.completed" or item.get("type") != "command_execution":
            continue
        reference: dict[str, Any] = {}
        _read_command(item["command"], readable, paths["workspace"], reference=reference)
        target = Path(reference.pop("path"))
        for name, prefix in (("fixture", paths["workspace"]), ("package", paths["package"]),
                             ("discovery", paths["discovery"])):
            if target.is_relative_to(prefix):
                relative = target.relative_to(prefix).as_posix()
                if name == "discovery":
                    relative = "skills/" + relative
                result.append({"eventOrdinal": ordinal, "source": name, "path": relative, **reference})
                break
        else:
            raise NativeObservationError("validated read has no public owner")
    return result


def _classify_host_diagnostic(message: str) -> str:
    """Observer inference from frozen templates, never an upstream error code.

    Warning, ConfigWarning and DeprecationNotice lose their source tag in
    JSONL. Unrecognized text cannot establish unaffected test prerequisites.
    """
    if message == DIRECT_TOOLS_FALLBACK_NOTICE:
        # Frozen v0.153.0 explicitly reports the Direct fallback selected under
        # this protocol. This is not a model reroute or permission fallback;
        # actual command paths/output still undergo ordinary bound-read checks.
        return "code-mode-direct-fallback"
    if message == CODE_MODE_FAIL_CLOSED_NOTICE:
        return "code-mode-fail-closed"
    if re.fullmatch(r"model rerouted: [^\r\n]+ -> [^\r\n]+ \([^\r\n]+\)", message):
        return "model-rerouted"
    if re.fullmatch(r"in-process app-server event stream lagged; dropped [0-9]+ events", message):
        return "evidence-incomplete"
    if re.fullmatch(
            r"Configured value for `(windows\.sandbox|approval_policy|approvals_reviewer|permission_profile|web_search_mode)` "
            r"is disallowed by requirements; falling back to required value [^\r\n]+\. Details: [^\r\n]+", message):
        return "configuration-unverified"
    if (message == "Error parsing rules; custom rules not applied." or
            re.fullmatch(r"Error parsing rules; custom rules not applied\. \([^\r\n]+\)", message) or
            message == "`--dangerously-bypass-hook-trust` is enabled. Enabled hooks may run without review for this invocation."):
        return "configuration-unverified"
    return "unknown"


def _diagnostic_outcome(facts: Mapping[str, Any]) -> str | None:
    classes = facts["hostDiagnosticClasses"]
    for category in classes:
        if category == "code-mode-fail-closed":
            return "tool-mode-unavailable"
        if category == "model-rerouted":
            return "model-mismatch"
        if category == "configuration-unverified":
            return "configuration-unverified"
        if category == "evidence-incomplete":
            return "evidence-incomplete"
        if category in {"unknown", "upstream-error"}:
            return "diagnostic-unknown"
    return None


def _inspect_native_event(raw: bytes, readable: Mapping[str, bytes], cwd: Path) -> None:
    event = legacy._parse_json_line(raw)
    kind = event.get("type")
    _require(type(kind) is str, "invalid native event type")
    if kind not in EVENT_TYPES[:-1]:
        raise NativeEventError("event-unsupported")
    if kind == "thread.started":
        legacy._exact_keys(event, {"type", "thread_id"}, kind)
        legacy._validate_thread_identifier(event["thread_id"])
    elif kind == "turn.started":
        legacy._exact_keys(event, {"type"}, kind)
    elif kind == "turn.completed":
        legacy._exact_keys(event, {"type", "usage"}, kind)
        legacy._validate_usage(event["usage"])
    elif kind in {"error", "turn.failed"}:
        if kind == "turn.failed":
            legacy._exact_keys(event, {"type", "error"}, kind)
            payload = legacy._exact_keys(event["error"], {"message"}, kind)
        else:
            payload = legacy._exact_keys(event, {"type", "message"}, kind)
        _require(type(payload["message"]) is str and
                 len(payload["message"].encode("utf-8")) <= legacy.MAX_JSONL_LINE_BYTES,
                 "invalid native error message")
    else:
        legacy._exact_keys(event, {"type", "item"}, kind)
        item = event["item"]
        _require(type(item) is dict, "native item missing")
        item_type = item.get("type")
        _require(type(item_type) is str, "invalid native item type")
        if item_type not in {"reasoning", "agent_message", "command_execution", "error"}:
            raise NativeEventError("item-unsupported")
        legacy._validate_item_payload(item, item_type)
        if item_type != "command_execution":
            if kind != "item.completed":
                raise NativeEventError("item-lifecycle")
        else:
            _require(type(item["status"]) is str and item["status"] in {
                "in_progress", "completed", "failed", "declined"}, "invalid native read status")
            expected = _read_command(item["command"], readable, cwd)
            if kind == "item.completed":
                if item["status"] != "completed" or item["exit_code"] != 0:
                    raise NativeReadError("read-lifecycle")
                if item["aggregated_output"].encode("utf-8") != expected:
                    raise NativeReadError("read-output-mismatch")
            else:
                if item["status"] != "in_progress" or item["exit_code"] is not None:
                    raise NativeReadError("read-lifecycle")
                if not expected.startswith(item["aggregated_output"].encode("utf-8")):
                    raise NativeReadError("read-prefix-mismatch")


def inspect_native_event(raw: bytes, readable: Mapping[str, bytes], cwd: Path) -> None:
    try:
        _inspect_native_event(raw, readable, cwd)
    except NativeEventError:
        raise
    except (ValueError, KeyError, TypeError, NativeObservationError):
        # Only actual field/type/shape failures reach this conversion. Read
        # predicates carry their own code before either consumer sees them.
        raise NativeReadError("event-shape") from None


def _observe_line(raw: bytes, readable: Mapping[str, bytes], cwd: Path, facts: dict[str, Any]) -> None:
    facts["eventCount"] += 1
    try:
        event = legacy._parse_json_line(raw)
    except (ValueError, NativeObservationError):
        _first_assertion(facts, "event-shape", facts["eventCount"])
        _first_failure(facts, "event", "event-invalid")
        raise NativeDiagnosticError(facts) from None
    kind = event.get("type")
    retained = kind if kind in EVENT_TYPES[:-1] else "unknown"
    if retained not in facts["eventTypes"]:
        facts["eventTypes"].append(retained)
    item = event.get("item")
    item_type = item.get("type") if type(item) is dict else None
    supported_items = {"reasoning", "agent_message", "command_execution", "error"}
    if type(kind) is str and kind.startswith("item."):
        retained_item = item_type if type(item_type) is str and item_type in supported_items else "unsupported"
        if retained_item not in facts["itemTypes"]:
            facts["itemTypes"].append(retained_item)
    if facts["eventCount"] > legacy.MAX_EVENT_COUNT:
        _first_failure(facts, "event", "output-limit")
        raise NativeDiagnosticError(facts)
    try:
        inspect_native_event(raw, readable, cwd)
    except NativeEventError as error:
        _first_assertion(facts, error.code, facts["eventCount"])
        if facts["policyReason"] == "none":
            facts["policyReason"] = ("unknown-event" if error.code == "event-unsupported" else
                "read-contract-rejected" if error.code in READ_REJECTIONS[1:] else
                "unsupported-item" if error.code == "item-unsupported" else
                "item-lifecycle-rejected" if error.code == "item-lifecycle" else "event-shape-rejected")
        _first_failure(facts, "event", "policy-rejected")
        raise NativeDiagnosticError(facts) from None
    classification = None
    if kind == "item.completed" and item_type == "error":
        facts["diagnosticItemCount"] += 1
        facts["preTurnDiagnosticCount"] += int("turn.started" not in facts["eventTypes"])
        classification = _classify_host_diagnostic(item["message"])
    elif kind == "error":
        classification = "upstream-error"
    if classification is not None and classification not in facts["hostDiagnosticClasses"]:
        facts["hostDiagnosticClasses"].append(classification)
    if kind == "turn.failed":
        _first_failure(facts, "event", "host-failure")
    # Diagnostics are not actions or terminal failures. Their effect on the
    # fixed test conditions is assessed after process and stream closure.


def parse_native_jsonl(data: bytes, taxonomy: Mapping[str, Any], readable: Mapping[str, bytes],
                       cwd: Path) -> tuple[legacy.StreamFacts, int]:
    """Validate all events, then parse only the last emitted response candidate.

    Frozen exec drops AgentMessage phase and may subsequently replace its final
    output from TurnCompleted.items. The run entrypoint therefore also checks
    the official --output-last-message artifact before accepting this candidate.
    """
    ordinal = None
    def require(condition: bool, code: str, phase: str = "stream") -> None:
        if not condition:
            error = NativeStreamError(code, ordinal, phase)
            if phase == "response":
                error.closed_terminal, error.completed_commands = terminal, completed_commands
            raise error
    require(len(data) <= legacy.MAX_STDOUT_BYTES and data.endswith(b"\n") and b"\r" not in data,
            "framing-or-size")
    lines = data.splitlines()
    require(len(lines) <= legacy.MAX_EVENT_COUNT, "event-count")
    ordered, item_types, statuses, journal = [], [], [], []
    states: dict[str, tuple[str, str]] = {}
    commands: dict[str, str] = {}
    completed_commands = 0
    thread_seen = turn_seen = False
    terminal = None
    result = None
    last_message = None
    last_message_ordinal = None
    for ordinal, raw in enumerate(lines, 1):
        require(terminal is None, "event-after-terminal")
        try:
            inspect_native_event(raw, readable, cwd)
            event = legacy._parse_json_line(raw)
        except NativeEventError as error:
            raise NativeStreamError(error.code, ordinal) from None
        except (ValueError, KeyError, TypeError, NativeObservationError):
            raise NativeStreamError("event-shape", ordinal) from None
        kind = event["type"]
        ordered.append(kind)
        definition = taxonomy["topLevelTypes"][kind]
        entry = {"ordinal": ordinal, "eventType": kind,
                 "category": definition["category"], "role": definition["role"]}
        if kind == "thread.started":
            require(ordinal == 1 and not thread_seen, "thread-start-order")
            thread_seen = True
        elif kind == "turn.started":
            require(thread_seen and not turn_seen, "turn-start-order")
            turn_seen = True
        elif kind in {"turn.completed", "turn.failed"}:
            require(turn_seen and all(state == "completed" for _, state in states.values()),
                    "terminal-active-items")
            terminal = kind
        elif kind == "error":
            require(thread_seen, "error-before-thread")
        else:
            item = event["item"]
            item_type, identifier = item["type"], item["id"]
            require(thread_seen and (turn_seen or item_type == "error"), "item-outside-lifecycle")
            previous = states.get(identifier)
            if previous is None:
                require(identifier == f"item_{len(states)}", "item-id-sequence")
            else:
                require(previous[0] == item_type and previous[1] != "completed", "item-id-reused")
            if item_type == "command_execution":
                if kind == "item.started":
                    require(previous is None, "command-start-duplicate")
                    commands[identifier] = item["command"]
                else:
                    require(previous is not None and commands.get(identifier) == item["command"],
                            "command-start-mismatch")
                    completed_commands += int(kind == "item.completed")
                statuses.append(item["status"])
                entry["status"] = item["status"]
            else:
                require(previous is None, "content-id-reused")
            states[identifier] = (item_type, "completed" if kind == "item.completed" else "active")
            item_types.append(item_type)
            entry.update(itemType=item_type, category=taxonomy["itemTypes"][item_type]["category"])
            if item_type == "agent_message":
                require(len(item["text"].encode("utf-8")) <= legacy.MAX_RESULT_BYTES, "agent-message-size")
                last_message = item["text"].encode("utf-8")
                last_message_ordinal = ordinal
        journal.append(entry)
    require(terminal is not None, "missing-terminal")
    if terminal == "turn.completed":
        require(last_message is not None, "final-message-missing", "response")
    if last_message is not None:
        ordinal = last_message_ordinal
        try:
            result = _json(last_message)
        except (ValueError, NativeObservationError):
            # A failed turn's commentary is not a structured success response.
            if terminal == "turn.completed":
                error = NativeStreamError("final-message-invalid-json", ordinal, "response")
                error.closed_terminal, error.completed_commands = terminal, completed_commands
                raise error from None
        else:
            require(type(result) is dict, "final-message-not-object", "response")
    return legacy.StreamFacts(ordered_event_types=tuple(ordered), item_types=tuple(item_types),
        item_statuses=tuple(statuses), journal=tuple(journal), terminal_type=terminal,
        terminal_count=1, events_after_terminal=0, structured_result_count=int(result is not None),
        tool_capable_event_count=sum(item == "command_execution" for item in item_types),
        unknown_event_count=0, unknown_item_count=0, unknown_status_count=0, malformed_line_count=0,
        structured_result=result), completed_commands


def _reserve_final_output(path: Path) -> tuple[int, int]:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        metadata = os.fstat(descriptor)
        return metadata.st_dev, metadata.st_ino
    finally:
        os.close(descriptor)


def _check_final_output(path: Path, identity: tuple[int, int], candidate: Any) -> None:
    """Bounded private official output; only a validated response may be retained."""
    try:
        metadata = path.lstat()
        _require(stat.S_ISREG(metadata.st_mode) and (metadata.st_dev, metadata.st_ino) == identity,
                 "final output identity changed")
        data = _read(path, maximum=legacy.MAX_RESULT_BYTES)
        value = _json(data)
    except (OSError, ValueError, NativeObservationError):
        raise NativeStreamError("final-output-unavailable", None, "response") from None
    if type(value) is not dict or _bytes(value) != _bytes(candidate):
        raise NativeStreamError("final-output-mismatch", None, "response")


def _readable(paths: Mapping[str, Path], definition: Mapping[str, Any], installed: bool) -> dict[str, bytes]:
    _verify_discovery(paths, installed)
    result = {str(paths["workspace"] / item["path"]): item["contentUtf8"].encode("utf-8")
              for item in definition["files"]}
    if installed:
        # Enumerate only the verified immutable public package, not CODEX_HOME.
        for relative, _, _, _ in legacy.snapshot_tree(paths["package"]):
            data = _read(paths["package"] / relative)
            result[str(paths["package"] / relative)] = data
            # The host advertises this verified standard discovery path. Bind
            # only its exact public skills subtree to the same package bytes;
            # never resolve arbitrary caller paths or admit other symlinks.
            if Path(relative).parts[0] == "skills":
                result[str(paths["discovery"] / Path(relative).relative_to("skills"))] = data
    return result


def _blank_case(case: Mapping[str, Any], materialized: legacy.CaseMaterialization,
                seed: bytes, protocol: Mapping[str, Any], definition: Mapping[str, Any], *,
                root: Path = REPOSITORY_ROOT) -> dict[str, Any]:
    fields = legacy._case_materialization_fields(
        materialization=materialized, materialization_seed=seed, protocol_digest=protocol["protocolDigest"],
        case=case, realized_fixture_digest=legacy._expected_realized_fixture_digest(definition),
        realized_file_set_digest=definition["canonicalFileSetDigest"], prompt_fully_delivered=True)
    return {"ordinal": materialized.ordinal, "caseId": case["id"], "status": "NOT-RUN",
            "diagnostic": "not-run", "cliLaunchCount": 0, "attemptCount": 0, "modelRequestCount": None,
            "privateCapture": _private_capture(), "operatorStderrCapture": _stderr_capture(),
            "operatorReadCapture": _private_capture(), "publicReads": [],
            "explicitInvocation": _case_explicit_selection(root, case["request"], materialized.ordinal,
                                                          protocol_digest=protocol["protocolDigest"]),
            "executionDiagnostics": _diagnostics(),
            "evidenceExtraction": {"stream": "not-checked", "response": "not-checked", "postcheck": "not-checked"},
            "installation": "not-checked", "authentication": "not-checked",
            "fixtureBeforeSha256": None, "fixtureAfterSha256": None,
            "packageBeforeSha256": None, "packageAfterSha256": None,
            "modelMetadataBefore": None, "modelMetadataAfter": None,
            "readonlyCommandCount": 0, "observed": None, "terminal": "not-observed", **fields,
            "opaqueBindingSha256": materialized.opaque_binding_sha256}


def run_native_observation(root: Path, run_root: Path, *, authorize_model_calls: bool = False,
                           reuse_test_auth: bool = False, followup: bool = False,
                           continuation: bool = False, private_diagnostics: bool = False, operator_diagnostics: bool = False, schema_followup: bool = False, model_followup: bool = False, stderr_followup: bool = False, read_followup: bool = False, resume_stderr_review: bool = False,
                           assessment_batch: bool = False, assessment_remainder: bool = False,
                           material_segment: bool = False, current_assessment: bool = False,
                           fixed_acceptance: bool = False, revision_four: bool = False,
                           process_runner: Callable[..., Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """One foreground batch; exclusive markers consume each case before spawn."""
    _require(not (fixed_acceptance and revision_four), "select one fixed window")
    fixed_acceptance = fixed_acceptance or revision_four
    contract = _fixed_contract(revision_four)
    _require(authorize_model_calls is True, "explicit model-call authorization is required")
    _require(not ((operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup) and private_diagnostics), "select one private capture format")
    _require(not resume_stderr_review or read_followup, "review resume requires the same read ledger")
    if assessment_batch:
        _require(not any((followup, continuation, operator_diagnostics, schema_followup,
                         model_followup, stderr_followup, read_followup, resume_stderr_review, private_diagnostics)),
                 "assessment batch cannot reuse a historical execution ledger")
        _assessment_prior(root)
    _require(not material_segment or (assessment_batch and not assessment_remainder), "material segment requires its own assessment mode")
    _require(not current_assessment or (assessment_batch and not material_segment and not assessment_remainder),
             "current assessment cannot reuse a historical segment")
    _require(not fixed_acceptance or (assessment_batch and not any((current_assessment, material_segment, assessment_remainder))),
             "fixed acceptance cannot reuse a historical segment")
    current_chain = (_verify_fixed_acceptance(root, run_root, revision_four=revision_four) if fixed_acceptance else
                     _verify_current_assessment(root, run_root) if current_assessment else None)
    if material_segment:
        _verify_material_segment(root, run_root)
    _require(not assessment_remainder or assessment_batch, "assessment remainder requires assessment mode")
    partial = _verify_assessment_remainder(root, run_root)[0] if assessment_remainder else (_verify_review_resume(root, run_root)[0] if resume_stderr_review else None)
    prefix_count = 10 if assessment_remainder else REVIEWED_PREFIX_COUNT
    protocol, state = _state(root, run_root, followup=followup, continuation=continuation, operator_diagnostics=operator_diagnostics, schema_followup=schema_followup, model_followup=model_followup, stderr_followup=stderr_followup, read_followup=read_followup, resume_stderr_review=resume_stderr_review, assessment_remainder=assessment_remainder)
    ledger = _ledger(run_root, followup, continuation, operator_diagnostics, schema_followup, model_followup, stderr_followup, read_followup)
    prior_count = current_chain["attempts"] if current_assessment or fixed_acceptance else 31 if material_segment else 20 if assessment_batch else 7 if read_followup else 6 if stderr_followup else 5 if model_followup else 4 if schema_followup else 3 if operator_diagnostics else 2 if continuation else int(followup)
    if read_followup:
        _verify_seven_prior_attempts(run_root)
    elif stderr_followup:
        _verify_six_prior_attempts(run_root)
    elif model_followup:
        _verify_five_prior_attempts(run_root)
    elif schema_followup:
        _verify_four_prior_attempts(run_root)
    elif operator_diagnostics:
        _verify_three_prior_attempts(run_root)
    elif continuation:
        _verify_two_prior_attempts(run_root)
    elif followup:
        _verify_prior_attempt(run_root)
    executable = Path(state["executable"])
    frozen = legacy.freeze_executable(executable, protocol["cli"]["sha256"])
    actual = process_runner is None and state["runMode"] == "actual"
    if fixed_acceptance:
        _require(state["runMode"] == ("actual" if process_runner is None else "simulated") and reuse_test_auth,
                 "fixed preparation mode or serial authentication changed")
    _require(not actual or assessment_batch, "actual execution requires the authorized assessment candidate")
    _require(not actual or fixed_acceptance, "actual execution requires the newly authorized fixed acceptance")
    _require(not actual or protocol[_fixed_history_key(revision_four) if fixed_acceptance else "executionWindow"]["state"] != "closed",
             "actual execution window closed")
    _require(not actual or fixed_acceptance or not _json(_read(root / HISTORY_RELATIVE))["results"],
             "current assessment already recorded; execution window consumed")
    execution_source = _execution_source(root) if actual else None
    if fixed_acceptance:
        _require(_fixed_registration(root, run_root.parent, revision_four=revision_four)["executionSource"] == execution_source,
                 "fixed execution commit changed after preparation")
    summaries = PrivateDiagnostics(ledger) if private_diagnostics else None
    operator = OperatorDiagnostics(ledger, reviewed_prefix=partial["caseResults"][:prefix_count] if partial else ()) if operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup or assessment_batch else None
    invoke = bounded_process if process_runner is None else process_runner
    cases = legacy.load_golden_cases(root)
    fixtures = _input(root, protocol, "fixtureMatrix")
    schema = _input(root, protocol, "modelResponseSchema")
    envelope = _input(root, protocol, "promptEnvelope")
    taxonomy = _input(root, protocol, "taxonomy")
    seed = bytes.fromhex(state["materializationSeed"])
    materials = [materialize_native_case_contract(root=root, materialization_seed=seed, ordinal=i,
        protocol_digest=protocol["protocolDigest"], model_schema=schema,
        prompt_envelope=envelope, request=case["request"]) for i, case in enumerate(cases, 1)]
    results = [_blank_case(case, material, seed, protocol, _definition(fixtures, i), root=root)
               for i, (case, material) in enumerate(zip(cases, materials), 1)]
    if partial:
        results[:prefix_count] = partial["caseResults"][:prefix_count]
        _require(assessment_remainder or _read(ledger / "catalog-case-06-review.json") == _read(root / REVIEW_RELATIVE),
                 "prepared same-attempt review changed")
    schema_prefix = "assessment-remainder-response-schema" if assessment_remainder else "catalog-response-schema" if partial else "response-schema"
    if reuse_test_auth and not (material_segment or current_assessment or fixed_acceptance):
        _require_test_auth_copy_state(run_root, {"protocolDigest": HISTORICAL_PROTOCOL_DIGEST} if followup or continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup else {"protocolDigest": ASSESSMENT_PROTOCOL_DIGEST} if assessment_remainder else protocol)
    _exclusive(ledger / ("assessment-remainder-started.json" if assessment_remainder else "catalog-remainder-started.json" if partial else "batch-started.json"),
               _bytes({"protocolDigest": protocol["protocolDigest"]}))
    for ordinal, (case, material, record) in enumerate(zip(cases, materials, results), 1):
        if (material_segment and ordinal < 10) or (partial and ordinal <= prefix_count):
            continue
        paths = _case_paths(run_root, ordinal)
        definition = _definition(fixtures, ordinal)
        installed = ordinal != 11
        diagnostic = "input-changed"
        phase = "precheck"
        events = _diagnostics()
        final_output = ledger / f"final-message-{ordinal:02d}.json"
        final_output_identity = None
        try:
            legacy.recheck_executable(frozen)
            _ordinary_directory(paths["workspace"])
            _ordinary_directory(paths["home"])
            _verify_config(paths, run_root / "marketplace", installed)
            _verify_discovery(paths, installed)
            record["fixtureBeforeSha256"] = fixture_identity(paths["workspace"], definition)
            _require(record["fixtureBeforeSha256"] == state["cases"][ordinal - 1]["fixtureSha256"], "prepared fixture changed")
            if installed:
                record["packageBeforeSha256"] = package_identity(paths["package"])
                _require(record["packageBeforeSha256"] == state["cases"][ordinal - 1]["packageSha256"] ==
                         protocol["bundle"]["packageSha256"], "prepared plugin changed")
            record["installation"] = "verified" if installed else "absent"
            record["modelMetadataBefore"] = _model_metadata(paths)
            _require(_read((ledger / f"{schema_prefix}-{ordinal:02d}.json") if assessment_remainder or followup or continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup else
                           paths["case"] / "response-schema.json") == material.schema_bytes,
                     "prepared response schema changed")
            diagnostic = "authentication-unavailable"
            phase = "login"
            if reuse_test_auth and ordinal > 1 and not (material_segment and ordinal == 10):
                # The prior iteration only advances after normal exit and closed
                # output/input validation. Never refill from the initial stale copy.
                _copy_test_auth(run_root, 9 if assessment_remainder and ordinal == 11 else ordinal - 1, ordinal, create=material_segment or current_assessment or fixed_acceptance)
            if reuse_test_auth:
                # Validate Case 1 as well as copied destinations before handing
                # the path to the official client; never inspect credential bytes.
                descriptor = _open_test_auth(run_root, ordinal, os.O_RDONLY)
                os.close(descriptor)
            login = invoke([str(executable), "-c", 'cli_auth_credentials_store="file"', "login", "status"],
                           cwd=paths["workspace"], env=case_environment(paths))
            combined = login["stdout"] + login["stderr"]
            _require(login["returncode"] == 0 and combined.strip() == b"Logged in using ChatGPT",
                     "official client did not confirm test ChatGPT login")
            record["authentication"] = "chatgpt"
            readable = _readable(paths, definition, installed)
            # The official client owns writing this reserved ordinary file.
            # Model tools cannot read the ledger under the existing profile.
            diagnostic, phase = "execution-failed", "precheck"
            final_output_identity = _reserve_final_output(final_output)
            diagnostic = "already-attempted"
            _exclusive(ledger / f"attempt-{ordinal:02d}.json", _bytes({
                "ordinal": ordinal, "caseId": case["id"], "protocolDigest": protocol["protocolDigest"]}))
            # The marker consumes budget even if spawn fails. CLI launch count
            # is separately recorded only once Popen has created the process.
            record["attemptCount"] = 1
            diagnostic = "execution-failed"
            phase = "launch"
            argv = build_native_argv(executable, run_root, ordinal, response_schema=(
                ledger / f"{schema_prefix}-{ordinal:02d}.json" if
                assessment_remainder or followup or continuation or operator_diagnostics or schema_followup or model_followup or stderr_followup or read_followup else None),
                final_output=final_output)
            def receive(raw: bytes) -> None:
                if operator is not None:
                    operator.event(raw)
                if summaries is not None:
                    summaries.event(ordinal, raw)
                try:
                    _observe_line(raw, readable, paths["workspace"], events)
                except NativeDiagnosticError:
                    if assessment_batch and operator is not None and events["streamAssertion"] in READ_REJECTIONS:
                        operator.rejected_command(raw)
                    raise
            try:
                capture = invoke(argv, cwd=paths["workspace"],
                                 env=case_environment(paths), stdin=material.prompt_bytes,
                                 started_callback=lambda: record.__setitem__("cliLaunchCount", 1),
                                 line_callback=receive)
            except NativeDiagnosticError as error:
                if error.capture is None:
                    raise
                capture = error.capture
            if operator is not None and (stderr_followup or read_followup or assessment_batch):
                # Only the canonical client's captured stderr enters this path.
                # Login and every other process remain outside this exception.
                operator.stderr(capture["stderr"])
            if summaries is not None:
                summaries.stderr(ordinal, capture["stderr"])
            _require(record["cliLaunchCount"] == 1, "client runner did not report a created process")
            facts = _capture_facts(capture)
            if events["streamAssertion"] != "none":
                _first_assertion(facts, events["streamAssertion"], events["streamEventOrdinal"])
            facts.update(eventCount=events["eventCount"], eventTypes=events["eventTypes"],
                         itemTypes=events["itemTypes"], policyReason=events["policyReason"],
                         diagnosticItemCount=events["diagnosticItemCount"],
                         preTurnDiagnosticCount=events["preTurnDiagnosticCount"],
                         hostDiagnosticClasses=events["hostDiagnosticClasses"])
            if events["category"] != "none":
                facts.update(phase=events["phase"], category=events["category"])
            record["executionDiagnostics"] = facts
            if "turn.failed" in events["eventTypes"]:
                record["terminal"] = "turn.failed"
            diagnostic = "stream-invalid"
            phase = "stream"
            record["evidenceExtraction"]["stream"] = "invalid"
            stream, count = parse_native_jsonl(capture["stdout"], taxonomy, readable, paths["workspace"])
            record["evidenceExtraction"]["stream"] = "valid"
            record["readonlyCommandCount"] = count
            record["publicReads"] = _public_reads(capture["stdout"], readable, paths)
            record["terminal"] = stream.terminal_type
            condition_failure = _diagnostic_outcome(facts)
            if condition_failure is not None:
                _first_failure(facts, "event", condition_failure)
            phase = "response"
            record["evidenceExtraction"]["response"] = "invalid"
            _require(type(stream.structured_result) is dict, "closed stream has no structured response")
            _check_final_output(final_output, final_output_identity, stream.structured_result)
            facts["finalOutputVerified"] = True
            observed = dict(stream.structured_result)
            _validate_native_response(observed, schema, material.token)
            record["evidenceExtraction"]["response"] = "valid"
            record["observed"] = {key: value for key, value in observed.items() if key != "opaqueCaseBinding"}
            failures = legacy.validate_model_response(observed, case, material.token, schema)
            if observed["selectedRoutes"] != sorted(observed["selectedRoutes"], key=lambda value: value.encode("utf-8")):
                failures.append("selectedRoutes report order is not UTF-8 lexical")
            diagnostic = "input-changed"
            phase = "postcheck"
            record["evidenceExtraction"]["postcheck"] = "invalid"
            record["fixtureAfterSha256"] = fixture_identity(paths["workspace"], definition)
            if installed:
                record["packageAfterSha256"] = package_identity(paths["package"])
            _require(record["fixtureAfterSha256"] == record["fixtureBeforeSha256"] and
                     record["packageAfterSha256"] == record["packageBeforeSha256"], "consumed inputs changed")
            _verify_config(paths, run_root / "marketplace", installed)
            _verify_discovery(paths, installed)
            record["modelMetadataAfter"] = _model_metadata(paths)
            record["evidenceExtraction"]["postcheck"] = "valid"
            if facts["category"] != "none":
                raise NativeDiagnosticError(facts)
            record["status"] = "FAIL" if failures else "PASS"
            record["diagnostic"] = "semantic-mismatch" if failures else "none"
        except (OSError, ValueError, KeyError, NativeObservationError, subprocess.SubprocessError) as error:
            record["status"] = "INCOMPLETE"
            facts = dict(error.facts) if isinstance(error, NativeDiagnosticError) else dict(record["executionDiagnostics"])
            if events["streamAssertion"] != "none":
                _first_assertion(facts, events["streamAssertion"], events["streamEventOrdinal"])
                record["evidenceExtraction"]["stream"] = "invalid"
            if isinstance(error, NativeStreamError):
                _first_assertion(facts, error.code, error.event_ordinal)
                if error.phase == "response":
                    phase, diagnostic = "response", "response-invalid"
                    record["evidenceExtraction"].update(stream="valid", response="invalid")
                    if error.closed_terminal is not None:
                        record["terminal"] = error.closed_terminal
                        record["readonlyCommandCount"] = error.completed_commands
                        record["publicReads"] = _public_reads(capture["stdout"], readable, paths)
            facts.update(eventCount=events["eventCount"], eventTypes=events["eventTypes"],
                         itemTypes=events["itemTypes"], policyReason=events["policyReason"],
                         diagnosticItemCount=events["diagnosticItemCount"],
                         preTurnDiagnosticCount=events["preTurnDiagnosticCount"],
                         hostDiagnosticClasses=events["hostDiagnosticClasses"])
            if events["category"] != "none":
                facts.update(phase=events["phase"], category=events["category"])
            _first_failure(facts, phase, "response-invalid" if phase == "response" else diagnostic)
            record["executionDiagnostics"] = facts
            record["diagnostic"] = facts["category"]
            if "turn.failed" in events["eventTypes"]:
                record["terminal"] = "turn.failed"
            if diagnostic == "authentication-unavailable":
                record["authentication"] = "unavailable"
                facts.update(phase="login", inputBytesSent=0, inputFullyDelivered=None)
            # Raw exceptions may contain private paths or output; do not retain them.
            del error
            break
        finally:
            if final_output_identity is not None:
                try:
                    metadata = final_output.lstat()
                    _require(stat.S_ISREG(metadata.st_mode) and
                             (metadata.st_dev, metadata.st_ino) == final_output_identity,
                             "private final output ownership changed")
                    final_output.unlink()
                except (OSError, NativeObservationError):
                    facts = record["executionDiagnostics"]
                    facts["cleanupFailed"] = True
                    _first_failure(facts, "cleanup", "cleanup-failed")
                    record.update(status="INCOMPLETE", diagnostic=facts["category"])
            if operator is not None:
                record["privateCapture"] = operator.save(ordinal)
                if assessment_batch:
                    record["operatorReadCapture"] = operator.save_command(ordinal)
                if stderr_followup or read_followup or assessment_batch:
                    record["operatorStderrCapture"] = operator.save_stderr(ordinal)
                if (record["privateCapture"]["status"] == "write-failed" or
                        record["operatorStderrCapture"]["status"] == "write-failed" or
                        record["operatorReadCapture"]["status"] == "write-failed"):
                    facts = record["executionDiagnostics"]
                    facts["cleanupFailed"] = True
                    _first_failure(facts, "cleanup", "cleanup-failed")
                    record.update(status="INCOMPLETE", diagnostic=facts["category"])
            # Raw buffers never leave this bounded execution scope.
            if "capture" in locals():
                del capture
            if record["cliLaunchCount"] and record["evidenceExtraction"]["postcheck"] == "not-checked":
                record["evidenceExtraction"]["postcheck"] = "invalid"
                try:
                    record["fixtureAfterSha256"] = fixture_identity(paths["workspace"], definition)
                    record["packageAfterSha256"] = package_identity(paths["package"]) if installed else None
                    _require(record["fixtureAfterSha256"] == record["fixtureBeforeSha256"] and
                             record["packageAfterSha256"] == record["packageBeforeSha256"], "consumed inputs changed")
                    _verify_config(paths, run_root / "marketplace", installed)
                    _verify_discovery(paths, installed)
                    record["modelMetadataAfter"] = _model_metadata(paths)
                    record["evidenceExtraction"]["postcheck"] = "valid"
                except (OSError, ValueError, KeyError, NativeObservationError):
                    _first_failure(record["executionDiagnostics"], "postcheck", "input-changed")
            if summaries is not None:
                try:
                    summaries.save()
                except OSError:
                    facts = record["executionDiagnostics"]
                    facts["cleanupFailed"] = True
                    _first_failure(facts, "cleanup", "cleanup-failed")
                    record.update(status="INCOMPLETE", diagnostic=facts["category"])
        if record["status"] == "INCOMPLETE":
            break
    statuses = [item["status"] for item in results]
    status = "INCOMPLETE" if not actual or any(value in {"NOT-RUN", "INCOMPLETE"} for value in statuses) else (
        "FAIL" if "FAIL" in statuses else "PASS")
    result = {"schemaVersion": "2", "diagnosticRevision": 11, "protocolId": PROTOCOL_ID,
              "executionModel": {"model": MODEL, "reasoningEffort": REASONING_EFFORT, "requiredToolMode": "direct"},
              "priorResultSha256s": contract["priorResultSha256s"] if fixed_acceptance else CURRENT_PRIOR_RESULTS if current_assessment else ASSESSMENT_PRIOR_RESULTS if assessment_batch else READ_PRIOR_RESULTS[:prior_count],
              "attemptCount": sum(item["attemptCount"] for item in results),
              "cumulativeAttemptCount": prior_count + sum(item["attemptCount"] for item in results),
              "discoveryMechanism": DISCOVERY_MECHANISM, "pluginRuntimeEnabled": False,
              "authenticationMode": "serial-test-auth-copy" if reuse_test_auth else "independent-official-login",
              "protocolDigest": protocol["protocolDigest"], "runMode": "actual" if actual else "simulated",
              "hostClaim": actual and status == "PASS", "status": status,
              "materializationSeed": seed.hex(), "cliLaunchCount": sum(item["cliLaunchCount"] for item in results),
              "modelRequestCount": None, "caseResults": results,
              "materializationCommitmentRoot": legacy._materialization_commitment_root(
                  [item["materializationCommitmentSha256"] for item in results]),
              "cleanup": "retained-test-state", "descendantClosure": "not-observed"}
    if fixed_acceptance:
        result["executionSource"] = execution_source
        result["executionSegment"] = {
            "kind": _fixed_kind(revision_four), "priorPartialSha256": FIXED_RESULT_SHA256 if revision_four else FIXED_REPLY_PRIORS[-1],
            "firstNewOrdinal": 1, "priorAttemptCount": contract["priorAttempts"],
            "authenticationSourceOrdinal": contract["authenticationSourceOrdinal"] if revision_four else 14,
            "newAttemptCount": result["attemptCount"], "newCliLaunchCount": result["cliLaunchCount"],
        }
    elif current_assessment:
        result["executionSegment"] = {
            "kind": "explicit-invocation-revision-1", "priorPartialSha256": ASSESSMENT_REVISION_THREE["sha256"],
            "firstNewOrdinal": 1, "priorAttemptCount": current_chain["attempts"],
            "authenticationSourceOrdinal": 16,
            "newAttemptCount": result["attemptCount"], "newCliLaunchCount": result["cliLaunchCount"],
        }
    elif material_segment:
        result["executionSegment"] = {
            "kind": "material-delivery", "priorPartialSha256": ASSESSMENT_REMAINDER_BINDING["sha256"],
            "firstNewOrdinal": 10, "priorAttemptCount": 31, "authenticationSourceOrdinal": 9,
            "newAttemptCount": result["attemptCount"], "newCliLaunchCount": result["cliLaunchCount"],
        }
    elif assessment_remainder:
        result["executionSegment"] = {
            "priorPartialSha256": ASSESSMENT_PARTIAL_BINDING["sha256"], "firstNewOrdinal": 11,
            "newAttemptCount": sum(item["attemptCount"] for item in results[10:]),
            "newCliLaunchCount": sum(item["cliLaunchCount"] for item in results[10:]),
            "priorAttemptCount": 30, "authenticationSourceOrdinal": 9,
        }
    elif partial:
        result["executionSegment"] = {
            "priorPartialSha256": REVIEWED_PARTIAL_SHA256,
            "reviewSha256": protocol["sameAttemptReview"]["sha256"], "firstNewOrdinal": REVIEWED_PREFIX_COUNT + 1,
            "newAttemptCount": sum(item["attemptCount"] for item in results[REVIEWED_PREFIX_COUNT:]),
            "newCliLaunchCount": sum(item["cliLaunchCount"] for item in results[REVIEWED_PREFIX_COUNT:]),
        }
    failures = validate_native_result(result, root)
    _require(not failures, "native normalized result failed semantic validation")
    _exclusive(ledger / ("normalized-assessment-remainder-result.json" if assessment_remainder else "normalized-catalog-remainder-result.json" if partial else "normalized-result.json"), _bytes(result))
    return result


def _validate_native_schema(value: Any, node: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    """Add real union validation to the reused closed-schema subset."""
    if "anyOf" in node:
        matched = False
        for branch in node["anyOf"]:
            try:
                _validate_native_schema(value, branch, schema)
                matched = True
                break
            except NativeObservationError:
                continue
        _require(matched, "native value does not match any closed union member")
        return
    if "$ref" in node:
        reference = node["$ref"]
        _require(reference.startswith("#/$defs/"), "unsupported native schema reference")
        _validate_native_schema(value, schema["$defs"][reference.removeprefix("#/$defs/")], schema)
        return
    legacy._validate_schema_value(value, node, schema, "native result")
    if type(value) is dict:
        for key, child in value.items():
            if key in node.get("properties", {}):
                _validate_native_schema(child, node["properties"][key], schema)
    elif type(value) is list and "items" in node:
        for child in value:
            _validate_native_schema(child, node["items"], schema)


def validate_native_result(document: Any, root: Path = REPOSITORY_ROOT) -> list[str]:
    """Check retained evidence consistency, not authenticity of an editable file."""
    try:
        protocol = _protocol(root)
        result_sha256 = hashlib.sha256(_bytes(document)).hexdigest()
        if result_sha256 == MERGED_ROUTING_SHA256:
            protocol = _merged_protocol(root)
        elif result_sha256 == FIXED_RESULT_SHA256:
            protocol = _fixed_protocol(root)
        elif result_sha256 == REVISION_FOUR_RESULT_SHA256:
            protocol = _revision_four_protocol(root)
        result_schema = _json(_read(root / RESULT_SCHEMA_RELATIVE))
        _validate_native_schema(document, result_schema, result_schema)
        _require(document["protocolDigest"] == protocol["protocolDigest"], "native result protocol mismatch")
        prior_results = document["priorResultSha256s"]
        _require(prior_results in [*[READ_PRIOR_RESULTS[:i] for i in range(8)], ASSESSMENT_PRIOR_RESULTS, CURRENT_PRIOR_RESULTS, FIXED_PRIOR_RESULTS, REVISION_FOUR_PRIOR_RESULTS], "invalid historical prefix")
        segment = document.get("executionSegment")
        material_segment = segment is not None and segment.get("kind") == "material-delivery"
        current_assessment = segment is not None and segment.get("kind") == "explicit-invocation-revision-1"
        revision_four = segment is not None and segment.get("kind") == _fixed_kind(True)
        fixed_acceptance = revision_four or (segment is not None and segment.get("kind") == _fixed_kind())
        contract = _fixed_contract(revision_four)
        chain = _fixed_attempt_history(root, revision_four) if fixed_acceptance else _attempt_history(root) if current_assessment else None
        _require((prior_results == CURRENT_PRIOR_RESULTS) == current_assessment, "current history requires its execution segment")
        _require((prior_results == contract["priorResultSha256s"]) == fixed_acceptance, "fixed history requires its execution segment")
        prior_count = chain["attempts"] if current_assessment or fixed_acceptance else 31 if material_segment else 20 if prior_results == ASSESSMENT_PRIOR_RESULTS else len(prior_results)
        _require(document["attemptCount"] == sum(item["attemptCount"] for item in document["caseResults"]),
                 "native attempt count mismatch")
        _require(document["cumulativeAttemptCount"] == prior_count + document["attemptCount"] <= (contract["priorAttempts"] + 16 if fixed_acceptance else CURRENT_ASSESSMENT["maximumCumulativeAttempts"] if current_assessment else 38 if material_segment else 16 + prior_count),
                 "native cumulative attempt budget mismatch")
        _require(sum(item["privateCapture"]["bytes"] for item in document["caseResults"]) <= PRIVATE_DIAGNOSTIC_LIMIT,
                 "private capture batch limit exceeded")
        _require(sum(item["operatorStderrCapture"]["bytes"] for item in document["caseResults"]) <= PRIVATE_DIAGNOSTIC_LIMIT,
                 "operator stderr batch limit exceeded")
        cases = legacy.load_golden_cases(root)
        fixtures = _input(root, protocol, "fixtureMatrix")
        model_schema = _input(root, protocol, "modelResponseSchema")
        envelope = _input(root, protocol, "promptEnvelope")
        seed = bytes.fromhex(document["materializationSeed"])
        segment = document.get("executionSegment")
        remainder = segment is not None and segment.get("firstNewOrdinal") == 11
        partial = _assessment_partial(root) if remainder else _reviewed_partial(root) if segment is not None and not (material_segment or current_assessment or fixed_acceptance) else None
        prefix_count = 10 if remainder else REVIEWED_PREFIX_COUNT
        if fixed_acceptance:
            _require(segment == {
                "kind": _fixed_kind(revision_four), "priorPartialSha256": FIXED_RESULT_SHA256 if revision_four else FIXED_REPLY_PRIORS[-1],
                "firstNewOrdinal": 1, "priorAttemptCount": contract["priorAttempts"],
                "authenticationSourceOrdinal": contract["authenticationSourceOrdinal"] if revision_four else 14,
                "newAttemptCount": document["attemptCount"], "newCliLaunchCount": document["cliLaunchCount"]
            }, "fixed acceptance provenance changed")
            _require(not any([r["ordinal"], r["materializationCommitmentSha256"]] in chain["identities"]
                             for r in document["caseResults"]), "fixed acceptance reused a historical case")
            _require((document["executionSource"] is not None) == (document["runMode"] == "actual"),
                     "fixed execution source and mode differ")
        elif current_assessment:
            _require(segment == {
                "kind": "explicit-invocation-revision-1", "priorPartialSha256": ASSESSMENT_REVISION_THREE["sha256"],
                "firstNewOrdinal": 1, "priorAttemptCount": chain["attempts"], "authenticationSourceOrdinal": 16,
                "newAttemptCount": document["attemptCount"], "newCliLaunchCount": document["cliLaunchCount"]
            } and document["attemptCount"] <= 16, "current assessment provenance or budget mismatch")
            _require(not any([r["ordinal"], r["materializationCommitmentSha256"]] in chain["identities"]
                             for r in document["caseResults"]), "current assessment reused a prior case input")
        elif material_segment:
            _assessment_remainder_result(root)
            _require(prior_results == ASSESSMENT_PRIOR_RESULTS and segment == {
                "kind": "material-delivery", "priorPartialSha256": ASSESSMENT_REMAINDER_BINDING["sha256"],
                "firstNewOrdinal": 10, "priorAttemptCount": 31, "authenticationSourceOrdinal": 9,
                "newAttemptCount": document["attemptCount"], "newCliLaunchCount": document["cliLaunchCount"]
            } and document["attemptCount"] <= 7, "material segment provenance or budget mismatch")
        elif remainder:
            _require(prior_results == ASSESSMENT_PRIOR_RESULTS and
                     document["materializationSeed"] == partial["materializationSeed"] and
                     document["authenticationMode"] == partial["authenticationMode"] and
                     segment == {"priorPartialSha256": ASSESSMENT_PARTIAL_BINDING["sha256"],
                         "firstNewOrdinal": 11, "priorAttemptCount": 30, "authenticationSourceOrdinal": 9,
                         "newAttemptCount": sum(item["attemptCount"] for item in document["caseResults"][10:]),
                         "newCliLaunchCount": sum(item["cliLaunchCount"] for item in document["caseResults"][10:])} and
                     segment["newAttemptCount"] <= 6 and document["cumulativeAttemptCount"] <= 36,
                     "assessment remainder provenance or budget mismatch")
        elif partial:
            _require(document["priorResultSha256s"] == READ_PRIOR_RESULTS and
                     document["materializationSeed"] == partial["materializationSeed"] and
                     document["authenticationMode"] == partial["authenticationMode"] and
                     segment == {"priorPartialSha256": REVIEWED_PARTIAL_SHA256,
                         "reviewSha256": protocol["sameAttemptReview"]["sha256"], "firstNewOrdinal": REVIEWED_PREFIX_COUNT + 1,
                         "newAttemptCount": sum(item["attemptCount"] for item in document["caseResults"][REVIEWED_PREFIX_COUNT:]),
                         "newCliLaunchCount": sum(item["cliLaunchCount"] for item in document["caseResults"][REVIEWED_PREFIX_COUNT:])},
                     "remainder provenance or budget mismatch")
        stopped = False
        for ordinal, (case, record) in enumerate(zip(cases, document["caseResults"]), 1):
            _require(record["ordinal"] == ordinal and record["caseId"] == case["id"], "native result case order mismatch")
            if partial and ordinal <= prefix_count:
                _require(record == partial["caseResults"][ordinal - 1], "reviewed prefix facts changed")
                continue  # Exact old bytes were validated under their original implementation/protocol.
            definition = _definition(fixtures, ordinal)
            material = materialize_native_case_contract(root=root, materialization_seed=seed, ordinal=ordinal,
                protocol_digest=protocol["protocolDigest"], model_schema=model_schema,
                prompt_envelope=envelope, request=case["request"])
            expected = _blank_case(case, material, seed, protocol, definition, root=root)
            _require(set(record) == set(expected), "current case record fields are not closed")
            _require(record["explicitInvocation"] == expected["explicitInvocation"],
                     "native explicit invocation binding mismatch")
            for field in ("opaqueBindingSha256", "modelResponseSchemaSha256", "casePromptSha256", "materializationCommitmentSha256"):
                _require(record[field] == expected[field], "native materialization binding mismatch")
            status = record["status"]
            if material_segment and ordinal < 10:
                _require(record == expected, "material segment attempted or inherited an out-of-scope case")
                continue
            if stopped:
                _require(status == "NOT-RUN", "native result continued after unreliable failure")
            if status == "NOT-RUN":
                _require(record == expected, "unstarted native case carries observed facts")
                stopped = True
                continue
            reads = record["publicReads"]
            _require((len(reads) == record["readonlyCommandCount"]) if record["evidenceExtraction"]["stream"] == "valid"
                     else not reads, "public reads lack strict stream provenance")
            _require([read["eventOrdinal"] for read in reads] == sorted({read["eventOrdinal"] for read in reads}),
                     "public read completion ordinals must be unique and ordered")
            public_paths = {entry["path"]: entry["contentUtf8"].encode("utf-8") for entry in definition["files"]}
            for read in reads:
                relative = Path(read["path"])
                _require(not relative.is_absolute() and ".." not in relative.parts and
                         1 <= read["eventOrdinal"] <= record["executionDiagnostics"]["eventCount"],
                         "public read identifier is invalid")
                if read["source"] == "fixture":
                    _require(read["path"] in public_paths, "unbound public fixture read")
                    source_bytes = public_paths[read["path"]]
                else:
                    evidence = _json(_read(root / STATIC_BUNDLE_EVIDENCE_RELATIVE))
                    manifest = evidence["bundleManifest"]
                    inventory = {entry["path"] for entry in manifest["runtimeFiles"]} | {".codex-plugin/plugin.json", "BUNDLE-MANIFEST.json"}
                    _require(ordinal != 11 and read["path"] in inventory and
                             (read["source"] != "discovery" or relative.parts[0] == "skills"),
                             "unbound installed public read")
                    if read["path"] == ".codex-plugin/plugin.json":
                        source_bytes = (json.dumps(manifest["derivedPluginManifest"]["fields"], ensure_ascii=True, indent=2) + "\n").encode("ascii")
                    elif read["path"] == "BUNDLE-MANIFEST.json":
                        source_bytes = (json.dumps(manifest, ensure_ascii=True, indent=2) + "\n").encode("ascii")
                    else:
                        source_bytes = _read(root / relative)
                if read["range"] is not None:
                    first, last = read["range"]
                    _require(1 <= first <= last <= 100000, "public read line range invalid")
                    pieces = source_bytes.split(b"\n")
                    lines = [part + b"\n" for part in pieces[:-1]] + ([pieces[-1]] if pieces[-1] else [])
                    source_bytes = b"".join(lines[first - 1:last])
                _require(read["bytes"] == len(source_bytes), "public read length differs from bound source")
            command = record["operatorReadCapture"]
            _require(command == _private_capture() or (prior_results in (ASSESSMENT_PRIOR_RESULTS, CURRENT_PRIOR_RESULTS, FIXED_PRIOR_RESULTS, REVISION_FOUR_PRIOR_RESULTS) and
                     status == "INCOMPLETE" and record["executionDiagnostics"]["streamAssertion"] in READ_REJECTIONS),
                     "operator command retention lacks a read rejection")
            _require(command["status"] != "saved" or command["bytes"] > 0, "empty command capture")
            _require(command["status"] != "write-failed" or record["executionDiagnostics"]["cleanupFailed"],
                     "command capture failure lost cleanup state")
            private = record["privateCapture"]
            _require(private["status"] not in {"not-requested", "no-diagnostics"} or
                     (private["bytes"] == 0 and not private["truncated"]), "empty private capture has content")
            _require(private["status"] != "omitted" or (private["bytes"] == 0 and private["truncated"]),
                     "omitted private capture lacks truncation")
            _require(private["status"] != "saved" or private["bytes"] > 0, "saved private capture is empty")
            _require(private["status"] != "write-failed" or
                     (status == "INCOMPLETE" and record["executionDiagnostics"]["cleanupFailed"]),
                     "failed private capture was accepted")
            _require(private["status"] == "not-requested" or prior_results in [PRIOR_RESULTS[:3], PRIOR_RESULTS, MODEL_PRIOR_RESULTS, STDERR_PRIOR_RESULTS, READ_PRIOR_RESULTS, ASSESSMENT_PRIOR_RESULTS, CURRENT_PRIOR_RESULTS, FIXED_PRIOR_RESULTS, REVISION_FOUR_PRIOR_RESULTS],
                     "operator capture lacks linked history authorization")
            facts = record["executionDiagnostics"]
            stderr = record["operatorStderrCapture"]
            _require(stderr == _stderr_capture() or prior_results in (STDERR_PRIOR_RESULTS, READ_PRIOR_RESULTS, ASSESSMENT_PRIOR_RESULTS, CURRENT_PRIOR_RESULTS, FIXED_PRIOR_RESULTS, REVISION_FOUR_PRIOR_RESULTS),
                     "operator stderr capture lacks linked continuation authorization")
            if prior_results in (STDERR_PRIOR_RESULTS, READ_PRIOR_RESULTS, ASSESSMENT_PRIOR_RESULTS, CURRENT_PRIOR_RESULTS, FIXED_PRIOR_RESULTS, REVISION_FOUR_PRIOR_RESULTS) and record["cliLaunchCount"]:
                _require(stderr["status"] != "not-requested", "captured client stderr was not retained")
            if stderr["status"] == "not-requested":
                _require(stderr == _stderr_capture(), "unrequested stderr capture has facts")
            elif stderr["status"] == "empty":
                _require(stderr["bytes"] == 0 and not stderr["truncated"] and
                         stderr["encoding"] == "utf-8" and facts["stderrBytes"] == 0,
                         "empty stderr capture disagrees with process")
            else:
                _require(stderr["encoding"] != "not-observed" and facts["stderrBytes"] > 0,
                         "stderr capture lacks captured input")
                _require(stderr["status"] != "saved" or stderr["bytes"] > 0, "saved stderr is empty")
                _require(stderr["status"] != "omitted" or (stderr["bytes"] == 0 and stderr["truncated"]),
                         "omitted stderr lacks truncation")
                _require(stderr["status"] != "write-failed" or (status == "INCOMPLETE" and facts["cleanupFailed"]),
                         "failed stderr retention was accepted")
            _require(facts["streamAssertion"] in STREAM_ASSERTIONS and
                     (facts["streamAssertion"] != "none" or facts["streamEventOrdinal"] is None),
                     "native stream assertion location is invalid")
            _require(facts["streamEventOrdinal"] is None or
                     1 <= facts["streamEventOrdinal"] <= facts["eventCount"],
                     "native stream assertion exceeds observed events")
            _require(facts["streamAssertion"] == "none" or
                     (status == "INCOMPLETE" and facts["category"] != "none"),
                     "native parser assertion cannot complete")
            if facts["streamAssertion"] in READ_REJECTIONS[1:]:
                _require(facts["streamEventOrdinal"] is not None and
                         facts["policyReason"] == "read-contract-rejected" and
                         facts["category"] != "none" and
                         "command_execution" in facts["itemTypes"] and
                         record["evidenceExtraction"]["stream"] == "invalid",
                         "read rejection lacks matching source and stream facts")
            _require(facts["policyReason"] != "read-contract-rejected" or
                     facts["streamAssertion"] in READ_REJECTIONS[1:],
                     "read rejection lost its predicate")
            _require(record["cliLaunchCount"] <= record["attemptCount"], "launch lacks consumed attempt")
            _require(facts["eventCount"] >= len(facts["eventTypes"]), "event summary count mismatch")
            _require(not facts["itemTypes"] or (any(kind.startswith("item.") for kind in facts["eventTypes"]) and
                     len(facts["itemTypes"]) <= facts["eventCount"]), "item summary lacks matching events")
            _require(0 <= facts["preTurnDiagnosticCount"] <= facts["diagnosticItemCount"] <= facts["eventCount"],
                     "diagnostic item counts disagree")
            _require((facts["diagnosticItemCount"] == 0 or "error" in facts["itemTypes"]) and
                     ("error" not in facts["itemTypes"] or facts["diagnosticItemCount"] > 0 or
                      facts["policyReason"] in {"event-shape-rejected", "item-lifecycle-rejected"}),
                     "diagnostic items lack matching count")
            classes = facts["hostDiagnosticClasses"]
            _require((("upstream-error" in classes) == ("error" in facts["eventTypes"])) or
                     (facts["policyReason"] == "event-shape-rejected" and "upstream-error" not in classes),
                     "upstream error summary differs from events")
            _require(bool(set(classes) - {"upstream-error"}) == (facts["diagnosticItemCount"] > 0) and
                     len(set(classes) - {"upstream-error"}) <= facts["diagnosticItemCount"],
                     "diagnostic classes lack matching items")
            _require(facts["inputBytesSent"] <= len(material.prompt_bytes), "input count exceeds prompt")
            if record["attemptCount"]:
                if facts["inputFullyDelivered"] is True:
                    _require(facts["inputBytesSent"] == len(material.prompt_bytes), "complete input count mismatch")
                elif facts["inputFullyDelivered"] is False:
                    _require(facts["inputBytesSent"] < len(material.prompt_bytes), "incomplete input count mismatch")
            _require(facts["signal"] == (-facts["returnCode"] if facts["returnCode"] is not None and
                     facts["returnCode"] < 0 else None), "signal and return code disagree")
            if facts["timedOut"]:
                _require(facts["category"] != "none", "timeout cannot succeed")
            if facts["cleanupFailed"]:
                _require(status == "INCOMPLETE" and facts["category"] != "none", "cleanup failure cannot complete")
            if status == "INCOMPLETE":
                _require(facts["category"] == record["diagnostic"] and facts["category"] != "none",
                         "incomplete diagnostic differs from first cause")
                stopped = True
                _require(record["diagnostic"] not in {"none", "not-run", "semantic-mismatch"}, "incomplete case lacks cause")
            for field in ("fixtureBeforeSha256", "fixtureAfterSha256"):
                if record[field] is not None:
                    _require(record[field] == legacy._expected_realized_fixture_digest(definition), "native fixture record mismatch")
            if ordinal == 11:
                _require(record["installation"] in {"absent", "not-checked"} and
                         record["packageBeforeSha256"] is None and record["packageAfterSha256"] is None,
                         "no-plugin control claimed an installation")
            else:
                for field in ("packageBeforeSha256", "packageAfterSha256"):
                    if record[field] is not None:
                        _require(record[field] == protocol["bundle"]["packageSha256"],
                                 "native package record is not bound to the verified bundle")
            if record["cliLaunchCount"]:
                _require(record["modelMetadataBefore"] is not None and record["authentication"] == "chatgpt" and
                         record["installation"] == ("absent" if ordinal == 11 else "verified") and
                         record["fixtureBeforeSha256"] is not None and
                         (ordinal == 11 or record["packageBeforeSha256"] is not None),
                         "native launch lacks verified prerequisites")
            extraction = record["evidenceExtraction"]
            _require((record["observed"] is not None) == (extraction["response"] == "valid"),
                     "response facts lack validation provenance")
            if extraction["stream"] != "valid":
                _require(record["readonlyCommandCount"] == 0 and record["observed"] is None,
                         "unvalidated stream carries accepted evidence")
            if extraction["response"] == "valid":
                _require(extraction["stream"] == "valid" and facts["finalOutputVerified"],
                         "response lacks closed stream or official final output")
                response = {**record["observed"], "opaqueCaseBinding": material.token}
                _validate_native_response(response, model_schema, material.token)
            if extraction["postcheck"] == "valid":
                _require(record["modelMetadataAfter"] is not None and record["fixtureAfterSha256"] is not None and
                         record["fixtureAfterSha256"] == record["fixtureBeforeSha256"] and
                         record["packageAfterSha256"] == record["packageBeforeSha256"],
                         "postcheck lacks stable inputs")
            if status in {"PASS", "FAIL"}:
                _require(record["modelMetadataBefore"] is not None and record["modelMetadataAfter"] is not None,
                         "completed case lacks pre/post official Direct metadata")
                _require(all(value == "valid" for value in extraction.values()), "complete case lacks evidence checks")
                _require(facts["category"] == "none" and facts["returnCode"] == 0 and
                         facts["finalOutputVerified"] and facts["streamAssertion"] == "none" and
                         facts["policyReason"] == "none" and
                         set(facts["itemTypes"]) <= {"reasoning", "agent_message", "command_execution", "error"} and
                         _diagnostic_outcome(facts) is None and
                         facts["inputFullyDelivered"] is True and not facts["observerTerminated"] and
                         facts["stderrClassification"] in {"empty", "known-nonfatal"} and
                         "turn.completed" in facts["eventTypes"] and "turn.failed" not in facts["eventTypes"] and
                         "unknown" not in facts["eventTypes"], "completed case lacks successful execution facts")
                _require(record["cliLaunchCount"] == 1 and record["authentication"] == "chatgpt" and
                         record["installation"] == ("absent" if ordinal == 11 else "verified") and
                         record["terminal"] == "turn.completed", "completed native case lacks required evidence")
                _require(record["fixtureBeforeSha256"] is not None and
                         record["fixtureBeforeSha256"] == record["fixtureAfterSha256"], "completed case lacks stable fixture")
                if ordinal != 11:
                    _require(record["packageBeforeSha256"] is not None and
                             record["packageBeforeSha256"] == record["packageAfterSha256"], "completed case lacks stable package")
                response = dict(record["observed"])
                response["opaqueCaseBinding"] = material.token
                mismatches = legacy.validate_model_response(response, case, material.token, model_schema)
                if response["selectedRoutes"] != sorted(response["selectedRoutes"], key=lambda value: value.encode("utf-8")):
                    mismatches.append("selectedRoutes report order is not UTF-8 lexical")
                _require((status == "PASS") == (not mismatches), "native semantic outcome differs from frozen case")
                _require(record["diagnostic"] == ("none" if status == "PASS" else "semantic-mismatch"), "native outcome diagnostic mismatch")
            if record["cliLaunchCount"] == 0:
                _require(record["observed"] is None and record["terminal"] == "not-observed" and
                         record["readonlyCommandCount"] == 0, "unlaunched case has model observations")
        _require(document["cliLaunchCount"] == sum(item["cliLaunchCount"] for item in document["caseResults"]),
                 "native launch count mismatch")
        _require(document["materializationCommitmentRoot"] == legacy._materialization_commitment_root(
            [item["materializationCommitmentSha256"] for item in document["caseResults"]]), "native commitment root mismatch")
        statuses = [item["status"] for item in document["caseResults"]]
        expected_status = "INCOMPLETE" if document["runMode"] == "simulated" or any(
            value in {"NOT-RUN", "INCOMPLETE"} for value in statuses) else ("FAIL" if "FAIL" in statuses else "PASS")
        _require(document["status"] == expected_status, "native overall status mismatch")
        _require(document["hostClaim"] == (document["runMode"] == "actual" and expected_status == "PASS"),
                 "simulated or incomplete result cannot claim host PASS")
        return []
    except (OSError, ValueError, KeyError, TypeError, NativeObservationError) as error:
        return [str(error)]


def main(argv: Sequence[str] | None = None, *, root: Path = REPOSITORY_ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--login-commands", action="store_true")
    group.add_argument("--share-test-auth", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--prepare-diagnostic-followup", action="store_true")
    group.add_argument("--prepare-diagnostic-continuation", action="store_true")
    group.add_argument("--prepare-operator-diagnostics", action="store_true")
    group.add_argument("--prepare-schema-followup", action="store_true")
    group.add_argument("--prepare-model-followup", action="store_true")
    group.add_argument("--prepare-stderr-followup", action="store_true")
    group.add_argument("--prepare-read-followup", action="store_true")
    group.add_argument("--prepare-stderr-review-resume", action="store_true")
    group.add_argument("--prepare-assessment-remainder", action="store_true")
    group.add_argument("--prepare-material-segment", action="store_true")
    group.add_argument("--prepare-current-assessment", action="store_true")
    group.add_argument("--prepare-fixed-acceptance", action="store_true")
    group.add_argument("--prepare-revision-four-acceptance", action="store_true")
    parser.add_argument("--revision-four-acceptance", action="store_true")
    parser.add_argument("--fixed-acceptance", action="store_true")
    parser.add_argument("--current-assessment", action="store_true")
    parser.add_argument("--previous-run-root", type=Path)
    parser.add_argument("--material-segment", action="store_true")
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--codex", type=Path)
    parser.add_argument("--authorize-local-install", action="store_true")
    parser.add_argument("--authorize-model-calls", action="store_true")
    parser.add_argument("--authorize-test-auth-copy", action="store_true")
    parser.add_argument("--reuse-test-auth", action="store_true")
    parser.add_argument("--diagnostic-followup", action="store_true")
    parser.add_argument("--diagnostic-continuation", action="store_true")
    parser.add_argument("--private-diagnostics", action="store_true")
    parser.add_argument("--operator-diagnostics", action="store_true")
    parser.add_argument("--schema-followup", action="store_true")
    parser.add_argument("--model-followup", action="store_true")
    parser.add_argument("--stderr-followup", action="store_true")
    parser.add_argument("--read-followup", action="store_true")
    parser.add_argument("--resume-stderr-review", action="store_true")
    parser.add_argument("--assessment-batch", action="store_true")
    parser.add_argument("--assessment-remainder", action="store_true")
    parser.add_argument("--preserve-existing-test-auth", type=int, nargs="*", default=[])
    args = parser.parse_args(argv)
    try:
        if args.prepare_fixed_acceptance or args.prepare_revision_four_acceptance:
            _require(all(x is not None for x in (args.run_root, args.previous_run_root, args.bundle_root)),
                     "fixed preparation requires registered roots and the frozen package")
            prepare_fixed_acceptance(root, args.run_root, args.previous_run_root, args.bundle_root,
                                     authorize_install=args.authorize_local_install,
                                     authorize_copy=args.authorize_test_auth_copy, revision_four=args.prepare_revision_four_acceptance)
            print("Fixed 16-plus-3 window registered; routing states prepared; no model started.")
        elif args.prepare_current_assessment:
            _require(args.run_root is not None and args.previous_run_root is not None, "assessment requires both registered roots")
            prepare_current_assessment(root, args.run_root, args.previous_run_root,
                                       authorize_install=args.authorize_local_install,
                                       authorize_copy=args.authorize_test_auth_copy)
            print("Fresh revision-3 assessment prepared; historical sessions retained; no model started.")
        elif args.prepare_material_segment:
            _require(args.run_root is not None and args.previous_run_root is not None, "material segment requires both registered roots")
            prepare_material_segment(root, args.run_root, args.previous_run_root,
                                     authorize_install=args.authorize_local_install,
                                     authorize_copy=args.authorize_test_auth_copy)
            print("Fresh material segment prepared; historical sessions retained; no model started.")
        elif args.prepare_assessment_remainder:
            _require(args.run_root is not None, "assessment remainder requires the registered run root")
            prepare_assessment_remainder(root, args.run_root)
            print("Assessment remainder prepared; original hard stop retained; no client started.")
        elif args.prepare_stderr_review_resume:
            _require(args.run_root is not None, "review resume requires the registered run root")
            prepare_stderr_review_resume(root, args.run_root)
            print("Reviewed remainder prepared; prior attempts and result preserved; no client started.")
        elif args.prepare_diagnostic_followup or args.prepare_diagnostic_continuation or args.prepare_operator_diagnostics or args.prepare_schema_followup or args.prepare_model_followup or args.prepare_stderr_followup or args.prepare_read_followup:
            _require(args.run_root is not None, "followup requires the existing test root")
            prepare_diagnostic_followup(root, args.run_root, continuation=args.prepare_diagnostic_continuation,
                                        operator_diagnostics=args.prepare_operator_diagnostics, schema_followup=args.prepare_schema_followup, model_followup=args.prepare_model_followup, stderr_followup=args.prepare_stderr_followup, read_followup=args.prepare_read_followup)
            print("Diagnostic followup prepared; historical state preserved; no client started.")
        elif args.prepare:
            _require(all(value is not None for value in (args.run_root, args.bundle_root, args.codex)),
                     "prepare requires explicit run root, bundle and CLI")
            prepare_native_run(root, args.run_root, args.bundle_root, args.codex,
                               authorize_install=args.authorize_local_install)
            print("Native preparation complete; no login or model request performed.")
        elif args.share_test_auth:
            _require(args.run_root is not None, "test-auth copy requires a prepared run root")
            share_test_authentication(root, args.run_root, authorize_copy=args.authorize_test_auth_copy,
                                      preserve_existing=args.preserve_existing_test_auth)
            print("Test authentication copied to registered homes; no content reported; no model started.")
        elif args.login_commands:
            _require(args.run_root is not None, "login commands require a prepared run root")
            print(json.dumps(login_commands(root, args.run_root), indent=2))
        elif args.run:
            _require(args.run_root is not None, "run requires a prepared run root")
            result = run_native_observation(root, args.run_root, authorize_model_calls=args.authorize_model_calls,
                                            reuse_test_auth=args.reuse_test_auth, followup=args.diagnostic_followup,
                                            continuation=args.diagnostic_continuation, private_diagnostics=args.private_diagnostics,
                                            operator_diagnostics=args.operator_diagnostics, schema_followup=args.schema_followup, model_followup=args.model_followup, stderr_followup=args.stderr_followup, read_followup=args.read_followup, resume_stderr_review=args.resume_stderr_review, assessment_batch=args.assessment_batch, assessment_remainder=args.assessment_remainder, material_segment=args.material_segment, current_assessment=args.current_assessment, fixed_acceptance=args.fixed_acceptance, revision_four=args.revision_four_acceptance)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        else:
            failures = validate_native_protocol(root)
            if failures:
                print("\n".join(failures), file=sys.stderr)
                return 1
            print("Native observation protocol: PASS (static only; no client started).")
        return 0
    except (OSError, ValueError, KeyError, NativeObservationError) as error:
        print(f"Native observation incomplete: {error}", file=sys.stderr)
        return 1
