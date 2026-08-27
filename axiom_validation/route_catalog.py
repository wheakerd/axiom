"""Canonical structured route-boundary data and deterministic documentation."""

from __future__ import annotations

import textwrap
from typing import Any

from .context import REPOSITORY_ROOT, display_path
from .context_budget import load_json


ROUTE_CATALOG_PATH = REPOSITORY_ROOT / "axiom_validation" / "route-boundaries-v1.json"
ROUTE_SURFACES = (
    "README.md",
    "docs/releases/v0.8.4.md",
)
ROUTE_MARKER = "route-boundary:traceable-git-submit-v1"
ROUTE_START = f"<!-- {ROUTE_MARKER}:start -->"
ROUTE_END = f"<!-- {ROUTE_MARKER}:end -->"
EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "schemaVersion",
        "contractId",
        "route",
        "hostNative",
        "preparedRelease",
        "traceableTriggers",
        "sharedSourceAnchors",
        "usingAxiomAnchors",
        "prohibitedClaims",
        "scenarios",
    }
)
EXPECTED_TRIGGER_IDS = (
    "explicit-route",
    "checkpoint",
    "baseline",
    "consolidation",
    "recovery",
    "multi-target",
    "force",
    "history-replacement",
)
EXPECTED_SCENARIO_KEYS = frozenset(
    {
        "name",
        "request",
        "classification",
        "trigger",
        "route",
        "phase",
        "references",
        "authorization",
    }
)


def _exact_keys(
    value: Any,
    label: str,
    expected: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def _string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    allow_empty: bool = False,
) -> list[str] | None:
    if (
        type(value) is not list
        or (not value and not allow_empty)
        or not all(type(item) is str and item for item in value)
    ):
        qualifier = "a string array" if allow_empty else "a non-empty-string array"
        failures.append(f"{label} must be {qualifier}")
        return None
    if len(value) != len(set(value)):
        failures.append(f"{label} must not contain duplicates")
    return value


