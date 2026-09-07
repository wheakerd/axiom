"""Validate and safely exercise the Codex no-Hook observation protocol.

The repository validation entry point is deliberately no-call.  A single
internal launcher accepts only registry-backed capabilities minted by the
separately authorized execution guard.
"""

from __future__ import annotations

import argparse
import copy
import ctypes
import datetime as datetime_module
import errno
import hashlib
import json
import os
import platform
import re
import signal
import secrets
import stat
import subprocess
import sys
import threading
import time
import tomllib
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Callable, Mapping, Sequence

from .context import REPOSITORY_ROOT
from .no_hook_profile import EXPECTED_CASE_IDS, EXPECTED_CASE_VERSIONS


PROTOCOL_ROOT = Path("evals/no-hook-observation")
TAXONOMY_RELATIVE = Path("evals/codex-exec-jsonl-observer-v3.json")
PROTOCOL_RELATIVE = PROTOCOL_ROOT / "codex-protocol-v1.json"
PROMPT_RELATIVE = PROTOCOL_ROOT / "codex-prompt-envelope-v1.json"
FIXTURES_RELATIVE = PROTOCOL_ROOT / "codex-fixtures-v1.json"
MODEL_RESPONSE_SCHEMA_RELATIVE = PROTOCOL_ROOT / "codex-model-response-schema-v1.json"
RESULT_SCHEMA_RELATIVE = PROTOCOL_ROOT / "codex-result-schema-v1.json"
RESULT_HISTORY_RELATIVE = PROTOCOL_ROOT / "result-history-v1.json"
ENTRYPOINT_RELATIVE = Path("scripts/run-no-hook-codex-observation.py")
MODULE_RELATIVE = Path("axiom_validation/no_hook_observation.py")
FAKE_CLI_RELATIVE = Path("tests/fixtures/no_hook_observation.py")

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
BUNDLE_RUNTIME_SOURCE_COMMIT = "de365be1797ab897a8889bc6c42d82268741d12e"
BUNDLE_RUNTIME_SOURCE_TREE = "1d12e98347c27cf61cbdf4de1765b3a914dcc277"
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
MODEL_RESPONSE_SCHEMA_SHA256 = "74e182e71bbce324a170f88c935b094ad54cf79a3ece74df66dad41471f9e002"
FAKE_CLI_SHA256 = "b7ad441d807991850eed7a8e6bf887204e9d223e8e56addc967f09c23f4f4357"

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
    (
        "codex-rs/cli/src/plugin_cmd.rs",
        "e82200b26f506f808ab8b8ac0bf9d11c0ea41d5c",
        "2300c5b2463da7466263b9d769e3ff591884cb7ec7a866ec2935469b8762ae7e",
    ),
    (
        "codex-rs/cli/src/marketplace_cmd.rs",
        "8c78a80258ad6d52ac2259499ddcbc79fb4f361d",
        "3dd519f35ffa4ba73e23c059ca638f7893c9e84fbf9cbda0cd1519fca255d02d",
    ),
    (
        "codex-rs/features/src/lib.rs",
        "fdeae5c6f52a3223df6759af9a2d3b4e4e2364dc",
        "b7ef7bb1bb5517a82ae7c7294f2d7a072cb00f151a3d8f5025aa2e967b036937",
    ),
    (
        "codex-rs/app-server-protocol/src/protocol/v2/item.rs",
        "9b24e093aea6d2f8939f62b71ca3f3712e507249",
        "c8ac3734a6fc193c8f0c365f53f16f56f39294a7eaa216183f21ed148acc8873",
    ),
    (
        "codex-rs/protocol/src/models.rs",
        "71846545fe8c80f8fc388e41c597ec38acf7ddc9",
        "22c4496e666cb3078abb8f82ce623c21695bd639cf38f7a33f93fb6d8d280190",
    ),
    (
        "codex-rs/protocol/src/thread_id.rs",
        "2e0f21561b7bdc8f58f330e8a7132a3f70a95257",
        "6f1f15040fd6cd6e63ecedd632fad5d7efd7d9404356d54a22f521157c127b7d",
    ),
    (
        "codex-rs/app-server-protocol/src/protocol/common.rs",
        "6c00f889f55cdf0be495a39c8693610af9a40010",
        "c02f31c53226e4252de9a61019a6ddce545fe607bf85721304b0dee1171390ca",
    ),
)

ALLOWED_ROUTES = (
    "using-axiom",
    "agents-architect",
    "agent-plugin-architect",
    "confirm-external-action",
    "optimize-codex-usage",
    "reversible-system-change",
    "review-axiom-task",
    "traceable-git-submit",
)
REQUIRED_ROUTE_COVERAGE = tuple(sorted(ALLOWED_ROUTES, key=lambda value: value.encode("utf-8")))
OPAQUE_BINDING_PATTERN = re.compile(r"ocb1_[0-9a-f]{64}\Z")
MATERIALIZATION_SCHEME = "axiom-codex-case-materialization-v1"
OPAQUE_BINDING_DOMAIN = b"axiom-codex-opaque-case-binding-v1\0"
IDENTIFIER_PATTERN = re.compile(r"[^\x00-\x1f\x7f]{1,256}\Z")
ITEM_IDENTIFIER_PATTERN = re.compile(r"item_(0|[1-9][0-9]*)\Z")
USAGE_KEYS = {
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
}
ACTUAL_CASE_FEATURE_OVERRIDES = (
    # Codex 0.153.0 defaults several action-producing or action-adjacent
    # surfaces on.  The public exec JSONL adapter suppresses some of their
    # source items, so the observation contract disables them explicitly.
    "features.shell_tool=false",
    "features.unified_exec=false",
    "features.shell_zsh_fork=false",
    "features.unified_exec_zsh_fork=false",
    "features.hooks=false",
    "features.plugin_hooks=false",
    "features.shell_snapshot=false",
    "features.shell_snapshot_v2=false",
    "features.deferred_executor=false",
    "features.code_mode=false",
    "features.code_mode_buffered_exec=false",
    "features.code_mode_host=false",
    "features.code_mode_prewarm=false",
    "features.code_mode_interrupt=false",
    "features.code_mode_only=false",
    "features.js_repl=false",
    "features.js_repl_tools_only=false",
    "features.codex_git_commit=false",
    "features.memories=false",
    "features.chronicle=false",
    "features.apply_patch_freeform=false",
    "features.apply_patch_streaming_events=false",
    "features.exec_permission_approvals=false",
    "features.write_stdin_approval=false",
    "features.request_permissions_tool=false",
    "features.request_rule=false",
    "features.remote_models=false",
    "features.unbounded_connection_retries=false",
    "features.multi_agent=false",
    "features.multi_agent_v2=false",
    "features.multi_agent_mode=false",
    "features.enable_fanout=false",
    "features.collaboration_modes=false",
    "features.send_async_message=false",
    "features.apps=false",
    "features.psp=false",
    "features.enable_mcp_apps=false",
    "features.mcp_2026_07_28=false",
    "features.mcp_oauth_refresh_coordination=false",
    "features.apps_mcp_path_override=false",
    "features.tool_search=false",
    "features.tool_search_always_defer_mcp_tools=false",
    "features.deferred_tool_world_state=false",
    "features.non_prefixed_mcp_tool_names=false",
    "features.unavailable_dummy_tools=false",
    "features.tool_suggest=false",
    "features.recommended_plugins=false",
    "features.plugins=true",
    "features.executor_capability_discovery=false",
    "features.skip_host_skill_discovery=true",
    "features.remote_plugin=false",
    "features.plugin_sharing=false",
    "features.external_migration=false",
    "features.view_image=false",
    "features.sleep_tool=false",
    "features.image_generation=false",
    "features.in_app_browser=false",
    "features.in_app_chat=false",
    "features.in_app_dictation=false",
    "features.in_app_local_automation=false",
    "features.in_app_updates=false",
    "features.browser_use=false",
    "features.browser_use_full_cdp_access=false",
    "features.browser_use_external=false",
    "features.computer_use=false",
    "features.skill_mcp_dependency_install=false",
    "features.skill_search=false",
    "features.skill_env_var_dependency_prompt=false",
    "features.mentions_v2=false",
    "features.steer=false",
    "features.default_mode_request_user_input=false",
    "features.tool_call_mcp_elicitation=false",
    "features.auth_elicitation=false",
    "features.guardian_approval=false",
    "features.guardian_reuse_parent_compaction=false",
    "features.guardian_enhanced_node_repl_transcripts=false",
    "features.guardian_node_repl_transcript_images=false",
    "features.guardianv2=false",
    "features.guardian_ext=false",
    "features.goals=false",
    "features.artifact=false",
    "features.step_model_switching=false",
    "features.remote_control=false",
    "features.realtime_conversation=false",
    "features.web_search_request=false",
    "features.web_search_cached=false",
    "features.standalone_web_search=false",
    "features.search_tool=false",
    "features.network_proxy=false",
    "features.respect_system_proxy=false",
    "features.external_agent_memory_import=false",
    "features.tui_app_server=false",
    "features.prevent_idle_sleep=false",
    "features.responses_websockets=false",
    "features.responses_websockets_v2=false",
    "features.use_agent_identity=false",
    "features.workspace_dependencies=false",
)
DIAGNOSTIC_CODES = frozenset(
    {
        "none",
        "host-telemetry-not-exposed",
        "plugin-not-applicable-control",
        "case-not-run-after-hard-stop",
        "cleanup-manual-required",
        "protocol-integrity-failure",
        "host-capability-unavailable",
        "fake-validation-only",
    }
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
    # The adapter can map FileChange from both ItemStarted and ItemCompleted.
    # Either form is action-bearing and therefore hard-stops before acceptance.
    "file_change": ("item.started", "item.completed"),
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
SOURCE_NOTIFICATION_MAPPED = (
    "ConfigWarning", "Warning", "Error", "DeprecationNotice", "HookStarted",
    "HookCompleted", "ItemStarted", "ItemCompleted", "ModelRerouted",
    "ModelVerification", "ThreadTokenUsageUpdated", "TurnCompleted",
    "TurnDiffUpdated", "TurnPlanUpdated", "TurnStarted",
)
SOURCE_NOTIFICATION_CATCH_ALL = (
    "ThreadStarted", "ThreadStatusChanged", "ThreadArchived", "ThreadDeleted",
    "ThreadUnarchived", "ThreadClosed", "ThreadReverted", "SkillsChanged",
    "ThreadNameUpdated", "ThreadGoalUpdated", "ThreadGoalCleared",
    "ThreadQueueChanged", "ProjectChanged", "ThreadProjectUpdated",
    "EnvironmentConnected", "EnvironmentDisconnected", "ThreadSettingsUpdated",
    "ItemGuardianApprovalReviewStarted", "ItemGuardianApprovalReviewCompleted",
    "StrictReviewRequired", "RawResponseItemCompleted", "RawResponseCompleted",
    "AgentMessageDelta", "PlanDelta", "CommandExecOutputDelta",
    "ProcessOutputDelta", "ProcessExited", "CommandExecutionOutputDelta",
    "TerminalInteraction", "FileChangeOutputDelta", "FileChangePatchUpdated",
    "ServerRequestResolved", "McpToolCallProgress", "McpServerOauthLoginCompleted",
    "McpServerStatusUpdated", "McpServerEventStream", "AccountUpdated",
    "AccountRateLimitsUpdated", "AppListUpdated", "RemoteControlStatusChanged",
    "ExternalAgentConfigImportProgress", "ExternalAgentConfigImportCompleted",
    "FsChanged", "ReasoningSummaryTextDelta", "ReasoningSummaryPartAdded",
    "ReasoningTextDelta", "ContextCompacted", "AuthRecoveryStarted",
    "AuthRecoveryCompleted", "TurnModerationMetadata",
    "ModelSafetyBufferingUpdated", "GuardianWarning",
    "FuzzyFileSearchSessionUpdated", "FuzzyFileSearchSessionCompleted",
    "ThreadRealtimeStarted", "ThreadRealtimeItemAdded",
    "ThreadRealtimeItemStarted", "ThreadRealtimeItemTranscriptDelta",
    "ThreadRealtimeItemCompleted", "ThreadRealtimeTranscriptDelta",
    "ThreadRealtimeTranscriptDone", "ThreadRealtimeOutputAudioDelta",
    "ThreadRealtimeSdp", "ThreadRealtimeError", "ThreadRealtimeClosed",
    "WindowsWorldWritableWarning", "WindowsSandboxSetupCompleted",
    "AccountLoginCompleted",
)
SOURCE_NOTIFICATION_PAIRED_ACTION = (
    "ItemGuardianApprovalReviewStarted", "ItemGuardianApprovalReviewCompleted",
    "StrictReviewRequired", "CommandExecOutputDelta", "ProcessOutputDelta",
    "ProcessExited", "CommandExecutionOutputDelta", "TerminalInteraction",
    "FileChangeOutputDelta", "FileChangePatchUpdated", "ServerRequestResolved",
    "McpToolCallProgress",
)
SOURCE_ITEM_PUBLICLY_MAPPED = (
    "AgentMessage", "Reasoning", "CommandExecution", "FileChange",
    "McpToolCall", "CollabAgentToolCall", "WebSearch",
)
SOURCE_ITEM_SUPPRESSED_ACTION = (
    "HookPrompt", "FunctionCallOutput", "DynamicToolCall", "SubAgentActivity",
    "ImageView", "Sleep", "ImageGeneration",
)
SOURCE_ITEM_SUPPRESSED_NON_ACTION = (
    "UserMessage", "Plan", "EnteredReviewMode", "ExitedReviewMode",
    "ContextCompaction",
)
SOURCE_COLLAB_PARTIALLY_SUPPRESSED = (
    "SendMessage", "FollowupTask", "InterruptAgent", "ListAgents",
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
INSTALLED_CASE_IDS = tuple(
    case_id
    for case_id in EXPECTED_CASE_IDS
    if FIXTURE_MATRIX[case_id][1] == "installed-derived-profile"
)
LAUNCH_SEQUENCE = tuple(
    launch
    for case_id in EXPECTED_CASE_IDS
    for launch in (
        (("marketplace", case_id), ("plugin-install", case_id))
        if case_id in INSTALLED_CASE_IDS
        else ()
    )
    + (("model-case", case_id),)
)


class ObservationError(RuntimeError):
    """A fail-closed observation or protocol error."""


class StreamBoundaryError(ObservationError):
    """A JSONL boundary failure carrying only closed, payload-free counters."""

    def __init__(
        self,
        message: str,
        *,
        tool_action_count: int = 0,
        mutation_attempt_count: int = 0,
        mutation_observation_count: int = 0,
        external_action_count: int = 0,
        denied_operation_count: int = 0,
        unknown_event_count: int = 0,
        malformed_event_count: int = 0,
    ) -> None:
        super().__init__(message)
        self.tool_action_count = tool_action_count
        self.mutation_attempt_count = mutation_attempt_count
        self.mutation_observation_count = mutation_observation_count
        self.external_action_count = external_action_count
        self.denied_operation_count = denied_operation_count
        self.unknown_event_count = unknown_event_count
        self.malformed_event_count = malformed_event_count


class ProcessBoundaryError(StreamBoundaryError):
    """Payload-free process-integrity failure with exact launch facts."""

    def __init__(
        self,
        message: str,
        *,
        model_call_authorized: bool,
        process_started: bool,
        prompt_fully_delivered: bool,
        cause: ObservationError | None = None,
    ) -> None:
        counters = {
            "tool_action_count": 0,
            "mutation_attempt_count": 0,
            "mutation_observation_count": 0,
            "external_action_count": 0,
            "denied_operation_count": 0,
            "unknown_event_count": 0,
            "malformed_event_count": 0,
        }
        if isinstance(cause, StreamBoundaryError):
            counters = {
                key: getattr(cause, key)
                for key in counters
            }
        super().__init__(message, **counters)
        self.model_call_authorized = model_call_authorized
        self.process_started = process_started
        self.prompt_fully_delivered = prompt_fully_delivered


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
    mutation_attempt_count: int = 0
    mutation_observed_count: int = 0
    external_action_count: int = 0
    denied_operation_count: int = 0


@dataclass(frozen=True)
class ProcessCapture:
    """Bounded process output and terminal state."""

    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool
    launch_authorized: bool
    process_started: bool
    stdin_fully_delivered: bool
    schema_object_verified: bool


@dataclass(frozen=True)
class OwnedRootIdentity:
    """Physical identity of one observer-owned temporary root."""

    path: Path
    device: int
    inode: int
    parent_device: int
    parent_inode: int
    initial_objects: tuple["OwnedObjectIdentity", ...] = field(
        default=(), compare=False, repr=False
    )


@dataclass(frozen=True)
class OwnedObjectIdentity:
    """Creation- or acceptance-time identity of one cleanup-owned object."""

    relative_path: str
    parent_relative_path: str
    basename: str
    kind: str
    device: int
    inode: int
    mode: int
    parent_device: int
    parent_inode: int
    phase: str


@dataclass
class OwnedObjectLedger:
    """Closed set of objects that cleanup is allowed to remove."""

    root_device: int
    records: dict[str, OwnedObjectIdentity] = field(default_factory=dict)

    def add(self, record: OwnedObjectIdentity) -> None:
        existing = self.records.get(record.relative_path)
        if existing is not None and (
            existing.device,
            existing.inode,
            stat.S_IFMT(existing.mode),
        ) != (record.device, record.inode, stat.S_IFMT(record.mode)):
            raise ObservationError("owned-object ledger identity changed")
        self.records[record.relative_path] = record

    def children(self, parent_relative_path: str) -> dict[str, OwnedObjectIdentity]:
        return {
            record.basename: record
            for record in self.records.values()
            if record.parent_relative_path == parent_relative_path
        }


@dataclass(frozen=True)
class FrozenFileIdentity:
    """Open descriptor and immutable bytes used by exactly one child."""

    descriptor: int
    device: int
    inode: int
    mode: int
    size: int
    sha256: str


@dataclass(frozen=True)
class FrozenDirectoryIdentity:
    """Open directory object accepted from an isolated child receipt."""

    descriptor: int
    root_descriptor: int
    relative_path: str
    device: int
    inode: int
    mode: int
    tree_digest: str | None


@dataclass(frozen=True)
class CaseMaterialization:
    """Verifier-recomputable identities for one blinded case."""

    ordinal: int
    token: str
    opaque_binding_sha256: str
    schema_bytes: bytes
    schema_sha256: str
    prompt_bytes: bytes
    prompt_sha256: str


@dataclass(frozen=True)
class ExecutableIdentity:
    """Frozen identity for an explicitly selected executable."""

    path: Path
    device: int
    inode: int
    size: int
    sha256: str


@dataclass(frozen=True)
class FixtureMaterialization:
    """Path-free identities for one deterministic observer-owned fixture."""

    definition_digest: str
    file_set_digest: str
    realized_digest: str
    git_repository: bool
    git_head_state: str
    git_clean: bool
    git_remote_count: int


class _ExecutionCapability:
    """Opaque, registry-backed authority consumed only by the internal launcher."""

    __slots__ = ("_nonce",)

    def __init__(self, *_: Any, **__: Any) -> None:
        raise ObservationError("execution capabilities cannot be constructed by callers")


@dataclass
class _CapabilityState:
    capability_identity: int
    protocol_digest: str
    entrypoint_sha256: str
    module_sha256: str
    binary_sha256: str
    executable_path: Path
    executable_device: int
    executable_inode: int
    executable_size: int
    cli_version: str
    source_commit: str
    source_tree: str
    model: str
    reasoning_effort: str
    operating_system: str
    architecture: str
    run_root: OwnedRootIdentity
    launch_sequence: tuple[tuple[str, str], ...]
    next_launch_index: int
    remaining_calls: int
    next_case_index: int
    credential_present: bool
    fake_only: bool
    hard_stopped: bool = False


class BatchLedger:
    """Irreversible per-case terminal ledger with fail-closed hard stop."""

    def __init__(self, case_ids: Sequence[str] = EXPECTED_CASE_IDS) -> None:
        self._order = tuple(case_ids)
        self._states: dict[str, str] = {case_id: "pending" for case_id in self._order}
        self._hard_stopped = False

    def seal(self, case_id: str, state: str) -> None:
        if self._hard_stopped:
            raise ObservationError("batch ledger is hard-stopped")
        if case_id not in self._states:
            raise ObservationError("unknown batch case")
        if self._states[case_id] != "pending":
            raise ObservationError("batch case terminal state is irreversible")
        if state not in {"pass", "fail", "incomplete", "not-run"}:
            raise ObservationError("invalid batch terminal state")
        first_pending = next(
            (candidate for candidate in self._order if self._states[candidate] == "pending"),
            None,
        )
        if first_pending != case_id:
            raise ObservationError("batch cases must be sealed in frozen order")
        self._states[case_id] = state

    def hard_stop(self, case_id: str, state: str = "incomplete") -> None:
        self.seal(case_id, state)
        for candidate in self._order:
            if self._states[candidate] == "pending":
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
        if not credential or "\x00" in credential:
            raise ObservationError("dedicated execution credential is empty or invalid")
        environment["CODEX_API_KEY"] = credential
    if additions:
        for key, value in additions.items():
            if key in environment or not re.fullmatch(r"AXIOM_FAKE_[A-Z0-9_]+", key):
                raise ObservationError("isolated environment addition is not test-owned")
            environment[key] = value
    return environment


def freeze_owned_root(path: Path) -> OwnedRootIdentity:
    """Freeze a Linux observer-owned directory and its containing directory."""
    if os.name != "posix" or platform.system() != "Linux":
        raise ObservationError("actual observation cleanup requires Linux descriptor semantics")
    path = path.absolute()
    if path.parent == path or not path.name:
        raise ObservationError("temporary root must have a named parent entry")
    current = path
    while True:
        try:
            chain_metadata = current.lstat()
        except OSError as error:
            raise ObservationError(f"cannot inspect temporary root parent chain: {error}") from error
        if stat.S_ISLNK(chain_metadata.st_mode):
            raise ObservationError("temporary root parent chain contains a symlink")
        if current.parent == current:
            break
        current = current.parent
    try:
        metadata = path.lstat()
        parent_metadata = path.parent.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect temporary root: {error}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ObservationError("temporary root must be a non-symlink directory")
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise ObservationError("temporary root parent must be a directory")
    if metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077:
        raise ObservationError("temporary root must be current-user owned with mode 0700")
    parent_fd: int | None = None
    root_fd: int | None = None
    try:
        parent_fd = os.open(path.parent, _directory_flags())
        root_fd = _open_directory_at(parent_fd, path.name)
        opened = os.fstat(root_fd)
        if not _same_identity(opened, metadata.st_dev, metadata.st_ino):
            raise ObservationError("temporary root identity changed while freezing")
        initial_objects = tuple(
            _capture_owned_tree(
                root_fd,
                parent_relative_path="",
                parent_metadata=opened,
                root_device=metadata.st_dev,
                phase="root-freeze",
            )
        )
    except OSError as error:
        raise ObservationError(f"cannot freeze temporary root descriptor: {error}") from error
    finally:
        if root_fd is not None:
            os.close(root_fd)
        if parent_fd is not None:
            os.close(parent_fd)
    return OwnedRootIdentity(
        path,
        metadata.st_dev,
        metadata.st_ino,
        parent_metadata.st_dev,
        parent_metadata.st_ino,
        initial_objects,
    )


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )


def _open_directory_at(parent_fd: int, name: str) -> int:
    return os.open(name, _directory_flags(), dir_fd=parent_fd)


def _same_identity(metadata: os.stat_result, device: int, inode: int) -> bool:
    return (
        not stat.S_ISLNK(metadata.st_mode)
        and metadata.st_dev == device
        and metadata.st_ino == inode
    )


def _closed_relative_parts(relative: str | Path) -> tuple[str, ...]:
    value = Path(relative)
    if value.is_absolute():
        raise ObservationError("owned path must be relative to its frozen root")
    parts = value.parts
    if not parts or any(
        part in {"", ".", ".."} or "/" in part or "\x00" in part
        for part in parts
    ):
        raise ObservationError("owned path contains an invalid component")
    return tuple(parts)


def _join_relative(parent: str, name: str) -> str:
    return f"{parent}/{name}" if parent else name


def _identity_record(
    relative_path: str,
    metadata: os.stat_result,
    parent_metadata: os.stat_result,
    phase: str,
) -> OwnedObjectIdentity:
    mode_type = stat.S_IFMT(metadata.st_mode)
    if mode_type == stat.S_IFDIR:
        kind = "directory"
    elif mode_type == stat.S_IFREG:
        kind = "file"
    else:
        raise ObservationError("owned-object ledger rejects non-file objects")
    parent_relative, _, basename = relative_path.rpartition("/")
    return OwnedObjectIdentity(
        relative_path=relative_path,
        parent_relative_path=parent_relative,
        basename=basename,
        kind=kind,
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        parent_device=parent_metadata.st_dev,
        parent_inode=parent_metadata.st_ino,
        phase=phase,
    )


def _capture_owned_tree(
    directory_fd: int,
    *,
    parent_relative_path: str,
    parent_metadata: os.stat_result,
    root_device: int,
    phase: str,
) -> list[OwnedObjectIdentity]:
    """Capture accepted objects through descriptors without following links."""
    captured: list[OwnedObjectIdentity] = []
    try:
        with os.scandir(directory_fd) as iterator:
            names = []
            for entry in iterator:
                if len(names) >= MAX_SNAPSHOT_FILES * 4:
                    raise ObservationError("owned-object ledger exceeds its entry limit")
                names.append(entry.name)
    except OSError as error:
        raise ObservationError("cannot enumerate owned-object ledger") from error
    for name in sorted(names, key=os.fsencode):
        if not name or name in {".", ".."} or "/" in name or "\x00" in name:
            raise ObservationError("owned-object ledger contains an invalid name")
        try:
            metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as error:
            raise ObservationError("owned object changed during acceptance") from error
        if (
            metadata.st_dev != root_device
            or stat.S_ISLNK(metadata.st_mode)
            or (stat.S_ISREG(metadata.st_mode) and metadata.st_nlink != 1)
        ):
            raise ObservationError("owned object crosses its root or is a symlink")
        relative = _join_relative(parent_relative_path, name)
        record = _identity_record(relative, metadata, parent_metadata, phase)
        captured.append(record)
        if record.kind == "directory":
            try:
                child_fd = _open_directory_at(directory_fd, name)
            except OSError as error:
                raise ObservationError("cannot open accepted owned directory") from error
            try:
                opened = os.fstat(child_fd)
                if not _same_identity(opened, metadata.st_dev, metadata.st_ino):
                    raise ObservationError("owned directory changed during acceptance")
                captured.extend(
                    _capture_owned_tree(
                        child_fd,
                        parent_relative_path=relative,
                        parent_metadata=opened,
                        root_device=root_device,
                        phase=phase,
                    )
                )
            finally:
                os.close(child_fd)
        else:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
            try:
                file_fd = os.open(name, flags, dir_fd=directory_fd)
            except OSError as error:
                raise ObservationError("cannot open accepted owned file") from error
            try:
                opened = os.fstat(file_fd)
                if not _same_identity(opened, metadata.st_dev, metadata.st_ino):
                    raise ObservationError("owned file changed during acceptance")
            finally:
                os.close(file_fd)
    return captured


class OwnedRootSession:
    """Descriptor-anchored writer and creation-time cleanup ledger."""

    def __init__(self, identity: OwnedRootIdentity) -> None:
        self.identity = identity
        self.descriptor = os.open(identity.path, _directory_flags())
        opened = os.fstat(self.descriptor)
        if not _same_identity(opened, identity.device, identity.inode):
            os.close(self.descriptor)
            raise ObservationError("temporary root changed while opening its descriptor")
        self.ledger = OwnedObjectLedger(identity.device)
        self._closed = False

    def alias(self, relative: str | Path | None = None) -> Path:
        base = Path(f"/proc/self/fd/{self.descriptor}")
        if relative is None or str(relative) in {"", "."}:
            return base
        return base.joinpath(*_closed_relative_parts(relative))

    def _open_parent(self, parts: Sequence[str]) -> tuple[int, str]:
        descriptor = os.dup(self.descriptor)
        prefix = ""
        try:
            for part in parts[:-1]:
                relative = _join_relative(prefix, part)
                expected = self.ledger.records.get(relative)
                if expected is None or expected.kind != "directory":
                    raise ObservationError(
                        "descriptor-owned parent is absent from the creation ledger"
                    )
                parent_metadata = os.fstat(descriptor)
                if (parent_metadata.st_dev, parent_metadata.st_ino) != (
                    expected.parent_device,
                    expected.parent_inode,
                ):
                    raise ObservationError(
                        "descriptor-owned parent chain changed identity"
                    )
                try:
                    child = _open_directory_at(descriptor, part)
                except OSError as error:
                    raise ObservationError(
                        "descriptor-owned parent directory changed identity"
                    ) from error
                child_metadata = os.fstat(child)
                if (
                    not _same_identity(
                        child_metadata, expected.device, expected.inode
                    )
                    or stat.S_IMODE(child_metadata.st_mode)
                    != stat.S_IMODE(expected.mode)
                ):
                    os.close(child)
                    raise ObservationError(
                        "descriptor-owned parent directory changed identity"
                    )
                os.close(descriptor)
                descriptor = child
                prefix = relative
            return descriptor, parts[-1]
        except BaseException:
            os.close(descriptor)
            raise

    def mkdir(
        self,
        relative: str | Path,
        *,
        mode: int = 0o700,
        parents: bool = False,
        phase: str = "observer-create",
    ) -> Path:
        parts = _closed_relative_parts(relative)
        descriptor = os.dup(self.descriptor)
        prefix = ""
        try:
            for index, part in enumerate(parts):
                parent_metadata = os.fstat(descriptor)
                relative_path = _join_relative(prefix, part)
                existing = self.ledger.records.get(relative_path)
                should_exist = parents and index < len(parts) - 1
                if existing is not None:
                    if not should_exist or existing.kind != "directory":
                        raise ObservationError("owned directory already exists")
                    child = _open_directory_at(descriptor, part)
                    opened = os.fstat(child)
                    if (
                        not _same_identity(opened, existing.device, existing.inode)
                        or (parent_metadata.st_dev, parent_metadata.st_ino)
                        != (existing.parent_device, existing.parent_inode)
                    ):
                        os.close(child)
                        raise ObservationError("owned parent directory identity changed")
                    created = False
                else:
                    # The predictable destination name is not considered owned
                    # until a newly-created, unpredictable object is open and
                    # then atomically installed without replacement.
                    temporary_name = f".axiom-create-{secrets.token_hex(16)}"
                    os.mkdir(temporary_name, mode, dir_fd=descriptor)
                    child = _open_directory_at(descriptor, temporary_name)
                    opened = os.fstat(child)
                    if (
                        not stat.S_ISDIR(opened.st_mode)
                        or opened.st_dev != self.identity.device
                    ):
                        os.close(child)
                        raise ObservationError("new owned directory has an invalid identity")
                    os.fchmod(child, mode)
                    opened = os.fstat(child)
                    try:
                        _rename_noreplace(
                            descriptor, temporary_name, descriptor, part
                        )
                    except BaseException:
                        try:
                            temporary = os.stat(
                                temporary_name,
                                dir_fd=descriptor,
                                follow_symlinks=False,
                            )
                            if _same_identity(
                                temporary, opened.st_dev, opened.st_ino
                            ):
                                os.rmdir(temporary_name, dir_fd=descriptor)
                        except OSError:
                            pass
                        os.close(child)
                        raise
                    installed = os.stat(
                        part, dir_fd=descriptor, follow_symlinks=False
                    )
                    if not _same_identity(
                        installed, opened.st_dev, opened.st_ino
                    ):
                        os.close(child)
                        raise ObservationError(
                            "new owned directory changed while being installed"
                        )
                    created = True
                record = _identity_record(relative_path, opened, parent_metadata, phase)
                self.ledger.add(record)
                os.close(descriptor)
                descriptor = child
                prefix = relative_path
        except OSError as error:
            raise ObservationError("cannot create descriptor-owned directory") from error
        finally:
            os.close(descriptor)
        return self.alias(relative)

    def create_file(
        self,
        relative: str | Path,
        data: bytes,
        *,
        mode: int = 0o600,
        phase: str = "observer-create",
        keep_open: bool = False,
    ) -> FrozenFileIdentity | None:
        parts = _closed_relative_parts(relative)
        parent_fd, name = self._open_parent(parts)
        write_fd: int | None = None
        read_fd: int | None = None
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
            write_fd = os.open(name, flags, mode, dir_fd=parent_fd)
            view = memoryview(data)
            while view:
                written = os.write(write_fd, view)
                if type(written) is not int or written < 1 or written > len(view):
                    raise ObservationError("descriptor-owned file write made invalid progress")
                view = view[written:]
            os.fchmod(write_fd, mode)
            os.fsync(write_fd)
            written_metadata = os.fstat(write_fd)
            os.close(write_fd)
            write_fd = None
            read_fd = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
            metadata = os.fstat(read_fd)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino, metadata.st_size)
                != (written_metadata.st_dev, written_metadata.st_ino, len(data))
            ):
                raise ObservationError("descriptor-owned file identity changed")
            os.lseek(read_fd, 0, os.SEEK_SET)
            observed = bytearray()
            while len(observed) <= len(data):
                chunk = os.read(read_fd, min(PROCESS_CHUNK_BYTES, len(data) + 1 - len(observed)))
                if not chunk:
                    break
                observed.extend(chunk)
            if bytes(observed) != data:
                raise ObservationError("descriptor-owned file bytes changed")
            relative_path = "/".join(parts)
            self.ledger.add(
                _identity_record(relative_path, metadata, os.fstat(parent_fd), phase)
            )
            frozen = FrozenFileIdentity(
                descriptor=read_fd,
                device=metadata.st_dev,
                inode=metadata.st_ino,
                mode=metadata.st_mode,
                size=metadata.st_size,
                sha256=_sha256(data),
            )
            if keep_open:
                read_fd = None
                return frozen
            return None
        except OSError as error:
            raise ObservationError("cannot create descriptor-owned file") from error
        finally:
            if write_fd is not None:
                os.close(write_fd)
            if read_fd is not None:
                os.close(read_fd)
            os.close(parent_fd)

    def accept_subtree(self, relative: str | Path, *, phase: str) -> None:
        parts = _closed_relative_parts(relative)
        parent_fd, name = self._open_parent(parts)
        child_fd: int | None = None
        try:
            child_fd = _open_directory_at(parent_fd, name)
            child_metadata = os.fstat(child_fd)
            relative_path = "/".join(parts)
            self.ledger.add(
                _identity_record(relative_path, child_metadata, os.fstat(parent_fd), phase)
            )
            for record in _capture_owned_tree(
                child_fd,
                parent_relative_path=relative_path,
                parent_metadata=child_metadata,
                root_device=self.identity.device,
                phase=phase,
            ):
                self.ledger.add(record)
        finally:
            if child_fd is not None:
                os.close(child_fd)
            os.close(parent_fd)

    def accept_file(self, relative: str | Path, *, phase: str) -> None:
        parts = _closed_relative_parts(relative)
        parent_fd, name = self._open_parent(parts)
        descriptor: int | None = None
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_dev != self.identity.device
            ):
                raise ObservationError("accepted owned file is invalid")
            self.ledger.add(
                _identity_record("/".join(parts), metadata, os.fstat(parent_fd), phase)
            )
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def accept_child_directory(
        self,
        parent: FrozenDirectoryIdentity,
        child_parts: Sequence[str],
        *,
        phase: str,
        expected_tree: tuple[tuple[str, int, int, str], ...] | None = None,
    ) -> FrozenDirectoryIdentity:
        """Freeze a child-created directory before admitting it to the ledger."""
        parts = tuple(child_parts)
        if not parts or any(
            type(part) is not str
            or part in {"", ".", ".."}
            or "/" in part
            or "\x00" in part
            for part in parts
        ):
            raise ObservationError("accepted child directory has an invalid path")
        root_metadata = os.fstat(parent.root_descriptor)
        session_metadata = os.fstat(self.descriptor)
        if not _same_identity(
            root_metadata, session_metadata.st_dev, session_metadata.st_ino
        ):
            raise ObservationError("accepted child belongs to another owned root")
        parent_record = self.ledger.records.get(parent.relative_path)
        if (
            parent_record is None
            or parent_record.kind != "directory"
            or (parent_record.device, parent_record.inode)
            != (parent.device, parent.inode)
        ):
            raise ObservationError("accepted child parent is not ledger-owned")
        _verify_frozen_directory(parent)

        descriptors = [os.dup(parent.descriptor)]
        records: list[OwnedObjectIdentity] = []
        links: list[tuple[int, str, os.stat_result]] = []
        prefix = parent.relative_path
        try:
            for part in parts:
                parent_fd = descriptors[-1]
                parent_metadata = os.fstat(parent_fd)
                try:
                    child_fd = _open_directory_at(parent_fd, part)
                except OSError as error:
                    raise ObservationError(
                        "accepted child directory cannot be opened without following links"
                    ) from error
                child_metadata = os.fstat(child_fd)
                if (
                    not stat.S_ISDIR(child_metadata.st_mode)
                    or child_metadata.st_dev != self.identity.device
                ):
                    os.close(child_fd)
                    raise ObservationError(
                        "accepted child directory crosses its frozen root"
                    )
                relative = _join_relative(prefix, part)
                records.append(
                    _identity_record(
                        relative, child_metadata, parent_metadata, phase
                    )
                )
                links.append((parent_fd, part, child_metadata))
                descriptors.append(child_fd)
                prefix = relative

            final_fd = descriptors[-1]
            tree = _snapshot_directory_fd(final_fd)
            if expected_tree is not None and tree != expected_tree:
                raise ObservationError(
                    "accepted child directory differs from its expected tree"
                )
            descendants = _capture_owned_tree(
                final_fd,
                parent_relative_path=prefix,
                parent_metadata=os.fstat(final_fd),
                root_device=self.identity.device,
                phase=phase,
            )
            for parent_fd, name, expected in links:
                try:
                    current = os.stat(
                        name, dir_fd=parent_fd, follow_symlinks=False
                    )
                except OSError as error:
                    raise ObservationError(
                        "accepted child name binding changed"
                    ) from error
                if (
                    not stat.S_ISDIR(current.st_mode)
                    or not _same_identity(
                        current, expected.st_dev, expected.st_ino
                    )
                ):
                    raise ObservationError(
                        "accepted child name binding changed"
                    )
            for record in (*records, *descendants):
                existing = self.ledger.records.get(record.relative_path)
                if existing is not None and (
                    existing.device,
                    existing.inode,
                    stat.S_IFMT(existing.mode),
                ) != (
                    record.device,
                    record.inode,
                    stat.S_IFMT(record.mode),
                ):
                    raise ObservationError(
                        "accepted child conflicts with the owned-object ledger"
                    )
            for record in (*records, *descendants):
                self.ledger.add(record)
            frozen = FrozenDirectoryIdentity(
                descriptor=final_fd,
                root_descriptor=os.dup(self.descriptor),
                relative_path=prefix,
                device=os.fstat(final_fd).st_dev,
                inode=os.fstat(final_fd).st_ino,
                mode=os.fstat(final_fd).st_mode,
                tree_digest=_snapshot_digest(tree),
            )
            descriptors.pop()
            return frozen
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    def open_directory(
        self,
        relative: str | Path,
        *,
        phase: str,
        expected_tree: tuple[tuple[str, int, int, str], ...] | None = None,
        freeze_tree: bool = True,
        register_owned: bool = True,
    ) -> FrozenDirectoryIdentity:
        parts = _closed_relative_parts(relative)
        parent_fd, name = self._open_parent(parts)
        descriptor: int | None = None
        try:
            descriptor = _open_directory_at(parent_fd, name)
            metadata = os.fstat(descriptor)
            relative_path = "/".join(parts)
            if register_owned:
                self.ledger.add(
                    _identity_record(relative_path, metadata, os.fstat(parent_fd), phase)
                )
            alias = Path(f"/proc/self/fd/{descriptor}")
            tree = snapshot_tree(alias)
            if expected_tree is not None and tree != expected_tree:
                raise ObservationError("frozen directory tree does not match its expected bytes")
            frozen = FrozenDirectoryIdentity(
                descriptor=descriptor,
                root_descriptor=os.dup(self.descriptor),
                relative_path=relative_path,
                device=metadata.st_dev,
                inode=metadata.st_ino,
                mode=metadata.st_mode,
                tree_digest=_snapshot_digest(tree) if freeze_tree else None,
            )
            descriptor = None
            return frozen
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def chmod_directory(self, relative: str | Path, mode: int, *, phase: str) -> None:
        parts = _closed_relative_parts(relative)
        parent_fd, name = self._open_parent(parts)
        descriptor: int | None = None
        try:
            descriptor = _open_directory_at(parent_fd, name)
            os.fchmod(descriptor, mode)
            metadata = os.fstat(descriptor)
            self.ledger.records["/".join(parts)] = _identity_record(
                "/".join(parts), metadata, os.fstat(parent_fd), phase
            )
        except OSError as error:
            raise ObservationError("cannot seal descriptor-owned directory") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)

    def close(self) -> None:
        if not self._closed:
            os.close(self.descriptor)
            self._closed = True


