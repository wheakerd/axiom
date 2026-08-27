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
    "confirm-external-action.jsonl",
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
