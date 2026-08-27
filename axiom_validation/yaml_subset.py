"""Strict parsers for Axiom's protected YAML subsets."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


class CanonicalYamlError(ValueError):
    """Raised when a protected YAML file leaves Axiom's strict tiny schema."""


def parse_agent_metadata_document(
    text: str,
    label: str,
    *,
    allow_policy: bool,
) -> dict[str, dict[str, Any]]:
    """Consume agents/openai.yaml through its exact canonical tiny schema."""
    quoted = r'"[^\r\n]*"'
    pattern = re.compile(
        rf"interface:\n"
        rf"  display_name: (?P<display_name>{quoted})\n"
        rf"  short_description: (?P<short_description>{quoted})\n"
        rf"  default_prompt: (?P<default_prompt>{quoted})"
        rf"(?P<policy>\npolicy:\n  allow_implicit_invocation: false)?\n?"
    )
    match = pattern.fullmatch(text)
    policy_present = match is not None and match.group("policy") is not None
    if match is None or policy_present != allow_policy:
        raise CanonicalYamlError(
            f"{label} must match the complete canonical interface"
            + (" plus non-implicit policy schema" if allow_policy else " schema with no tail")
        )
    try:
        interface = {
            field: json.loads(match.group(field))
            for field in ("display_name", "short_description", "default_prompt")
        }
    except json.JSONDecodeError as error:
        raise CanonicalYamlError(f"{label} has an invalid quoted string: {error.msg}") from error
    result: dict[str, dict[str, Any]] = {"interface": interface}
    if allow_policy:
        result["policy"] = {"allow_implicit_invocation": False}
    return result


def parse_skill_frontmatter_document(text: str, label: str) -> dict[str, str]:
    """Parse the complete frontmatter document and reject non-schema content."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise CanonicalYamlError(f"{label} must start with an exact YAML delimiter")
    try:
        closing_index = lines.index("---", 1)
    except ValueError as error:
        raise CanonicalYamlError(f"{label} has no closing YAML delimiter") from error
    if closing_index == 1:
        raise CanonicalYamlError(f"{label} frontmatter is empty")
    if not any(line.strip() for line in lines[closing_index + 1 :]):
        raise CanonicalYamlError(f"{label} must contain a Markdown body after frontmatter")

    expected = ("name", "description")
    implicit_non_strings = {
        "y",
        "yes",
        "n",
        "no",
        "true",
        "false",
        "on",
        "off",
        "null",
        "~",
    }
    fields: dict[str, str] = {}
    order: list[str] = []
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        match = re.fullmatch(r"([a-z_]+): (.+)", line)
        if match is None or line != line.rstrip() or "\t" in line:
            raise CanonicalYamlError(
                f"{label}:{line_number} frontmatter must use one canonical key and scalar"
            )
        key, raw_value = match.groups()
        if key in fields:
            raise CanonicalYamlError(f"{label}:{line_number} duplicate field {key!r}")
        if key not in expected:
            raise CanonicalYamlError(f"{label}:{line_number} unknown field {key!r}")
        if (
            raw_value != raw_value.strip()
            or raw_value.casefold() in implicit_non_strings
            or re.fullmatch(r"[A-Za-z][\x20-\x7e]*", raw_value) is None
            or " #" in raw_value
            or ": " in raw_value
            or raw_value.endswith(":")
        ):
            raise CanonicalYamlError(
                f"{label}:{line_number} {key!r} must be a canonical plain string"
            )
        fields[key] = raw_value
        order.append(key)
    if tuple(order) != expected:
        raise CanonicalYamlError(f"{label} frontmatter must contain only name then description")
    return fields


@dataclass(frozen=True)


class CanonicalYamlScalar:
    """A scalar from Axiom's dependency-free canonical YAML subset."""

    value: str
    comment: str
    line: int


@dataclass(frozen=True)


class CanonicalYamlLine:
    indent: int
    content: str
    line: int


@dataclass(frozen=True)


class ActionUse:
    declaration: str
    comment: str
    line: int
    scope: str