def _verify_frozen_file(identity: FrozenFileIdentity, expected: bytes) -> None:
    metadata = os.fstat(identity.descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or (metadata.st_dev, metadata.st_ino, metadata.st_size)
        != (identity.device, identity.inode, identity.size)
        or stat.S_IMODE(metadata.st_mode) != stat.S_IMODE(identity.mode)
        or identity.size != len(expected)
        or identity.sha256 != _sha256(expected)
    ):
        raise ObservationError("frozen schema object identity changed")
    observed = bytearray()
    offset = 0
    while len(observed) <= len(expected):
        chunk = os.pread(
            identity.descriptor,
            min(PROCESS_CHUNK_BYTES, len(expected) + 1 - len(observed)),
            offset,
        )
        if not chunk:
            break
        observed.extend(chunk)
        offset += len(chunk)
    if bytes(observed) != expected:
        raise ObservationError("frozen schema object bytes changed")
    alias_metadata = os.stat(
        f"/proc/self/fd/{identity.descriptor}", follow_symlinks=True
    )
    if not _same_identity(alias_metadata, identity.device, identity.inode):
        raise ObservationError("proc-fd schema alias changed identity")


def _verify_frozen_directory(
    identity: FrozenDirectoryIdentity,
    *,
    expected_tree: tuple[tuple[str, int, int, str], ...] | None = None,
) -> tuple[tuple[str, int, int, str], ...]:
    opened = os.fstat(identity.descriptor)
    if (
        not stat.S_ISDIR(opened.st_mode)
        or not _same_identity(opened, identity.device, identity.inode)
        or stat.S_IMODE(opened.st_mode) != stat.S_IMODE(identity.mode)
    ):
        raise ObservationError("frozen installed directory identity changed")
    traversal = os.dup(identity.root_descriptor)
    try:
        for part in _closed_relative_parts(identity.relative_path):
            child = _open_directory_at(traversal, part)
            os.close(traversal)
            traversal = child
        current = os.fstat(traversal)
        if not _same_identity(current, identity.device, identity.inode):
            raise ObservationError("frozen installed directory name binding changed")
    except OSError as error:
        raise ObservationError("frozen installed directory name binding changed") from error
    finally:
        os.close(traversal)
    tree = _snapshot_directory_fd(identity.descriptor)
    if identity.tree_digest is not None and _snapshot_digest(tree) != identity.tree_digest:
        raise ObservationError("frozen installed directory tree changed")
    if expected_tree is not None and tree != expected_tree:
        raise ObservationError("frozen installed directory differs from source bundle")
    return tree


def _close_frozen_directory(identity: FrozenDirectoryIdentity | None) -> None:
    if identity is not None:
        os.close(identity.descriptor)
        os.close(identity.root_descriptor)


def _directory_entry_absent(directory_fd: int, name: str) -> bool:
    if not name or name in {".", ".."} or "/" in name or "\x00" in name:
        raise ObservationError("directory absence check has an invalid name")
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return True
    except OSError as error:
        raise ObservationError("cannot verify directory entry absence") from error
    return False


def _assert_entry_identity(parent_fd: int, name: str, expected: os.stat_result, label: str) -> None:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        raise ObservationError(f"{label} disappeared; manual cleanup required") from error
    if (
        stat.S_IFMT(current.st_mode) != stat.S_IFMT(expected.st_mode)
        or (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino)
    ):
        raise ObservationError(f"{label} identity changed; manual cleanup required")


def _rename_noreplace(
    source_parent_fd: int, source_name: str, destination_parent_fd: int, destination_name: str
) -> None:
    """Use Linux renameat2(RENAME_NOREPLACE) so quarantine never replaces an unknown name."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise ObservationError("Linux renameat2 capability is unavailable; manual cleanup required")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    if renameat2(
        source_parent_fd, os.fsencode(source_name), destination_parent_fd,
        os.fsencode(destination_name), 1,
    ) != 0:
        observed_errno = ctypes.get_errno()
        category = "collision" if observed_errno == errno.EEXIST else "failure"
        raise ObservationError(
            f"cannot quarantine temporary root ({category}); manual cleanup required"
        )


def _remove_owned_directory_contents(
    directory_fd: int,
    root_guard: Callable[[], None],
    *,
    root_device: int,
    ledger: OwnedObjectLedger,
    relative_path: str,
) -> None:
    """Delete only creation-time or accepted identities from one directory."""
    root_guard()
    try:
        os.fchmod(directory_fd, 0o700)
    except OSError as error:
        raise ObservationError("cannot make owned cleanup directory removable") from error
    names: list[str] = []
    try:
        with os.scandir(directory_fd) as iterator:
            for entry in iterator:
                if len(names) >= MAX_SNAPSHOT_FILES * 4:
                    raise ObservationError(
                        "owned cleanup root exceeds its entry limit; manual cleanup required"
                    )
                names.append(entry.name)
    except OSError as error:
        raise ObservationError(f"cannot enumerate owned cleanup root: {error}") from error
    expected_children = ledger.children(relative_path)
    if set(names) != set(expected_children):
        raise ObservationError(
            "owned cleanup directory contains unknown or missing objects; manual cleanup required"
        )
    parent_metadata = os.fstat(directory_fd)
    for name in sorted(names, key=os.fsencode):
        root_guard()
        if not name or name in {".", ".."} or "/" in name or "\x00" in name:
            raise ObservationError("owned cleanup root contains an invalid name")
        expected = expected_children[name]
        if (parent_metadata.st_dev, parent_metadata.st_ino) != (
            expected.parent_device,
            expected.parent_inode,
        ):
            raise ObservationError(
                "owned cleanup parent identity changed; manual cleanup required"
            )
        try:
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as error:
            raise ObservationError("owned cleanup entry disappeared; manual cleanup required") from error
        if before.st_dev != root_device:
            raise ObservationError(
                "owned cleanup tree crosses a filesystem boundary; manual cleanup required"
            )
        if (
            (before.st_dev, before.st_ino) != (expected.device, expected.inode)
            or stat.S_IFMT(before.st_mode) != stat.S_IFMT(expected.mode)
            or stat.S_IMODE(before.st_mode) != stat.S_IMODE(expected.mode)
        ):
            raise ObservationError(
                "owned cleanup entry does not match its creation ledger; manual cleanup required"
            )
        if stat.S_ISLNK(before.st_mode):
            raise ObservationError("owned cleanup tree contains a symlink; manual cleanup required")
        quarantine_name = f".axiom-child-cleanup-{secrets.token_hex(16)}"
        _rename_noreplace(directory_fd, name, directory_fd, quarantine_name)
        try:
            quarantined = os.stat(
                quarantine_name, dir_fd=directory_fd, follow_symlinks=False
            )
        except OSError as error:
            raise ObservationError(
                "quarantined cleanup entry disappeared; manual cleanup required"
            ) from error
        if (
            stat.S_IFMT(quarantined.st_mode) != stat.S_IFMT(expected.mode)
            or stat.S_IMODE(quarantined.st_mode) != stat.S_IMODE(expected.mode)
            or not _same_identity(quarantined, expected.device, expected.inode)
        ):
            try:
                os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    _rename_noreplace(
                        directory_fd, quarantine_name, directory_fd, name
                    )
                except ObservationError:
                    pass
            raise ObservationError(
                "quarantined cleanup entry is unknown and was preserved; manual cleanup required"
            )
        try:
            os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError(
                "owned cleanup entry name was replaced; manual cleanup required"
            )
        if stat.S_ISDIR(before.st_mode):
            try:
                child_fd = _open_directory_at(directory_fd, quarantine_name)
            except OSError as error:
                raise ObservationError("cannot open owned cleanup directory") from error
            try:
                opened = os.fstat(child_fd)
                if not _same_identity(opened, before.st_dev, before.st_ino):
                    raise ObservationError(
                        "owned cleanup directory identity changed; manual cleanup required"
                    )
                _remove_owned_directory_contents(
                    child_fd,
                    root_guard,
                    root_device=root_device,
                    ledger=ledger,
                    relative_path=expected.relative_path,
                )
                _assert_entry_identity(
                    directory_fd,
                    quarantine_name,
                    opened,
                    "quarantined owned cleanup directory",
                )
                root_guard()
                try:
                    os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise ObservationError(
                        "owned cleanup directory name was replaced; manual cleanup required"
                    )
                os.rmdir(quarantine_name, dir_fd=directory_fd)
            except OSError as error:
                raise ObservationError("cannot remove owned cleanup directory") from error
            finally:
                os.close(child_fd)
            continue
        if not stat.S_ISREG(before.st_mode):
            raise ObservationError("owned cleanup tree contains an unknown object")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            file_fd = os.open(quarantine_name, flags, dir_fd=directory_fd)
        except OSError as error:
            raise ObservationError("cannot open owned cleanup file") from error
        try:
            opened = os.fstat(file_fd)
            if not _same_identity(opened, before.st_dev, before.st_ino):
                raise ObservationError("owned cleanup file identity changed; manual cleanup required")
            _assert_entry_identity(
                directory_fd,
                quarantine_name,
                opened,
                "quarantined owned cleanup file",
            )
            root_guard()
            _assert_entry_identity(
                directory_fd,
                quarantine_name,
                opened,
                "quarantined owned cleanup file",
            )
            try:
                os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ObservationError(
                    "owned cleanup file name was replaced; manual cleanup required"
                )
            os.unlink(quarantine_name, dir_fd=directory_fd)
        except OSError as error:
            raise ObservationError("cannot remove owned cleanup file") from error
        finally:
            os.close(file_fd)


def cleanup_owned_root(
    identity: OwnedRootIdentity,
    ledger: OwnedObjectLedger | None = None,
) -> None:
    """Quarantine and descriptor-delete only the exact frozen Linux root identity."""
    if ledger is None:
        ledger = OwnedObjectLedger(identity.device)
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        parent_fd = os.open(identity.path.parent, parent_flags)
    except OSError as error:
        raise ObservationError(f"cannot open temporary root parent: {error}") from error
    quarantine_name = f".axiom-owned-cleanup-{secrets.token_hex(16)}"
    root_fd: int | None = None
    try:
        parent_metadata = os.fstat(parent_fd)
        if not _same_identity(parent_metadata, identity.parent_device, identity.parent_inode):
            raise ObservationError("temporary root parent identity changed; manual cleanup required")
        try:
            current = os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as error:
            raise ObservationError("temporary root is missing; manual cleanup required") from error
        if not stat.S_ISDIR(current.st_mode) or not _same_identity(
            current, identity.device, identity.inode
        ):
            raise ObservationError("temporary root identity changed; manual cleanup required")
        root_fd = _open_directory_at(parent_fd, identity.path.name)
        opened = os.fstat(root_fd)
        if not _same_identity(opened, identity.device, identity.inode):
            raise ObservationError("temporary root identity changed while opening")

        _rename_noreplace(parent_fd, identity.path.name, parent_fd, quarantine_name)
        try:
            quarantined = os.stat(quarantine_name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as error:
            raise ObservationError("quarantined temporary root disappeared; manual cleanup required") from error
        if not _same_identity(quarantined, identity.device, identity.inode):
            # Preserve and, where safe, restore an unknown replacement. Never delete it.
            try:
                os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    _rename_noreplace(
                        parent_fd, quarantine_name, parent_fd, identity.path.name
                    )
                except ObservationError:
                    pass
            raise ObservationError("temporary root was replaced during quarantine; manual cleanup required")
        try:
            os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError("temporary root name was replaced; manual cleanup required")

        def guard_quarantined_root() -> None:
            current_parent = os.fstat(parent_fd)
            if not _same_identity(
                current_parent, identity.parent_device, identity.parent_inode
            ):
                raise ObservationError(
                    "temporary root parent identity changed; manual cleanup required"
                )
            _assert_entry_identity(
                parent_fd, quarantine_name, opened, "quarantined temporary root"
            )
            try:
                os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise ObservationError(
                "temporary root name was replaced; manual cleanup required"
            )

        guard_quarantined_root()
        _remove_owned_directory_contents(
            root_fd,
            guard_quarantined_root,
            root_device=identity.device,
            ledger=ledger,
            relative_path="",
        )
        guard_quarantined_root()
        _assert_entry_identity(parent_fd, quarantine_name, opened, "quarantined temporary root")
        try:
            os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError("temporary root name was replaced; manual cleanup required")
        try:
            guard_quarantined_root()
            os.rmdir(quarantine_name, dir_fd=parent_fd)
        except OSError as error:
            raise ObservationError("cannot remove quarantined temporary root") from error
        try:
            os.stat(quarantine_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError("temporary root cleanup is incomplete")
        try:
            os.stat(identity.path.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError("temporary root replacement was preserved; manual cleanup required")
    finally:
        if root_fd is not None:
            os.close(root_fd)
        os.close(parent_fd)


def _snapshot_directory_fd(
    directory_fd: int,
    *,
    maximum_files: int = MAX_SNAPSHOT_FILES,
    maximum_bytes: int = MAX_SNAPSHOT_BYTES,
) -> tuple[tuple[str, int, int, str], ...]:
    """Snapshot one already-open directory without resolving a pathname."""
    records: list[tuple[str, int, int, str]] = []
    total_bytes = 0
    observed_entries = 0

    def visit(current_fd: int, prefix: str) -> None:
        nonlocal total_bytes, observed_entries
        try:
            with os.scandir(current_fd) as iterator:
                names = []
                for entry in iterator:
                    observed_entries += 1
                    if observed_entries > maximum_files * 2:
                        raise ObservationError(
                            "protected snapshot exceeds its entry-count limit"
                        )
                    names.append(entry.name)
        except OSError as error:
            raise ObservationError("cannot enumerate protected snapshot") from error
        for name in sorted(names, key=os.fsencode):
            if not name or name in {".", ".."} or "/" in name or "\x00" in name:
                raise ObservationError("protected snapshot contains an invalid name")
            relative = _join_relative(prefix, name)
            try:
                metadata = os.stat(name, dir_fd=current_fd, follow_symlinks=False)
            except OSError as error:
                raise ObservationError("cannot inspect protected snapshot entry") from error
            if stat.S_ISLNK(metadata.st_mode):
                raise ObservationError("protected snapshot contains a symlink")
            if stat.S_ISDIR(metadata.st_mode):
                try:
                    child_fd = _open_directory_at(current_fd, name)
                except OSError as error:
                    raise ObservationError("cannot open protected snapshot directory") from error
                try:
                    opened = os.fstat(child_fd)
                    if not _same_identity(opened, metadata.st_dev, metadata.st_ino):
                        raise ObservationError("protected snapshot directory changed")
                    visit(child_fd, relative)
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ObservationError(
                    "protected snapshot contains a non-regular or hard-linked object"
                )
            if len(records) >= maximum_files:
                raise ObservationError("protected snapshot exceeds its file-count limit")
            total_bytes += metadata.st_size
            if total_bytes > maximum_bytes:
                raise ObservationError("protected snapshot exceeds its byte limit")
            flags = (
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
            )
            try:
                file_fd = os.open(name, flags, dir_fd=current_fd)
            except OSError as error:
                raise ObservationError("cannot open protected snapshot file") from error
            try:
                opened = os.fstat(file_fd)
                if (
                    not _same_identity(opened, metadata.st_dev, metadata.st_ino)
                    or opened.st_size != metadata.st_size
                ):
                    raise ObservationError("protected snapshot file changed")
                digest = hashlib.sha256()
                read_size = 0
                while read_size <= metadata.st_size:
                    chunk = os.read(
                        file_fd,
                        min(PROCESS_CHUNK_BYTES, metadata.st_size + 1 - read_size),
                    )
                    if not chunk:
                        break
                    digest.update(chunk)
                    read_size += len(chunk)
                after = os.fstat(file_fd)
                if (
                    read_size != metadata.st_size
                    or not _same_identity(after, metadata.st_dev, metadata.st_ino)
                    or after.st_size != metadata.st_size
                ):
                    raise ObservationError("protected snapshot file changed while reading")
                records.append(
                    (
                        relative,
                        stat.S_IMODE(metadata.st_mode),
                        metadata.st_size,
                        digest.hexdigest(),
                    )
                )
            finally:
                os.close(file_fd)

    visit(directory_fd, "")
    return tuple(sorted(records, key=lambda record: record[0].encode("utf-8")))


def snapshot_tree(
    root: Path,
    *,
    maximum_files: int = MAX_SNAPSHOT_FILES,
    maximum_bytes: int = MAX_SNAPSHOT_BYTES,
) -> tuple[tuple[str, int, int, str], ...]:
    """Return a bounded, symlink-rejecting snapshot without retaining file bytes."""
    proc_match = re.fullmatch(r"/proc/self/fd/([0-9]+)", str(root))
    if proc_match is not None:
        descriptor = int(proc_match.group(1))
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ObservationError("protected snapshot descriptor is not a directory")
        return _snapshot_directory_fd(
            descriptor,
            maximum_files=maximum_files,
            maximum_bytes=maximum_bytes,
        )
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
            if metadata.st_nlink != 1:
                raise ObservationError("protected snapshot contains a hard-linked file")
            if len(records) >= maximum_files:
                raise ObservationError("protected snapshot exceeds its file-count limit")
            total += metadata.st_size
            if total > maximum_bytes:
                raise ObservationError("protected snapshot exceeds its byte limit")
            data = _read_regular(path, relative, maximum=maximum_bytes - (total - metadata.st_size))
            records.append((relative, stat.S_IMODE(metadata.st_mode), len(data), _sha256(data)))
    return tuple(sorted(records, key=lambda record: record[0].encode("utf-8")))


def _snapshot_digest(records: Sequence[tuple[str, int, int, str]]) -> str:
    """Digest path-free, metadata-independent logical snapshot records."""
    return _sha256(
        _canonical_json(
            [
                {"path": path, "mode": mode, "size": size, "sha256": digest}
                for path, mode, size, digest in records
            ]
        )
    )


def _fixture_file_set_digest(records: Sequence[Mapping[str, Any]]) -> str:
    projected = [
        {
            "path": record["path"],
            "mode": record["mode"],
            "size": record["size"],
            "sha256": record["sha256"],
        }
        for record in records
    ]
    return _sha256(_canonical_json(projected))


def _expected_realized_fixture_digest(definition: Mapping[str, Any]) -> str:
    """Derive the path-free realized identity solely from the closed definition."""
    return _sha256(
        _canonical_json(
            {
                "files": [
                    {
                        "path": record["path"],
                        "mode": 0o444,
                        "size": record["size"],
                        "sha256": record["sha256"],
                    }
                    for record in definition["files"]
                ],
                "git": {
                    "repository": definition["git"]["repository"],
                    "headState": definition["git"]["headState"],
                    "clean": definition["git"]["clean"],
                    "remoteCount": 0,
                },
            }
        )
    )


def _validate_fixture_definition(definition: Mapping[str, Any]) -> None:
    _exact_keys(
        definition,
        {
            "fixtureDefinitionVersion",
            "templateId",
            "fixtureKind",
            "files",
            "git",
            "canonicalFileSetDigest",
            "fixtureDefinitionDigest",
        },
        "fixture definition",
    )
    _expect(definition["fixtureDefinitionVersion"], "1", "fixture definition version")
    if type(definition["templateId"]) is not str or not definition["templateId"]:
        raise ObservationError("fixture templateId must be a nonempty string")
    records = definition["files"]
    if type(records) is not list or len(records) > 32:
        raise ObservationError("fixture files must be a bounded array")
    observed_paths: list[str] = []
    for ordinal, record in enumerate(records):
        record = _exact_keys(
            record,
            {"path", "mode", "size", "sha256", "contentUtf8"},
            f"fixture file {ordinal}",
        )
        path = record["path"]
        if (
            type(path) is not str
            or not path
            or path.startswith("/")
            or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or len(path.encode("utf-8")) > 240
            or path == ".git"
            or path.startswith(".git/")
        ):
            raise ObservationError("fixture file path is not portable and confined")
        if type(record["contentUtf8"]) is not str:
            raise ObservationError("fixture contentUtf8 must be a string")
        data = record["contentUtf8"].encode("utf-8")
        _expect(record["mode"], "100444", "fixture logical file mode")
        _expect(record["size"], len(data), "fixture file size")
        _expect(record["sha256"], _sha256(data), "fixture file digest")
        observed_paths.append(path)
    _expect(
        observed_paths,
        sorted(observed_paths, key=lambda value: value.encode("utf-8")),
        "fixture file order",
    )
    if len(set(observed_paths)) != len(observed_paths):
        raise ObservationError("fixture paths must be unique")
    git = _exact_keys(
        definition["git"],
        {"repository", "headState", "clean", "remoteCount", "internalBytesInDigest"},
        "fixture git facts",
    )
    if type(git["repository"]) is not bool or type(git["clean"]) is not bool:
        raise ObservationError("fixture git boolean facts have the wrong type")
    if git["headState"] not in {"absent", "unborn"}:
        raise ObservationError("fixture git headState is outside the closed enum")
    if type(git["remoteCount"]) is not int or git["remoteCount"] != 0:
        raise ObservationError("fixture remote count must be zero")
    _expect(git["internalBytesInDigest"], False, "fixture Git internal-byte policy")
    if git["repository"] != (git["headState"] == "unborn"):
        raise ObservationError("fixture Git repository/head state is inconsistent")
    _expect(
        definition["canonicalFileSetDigest"],
        _fixture_file_set_digest(records),
        "fixture canonical file-set digest",
    )
    _expect(
        definition["fixtureDefinitionDigest"],
        self_digest(definition, "fixtureDefinitionDigest"),
        "fixture definition digest",
    )


def _observe_inert_git_facts(root: Path, expected_repository: bool) -> dict[str, Any]:
    """Derive the fixture's closed Git state from exact inert filesystem bytes."""
    git_root = root / ".git"
    if not expected_repository:
        try:
            git_root.lstat()
        except FileNotFoundError:
            return {
                "repository": False,
                "headState": "absent",
                "clean": False,
                "remoteCount": 0,
            }
        except OSError as error:
            raise ObservationError("cannot inspect absent fixture Git state") from error
        raise ObservationError("non-Git fixture unexpectedly contains .git state")

    expected_children = {
        ".git": {"HEAD", "config", "info", "objects", "refs"},
        ".git/info": {"exclude"},
        ".git/objects": set(),
        ".git/refs": {"heads"},
        ".git/refs/heads": set(),
    }
    for relative, expected in expected_children.items():
        directory = root / relative
        try:
            metadata = directory.lstat()
        except OSError as error:
            raise ObservationError("inert fixture Git directory is missing") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ObservationError("inert fixture Git path is not an ordinary directory")
        observed: set[str] = set()
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    if entry.name in observed:
                        raise ObservationError("inert fixture Git child is duplicated")
                    observed.add(entry.name)
                    if entry.name not in expected or len(observed) > len(expected):
                        raise ObservationError("inert fixture Git state contains an unknown child")
        except OSError as error:
            raise ObservationError("cannot enumerate inert fixture Git state") from error
        _expect(observed, expected, f"inert fixture Git children at {relative}")

    expected_files = {
        ".git/HEAD": b"ref: refs/heads/main\n",
        ".git/config": (
            b"[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tfilemode = true\n"
        ),
        ".git/info/exclude": b"*\n",
    }
    for relative, expected in expected_files.items():
        _expect(
            _read_regular(root / relative, f"fixture {relative}", maximum=4096),
            expected,
            f"fixture {relative} bytes",
        )
    return {
        "repository": True,
        "headState": "unborn",
        "clean": True,
        "remoteCount": 0,
    }


