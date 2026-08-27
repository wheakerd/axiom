"""Shared strict-evidence gate regression fixtures."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


NON_TRUE_EVIDENCE_VALUES = (
    False,
    None,
    0,
    1,
    "false",
    "true",
    "",
    "present",
    [],
    ["present"],
    {},
    {"unexpected": "object"},
)


def check_strict_evidence_gate(
    gate: Callable[[Mapping[str, Any]], bool],
    fields: Sequence[str],
    label: str,
    failures: list[str],
) -> int:
    scenario_count = 0
    complete = {field: True for field in fields}
    if not gate(complete):
        failures.append(f"complete {label} evidence must pass")
    scenario_count += 1

    for field in fields:
        for value in NON_TRUE_EVIDENCE_VALUES:
            rejected = dict(complete)
            rejected[field] = value
            if gate(rejected):
                failures.append(
                    f"{label} field {field!r} must reject "
                    f"{type(value).__name__} value {value!r}"
                )
            scenario_count += 1

        missing = dict(complete)
        del missing[field]
        if gate(missing):
            failures.append(f"{label} evidence missing {field!r} must fail closed")
        scenario_count += 1

        missing_with_unknown = dict(missing)
        missing_with_unknown["unexpected_evidence"] = True
        if gate(missing_with_unknown):
            failures.append(
                f"unknown {label} evidence must not replace missing field {field!r}"
            )
        scenario_count += 1
    return scenario_count