def validate_route_catalog(document: dict[str, Any], failures: list[str]) -> bool:
    """Validate the closed route-boundary schema and semantic partitions."""
    initial_count = len(failures)
    root = _exact_keys(document, "route catalog", EXPECTED_TOP_LEVEL_KEYS, failures)
    if root is None:
        return False
    if root.get("schemaVersion") != "1":
        failures.append("route catalog schemaVersion must be '1'")
    if root.get("contractId") != "traceable-git-route-boundary-v1":
        failures.append("route catalog contractId drifted")
    if root.get("route") != "traceable-git-submit":
        failures.append("route catalog route must be 'traceable-git-submit'")

    host_native = _exact_keys(
        root.get("hostNative"),
        "route catalog hostNative",
        frozenset({"operations", "conditions", "expectedRoute", "expectedPhase"}),
        failures,
    )
    if host_native is not None:
        if host_native.get("operations") != ["stage", "commit", "push"]:
            failures.append("route catalog hostNative operations must be stage/commit/push")
        conditions = _exact_keys(
            host_native.get("conditions"),
            "route catalog hostNative.conditions",
            frozenset({"target", "force", "tag", "traceableTrigger"}),
            failures,
        )
        if conditions != {
            "target": "named-remote",
            "force": False,
            "tag": False,
            "traceableTrigger": False,
        }:
            failures.append(
                "route catalog hostNative conditions must retain the named-remote, "
                "non-force, no-tag, no-trigger boundary"
            )
        if host_native.get("expectedRoute") is not None:
            failures.append("route catalog hostNative expectedRoute must be null")
        if host_native.get("expectedPhase") != "normal":
            failures.append("route catalog hostNative expectedPhase must be 'normal'")

    prepared = _exact_keys(
        root.get("preparedRelease"),
        "route catalog preparedRelease",
        frozenset({"operations", "artifactState", "expectedRoute", "expectedPhase"}),
        failures,
    )
    if prepared is not None:
        if prepared.get("operations") != ["commit", "tag", "push"]:
            failures.append("route catalog preparedRelease operations must be commit/tag/push")
        if prepared.get("artifactState") != "already-prepared-plugin-release":
            failures.append("route catalog preparedRelease artifactState drifted")
        if prepared.get("expectedRoute") != root.get("route"):
            failures.append("route catalog preparedRelease expectedRoute drifted")
        if prepared.get("expectedPhase") != "hardened-submit":
            failures.append("route catalog preparedRelease expectedPhase drifted")

    trigger_values = root.get("traceableTriggers")
    trigger_ids: list[str] = []
    if type(trigger_values) is not list:
        failures.append("route catalog traceableTriggers must be an array")
    else:
        for index, value in enumerate(trigger_values):
            trigger = _exact_keys(
                value,
                f"route catalog traceableTriggers[{index}]",
                frozenset({"id", "label"}),
                failures,
            )
            if trigger is None:
                continue
            trigger_id = trigger.get("id")
            label = trigger.get("label")
            if type(trigger_id) is not str or not trigger_id:
                failures.append(f"route catalog traceableTriggers[{index}].id must be a string")
            else:
                trigger_ids.append(trigger_id)
            if type(label) is not str or not label:
                failures.append(f"route catalog traceableTriggers[{index}].label must be a string")
    if tuple(trigger_ids) != EXPECTED_TRIGGER_IDS:
        failures.append(
            "route catalog trigger order or membership drifted: " + ", ".join(trigger_ids)
        )

    anchors = _string_list(root.get("usingAxiomAnchors"), "route catalog usingAxiomAnchors", failures)
    if anchors is not None and len(anchors) < 4:
        failures.append("route catalog must retain all using-axiom boundary anchors")
    shared_anchors = _string_list(
        root.get("sharedSourceAnchors"),
        "route catalog sharedSourceAnchors",
        failures,
    )
    if shared_anchors is not None and len(shared_anchors) < 5:
        failures.append("route catalog must retain all shared route-source anchors")
    prohibited = _string_list(root.get("prohibitedClaims"), "route catalog prohibitedClaims", failures)
    if prohibited is not None and not any(
        "submit, publish, or push selects" in claim for claim in prohibited
    ):
        failures.append("route catalog must reject the over-broad submit/publish/push claim")

    scenarios = root.get("scenarios")
    scenario_names: list[str] = []
    covered_triggers: list[str] = []
    host_native_count = 0
    prepared_count = 0
    if type(scenarios) is not list:
        failures.append("route catalog scenarios must be an array")
    else:
        for index, value in enumerate(scenarios):
            scenario = _exact_keys(
                value,
                f"route catalog scenarios[{index}]",
                EXPECTED_SCENARIO_KEYS,
                failures,
            )
            if scenario is None:
                continue
            name = scenario.get("name")
            request = scenario.get("request")
            classification = scenario.get("classification")
            trigger = scenario.get("trigger")
            route = scenario.get("route")
            phase = scenario.get("phase")
            if type(name) is not str or not name:
                failures.append(f"route catalog scenarios[{index}].name must be a string")
            else:
                scenario_names.append(name)
            if type(request) is not str or not request:
                failures.append(f"route catalog scenarios[{index}].request must be a string")
            if classification not in {"host-native", "traceable"}:
                failures.append(f"route catalog scenarios[{index}].classification is invalid")
            if type(phase) is not str or not phase:
                failures.append(f"route catalog scenarios[{index}].phase must be a string")
            _string_list(
                scenario.get("references"),
                f"route catalog scenarios[{index}].references",
                failures,
                allow_empty=True,
            )
            authorization = _string_list(
                scenario.get("authorization"),
                f"route catalog scenarios[{index}].authorization",
                failures,
            )
            if authorization is not None and "read" not in authorization:
                failures.append(f"route catalog scenarios[{index}] must retain read authority")
            if classification == "host-native":
                host_native_count += 1
                if trigger is not None or route is not None or phase != "normal":
                    failures.append(
                        f"route catalog scenarios[{index}] host-native boundary drifted"
                    )
            else:
                if type(trigger) is not str or trigger not in {
                    "prepared-plugin-release",
                    *EXPECTED_TRIGGER_IDS,
                }:
                    failures.append(f"route catalog scenarios[{index}].trigger is invalid")
                else:
                    covered_triggers.append(trigger)
                if route != root.get("route"):
                    failures.append(f"route catalog scenarios[{index}].route drifted")
                if trigger == "prepared-plugin-release":
                    prepared_count += 1
                    if phase != "hardened-submit":
                        failures.append(
                            f"route catalog scenarios[{index}] prepared release phase drifted"
                        )
    if len(scenario_names) != len(set(scenario_names)):
        failures.append("route catalog scenario names must be unique")
    if host_native_count != 1:
        failures.append("route catalog must contain exactly one canonical host-native scenario")
    if prepared_count != 1:
        failures.append("route catalog must contain exactly one prepared-release scenario")
    if tuple(
        trigger for trigger in covered_triggers if trigger != "prepared-plugin-release"
    ) != EXPECTED_TRIGGER_IDS:
        failures.append("route catalog scenarios do not cover every traceable trigger in order")
    return len(failures) == initial_count