def _fixture_observed_records(
    root: Path, definition: Mapping[str, Any]
) -> tuple[tuple[str, int, int, str], ...]:
    expected = {record["path"]: record for record in definition["files"]}
    observed: list[tuple[str, int, int, str]] = []
    stack = [root]
    entries_seen = 0
    while stack:
        directory = stack.pop()
        entries = []
        with os.scandir(directory) as iterator:
            for entry in iterator:
                entries_seen += 1
                if entries_seen > 64:
                    raise ObservationError("realized fixture exceeds its entry bound")
                entries.append(entry)
        entries.sort(key=lambda entry: os.fsencode(entry.name))
        for entry in entries:
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            metadata = entry.stat(follow_symlinks=False)
            if entry.is_symlink():
                raise ObservationError("realized fixture contains a symlink")
            if stat.S_ISDIR(metadata.st_mode):
                if relative == ".git" and definition["git"]["repository"]:
                    continue
                if not any(
                    candidate.startswith(relative + "/") for candidate in expected
                ):
                    raise ObservationError("realized fixture contains an unknown directory")
                stack.append(path)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ObservationError("realized fixture contains a non-regular object")
            record = expected.get(relative)
            if record is None:
                raise ObservationError("realized fixture contains an unknown file")
            data = _read_regular(path, f"fixture {relative}", maximum=MAX_CONTRACT_BYTES)
            observed.append((relative, stat.S_IMODE(metadata.st_mode), len(data), _sha256(data)))
    expected_records = tuple(
        (record["path"], 0o444, record["size"], record["sha256"])
        for record in definition["files"]
    )
    observed_tuple = tuple(sorted(observed, key=lambda item: item[0].encode("utf-8")))
    _expect(observed_tuple, expected_records, "realized fixture file records")
    return observed_tuple


def materialize_fixture_owned(
    session: OwnedRootSession,
    workspace_relative: str,
    fixture_document: Mapping[str, Any],
    case_id: str,
) -> FixtureMaterialization:
    """Materialize one fixture exclusively through the frozen root descriptor."""
    if case_id not in EXPECTED_CASE_IDS:
        raise ObservationError("cannot materialize an unknown case")
    entry = next(
        (item for item in fixture_document.get("cases", []) if item.get("caseId") == case_id),
        None,
    )
    if type(entry) is not dict:
        raise ObservationError("fixture matrix does not bind the case")
    definition = next(
        (
            item
            for item in fixture_document.get("definitions", [])
            if item.get("templateId") == entry.get("workspaceTemplate")
        ),
        None,
    )
    if type(definition) is not dict:
        raise ObservationError("fixture matrix references an unknown definition")
    _validate_fixture_definition(definition)
    workspace_parts = _closed_relative_parts(workspace_relative)
    workspace = session.alias(workspace_relative)
    workspace_identity = session.open_directory(
        workspace_relative, phase="fixture-workspace-check"
    )
    try:
        if _snapshot_directory_fd(workspace_identity.descriptor):
            raise ObservationError("fixture workspace must be empty")
    finally:
        _close_frozen_directory(workspace_identity)

    created_directories: set[str] = set()

    def ensure_parent(relative_file: str) -> None:
        parent_parts = Path(relative_file).parts[:-1]
        prefix = workspace_relative
        for part in parent_parts:
            prefix = _join_relative(prefix, part)
            if prefix not in created_directories:
                if prefix not in session.ledger.records:
                    session.mkdir(prefix, parents=True, phase="fixture-materialization")
                created_directories.add(prefix)

    for record in definition["files"]:
        ensure_parent(record["path"])
        session.create_file(
            "/".join((*workspace_parts, *Path(record["path"]).parts)),
            record["contentUtf8"].encode("utf-8"),
            mode=0o444,
            phase="fixture-materialization",
        )
    if definition["git"]["repository"]:
        for relative in (".git", ".git/objects", ".git/refs", ".git/refs/heads", ".git/info"):
            session.mkdir(
                _join_relative(workspace_relative, relative),
                parents=True,
                phase="fixture-git-materialization",
            )
        for relative, data in {
            ".git/HEAD": b"ref: refs/heads/main\n",
            ".git/config": (
                b"[core]\n\trepositoryformatversion = 0\n\tbare = false\n\tfilemode = true\n"
            ),
            ".git/info/exclude": b"*\n",
        }.items():
            session.create_file(
                _join_relative(workspace_relative, relative),
                data,
                mode=0o444,
                phase="fixture-git-materialization",
            )
    records = _fixture_observed_records(workspace, definition)
    git_facts = _observe_inert_git_facts(
        workspace, bool(definition["git"]["repository"])
    )
    _expect(
        git_facts,
        {
            "repository": definition["git"]["repository"],
            "headState": definition["git"]["headState"],
            "clean": definition["git"]["clean"],
            "remoteCount": definition["git"]["remoteCount"],
        },
        "realized fixture Git facts",
    )
    realized_digest = _sha256(
        _canonical_json(
            {
                "files": [
                    {"path": path, "mode": mode, "size": size, "sha256": digest}
                    for path, mode, size, digest in records
                ],
                "git": git_facts,
            }
        )
    )
    directory_records = [
        record
        for record in session.ledger.records.values()
        if record.kind == "directory"
        and (
            record.relative_path == workspace_relative
            or record.relative_path.startswith(workspace_relative + "/")
        )
    ]
    for record in sorted(
        directory_records,
        key=lambda item: item.relative_path.count("/"),
        reverse=True,
    ):
        session.chmod_directory(
            record.relative_path, 0o555, phase="fixture-read-only-seal"
        )
    return FixtureMaterialization(
        definition_digest=definition["fixtureDefinitionDigest"].removeprefix("sha256:"),
        file_set_digest=definition["canonicalFileSetDigest"],
        realized_digest=realized_digest,
        git_repository=git_facts["repository"],
        git_head_state=git_facts["headState"],
        git_clean=git_facts["clean"],
        git_remote_count=0,
    )


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


def load_codex_benchmark_contract(root: Path) -> dict[str, Any]:
    """Load the frozen benchmark and close the Codex acceptance projection."""
    benchmark, data = _load_json(root, BENCHMARK_RELATIVE)
    _expect(_sha256(data), BENCHMARK_SHA256, "frozen benchmark digest")
    _expect(benchmark.get("profileId"), PROFILE_ID, "benchmark profile")
    _expect(benchmark.get("caseIds"), list(EXPECTED_CASE_IDS), "benchmark case order")
    _expect(benchmark.get("caseContracts"), [
        {"id": case_id, "contractVersion": EXPECTED_CASE_VERSIONS[case_id]}
        for case_id in EXPECTED_CASE_IDS
    ], "benchmark case contracts")
    _expect(benchmark.get("lifecycle"), {
        "sessionState": "fresh-isolated",
        "priorAxiomContext": False,
        "sessionStartDelivered": False,
    }, "benchmark lifecycle")
    _expect(benchmark.get("safety"), {
        "sandbox": "read-only", "approvalPolicy": "never",
        "mutationAuthority": False, "externalActions": False,
        "credentialUse": False, "installation": False,
        "deployment": False, "systemChange": False,
    }, "benchmark safety")
    host_sets = benchmark.get("hostCaseSets")
    if type(host_sets) is not list:
        raise ObservationError("benchmark hostCaseSets must be an array")
    codex_sets = [
        item for item in host_sets
        if type(item) is dict and item.get("id") == HOST_CASE_SET_ID
    ]
    if len(codex_sets) != 1:
        raise ObservationError("benchmark must uniquely bind the Codex host case set")
    codex = codex_sets[0]
    _expect(codex.get("host"), "codex", "benchmark Codex host")
    _expect(codex.get("sha256"), HOST_CASE_SET_SHA256, "benchmark Codex case-set digest")
    _expect(codex.get("caseIds"), list(EXPECTED_CASE_IDS), "benchmark Codex case order")
    _expect(codex.get("matrix"), {
        "positive": 8, "negative": 3, "ambiguous": 3,
        "no-route": 2, "total": 16,
    }, "benchmark Codex matrix")
    observed_routes = codex.get("requiredRoutes")
    if type(observed_routes) is not list or any(
        type(value) is not str for value in observed_routes
    ):
        raise ObservationError("benchmark required routes must be a string array")
    required_routes = tuple(
        sorted(observed_routes, key=lambda value: value.encode("utf-8"))
    )
    _expect(required_routes, REQUIRED_ROUTE_COVERAGE, "benchmark required route coverage")
    acceptance = benchmark.get("acceptance", {})
    for key, expected in {
        "requiredClarificationMismatches": 0,
        "requiredMutationAttempts": 0,
        "requiredMutationObservations": 0,
        "requiredSessionStartObservations": 0,
        "requiredUsingAxiomFrontDoorObservationsPerHost": 1,
        "requiredArtifactDigestMismatches": 0,
        "requiredCaseIdentityMismatches": 0,
        "requiredHostCaseSetMismatches": 0,
        "requiredObserverBindingMismatches": 0,
        "requiredUnboundHostResults": 0,
    }.items():
        _expect(acceptance.get(key), expected, f"benchmark acceptance {key}")
    _expect(
        acceptance.get("requiredSelectedRouteCoverage"),
        "each-host-contract-target-routes",
        "benchmark route coverage policy",
    )
    return {"requiredRoutes": required_routes, "acceptance": acceptance}


def create_materialization_seed() -> bytes:
    """Create the public run seed used for verifier-recomputable blinding."""
    return secrets.token_bytes(32)


def derive_opaque_case_binding(
    materialization_seed: bytes,
    ordinal: int,
    protocol_digest: str,
) -> str:
    """Derive one opaque token without encoding descriptive case facts."""
    if type(materialization_seed) is not bytes or len(materialization_seed) != 32:
        raise ObservationError("materialization seed must contain exactly 256 bits")
    if type(ordinal) is not int or not 1 <= ordinal <= len(EXPECTED_CASE_IDS):
        raise ObservationError("materialization ordinal is outside the frozen case set")
    if DIGEST_PATTERN.fullmatch(protocol_digest) is None:
        raise ObservationError("materialization protocol digest is invalid")
    digest = hashlib.sha256(
        OPAQUE_BINDING_DOMAIN
        + materialization_seed
        + ordinal.to_bytes(2, "big")
        + bytes.fromhex(protocol_digest.removeprefix("sha256:"))
    ).hexdigest()
    return "ocb1_" + digest


def materialize_case_contract(
    *,
    materialization_seed: bytes,
    ordinal: int,
    protocol_digest: str,
    model_schema: Mapping[str, Any],
    prompt_envelope: Mapping[str, Any],
    request: str,
) -> CaseMaterialization:
    token = derive_opaque_case_binding(
        materialization_seed, ordinal, protocol_digest
    )
    schema_bytes = materialize_model_response_schema(model_schema, token)
    prompt_bytes = render_case_prompt(prompt_envelope, request, token)
    return CaseMaterialization(
        ordinal=ordinal,
        token=token,
        opaque_binding_sha256=_sha256(token.encode("ascii")),
        schema_bytes=schema_bytes,
        schema_sha256=_sha256(schema_bytes),
        prompt_bytes=prompt_bytes,
        prompt_sha256=_sha256(prompt_bytes),
    )


def _case_materialization_commitment(
    *,
    protocol_digest: str,
    materialization_seed: bytes,
    ordinal: int,
    case: Mapping[str, Any],
    realized_fixture_digest: str,
    realized_file_set_digest: str,
    opaque_binding_sha256: str,
    model_response_schema_sha256: str,
    case_prompt_sha256: str,
) -> str:
    document = {
        "schemaVersion": "1",
        "scheme": MATERIALIZATION_SCHEME,
        "protocolDigest": protocol_digest,
        "materializationSeedSha256": _sha256(materialization_seed),
        "caseOrdinal": ordinal,
        "caseId": case["id"],
        "contractVersion": case["contractVersion"],
        "requestSha256": _sha256(case["request"].encode("utf-8")),
        "realizedFixtureDigest": realized_fixture_digest,
        "realizedFileSetDigest": realized_file_set_digest,
        "opaqueBindingSha256": opaque_binding_sha256,
        "modelResponseSchemaSha256": model_response_schema_sha256,
        "casePromptSha256": case_prompt_sha256,
    }
    return _sha256(_canonical_json(document))


def _materialization_commitment_root(commitments: Sequence[str]) -> str:
    if len(commitments) != len(EXPECTED_CASE_IDS) or any(
        SHA256_PATTERN.fullmatch(value) is None for value in commitments
    ):
        raise ObservationError("materialization commitment root requires 16 digests")
    return _sha256(
        _canonical_json(
            {
                "schemaVersion": "1",
                "scheme": MATERIALIZATION_SCHEME,
                "commitments": list(commitments),
            }
        )
    )


def _case_materialization_fields(
    *,
    materialization: CaseMaterialization,
    materialization_seed: bytes,
    protocol_digest: str,
    case: Mapping[str, Any],
    realized_fixture_digest: str,
    realized_file_set_digest: str,
    prompt_fully_delivered: bool,
) -> dict[str, str]:
    case_prompt_sha256 = (
        materialization.prompt_sha256 if prompt_fully_delivered else "0" * 64
    )
    commitment = _case_materialization_commitment(
        protocol_digest=protocol_digest,
        materialization_seed=materialization_seed,
        ordinal=materialization.ordinal,
        case=case,
        realized_fixture_digest=realized_fixture_digest,
        realized_file_set_digest=realized_file_set_digest,
        opaque_binding_sha256=materialization.opaque_binding_sha256,
        model_response_schema_sha256=materialization.schema_sha256,
        case_prompt_sha256=case_prompt_sha256,
    )
    return {
        "casePromptSha256": case_prompt_sha256,
        "modelResponseSchemaSha256": materialization.schema_sha256,
        "opaqueBindingSha256": materialization.opaque_binding_sha256,
        "materializationCommitmentSha256": commitment,
    }


def materialize_model_response_schema(
    schema: Mapping[str, Any], opaque_binding: str
) -> bytes:
    """Bind the closed model-facing schema to one opaque, non-descriptive token."""
    if OPAQUE_BINDING_PATTERN.fullmatch(opaque_binding) is None:
        raise ObservationError("opaque case binding must contain at least 128 bits")
    materialized = copy.deepcopy(dict(schema))
    try:
        node = materialized["properties"]["opaqueCaseBinding"]
    except (KeyError, TypeError) as error:
        raise ObservationError("model response schema lacks the opaque binding field") from error
    if type(node) is not dict:
        raise ObservationError("model response opaque binding schema must be an object")
    node.pop("pattern", None)
    node["const"] = opaque_binding
    return json.dumps(
        materialized,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    ).encode("ascii") + b"\n"


def render_case_prompt(
    envelope: Mapping[str, Any],
    request: str,
    opaque_binding: str,
) -> bytes:
    """Render one blinded model prompt; canonical case identity remains observer-side."""
    if type(request) is not str or not request:
        raise ObservationError("case request must be a nonempty string")
    if OPAQUE_BINDING_PATTERN.fullmatch(opaque_binding) is None:
        raise ObservationError("opaque case binding must contain at least 128 bits")
    bindings = envelope["contractBindings"]
    lines = [
        f"profileId: {PROFILE_ID}",
        f"opaqueCaseBinding: {opaque_binding}",
        f"profileContractSha256: {bindings['profileContractSha256']}",
        f"goldenSetSha256: {bindings['goldenSetSha256']}",
        f"modelResponseSchemaSha256: {bindings['modelResponseSchemaSha256']}",
        f"hostCaseSetId: {bindings['hostCaseSetId']}",
        f"hostCaseSetSha256: {bindings['hostCaseSetSha256']}",
        "sessionStartDelivered: false",
        "routeAssessmentOnly: true",
        "",
        "Instructions:",
    ]
    lines.extend(f"- {instruction}" for instruction in envelope["fixedInstructions"])
    lines.extend(("", "User request:", request))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _validate_taxonomy(document: dict[str, Any]) -> None:
    _exact_keys(
        document,
        {
            "schemaVersion", "taxonomyVersion", "host", "source",
            "probeAdjudication", "categories", "topLevelTypes", "itemTypes",
            "collaboration", "sourceSuppressionAudit", "requiredFeatureOverrides",
            "payloadContract", "lifecycle", "stderrPolicy", "retention",
        },
        "observer taxonomy",
    )
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
    for item in files:
        _exact_keys(item, {"path", "blob", "sha256", "authority"}, "observer source file")
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
    _expect(
        document.get("categories"),
        [
            "benign-content-progress", "tool-action-capable", "failure-error",
            "forbidden-unknown",
        ],
        "observer categories",
    )
    stderr = probe.get("stderr", {})
    _expect(stderr.get("category"), "codex-cli-stdin-additional-context-notice", "probe stderr category")
    _expect(stderr.get("length"), len(PROBE_NOTICE), "probe notice length")
    _expect(stderr.get("sourceDerivedSha256"), PROBE_NOTICE_SHA256, "probe notice digest")
    _expect(_sha256(PROBE_NOTICE), PROBE_NOTICE_SHA256, "source-derived notice bytes")
    observed_top = document.get("topLevelTypes")
    if type(observed_top) is not dict:
        raise ObservationError("observer topLevelTypes must be an object")
    for node in observed_top.values():
        _exact_keys(node, {"category", "role"}, "observer top-level type")
    _expect({key: value.get("role") for key, value in observed_top.items()}, TOP_LEVEL_TYPES, "top-level taxonomy")
    observed_items = document.get("itemTypes")
    if type(observed_items) is not dict:
        raise ObservationError("observer itemTypes must be an object")
    _expect(set(observed_items), set(ITEM_EVENTS), "item taxonomy")
    for item_type, events in ITEM_EVENTS.items():
        expected_item_keys = {"category", "allowedEvents"}
        if item_type in ITEM_STATUSES:
            expected_item_keys.add("statuses")
        _exact_keys(observed_items[item_type], expected_item_keys, f"{item_type} taxonomy")
        _expect(tuple(observed_items[item_type].get("allowedEvents", [])), events, f"{item_type} events")
        expected_statuses = ITEM_STATUSES.get(item_type)
        if expected_statuses is None:
            if "statuses" in observed_items[item_type]:
                raise ObservationError(f"{item_type} must not invent statuses")
        else:
            _expect(tuple(observed_items[item_type].get("statuses", [])), expected_statuses, f"{item_type} statuses")
    stderr_policy = _exact_keys(
        document.get("stderrPolicy"),
        {"actualCaseExpected", "probeNoticeIsGenerallyAllowed", "unknownNonempty", "rawRetention"},
        "observer stderr policy",
    )
    _expect(stderr_policy["actualCaseExpected"], "empty", "actual stderr policy")
    _expect(stderr_policy["probeNoticeIsGenerallyAllowed"], False, "probe notice scope")
    _expect(stderr_policy["unknownNonempty"], "incomplete", "unknown stderr policy")
    _expect(stderr_policy["rawRetention"], "forbidden", "stderr retention policy")

    payload = _exact_keys(
        document.get("payloadContract"),
        {
            "duplicateKeys",
            "partialUtf8OrLine",
            "threadStartedRequiredFields",
            "itemRequiredFields",
            "turnCompletedRequiredFields",
            "usageRequiredFields",
            "identifiers",
            "threadIdFormat",
            "itemIdFormat",
        },
        "observer payload contract",
    )
    _expect(payload["duplicateKeys"], "fail-closed", "observer duplicate-key policy")
    _expect(payload["partialUtf8OrLine"], "fail-closed", "observer partial-line policy")
    _expect(payload["threadStartedRequiredFields"], ["type", "thread_id"], "thread.started payload")
    _expect(payload["itemRequiredFields"], ["id", "type"], "item payload")
    _expect(payload["turnCompletedRequiredFields"], ["type", "usage"], "turn.completed payload")
    _expect(set(payload["usageRequiredFields"]), USAGE_KEYS, "turn usage payload")
    _expect(payload["identifiers"], "validate-for-stream-correlation-then-discard", "identifier retention")
    _expect(payload["threadIdFormat"], "canonical-uuid-v7", "thread identifier format")
    _expect(payload["itemIdFormat"], "item-underscore-monotonic-decimal", "item identifier format")

    lifecycle = document.get("lifecycle", {})
    _expect(lifecycle.get("threadStartedIsFirstNormalEvent"), True, "thread-start sequencing")
    _expect(lifecycle.get("knownItemsAllowedBetweenThreadAndTurn"), False, "pre-turn item policy")
    _expect(lifecycle.get("classifyItemBeforeSequencing"), True, "action-first classification")
    _expect(lifecycle.get("toolOrErrorAtAnyPhase"), "classify-and-hard-stop", "action hard-stop policy")
    _expect(lifecycle.get("eventAfterTerminal"), "fail-closed", "post-terminal policy")
    _expect(lifecycle.get("missingOrMultipleTerminal"), "fail-closed", "terminal policy")

    _expect(tuple(document.get("requiredFeatureOverrides", [])), ACTUAL_CASE_FEATURE_OVERRIDES, "suppressed-action feature controls")
    suppression = document.get("sourceSuppressionAudit", {})
    _exact_keys(
        suppression,
        {
            "actionBearing", "hookTelemetry", "nonActionContent",
            "itemVariantAudit", "additionalExecutionControls",
            "notificationCatchAllAudit", "catchAllPolicy",
        },
        "source suppression audit",
    )
    _expect(
        suppression.get("catchAllPolicy"),
        "every-action-bearing-suppressed-variant-disabled-or-batch-blocked",
        "suppressed catch-all policy",
    )
    action_bearing = suppression.get("actionBearing")
    if type(action_bearing) is not list or len(action_bearing) != 6:
        raise ObservationError("suppressed action audit must contain six closed groups")
    required_controls = {
        control
        for group in action_bearing
        if type(group) is dict
        for control in group.get("requiredControls", [])
        if control != "mcp_servers={}"
    }
    additional_controls = suppression.get("additionalExecutionControls")
    if (
        type(additional_controls) is not list
        or len(additional_controls) != len(set(additional_controls))
    ):
        raise ObservationError("additional execution controls must be a unique array")
    _expect(
        required_controls | set(additional_controls),
        set(ACTUAL_CASE_FEATURE_OVERRIDES),
        "suppressed and defensive action controls",
    )
    for group in action_bearing:
        _exact_keys(group, {"sourceVariants", "publicJsonl", "requiredControls"}, "suppressed action group")
        _expect(group.get("publicJsonl"), "suppressed", "suppressed action JSONL visibility")
        variants = group.get("sourceVariants")
        if type(variants) is not list or not variants or len(set(variants)) != len(variants):
            raise ObservationError("suppressed action variants must be a nonempty unique array")
    item_audit = _exact_keys(
        suppression.get("itemVariantAudit"),
        {
            "sourceVariantCount", "publiclyMappedVariants",
            "suppressedActionVariants", "suppressedNonActionVariants",
            "partiallySuppressedCollabVariants", "suppressedActionPolicy",
            "functionCallOutputPolicy", "sourceValidDoesNotMeanAcceptanceSafe",
        },
        "source item-variant audit",
    )
    _expect(item_audit["sourceVariantCount"], 19, "source item variant count")
    _expect(
        tuple(item_audit["publiclyMappedVariants"]),
        SOURCE_ITEM_PUBLICLY_MAPPED,
        "publicly mapped source item variants",
    )
    _expect(
        tuple(item_audit["suppressedActionVariants"]),
        SOURCE_ITEM_SUPPRESSED_ACTION,
        "suppressed source action variants",
    )
    _expect(
        tuple(item_audit["suppressedNonActionVariants"]),
        SOURCE_ITEM_SUPPRESSED_NON_ACTION,
        "suppressed source non-action variants",
    )
    _expect(
        tuple(item_audit["partiallySuppressedCollabVariants"]),
        SOURCE_COLLAB_PARTIALLY_SUPPRESSED,
        "partially suppressed collaboration variants",
    )
    _expect(
        item_audit["suppressedActionPolicy"],
        "disabled-by-exact-source-feature-controls-or-paired-public-item-hard-stop",
        "suppressed source action policy",
    )
    _expect(
        item_audit["functionCallOutputPolicy"],
        "paired-with-source-visible-tool-call-and-cannot-own-acceptance",
        "function-call-output policy",
    )
    _expect(
        item_audit["sourceValidDoesNotMeanAcceptanceSafe"],
        True,
        "source-valid item acceptance boundary",
    )
    notification_audit = _exact_keys(
        suppression.get("notificationCatchAllAudit"),
        {
            "sourceVariantCount", "explicitlyMappedVariants", "catchAllVariants",
            "pairedActionVariants", "pairedActionPolicy", "unpairedActionPolicy",
            "snapshotIsActionEvidence",
        },
        "notification catch-all audit",
    )
    _expect(notification_audit["sourceVariantCount"], 83, "source notification count")
    _expect(
        tuple(notification_audit["explicitlyMappedVariants"]),
        SOURCE_NOTIFICATION_MAPPED,
        "explicitly mapped source notifications",
    )
    _expect(
        tuple(notification_audit["catchAllVariants"]),
        SOURCE_NOTIFICATION_CATCH_ALL,
        "source notification catch-all",
    )
    _expect(
        tuple(notification_audit["pairedActionVariants"]),
        SOURCE_NOTIFICATION_PAIRED_ACTION,
        "source-suppressed paired action notifications",
    )
    _expect(
        notification_audit["pairedActionPolicy"],
        "corresponding-public-item-must-hard-stop-before-acceptance",
        "paired suppressed-action policy",
    )
    _expect(
        notification_audit["unpairedActionPolicy"],
        "no-app-server-request-channel-and-source-action-features-explicitly-disabled",
        "unpaired suppressed-action policy",
    )
    _expect(
        notification_audit["snapshotIsActionEvidence"],
        False,
        "snapshot action-evidence boundary",
    )
    hook = suppression.get("hookTelemetry", {})
    _exact_keys(hook, {"sourceVariants", "publicJsonl", "proofOwner"}, "Hook telemetry audit")
    _expect(hook.get("publicJsonl"), "not-exposed-by-codex-0.153.0", "Hook telemetry visibility")
    _expect(hook.get("proofOwner"), "verified-package-installed-tree-and-temporary-config", "no-Hook proof owner")
    _expect(
        suppression.get("nonActionContent"),
        [
            "UserMessage", "Plan", "EnteredReviewMode",
            "ExitedReviewMode", "ContextCompaction",
        ],
        "suppressed non-action variants",
    )
    collaboration = _exact_keys(
        document.get("collaboration"), {"tools", "agentStatuses"}, "collaboration taxonomy"
    )
    _expect(
        collaboration["tools"],
        ["spawn_agent", "send_input", "wait", "close_agent"],
        "collaboration tool enum",
    )
    retention = _exact_keys(
        document.get("retention"), {"allowedJournalFields", "forbidden"}, "taxonomy retention"
    )
    _expect(
        retention["allowedJournalFields"],
        ["ordinal", "eventType", "itemType", "category", "role", "status"],
        "taxonomy journal fields",
    )


def _validate_prompt(envelope: dict[str, Any], cases: Sequence[dict[str, Any]]) -> None:
    expected_keys = {
        "schemaVersion", "kind", "profileId", "transport", "contractBindings",
        "fixedInstructions", "renderOrder", "forbiddenModelInputs", "opaqueBinding",
        "requestBindings", "promptEnvelopeDigest",
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
        "modelResponseSchemaSha256": MODEL_RESPONSE_SCHEMA_SHA256,
        "hostCaseSetId": HOST_CASE_SET_ID,
        "hostCaseSetSha256": HOST_CASE_SET_SHA256,
    }
    _expect(envelope["contractBindings"], expected_bindings, "prompt contract bindings")
    forbidden = " ".join(envelope.get("fixedInstructions", [])).lower()
    for token in ("expectedroutes", "expected routes", "expectedoutcome", "caseclass", "pass label"):
        if token in forbidden:
            raise ObservationError(f"prompt instructions leak {token!r}")
    _expect(
        envelope["opaqueBinding"],
        {
            "owner": "observer",
            "entropyBitsMinimum": 128,
            "encoding": "lowercase-hex",
            "rawRetention": "forbidden",
            "trackedForm": "sha256-only",
        },
        "prompt opaque binding",
    )
    entries = envelope.get("requestBindings")
    if type(entries) is not list or len(entries) != len(cases):
        raise ObservationError("prompt request bindings must cover all 16 cases")
    expected_entries = []
    for ordinal, case in enumerate(cases, 1):
        expected_entries.append(
            {
                "ordinal": ordinal,
                "requestSha256": _sha256(case["request"].encode("utf-8")),
            }
        )
    _expect(entries, expected_entries, "prompt case bindings")
    prefix_token = "ocb1_" + "a" * 64
    for case in cases:
        prompt = render_case_prompt(envelope, case["request"], prefix_token).decode("utf-8")
        prefix, request = prompt.rsplit("User request:\n", 1)
        _expect(request, case["request"] + "\n", "prompt exact request bytes")
        if case["id"] in prompt or "contractVersion" in prefix:
            raise ObservationError("model-facing prompt leaks canonical case identity")
        for leaked in ("positive", "negative", "ambiguous", "no-route"):
            if leaked in prefix.lower():
                raise ObservationError("model-facing prompt leaks a case class")
    digest = envelope.get("promptEnvelopeDigest")
    if type(digest) is not str or DIGEST_PATTERN.fullmatch(digest) is None:
        raise ObservationError("promptEnvelopeDigest must be a SHA-256 identity")
    _expect(digest, self_digest(envelope, "promptEnvelopeDigest"), "promptEnvelopeDigest")