def split_yaml_comment(raw: str) -> tuple[str, str]:
    """Split a YAML scalar from an unquoted inline comment."""
    single_quoted = False
    double_quoted = False
    escaped = False
    index = 0
    while index < len(raw):
        character = raw[index]
        if double_quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                double_quoted = False
            index += 1
            continue
        if single_quoted:
            if character == "'":
                if index + 1 < len(raw) and raw[index + 1] == "'":
                    index += 2
                    continue
                single_quoted = False
            index += 1
            continue
        if character == '"':
            double_quoted = True
        elif character == "'":
            single_quoted = True
        elif character == "#" and (index == 0 or raw[index - 1].isspace()):
            return raw[:index].rstrip(), raw[index + 1 :].strip()
        index += 1
    return raw.rstrip(), ""


def canonical_yaml_lines(text: str, label: str) -> list[CanonicalYamlLine]:
    """Tokenize canonical block YAML while treating scalar bodies as opaque."""
    if "\r" in text:
        raise CanonicalYamlError(f"{label} must use LF line endings")

    tokens: list[CanonicalYamlLine] = []
    block_parent_indent: int | None = None
    block_header = re.compile(
        r"(?:-\s+)?[A-Za-z_][A-Za-z0-9_-]*:\s*[>|][+-]?[0-9]*$"
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(" \t"))]
        indent = len(leading)
        if block_parent_indent is not None:
            if not raw_line.strip() or indent > block_parent_indent:
                continue
            block_parent_indent = None

        if not raw_line.strip() or raw_line.lstrip(" ").startswith("#"):
            continue
        if "\t" in raw_line:
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML must not contain tabs"
            )
        if raw_line != raw_line.rstrip(" "):
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML must not contain trailing spaces"
            )
        if indent % 2:
            raise CanonicalYamlError(
                f"{label}:{line_number} canonical YAML indentation must use two-space levels"
            )

        content = raw_line[indent:]
        uncommented, _ = split_yaml_comment(content)
        if uncommented in {"---", "..."}:
            raise CanonicalYamlError(
                f"{label}:{line_number} multiple YAML documents are not allowed"
            )
        tokens.append(CanonicalYamlLine(indent, content, line_number))
        if block_header.fullmatch(uncommented):
            block_parent_indent = indent
    return tokens


