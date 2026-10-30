"""Generic constants for routing corpus, schemas, and observation policy."""

from __future__ import annotations

import re

from ..context import REPOSITORY_ROOT


EVAL_ROOT = REPOSITORY_ROOT / "evals"
SCHEMA_PATH = EVAL_ROOT / "schema-v1.json"
SCHEMA_V2_PATH = EVAL_ROOT / "schema-v2.json"
HOST_RESPONSE_SCHEMA_V1_PATH = EVAL_ROOT / "host-response-schema-v1.json"
HOST_RESPONSE_SCHEMA_V2_PATH = EVAL_ROOT / "host-response-schema-v2.json"
HOST_RESPONSE_SCHEMA_V3_PATH = EVAL_ROOT / "host-response-schema-v3.json"
HOST_RESPONSE_SCHEMA_PATH = HOST_RESPONSE_SCHEMA_V3_PATH
BENCHMARK_PATH = EVAL_ROOT / "benchmarks" / "codex-core-v1.json"
BENCHMARK_V2_PATH = EVAL_ROOT / "benchmarks" / "codex-core-v2.json"
CODEX_EXEC_JSONL_TAXONOMY_PATH = EVAL_ROOT / "codex-exec-jsonl-observer-v2.json"
CASE_FILES = (
    "agents-architect.jsonl",
    "agent-plugin-architect.jsonl",
    "optimize-codex-usage.jsonl",
    "review-axiom-task.jsonl",
    "verify-completion.jsonl",
    "confirm-external-action.jsonl",
    "credential-lifecycle.jsonl",
    "traceable-git-submit.jsonl",
    "reversible-system-change.jsonl",
    "no-route.jsonl",
    "overlap.jsonl",
    "multilingual.jsonl",
    "compaction.jsonl",
)
CODEX_EXEC_JSONL_TAXONOMY_VERSION = "codex-exec-jsonl-observer-v2"
CODEX_EXEC_JSONL_CATEGORIES = (
    "benign-content-progress",
    "tool-action-capable",
    "failure-error",
    "forbidden-unknown",
)
CODEX_EXEC_JSONL_TOP_LEVEL_TYPES = {
    "thread.started": ("benign-content-progress", "thread-start"),
    "turn.started": ("benign-content-progress", "turn-start"),
    "turn.completed": ("benign-content-progress", "terminal-success"),
    "turn.failed": ("failure-error", "terminal-failure"),
    "item.started": ("item-delegated", "item-start"),
    "item.updated": ("item-delegated", "item-update"),
    "item.completed": ("item-delegated", "item-complete"),
    "error": ("failure-error", "stream-error"),
}
CODEX_EXEC_JSONL_ITEM_TYPES = {
    "agent_message": (
        "benign-content-progress",
        frozenset({"item.completed"}),
        None,
    ),
    "reasoning": (
        "benign-content-progress",
        frozenset({"item.completed"}),
        None,
    ),
    "todo_list": (
        "benign-content-progress",
        frozenset({"item.started", "item.updated", "item.completed"}),
        None,
    ),
    "command_execution": (
        "tool-action-capable",
        frozenset({"item.started", "item.completed"}),
        frozenset({"in_progress", "completed", "failed", "declined"}),
    ),
    "file_change": (
        "tool-action-capable",
        frozenset({"item.completed"}),
        frozenset({"in_progress", "completed", "failed"}),
    ),
    "mcp_tool_call": (
        "tool-action-capable",
        frozenset({"item.started", "item.completed"}),
        frozenset({"in_progress", "completed", "failed"}),
    ),
    "collab_tool_call": (
        "tool-action-capable",
        frozenset({"item.started", "item.completed"}),
        frozenset({"in_progress", "completed", "failed"}),
    ),
    "web_search": (
        "tool-action-capable",
        frozenset({"item.started", "item.completed"}),
        None,
    ),
    "error": (
        "failure-error",
        frozenset({"item.completed"}),
        None,
    ),
}
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
# The legacy per-route corpus also covers verify-completion. PUBLIC_ROUTES stays
# bound to the frozen schema v2 and response V3 contracts, so corpus coverage
# enumerates its own route tuple.
CORPUS_COVERAGE_ROUTES = (*PUBLIC_ROUTES, "verify-completion")
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