def _validate_fixtures(document: dict[str, Any]) -> None:
    _exact_keys(
        document,
        {
            "schemaVersion", "kind", "profileId", "generation",
            "definitions", "cases", "snapshot",
        },
        "fixture matrix",
    )
    _expect(document.get("schemaVersion"), "1", "fixture schemaVersion")
    _expect(document.get("kind"), "axiom-codex-no-hook-fixture-matrix", "fixture kind")
    _expect(document.get("profileId"), PROFILE_ID, "fixture profileId")
    _expect(
        document.get("generation"),
        {
            "model": "observer-owned-deterministic-v1",
            "networkRemote": False,
            "credentials": False,
            "realExternalChannel": False,
            "realSystemTarget": False,
            "writableMutationTarget": False,
            "prePostSnapshot": "logical-paths-modes-sizes-sha256-and-git-facts",
        },
        "fixture generation contract",
    )
    definitions = document.get("definitions")
    if type(definitions) is not list or len(definitions) != 9:
        raise ObservationError("fixture definitions must contain exactly nine templates")
    by_template: dict[str, dict[str, Any]] = {}
    for definition in definitions:
        if type(definition) is not dict:
            raise ObservationError("fixture definition must be an object")
        _validate_fixture_definition(definition)
        template_id = definition["templateId"]
        if template_id in by_template:
            raise ObservationError("fixture template IDs must be unique")
        by_template[template_id] = definition
    model_visible_fixtures = json.dumps(
        definitions, ensure_ascii=False, sort_keys=True
    ).casefold()
    for forbidden in (
        "positive", "negative", "ambiguous", "no-route", "expectedroute",
        "expectedoutcome", *ALLOWED_ROUTES,
    ):
        if forbidden.casefold() in model_visible_fixtures:
            raise ObservationError(
                "fixture definition leaks observer-owned route or case metadata"
            )
    entries = document.get("cases")
    if type(entries) is not list or len(entries) != 16:
        raise ObservationError("fixture cases must cover all 16 cases")
    expected = []
    for case_id, values in FIXTURE_MATRIX.items():
        expected.append(
            {
                "caseId": case_id,
                "fixtureKind": values[0],
                "pluginState": values[1],
                "workspaceTemplate": values[2],
                "mutationTarget": "unavailable-read-only",
            }
        )
        if values[2] not in by_template:
            raise ObservationError("fixture case references an unknown template")
        _expect(
            by_template[values[2]]["fixtureKind"],
            values[0],
            f"fixture kind for {case_id}",
        )
    _expect(entries, expected, "fixture matrix")
    case11 = entries[10]
    _expect(case11["caseId"], "no-hook-negative-unavailable-discovery-001", "case 11 identity")
    _expect(case11["pluginState"], "absent", "case 11 plugin state")
    _expect(
        document.get("snapshot"),
        {
            "beforeAndAfter": True,
            "unknownPath": "hard-stop",
            "contentChange": "hard-stop",
            "metadataChange": "hard-stop",
            "gitFactChange": "hard-stop",
            "externalState": "unavailable-by-construction",
        },
        "fixture snapshot contract",
    )


def _validate_model_response_schema(document: dict[str, Any]) -> None:
    _exact_keys(
        document,
        {"$schema", "$id", "title", "type", "additionalProperties", "required", "properties"},
        "model response schema",
    )
    _expect(document["$schema"], "https://json-schema.org/draft/2020-12/schema", "model schema dialect")
    _expect(
        document["$id"],
        "https://github.com/wheakerd/axiom/blob/main/evals/no-hook-observation/codex-model-response-schema-v1.json",
        "model schema id",
    )
    _expect(document["type"], "object", "model schema root type")
    _expect(document["additionalProperties"], False, "model schema closure")
    properties = document["properties"]
    _expect(set(document["required"]), set(properties), "model schema required fields")
    for key, node in properties.items():
        _validate_closed_schema_node(node, document, f"model schema properties/{key}")
    _expect(
        set(properties),
        {
            "profileId",
            "opaqueCaseBinding",
            "contractBindings",
            "discoveryOutcome",
            "selectedRoutes",
            "clarificationCount",
            "usingAxiomFrontDoorObserved",
            "sessionStartObserved",
            "mutationAttempted",
            "mutationObserved",
        },
        "model schema fields",
    )
    forbidden = {
        "caseId", "contractVersion", "caseClass", "expectedRoutes", "expectedOutcome",
        "expectedClarificationCount", "status", "pass", "hostIdentity", "acceptanceDiagnostic",
    }
    if forbidden & set(properties):
        raise ObservationError("model response schema exposes observer-owned acceptance data")
    _expect(properties["profileId"], {"const": PROFILE_ID}, "model profile binding")
    binding = properties["opaqueCaseBinding"]
    _expect(binding.get("type"), "string", "opaque model binding type")
    _expect(binding.get("pattern"), "^[0-9a-f]{32,128}$", "opaque model binding format")
    routes = properties["selectedRoutes"]
    _expect(tuple(routes.get("items", {}).get("enum", [])), ALLOWED_ROUTES, "uniform route enum")
    _expect(routes.get("maxItems"), 2, "model route bound")
    contracts = properties["contractBindings"]
    _expect(contracts.get("additionalProperties"), False, "model contract closure")
    _expect(set(contracts.get("required", [])), set(contracts.get("properties", {})), "model contract required fields")
    _expect(
        {key: value.get("const") for key, value in contracts["properties"].items()},
        {
            "profileContractSha256": PROFILE_SHA256,
            "goldenSetSha256": GOLDEN_SET_SHA256,
            "hostCaseSetSha256": HOST_CASE_SET_SHA256,
        },
        "model contract bindings",
    )


_SCHEMA_NODE_KEYS = frozenset(
    {
        "$ref",
        "type",
        "const",
        "enum",
        "pattern",
        "format",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "uniqueItems",
        "items",
        "additionalProperties",
        "required",
        "properties",
    }
)


def _validate_closed_schema_node(
    node: Any,
    root: Mapping[str, Any],
    label: str,
) -> None:
    """Require the exact JSON-Schema subset enforced by this observer.

    A schema is itself an untrusted acceptance input.  Rejecting unsupported
    keywords prevents a maintainer from adding a condition that a generic
    schema implementation would enforce but the bundled closed validator would
    silently ignore.
    """
    if type(node) is not dict:
        raise ObservationError(f"{label} must be a schema object")
    unknown = set(node) - _SCHEMA_NODE_KEYS
    if unknown:
        raise ObservationError(f"{label} uses unsupported schema keywords: {sorted(unknown)!r}")
    if "$ref" in node:
        if set(node) != {"$ref"}:
            raise ObservationError(f"{label} combines a reference with sibling keywords")
        reference = node["$ref"]
        if type(reference) is not str or not reference.startswith("#/$defs/"):
            raise ObservationError(f"{label} uses an unsupported schema reference")
        target = root.get("$defs", {}).get(reference.removeprefix("#/$defs/"))
        if type(target) is not dict:
            raise ObservationError(f"{label} references an unknown schema definition")
        return
    if "const" in node:
        if set(node) != {"const"}:
            raise ObservationError(f"{label} const schema has unexpected siblings")
        return
    if "enum" in node:
        if set(node) != {"enum"}:
            raise ObservationError(f"{label} enum schema has unexpected siblings")
        values = node["enum"]
        if type(values) is not list or not values:
            raise ObservationError(f"{label} enum must be a nonempty array")
        encoded = [_canonical_json(value) for value in values]
        if len(encoded) != len(set(encoded)):
            raise ObservationError(f"{label} enum contains duplicate values")
        return
    node_type = node.get("type")
    if node_type not in {"object", "array", "string", "integer", "boolean", "null"}:
        raise ObservationError(f"{label} has an unsupported or missing schema type")
    if node_type == "object":
        allowed = {"type", "additionalProperties", "required", "properties"}
        if set(node) != allowed or node["additionalProperties"] is not False:
            raise ObservationError(f"{label} object schema is not exactly closed")
        properties = node["properties"]
        required = node["required"]
        if (
            type(properties) is not dict
            or type(required) is not list
            or len(required) != len(set(required))
            or set(required) != set(properties)
        ):
            raise ObservationError(f"{label} required fields do not close its properties")
        for key, child in properties.items():
            if type(key) is not str or not key:
                raise ObservationError(f"{label} contains an invalid property name")
            _validate_closed_schema_node(child, root, f"{label}/properties/{key}")
        return
    if node_type == "array":
        allowed = {"type", "items", "minItems", "maxItems", "uniqueItems"}
        if set(node) - allowed or "items" not in node:
            raise ObservationError(f"{label} array schema is outside the closed subset")
        minimum = node.get("minItems", 0)
        maximum = node.get("maxItems")
        if type(minimum) is not int or minimum < 0:
            raise ObservationError(f"{label} has an invalid minimum item count")
        if maximum is not None and (
            type(maximum) is not int or maximum < minimum
        ):
            raise ObservationError(f"{label} has an invalid maximum item count")
        if "uniqueItems" in node and type(node["uniqueItems"]) is not bool:
            raise ObservationError(f"{label} has an invalid uniqueItems flag")
        _validate_closed_schema_node(node["items"], root, f"{label}/items")
        return
    allowed_by_type = {
        "string": {"type", "pattern", "format"},
        "integer": {"type", "minimum", "maximum"},
        "boolean": {"type"},
        "null": {"type"},
    }
    if set(node) - allowed_by_type[node_type]:
        raise ObservationError(f"{label} scalar schema is outside the closed subset")
    if node_type == "string":
        if "pattern" in node and type(node["pattern"]) is not str:
            raise ObservationError(f"{label} has an invalid pattern")
        if "format" in node and node["format"] != "date-time":
            raise ObservationError(f"{label} has an unsupported format")
    if node_type == "integer":
        minimum = node.get("minimum")
        maximum = node.get("maximum")
        if minimum is not None and type(minimum) is not int:
            raise ObservationError(f"{label} has an invalid integer minimum")
        if maximum is not None and type(maximum) is not int:
            raise ObservationError(f"{label} has an invalid integer maximum")
        if minimum is not None and maximum is not None and maximum < minimum:
            raise ObservationError(f"{label} has an inverted integer range")


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
        "schemaVersion", "kind", "runMode", "runId", "recordedAt", "overallStatus",
        "materialization", "observationProtocol", "runner", "axiomIdentity",
        "contractBindings", "hostIdentity", "executionFacts",
        "installationFacts", "objectBindingFacts", "noHookProof", "cases",
        "summary", "cleanup", "diagnosticCodes",
    }
    _expect(set(properties), expected_root, "result schema root fields")
    for key, node in properties.items():
        _validate_closed_schema_node(node, document, f"result schema properties/{key}")
    for key, node in document["$defs"].items():
        _validate_closed_schema_node(node, document, f"result schema definitions/{key}")
    for key in (
        "observationProtocol", "runner", "axiomIdentity", "contractBindings",
        "materialization", "hostIdentity", "executionFacts", "installationFacts",
        "objectBindingFacts", "noHookProof", "summary", "cleanup",
    ):
        node = properties[key]
        _expect(node.get("type"), "object", f"result schema {key} type")
        _expect(node.get("additionalProperties"), False, f"result schema {key} closure")
        _expect(set(node.get("required", [])), set(node.get("properties", {})), f"result schema {key} required fields")
    case_def = document.get("$defs", {}).get("caseResult", {})
    _expect(set(document.get("$defs", {})), {"sha256", "prefixedSha256", "diagnosticCodes", "fixtureFacts", "caseResult"}, "result schema definitions")
    _expect(case_def.get("type"), "object", "case result type")
    _expect(case_def.get("additionalProperties"), False, "case result closure")
    _expect(set(case_def.get("required", [])), set(case_def.get("properties", {})), "case result required fields")
    _expect(
        set(case_def.get("properties", {})),
        {
            "caseId", "contractVersion", "casePromptSha256", "modelResponseSchemaSha256",
            "opaqueBindingSha256", "materializationCommitmentSha256",
            "opaqueBindingMatched", "modelResponseSchemaMatched",
            "fixtureDefinitionDigest", "realizedFixtureDigest", "realizedFileSetDigest",
            "fixturePreSnapshotSha256", "fixturePostSnapshotSha256",
            "fixtureMatched", "fixtureFacts", "status", "responseDiagnostic",
            "acceptanceDiagnostic", "discoveryOutcome", "selectedRoutes", "clarificationCount",
            "usingAxiomFrontDoorObserved", "sessionStartObserved", "mutationAttempted",
            "mutationObserved", "toolActionCount", "mutationAttemptCount",
            "mutationObservationCount", "externalActionCount", "deniedOperationCount",
            "unknownEventCount", "malformedEventCount", "workspaceUnchanged",
            "bundleUnchanged", "installedCopyUnchanged", "temporaryUserStateUnchanged",
            "modelCallAuthorized", "modelProcessStarted", "promptFullyDelivered",
            "marketplaceProcessStarted", "pluginInstallProcessStarted",
            "schemaObjectVerified", "installedDirectoryIdentityVerified",
            "diagnosticCodes",
        },
        "case result fields",
    )
    _expect(properties["cases"].get("minItems"), 16, "result cases minimum")
    _expect(properties["cases"].get("maxItems"), 16, "result cases maximum")
    forbidden_names = {"rawJsonl", "rawStderr", "responseText", "reasoningText", "toolArguments", "commandText", "absolutePath", "credential", "environment", "limitations", "threadId", "itemId"}
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
    materialization = properties["materialization"]["properties"]
    _expect(
        materialization["scheme"].get("const"),
        MATERIALIZATION_SCHEME,
        "result materialization scheme",
    )
    _expect(
        materialization["schemaVersion"].get("const"),
        "1",
        "result materialization version",
    )
    _expect(
        materialization["materializationSeed"].get("pattern"),
        "^[0-9a-f]{64}$",
        "result public materialization seed shape",
    )
    codes = document["$defs"]["diagnosticCodes"]["items"].get("enum")
    _expect(set(codes), set(DIAGNOSTIC_CODES), "result diagnostic codes")
    if any(type(value) is str and value == "string" for value in _walk_json(document.get("properties", {}))):
        # Every retained string must be constrained by const, enum, pattern, or format.
        def inspect(node: Any, label: str) -> None:
            if type(node) is dict:
                if node.get("type") == "string" and not any(key in node for key in ("const", "enum", "pattern", "format")):
                    raise ObservationError(f"result schema exposes unconstrained retained text at {label}")
                for key, child in node.items():
                    inspect(child, f"{label}/{key}")
            elif type(node) is list:
                for index, child in enumerate(node):
                    inspect(child, f"{label}/{index}")
        inspect(document, "result schema")


def _validate_protocol(
    protocol: dict[str, Any],
    file_bytes: Mapping[Path, bytes],
    envelope: dict[str, Any],
) -> None:
    _exact_keys(
        protocol,
        {
            "schemaVersion", "kind", "protocolId", "status", "source",
            "axiomIdentity", "contractBindings", "host", "execution",
            "installation", "noHookProof", "bounds", "stderrPolicy",
            "batchPolicy", "retention", "materialization", "objectBinding",
            "cases", "runner", "cleanup", "nonClaims", "protocolDigest",
        },
        "observation protocol",
    )
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
    _exact_keys(
        bindings,
        {
            "profileContract", "goldenSet", "responseSchema",
            "modelResponseSchema", "benchmark", "hostCaseSet",
            "observerTaxonomy", "promptEnvelope", "fixtureMatrix",
            "resultSchema",
        },
        "protocol contract bindings",
    )
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
    _expect(bindings.get("modelResponseSchema"), {"path": MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix(), "sha256": _sha256(file_bytes[MODEL_RESPONSE_SCHEMA_RELATIVE])}, "protocol model schema binding")
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
        "targetOperatingSystem": "linux",
        "targetArchitecture": "x86_64",
        "sourceSuppressedActionPolicy": "explicitly-disabled",
        "featureOverrides": list(ACTUAL_CASE_FEATURE_OVERRIDES),
        "criticalPathTransport": "linux-proc-fd-inherited",
        "childDescriptorAllowlist": "minimum-required-pass-fds",
    }
    _expect(execution, required_execution, "protocol execution")
    _expect(
        protocol.get("installation"),
        {
            "scope": "isolated-ephemeral-test-only",
            "marketplace": "observer-owned-local",
            "sourceBundleIdentityRequired": True,
            "installedPathWithinTemporaryHome": True,
            "installedTreeMustMatchBundle": True,
            "sharedInstalledBytesAcrossCases": False,
            "case11PluginState": "absent",
            "fullProfileWrapperAllowed": False,
            "credentialStoreOverride": "file-within-temporary-codex-home",
            "cleanupAfterBatch": True,
            "persistentUserStateChangeAllowed": False,
            "installedObjectBinding": "descriptor-pinned-within-frozen-codex-home",
        },
        "protocol installation contract",
    )
    _expect(
        protocol.get("noHookProof"),
        {
            "staticPackageFacts": ["manifest-hooks-field-absent", "hooks-path-absent"],
            "isolatedInstallationFacts": [
                "installed-manifest-hooks-field-absent", "installed-hooks-path-absent",
                "temporary-config-hook-registration-absent", "full-profile-wrapper-absent",
            ],
            "publicJsonlHookTelemetry": "not-exposed-by-codex-0.153.0",
            "modelResponseFacts": ["sessionStartObserved-false"],
            "proofOwner": "verified-package-installed-tree-and-temporary-config",
            "publicJsonlAbsenceIsRuntimeProof": False,
            "fullProfileHookCiReusable": False,
        },
        "protocol no-Hook proof contract",
    )
    bounds = protocol.get("bounds", {})
    _expect(bounds.get("caseTimeoutSeconds"), CASE_TIMEOUT_SECONDS, "case timeout")
    _expect(bounds.get("stdoutBytes"), MAX_STDOUT_BYTES, "stdout bound")
    _expect(bounds.get("stderrBytes"), MAX_STDERR_BYTES, "stderr bound")
    _expect(bounds.get("jsonlLineBytes"), MAX_JSONL_LINE_BYTES, "line bound")
    _expect(bounds.get("eventCount"), MAX_EVENT_COUNT, "event bound")
    _expect(bounds.get("structuredResultBytes"), MAX_RESULT_BYTES, "result bound")
    _expect(bounds.get("diagnosticCodeCount"), len(DIAGNOSTIC_CODES), "diagnostic code bound")
    _expect(
        set(bounds),
        {
            "caseTimeoutSeconds", "stdoutBytes", "stderrBytes",
            "jsonlLineBytes", "eventCount", "structuredResultBytes",
            "retainedJournalEntries", "diagnosticCodeCount",
        },
        "protocol bound fields",
    )
    _expect(bounds.get("retainedJournalEntries"), MAX_EVENT_COUNT, "journal bound")
    _expect(
        protocol.get("stderrPolicy"),
        {
            "actualCaseExpected": "empty",
            "nonemptyUnknownOutcome": "incomplete-hard-stop",
            "rawRetention": "forbidden",
            "probeOnlyCategory": "codex-cli-stdin-additional-context-notice",
            "probeOnlyCategoryAllowedForActualCases": False,
        },
        "protocol stderr contract",
    )
    _expect(
        protocol.get("batchPolicy"),
        {
            "routingMismatch": "case-fail-continue",
            "hardStopReasons": [
                "schema-mismatch", "unknown-event-item-or-status",
                "malformed-jsonl", "tool-or-mutation-attempt",
                "workspace-mutation", "bundle-or-installed-copy-drift",
                "credential-exposure", "identity-drift",
                "observer-integrity-failure", "missing-or-multiple-terminal",
                "event-after-terminal", "unexpected-stderr",
                "stdin-write-integrity-failure",
                "source-suppressed-action-surface-enabled",
                "cleanup-incomplete",
            ],
            "remainingCasesAfterHardStop": "not-run",
            "terminalLedgerState": "irreversible",
        },
        "protocol batch contract",
    )
    _expect(
        protocol.get("retention"),
        {
            "normalizedOnly": True,
            "rawJsonl": "forbidden",
            "rawStderr": "forbidden",
            "modelText": "forbidden",
            "reasoningText": "forbidden",
            "toolArgumentsAndOutput": "forbidden",
            "sessionThreadItemIdentifiers": "forbidden",
            "credentialsAndConfiguration": "forbidden",
            "absolutePathsAndTemporaryNames": "forbidden",
            "environmentDump": "forbidden",
            "opaqueCaseToken": "forbidden",
            "descriptorDeviceInode": "forbidden",
            "procfsAliases": "forbidden",
            "materializationSeed": "public-verifier-input",
        },
        "protocol retention contract",
    )
    _expect(
        protocol.get("materialization"),
        {
            "scheme": MATERIALIZATION_SCHEME,
            "schemaVersion": "1",
            "seedBytes": 32,
            "seedEncoding": "64-lowercase-hex",
            "seedGeneration": "observer-cryptographic-random",
            "seedRetention": "public-verifier-input",
            "seedModelDisclosure": "forbidden",
            "opaqueTokenDerivation": "sha256-domain-seed-ordinal-protocol",
            "opaqueTokenDomain": "axiom-codex-opaque-case-binding-v1\u0000",
            "ordinalEncoding": "unsigned-2-byte-big-endian",
            "protocolDigestEncoding": "32-raw-bytes-without-sha256-prefix",
            "opaqueTokenEncoding": "ocb1-lowercase-hex",
            "opaqueTokenRetention": "forbidden",
            "caseCommitment": "canonical-json-sha256",
            "caseCommitmentCanonicalFields": [
                "schemaVersion", "scheme", "protocolDigest",
                "materializationSeedSha256", "caseOrdinal", "caseId",
                "contractVersion", "requestSha256", "realizedFixtureDigest",
                "realizedFileSetDigest", "opaqueBindingSha256",
                "modelResponseSchemaSha256", "casePromptSha256",
            ],
            "caseCommitmentSeedIdentity": "sha256-of-32-raw-seed-bytes",
            "caseCommitmentRequestIdentity": "sha256-of-exact-utf8-request-bytes",
            "undeliveredPromptDigest": "64-zero-sentinel",
            "rootCommitment": "ordered-16-case-canonical-json-sha256",
            "rootCommitmentCanonicalFields": [
                "schemaVersion", "scheme", "commitments",
            ],
            "rootCommitmentOrder": "canonical-host-case-set-ordinal",
            "validatorRecomputation": "required",
        },
        "protocol materialization contract",
    )
    _expect(
        protocol.get("objectBinding"),
        {
            "runRootWrites": "frozen-root-fd-relative-only",
            "runRootReplacement": "write-original-object-then-incomplete-manual-cleanup",
            "schemaObject": "open-nofollow-regular-single-link-fd-inherited",
            "schemaArgument": "linux-proc-self-fd-alias-no-path-fallback",
            "schemaLifetime": "open-through-child-terminal",
            "childDescriptorAllowlist": "exact-required-pass-fds",
            "installedDirectory": "componentwise-nofollow-from-frozen-codex-home-held-pre-launch-post-launch",
            "codexHomeTransport": "linux-proc-self-fd-alias",
            "externalOutput": "prefrozen-parent-fd-exclusive-single-basename",
            "externalOutputParentFreeze": "before-observation-orchestration",
            "externalOutputFailure": "incomplete-manual-cleanup-no-host-pass",
            "cleanupOwnership": "creation-immediate-or-validated-child-acceptance-ledger",
            "childObjectAcceptance": "closed-receipt-object-and-tree-before-ledger",
            "unknownObjectPolicy": "preserve-never-delete",
            "identityFailure": "incomplete-manual-cleanup",
            "portableEvidence": "closed-normalized-facts-and-commitments-only",
            "retainedDescriptorNumbers": False,
        },
        "protocol object-binding contract",
    )
    _expect(protocol.get("cases"), _case_contracts(), "protocol cases")
    runner = protocol.get("runner", {})
    _exact_keys(
        runner,
        {"version", "behaviorDependencies", "defaultMode", "executionGuards", "output"},
        "protocol runner",
    )
    expected_dependencies = [
        {"path": ENTRYPOINT_RELATIVE.as_posix(), "role": "entrypoint", "sha256": _sha256(file_bytes[ENTRYPOINT_RELATIVE])},
        {"path": MODULE_RELATIVE.as_posix(), "role": "implementation-validator", "sha256": _sha256(file_bytes[MODULE_RELATIVE])},
        {"path": FAKE_CLI_RELATIVE.as_posix(), "role": "fake-process-fixture", "sha256": _sha256(file_bytes[FAKE_CLI_RELATIVE])},
    ]
    _expect(runner.get("behaviorDependencies"), expected_dependencies, "runner behavior dependencies")
    _expect(runner.get("defaultMode"), "protocol-validation-only", "runner default mode")
    _expect(runner.get("version"), "1", "runner version")
    _expect(runner.get("output"), "caller-supplied-path-outside-repository", "runner output")
    _expect(
        set(runner.get("executionGuards", [])),
        {
            "execute-flag", "exact-protocol-digest", "exact-runner-and-module-digests",
            "exact-binary-digest", "exact-cli-version", "exact-source-main-and-tree",
            "exact-model-and-reasoning-effort", "exact-linux-x86-64-host",
            "exact-run-root-identity", "exact-call-count-authorization",
            "dedicated-credential-presence", "single-use-run-nonce",
            "irreversible-call-counter", "single-launcher-purpose-argv-env-binding",
            "executable-fd-pinning", "pidfd-termination",
            "install-sequence-authorization",
        },
        "runner execution guards",
    )
    _expect(
        protocol.get("cleanup"),
        {
            "order": [
                "terminate-and-reap-child", "seal-terminal-ledger",
                "remove-raw-streams", "remove-case-workspace",
                "remove-installed-copy", "remove-case-codex-home",
                "remove-local-marketplace", "remove-runtime-root",
                "verify-user-state-unchanged",
            ],
            "identitySubstitution": "stop-and-preserve-for-manual-cleanup",
            "successRequirement": "all-observer-owned-temporary-state-absent",
            "ownershipLedger": "creation-or-accepted-child-identity-only",
            "deletionMethod": "descriptor-relative-quarantine-then-delete",
        },
        "protocol cleanup contract",
    )
    _expect(
        protocol.get("nonClaims"),
        [
            "codex-no-hook-host-observed", "chatgpt-host-observed",
            "windows-native-bundle-executed", "full-profile-installed-observed",
            "official-submission", "installation", "publication",
        ],
        "protocol non-claims",
    )
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
        MODEL_RESPONSE_SCHEMA_RELATIVE,
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
        FAKE_CLI_RELATIVE,
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
    load_codex_benchmark_contract(root)
    _validate_taxonomy(documents[TAXONOMY_RELATIVE])
    _validate_prompt(documents[PROMPT_RELATIVE], cases)
    _validate_fixtures(documents[FIXTURES_RELATIVE])
    _validate_model_response_schema(documents[MODEL_RESPONSE_SCHEMA_RELATIVE])
    _expect(
        _sha256(file_bytes[MODEL_RESPONSE_SCHEMA_RELATIVE]),
        MODEL_RESPONSE_SCHEMA_SHA256,
        "model response schema SHA-256",
    )
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
        "modelResponseSchemaSha256": _sha256(file_bytes[MODEL_RESPONSE_SCHEMA_RELATIVE]),
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
        raise StreamBoundaryError(
            "JSONL line exceeds the byte limit", malformed_event_count=1
        )
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise StreamBoundaryError(
            f"malformed JSONL: {error}", malformed_event_count=1
        ) from error
    if type(value) is not dict:
        raise StreamBoundaryError(
            "JSONL event must be an object", malformed_event_count=1
        )
    return value


def _validate_identifier(value: Any, label: str) -> str:
    if type(value) is not str or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ObservationError(f"{label} must be a bounded non-control string")
    return value


def _validate_thread_identifier(value: Any) -> str:
    value = _validate_identifier(value, "thread.started thread_id")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as error:
        raise ObservationError("thread.started thread_id must be a canonical UUIDv7") from error
    if (
        str(parsed) != value
        or parsed.version != 7
        or parsed.variant != uuid.RFC_4122
    ):
        raise ObservationError("thread.started thread_id must be a canonical UUIDv7")
    return value


def _validate_item_identifier(value: Any, label: str) -> str:
    value = _validate_identifier(value, label)
    if ITEM_IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ObservationError(f"{label} must use the source item_<ordinal> form")
    return value


def _validate_usage(value: Any) -> None:
    usage = _exact_keys(value, USAGE_KEYS, "turn.completed usage")
    for key, count in usage.items():
        if type(count) is not int or count < 0 or count > 2**63 - 1:
            raise ObservationError(f"turn.completed usage {key} is outside the source range")


def _validate_item_payload(item: dict[str, Any], item_type: str) -> str:
    """Validate source-required shape and return the privacy-safe item identifier."""
    required: dict[str, set[str]] = {
        "agent_message": {"id", "type", "text"},
        "reasoning": {"id", "type", "text"},
        "todo_list": {"id", "type", "items"},
        "command_execution": {"id", "type", "command", "aggregated_output", "exit_code", "status"},
        "file_change": {"id", "type", "changes", "status"},
        "mcp_tool_call": {"id", "type", "server", "tool", "arguments", "result", "error", "status"},
        "collab_tool_call": {"id", "type", "tool", "sender_thread_id", "receiver_thread_ids", "prompt", "agents_states", "status"},
        "web_search": {"id", "type", "query", "action"},
        "error": {"id", "type", "message"},
    }
    _exact_keys(item, required[item_type], f"{item_type} item")
    item_id = _validate_item_identifier(item["id"], f"{item_type} item id")
    if item_type in {"agent_message", "reasoning", "error"}:
        field = "message" if item_type == "error" else "text"
        if type(item[field]) is not str or len(item[field].encode("utf-8")) > MAX_JSONL_LINE_BYTES:
            raise ObservationError(f"{item_type} {field} must be a string")
    elif item_type == "todo_list":
        if type(item["items"]) is not list or len(item["items"]) > 256:
            raise ObservationError("todo_list items must be a bounded array")
        for ordinal, todo in enumerate(item["items"]):
            todo = _exact_keys(todo, {"text", "completed"}, f"todo_list item {ordinal}")
            if type(todo["text"]) is not str or type(todo["completed"]) is not bool:
                raise ObservationError("todo_list item has an invalid shape")
    elif item_type == "command_execution":
        if type(item["command"]) is not str or type(item["aggregated_output"]) is not str:
            raise ObservationError("command_execution text fields have invalid types")
        exit_code = item["exit_code"]
        if exit_code is not None and (
            type(exit_code) is not int or exit_code < -(2**31) or exit_code > 2**31 - 1
        ):
            raise ObservationError("command_execution exit_code is outside the source range")
    elif item_type == "file_change":
        changes = item["changes"]
        if type(changes) is not list or len(changes) > 1024:
            raise ObservationError("file_change changes must be a bounded array")
        for ordinal, change in enumerate(changes):
            change = _exact_keys(change, {"path", "kind"}, f"file_change entry {ordinal}")
            if type(change["path"]) is not str or not change["path"]:
                raise ObservationError("file_change path must be a nonempty string")
            if change["kind"] not in {"add", "delete", "update"}:
                raise ObservationError("file_change kind is outside the source enum")
    elif item_type == "mcp_tool_call":
        if type(item["server"]) is not str or type(item["tool"]) is not str:
            raise ObservationError("mcp_tool_call owner fields must be strings")
        result = item["result"]
        if result is not None:
            if type(result) is not dict or not {"content", "structured_content"} <= set(result):
                raise ObservationError("mcp_tool_call result has an invalid shape")
            if set(result) - {"content", "structured_content", "_meta"}:
                raise ObservationError("mcp_tool_call result has unowned fields")
            if type(result["content"]) is not list or len(result["content"]) > 1024:
                raise ObservationError("mcp_tool_call content must be a bounded array")
        error = item["error"]
        if error is not None:
            error = _exact_keys(error, {"message"}, "mcp_tool_call error")
            if type(error["message"]) is not str:
                raise ObservationError("mcp_tool_call error message must be a string")
    elif item_type == "collab_tool_call":
        if item["tool"] not in {"spawn_agent", "send_input", "wait", "close_agent"}:
            raise ObservationError("collab_tool_call tool is outside the source enum")
        _validate_identifier(item["sender_thread_id"], "collab sender thread id")
        receiver_ids = item["receiver_thread_ids"]
        if type(receiver_ids) is not list or len(receiver_ids) > 256:
            raise ObservationError("collab receiver IDs must be a bounded array")
        for value in receiver_ids:
            _validate_identifier(value, "collab receiver thread id")
        if item["prompt"] is not None and type(item["prompt"]) is not str:
            raise ObservationError("collab prompt must be null or a string")
        states = item["agents_states"]
        if type(states) is not dict or len(states) > 256:
            raise ObservationError("collab agent states must be a bounded object")
        for key, value in states.items():
            _validate_identifier(key, "collab agent state id")
            value = _exact_keys(value, {"status", "message"}, "collab agent state")
            if value["status"] not in {
                "pending_init", "running", "interrupted", "completed", "errored",
                "shutdown", "not_found",
            }:
                raise ObservationError("collab agent status is outside the source enum")
            if value["message"] is not None and type(value["message"]) is not str:
                raise ObservationError("collab agent message must be null or a string")
    elif item_type == "web_search":
        if type(item["query"]) is not str or type(item["action"]) is not dict:
            raise ObservationError("web_search payload has invalid source types")
        action = item["action"]
        action_type = action.get("type")
        fields_by_type = {
            "search": {"type", "query", "queries"},
            "open_page": {"type", "url"},
            "find_in_page": {"type", "url", "pattern"},
            "other": {"type"},
        }
        if action_type not in fields_by_type:
            raise ObservationError("web_search action is outside the source enum")
        if set(action) - fields_by_type[action_type] or "type" not in action:
            raise ObservationError("web_search action contains unowned fields")
        for key, value in action.items():
            if key == "type":
                continue
            if key == "queries":
                if type(value) is not list or len(value) > 256 or any(
                    type(query) is not str for query in value
                ):
                    raise ObservationError("web_search queries have an invalid source shape")
            elif value is not None and type(value) is not str:
                raise ObservationError("web_search action field has an invalid source type")
    return item_id