def load_route_catalog(failures: list[str]) -> dict[str, Any] | None:
    document = load_json(ROUTE_CATALOG_PATH, failures)
    if document is None:
        return None
    return document if validate_route_catalog(document, failures) else None


def route_boundary_scenarios() -> tuple[dict[str, Any], ...]:
    """Build offline fixtures directly from the reviewed structured catalog."""
    failures: list[str] = []
    document = load_route_catalog(failures)
    if document is None:
        return ()
    return tuple(
        {
            "name": scenario["name"],
            "request": scenario["request"],
            "route": scenario["route"],
            "phase": scenario["phase"],
            "references": tuple(scenario["references"]),
            "authorization": frozenset(scenario["authorization"]),
        }
        for scenario in document["scenarios"]
    )


def _english_join(values: list[str]) -> str:
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def render_route_boundary(document: dict[str, Any]) -> str:
    """Render the reviewed Git route boundary without prose-owned facts."""
    route = document["route"]
    trigger_labels = [entry["label"] for entry in document["traceableTriggers"]]
    return (
        "Ordinary named-remote, non-force staging, commits, and pushes stay "
        "host-native when they include neither a tag nor a traceable trigger. "
        "A combined commit, tag, and push of an already-prepared plugin release "
        f"selects `{route}`'s hardened phase. The traceable triggers are "
        f"{_english_join(trigger_labels)}. Merely mentioning `submit`, `publish`, "
        "or `push` does not select the route."
    )


def rendered_route_block(document: dict[str, Any]) -> str:
    body = textwrap.fill(
        render_route_boundary(document),
        width=88,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return f"{ROUTE_START}\n{body}\n{ROUTE_END}"


def replace_route_block(text: str, document: dict[str, Any]) -> str:
    """Return text with its one route-boundary marker region rendered."""
    if text.count(ROUTE_START) != 1 or text.count(ROUTE_END) != 1:
        raise ValueError("route-boundary document must contain one start and one end marker")
    start = text.index(ROUTE_START)
    end = text.index(ROUTE_END, start) + len(ROUTE_END)
    return text[:start] + rendered_route_block(document) + text[end:]


def check_route_surface_text(
    relative_path: str,
    text: str,
    document: dict[str, Any],
    failures: list[str],
) -> None:
    expected = rendered_route_block(document)
    if text.count(ROUTE_START) != 1 or text.count(ROUTE_END) != 1:
        failures.append(f"{relative_path} must contain exactly one managed route-boundary block")
    elif expected not in text:
        failures.append(
            f"{relative_path} route-boundary block drifted; run "
            "python3 scripts/render-release-facts.py --render"
        )
    normalized = " ".join(text.split()).casefold()
    for claim in document["prohibitedClaims"]:
        if " ".join(claim.split()).casefold() in normalized:
            failures.append(f"{relative_path} restores prohibited over-broad route claim {claim!r}")


def check_route_catalog(failures: list[str]) -> int:
    """Validate structured data, using-axiom anchors, docs, and fixture coverage."""
    document = load_route_catalog(failures)
    if document is None:
        return 0

    front_door_path = REPOSITORY_ROOT / "skills" / "using-axiom" / "SKILL.md"
    try:
        front_door = " ".join(front_door_path.read_text(encoding="utf-8").split()).casefold()
    except OSError as error:
        failures.append(f"cannot read {display_path(front_door_path)}: {error}")
    else:
        for anchor in document["usingAxiomAnchors"]:
            if " ".join(anchor.split()).casefold() not in front_door:
                failures.append(
                    f"{display_path(front_door_path)} drifted from route catalog anchor {anchor!r}"
                )

    for relative_path in ROUTE_SURFACES:
        path = REPOSITORY_ROOT / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {relative_path}: {error}")
            continue
        check_route_surface_text(relative_path, text, document, failures)
    return len(document["scenarios"])


__all__ = (
    "ROUTE_CATALOG_PATH",
    "ROUTE_END",
    "ROUTE_MARKER",
    "ROUTE_START",
    "ROUTE_SURFACES",
    "check_route_catalog",
    "check_route_surface_text",
    "load_route_catalog",
    "render_route_boundary",
    "rendered_route_block",
    "replace_route_block",
    "route_boundary_scenarios",
    "validate_route_catalog",
)