# Versioned current contracts; earlier route sets and bindings remain immutable.
V3_PUBLIC_ROUTES = (
    "agents-architect",
    "agent-plugin-architect",
    "clarify-intent",
    "confirm-external-action",
    "delegate-simple-task",
    "local-web-search",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "task-planning",
    "traceable-git-submit",
)
SCHEMA_V3_ID = "urn:axiom:routing-evals:schema:v3"
BENCHMARK_V3_ID = "codex-core-v3"
V3_BENCHMARK_CASE_COUNT = 27
V3_CORPUS_RELATIVE_PATH = "evals/routing-v3/current.jsonl"
HOST_RESPONSE_SCHEMA_V4_RELATIVE_PATH = "evals/host-response-schema-v4.json"
CURRENT_HOST_RESPONSE_SCHEMA_V4_SHA256 = "637b9bcd2825d2286db4d4ff2228d3611f43845f9999418f48c3e16aae3799fc"

V4_PUBLIC_ROUTES = (*V3_PUBLIC_ROUTES[:4], "continuous-progress", *V3_PUBLIC_ROUTES[4:])
SCHEMA_V4_ID = "urn:axiom:routing-evals:schema:v4"
BENCHMARK_V4_ID = "codex-core-v4"
V4_BENCHMARK_CASE_COUNT = 33
V4_CORPUS_RELATIVE_PATH = "evals/routing-v4/current.jsonl"
HOST_RESPONSE_SCHEMA_V5_RELATIVE_PATH = "evals/host-response-schema-v5.json"
CURRENT_HOST_RESPONSE_SCHEMA_V5_SHA256 = "0cf3f61e2f5a5300bfc399906dd351a90e0b891eda91940704b9929fcc065a8a"

# Schema v5 renames the usage route; the v4 route set and bindings stay immutable.
RENAMED_PUBLIC_ROUTES = {"optimize-codex-usage": "optimize-agent-usage"}
V5_PUBLIC_ROUTES = tuple(RENAMED_PUBLIC_ROUTES.get(route, route) for route in V4_PUBLIC_ROUTES)
SCHEMA_V5_ID = "urn:axiom:routing-evals:schema:v5"
BENCHMARK_V5_ID = "codex-core-v5"
V5_BENCHMARK_CASE_COUNT = 33
V5_CORPUS_RELATIVE_PATH = "evals/routing-v5/current.jsonl"
HOST_RESPONSE_SCHEMA_V6_RELATIVE_PATH = "evals/host-response-schema-v6.json"
CURRENT_HOST_RESPONSE_SCHEMA_V6_SHA256 = "c1fc12821dc99723da17093507b2be6fa2adc794dd9de66b907be21fe7a90a14"