def classify_action_item(item_type: str, status_value: Any, item: Mapping[str, Any] | None = None) -> str:
    """Classify source-visible tool activity without interpreting retained command text."""
    if item_type == "file_change":
        return "mutation-observed" if status_value == "completed" else "mutation-attempt"
    if item_type == "command_execution":
        if status_value == "declined":
            return "denied-operation"
        command = item.get("command") if item is not None else None
        if type(command) is not str or not command.strip():
            return "unknown-action"
        lowered = command.lower()
        if any(token in lowered for token in ("auth.json", "codex_api_key", "credential", "token")):
            return "external-action"
        if re.search(r"(^|[;&| ]|sudo )(rm|mv|cp|touch|mkdir|chmod|chown|tee|curl|wget)( |$)", lowered) or re.search(r"git\s+(commit|push|reset|checkout|clean|stash|tag|merge|rebase)\b", lowered) or any(token in command for token in (">", "2>", ">>")):
            return "mutation-attempt"
        if re.fullmatch(r"\s*(pwd|ls(?:\s+[^;&|<>]+)?|stat\s+[^;&|<>]+|git\s+(status|diff|show|rev-parse)(?:\s+[^;&|<>]+)?)\s*", command):
            return "read-only-inspection"
        return "unknown-action"
    if item_type in {"mcp_tool_call", "collab_tool_call", "web_search"}:
        return "external-action"
    return "read-only-inspection"


def parse_jsonl(data: bytes, taxonomy: Mapping[str, Any]) -> StreamFacts:
    """Validate the exact 0.153.0 public JSONL lifecycle without retaining payloads."""
    if len(data) > MAX_STDOUT_BYTES:
        raise ObservationError("JSONL stdout exceeds the byte limit")
    raw_lines = data.splitlines(keepends=True)
    if data and not data.endswith(b"\n"):
        raise ObservationError("JSONL stream ends with a truncated line")
    if b"\r" in data:
        raise ObservationError("JSONL stream is not canonical Linux LF data")
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
    item_states: dict[str, str] = {}
    completed_item_ids: set[str] = set()
    next_item_ordinal = 0

    for ordinal, raw in enumerate(raw_lines, 1):
        if terminal is not None:
            events_after_terminal += 1
            raise ObservationError("event appeared after terminal outcome")
        if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
            raise ObservationError("JSONL record framing is invalid")
        event = _parse_json_line(raw[:-1])
        event_type = event.get("type")
        if type(event_type) is not str or event_type not in known_top:
            raise StreamBoundaryError(
                "unknown top-level JSONL event", unknown_event_count=1
            )
        ordered.append(event_type)
        entry: dict[str, Any] = {
            "ordinal": ordinal,
            "eventType": event_type,
            "category": known_top[event_type]["category"],
            "role": known_top[event_type]["role"],
        }
        if event_type == "thread.started":
            _exact_keys(event, {"type", "thread_id"}, "thread.started")
            _validate_thread_identifier(event["thread_id"])
            if thread_seen or turn_seen:
                raise ObservationError("duplicate or out-of-order thread.started")
            if ordinal != 1:
                raise ObservationError("thread.started must be the first event")
            thread_seen = True
        elif event_type == "turn.started":
            _exact_keys(event, {"type"}, "turn.started")
            if not thread_seen or turn_seen:
                raise ObservationError("duplicate or out-of-order turn.started")
            turn_seen = True
        elif event_type in {"turn.completed", "turn.failed"}:
            if not thread_seen or not turn_seen:
                raise ObservationError("terminal event preceded lifecycle start")
            if any(state != "completed" for state in item_states.values()):
                raise ObservationError("terminal event left an item lifecycle incomplete")
            if event_type == "turn.completed":
                _exact_keys(event, {"type", "usage"}, "turn.completed")
                _validate_usage(event["usage"])
            else:
                failure = _exact_keys(event, {"type", "error"}, "turn.failed")
                error = _exact_keys(failure["error"], {"message"}, "turn.failed error")
                if type(error["message"]) is not str:
                    raise ObservationError("turn.failed error message must be a string")
            terminal = event_type
            terminal_count += 1
        elif event_type == "error":
            _exact_keys(event, {"type", "message"}, "error event")
            raise ObservationError("top-level error event")
        else:
            _exact_keys(event, {"type", "item"}, f"{event_type} event")
            item = event.get("item")
            if type(item) is not dict:
                raise ObservationError("item event lacks an item object")
            item_type = item.get("type")
            if type(item_type) is not str or item_type not in known_items:
                raise StreamBoundaryError(
                    "unknown JSONL item type", unknown_event_count=1
                )
            status_values = known_items[item_type].get("statuses")
            status_value = item.get("status")
            if status_values is not None:
                if status_value not in status_values:
                    raise StreamBoundaryError(
                        "unknown JSONL item status",
                        tool_action_count=int(item_type in TOOL_ITEM_TYPES),
                        unknown_event_count=1,
                    )
            elif status_value is not None:
                raise ObservationError("status is not allowed for this JSONL item")
            if item_type in TOOL_ITEM_TYPES:
                tool_count += 1
                try:
                    _validate_item_payload(item, item_type)
                except ObservationError as error:
                    raise StreamBoundaryError(
                        "tool-capable event has an invalid source payload",
                        tool_action_count=1,
                        unknown_event_count=1,
                    ) from error
                action = classify_action_item(item_type, status_value, item)
                counters = {
                    "mutation-attempt": {"mutation_attempt_count": 1},
                    "mutation-observed": {"mutation_observation_count": 1},
                    "external-action": {"external_action_count": 1},
                    "denied-operation": {"denied_operation_count": 1},
                    "unknown-action": {"unknown_event_count": 1},
                }.get(action, {})
                raise StreamBoundaryError(
                    f"tool-capable event observed: {action}",
                    tool_action_count=1,
                    **counters,
                )
            allowed_events = known_items[item_type].get("allowedEvents", [])
            if event_type not in allowed_events:
                raise ObservationError("item appeared in an invalid lifecycle event")
            item_id = _validate_item_payload(item, item_type)
            item_types.append(item_type)
            entry["itemType"] = item_type
            entry["category"] = known_items[item_type]["category"]
            if status_values is not None:
                statuses.append(status_value)
                entry["status"] = status_value
            if item_type == "error":
                raise ObservationError("error item observed")
            if not thread_seen or not turn_seen:
                raise ObservationError("item appeared outside the active turn")
            previous = item_states.get(item_id)
            if previous is None and item_id not in completed_item_ids:
                expected_item_id = f"item_{next_item_ordinal}"
                if item_id != expected_item_id:
                    raise ObservationError("item id is outside the source emission sequence")
                next_item_ordinal += 1
            if event_type == "item.started":
                if previous is not None or item_id in completed_item_ids:
                    raise ObservationError("item.started reused an item id")
                item_states[item_id] = "started"
            elif event_type == "item.updated":
                if previous not in {"started", "updated"}:
                    raise ObservationError("item.updated lacks a matching start")
                item_states[item_id] = "updated"
            elif event_type == "item.completed":
                if item_type == "todo_list":
                    if previous not in {"started", "updated"}:
                        raise ObservationError("todo_list completion lacks a matching start")
                elif previous is not None:
                    raise ObservationError("completed content item reused a live item id")
                if item_id in completed_item_ids:
                    raise ObservationError("item id completed more than once")
                item_states[item_id] = "completed"
                completed_item_ids.add(item_id)
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


def validate_model_response(
    response: Mapping[str, Any],
    case: Mapping[str, Any],
    opaque_binding: str,
    model_schema: Mapping[str, Any],
) -> list[str]:
    """Validate blinded model facts and compare only observer-owned expectations."""
    failures: list[str] = []
    try:
        materialized = json.loads(
            materialize_model_response_schema(model_schema, opaque_binding),
            object_pairs_hook=_reject_duplicate_pairs,
        )
        _validate_schema_value(response, materialized, materialized, "model response")
    except (json.JSONDecodeError, ObservationError):
        return ["response keys do not match the closed schema"]
    if response.get("opaqueCaseBinding") != opaque_binding:
        failures.append("opaque binding mismatch")
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
        *[
            argument
            for feature in ACTUAL_CASE_FEATURE_OVERRIDES
            for argument in ("-c", feature)
        ],
        "-",
    ]


def build_marketplace_add_argv(executable: Path, marketplace: Path) -> list[str]:
    """Build the isolated local-marketplace registration command."""
    return [
        str(executable),
        "-c",
        'cli_auth_credentials_store="file"',
        "plugin",
        "marketplace",
        "add",
        str(marketplace),
        "--json",
    ]


def build_plugin_add_argv(executable: Path) -> list[str]:
    """Build the isolated derived-profile installation command."""
    return [
        str(executable),
        "-c",
        'cli_auth_credentials_store="file"',
        "plugin",
        "add",
        PLUGIN_ID,
        "--json",
    ]


def _load_process_json(data: bytes, label: str) -> dict[str, Any]:
    if len(data) > MAX_RECEIPT_BYTES:
        raise ObservationError(f"{label} exceeds the receipt byte limit")
    try:
        text = data.decode("utf-8")
        decoder = json.JSONDecoder(object_pairs_hook=_reject_duplicate_pairs)
        start = len(text) - len(text.lstrip())
        document, end = decoder.raw_decode(text, start)
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise ObservationError(f"{label} is invalid JSON: {error}") from error
    if text[end:].strip():
        raise ObservationError(f"{label} contains trailing data or multiple JSON values")
    if type(document) is not dict:
        raise ObservationError(f"{label} must contain a JSON object")
    return document


def _receipt_relative_path(
    value: str,
    codex_home: FrozenDirectoryIdentity,
    expected: tuple[str, ...],
    label: str,
) -> str:
    path = Path(value)
    codex_alias = Path(f"/proc/self/fd/{codex_home.descriptor}")
    if not path.is_absolute():
        raise ObservationError(f"{label} must be absolute")
    try:
        relative = path.relative_to(codex_alias)
    except ValueError as error:
        raise ObservationError(f"{label} is not lexically within its isolated home") from error
    if relative.parts != expected:
        raise ObservationError(f"{label} is outside its exact source-owned location")
    return "/".join((*_closed_relative_parts(codex_home.relative_path), *expected))


def parse_marketplace_receipt(
    data: bytes,
    session: OwnedRootSession,
    codex_home: FrozenDirectoryIdentity,
) -> dict[str, Any]:
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
    _verify_frozen_directory(codex_home)
    _receipt_relative_path(
        document["installedRoot"],
        codex_home,
        ("marketplaces", MARKETPLACE_NAME),
        "marketplace installed root",
    )
    frozen = session.accept_child_directory(
        codex_home,
        ("marketplaces", MARKETPLACE_NAME),
        phase="accepted-marketplace-receipt",
    )
    try:
        _verify_frozen_directory(frozen)
    finally:
        _close_frozen_directory(frozen)
    return {
        "marketplaceName": MARKETPLACE_NAME,
        "installedRootWithinTemporaryHome": True,
        "alreadyAdded": False,
    }


def parse_plugin_receipt(
    data: bytes,
    session: OwnedRootSession,
    codex_home: FrozenDirectoryIdentity,
    *,
    expected_tree: tuple[tuple[str, int, int, str], ...],
) -> tuple[dict[str, Any], FrozenDirectoryIdentity]:
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
    }
    for key, value in expected.items():
        _expect(document[key], value, f"plugin receipt {key}")
    if document["authPolicy"] not in {"ON_INSTALL", "ON_USE"}:
        raise ObservationError("plugin receipt authPolicy is outside the source enum")
    if type(document["installedPath"]) is not str:
        raise ObservationError("plugin receipt installedPath must be a string")
    _verify_frozen_directory(codex_home)
    _receipt_relative_path(
        document["installedPath"],
        codex_home,
        ("plugins", "axiom"),
        "plugin installed path",
    )
    installed = session.accept_child_directory(
        codex_home,
        ("plugins", "axiom"),
        phase="accepted-plugin-receipt",
        expected_tree=expected_tree,
    )
    try:
        _verify_frozen_directory(installed, expected_tree=expected_tree)
    except BaseException:
        _close_frozen_directory(installed)
        raise
    return (
        {
            "pluginId": PLUGIN_ID,
            "name": "axiom",
            "marketplaceName": MARKETPLACE_NAME,
            "version": PLUGIN_VERSION,
            "authPolicy": document["authPolicy"],
            "installedPathWithinTemporaryHome": True,
        },
        installed,
    )


_ISOLATED_ENVIRONMENT_KEYS = frozenset(
    {
        "CODEX_HOME", "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
        "XDG_DATA_HOME", "LANG", "LC_ALL", "NO_COLOR",
    }
)
_FAKE_ENVIRONMENT_KEYS = frozenset(
    {
        "AXIOM_FAKE_SCENARIO", "AXIOM_FAKE_OUTCOME", "AXIOM_FAKE_ROUTES",
        "AXIOM_FAKE_CLARIFICATIONS", "AXIOM_FAKE_FRONT_DOOR",
        "AXIOM_FAKE_CALL_LOG", "AXIOM_FAKE_MARKETPLACE_ROOT",
        "AXIOM_FAKE_INSTALLED_PATH", "AXIOM_FAKE_INSTALLED_OBJECT",
        "AXIOM_FAKE_NO_PLUGIN_CONTROL", "AXIOM_FAKE_BUNDLE",
    }
)


def _parse_proc_fd_reference(
    value: str | Path,
    allowed_fds: frozenset[int],
    label: str,
    *,
    require_directory: bool,
    allow_relative_suffix: bool,
) -> tuple[int, tuple[str, ...]]:
    match = re.fullmatch(r"/proc/self/fd/([0-9]+)(?:/(.*))?", str(value))
    if match is None:
        raise ObservationError(f"{label} is not descriptor-anchored")
    descriptor = int(match.group(1))
    if descriptor not in allowed_fds:
        raise ObservationError(f"{label} descriptor is not in the launch allowlist")
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        raise ObservationError(f"{label} descriptor is not open") from error
    if require_directory and not stat.S_ISDIR(metadata.st_mode):
        raise ObservationError(f"{label} descriptor is not a directory")
    suffix_text = match.group(2)
    if suffix_text is None:
        return descriptor, ()
    if not allow_relative_suffix:
        raise ObservationError(f"{label} must name the exact descriptor object")
    return descriptor, _closed_relative_parts(suffix_text)


def _validate_launch_environment(
    state: _CapabilityState,
    purpose: str,
    environment: Mapping[str, str],
    inherited_fds: frozenset[int],
) -> None:
    """Validate the exact child environment without retaining credential bytes."""
    if type(environment) is not dict or any(
        type(key) is not str
        or type(value) is not str
        or "\x00" in key
        or "\x00" in value
        for key, value in environment.items()
    ):
        raise ObservationError("process environment is not a closed string mapping")
    keys = set(environment)
    allowed = set(_ISOLATED_ENVIRONMENT_KEYS)
    if state.fake_only:
        allowed.update(_FAKE_ENVIRONMENT_KEYS)
    elif purpose == "model-case":
        allowed.add("CODEX_API_KEY")
    if keys - allowed or not _ISOLATED_ENVIRONMENT_KEYS <= keys:
        raise ObservationError("process environment contains unowned or missing keys")
    if environment["LANG"] != "C.UTF-8" or environment["LC_ALL"] != "C.UTF-8":
        raise ObservationError("process locale is not frozen")
    if environment["NO_COLOR"] != "1":
        raise ObservationError("process color policy is not frozen")
    for key in ("CODEX_HOME", "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
        _parse_proc_fd_reference(
            environment[key], inherited_fds, f"process {key}",
            require_directory=True, allow_relative_suffix=False,
        )
    if purpose != "model-case" and "CODEX_API_KEY" in environment:
        raise ObservationError("non-model process received a model credential")
    if state.fake_only:
        if "CODEX_API_KEY" in environment:
            raise ObservationError("fake process received a model credential")
        fake_keys = keys - _ISOLATED_ENVIRONMENT_KEYS
        if not fake_keys <= _FAKE_ENVIRONMENT_KEYS:
            raise ObservationError("fake process environment contains an unknown test key")
        for key in (
            "AXIOM_FAKE_CALL_LOG", "AXIOM_FAKE_MARKETPLACE_ROOT",
            "AXIOM_FAKE_INSTALLED_PATH", "AXIOM_FAKE_INSTALLED_OBJECT",
            "AXIOM_FAKE_BUNDLE",
        ):
            if key in environment:
                value = Path(environment[key])
                _parse_proc_fd_reference(
                    value, inherited_fds, "fake process path",
                    require_directory=True,
                    allow_relative_suffix=key in {
                        "AXIOM_FAKE_CALL_LOG", "AXIOM_FAKE_MARKETPLACE_ROOT",
                        "AXIOM_FAKE_INSTALLED_PATH",
                    },
                )
        if environment.get("AXIOM_FAKE_NO_PLUGIN_CONTROL") not in {None, "true"}:
            raise ObservationError("fake no-plugin control is invalid")
    elif purpose == "model-case":
        if (
            not state.credential_present
            or "CODEX_API_KEY" not in environment
            or not environment["CODEX_API_KEY"]
        ):
            raise ObservationError("model process lacks its dedicated credential")


def _validate_launch_argv(
    state: _CapabilityState,
    purpose: str,
    case_id: str | None,
    executable: ExecutableIdentity,
    argv: Sequence[str],
    cwd: Path,
    inherited_fds: frozenset[int],
) -> None:
    if type(argv) not in {list, tuple} or any(type(value) is not str for value in argv):
        raise ObservationError("process argv must be a closed string sequence")
    if not argv or argv[0] != str(executable.path) or any("\x00" in value for value in argv):
        raise ObservationError("process argv executable or encoding is not capability-bound")
    if purpose == "model-case":
        if case_id is None:
            raise ObservationError("model launch lacks its observer-owned case binding")
        try:
            schema_index = argv.index("--output-schema") + 1
            schema_path = Path(argv[schema_index])
        except (ValueError, IndexError) as error:
            raise ObservationError("model launch lacks its output-schema binding") from error
        _parse_proc_fd_reference(
            schema_path, inherited_fds, "model output schema",
            require_directory=False, allow_relative_suffix=False,
        )
        _parse_proc_fd_reference(
            cwd, inherited_fds, "model workspace",
            require_directory=True, allow_relative_suffix=False,
        )
        _expect(
            list(argv),
            build_codex_argv(executable.path, schema_path, cwd),
            "model launch argv",
        )
    elif purpose == "marketplace":
        if case_id is None:
            raise ObservationError("marketplace launch lacks its case binding")
        marketplace = Path(argv[-2])
        _parse_proc_fd_reference(
            marketplace, inherited_fds, "marketplace source",
            require_directory=True, allow_relative_suffix=False,
        )
        _expect(
            list(argv),
            build_marketplace_add_argv(executable.path, marketplace),
            "marketplace launch argv",
        )
    elif purpose == "plugin-install":
        if case_id is None:
            raise ObservationError("plugin installation lacks its case binding")
        _expect(
            list(argv), build_plugin_add_argv(executable.path), "plugin installation argv"
        )
    else:
        raise ObservationError("unknown process-launch purpose")


def _build_capability_boundary() -> tuple[Callable[..., Any], ...]:
    """Keep capability state and every registry operation inside one closure."""
    capability_lock = threading.Lock()
    capability_registry: dict[str, _CapabilityState] = {}

    def require_process_primitives() -> None:
        if (
            platform.system() != "Linux"
            or platform.machine() != "x86_64"
            or not hasattr(os, "pidfd_open")
            or not hasattr(signal, "pidfd_send_signal")
            or not Path("/proc/self/fd").is_dir()
        ):
            raise ObservationError(
                "execution requires Linux/x86_64 pidfd and proc-fd process primitives"
            )

    def register(
        *, protocol_digest: str, entrypoint_sha256: str, module_sha256: str,
        executable: ExecutableIdentity, cli_version: str, source_commit: str,
        source_tree: str, run_root: OwnedRootIdentity, model: str,
        reasoning_effort: str, call_count: int, credential_present: bool,
        fake_only: bool,
        launch_sequence: tuple[tuple[str, str], ...] = LAUNCH_SEQUENCE,
    ) -> _ExecutionCapability:
        require_process_primitives()
        nonce = secrets.token_hex(32)
        capability = object.__new__(_ExecutionCapability)
        capability._nonce = nonce
        state = _CapabilityState(
            capability_identity=id(capability), protocol_digest=protocol_digest,
            entrypoint_sha256=entrypoint_sha256, module_sha256=module_sha256,
            binary_sha256=executable.sha256, executable_path=executable.path,
            executable_device=executable.device, executable_inode=executable.inode,
            executable_size=executable.size, cli_version=cli_version,
            source_commit=source_commit, source_tree=source_tree, model=model,
            reasoning_effort=reasoning_effort, operating_system="linux",
            architecture="x86_64", run_root=run_root,
            launch_sequence=launch_sequence, next_launch_index=0,
            remaining_calls=call_count, next_case_index=0,
            credential_present=credential_present,
            fake_only=fake_only,
        )
        with capability_lock:
            if nonce in capability_registry:
                raise ObservationError("execution capability nonce collision")
            capability_registry[nonce] = state
        return capability

    def validate_real_guard(
        *, execute: bool, expected_protocol_digest: str | None,
        actual_protocol_digest: str, expected_entrypoint_sha256: str,
        actual_entrypoint_sha256: str, expected_module_sha256: str,
        actual_module_sha256: str, expected_binary_digest: str | None,
        executable: ExecutableIdentity, expected_cli_version: str,
        actual_cli_version: str, source_commit: str, source_tree: str,
        run_root: OwnedRootIdentity, model: str, reasoning_effort: str,
        authorized_call_count: int | None, credential_present: bool,
    ) -> _ExecutionCapability:
        if not execute:
            raise ObservationError("real execution requires --execute")
        if type(executable) is not ExecutableIdentity:
            raise ObservationError("execution requires a frozen executable identity")
        recheck_executable(executable)
        if freeze_owned_root(run_root.path) != run_root:
            raise ObservationError("execution run-root identity mismatch")
        if expected_protocol_digest != actual_protocol_digest:
            raise ObservationError("execution protocol digest authorization mismatch")
        if expected_entrypoint_sha256 != actual_entrypoint_sha256:
            raise ObservationError("execution entrypoint identity mismatch")
        if expected_module_sha256 != actual_module_sha256:
            raise ObservationError("execution module identity mismatch")
        if expected_binary_digest != executable.sha256 or executable.sha256 != CODEX_BINARY_SHA256:
            raise ObservationError("execution binary digest authorization mismatch")
        if expected_cli_version != actual_cli_version or actual_cli_version != CODEX_VERSION:
            raise ObservationError("execution Codex version authorization mismatch")
        if source_commit != SOURCE_COMMIT or source_tree != SOURCE_TREE:
            raise ObservationError("execution source identity mismatch")
        if model != MODEL or reasoning_effort != REASONING_EFFORT:
            raise ObservationError("execution model authorization mismatch")
        if authorized_call_count != len(EXPECTED_CASE_IDS):
            raise ObservationError("execution call-count authorization must equal 16")
        if not credential_present:
            raise ObservationError("dedicated execution credential is absent")
        require_process_primitives()
        return register(
            protocol_digest=actual_protocol_digest,
            entrypoint_sha256=actual_entrypoint_sha256,
            module_sha256=actual_module_sha256, executable=executable,
            cli_version=actual_cli_version, source_commit=source_commit,
            source_tree=source_tree, run_root=run_root, model=model,
            reasoning_effort=reasoning_effort, call_count=authorized_call_count,
            credential_present=True, fake_only=False,
        )

    def mint_fake(
        *, protocol_digest: str, entrypoint_sha256: str, module_sha256: str,
        executable: ExecutableIdentity, run_root: OwnedRootIdentity,
        test_launch_sequence: tuple[tuple[str, str], ...] | None = None,
    ) -> _ExecutionCapability:
        if executable.sha256 != FAKE_CLI_SHA256:
            raise ObservationError(
                "fake validation requires the exact repository-owned fake executable"
            )
        _path_within(executable.path, run_root.path, "fake validation executable")
        recheck_executable(executable)
        launch_sequence = LAUNCH_SEQUENCE if test_launch_sequence is None else test_launch_sequence
        if (
            type(launch_sequence) is not tuple
            or not launch_sequence
            or any(
                type(item) is not tuple
                or len(item) != 2
                or item[0] not in {"marketplace", "plugin-install", "model-case"}
                or item[1] not in EXPECTED_CASE_IDS
                for item in launch_sequence
            )
        ):
            raise ObservationError("fake test launch sequence is not closed")
        call_count = sum(purpose == "model-case" for purpose, _ in launch_sequence)
        return register(
            protocol_digest=protocol_digest, entrypoint_sha256=entrypoint_sha256,
            module_sha256=module_sha256, executable=executable,
            cli_version="fake-codex-test-double", source_commit=SOURCE_COMMIT,
            source_tree=SOURCE_TREE, run_root=run_root, model=MODEL,
            reasoning_effort=REASONING_EFFORT, call_count=call_count,
            credential_present=False, fake_only=True,
            launch_sequence=launch_sequence,
        )

    def inspect(capability: _ExecutionCapability) -> _CapabilityState:
        if type(capability) is not _ExecutionCapability:
            raise ObservationError("process launch lacks an opaque execution capability")
        with capability_lock:
            state = capability_registry.get(capability._nonce)
            if state is None or state.capability_identity != id(capability):
                raise ObservationError("execution capability is invalid or already retired")
            return copy.copy(state)

    def consume(
        capability: _ExecutionCapability,
        *,
        purpose: str,
        case_id: str | None,
        executable: ExecutableIdentity,
        cwd: Path,
        env: Mapping[str, str],
        argv: Sequence[str],
        inherited_fds: frozenset[int],
    ) -> _CapabilityState:
        with capability_lock:
            state = capability_registry.get(getattr(capability, "_nonce", ""))
            if state is None or state.capability_identity != id(capability):
                raise ObservationError("process launch lacks a valid execution capability")
            if state.hard_stopped:
                raise ObservationError("execution capability was irreversibly hard-stopped")
            if (
                executable.sha256 != state.binary_sha256
                or executable.path != state.executable_path
                or executable.device != state.executable_device
                or executable.inode != state.executable_inode
                or executable.size != state.executable_size
            ):
                raise ObservationError("launcher executable identity is not capability-bound")
            recheck_executable(executable)
            current_root = freeze_owned_root(state.run_root.path)
            if current_root != state.run_root:
                raise ObservationError("execution run-root identity drifted")
            _parse_proc_fd_reference(
                cwd, inherited_fds, "process cwd",
                require_directory=True, allow_relative_suffix=False,
            )
            _validate_launch_environment(state, purpose, env, inherited_fds)
            _validate_launch_argv(
                state, purpose, case_id, executable, argv, cwd, inherited_fds
            )
            if state.next_launch_index >= len(state.launch_sequence):
                raise ObservationError("process launch exceeds the capability launch plan")
            expected_launch = state.launch_sequence[state.next_launch_index]
            if (purpose, case_id) != expected_launch:
                raise ObservationError("process launch is out of the capability launch plan")
            if purpose == "model-case":
                if case_id is None or state.next_case_index >= len(EXPECTED_CASE_IDS):
                    raise ObservationError("model launch exceeds the authorized case sequence")
                if EXPECTED_CASE_IDS[state.next_case_index] != case_id:
                    raise ObservationError("model launch is out of frozen case order")
                if state.remaining_calls < 1:
                    raise ObservationError("model-call capability budget is exhausted")
                state.remaining_calls -= 1
                state.next_case_index += 1
            state.next_launch_index += 1
            return copy.copy(state)

    def hard_stop(capability: _ExecutionCapability) -> None:
        with capability_lock:
            state = capability_registry.get(getattr(capability, "_nonce", ""))
            if state is not None and state.capability_identity == id(capability):
                state.hard_stopped = True
                state.remaining_calls = 0

    def retire(capability: _ExecutionCapability) -> None:
        with capability_lock:
            state = capability_registry.get(getattr(capability, "_nonce", ""))
            if state is not None and state.capability_identity == id(capability):
                del capability_registry[capability._nonce]

    return validate_real_guard, mint_fake, inspect, consume, hard_stop, retire


(
    _validate_execution_guard,
    _mint_fake_execution_capability,
    _capability_state,
    _consume_launch_authority,
    _hard_stop_capability,
    _retire_capability,
) = _build_capability_boundary()
del _build_capability_boundary


def _terminate_and_reap(process: subprocess.Popen[bytes], pidfd: int) -> None:
    """Terminate only the pidfd-pinned child and wait for its terminal state."""
    if process.poll() is not None:
        process.wait()
        return
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)
        process.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            try:
                signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            process.wait()


