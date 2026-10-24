"""Claude Code stream-json observer and review-profile contracts on synthetic streams."""

import json
import shutil
import tempfile
from pathlib import Path
import unittest

from axiom_validation.context import REPOSITORY_ROOT
from axiom_validation.routing_evals import (
    CLAUDE_CODE_REVIEW_SEQUENCE_RELATIVE_PATH,
    check_claude_code_stream_json_taxonomy,
    check_review_sequence_contracts,
    classify_claude_code_stream_json_lines,
)

GATE = "Synthetic preamble.\n\nSynthetic routing gate.\n"
SKILLS = ("axiom:agents-architect", "axiom:using-axiom")
SUCCESS = {"type": "result", "subtype": "success", "is_error": False,
           "terminal_reason": "completed", "api_error_status": None, "permission_denials": []}


def stream(*extra, result=SUCCESS, hook_output=GATE, init_extra=None):
    """Build synthetic events shaped like the documented stream; no host output."""
    init = {"type": "system", "subtype": "init",
            "plugins": [{"name": "axiom", "version": "0.16.0"}], "skills": list(SKILLS)}
    init.update(init_extra or {})
    events = [
        {"type": "system", "subtype": "hook_started", "hook_event": "SessionStart"},
        {"type": "system", "subtype": "hook_response", "hook_event": "SessionStart",
         "outcome": "success", "exit_code": 0, "output": hook_output},
        init,
        {"type": "assistant", "parent_tool_use_id": None,
         "message": {"content": [{"type": "tool_use", "name": "StructuredOutput", "input": {}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
        *extra,
    ]
    if result is not None:
        events.append(result)
    return [json.dumps(event) for event in events]


def classify(lines):
    return classify_claude_code_stream_json_lines(
        lines, expected_startup_output=GATE, expected_plugin_version="0.16.0",
        expected_skills=SKILLS,
    )


class ClaudeCodeObserverTests(unittest.TestCase):
    def test_complete_run_yields_every_passing_fact(self):
        result = classify(stream())
        self.assertEqual("pass", result["outcome"])
        self.assertTrue(result["turnCompleted"])
        self.assertTrue(result["startupHookVerified"])
        self.assertTrue(result["installedPluginVerified"])
        self.assertEqual(1, result["structuredOutputCalls"])
        self.assertEqual(0, result["unexpectedTools"])
        self.assertFalse(result["failureSeen"] or result["forbiddenUnknownSeen"])
        allowed = {"ordinal", "eventType", "category", "role", "toolName"}
        self.assertTrue(all(set(entry) <= allowed for entry in result["journal"]))

    def test_other_tools_and_denials_count_as_unexpected(self):
        bash = {"type": "assistant", "parent_tool_use_id": None,
                "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {}}]}}
        self.assertEqual(1, classify(stream(bash))["unexpectedTools"])
        denied = {"type": "system", "subtype": "permission_denied"}
        result = classify(stream(denied, result=dict(SUCCESS, permission_denials=[{}])))
        self.assertEqual(1, result["unexpectedTools"])

    def test_startup_and_plugin_facts_compare_exactly(self):
        self.assertFalse(classify(stream(hook_output="different"))["startupHookVerified"])
        errors = {"plugin_errors": [{"plugin": "axiom", "type": "load", "message": "x"}]}
        self.assertFalse(classify(stream(init_extra=errors))["installedPluginVerified"])
        self.assertFalse(classify(stream(init_extra={"skills": [SKILLS[0]]}))["installedPluginVerified"])

    def test_unknown_late_missing_or_failed_events_fail_closed(self):
        unknown = classify(stream({"type": "system", "subtype": "unreviewed"}))
        self.assertEqual(("unknown", True), (unknown["outcome"], unknown["forbiddenUnknownSeen"]))
        late = classify([*stream(), json.dumps({"type": "user", "message": {"content": []}})])
        self.assertEqual("event-after-terminal", late["terminalReason"])
        missing = classify(stream(result=None))
        self.assertEqual(("unknown", "abrupt-input"), (missing["outcome"], missing["terminalReason"]))
        failed = classify(stream(result=dict(SUCCESS, subtype="error_during_execution", is_error=True)))
        self.assertEqual(("fail", True, False), (failed["outcome"], failed["failureSeen"], failed["turnCompleted"]))
        self.assertEqual("malformed-json-event", classify(["{"])["terminalReason"])

    def test_reviewed_taxonomy_is_exact(self):
        failures = []
        check_claude_code_stream_json_taxonomy(REPOSITORY_ROOT, failures)
        self.assertEqual([], failures)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            name = "claude-code-stream-json-observer-v1.json"
            document = json.loads((REPOSITORY_ROOT / "evals" / name).read_text())
            document["host"]["version"] = "0.0.0"
            (root / "evals" / name).write_text(json.dumps(document))
            check_claude_code_stream_json_taxonomy(root, failures)
        self.assertTrue(any("drifted from the reviewed Claude Code" in item for item in failures))

    def test_claude_code_review_profile_keeps_the_exact_cases(self):
        failures = []
        check_review_sequence_contracts(failures)
        self.assertEqual([], failures)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evals").mkdir()
            for name in ("review-sequences-v1.json", "review-response-schema-v1.json", "README.md"):
                shutil.copy(REPOSITORY_ROOT / "evals" / name, root / "evals" / name)
            profile = json.loads((REPOSITORY_ROOT / CLAUDE_CODE_REVIEW_SEQUENCE_RELATIVE_PATH).read_text())
            profile["safety"]["permissionMode"] = "bypassPermissions"
            profile["cases"] = profile["cases"][:-1]
            (root / CLAUDE_CODE_REVIEW_SEQUENCE_RELATIVE_PATH).write_text(json.dumps(profile, indent=2) + "\n")
            check_review_sequence_contracts(failures, root)
        for expected in ("digest drifted", "safety envelope drifted", "exact sanitized review cases"):
            self.assertTrue(any(expected in item for item in failures), expected)


if __name__ == "__main__":
    unittest.main()