class CanonicalYamlParser:
    """Parse the canonical block subset used by workflows and action metadata."""

    def __init__(self, text: str, label: str) -> None:
        self.label = label
        self.tokens = canonical_yaml_lines(text, label)

    def parse(self) -> dict[str, Any]:
        if not self.tokens:
            raise CanonicalYamlError(f"{self.label} is empty")
        if self.tokens[0].indent != 0 or self.tokens[0].content.startswith("-"):
            raise CanonicalYamlError(
                f"{self.label}:{self.tokens[0].line} must start with a top-level mapping"
            )
        value, index = self.parse_mapping(0, 0)
        if index != len(self.tokens):
            token = self.tokens[index]
            raise CanonicalYamlError(
                f"{self.label}:{token.line} has an unexpected YAML structure"
            )
        return value

    def parse_mapping(self, index: int, indent: int) -> tuple[dict[str, Any], int]:
        mapping: dict[str, Any] = {}
        while index < len(self.tokens):
            token = self.tokens[index]
            if token.indent < indent:
                break
            if token.indent > indent:
                raise CanonicalYamlError(
                    f"{self.label}:{token.line} has an unexpected indentation level"
                )
            if token.content.startswith("-"):
                break
            index = self.parse_mapping_entry(
                mapping,
                token.content,
                token.line,
                indent,
                index + 1,
            )
        return mapping, index

    def parse_mapping_entry(
        self,
        mapping: dict[str, Any],
        content: str,
        line: int,
        indent: int,
        next_index: int,
    ) -> int:
        uncommented, comment = split_yaml_comment(content)
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?", uncommented)
        if match is None:
            raise CanonicalYamlError(
                f"{self.label}:{line} must use an unquoted canonical mapping key"
            )
        key, raw_value = match.groups()
        if key in mapping:
            raise CanonicalYamlError(
                f"{self.label}:{line} contains duplicate mapping key {key!r}"
            )
        if raw_value is not None:
            mapping[key] = self.parse_scalar(raw_value, comment, line)
            return next_index

        if next_index < len(self.tokens) and self.tokens[next_index].indent > indent:
            child = self.tokens[next_index]
            if child.indent != indent + 2:
                raise CanonicalYamlError(
                    f"{self.label}:{child.line} nested content must advance one indentation level"
                )
            if child.content.startswith("-"):
                mapping[key], next_index = self.parse_sequence(next_index, indent + 2)
            else:
                mapping[key], next_index = self.parse_mapping(next_index, indent + 2)
        else:
            mapping[key] = CanonicalYamlScalar("", comment, line)
        return next_index

    def parse_sequence(self, index: int, indent: int) -> tuple[list[Any], int]:
        sequence: list[Any] = []
        while index < len(self.tokens):
            token = self.tokens[index]
            if token.indent < indent:
                break
            if token.indent > indent:
                raise CanonicalYamlError(
                    f"{self.label}:{token.line} has an unexpected sequence indentation"
                )
            if token.content == "-":
                next_index = index + 1
                if next_index >= len(self.tokens) or self.tokens[next_index].indent != indent + 2:
                    raise CanonicalYamlError(
                        f"{self.label}:{token.line} empty sequence entry has no child"
                    )
                child = self.tokens[next_index]
                if child.content.startswith("-"):
                    value, index = self.parse_sequence(next_index, indent + 2)
                else:
                    value, index = self.parse_mapping(next_index, indent + 2)
                sequence.append(value)
                continue
            if not token.content.startswith("- "):
                break

            remainder = token.content[2:]
            uncommented, _ = split_yaml_comment(remainder)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*:(?: .*)?", uncommented):
                item: dict[str, Any] = {}
                index = self.parse_mapping_entry(
                    item,
                    remainder,
                    token.line,
                    indent + 2,
                    index + 1,
                )
                while index < len(self.tokens):
                    continuation = self.tokens[index]
                    if continuation.indent != indent + 2 or continuation.content.startswith("-"):
                        break
                    index = self.parse_mapping_entry(
                        item,
                        continuation.content,
                        continuation.line,
                        indent + 2,
                        index + 1,
                    )
                sequence.append(item)
                continue

            raw_scalar, comment = split_yaml_comment(remainder)
            sequence.append(self.parse_scalar(raw_scalar, comment, token.line))
            index += 1
            if index < len(self.tokens) and self.tokens[index].indent > indent:
                child = self.tokens[index]
                raise CanonicalYamlError(
                    f"{self.label}:{child.line} scalar sequence entry cannot own nested content"
                )
        return sequence, index

    def parse_scalar(self, raw: str, comment: str, line: int) -> CanonicalYamlScalar:
        if not raw or raw != raw.strip():
            raise CanonicalYamlError(
                f"{self.label}:{line} scalar must use canonical spacing"
            )
        if raw[0] in "&*!{[" or raw.startswith("<<:"):
            raise CanonicalYamlError(
                f"{self.label}:{line} aliases, tags, and flow collections are not allowed"
            )
        if raw.startswith('"') or raw.endswith('"'):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as error:
                raise CanonicalYamlError(
                    f"{self.label}:{line} has an invalid double-quoted scalar"
                ) from error
            if not isinstance(value, str):
                raise CanonicalYamlError(
                    f"{self.label}:{line} quoted scalar must decode to a string"
                )
        elif raw.startswith("'") or raw.endswith("'"):
            if re.fullmatch(r"'(?:[^']|'')*'", raw) is None:
                raise CanonicalYamlError(
                    f"{self.label}:{line} has an invalid single-quoted scalar"
                )
            value = raw[1:-1].replace("''", "'")
        else:
            if ": " in raw:
                raise CanonicalYamlError(
                    f"{self.label}:{line} ambiguous plain scalar must be quoted"
                )
            value = raw
        return CanonicalYamlScalar(value, comment, line)


def parse_canonical_yaml_document(text: str, label: str) -> dict[str, Any]:
    return CanonicalYamlParser(text, label).parse()