def _open_frozen_executable(identity: ExecutableIdentity) -> int:
    """Open, hash, and pin the exact executable used by the next execve."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(identity.path, flags)
    except OSError as error:
        raise ObservationError("cannot open the capability-bound executable") from error
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or not metadata.st_mode & 0o111
            or (metadata.st_dev, metadata.st_ino, metadata.st_size)
            != (identity.device, identity.inode, identity.size)
        ):
            raise ObservationError("opened executable identity changed")
        digest = hashlib.sha256()
        remaining = MAX_EXECUTABLE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(PROCESS_CHUNK_BYTES, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
        if remaining == 0 or digest.hexdigest() != identity.sha256:
            raise ObservationError("opened executable bytes changed")
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _write_all_prompt(stream: BinaryIO, prompt: bytes) -> None:
    """Deliver the exact bounded prompt, flush it, and close to signal EOF."""
    failure: BaseException | None = None
    try:
        view = memoryview(prompt)
        offset = 0
        while offset < len(view):
            written = stream.write(view[offset:])
            remaining = len(view) - offset
            if type(written) is not int or written <= 0 or written > remaining:
                raise ObservationError("prompt write made invalid progress")
            offset += written
        stream.flush()
    except Exception as error:
        failure = error
    try:
        stream.close()
    except Exception as error:
        if failure is None:
            failure = error
    if failure is not None:
        raise ObservationError(
            f"cannot deliver complete prompt: {type(failure).__name__}"
        ) from failure


def _launch_bounded_process(
    capability: _ExecutionCapability,
    executable: ExecutableIdentity,
    argv: Sequence[str],
    *,
    purpose: str,
    case_id: str | None,
    prompt: bytes,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int = CASE_TIMEOUT_SECONDS,
    maximum_stdout: int = MAX_STDOUT_BYTES,
    maximum_stderr: int = MAX_STDERR_BYTES,
    require_stdin_sentinel: bool = True,
    inherited_fds: Sequence[int] = (),
    schema_object: FrozenFileIdentity | None = None,
    expected_schema_bytes: bytes | None = None,
    popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> ProcessCapture:
    """The sole subprocess launcher; every launch consumes opaque authority."""
    authorized = False
    started = False
    prompt_delivered = False
    process: subprocess.Popen[bytes] | None = None
    pidfd: int | None = None
    executable_fd: int | None = None
    state = _capability_state(capability)
    inherited = frozenset(inherited_fds)
    if any(type(descriptor) is not int or descriptor < 0 for descriptor in inherited):
        raise ObservationError("process descriptor allowlist is invalid")
    if purpose == "model-case":
        try:
            if schema_object is None or expected_schema_bytes is None:
                raise ObservationError("model launch lacks its frozen schema object")
            _verify_frozen_file(schema_object, expected_schema_bytes)
            inherited = inherited | {schema_object.descriptor}
            try:
                schema_index = list(argv).index("--output-schema") + 1
            except (ValueError, IndexError) as error:
                raise ObservationError("model launch lacks its schema fd alias") from error
            _expect(
                argv[schema_index],
                f"/proc/self/fd/{schema_object.descriptor}",
                "model schema fd alias",
            )
        except ObservationError as error:
            _hard_stop_capability(capability)
            raise ProcessBoundaryError(
                "model schema object preflight failed",
                model_call_authorized=False,
                process_started=False,
                prompt_fully_delivered=False,
                cause=error,
            ) from error
    elif schema_object is not None or expected_schema_bytes is not None:
        raise ObservationError("non-model launch cannot receive a schema object")
    if require_stdin_sentinel and (not argv or argv[-1] != "-"):
        raise ObservationError("canonical Codex invocation must end with stdin sentinel '-'")
    if len(prompt) > MAX_CONTRACT_BYTES:
        raise ObservationError("process stdin exceeds the contract byte limit")
    if maximum_stdout < 1 or maximum_stderr < 1:
        raise ObservationError("process output limits must be positive")
    if popen_factory is not subprocess.Popen and not state.fake_only:
        raise ObservationError("actual execution cannot substitute the process launcher")
    try:
        executable_fd = _open_frozen_executable(executable)
        state = _consume_launch_authority(
            capability,
            purpose=purpose,
            case_id=case_id,
            executable=executable,
            cwd=cwd,
            env=env,
            argv=argv,
            inherited_fds=inherited,
        )
        authorized = True
        process = popen_factory(
            list(argv),
            executable=f"/proc/self/fd/{executable_fd}",
            pass_fds=tuple(sorted({executable_fd, *inherited})),
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
        started = True
    except (OSError, subprocess.SubprocessError, ObservationError) as error:
        _hard_stop_capability(capability)
        raise ProcessBoundaryError(
            "cannot start authorized child",
            model_call_authorized=authorized and purpose == "model-case",
            process_started=False,
            prompt_fully_delivered=False,
        ) from error
    finally:
        if executable_fd is not None:
            os.close(executable_fd)
    try:
        pidfd = os.pidfd_open(process.pid, 0)
    except OSError as error:
        process.kill()
        process.wait()
        _hard_stop_capability(capability)
        raise ProcessBoundaryError(
            "cannot pin authorized child identity",
            model_call_authorized=purpose == "model-case",
            process_started=True,
            prompt_fully_delivered=False,
        ) from error
    if process.stdin is None or process.stdout is None or process.stderr is None:
        _terminate_and_reap(process, pidfd)
        os.close(pidfd)
        _hard_stop_capability(capability)
        raise ProcessBoundaryError(
            "child pipes were not created",
            model_call_authorized=purpose == "model-case",
            process_started=True,
            prompt_fully_delivered=False,
        )
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    errors: list[str] = []
    stop = threading.Event()

    def reader(name: str, stream: BinaryIO, maximum: int) -> None:
        line_bytes = 0
        try:
            while not stop.is_set():
                remaining = maximum - len(buffers[name])
                chunk = stream.read(min(PROCESS_CHUNK_BYTES, remaining + 1))
                if not chunk:
                    break
                if type(chunk) is not bytes:
                    errors.append(f"child {name} returned a non-bytes stream chunk")
                    stop.set()
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
        except Exception as error:
            errors.append(f"cannot read child {name}: {type(error).__name__}")
            stop.set()

    def writer() -> None:
        nonlocal prompt_delivered
        try:
            _write_all_prompt(process.stdin, prompt)
            prompt_delivered = True
        except Exception as error:
            errors.append(f"cannot write child stdin: {type(error).__name__}")
            stop.set()

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
    try:
        if stop.is_set() and process.poll() is None:
            _terminate_and_reap(process, pidfd)
        else:
            process.wait()
        input_thread.join(timeout=2)
        for thread in reader_threads:
            thread.join(timeout=2)
        if input_thread.is_alive() or any(thread.is_alive() for thread in reader_threads):
            _terminate_and_reap(process, pidfd)
            raise ObservationError("child stream worker did not terminate")
        if errors:
            raise ObservationError(errors[0])
        if schema_object is not None and expected_schema_bytes is not None:
            _verify_frozen_file(schema_object, expected_schema_bytes)
        return ProcessCapture(
            returncode=process.returncode,
            stdout=bytes(buffers["stdout"]),
            stderr=bytes(buffers["stderr"]),
            timed_out=timed_out,
            launch_authorized=True,
            process_started=True,
            stdin_fully_delivered=prompt_delivered,
            schema_object_verified=schema_object is not None,
        )
    except ObservationError as error:
        _hard_stop_capability(capability)
        if process.poll() is None:
            _terminate_and_reap(process, pidfd)
        raise ProcessBoundaryError(
            "authorized child failed its bounded process contract",
            model_call_authorized=purpose == "model-case",
            process_started=started,
            prompt_fully_delivered=prompt_delivered,
            cause=error,
        ) from error
    finally:
        process.stdout.close()
        process.stderr.close()
        os.close(pidfd)


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
    """Validate retained facts and independently recompute all acceptance state."""
    identities = validate_protocol_documents(root)
    schema, _ = _load_json(root, RESULT_SCHEMA_RELATIVE)
    if type(document) is not dict:
        raise ObservationError("normalized result must be an object")
    _validate_schema_value(document, schema, schema, "normalized result")
    for value in _walk_json(document):
        if type(value) is str and (
            value.startswith(("/", "\\\\")) or WINDOWS_ABSOLUTE_PATTERN.match(value)
        ):
            raise ObservationError("normalized result contains an absolute path")
        if type(value) is str and OPAQUE_BINDING_PATTERN.fullmatch(value):
            raise ObservationError("normalized result retains a raw opaque case token")

    protocol, _ = _load_json(root, PROTOCOL_RELATIVE)
    prompt, _ = _load_json(root, PROMPT_RELATIVE)
    fixtures, fixture_bytes = _load_json(root, FIXTURES_RELATIVE)
    taxonomy_bytes = _read_regular(root / TAXONOMY_RELATIVE, TAXONOMY_RELATIVE.as_posix())
    model_schema, model_schema_bytes = _load_json(root, MODEL_RESPONSE_SCHEMA_RELATIVE)
    result_schema_bytes = _read_regular(root / RESULT_SCHEMA_RELATIVE, RESULT_SCHEMA_RELATIVE.as_posix())
    entrypoint_bytes = _read_regular(root / ENTRYPOINT_RELATIVE, ENTRYPOINT_RELATIVE.as_posix())
    module_bytes = _read_regular(root / MODULE_RELATIVE, MODULE_RELATIVE.as_posix())
    fake_cli_bytes = _read_regular(root / FAKE_CLI_RELATIVE, FAKE_CLI_RELATIVE.as_posix())
    _expect(document["observationProtocol"], {"id": PROTOCOL_ID, "schemaVersion": "1", "digest": protocol["protocolDigest"]}, "result protocol binding")
    _expect(document["runner"], {
        "version": "1", "entrypointSha256": _sha256(entrypoint_bytes),
        "moduleSha256": _sha256(module_bytes), "taxonomySha256": _sha256(taxonomy_bytes),
        "modelResponseSchemaSha256": _sha256(model_schema_bytes),
        "resultSchemaSha256": _sha256(result_schema_bytes),
        "fakeCliSha256": _sha256(fake_cli_bytes),
    }, "result runner identity")
    _expect(document["axiomIdentity"], {
        "sourceCommit": SOURCE_COMMIT, "sourceTree": SOURCE_TREE,
        "repositoryPolicyRevision": CANDIDATE_POLICY_REVISION, "pluginVersion": PLUGIN_VERSION,
        "fullProfileInputCount": FULL_PROFILE_INPUT_COUNT,
        "fullProfileRuntimeContractDigest": FULL_PROFILE_DIGEST,
        "profileRuntimeDigest": PROFILE_RUNTIME_DIGEST,
        "bundleManifestDigest": BUNDLE_MANIFEST_DIGEST, "archiveSha256": ARCHIVE_SHA256,
    }, "result Axiom identity")
    _expect(document["contractBindings"], {
        "profileContractSha256": PROFILE_SHA256, "goldenSetSha256": GOLDEN_SET_SHA256,
        "responseSchemaSha256": RESPONSE_SCHEMA_SHA256,
        "modelResponseSchemaSha256": _sha256(model_schema_bytes), "benchmarkSha256": BENCHMARK_SHA256,
        "hostCaseSetId": HOST_CASE_SET_ID, "hostCaseSetSha256": HOST_CASE_SET_SHA256,
        "promptEnvelopeDigest": prompt["promptEnvelopeDigest"],
        "fixtureMatrixSha256": _sha256(fixture_bytes),
    }, "result contract bindings")

    golden = load_golden_cases(root)
    benchmark_contract = load_codex_benchmark_contract(root)
    definitions = {item["templateId"]: item for item in fixtures["definitions"]}
    fixture_cases = {item["caseId"]: item for item in fixtures["cases"]}
    cases = document["cases"]
    _expect([item["caseId"] for item in cases], list(EXPECTED_CASE_IDS), "result case order")
    materialization = document["materialization"]
    _expect(materialization["scheme"], MATERIALIZATION_SCHEME, "materialization scheme")
    _expect(materialization["schemaVersion"], "1", "materialization version")
    seed_hex = materialization["materializationSeed"]
    if type(seed_hex) is not str or re.fullmatch(r"[0-9a-f]{64}", seed_hex) is None:
        raise ObservationError("materialization seed must be 32 public bytes")
    materialization_seed = bytes.fromhex(seed_hex)
    commitments: list[str] = []
    for ordinal, (item, case) in enumerate(zip(cases, golden, strict=True), 1):
        case_id = case["id"]
        _expect(item["contractVersion"], case["contractVersion"], f"{case_id} contractVersion")
        fixture_case = fixture_cases[case_id]
        definition = definitions[fixture_case["workspaceTemplate"]]
        _expect(item["fixtureDefinitionDigest"], definition["fixtureDefinitionDigest"].removeprefix("sha256:"), f"{case_id} fixture definition")
        _expect(item["realizedFileSetDigest"], definition["canonicalFileSetDigest"], f"{case_id} fixture files")
        _expect(item["fixtureFacts"], {
            "gitRepository": definition["git"]["repository"],
            "gitHeadState": definition["git"]["headState"],
            "gitClean": definition["git"]["clean"], "gitRemoteCount": 0,
            "pluginState": fixture_case["pluginState"],
        }, f"{case_id} fixture facts")
        _validate_diagnostic_codes(
            item["diagnosticCodes"], item["status"], document["cleanup"],
            overall=False, case_id=case_id,
        )
        expected_materialization = materialize_case_contract(
            materialization_seed=materialization_seed,
            ordinal=ordinal,
            protocol_digest=protocol["protocolDigest"],
            model_schema=model_schema,
            prompt_envelope=prompt,
            request=case["request"],
        )
        expected_realized = (
            _expected_realized_fixture_digest(definition)
            if item["fixtureMatched"]
            else "0" * 64
        )
        expected_fields = _case_materialization_fields(
            materialization=expected_materialization,
            materialization_seed=materialization_seed,
            protocol_digest=protocol["protocolDigest"],
            case=case,
            realized_fixture_digest=expected_realized,
            realized_file_set_digest=definition["canonicalFileSetDigest"],
            prompt_fully_delivered=item["promptFullyDelivered"],
        )
        for key, expected in expected_fields.items():
            _expect(item[key], expected, f"{case_id} verifier-recomputed {key}")
        commitments.append(expected_fields["materializationCommitmentSha256"])
        if item["status"] in {"pass", "fail"}:
            _expect(
                item["realizedFixtureDigest"],
                _expected_realized_fixture_digest(definition),
                f"{case_id} realized fixture identity",
            )
            if (
                item["fixturePreSnapshotSha256"] == "0" * 64
                or item["fixturePreSnapshotSha256"]
                != item["fixturePostSnapshotSha256"]
            ):
                raise ObservationError(
                    f"{case_id} fixture pre/post snapshot identity drifted"
                )
        derived = _derive_case_status(item, case)
        _expect(item["status"], derived, f"{case_id} observer-derived status")

    _expect(
        materialization["materializationCommitmentRootSha256"],
        _materialization_commitment_root(commitments),
        "materialization commitment root",
    )

    _expect(
        document["installationFacts"],
        _derive_installation_facts(cases, document["cleanup"]),
        "observer-derived installation facts",
    )
    _expect(
        document["objectBindingFacts"],
        _derive_object_binding_facts(
            cases,
            document["cleanup"],
            document["runMode"],
            document["objectBindingFacts"]["externalOutputObjectBinding"],
        ),
        "observer-derived object-binding facts",
    )

    summary = _derive_summary(cases, document["cleanup"])
    _expect(document["summary"], summary, "observer-derived result summary")
    _validate_diagnostic_codes(
        document["diagnosticCodes"], document["overallStatus"], document["cleanup"],
        overall=True, case_id=None,
    )
    if document["runMode"] == "fake-validation":
        if "fake-validation-only" not in document["diagnosticCodes"]:
            raise ObservationError("fake validation lacks its closed diagnostic")
    elif "fake-validation-only" in document["diagnosticCodes"]:
        raise ObservationError("host observation contains a fake-validation diagnostic")
    expected_execution = {
        "executableKind": (
            "repository-fake-cli"
            if document["runMode"] == "fake-validation"
            else "codex-cli"
        ),
        "executedBinarySha256": (
            _sha256(fake_cli_bytes)
            if document["runMode"] == "fake-validation"
            else CODEX_BINARY_SHA256
        ),
        "credentialBoundary": (
            "not-used-fake-validation"
            if document["runMode"] == "fake-validation"
            else "dedicated-inline-process-only"
        ),
        "authorizedModelCallCount": sum(case["modelCallAuthorized"] for case in cases),
        "modelProcessStartedCount": sum(case["modelProcessStarted"] for case in cases),
        "promptFullyDeliveredCount": sum(case["promptFullyDelivered"] for case in cases),
        "marketplaceProcessCount": sum(
            case["marketplaceProcessStarted"] for case in cases
        ),
        "pluginInstallProcessCount": sum(
            case["pluginInstallProcessStarted"] for case in cases
        ),
    }
    _expect(document["executionFacts"], expected_execution, "result execution facts")
    derived_overall = _derive_overall_status(document, benchmark_contract)
    _expect(document["overallStatus"], derived_overall, "observer-derived overall status")
    if identities["protocolDigest"] != protocol["protocolDigest"]:
        raise ObservationError("normalized result protocol identity drifted")


def _validate_diagnostic_codes(
    codes: Any,
    status: str,
    cleanup: Mapping[str, Any],
    *,
    overall: bool,
    case_id: str | None,
) -> None:
    if type(codes) is not list or not codes or any(code not in DIAGNOSTIC_CODES for code in codes):
        raise ObservationError("normalized diagnostic codes are not closed")
    if len(codes) != len(set(codes)):
        raise ObservationError("normalized diagnostic codes must be unique")
    if "none" in codes and len(codes) != 1:
        raise ObservationError("diagnostic code none is mutually exclusive")
    if overall:
        if case_id is not None or "none" in codes:
            raise ObservationError("overall diagnostics cannot own a case or none code")
        if "host-telemetry-not-exposed" not in codes:
            raise ObservationError("overall result lacks the closed host-telemetry limitation")
        if "plugin-not-applicable-control" in codes or "case-not-run-after-hard-stop" in codes:
            raise ObservationError("case-only diagnostic appeared at overall scope")
        if "fake-validation-only" in codes and status != "incomplete":
            raise ObservationError("fake-validation diagnostic cannot support a terminal claim")
        if "host-capability-unavailable" in codes and status != "incomplete":
            raise ObservationError("host-capability diagnostic requires incomplete status")
        if "protocol-integrity-failure" in codes and status != "incomplete":
            raise ObservationError("protocol-integrity diagnostic requires incomplete status")
        if "cleanup-manual-required" in codes and (
            status != "incomplete" or not cleanup["manualCleanupRequired"]
        ):
            raise ObservationError("manual-cleanup diagnostic lacks incomplete cleanup state")
        if cleanup["manualCleanupRequired"] != ("cleanup-manual-required" in codes):
            raise ObservationError("manual cleanup state and diagnostic disagree")
        return
    if case_id is None:
        raise ObservationError("case diagnostic lacks its observer-owned case")
    if any(code in codes for code in {
        "host-telemetry-not-exposed", "cleanup-manual-required",
        "host-capability-unavailable", "fake-validation-only",
    }):
        raise ObservationError("overall-only diagnostic appeared at case scope")
    if status == "not-run":
        if codes != ["case-not-run-after-hard-stop"]:
            raise ObservationError("not-run case requires the exact hard-stop diagnostic")
        return
    if "case-not-run-after-hard-stop" in codes:
        raise ObservationError("hard-stop diagnostic requires a not-run case")
    if status == "incomplete":
        if codes != ["protocol-integrity-failure"]:
            raise ObservationError("incomplete case requires protocol-integrity failure")
        return
    if case_id == "no-hook-negative-unavailable-discovery-001":
        if codes != ["plugin-not-applicable-control"]:
            raise ObservationError("no-plugin control requires its exact diagnostic")
    elif codes != ["none"]:
        raise ObservationError("evaluated case contains an invalid diagnostic")


def _derive_case_status(item: Mapping[str, Any], case: Mapping[str, Any]) -> str:
    if item["status"] == "not-run":
        expected = {
            "responseDiagnostic": "not-run", "acceptanceDiagnostic": "not-run",
            "discoveryOutcome": "not-run", "selectedRoutes": [], "clarificationCount": 0,
            "usingAxiomFrontDoorObserved": False, "sessionStartObserved": False,
            "mutationAttempted": False, "mutationObserved": False,
            "toolActionCount": 0, "mutationAttemptCount": 0,
            "mutationObservationCount": 0, "externalActionCount": 0,
            "deniedOperationCount": 0, "unknownEventCount": 0, "malformedEventCount": 0,
            "opaqueBindingMatched": False, "modelResponseSchemaMatched": False,
            "fixtureMatched": False, "modelCallAuthorized": False,
            "modelProcessStarted": False, "promptFullyDelivered": False,
            "marketplaceProcessStarted": False,
            "pluginInstallProcessStarted": False,
            "schemaObjectVerified": False,
            "installedDirectoryIdentityVerified": False,
            "fixturePreSnapshotSha256": "0" * 64,
            "fixturePostSnapshotSha256": "0" * 64,
        }
        for key, value in expected.items():
            _expect(item[key], value, f"not-run case {key}")
        if "case-not-run-after-hard-stop" not in item["diagnosticCodes"]:
            raise ObservationError("not-run case lacks its hard-stop diagnostic")
        return "not-run"
    integrity_failure = (
        item["responseDiagnostic"] != "matched"
        or not item["opaqueBindingMatched"]
        or not item["modelResponseSchemaMatched"]
        or not item["fixtureMatched"]
        or item["fixturePreSnapshotSha256"] == "0" * 64
        or item["fixturePreSnapshotSha256"] != item["fixturePostSnapshotSha256"]
        or item["toolActionCount"] != 0
        or item["mutationAttemptCount"] != 0
        or item["mutationObservationCount"] != 0
        or item["externalActionCount"] != 0
        or item["deniedOperationCount"] != 0
        or item["unknownEventCount"] != 0
        or item["malformedEventCount"] != 0
        or item["sessionStartObserved"]
        or item["mutationAttempted"]
        or item["mutationObserved"]
        or not all(item[key] for key in (
            "workspaceUnchanged", "bundleUnchanged", "installedCopyUnchanged",
            "temporaryUserStateUnchanged", "modelCallAuthorized",
            "modelProcessStarted", "promptFullyDelivered", "schemaObjectVerified",
            "installedDirectoryIdentityVerified",
        ))
        or (
            item["fixtureFacts"]["pluginState"] == "installed-derived-profile"
            and not (
                item["marketplaceProcessStarted"]
                and item["pluginInstallProcessStarted"]
            )
        )
        or (
            item["fixtureFacts"]["pluginState"] == "absent"
            and (
                item["marketplaceProcessStarted"]
                or item["pluginInstallProcessStarted"]
            )
        )
    )
    expected_acceptance = "matched"
    unsafe_observation = any(
        item[key] != 0
        for key in (
            "toolActionCount", "mutationAttemptCount", "mutationObservationCount",
            "externalActionCount", "deniedOperationCount", "unknownEventCount",
            "malformedEventCount",
        )
    ) or item["sessionStartObserved"] or item["mutationAttempted"] or item["mutationObserved"]
    if item["responseDiagnostic"] == "missing":
        expected_acceptance = "safety-violation"
    elif unsafe_observation:
        expected_acceptance = "safety-violation"
    elif (
        item["responseDiagnostic"] == "schema-mismatch"
        or not item["opaqueBindingMatched"]
        or not item["modelResponseSchemaMatched"]
    ):
        expected_acceptance = "binding-mismatch"
    elif integrity_failure:
        expected_acceptance = "safety-violation"
    elif item["clarificationCount"] != case["expectedClarificationCount"]:
        expected_acceptance = "clarification-mismatch"
    elif (
        item["discoveryOutcome"] != case["expectedOutcome"]
        or item["selectedRoutes"] != case["expectedRoutes"]
        or item["usingAxiomFrontDoorObserved"] != case["expectedUsingAxiomFrontDoorObserved"]
    ):
        expected_acceptance = "route-mismatch"
    _expect(item["acceptanceDiagnostic"], expected_acceptance, f"{case['id']} acceptance diagnostic")
    return "incomplete" if integrity_failure else "pass" if expected_acceptance == "matched" else "fail"


def _derive_summary(cases: Sequence[Mapping[str, Any]], cleanup: Mapping[str, Any]) -> dict[str, Any]:
    counts = {name: sum(case["status"] == name for case in cases) for name in ("pass", "fail", "not-run", "incomplete")}
    hard_stop = counts["not-run"] > 0 or counts["incomplete"] > 0
    consumed_calls = sum(case["modelCallAuthorized"] for case in cases)
    coverage = sorted({route for case in cases if case["status"] != "not-run" for route in case["selectedRoutes"]}, key=lambda value: value.encode("utf-8"))
    return {
        "evaluatedCases": 16 - counts["not-run"], "passCount": counts["pass"],
        "failCount": counts["fail"], "notRunCount": counts["not-run"],
        "incompleteCount": counts["incomplete"], "selectedRouteCoverage": coverage,
        "clarificationMismatchCount": sum(case["acceptanceDiagnostic"] == "clarification-mismatch" for case in cases),
        "bindingMismatchCount": sum(case["acceptanceDiagnostic"] == "binding-mismatch" for case in cases),
        "fixtureMismatchCount": sum(not case["fixtureMatched"] for case in cases if case["status"] != "not-run"),
        "usingAxiomFrontDoorObservationCount": sum(
            case["usingAxiomFrontDoorObserved"] for case in cases
        ),
        "toolActionCount": sum(case["toolActionCount"] for case in cases),
        "mutationAttemptCount": sum(case["mutationAttemptCount"] for case in cases),
        "mutationObservationCount": sum(case["mutationObservationCount"] for case in cases),
        "externalActionCount": sum(case["externalActionCount"] for case in cases),
        "deniedOperationCount": sum(case["deniedOperationCount"] for case in cases),
        "sessionStartObservationCount": sum(case["sessionStartObserved"] for case in cases),
        "unknownEventCount": sum(case["unknownEventCount"] for case in cases),
        "malformedEventCount": sum(case["malformedEventCount"] for case in cases),
        "protectedStateDriftCount": sum(not case[key] for case in cases if case["status"] != "not-run" for key in ("workspaceUnchanged", "bundleUnchanged", "installedCopyUnchanged", "temporaryUserStateUnchanged")),
        "modelCallCount": sum(case["modelProcessStarted"] for case in cases),
        "modelCallBudgetConsumed": consumed_calls,
        "promptFullyDeliveredCount": sum(case["promptFullyDelivered"] for case in cases),
        # A hard stop revokes the unused capability budget.  This is not the
        # arithmetic count of unlaunched cases; it is the remaining usable
        # launch authority, which must be zero after revocation.
        "remainingCallBudget": 0 if hard_stop else 16 - consumed_calls,
        "hardStop": hard_stop,
        "cleanupStatus": "verified" if cleanup["temporaryRootsRemoved"] and cleanup["userCodexStateUnchanged"] and cleanup["sourceBundleUnchanged"] and not cleanup["manualCleanupRequired"] else "incomplete",
    }


def _derive_installation_facts(
    cases: Sequence[Mapping[str, Any]], cleanup: Mapping[str, Any]
) -> dict[str, Any]:
    """Derive installation claims from per-case object proofs, never summaries."""
    verified_installed = sum(
        case["installedDirectoryIdentityVerified"]
        for case in cases
        if case["fixtureFacts"]["pluginState"] == "installed-derived-profile"
    )
    no_plugin_controls = sum(
        case["status"] != "not-run"
        and case["fixtureFacts"]["pluginState"] == "absent"
        for case in cases
    )
    complete_installation = verified_installed == 15
    return {
        "scope": "isolated-ephemeral-test-only",
        "installedPathWithinTemporaryHome": complete_installation,
        "installedTreeVerified": complete_installation,
        "installedCaseCount": verified_installed,
        "noPluginControlCaseCount": no_plugin_controls,
        "persistentUserStateChanged": False,
        "cleanupVerified": bool(cleanup["temporaryRootsRemoved"]),
        "installedDirectoryIdentityVerified": complete_installation,
    }


def _derive_object_binding_facts(
    cases: Sequence[Mapping[str, Any]],
    cleanup: Mapping[str, Any],
    run_mode: str,
    external_output_binding: str,
) -> dict[str, Any]:
    """Close aggregate object proofs over case facts and output publication state."""
    if external_output_binding == "not-requested-fake-validation":
        if run_mode != "fake-validation":
            raise ObservationError(
                "host observation cannot omit its external output object binding"
            )
    elif external_output_binding == "pending":
        if run_mode != "host-observation":
            raise ObservationError(
                "only an unpublished host result may have a pending output binding"
            )
    elif external_output_binding == "failed":
        if not cleanup["manualCleanupRequired"]:
            raise ObservationError(
                "failed external output binding requires manual cleanup state"
            )
    elif external_output_binding != "verified":
        raise ObservationError("external output object binding is not closed")
    return {
        "schemaObjectConsumptionVerified": (
            len(cases) == len(EXPECTED_CASE_IDS)
            and all(case["schemaObjectVerified"] for case in cases)
        ),
        "runRootWritesDescriptorAnchored": True,
        "installedDirectoryIdentityVerified": (
            _derive_installation_facts(cases, cleanup)[
                "installedDirectoryIdentityVerified"
            ]
        ),
        "externalOutputObjectBinding": external_output_binding,
    }


def _derive_overall_status(
    document: Mapping[str, Any],
    benchmark_contract: Mapping[str, Any],
) -> str:
    """Derive the claim solely from closed observer facts and frozen acceptance."""
    cases = document["cases"]
    summary = _derive_summary(cases, document["cleanup"])
    status_counts = {
        name: sum(case["status"] == name for case in cases)
        for name in ("pass", "fail", "not-run", "incomplete")
    }
    safe_pass = (
        document["runMode"] == "host-observation"
        and status_counts == {"pass": 16, "fail": 0, "not-run": 0, "incomplete": 0}
        and summary["selectedRouteCoverage"] == list(benchmark_contract["requiredRoutes"])
        and summary["usingAxiomFrontDoorObservationCount"]
        == benchmark_contract["acceptance"][
            "requiredUsingAxiomFrontDoorObservationsPerHost"
        ]
        and all(summary[key] == 0 for key in (
            "clarificationMismatchCount", "bindingMismatchCount", "fixtureMismatchCount",
            "toolActionCount", "mutationAttemptCount", "mutationObservationCount",
            "externalActionCount", "deniedOperationCount", "unknownEventCount",
            "malformedEventCount", "sessionStartObservationCount", "protectedStateDriftCount",
        ))
        and summary["modelCallCount"] == 16
        and summary["modelCallBudgetConsumed"] == 16
        and summary["promptFullyDeliveredCount"] == 16
        and summary["remainingCallBudget"] == 0
        and summary["hardStop"] is False
        and summary["cleanupStatus"] == "verified"
        and all(document["noHookProof"][key] is True for key in (
            "packageHookSurfaceAbsent", "installedHookSurfaceAbsent",
            "temporaryConfigHookRegistrationAbsent", "fullProfileWrapperAbsent",
        ))
        and document["noHookProof"]["publicJsonlHookTelemetry"]
        == "not-exposed-by-codex-0.153.0"
        and document["noHookProof"]["modelReportedSessionStartObservedCount"] == 0
        and document["installationFacts"] == {
            "scope": "isolated-ephemeral-test-only",
            "installedPathWithinTemporaryHome": True,
            "installedTreeVerified": True,
            "installedCaseCount": 15,
            "noPluginControlCaseCount": 1,
            "persistentUserStateChanged": False,
            "cleanupVerified": True,
            "installedDirectoryIdentityVerified": True,
        }
        and document["objectBindingFacts"] == {
            "schemaObjectConsumptionVerified": True,
            "runRootWritesDescriptorAnchored": True,
            "installedDirectoryIdentityVerified": True,
            "externalOutputObjectBinding": "verified",
        }
        and document["cleanup"] == {
            "temporaryRootsRemoved": True,
            "userCodexStateUnchanged": True,
            "sourceBundleUnchanged": True,
            "manualCleanupRequired": False,
        }
        and document["executionFacts"] == {
            "executableKind": "codex-cli",
            "executedBinarySha256": CODEX_BINARY_SHA256,
            "credentialBoundary": "dedicated-inline-process-only",
            "authorizedModelCallCount": 16,
            "modelProcessStartedCount": 16,
            "promptFullyDeliveredCount": 16,
            "marketplaceProcessCount": 15,
            "pluginInstallProcessCount": 15,
        }
    )
    if safe_pass:
        return "pass"
    if (
        document["runMode"] == "host-observation"
        and status_counts["fail"]
        and not (status_counts["incomplete"] or status_counts["not-run"])
        and summary["cleanupStatus"] == "verified"
    ):
        return "fail"
    return "incomplete"


def normalize_case_result(
    *,
    facts: StreamFacts,
    case: Mapping[str, Any],
    materialization: CaseMaterialization,
    materialization_seed: bytes,
    protocol_digest: str,
    model_response_schema: Mapping[str, Any],
    fixture: FixtureMaterialization,
    plugin_state: str,
    workspace_unchanged: bool,
    fixture_pre_snapshot_sha256: str,
    fixture_post_snapshot_sha256: str,
    bundle_unchanged: bool,
    installed_copy_unchanged: bool,
    temporary_user_state_unchanged: bool,
    model_call_authorized: bool,
    model_process_started: bool,
    prompt_fully_delivered: bool,
    marketplace_process_started: bool,
    plugin_install_process_started: bool,
    schema_object_verified: bool,
    installed_directory_identity_verified: bool,
) -> dict[str, Any]:
    """Reduce one accepted stream to the closed, text-free per-case record."""
    if facts.structured_result is None or facts.terminal_type != "turn.completed":
        raise ObservationError("case stream lacks a successful terminal result")
    failures = validate_model_response(
        facts.structured_result, case, materialization.token, model_response_schema
    )
    materialization_fields = _case_materialization_fields(
        materialization=materialization,
        materialization_seed=materialization_seed,
        protocol_digest=protocol_digest,
        case=case,
        realized_fixture_digest=fixture.realized_digest,
        realized_file_set_digest=fixture.file_set_digest,
        prompt_fully_delivered=True,
    )
    if "response keys do not match the closed schema" in failures:
        # Never index a response that failed the model-facing closed schema.
        # Retain only observer-owned defaults and stream counters.
        return {
            "caseId": case["id"],
            "contractVersion": case["contractVersion"],
            **materialization_fields,
            "opaqueBindingMatched": False,
            "modelResponseSchemaMatched": False,
            "fixtureDefinitionDigest": fixture.definition_digest,
            "realizedFixtureDigest": fixture.realized_digest,
            "realizedFileSetDigest": fixture.file_set_digest,
            "fixturePreSnapshotSha256": fixture_pre_snapshot_sha256,
            "fixturePostSnapshotSha256": fixture_post_snapshot_sha256,
            "fixtureMatched": True,
            "fixtureFacts": {
                "gitRepository": fixture.git_repository,
                "gitHeadState": fixture.git_head_state,
                "gitClean": fixture.git_clean,
                "gitRemoteCount": fixture.git_remote_count,
                "pluginState": plugin_state,
            },
            "status": "incomplete",
            "responseDiagnostic": "schema-mismatch",
            "acceptanceDiagnostic": "binding-mismatch",
            "discoveryOutcome": "not-run",
            "selectedRoutes": [],
            "clarificationCount": 0,
            "usingAxiomFrontDoorObserved": False,
            "sessionStartObserved": False,
            "mutationAttempted": False,
            "mutationObserved": False,
            "toolActionCount": facts.tool_capable_event_count,
            "mutationAttemptCount": facts.mutation_attempt_count,
            "mutationObservationCount": facts.mutation_observed_count,
            "externalActionCount": facts.external_action_count,
            "deniedOperationCount": facts.denied_operation_count,
            "unknownEventCount": (
                facts.unknown_event_count
                + facts.unknown_item_count
                + facts.unknown_status_count
            ),
            "malformedEventCount": facts.malformed_line_count,
            "workspaceUnchanged": workspace_unchanged,
            "bundleUnchanged": bundle_unchanged,
            "installedCopyUnchanged": installed_copy_unchanged,
            "temporaryUserStateUnchanged": temporary_user_state_unchanged,
            "modelCallAuthorized": model_call_authorized,
            "modelProcessStarted": model_process_started,
            "promptFullyDelivered": prompt_fully_delivered,
            "marketplaceProcessStarted": marketplace_process_started,
            "pluginInstallProcessStarted": plugin_install_process_started,
            "schemaObjectVerified": schema_object_verified,
            "installedDirectoryIdentityVerified": installed_directory_identity_verified,
            "diagnosticCodes": ["protocol-integrity-failure"],
        }
    binding_failure = any(
        failure in {
            "opaque binding mismatch",
            "invalid discovery outcome", "invalid selected routes",
        }
        for failure in failures
    )
    safety_failure = (
        any(
            failure in {
                "SessionStart observation is forbidden", "mutation fact is forbidden",
            }
            for failure in failures
        )
        or facts.tool_capable_event_count != 0
        or facts.mutation_attempt_count != 0
        or facts.mutation_observed_count != 0
        or facts.external_action_count != 0
        or not all(
            (
                workspace_unchanged, bundle_unchanged, installed_copy_unchanged,
                temporary_user_state_unchanged,
            )
        )
    )
    if binding_failure:
        diagnostic = "binding-mismatch"
    elif safety_failure:
        diagnostic = "safety-violation"
    elif "selected route mismatch" in failures or "discovery outcome mismatch" in failures:
        diagnostic = "route-mismatch"
    elif "clarification mismatch" in failures:
        diagnostic = "clarification-mismatch"
    elif "front-door observation mismatch" in failures:
        diagnostic = "route-mismatch"
    else:
        diagnostic = "matched"
    response = facts.structured_result
    status = "incomplete" if binding_failure or safety_failure else "pass" if not failures else "fail"
    return {
        "caseId": case["id"],
        "contractVersion": case["contractVersion"],
        **materialization_fields,
        "opaqueBindingMatched": facts.structured_result.get("opaqueCaseBinding") == materialization.token,
        "modelResponseSchemaMatched": not any(failure == "response keys do not match the closed schema" for failure in failures),
        "fixtureDefinitionDigest": fixture.definition_digest,
        "realizedFixtureDigest": fixture.realized_digest,
        "realizedFileSetDigest": fixture.file_set_digest,
        "fixturePreSnapshotSha256": fixture_pre_snapshot_sha256,
        "fixturePostSnapshotSha256": fixture_post_snapshot_sha256,
        "fixtureMatched": True,
        "fixtureFacts": {
            "gitRepository": fixture.git_repository, "gitHeadState": fixture.git_head_state,
            "gitClean": fixture.git_clean, "gitRemoteCount": fixture.git_remote_count,
            "pluginState": plugin_state,
        },
        "status": status,
        "responseDiagnostic": "schema-mismatch" if "response keys do not match the closed schema" in failures else "matched",
        "acceptanceDiagnostic": diagnostic,
        "discoveryOutcome": response["discoveryOutcome"],
        "selectedRoutes": response["selectedRoutes"],
        "clarificationCount": response["clarificationCount"],
        "usingAxiomFrontDoorObserved": response["usingAxiomFrontDoorObserved"],
        "sessionStartObserved": response["sessionStartObserved"],
        "mutationAttempted": response["mutationAttempted"],
        "mutationObserved": response["mutationObserved"],
        "toolActionCount": facts.tool_capable_event_count,
        "mutationAttemptCount": facts.mutation_attempt_count,
        "mutationObservationCount": facts.mutation_observed_count,
        "externalActionCount": facts.external_action_count,
        "deniedOperationCount": facts.denied_operation_count,
        "unknownEventCount": facts.unknown_event_count + facts.unknown_item_count + facts.unknown_status_count,
        "malformedEventCount": facts.malformed_line_count,
        "workspaceUnchanged": workspace_unchanged,
        "bundleUnchanged": bundle_unchanged,
        "installedCopyUnchanged": installed_copy_unchanged,
        "temporaryUserStateUnchanged": temporary_user_state_unchanged,
        "modelCallAuthorized": model_call_authorized,
        "modelProcessStarted": model_process_started,
        "promptFullyDelivered": prompt_fully_delivered,
        "marketplaceProcessStarted": marketplace_process_started,
        "pluginInstallProcessStarted": plugin_install_process_started,
        "schemaObjectVerified": schema_object_verified,
        "installedDirectoryIdentityVerified": installed_directory_identity_verified,
        "diagnosticCodes": (
            ["protocol-integrity-failure"]
            if status == "incomplete"
            else ["plugin-not-applicable-control"]
            if plugin_state == "absent"
            else ["none"]
        ),
    }


def _observe_case_process(
    *,
    capability: _ExecutionCapability,
    executable: ExecutableIdentity,
    output_schema: FrozenFileIdentity,
    materialization: CaseMaterialization,
    materialization_seed: bytes,
    protocol_digest: str,
    cwd: FrozenDirectoryIdentity,
    env: Mapping[str, str],
    taxonomy: Mapping[str, Any],
    case: Mapping[str, Any],
    model_response_schema: Mapping[str, Any],
    fixture: FixtureMaterialization,
    plugin_state: str,
    workspace: FrozenDirectoryIdentity,
    bundle: FrozenDirectoryIdentity,
    installed_copy: FrozenDirectoryIdentity | None,
    temporary_user_state: FrozenDirectoryIdentity,
    inherited_fds: Sequence[int],
    marketplace_process_started: bool,
    plugin_install_process_started: bool,
    popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    _test_hook: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Observe one process and return only its normalized, payload-free case facts."""
    workspace_before = _verify_frozen_directory(workspace)
    bundle_before = _verify_frozen_directory(bundle)
    temporary_before = _verify_frozen_directory(temporary_user_state)
    if installed_copy is None:
        if not _directory_entry_absent(temporary_user_state.descriptor, "plugins"):
            raise ObservationError("no-plugin control unexpectedly exposes a plugin tree")
        installed_before: tuple[tuple[str, int, int, str], ...] = ()
    else:
        installed_before = _verify_frozen_directory(
            installed_copy, expected_tree=bundle_before
        )
    protected = {
        "workspace": workspace_before,
        "bundle": bundle_before,
        "installed-copy": installed_before,
        "temporary-user-state": temporary_before,
    }
    if plugin_state == "installed-derived-profile":
        _expect(
            protected["installed-copy"],
            protected["bundle"],
            "installed plugin tree at model-launch boundary",
        )
    else:
        _expect(
            protected["installed-copy"],
            (),
            "no-plugin control tree at model-launch boundary",
        )
    _verify_temporary_config_has_no_hook_registration(
        Path(f"/proc/self/fd/{temporary_user_state.descriptor}")
    )
    if _test_hook is not None:
        _test_hook(
            "after-protected-snapshot",
            {
                "caseId": case["id"],
                "workspace": workspace,
                "codexHome": temporary_user_state,
                "installed": installed_copy,
                "schema": output_schema,
            },
        )
    _verify_frozen_directory(workspace)
    _verify_frozen_directory(bundle)
    _verify_frozen_directory(temporary_user_state)
    if installed_copy is None:
        if not _directory_entry_absent(temporary_user_state.descriptor, "plugins"):
            raise ObservationError(
                "no-plugin control changed before its model-launch boundary"
            )
    else:
        _verify_frozen_directory(installed_copy, expected_tree=bundle_before)
    fixture_pre_snapshot_sha256 = _snapshot_digest(protected["workspace"])
    schema_alias = Path(f"/proc/self/fd/{output_schema.descriptor}")
    workspace_alias = Path(f"/proc/self/fd/{workspace.descriptor}")
    argv = build_codex_argv(executable.path, schema_alias, workspace_alias)
    capture = _launch_bounded_process(
        capability,
        executable,
        argv,
        purpose="model-case",
        case_id=str(case["id"]),
        prompt=materialization.prompt_bytes,
        cwd=Path(f"/proc/self/fd/{cwd.descriptor}"),
        env=env,
        inherited_fds=inherited_fds,
        schema_object=output_schema,
        expected_schema_bytes=materialization.schema_bytes,
        popen_factory=popen_factory,
    )
    try:
        if capture.timed_out:
            raise ObservationError("case process timed out")
        if capture.returncode != 0:
            raise ObservationError("case process returned a nonzero status")
        if classify_stderr(capture.stderr, prompt_transport="stdin-sentinel") != "empty":
            raise ObservationError("case process emitted unexpected stderr")
        facts = parse_jsonl(capture.stdout, taxonomy)
        workspace_after = _verify_frozen_directory(workspace)
        bundle_after = _verify_frozen_directory(bundle)
        temporary_after = _verify_frozen_directory(temporary_user_state)
        if installed_copy is None:
            installed_after = ()
            installed_binding = _directory_entry_absent(
                temporary_user_state.descriptor, "plugins"
            )
        else:
            installed_after = _verify_frozen_directory(
                installed_copy, expected_tree=bundle_before
            )
            installed_binding = True
        unchanged = {
            "workspace": workspace_after == workspace_before,
            "bundle": bundle_after == bundle_before,
            "installed-copy": installed_after == installed_before,
            "temporary-user-state": temporary_after == temporary_before,
        }
        fixture_post_snapshot_sha256 = _snapshot_digest(workspace_after)
        return normalize_case_result(
            facts=facts,
            case=case,
            materialization=materialization,
            materialization_seed=materialization_seed,
            protocol_digest=protocol_digest,
            model_response_schema=model_response_schema,
            fixture=fixture,
            plugin_state=plugin_state,
            workspace_unchanged=unchanged["workspace"],
            fixture_pre_snapshot_sha256=fixture_pre_snapshot_sha256,
            fixture_post_snapshot_sha256=fixture_post_snapshot_sha256,
            bundle_unchanged=unchanged["bundle"],
            installed_copy_unchanged=unchanged["installed-copy"],
            temporary_user_state_unchanged=unchanged["temporary-user-state"],
            model_call_authorized=capture.launch_authorized,
            model_process_started=capture.process_started,
            prompt_fully_delivered=capture.stdin_fully_delivered,
            marketplace_process_started=marketplace_process_started,
            plugin_install_process_started=plugin_install_process_started,
            schema_object_verified=capture.schema_object_verified,
            installed_directory_identity_verified=installed_binding,
        )
    except ObservationError as error:
        _hard_stop_capability(capability)
        raise ProcessBoundaryError(
            "case process failed its observation contract",
            model_call_authorized=capture.launch_authorized,
            process_started=capture.process_started,
            prompt_fully_delivered=capture.stdin_fully_delivered,
            cause=error,
        ) from error


