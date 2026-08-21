"""Deterministic publication-policy result formatting."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar


Result = TypeVar("Result")


def run_policy(
    domain: str,
    operation: Callable[[list[str]], Result],
    failures: list[str],
) -> Result:
    """Run one domain and attach its owner to every reported failure."""
    local_failures: list[str] = []
    result = operation(local_failures)
    failures.extend(f"[{domain}] {failure}" for failure in local_failures)
    return result
