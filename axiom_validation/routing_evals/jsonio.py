"""Dependency-free strict JSON and bounded-file helpers."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any, Iterable

from ..context import REPOSITORY_ROOT, display_path
from .constants import MAX_JSON_BYTES, MAX_JSONL_BYTES
class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON or JSONL object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _display(path: Path, root: Path) -> str:
    if root == REPOSITORY_ROOT:
        return display_path(path)
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _inspect_regular_file(
    path: Path,
    maximum_bytes: int,
    failures: list[str],
    root: Path,
) -> bool:
    label = _display(path, root)
    try:
        metadata = path.lstat()
    except OSError as error:
        failures.append(f"cannot inspect {label}: {error}")
        return False
    if stat.S_ISLNK(metadata.st_mode):
        failures.append(f"{label} must not be a symbolic link")
        return False
    if not stat.S_ISREG(metadata.st_mode):
        failures.append(f"{label} must be a regular file")
        return False
    if metadata.st_size > maximum_bytes:
        failures.append(f"{label} exceeds the {maximum_bytes}-byte limit")
        return False
    return True


def load_json_object(
    path: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> dict[str, Any] | None:
    if not _inspect_regular_file(path, MAX_JSON_BYTES, failures, root):
        return None
    label = _display(path, root)
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKeyError) as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None
    if type(value) is not dict:
        failures.append(f"{label} must contain one top-level object")
        return None
    return value


def load_jsonl_cases(
    path: Path,
    failures: list[str],
    root: Path = REPOSITORY_ROOT,
) -> list[dict[str, Any]]:
    if not _inspect_regular_file(path, MAX_JSONL_BYTES, failures, root):
        return []
    label = _display(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {label}: {error}")
        return []
    if not lines:
        failures.append(f"{label} must contain at least one case")
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        line_label = f"{label}:{line_number}"
        if not line.strip():
            failures.append(f"{line_label} must not be blank")
            continue
        try:
            value = json.loads(line, object_pairs_hook=reject_duplicate_json_keys)
        except (json.JSONDecodeError, DuplicateJsonKeyError) as error:
            failures.append(f"invalid JSONL record in {line_label}: {error}")
            continue
        if type(value) is not dict:
            failures.append(f"{line_label} must contain one object")
            continue
        records.append(value)
    return records


def exact_object(
    value: Any,
    expected_keys: frozenset[str],
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(expected_keys - set(value))
    unknown = sorted(set(value) - expected_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def exact_object_with_optional(
    value: Any,
    required_keys: frozenset[str],
    optional_keys: frozenset[str],
    label: str,
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    missing = sorted(required_keys - set(value))
    unknown = sorted(set(value) - required_keys - optional_keys)
    if missing:
        failures.append(f"{label} is missing fields: {', '.join(missing)}")
    if unknown:
        failures.append(f"{label} contains unknown fields: {', '.join(unknown)}")
    return value


def require_string(
    value: Any,
    label: str,
    failures: list[str],
    maximum: int = 600,
) -> str | None:
    if type(value) is not str or not value:
        failures.append(f"{label} must be a non-empty string")
        return None
    if len(value) > maximum:
        failures.append(f"{label} exceeds {maximum} characters")
    return value


def require_bool(value: Any, label: str, failures: list[str]) -> bool | None:
    if type(value) is not bool:
        failures.append(f"{label} must be a boolean")
        return None
    return value


def require_int(
    value: Any,
    label: str,
    failures: list[str],
    minimum: int = 0,
) -> int | None:
    if type(value) is not int or value < minimum:
        failures.append(f"{label} must be an integer >= {minimum}")
        return None
    return value


def optional_bool(value: Any, label: str, failures: list[str]) -> bool | None:
    if value is None:
        return None
    return require_bool(value, label, failures)


def optional_int(
    value: Any,
    label: str,
    failures: list[str],
    *,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    result = require_int(value, label, failures)
    if result is not None and maximum is not None and result > maximum:
        failures.append(f"{label} must be <= {maximum}")
    return result


def require_string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    allowed: Iterable[str] | None = None,
    maximum_items: int = 16,
    maximum_length: int = 160,
) -> list[str] | None:
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return None
    if len(value) > maximum_items:
        failures.append(f"{label} exceeds {maximum_items} items")
    permitted = set(allowed) if allowed is not None else None
    seen: set[str] = set()
    for index, item in enumerate(value):
        string = require_string(item, f"{label}[{index}]", failures, maximum_length)
        if string is None:
            continue
        if string in seen:
            failures.append(f"{label} repeats {string!r}")
        seen.add(string)
        if permitted is not None and string not in permitted:
            failures.append(f"{label}[{index}] has unsupported value {string!r}")
    return value


def require_model_string_list(
    value: Any,
    label: str,
    failures: list[str],
    *,
    minimum_items: int,
    maximum_items: int,
    allowed: Iterable[str] | None = None,
) -> list[str] | None:
    """Validate only array constraints present in the model-facing schema."""
    if type(value) is not list:
        failures.append(f"{label} must be an array")
        return None
    if len(value) < minimum_items:
        failures.append(f"{label} must contain at least {minimum_items} items")
    if len(value) > maximum_items:
        failures.append(f"{label} exceeds {maximum_items} items")
    permitted = set(allowed) if allowed is not None else None
    for index, item in enumerate(value):
        if type(item) is not str:
            failures.append(f"{label}[{index}] must be a string")
        elif permitted is not None and item not in permitted:
            failures.append(f"{label}[{index}] has an unsupported enum value")
    return value