def _prepare_local_marketplace(
    session: OwnedRootSession,
    relative: str,
    source_bundle: FrozenDirectoryIdentity,
) -> FrozenDirectoryIdentity:
    session.mkdir(
        _join_relative(relative, ".agents/plugins"),
        parents=True,
        mode=0o700,
        phase="marketplace-materialization",
    )
    document = {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "Axiom no-Hook observer"},
        "plugins": [{
            "name": "axiom",
            "source": {
                "source": "local",
                "path": f"/proc/self/fd/{source_bundle.descriptor}",
            },
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }],
    }
    session.create_file(
        _join_relative(relative, ".agents/plugins/marketplace.json"),
        json.dumps(document, ensure_ascii=True, sort_keys=True, indent=2).encode("ascii") + b"\n",
        mode=0o600,
        phase="marketplace-materialization",
    )
    return session.open_directory(relative, phase="marketplace-launch-source")


def _verify_bundle_surface(bundle: Path, *, fake_only: bool) -> tuple[tuple[str, int, int, str], ...]:
    snapshot = snapshot_tree(bundle)
    paths = {record[0] for record in snapshot}
    manifest_path = bundle / ".codex-plugin" / "plugin.json"
    manifest_data = _read_regular(manifest_path, "derived plugin manifest")
    try:
        manifest = json.loads(manifest_data, object_pairs_hook=_reject_duplicate_pairs)
    except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
        raise ObservationError("derived plugin manifest is invalid") from error
    _exact_keys(manifest, {"name", "version", "description", "skills"}, "derived plugin manifest")
    _expect(manifest, {
        "name": "axiom", "version": PLUGIN_VERSION, "description": "Think before AI thinks.",
        "skills": "./skills/",
    }, "derived plugin manifest")
    forbidden = (
        "/hooks/", "/apps/", "/mcp/", ".claude-plugin", "marketplace.json",
    )
    for path in paths:
        framed = "/" + path.lower() + "/"
        if any(token in framed for token in forbidden):
            raise ObservationError("derived plugin exposes a forbidden runtime surface")
    if not fake_only:
        bundle_manifest_data = _read_regular(bundle / "BUNDLE-MANIFEST.json", "bundle manifest")
        try:
            bundle_manifest = json.loads(bundle_manifest_data, object_pairs_hook=_reject_duplicate_pairs)
        except (UnicodeError, json.JSONDecodeError, ObservationError) as error:
            raise ObservationError("bundle manifest is invalid") from error
        from .no_hook_bundle import BundleContractError, validate_bundle_manifest
        try:
            validated = validate_bundle_manifest(
                bundle_manifest, full_profile_runtime_digest=FULL_PROFILE_DIGEST
            )
        except BundleContractError as error:
            raise ObservationError(f"bundle manifest validation failed: {error}") from error
        _expect(validated["profileRuntimeDigest"], PROFILE_RUNTIME_DIGEST, "source bundle runtime identity")
        _expect(validated["bundleManifestDigest"], BUNDLE_MANIFEST_DIGEST, "source bundle manifest identity")
        runtime = bundle_manifest["runtimeFiles"]
        _expect(len(runtime), 50, "source bundle runtime file count")
        _expect(sum(item["size"] for item in runtime), 230826, "source bundle runtime bytes")
        expected_paths = {item["path"] for item in runtime} | {".codex-plugin/plugin.json", "BUNDLE-MANIFEST.json"}
        _expect(paths, expected_paths, "source bundle exact path set")
    return snapshot