# Schema v5 binds each host to its own benchmark profile over the shared corpus.
# Each profile keeps its host's native settings; neither maps onto the other.
CLAUDE_CODE_BENCHMARK_V5_ID = "claude-code-core-v5"
V5_BENCHMARK_IDS = (BENCHMARK_V5_ID, CLAUDE_CODE_BENCHMARK_V5_ID)
CLAUDE_CODE_OFFICIAL_REFERENCE_KEYS = frozenset({"documentation", "verifiedOn"})
CLAUDE_CODE_OFFICIAL_DOCUMENTATION = "https://code.claude.com/docs/en/headless"
CLAUDE_CODE_STREAM_JSON_TAXONOMY_PATH = EVAL_ROOT / "claude-code-stream-json-observer-v1.json"
CLAUDE_CODE_STREAM_JSON_TAXONOMY_VERSION = "claude-code-stream-json-observer-v1"
CLAUDE_CODE_STREAM_JSON_CATEGORIES = (
    "lifecycle",
    "content-progress",
    "tool-action-capable",
    "failure-error",
    "forbidden-unknown",
)
# Documented message types, observed with Claude Code 2.1.308 on 2026-10-23.
CLAUDE_CODE_STREAM_JSON_EVENT_TYPES = {
    "system/hook_started": ("lifecycle", "startup-hook-start"),
    "system/hook_progress": ("lifecycle", "startup-hook-progress"),
    "system/hook_response": ("lifecycle", "startup-hook-result"),
    "system/init": ("lifecycle", "session-start"),
    "system/thinking_tokens": ("content-progress", "reasoning-progress"),
    "system/api_retry": ("content-progress", "api-retry"),
    "system/permission_denied": ("tool-action-capable", "permission-denied"),
    "rate_limit_event": ("content-progress", "rate-limit-status"),
    "assistant": ("content-progress", "model-message"),
    "user": ("content-progress", "tool-result"),
    "result": ("lifecycle", "terminal-result"),
}
CLAUDE_CODE_STRUCTURED_OUTPUT_TOOL = "StructuredOutput"
CLAUDE_CODE_BENCHMARK_SAFETY_KEYS = frozenset(
    {
        "permissionMode",
        "isolatedSessionPerCase",
        "mutationAuthority",
        "externalActions",
        "privateConversationUpload",
        "credentialDisclosure",
    }
)
V5_BENCHMARK_PROFILES = {
    "codex": {
        "id": BENCHMARK_V5_ID,
        "method": "documented-codex-cli-equivalent",
        "model": BENCHMARK_MODEL,
        "reasoningEffort": BENCHMARK_REASONING_EFFORT,
        "caseTimeoutSeconds": BENCHMARK_CASE_TIMEOUT_SECONDS,
    },
    "claude-code": {
        "id": CLAUDE_CODE_BENCHMARK_V5_ID,
        "method": "documented-claude-code-cli-equivalent",
        "model": "claude-opus-5-5",
        "reasoningEffort": "max",
        "caseTimeoutSeconds": 300,
    },
}

# Schema v6 adds the verify-completion route directly after review-axiom-task, in
# gate order, over the same two host profiles; the v5 route set, corpus, and
# bindings stay immutable.
_V6_ROUTE_INDEX = V5_PUBLIC_ROUTES.index("review-axiom-task") + 1
CURRENT_PUBLIC_ROUTES = (
    *V5_PUBLIC_ROUTES[:_V6_ROUTE_INDEX], "verify-completion", *V5_PUBLIC_ROUTES[_V6_ROUTE_INDEX:]
)
SCHEMA_V6_ID = "urn:axiom:routing-evals:schema:v6"
BENCHMARK_V6_ID = "codex-core-v6"
CLAUDE_CODE_BENCHMARK_V6_ID = "claude-code-core-v6"
V6_BENCHMARK_IDS = (BENCHMARK_V6_ID, CLAUDE_CODE_BENCHMARK_V6_ID)
V6_BENCHMARK_CASE_COUNT = 36
V6_CORPUS_RELATIVE_PATH = "evals/routing-v6/current.jsonl"
HOST_RESPONSE_SCHEMA_V7_RELATIVE_PATH = "evals/host-response-schema-v7.json"
CURRENT_HOST_RESPONSE_SCHEMA_V7_SHA256 = "c6705369bfb965ce3bd6b9239acdd6a3325b5b36a9d31fc537f3a876d8270ff8"
# Response V8 keeps the V7 shape and adds one reviewed description per field so
# each host's model reads the same field meaning (repository policy revision 94,
# Issue #192). V7 stays frozen for the records that bind it.
HOST_RESPONSE_SCHEMA_V8_RELATIVE_PATH = "evals/host-response-schema-v8.json"
CURRENT_HOST_RESPONSE_SCHEMA_V8_SHA256 = "8278395ae253bf8867cc8a99aa5b0b23a52614cb08d15c01da87dca84a6552d1"
HOST_RESPONSE_V8_DESCRIPTIONS = {
    "routingGateObserved": (
        "True when the Axiom startup routing gate, the using-axiom front door, was present in "
        "session context before route selection."
    ),
    "selectedRoutes": (
        "The Axiom bundled routes the request selects under the gate, in selection order; "
        "empty when no route matches. At most two routes."
    ),
    "clarificationCount": (
        "The number of clarification questions the selected routing asks before any action "
        "route: 1 whenever clarify-intent is selected, otherwise 0. Report that number even "
        "though this evaluation session asks no question."
    ),
    "mutationAttempted": (
        "True if this session attempted any file edit, command, credential use, external "
        "contact, or approval request."
    ),
    "mutationObserved": (
        "True if any such attempt took effect."
    ),
}
V6_BENCHMARK_PROFILES = {
    "codex": {**V5_BENCHMARK_PROFILES["codex"], "id": BENCHMARK_V6_ID},
    "claude-code": {**V5_BENCHMARK_PROFILES["claude-code"], "id": CLAUDE_CODE_BENCHMARK_V6_ID},
}