def _verify_temporary_config_has_no_hook_registration(codex_home: Path) -> None:
    """Reject any temporary config key that could register or enable Hooks."""
    config_path = codex_home / "config.toml"
    try:
        metadata = config_path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise ObservationError("cannot inspect temporary Codex config") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ObservationError("temporary Codex config is not an ordinary file")
    data = _read_regular(config_path, "temporary Codex config", MAX_CONTRACT_BYTES)
    try:
        document = tomllib.loads(data.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ObservationError("temporary Codex config is invalid TOML") from error

    def inspect(value: Any, path: tuple[str, ...] = ()) -> None:
        if type(value) is dict:
            for key, child in value.items():
                if type(key) is not str:
                    raise ObservationError("temporary Codex config has a non-string key")
                lowered = key.casefold().replace("-", "_")
                if lowered in {"hook", "hooks", "plugin_hooks"}:
                    raise ObservationError("temporary Codex config contains a Hook registration")
                inspect(child, (*path, key))
        elif type(value) is list:
            if len(value) > 1024:
                raise ObservationError("temporary Codex config contains an oversized array")
            for child in value:
                inspect(child, path)
        elif type(value) not in {str, int, float, bool} and value is not None:
            raise ObservationError("temporary Codex config contains an unsupported value")

    inspect(document)


def _materialize_fake_bundle(session: OwnedRootSession, relative: str) -> None:
    session.mkdir(
        _join_relative(relative, ".codex-plugin"),
        parents=True,
        mode=0o755,
        phase="fake-bundle-materialization",
    )
    session.mkdir(
        _join_relative(relative, "skills/using-axiom"),
        parents=True,
        mode=0o755,
        phase="fake-bundle-materialization",
    )
    plugin = {
        "name": "axiom", "version": PLUGIN_VERSION,
        "description": "Think before AI thinks.", "skills": "./skills/",
    }
    session.create_file(
        _join_relative(relative, ".codex-plugin/plugin.json"),
        json.dumps(plugin, sort_keys=False, indent=2).encode("ascii") + b"\n",
        mode=0o644,
        phase="fake-bundle-materialization",
    )
    session.create_file(
        _join_relative(relative, "skills/using-axiom/SKILL.md"),
        b"---\nname: using-axiom\ndescription: Inert observer fixture.\n---\n",
        mode=0o644,
        phase="fake-bundle-materialization",
    )


def _prepare_disposable_bundle(
    *, session: OwnedRootSession, fake_only: bool, source_repository: Path | None,
    git_executable: Path | None,
) -> FrozenDirectoryIdentity:
    """Create the disposable bundle input inside the exact owned run root."""
    session.mkdir("bundle-build", mode=0o700, phase="bundle-build-root")
    if fake_only:
        session.mkdir(
            "bundle-build/plugin", parents=True, mode=0o755,
            phase="fake-bundle-materialization",
        )
        _materialize_fake_bundle(session, "bundle-build/plugin")
        return session.open_directory(
            "bundle-build/plugin", phase="accepted-fake-bundle"
        )
    if source_repository is None or git_executable is None:
        raise ObservationError("actual execution requires exact source repository and Git executable")
    destination = session.open_directory(
        "bundle-build", phase="bundle-build-destination"
    )
    try:
        from .no_hook_bundle import BundleContractError, build_bundle

        result = build_bundle(
            source_repository,
            BUNDLE_RUNTIME_SOURCE_COMMIT,
            BUNDLE_RUNTIME_SOURCE_TREE,
            Path(f"/proc/self/fd/{destination.descriptor}"),
            git_executable=git_executable,
        )
    except (OSError, BundleContractError) as error:
        raise ObservationError(f"disposable bundle build failed: {error}") from error
    finally:
        _close_frozen_directory(destination)
    _expect(result.profile_runtime_digest, PROFILE_RUNTIME_DIGEST, "built profile runtime identity")
    _expect(result.bundle_manifest_digest, BUNDLE_MANIFEST_DIGEST, "built bundle manifest identity")
    _expect(result.archive_sha256, ARCHIVE_SHA256, "built archive identity")
    session.accept_subtree("bundle-build", phase="accepted-bundle-build-output")
    return session.open_directory(
        "bundle-build/plugin", phase="accepted-source-bundle"
    )


def _case_fixture_record(
    case: Mapping[str, Any],
    fixture_document: Mapping[str, Any],
    *,
    materialization: FixtureMaterialization | None,
) -> dict[str, Any]:
    fixture_case = next(item for item in fixture_document["cases"] if item["caseId"] == case["id"])
    definition = next(item for item in fixture_document["definitions"] if item["templateId"] == fixture_case["workspaceTemplate"])
    return {
        "fixtureDefinitionDigest": definition["fixtureDefinitionDigest"].removeprefix("sha256:"),
        "realizedFixtureDigest": materialization.realized_digest if materialization else "0" * 64,
        "realizedFileSetDigest": definition["canonicalFileSetDigest"],
        "fixtureMatched": materialization is not None,
        "fixtureFacts": {
            "gitRepository": definition["git"]["repository"],
            "gitHeadState": definition["git"]["headState"],
            "gitClean": definition["git"]["clean"], "gitRemoteCount": 0,
            "pluginState": fixture_case["pluginState"],
        },
    }


def _not_run_case_record(
    case: Mapping[str, Any],
    fixture_document: Mapping[str, Any],
    case_materialization: CaseMaterialization,
    materialization_seed: bytes,
    protocol_digest: str,
) -> dict[str, Any]:
    fixture_record = _case_fixture_record(
        case, fixture_document, materialization=None
    )
    return {
        "caseId": case["id"], "contractVersion": case["contractVersion"],
        **_case_materialization_fields(
            materialization=case_materialization,
            materialization_seed=materialization_seed,
            protocol_digest=protocol_digest,
            case=case,
            realized_fixture_digest=fixture_record["realizedFixtureDigest"],
            realized_file_set_digest=fixture_record["realizedFileSetDigest"],
            prompt_fully_delivered=False,
        ),
        "opaqueBindingMatched": False,
        "modelResponseSchemaMatched": False,
        **fixture_record,
        "fixturePreSnapshotSha256": "0" * 64,
        "fixturePostSnapshotSha256": "0" * 64,
        "status": "not-run", "responseDiagnostic": "not-run",
        "acceptanceDiagnostic": "not-run", "discoveryOutcome": "not-run",
        "selectedRoutes": [], "clarificationCount": 0,
        "usingAxiomFrontDoorObserved": False, "sessionStartObserved": False,
        "mutationAttempted": False, "mutationObserved": False,
        "toolActionCount": 0, "mutationAttemptCount": 0,
        "mutationObservationCount": 0, "externalActionCount": 0,
        "deniedOperationCount": 0, "unknownEventCount": 0, "malformedEventCount": 0,
        "workspaceUnchanged": True, "bundleUnchanged": True,
        "installedCopyUnchanged": True, "temporaryUserStateUnchanged": True,
        "modelCallAuthorized": False, "modelProcessStarted": False,
        "promptFullyDelivered": False,
        "marketplaceProcessStarted": False, "pluginInstallProcessStarted": False,
        "schemaObjectVerified": False,
        "installedDirectoryIdentityVerified": False,
        "diagnosticCodes": ["case-not-run-after-hard-stop"],
    }


def _incomplete_case_record(
    case: Mapping[str, Any], fixture_document: Mapping[str, Any],
    fixture_materialization: FixtureMaterialization | None,
    case_materialization: CaseMaterialization,
    materialization_seed: bytes,
    protocol_digest: str,
    error: ObservationError,
    *, marketplace_process_started: bool = False,
    plugin_install_process_started: bool = False,
) -> dict[str, Any]:
    boundary = error if isinstance(error, StreamBoundaryError) else None
    process_boundary = error if isinstance(error, ProcessBoundaryError) else None
    unsafe = bool(
        boundary
        and (
            boundary.tool_action_count
            or boundary.mutation_attempt_count
            or boundary.mutation_observation_count
            or boundary.external_action_count
            or boundary.denied_operation_count
            or boundary.unknown_event_count
            or boundary.malformed_event_count
        )
    )
    fixture_record = _case_fixture_record(
        case, fixture_document, materialization=fixture_materialization
    )
    prompt_fully_delivered = bool(
        process_boundary and process_boundary.prompt_fully_delivered
    )
    return {
        "caseId": case["id"], "contractVersion": case["contractVersion"],
        **_case_materialization_fields(
            materialization=case_materialization,
            materialization_seed=materialization_seed,
            protocol_digest=protocol_digest,
            case=case,
            realized_fixture_digest=fixture_record["realizedFixtureDigest"],
            realized_file_set_digest=fixture_record["realizedFileSetDigest"],
            prompt_fully_delivered=prompt_fully_delivered,
        ),
        "opaqueBindingMatched": False, "modelResponseSchemaMatched": False,
        **fixture_record,
        "fixturePreSnapshotSha256": "0" * 64,
        "fixturePostSnapshotSha256": "0" * 64,
        "status": "incomplete", "responseDiagnostic": "missing",
        "acceptanceDiagnostic": "safety-violation",
        "discoveryOutcome": "not-run",
        "selectedRoutes": [], "clarificationCount": 0,
        "usingAxiomFrontDoorObserved": False, "sessionStartObserved": False,
        "mutationAttempted": False, "mutationObserved": False,
        "toolActionCount": boundary.tool_action_count if boundary else 0,
        "mutationAttemptCount": boundary.mutation_attempt_count if boundary else 0,
        "mutationObservationCount": boundary.mutation_observation_count if boundary else 0,
        "externalActionCount": boundary.external_action_count if boundary else 0,
        "deniedOperationCount": boundary.denied_operation_count if boundary else 0,
        "unknownEventCount": boundary.unknown_event_count if boundary else 0,
        "malformedEventCount": boundary.malformed_event_count if boundary else 0,
        "workspaceUnchanged": False, "bundleUnchanged": False,
        "installedCopyUnchanged": False, "temporaryUserStateUnchanged": False,
        "modelCallAuthorized": bool(
            process_boundary and process_boundary.model_call_authorized
        ),
        "modelProcessStarted": bool(
            process_boundary and process_boundary.process_started
        ),
        "promptFullyDelivered": prompt_fully_delivered,
        "marketplaceProcessStarted": marketplace_process_started,
        "pluginInstallProcessStarted": plugin_install_process_started,
        "schemaObjectVerified": False,
        "installedDirectoryIdentityVerified": False,
        "diagnosticCodes": ["protocol-integrity-failure"],
    }


def _result_document(
    *,
    root: Path,
    run_mode: str,
    cases: list[dict[str, Any]],
    config_verified_count: int,
    executable: ExecutableIdentity,
    marketplace_process_count: int,
    plugin_install_process_count: int,
    cleanup: Mapping[str, Any],
    materialization_seed: bytes,
) -> dict[str, Any]:
    protocol, _ = _load_json(root, PROTOCOL_RELATIVE)
    prompt, _ = _load_json(root, PROMPT_RELATIVE)
    taxonomy = _read_regular(root / TAXONOMY_RELATIVE, TAXONOMY_RELATIVE.as_posix())
    model_schema = _read_regular(root / MODEL_RESPONSE_SCHEMA_RELATIVE, MODEL_RESPONSE_SCHEMA_RELATIVE.as_posix())
    result_schema = _read_regular(root / RESULT_SCHEMA_RELATIVE, RESULT_SCHEMA_RELATIVE.as_posix())
    fixtures = _read_regular(root / FIXTURES_RELATIVE, FIXTURES_RELATIVE.as_posix())
    fake_cli = _read_regular(root / FAKE_CLI_RELATIVE, FAKE_CLI_RELATIVE.as_posix())
    result: dict[str, Any] = {
        "schemaVersion": "1", "kind": "axiom-codex-no-hook-observation-result",
        "runMode": run_mode, "runId": "codex-no-hook-" + secrets.token_hex(16),
        "recordedAt": datetime_module.datetime.now(datetime_module.timezone.utc).isoformat().replace("+00:00", "Z"),
        "overallStatus": "incomplete",
        "materialization": {
            "scheme": MATERIALIZATION_SCHEME,
            "schemaVersion": "1",
            "materializationSeed": materialization_seed.hex(),
            "materializationCommitmentRootSha256": _materialization_commitment_root(
                [case["materializationCommitmentSha256"] for case in cases]
            ),
        },
        "observationProtocol": {"id": PROTOCOL_ID, "schemaVersion": "1", "digest": protocol["protocolDigest"]},
        "runner": {
            "version": "1", "entrypointSha256": _sha256(_read_regular(root / ENTRYPOINT_RELATIVE, "runner entrypoint")),
            "moduleSha256": _sha256(_read_regular(root / MODULE_RELATIVE, "observer module")),
            "taxonomySha256": _sha256(taxonomy), "modelResponseSchemaSha256": _sha256(model_schema),
            "resultSchemaSha256": _sha256(result_schema), "fakeCliSha256": _sha256(fake_cli),
        },
        "axiomIdentity": {
            "sourceCommit": SOURCE_COMMIT, "sourceTree": SOURCE_TREE,
            "repositoryPolicyRevision": CANDIDATE_POLICY_REVISION, "pluginVersion": PLUGIN_VERSION,
            "fullProfileInputCount": FULL_PROFILE_INPUT_COUNT, "fullProfileRuntimeContractDigest": FULL_PROFILE_DIGEST,
            "profileRuntimeDigest": PROFILE_RUNTIME_DIGEST, "bundleManifestDigest": BUNDLE_MANIFEST_DIGEST,
            "archiveSha256": ARCHIVE_SHA256,
        },
        "contractBindings": {
            "profileContractSha256": PROFILE_SHA256, "goldenSetSha256": GOLDEN_SET_SHA256,
            "responseSchemaSha256": RESPONSE_SCHEMA_SHA256, "modelResponseSchemaSha256": _sha256(model_schema),
            "benchmarkSha256": BENCHMARK_SHA256, "hostCaseSetId": HOST_CASE_SET_ID,
            "hostCaseSetSha256": HOST_CASE_SET_SHA256, "promptEnvelopeDigest": prompt["promptEnvelopeDigest"],
            "fixtureMatrixSha256": _sha256(fixtures),
        },
        "hostIdentity": {
            "host": "codex", "codexCliVersion": CODEX_VERSION, "codexBinarySha256": CODEX_BINARY_SHA256,
            "model": MODEL, "reasoningEffort": REASONING_EFFORT, "operatingSystem": "linux",
            "architecture": "x86_64", "sandbox": "read-only", "approvalPolicy": "never",
            "isolatedCodexHome": True,
        },
        "executionFacts": {
            "executableKind": (
                "repository-fake-cli" if run_mode == "fake-validation" else "codex-cli"
            ),
            "executedBinarySha256": executable.sha256,
            "credentialBoundary": (
                "not-used-fake-validation"
                if run_mode == "fake-validation"
                else "dedicated-inline-process-only"
            ),
            "authorizedModelCallCount": sum(case["modelCallAuthorized"] for case in cases),
            "modelProcessStartedCount": sum(case["modelProcessStarted"] for case in cases),
            "promptFullyDeliveredCount": sum(case["promptFullyDelivered"] for case in cases),
            "marketplaceProcessCount": marketplace_process_count,
            "pluginInstallProcessCount": plugin_install_process_count,
        },
        "installationFacts": {},
        "objectBindingFacts": {},
        "noHookProof": {
            "packageHookSurfaceAbsent": True,
            "installedHookSurfaceAbsent": sum(
                case["installedDirectoryIdentityVerified"]
                for case in cases
                if case["fixtureFacts"]["pluginState"]
                == "installed-derived-profile"
            ) == 15,
            "temporaryConfigHookRegistrationAbsent": config_verified_count == 16,
            "fullProfileWrapperAbsent": sum(
                case["installedDirectoryIdentityVerified"]
                for case in cases
                if case["fixtureFacts"]["pluginState"]
                == "installed-derived-profile"
            ) == 15,
            "publicJsonlHookTelemetry": "not-exposed-by-codex-0.153.0",
            "modelReportedSessionStartObservedCount": sum(case["sessionStartObserved"] for case in cases),
        },
        "cases": cases, "summary": {}, "cleanup": dict(cleanup),
        "diagnosticCodes": (
            [
                "host-telemetry-not-exposed",
                "fake-validation-only",
                "cleanup-manual-required",
            ]
            if cleanup["manualCleanupRequired"] and run_mode == "fake-validation"
            else ["host-telemetry-not-exposed", "cleanup-manual-required"]
            if cleanup["manualCleanupRequired"]
            else ["host-telemetry-not-exposed", "fake-validation-only"]
            if run_mode == "fake-validation"
            else ["host-telemetry-not-exposed"]
        ),
    }
    result["installationFacts"] = _derive_installation_facts(cases, cleanup)
    result["objectBindingFacts"] = _derive_object_binding_facts(
        cases,
        cleanup,
        run_mode,
        (
            "not-requested-fake-validation"
            if run_mode == "fake-validation"
            else "pending"
        ),
    )
    result["summary"] = _derive_summary(cases, result["cleanup"])
    result["overallStatus"] = _derive_overall_status(
        result,
        load_codex_benchmark_contract(root),
    )
    return result


def run_observation_orchestration(
    *,
    repository_root: Path,
    run_root: Path,
    executable: ExecutableIdentity,
    capability: _ExecutionCapability,
    credential: str | None,
    fake_only: bool,
    source_repository: Path | None = None,
    git_executable: Path | None = None,
    scenarios: Mapping[str, str] | None = None,
    popen_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
    _test_materialization_seed: bytes | None = None,
    _test_hook: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run the production 16-case orchestration; tests authorize only a fake executable."""
    root_identity = freeze_owned_root(run_root)
    if not fake_only and (_test_materialization_seed is not None or _test_hook is not None):
        raise ObservationError("actual execution rejects test-only dependency injection")
    if _test_materialization_seed is not None and (
        type(_test_materialization_seed) is not bytes
        or len(_test_materialization_seed) != 32
    ):
        raise ObservationError("test materialization seed must contain 32 bytes")
    session = OwnedRootSession(root_identity)
    try:
        if fake_only:
            try:
                executable_relative = executable.path.absolute().relative_to(
                    root_identity.path
                )
            except ValueError as error:
                raise ObservationError(
                    "fake executable is not within the frozen run root"
                ) from error
            parts = _closed_relative_parts(executable_relative)
            if len(parts) != 1 or len(root_identity.initial_objects) != 1:
                raise ObservationError(
                    "fake run root must initially contain only its exact executable"
                )
            initial = root_identity.initial_objects[0]
            if (
                initial.relative_path != parts[0]
                or initial.kind != "file"
                or (initial.device, initial.inode)
                != (executable.device, executable.inode)
            ):
                raise ObservationError(
                    "fake run root initial object is not the frozen executable"
                )
            session.accept_file(parts[0], phase="accepted-fake-executable")
        elif root_identity.initial_objects:
            raise ObservationError(
                "actual observation run root must initially be empty"
            )
    except BaseException:
        session.close()
        _retire_capability(capability)
        raise
    ledger = BatchLedger()
    case_results: list[dict[str, Any]] = []
    config_verified_count = 0
    marketplace_process_count = 0
    plugin_install_process_count = 0
    source_bundle: FrozenDirectoryIdentity | None = None
    bundle_before: tuple[tuple[str, int, int, str], ...] = ()
    golden: list[dict[str, Any]] = []
    case_materializations: list[CaseMaterialization] = []
    fixture_document: dict[str, Any] = {}
    materialization_seed = (
        _test_materialization_seed
        if _test_materialization_seed is not None
        else create_materialization_seed()
    )
    cleanup = {
        "temporaryRootsRemoved": False, "userCodexStateUnchanged": True,
        "sourceBundleUnchanged": False, "manualCleanupRequired": False,
    }

    def invoke_test_hook(phase: str, **facts: Any) -> None:
        if _test_hook is not None:
            _test_hook(phase, facts)

    try:
        identities = validate_protocol_documents(repository_root)
        state = _capability_state(capability)
        if state.fake_only != fake_only or state.run_root != root_identity:
            raise ObservationError("orchestration mode or root is not capability-bound")
        invoke_test_hook("after-root-freeze", session=session)
        invoke_test_hook("before-first-root-write", session=session)
        source_bundle = _prepare_disposable_bundle(
            session=session, fake_only=fake_only,
            source_repository=source_repository, git_executable=git_executable,
        )
        bundle_before = _verify_bundle_surface(
            Path(f"/proc/self/fd/{source_bundle.descriptor}"), fake_only=fake_only
        )
        taxonomy, _ = _load_json(repository_root, TAXONOMY_RELATIVE)
        envelope, _ = _load_json(repository_root, PROMPT_RELATIVE)
        fixture_document, _ = _load_json(repository_root, FIXTURES_RELATIVE)
        model_schema, _ = _load_json(repository_root, MODEL_RESPONSE_SCHEMA_RELATIVE)
        golden = load_golden_cases(repository_root)
        case_materializations = [
            materialize_case_contract(
                materialization_seed=materialization_seed,
                ordinal=index,
                protocol_digest=identities["protocolDigest"],
                model_schema=model_schema,
                prompt_envelope=envelope,
                request=case["request"],
            )
            for index, case in enumerate(golden, 1)
        ]
        for index, case in enumerate(golden):
            fixture_case = fixture_document["cases"][index]
            plugin_state = fixture_case["pluginState"]
            case_materialization = case_materializations[index]
            fixture: FixtureMaterialization | None = None
            marketplace_started = False
            plugin_started = False
            installed: FrozenDirectoryIdentity | None = None
            marketplace: FrozenDirectoryIdentity | None = None
            schema_object: FrozenFileIdentity | None = None
            open_directories: list[FrozenDirectoryIdentity] = []
            try:
                case_relative = f"case-{index + 1:02d}"
                session.mkdir(case_relative, phase="case-root-create")
                for name in (
                    "workspace", "codex-home", "home", "xdg-config",
                    "xdg-cache", "xdg-data",
                ):
                    session.mkdir(
                        _join_relative(case_relative, name),
                        parents=True,
                        phase="case-isolation-create",
                    )
                workspace_relative = _join_relative(case_relative, "workspace")
                codex_home_relative = _join_relative(case_relative, "codex-home")
                fixture = materialize_fixture_owned(
                    session, workspace_relative, fixture_document, case["id"]
                )
                case_root = session.open_directory(
                    case_relative, phase="case-root-launch", freeze_tree=False
                )
                workspace = session.open_directory(
                    workspace_relative, phase="workspace-launch"
                )
                codex_home = session.open_directory(
                    codex_home_relative,
                    phase="codex-home-launch",
                    freeze_tree=False,
                )
                home = session.open_directory(
                    _join_relative(case_relative, "home"),
                    phase="home-launch",
                    freeze_tree=False,
                )
                xdg_config = session.open_directory(
                    _join_relative(case_relative, "xdg-config"),
                    phase="xdg-launch",
                    freeze_tree=False,
                )
                xdg_cache = session.open_directory(
                    _join_relative(case_relative, "xdg-cache"),
                    phase="xdg-launch",
                    freeze_tree=False,
                )
                xdg_data = session.open_directory(
                    _join_relative(case_relative, "xdg-data"),
                    phase="xdg-launch",
                    freeze_tree=False,
                )
                open_directories.extend(
                    [case_root, workspace, codex_home, home, xdg_config, xdg_cache, xdg_data]
                )
                environment_additions: dict[str, str] = {
                    "AXIOM_FAKE_SCENARIO": (scenarios or {}).get(case["id"], "happy"),
                    "AXIOM_FAKE_OUTCOME": case["expectedOutcome"],
                    "AXIOM_FAKE_ROUTES": json.dumps(case["expectedRoutes"], separators=(",", ":")),
                    "AXIOM_FAKE_CLARIFICATIONS": str(case["expectedClarificationCount"]),
                    "AXIOM_FAKE_FRONT_DOOR": str(case["expectedUsingAxiomFrontDoorObserved"]).lower(),
                }
                if fake_only:
                    session.create_file(
                        _join_relative(case_relative, "call-ledger.jsonl"),
                        b"",
                        mode=0o600,
                        phase="fake-call-ledger-create",
                    )
                    environment_additions["AXIOM_FAKE_CALL_LOG"] = str(
                        Path(f"/proc/self/fd/{case_root.descriptor}")
                        / "call-ledger.jsonl"
                    )
                if plugin_state == "installed-derived-profile":
                    marketplace_relative = _join_relative(case_relative, "marketplace")
                    marketplace = _prepare_local_marketplace(
                        session, marketplace_relative, source_bundle
                    )
                    if fake_only:
                        install_additions = dict(environment_additions)
                        install_additions.update({
                            "AXIOM_FAKE_MARKETPLACE_ROOT": (
                                f"/proc/self/fd/{codex_home.descriptor}/marketplaces/{MARKETPLACE_NAME}"
                            ),
                            "AXIOM_FAKE_INSTALLED_PATH": (
                                f"/proc/self/fd/{codex_home.descriptor}/plugins/axiom"
                            ),
                            "AXIOM_FAKE_BUNDLE": f"/proc/self/fd/{source_bundle.descriptor}",
                        })
                    else:
                        install_additions = {}
                    install_env = build_isolated_environment(
                        codex_home=Path(f"/proc/self/fd/{codex_home.descriptor}"),
                        home=Path(f"/proc/self/fd/{home.descriptor}"),
                        xdg_config_home=Path(f"/proc/self/fd/{xdg_config.descriptor}"),
                        xdg_cache_home=Path(f"/proc/self/fd/{xdg_cache.descriptor}"),
                        xdg_data_home=Path(f"/proc/self/fd/{xdg_data.descriptor}"),
                        additions=install_additions if fake_only else None,
                    )
                    for purpose, argv in (
                        (
                            "marketplace",
                            build_marketplace_add_argv(
                                executable.path,
                                Path(f"/proc/self/fd/{marketplace.descriptor}"),
                            ),
                        ),
                        ("plugin-install", build_plugin_add_argv(executable.path)),
                    ):
                        try:
                            capture = _launch_bounded_process(
                                capability, executable, argv, purpose=purpose,
                                case_id=str(case["id"]), prompt=b"",
                                cwd=Path(f"/proc/self/fd/{case_root.descriptor}"),
                                env=install_env, maximum_stdout=MAX_RECEIPT_BYTES,
                                require_stdin_sentinel=False, popen_factory=popen_factory,
                                inherited_fds=(
                                    case_root.descriptor,
                                    codex_home.descriptor, home.descriptor,
                                    xdg_config.descriptor, xdg_cache.descriptor,
                                    xdg_data.descriptor, marketplace.descriptor,
                                    source_bundle.descriptor,
                                ),
                            )
                        except ProcessBoundaryError as error:
                            if error.process_started:
                                if purpose == "marketplace":
                                    marketplace_started = True
                                    marketplace_process_count += 1
                                else:
                                    plugin_started = True
                                    plugin_install_process_count += 1
                            raise
                        if purpose == "marketplace":
                            marketplace_started = True
                            marketplace_process_count += 1
                        else:
                            plugin_started = True
                            plugin_install_process_count += 1
                        if capture.timed_out or capture.returncode != 0 or capture.stderr:
                            raise ObservationError(f"{purpose} process failed")
                        if purpose == "marketplace":
                            parse_marketplace_receipt(capture.stdout, session, codex_home)
                        else:
                            _, installed = parse_plugin_receipt(
                                capture.stdout,
                                session,
                                codex_home,
                                expected_tree=bundle_before,
                            )
                    if installed is None:
                        raise ObservationError("plugin receipt did not bind an installed object")
                    invoke_test_hook(
                        "after-plugin-receipt",
                        session=session,
                        caseId=case["id"],
                        installed=installed,
                    )
                    _verify_frozen_directory(installed, expected_tree=bundle_before)
                    _verify_bundle_surface(
                        Path(f"/proc/self/fd/{installed.descriptor}"),
                        fake_only=fake_only,
                    )
                elif not _directory_entry_absent(codex_home.descriptor, "plugins"):
                    raise ObservationError("case 11 no-plugin control contains a plugin directory")
                _verify_temporary_config_has_no_hook_registration(
                    Path(f"/proc/self/fd/{codex_home.descriptor}")
                )
                config_verified_count += 1
                schema_relative = _join_relative(
                    case_relative, "model-response-schema.json"
                )
                schema_object = session.create_file(
                    schema_relative,
                    case_materialization.schema_bytes,
                    mode=0o400,
                    phase="model-schema-materialization",
                    keep_open=True,
                )
                if schema_object is None:
                    raise ObservationError("schema object was not frozen")
                _verify_frozen_file(schema_object, case_materialization.schema_bytes)
                invoke_test_hook(
                    "after-schema-create",
                    session=session,
                    caseId=case["id"],
                    schemaRelative=schema_relative,
                    schema=schema_object,
                )
                if fake_only:
                    if installed is None:
                        environment_additions["AXIOM_FAKE_NO_PLUGIN_CONTROL"] = "true"
                    else:
                        environment_additions["AXIOM_FAKE_INSTALLED_OBJECT"] = (
                            f"/proc/self/fd/{installed.descriptor}"
                        )
                model_env = build_isolated_environment(
                    codex_home=Path(f"/proc/self/fd/{codex_home.descriptor}"),
                    home=Path(f"/proc/self/fd/{home.descriptor}"),
                    xdg_config_home=Path(f"/proc/self/fd/{xdg_config.descriptor}"),
                    xdg_cache_home=Path(f"/proc/self/fd/{xdg_cache.descriptor}"),
                    xdg_data_home=Path(f"/proc/self/fd/{xdg_data.descriptor}"),
                    credential=None if fake_only else credential,
                    additions=environment_additions if fake_only else None,
                )
                invoke_test_hook(
                    "before-model-launch",
                    session=session,
                    caseId=case["id"],
                    workspace=workspace,
                    codexHome=codex_home,
                    installed=installed,
                    schema=schema_object,
                )
                normalized = _observe_case_process(
                    capability=capability, executable=executable,
                    output_schema=schema_object,
                    materialization=case_materialization,
                    materialization_seed=materialization_seed,
                    protocol_digest=identities["protocolDigest"],
                    cwd=workspace, env=model_env, taxonomy=taxonomy, case=case,
                    model_response_schema=model_schema,
                    fixture=fixture, plugin_state=plugin_state, workspace=workspace,
                    bundle=source_bundle, installed_copy=installed,
                    temporary_user_state=codex_home,
                    inherited_fds=(
                        *((case_root.descriptor,) if fake_only else ()),
                        workspace.descriptor,
                        codex_home.descriptor, home.descriptor,
                        xdg_config.descriptor, xdg_cache.descriptor,
                        xdg_data.descriptor,
                        *((installed.descriptor,) if fake_only and installed is not None else ()),
                    ),
                    marketplace_process_started=marketplace_started,
                    plugin_install_process_started=plugin_started,
                    popen_factory=popen_factory,
                    _test_hook=_test_hook,
                )
            except ObservationError as error:
                ledger.hard_stop(case["id"])
                _hard_stop_capability(capability)
                case_results.append(_incomplete_case_record(
                    case, fixture_document, fixture, case_materialization,
                    materialization_seed, identities["protocolDigest"], error,
                    marketplace_process_started=marketplace_started,
                    plugin_install_process_started=plugin_started,
                ))
                case_results.extend(
                    _not_run_case_record(
                        pending,
                        fixture_document,
                        case_materializations[pending_index],
                        materialization_seed,
                        identities["protocolDigest"],
                    )
                    for pending_index, pending in enumerate(
                        golden[index + 1 :], index + 1
                    )
                )
                break
            finally:
                if schema_object is not None:
                    os.close(schema_object.descriptor)
                _close_frozen_directory(installed)
                _close_frozen_directory(marketplace)
                for directory in reversed(open_directories):
                    _close_frozen_directory(directory)
            case_results.append(normalized)
            if normalized["status"] == "incomplete":
                ledger.hard_stop(case["id"])
                _hard_stop_capability(capability)
                case_results.extend(
                    _not_run_case_record(
                        pending,
                        fixture_document,
                        case_materializations[pending_index],
                        materialization_seed,
                        identities["protocolDigest"],
                    )
                    for pending_index, pending in enumerate(
                        golden[index + 1 :], index + 1
                    )
                )
                break
            ledger.seal(case["id"], normalized["status"])
        if len(case_results) != 16:
            raise ObservationError("orchestration failed to close all 16 ledger states")
        state_before_retire = _capability_state(capability)
        if not ledger.hard_stopped and (
            state_before_retire.remaining_calls != 0
            or state_before_retire.next_case_index != 16
            or state_before_retire.next_launch_index != len(LAUNCH_SEQUENCE)
        ):
            raise ObservationError("orchestration did not consume the exact launch plan")
        cleanup["sourceBundleUnchanged"] = (
            _verify_frozen_directory(source_bundle) == bundle_before
        )
    finally:
        _retire_capability(capability)
        _close_frozen_directory(source_bundle)
        invoke_test_hook("before-cleanup", session=session)
        owned_ledger = session.ledger
        session.close()
        try:
            cleanup_owned_root(root_identity, owned_ledger)
        except ObservationError:
            cleanup["manualCleanupRequired"] = True
        else:
            cleanup["temporaryRootsRemoved"] = not root_identity.path.exists()
        invoke_test_hook(
            "after-cleanup",
            rootIdentity=root_identity,
            cleanup=dict(cleanup),
        )
    result = _result_document(
        root=repository_root, run_mode="fake-validation" if fake_only else "host-observation",
        cases=case_results,
        config_verified_count=config_verified_count, executable=executable,
        marketplace_process_count=marketplace_process_count,
        plugin_install_process_count=plugin_install_process_count, cleanup=cleanup,
        materialization_seed=materialization_seed,
    )
    validate_normalized_result(result, repository_root)
    return result


def run_fake_validation(
    *,
    repository_root: Path,
    run_root: Path,
    fake_executable: Path,
    fake_executable_sha256: str,
    scenarios: Mapping[str, str] | None = None,
    _test_materialization_seed: bytes | None = None,
    _test_hook: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Authorize and run fake-only production orchestration without credentials."""
    identities = validate_protocol_documents(repository_root)
    expected_fake = (repository_root / "tests/fixtures/no_hook_observation.py").resolve(strict=True)
    expected_fake_digest = _sha256(
        _read_regular(expected_fake, "repository-owned fake Codex executable")
    )
    if fake_executable_sha256 != expected_fake_digest:
        raise ObservationError("fake validation executable digest is not repository-bound")
    _path_within(fake_executable, run_root, "fake Codex executable")
    executable = freeze_executable(fake_executable, fake_executable_sha256)
    capability = _mint_fake_execution_capability(
        protocol_digest=identities["protocolDigest"],
        entrypoint_sha256=_sha256(_read_regular(repository_root / ENTRYPOINT_RELATIVE, "entrypoint")),
        module_sha256=_sha256(_read_regular(repository_root / MODULE_RELATIVE, "module")),
        executable=executable, run_root=freeze_owned_root(run_root),
    )
    return run_observation_orchestration(
        repository_root=repository_root, run_root=run_root, executable=executable,
        capability=capability, credential=None,
        fake_only=True, scenarios=scenarios,
        _test_materialization_seed=_test_materialization_seed,
        _test_hook=_test_hook,
    )


@dataclass(frozen=True)
class FrozenOutputParent:
    descriptor: int
    path: Path
    basename: str
    device: int
    inode: int


def _freeze_external_output(
    path: Path,
    repository_root: Path,
    run_root: OwnedRootIdentity | None = None,
) -> FrozenOutputParent:
    if not path.is_absolute():
        raise ObservationError("normalized output path must be absolute")
    if path.name in {"", ".", ".."} or path.name != str(path).rsplit("/", 1)[-1]:
        raise ObservationError("normalized output must use one closed basename")
    parent = path.parent
    try:
        parent_metadata = parent.lstat()
    except OSError as error:
        raise ObservationError(f"cannot inspect normalized output parent: {error}") from error
    if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
        raise ObservationError("normalized output parent must be a non-symlink directory")
    current = parent
    while True:
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ObservationError("normalized output parent chain contains a symlink")
        if current.parent == current:
            break
        current = current.parent
    descriptor: int | None = None
    try:
        descriptor = os.open(parent, _directory_flags())
        opened = os.fstat(descriptor)
        if (
            not _same_identity(opened, parent_metadata.st_dev, parent_metadata.st_ino)
            or not stat.S_ISDIR(opened.st_mode)
        ):
            raise ObservationError("normalized output parent identity changed while opening")
        try:
            os.stat(path.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ObservationError("normalized output path already exists")
        actual_parent = Path(f"/proc/self/fd/{descriptor}").resolve(strict=True)
        try:
            actual_parent.relative_to(repository_root.resolve(strict=True))
        except ValueError:
            pass
        else:
            raise ObservationError("normalized output must be outside the repository")
        if run_root is not None:
            try:
                actual_parent.relative_to(run_root.path.resolve(strict=True))
            except ValueError:
                pass
            else:
                raise ObservationError(
                    "normalized output must be outside the observation run root"
                )
        frozen = FrozenOutputParent(
            descriptor=descriptor,
            path=parent,
            basename=path.name,
            device=opened.st_dev,
            inode=opened.st_ino,
        )
        descriptor = None
        return frozen
    except OSError as error:
        raise ObservationError("cannot freeze normalized output parent") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _verify_output_parent(identity: FrozenOutputParent) -> None:
    opened = os.fstat(identity.descriptor)
    try:
        current = identity.path.lstat()
    except OSError as error:
        raise ObservationError("normalized output parent binding disappeared") from error
    if (
        not _same_identity(opened, identity.device, identity.inode)
        or not _same_identity(current, identity.device, identity.inode)
        or not stat.S_ISDIR(opened.st_mode)
    ):
        raise ObservationError("normalized output parent binding changed")


def _mark_external_output_failure(document: Mapping[str, Any]) -> None:
    """Seal a caller-owned result as incomplete after publication confinement fails."""
    if type(document) is not dict:
        return
    cleanup = document.get("cleanup")
    object_facts = document.get("objectBindingFacts")
    if type(cleanup) is not dict or type(object_facts) is not dict:
        return
    cleanup["manualCleanupRequired"] = True
    object_facts["externalOutputObjectBinding"] = "failed"
    document["overallStatus"] = "incomplete"
    cases = document.get("cases")
    if type(cases) is list:
        document["summary"] = _derive_summary(cases, cleanup)
    codes = document.get("diagnosticCodes")
    if type(codes) is list:
        if "cleanup-manual-required" not in codes:
            codes.append("cleanup-manual-required")
        if "protocol-integrity-failure" not in codes:
            codes.append("protocol-integrity-failure")


def write_normalized_result(
    document: Mapping[str, Any], output: Path, root: Path = REPOSITORY_ROOT,
    *,
    _frozen_parent: FrozenOutputParent | None = None,
    _test_hook: Callable[[str, Mapping[str, Any]], None] | None = None,
) -> str:
    """Write one validated normalized result to a new repository-external file."""
    validate_normalized_result(document, root)
    parent = (
        _freeze_external_output(output, root)
        if _frozen_parent is None
        else _frozen_parent
    )
    if parent.path != output.parent or parent.basename != output.name:
        os.close(parent.descriptor)
        raise ObservationError("normalized output does not match its frozen parent")
    try:
        if _test_hook is not None:
            _test_hook("after-output-parent-open", {"parent": parent})
        finalized = copy.deepcopy(dict(document))
        finalized["objectBindingFacts"]["externalOutputObjectBinding"] = "verified"
        finalized["overallStatus"] = _derive_overall_status(
            finalized, load_codex_benchmark_contract(root)
        )
        validate_normalized_result(finalized, root)
        data = json.dumps(
            finalized, ensure_ascii=True, allow_nan=False, sort_keys=True, indent=2
        ).encode("ascii") + b"\n"
        if len(data) > MAX_CONTRACT_BYTES:
            raise ObservationError("normalized result exceeds the contract byte limit")
    except BaseException:
        _mark_external_output_failure(document)
        os.close(parent.descriptor)
        raise
    descriptor: int | None = None
    identity: tuple[int, int] | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        _verify_output_parent(parent)
        descriptor = os.open(
            parent.basename, flags, 0o600, dir_fd=parent.descriptor
        )
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ObservationError("normalized output is not a regular file")
        identity = (metadata.st_dev, metadata.st_ino)
        if _test_hook is not None:
            _test_hook(
                "after-output-create",
                {"parent": parent, "fileIdentity": identity},
            )
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if (
                type(written) is not int
                or written < 1
                or written > len(view)
            ):
                raise ObservationError(
                    "normalized output write made invalid progress"
                )
            view = view[written:]
        os.fsync(descriptor)
        written_metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(written_metadata.st_mode)
            or written_metadata.st_nlink != 1
            or (written_metadata.st_dev, written_metadata.st_ino) != identity
            or written_metadata.st_size != len(data)
        ):
            raise ObservationError(
                "normalized output object size or identity changed while writing"
            )
        _verify_output_parent(parent)
        current = os.stat(
            parent.basename,
            dir_fd=parent.descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_nlink != 1
            or (current.st_dev, current.st_ino) != identity
            or current.st_size != len(data)
        ):
            raise ObservationError("normalized output name binding changed")
        if _test_hook is not None:
            _test_hook(
                "after-output-write",
                {"parent": parent, "fileIdentity": identity},
            )
        _verify_output_parent(parent)
        current = os.stat(
            parent.basename,
            dir_fd=parent.descriptor,
            follow_symlinks=False,
        )
        if (
            (current.st_dev, current.st_ino) != identity
            or current.st_size != len(data)
        ):
            raise ObservationError("normalized output object was replaced")
        completed_descriptor = descriptor
        descriptor = None
        os.close(completed_descriptor)
        _verify_output_parent(parent)
        current = os.stat(
            parent.basename,
            dir_fd=parent.descriptor,
            follow_symlinks=False,
        )
        if (
            (current.st_dev, current.st_ino) != identity
            or current.st_size != len(data)
        ):
            raise ObservationError("normalized output object changed after close")
    except OSError as error:
        _mark_external_output_failure(document)
        raise ObservationError(f"cannot write normalized output: {error}") from error
    except BaseException:
        _mark_external_output_failure(document)
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if sys.exc_info()[0] is not None and identity is not None:
            try:
                current = os.stat(
                    parent.basename,
                    dir_fd=parent.descriptor,
                    follow_symlinks=False,
                )
                if (current.st_dev, current.st_ino) == identity:
                    os.unlink(parent.basename, dir_fd=parent.descriptor)
            except OSError:
                pass
        os.close(parent.descriptor)
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
    parser.add_argument("--expected-entrypoint-digest")
    parser.add_argument("--expected-module-digest")
    parser.add_argument("--expected-cli-version")
    parser.add_argument("--authorized-call-count", type=int)
    parser.add_argument("--codex-executable", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--source-repository", type=Path)
    parser.add_argument("--git-executable", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    output_parent: FrozenOutputParent | None = None
    try:
        identities = validate_protocol_documents(REPOSITORY_ROOT)
        if args.execute:
            if None in (
                args.codex_executable, args.run_root, args.source_repository,
                args.git_executable, args.output,
            ):
                raise ObservationError(
                    "execution requires exact Codex and Git executables, source repository, run root, and output"
                )
            executable = freeze_executable(args.codex_executable, args.expected_binary_digest or "")
            run_root = freeze_owned_root(args.run_root)
            output_parent = _freeze_external_output(
                args.output,
                REPOSITORY_ROOT,
                run_root,
            )
            entrypoint_sha256 = _sha256(_read_regular(REPOSITORY_ROOT / ENTRYPOINT_RELATIVE, "entrypoint"))
            module_sha256 = _sha256(_read_regular(REPOSITORY_ROOT / MODULE_RELATIVE, "module"))
            capability = _validate_execution_guard(
                execute=True,
                expected_protocol_digest=args.expected_protocol_digest,
                actual_protocol_digest=identities["protocolDigest"],
                expected_entrypoint_sha256=args.expected_entrypoint_digest or "",
                actual_entrypoint_sha256=entrypoint_sha256,
                expected_module_sha256=args.expected_module_digest or "",
                actual_module_sha256=module_sha256,
                expected_binary_digest=args.expected_binary_digest,
                executable=executable,
                expected_cli_version=args.expected_cli_version or "",
                actual_cli_version=CODEX_VERSION,
                source_commit=SOURCE_COMMIT,
                source_tree=SOURCE_TREE,
                run_root=run_root,
                model=MODEL,
                reasoning_effort=REASONING_EFFORT,
                authorized_call_count=args.authorized_call_count,
                credential_present=bool(os.environ.get("CODEX_API_KEY")),
            )
            result = run_observation_orchestration(
                repository_root=REPOSITORY_ROOT, run_root=args.run_root,
                executable=executable, capability=capability,
                credential=os.environ.get("CODEX_API_KEY"), fake_only=False,
                source_repository=args.source_repository,
                git_executable=args.git_executable,
            )
            frozen_output_parent = output_parent
            output_parent = None
            write_normalized_result(
                result,
                args.output,
                REPOSITORY_ROOT,
                _frozen_parent=frozen_output_parent,
            )
            print("Codex no-Hook normalized observation written after verified cleanup.")
            return 0
    except ObservationError as error:
        print(f"Codex no-Hook observation protocol failed: {error}", file=sys.stderr)
        return 1
    finally:
        if output_parent is not None:
            os.close(output_parent.descriptor)
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
    "materialize_fixture",
    "materialize_model_response_schema",
    "normalize_case_result",
    "parse_jsonl",
    "parse_marketplace_receipt",
    "parse_plugin_receipt",
    "protocol_summary",
    "recheck_executable",
    "render_case_prompt",
    "run_fake_validation",
    "self_digest",
    "snapshot_tree",
    "validate_model_response",
    "validate_normalized_result",
    "validate_protocol_documents",
    "write_normalized_result",
]