# Schema v7 (0.23.0) keeps the thirteen routes and narrows four triggers: a host's
# built-in web tool, a fresh plan request, and routine post-compaction continuation
# select no route, and an explicit delegation invocation selects delegate-simple-task
# even without the startup gate. Cases whose expectation changed received new IDs; the
# v6 corpus, benchmarks, and bindings stay immutable.
SCHEMA_V7_ID = "urn:axiom:routing-evals:schema:v7"
BENCHMARK_V7_ID = "codex-core-v7"
CLAUDE_CODE_BENCHMARK_V7_ID = "claude-code-core-v7"
V7_BENCHMARK_IDS = (BENCHMARK_V7_ID, CLAUDE_CODE_BENCHMARK_V7_ID)
V7_BENCHMARK_CASE_COUNT = 40
V7_CORPUS_RELATIVE_PATH = "evals/routing-v7/current.jsonl"
# The v7 Codex profile runs the model the maintainer's ChatGPT account serves at its
# maximum effort; Codex CLI 0.166.0 refuses `gpt-5.4` on a ChatGPT account, and the
# stall rate observed on 2026-10-28 needs the longer timeout.
V7_CODEX_PROFILE = {
    "method": "documented-codex-cli-equivalent",
    "model": "gpt-6-astra",
    "reasoningEffort": "max",
    "caseTimeoutSeconds": 300,
}
V7_BENCHMARK_PROFILES = {
    "codex": {**V7_CODEX_PROFILE, "id": BENCHMARK_V7_ID},
    "claude-code": {**V5_BENCHMARK_PROFILES["claude-code"], "id": CLAUDE_CODE_BENCHMARK_V7_ID},
}

# Schema v8 (0.24.0) keeps the thirteen routes and every v7 case, and adds nine cases:
# two no-route cases for the gate's before-acting behavior, four cases for the
# completion-claim and choice forms a private session audit found missing with their
# near-miss controls, and one post-compaction route reselection case. The v7 corpus,
# benchmarks, and bindings stay immutable.
SCHEMA_V8_ID = "urn:axiom:routing-evals:schema:v8"
BENCHMARK_V8_ID = "codex-core-v8"
CLAUDE_CODE_BENCHMARK_V8_ID = "claude-code-core-v8"
CURRENT_BENCHMARK_IDS = (BENCHMARK_V8_ID, CLAUDE_CODE_BENCHMARK_V8_ID)
CURRENT_BENCHMARK_CASE_COUNT = 49
CURRENT_CORPUS_RELATIVE_PATH = "evals/routing-v8/current.jsonl"
CURRENT_BENCHMARK_PROFILES = {
    "codex": {**V7_CODEX_PROFILE, "id": BENCHMARK_V8_ID},
    "claude-code": {**V5_BENCHMARK_PROFILES["claude-code"], "id": CLAUDE_CODE_BENCHMARK_V8_ID},
}
# Schema versions that bind a benchmark profile per host, with their profiles.
HOST_BENCHMARK_PROFILES_BY_VERSION = {
    "5": V5_BENCHMARK_PROFILES, "6": V6_BENCHMARK_PROFILES, "7": V7_BENCHMARK_PROFILES,
    "8": CURRENT_BENCHMARK_PROFILES,
}
