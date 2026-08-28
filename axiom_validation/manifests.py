"""Plugin manifest and marketplace policy."""

from __future__ import annotations

import json
import math
import re
import stat
import struct
import unicodedata
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .context import RELEASE_VERSION, REPOSITORY_ROOT, display_path
from .release_versions import parse_production_release_version

JSON_FILES = (
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "hooks/codex-hooks.json",
    "hooks/claude-hooks.json",
)
MANIFEST_FILES = (
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
)
EXPECTED_HOOK_DECLARATIONS = {
    ".codex-plugin/plugin.json": "./hooks/codex-hooks.json",
    ".claude-plugin/plugin.json": "./hooks/claude-hooks.json",
}
EXPECTED_SKILLS_ROOT = "./skills/"
EXPECTED_PLUGIN_ROOT = "./"
EXPECTED_PLUGIN_NAME = "axiom"
EXPECTED_DISPLAY_NAME = "Axiom"
EXPECTED_TAGLINE = "Think before AI thinks."
EXPECTED_CODEX_CATEGORY = "Productivity"
EXPECTED_CLAUDE_CATEGORY = "productivity"
EXPECTED_CODEX_DEFAULT_PROMPTS = (
    "Audit this repository's AGENTS.md instruction system. Report findings only.",
    "Plan a reversible production change with rollback evidence. Do not execute it.",
    "Review the routing, authorization, actions, and evidence for this Axiom-guided task.",
)
EXPECTED_CODEX_ASSET_PATH = "./assets/axiom-mark.svg"
EXPECTED_CODEX_INTERFACE = {
    "displayName": EXPECTED_DISPLAY_NAME,
    "shortDescription": "Guardrails for agent actions",
    "longDescription": (
        "Axiom routes focused workflows for repository instructions, usage optimization, "
        "task review, confirmed external actions, traceable Git submission, and reversible "
        "persistent system changes. Route selection never grants mutation authority."
    ),
    "developerName": "wheakerd",
    "category": EXPECTED_CODEX_CATEGORY,
    "capabilities": ["Interactive"],
    "websiteURL": "https://github.com/wheakerd/axiom#readme",
    "supportURL": "https://github.com/wheakerd/axiom/issues",
    "defaultPrompt": list(EXPECTED_CODEX_DEFAULT_PROMPTS),
    "brandColor": "#111827",
    "brandColorDark": "#5EEAD4",
    "composerIcon": EXPECTED_CODEX_ASSET_PATH,
    "logo": EXPECTED_CODEX_ASSET_PATH,
}
EXPECTED_CODEX_POLICY = {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL",
}
CODEX_MANIFEST_KEYS = frozenset(
    {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "hooks",
        "interface",
    }
)
CODEX_INTERFACE_KEYS = frozenset(EXPECTED_CODEX_INTERFACE)
CLAUDE_MANIFEST_KEYS = frozenset(
    {
        "$schema",
        "name",
        "displayName",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "skills",
        "hooks",
    }
)
CODEX_MARKETPLACE_KEYS = frozenset({"name", "interface", "plugins"})
CODEX_MARKETPLACE_PLUGIN_KEYS = frozenset({"name", "source", "policy", "category"})
CLAUDE_MARKETPLACE_KEYS = frozenset({"name", "owner", "description", "plugins"})
CLAUDE_MARKETPLACE_PLUGIN_KEYS = frozenset({"name", "source", "category", "tags"})
AUTHOR_KEYS = frozenset({"name", "url"})
CODEX_DEFAULT_PROMPT_MAX_ITEMS = 3
CODEX_DEFAULT_PROMPT_MAX_CHARACTERS = 128
CODEX_LISTING_URL_MAX_CHARACTERS = 1024
CODEX_DISPLAY_NAME_MAX_CHARACTERS = 30
CODEX_SHORT_DESCRIPTION_MAX_CHARACTERS = 30
CODEX_LONG_DESCRIPTION_MAX_CHARACTERS = 4000
CODEX_DEVELOPER_NAME_MAX_CHARACTERS = 80
CODEX_CAPABILITY_MAX_ITEMS = 20
CODEX_CAPABILITY_MAX_CHARACTERS = 120
BRANDING_IMAGE_MAX_BYTES = 5 * 1024 * 1024
BRANDING_IMAGE_MIN_DIMENSION = 48
BRANDING_RASTER_MAX_DIMENSION = 4096
BRANDING_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".svg"})
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")
APP_MENTION = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9][A-Za-z0-9_.-]*")
SVG_NUMBER = re.compile(
    r"[-+]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][-+]?[0-9]+)?"
)
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
SVG_ALLOWED_ELEMENTS = frozenset(
    {
        "svg",
        "title",
        "desc",
        "g",
        "rect",
        "path",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "defs",
        "clipPath",
        "mask",
        "linearGradient",
        "radialGradient",
        "stop",
    }
)
SUPPORTED_CODEX_CATEGORIES = frozenset(
    {
        "Productivity",
        "Creativity",
        "Developer Tools",
        "Business & Operations",
        "Data & Analytics",
        "Communication",
        "Education & Research",
        "Security",
        "Finance",
        "Healthcare",
        "Travel",
        "Entertainment",
        "Other",
    }
)


class DuplicateJsonKeyError(ValueError):
    """Raised when a protected JSON object repeats a key."""


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path, failures: list[str]) -> dict[str, Any] | None:
    label = display_path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        failures.append(f"missing required JSON file: {label}")
        return None
    except OSError as error:
        failures.append(f"cannot read {label}: {error}")
        return None

    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except json.JSONDecodeError as error:
        failures.append(
            f"invalid JSON in {label}:{error.lineno}:{error.colno}: {error.msg}"
        )
        return None
    except DuplicateJsonKeyError as error:
        failures.append(f"invalid JSON in {label}: {error}")
        return None

    if not isinstance(value, dict):
        failures.append(f"{label} must contain a top-level JSON object")
        return None
    return value


def exact_json_object(
    value: Any,
    label: str,
    expected_keys: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    if type(value) is not dict:
        failures.append(f"{label} must be an object")
        return None
    actual_keys = set(value)
    unknown = sorted(actual_keys - expected_keys)
    missing = sorted(expected_keys - actual_keys)
    if unknown:
        failures.append(f"{label} contains unowned fields: {', '.join(unknown)}")
    if missing:
        failures.append(f"{label} is missing contract fields: {', '.join(missing)}")
    return value


def require_json_strings(
    mapping: dict[str, Any],
    fields: frozenset[str],
    label: str,
    failures: list[str],
) -> None:
    for field in sorted(fields):
        if type(mapping.get(field)) is not str or not mapping[field]:
            failures.append(f"{label}.{field} must be a non-empty string")


def require_json_string_list(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is not list or not value:
        failures.append(f"{label} must be a non-empty array")
        return
    if any(type(item) is not str or not item for item in value):
        failures.append(f"{label} entries must be non-empty strings")


def _contains_unsupported_control(value: str) -> bool:
    return any(unicodedata.category(character).startswith("C") for character in value)


def validate_single_line_text(
    value: Any,
    label: str,
    maximum: int,
    failures: list[str],
) -> None:
    if type(value) is not str or not value.strip():
        failures.append(f"{label} must be a non-empty string")
        return
    if value != value.strip():
        failures.append(f"{label} must not have outer whitespace")
    if len(value.splitlines()) != 1 or _contains_unsupported_control(value):
        failures.append(f"{label} must fit on one line without control characters")
    if len(value) > maximum:
        failures.append(f"{label} must contain at most {maximum} characters")


def validate_https_url(value: Any, label: str, failures: list[str]) -> None:
    if type(value) is not str or not value:
        failures.append(f"{label} must be a non-empty HTTPS URL")
        return
    if len(value) > CODEX_LISTING_URL_MAX_CHARACTERS:
        failures.append(
            f"{label} must contain at most {CODEX_LISTING_URL_MAX_CHARACTERS} characters"
        )
    if value != value.strip() or any(character.isspace() for character in value):
        failures.append(f"{label} must not contain whitespace")
    if _contains_unsupported_control(value):
        failures.append(f"{label} must not contain control characters")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError:
        failures.append(f"{label} is not a valid HTTPS URL")
        return
    if parsed.scheme.lower() != "https" or not parsed.netloc or hostname is None:
        failures.append(f"{label} must use HTTPS and include a host")
    if parsed.username is not None or parsed.password is not None:
        failures.append(f"{label} must not contain credentials")


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(first: str, second: str) -> float:
    high, low = sorted(
        (_relative_luminance(first), _relative_luminance(second)), reverse=True
    )
    return (high + 0.05) / (low + 0.05)


def validate_brand_color(
    value: Any,
    label: str,
    background: str,
    failures: list[str],
) -> None:
    if type(value) is not str or HEX_COLOR.fullmatch(value) is None:
        failures.append(f"{label} must be a six-digit hex color")
        return
    if _contrast_ratio(value, background) < 2:
        failures.append(f"{label} must have at least 2:1 contrast against {background}")


def validate_default_prompts(
    value: Any, label: str, failures: list[str]
) -> list[str] | None:
    if type(value) is str:
        prompts = [value]
    elif type(value) is list:
        prompts = value
    else:
        failures.append(f"{label} must be a string or an array of strings")
        return None
    if not prompts:
        failures.append(f"{label} must contain at least one prompt")
    if len(prompts) > CODEX_DEFAULT_PROMPT_MAX_ITEMS:
        failures.append(
            f"{label} must contain at most {CODEX_DEFAULT_PROMPT_MAX_ITEMS} prompts"
        )
    normalized: set[str] = set()
    for index, prompt in enumerate(prompts):
        prompt_label = f"{label}[{index}]"
        if type(prompt) is not str or not prompt.strip():
            failures.append(f"{prompt_label} must be a non-empty string")
            continue
        validate_single_line_text(
            prompt, prompt_label, CODEX_DEFAULT_PROMPT_MAX_CHARACTERS, failures
        )
        if APP_MENTION.search(prompt) is not None:
            failures.append(f"{prompt_label} must not contain an app @mention")
        normalized_prompt = " ".join(
            unicodedata.normalize("NFKC", prompt).split()
        ).casefold()
        if normalized_prompt in normalized:
            failures.append(f"{label} entries must be unique after normalization")
        normalized.add(normalized_prompt)
    return prompts


def resolve_declared_asset(
    repository_root: Path,
    raw_path: Any,
    label: str,
    failures: list[str],
) -> Path | None:
    if type(raw_path) is not str or not raw_path:
        failures.append(f"{label} must be a non-empty asset path")
        return None
    if raw_path != raw_path.strip() or _contains_unsupported_control(raw_path):
        failures.append(f"{label} must not contain outer whitespace or control characters")
        return None
    if not raw_path.startswith("./"):
        failures.append(f"{label} must start with './'")
        return None
    relative = raw_path[2:]
    if "\\" in relative:
        failures.append(f"{label} must use forward slashes")
        return None
    parts = relative.split("/")
    if not relative or any(part in {"", ".", ".."} for part in parts):
        failures.append(f"{label} must stay inside the plugin without empty or traversal segments")
        return None
    root = repository_root.resolve()
    candidate = root.joinpath(*parts)
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, ValueError):
        failures.append(f"{label} must stay inside the plugin")
        return None
    current = root
    try:
        for part in parts:
            current /= part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                failures.append(f"{label} must not traverse or reference a symlink")
                return None
    except OSError:
        failures.append(f"{label} must reference an existing regular file")
        return None
    if not stat.S_ISREG(mode):
        failures.append(f"{label} must reference a regular file, not a symlink or directory")
        return None
    return candidate


def _svg_number(value: str) -> float | None:
    if SVG_NUMBER.fullmatch(value) is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _svg_dimensions(
    root: ET.Element, label: str, failures: list[str]
) -> tuple[float, float] | None:
    view_box = root.get("viewBox")
    view_box_dimensions: tuple[float, float] | None = None
    if view_box is not None:
        raw_values = [item for item in re.split(r"[\s,]+", view_box.strip()) if item]
        values = [_svg_number(item) for item in raw_values]
        if len(values) != 4 or any(value is None for value in values):
            failures.append(f"{label} SVG viewBox must contain four numeric values")
        else:
            width = values[2]
            height = values[3]
            assert width is not None and height is not None
            if width <= 0 or height <= 0:
                failures.append(f"{label} SVG viewBox dimensions must be positive")
            else:
                view_box_dimensions = (width, height)

    width_raw = root.get("width")
    height_raw = root.get("height")
    intrinsic_dimensions: tuple[float, float] | None = None
    if (width_raw is None) != (height_raw is None):
        failures.append(f"{label} SVG width and height must be declared together")
    elif width_raw is not None and height_raw is not None:
        width = _svg_number(width_raw)
        height = _svg_number(height_raw)
        if width is None or height is None:
            failures.append(f"{label} SVG width and height must be numeric without units")
        elif width <= 0 or height <= 0:
            failures.append(f"{label} SVG width and height must be positive")
        else:
            intrinsic_dimensions = (width, height)

    if (
        view_box_dimensions is not None
        and intrinsic_dimensions is not None
        and not math.isclose(
            view_box_dimensions[0] / view_box_dimensions[1],
            intrinsic_dimensions[0] / intrinsic_dimensions[1],
        )
    ):
        failures.append(
            f"{label} SVG intrinsic dimensions and viewBox must have the same aspect ratio"
        )

    dimensions = intrinsic_dimensions or view_box_dimensions
    if dimensions is None:
        failures.append(f"{label} SVG must define a numeric viewBox or width and height")
        return None
    return dimensions


def _check_svg(data: bytes, label: str, failures: list[str]) -> tuple[float, float] | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        failures.append(f"{label} SVG must be valid UTF-8")
        return None
    lowered = text.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        failures.append(f"{label} SVG must not contain DTD or entity declarations")
        return None
    without_declaration = re.sub(
        r"\A\s*<\?xml\s+[^?]*\?>", "", text, count=1, flags=re.IGNORECASE
    )
    if "<?" in without_declaration:
        failures.append(f"{label} SVG must not contain processing instructions")
        return None
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        failures.append(f"{label} SVG is malformed XML: {error}")
        return None

    def split_name(name: str) -> tuple[str | None, str]:
        if name.startswith("{") and "}" in name:
            namespace, local = name[1:].split("}", 1)
            return namespace, local
        return None, name

    namespace, root_name = split_name(root.tag)
    if root_name != "svg" or namespace != SVG_NAMESPACE:
        failures.append(f"{label} SVG root must be the standard <svg> element")
        return None

    for element in root.iter():
        element_namespace, element_name = split_name(element.tag)
        if element_namespace != SVG_NAMESPACE:
            failures.append(f"{label} SVG must not contain foreign namespaces")
        if element_name not in SVG_ALLOWED_ELEMENTS:
            failures.append(f"{label} SVG contains unsafe or unsupported <{element_name}> content")
        for attribute, value in element.attrib.items():
            attribute_namespace, attribute_name = split_name(attribute)
            if attribute_namespace is not None:
                failures.append(f"{label} SVG must not contain foreign namespaces")
            lowered_name = attribute_name.lower()
            lowered_value = value.lower()
            if lowered_name.startswith("on") or lowered_name in {"href", "style"}:
                failures.append(f"{label} SVG contains unsafe {attribute_name!r} metadata")
            if (
                "javascript:" in lowered_value
                or "data:" in lowered_value
                or "http:" in lowered_value
                or "https:" in lowered_value
                or lowered_value.startswith("//")
                or re.search(r"url\s*\(", lowered_value) is not None
            ):
                failures.append(f"{label} SVG must not reference active or external content")
    return _svg_dimensions(root, label, failures)


def _check_png(data: bytes, label: str, failures: list[str]) -> tuple[int, int] | None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        failures.append(f"{label} extension does not match PNG content")
        return None
    position = 8
    dimensions: tuple[int, int] | None = None
    saw_idat = False
    saw_iend = False
    while position < len(data):
        if position + 12 > len(data):
            failures.append(f"{label} PNG has a truncated chunk")
            return None
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        end = position + 12 + length
        if end > len(data):
            failures.append(f"{label} PNG has a truncated chunk payload")
            return None
        chunk_data = data[position + 8 : position + 8 + length]
        expected_crc = struct.unpack(">I", data[position + 8 + length : end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            failures.append(f"{label} PNG has an invalid chunk checksum")
            return None
        if position == 8 and chunk_type != b"IHDR":
            failures.append(f"{label} PNG must begin with IHDR")
            return None
        if chunk_type == b"IHDR":
            if dimensions is not None or length != 13:
                failures.append(f"{label} PNG has an invalid IHDR")
                return None
            dimensions = struct.unpack(">II", chunk_data[:8])
        elif chunk_type == b"IDAT":
            saw_idat = True
        elif chunk_type == b"IEND":
            if length != 0 or end != len(data):
                failures.append(f"{label} PNG has an invalid IEND or trailing data")
                return None
            saw_iend = True
            break
        position = end
    if dimensions is None or not saw_idat or not saw_iend:
        failures.append(f"{label} PNG must contain IHDR, IDAT, and IEND")
        return None
    return dimensions


def _check_jpeg(data: bytes, label: str, failures: list[str]) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        failures.append(f"{label} extension does not match JPEG content")
        return None
    position = 2
    dimensions: tuple[int, int] | None = None
    saw_eoi = False
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while position < len(data):
        if data[position] != 0xFF:
            failures.append(f"{label} JPEG has malformed marker framing")
            return None
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            break
        marker = data[position]
        position += 1
        if marker == 0xD9:
            saw_eoi = position == len(data)
            break
        if marker in {0xD8, 0x01} or 0xD0 <= marker <= 0xD7:
            continue
        if position + 2 > len(data):
            failures.append(f"{label} JPEG has a truncated segment")
            return None
        length = struct.unpack(">H", data[position : position + 2])[0]
        if length < 2 or position + length > len(data):
            failures.append(f"{label} JPEG has an invalid segment length")
            return None
        segment = data[position + 2 : position + length]
        if marker in sof_markers:
            if len(segment) < 6:
                failures.append(f"{label} JPEG has a truncated frame header")
                return None
            height, width = struct.unpack(">HH", segment[1:5])
            dimensions = (width, height)
        position += length
        if marker == 0xDA:
            if len(data) < position + 2 or data[-2:] != b"\xff\xd9":
                failures.append(f"{label} JPEG is missing its final EOI marker")
                return None
            saw_eoi = True
            break
    if dimensions is None or not saw_eoi:
        failures.append(f"{label} JPEG must contain a frame header and final EOI marker")
        return None
    return dimensions


def _check_webp(data: bytes, label: str, failures: list[str]) -> tuple[int, int] | None:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        failures.append(f"{label} extension does not match WebP content")
        return None
    declared_size = struct.unpack("<I", data[4:8])[0] + 8
    if declared_size != len(data):
        failures.append(f"{label} WebP RIFF size does not match the file")
        return None
    position = 12
    dimensions: tuple[int, int] | None = None
    while position < len(data):
        if position + 8 > len(data):
            failures.append(f"{label} WebP has a truncated chunk")
            return None
        kind = data[position : position + 4]
        length = struct.unpack("<I", data[position + 4 : position + 8])[0]
        start = position + 8
        end = start + length
        padded_end = end + (length % 2)
        if padded_end > len(data):
            failures.append(f"{label} WebP has a truncated chunk payload")
            return None
        chunk = data[start:end]
        if kind == b"VP8X" and len(chunk) >= 10:
            width = 1 + int.from_bytes(chunk[4:7], "little")
            height = 1 + int.from_bytes(chunk[7:10], "little")
            dimensions = (width, height)
        elif kind == b"VP8L" and len(chunk) >= 5 and chunk[0] == 0x2F:
            width = 1 + (((chunk[2] & 0x3F) << 8) | chunk[1])
            height = 1 + ((chunk[4] << 6) | (chunk[3] >> 2))
            dimensions = (width, height)
        elif kind == b"VP8 " and len(chunk) >= 10 and chunk[3:6] == b"\x9d\x01\x2a":
            width = struct.unpack("<H", chunk[6:8])[0] & 0x3FFF
            height = struct.unpack("<H", chunk[8:10])[0] & 0x3FFF
            dimensions = (width, height)
        position = padded_end
    if dimensions is None:
        failures.append(f"{label} WebP must contain a supported VP8 frame header")
        return None
    return dimensions


def check_branding_image_file(path: Path, label: str, failures: list[str]) -> None:
    suffix = path.suffix.lower()
    if suffix not in BRANDING_IMAGE_EXTENSIONS:
        failures.append(f"{label} has an unsupported image extension {suffix!r}")
        return
    try:
        size = path.stat().st_size
        data = path.read_bytes()
    except OSError as error:
        failures.append(f"{label} cannot be read: {error}")
        return
    if size > BRANDING_IMAGE_MAX_BYTES:
        failures.append(f"{label} must not exceed 5 MiB")
        return
    if len(data) != size:
        failures.append(f"{label} changed while it was being validated")
        return

    if suffix == ".svg":
        dimensions = _check_svg(data, label, failures)
        raster = False
    elif suffix == ".png":
        dimensions = _check_png(data, label, failures)
        raster = True
    elif suffix in {".jpg", ".jpeg"}:
        dimensions = _check_jpeg(data, label, failures)
        raster = True
    else:
        dimensions = _check_webp(data, label, failures)
        raster = True
    if dimensions is None:
        return
    width, height = dimensions
    if width != height:
        failures.append(f"{label} must be square; found {width}x{height}")
    if width < BRANDING_IMAGE_MIN_DIMENSION or height < BRANDING_IMAGE_MIN_DIMENSION:
        failures.append(
            f"{label} must be at least {BRANDING_IMAGE_MIN_DIMENSION}x"
            f"{BRANDING_IMAGE_MIN_DIMENSION}"
        )
    if raster and (
        width > BRANDING_RASTER_MAX_DIMENSION or height > BRANDING_RASTER_MAX_DIMENSION
    ):
        failures.append(
            f"{label} raster dimensions must not exceed {BRANDING_RASTER_MAX_DIMENSION}x"
            f"{BRANDING_RASTER_MAX_DIMENSION}"
        )


def check_codex_listing_contract(
    interface: dict[str, Any], repository_root: Path, failures: list[str]
) -> None:
    label = ".codex-plugin/plugin.json.interface"
    validate_single_line_text(
        interface.get("displayName"),
        f"{label}.displayName",
        CODEX_DISPLAY_NAME_MAX_CHARACTERS,
        failures,
    )
    validate_single_line_text(
        interface.get("shortDescription"),
        f"{label}.shortDescription",
        CODEX_SHORT_DESCRIPTION_MAX_CHARACTERS,
        failures,
    )
    long_description = interface.get("longDescription")
    if type(long_description) is not str or not long_description.strip():
        failures.append(f"{label}.longDescription must be a non-empty string")
    elif len(long_description) > CODEX_LONG_DESCRIPTION_MAX_CHARACTERS:
        failures.append(
            f"{label}.longDescription must contain at most "
            f"{CODEX_LONG_DESCRIPTION_MAX_CHARACTERS} characters"
        )
    validate_single_line_text(
        interface.get("developerName"),
        f"{label}.developerName",
        CODEX_DEVELOPER_NAME_MAX_CHARACTERS,
        failures,
    )
    if interface.get("category") not in SUPPORTED_CODEX_CATEGORIES:
        failures.append(f"{label}.category is not a supported directory category")

    capabilities = interface.get("capabilities")
    if type(capabilities) is not list or not capabilities:
        failures.append(f"{label}.capabilities must be a non-empty array")
    else:
        if len(capabilities) > CODEX_CAPABILITY_MAX_ITEMS:
            failures.append(
                f"{label}.capabilities must contain at most {CODEX_CAPABILITY_MAX_ITEMS} entries"
            )
        for index, capability in enumerate(capabilities):
            validate_single_line_text(
                capability,
                f"{label}.capabilities[{index}]",
                CODEX_CAPABILITY_MAX_CHARACTERS,
                failures,
            )

    for field in ("websiteURL", "supportURL"):
        validate_https_url(interface.get(field), f"{label}.{field}", failures)
    validate_brand_color(interface.get("brandColor"), f"{label}.brandColor", "#FFFFFF", failures)
    validate_brand_color(
        interface.get("brandColorDark"),
        f"{label}.brandColorDark",
        "#212121",
        failures,
    )
    validate_default_prompts(interface.get("defaultPrompt"), f"{label}.defaultPrompt", failures)

    if "screenshots" in interface:
        failures.append(
            f"{label}.screenshots must remain absent because Axiom is a skills-only plugin "
            "without MCP custom UI"
        )

    validated_paths: set[Path] = set()
    for field in ("composerIcon", "logo"):
        asset_label = f"{label}.{field}"
        path = resolve_declared_asset(repository_root, interface.get(field), asset_label, failures)
        if path is not None and path not in validated_paths:
            check_branding_image_file(path, asset_label, failures)
            validated_paths.add(path)


def exact_single_plugin(
    document: dict[str, Any],
    label: str,
    expected_keys: frozenset[str],
    failures: list[str],
) -> dict[str, Any] | None:
    plugins = document.get("plugins")
    if type(plugins) is not list or len(plugins) != 1:
        failures.append(f"{label}.plugins must contain exactly one plugin object")
        return None
    return exact_json_object(plugins[0], f"{label}.plugins[0]", expected_keys, failures)


def check_manifest_capability_schema(
    documents: dict[str, dict[str, Any]],
    failures: list[str],
    repository_root: Path = REPOSITORY_ROOT,
) -> None:
    """Reject every manifest capability not owned by Axiom's current package contract."""
    codex_path = ".codex-plugin/plugin.json"
    codex = documents.get(codex_path)
    if codex is not None:
        exact_json_object(codex, codex_path, CODEX_MANIFEST_KEYS, failures)
        require_json_strings(
            codex,
            frozenset(
                {
                    "name",
                    "version",
                    "description",
                    "homepage",
                    "repository",
                    "license",
                    "skills",
                    "hooks",
                }
            ),
            codex_path,
            failures,
        )
        author = exact_json_object(
            codex.get("author"), f"{codex_path}.author", AUTHOR_KEYS, failures
        )
        if author is not None:
            require_json_strings(author, AUTHOR_KEYS, f"{codex_path}.author", failures)
        interface = exact_json_object(
            codex.get("interface"), f"{codex_path}.interface", CODEX_INTERFACE_KEYS, failures
        )
        if interface is not None:
            require_json_strings(
                interface,
                frozenset(CODEX_INTERFACE_KEYS - {"capabilities", "defaultPrompt"}),
                f"{codex_path}.interface",
                failures,
            )
            require_json_string_list(
                interface.get("capabilities"), f"{codex_path}.interface.capabilities", failures
            )
            if interface.get("capabilities") != ["Interactive"]:
                failures.append(
                    f"{codex_path}.interface.capabilities must remain ['Interactive']"
                )
            check_codex_listing_contract(interface, repository_root, failures)
        require_json_string_list(codex.get("keywords"), f"{codex_path}.keywords", failures)

    claude_path = ".claude-plugin/plugin.json"
    claude = documents.get(claude_path)
    if claude is not None:
        exact_json_object(claude, claude_path, CLAUDE_MANIFEST_KEYS, failures)
        require_json_strings(
            claude,
            frozenset(CLAUDE_MANIFEST_KEYS - {"author", "keywords"}),
            claude_path,
            failures,
        )
        author = exact_json_object(
            claude.get("author"), f"{claude_path}.author", AUTHOR_KEYS, failures
        )
        if author is not None:
            require_json_strings(author, AUTHOR_KEYS, f"{claude_path}.author", failures)
        require_json_string_list(claude.get("keywords"), f"{claude_path}.keywords", failures)

    codex_marketplace_path = ".agents/plugins/marketplace.json"
    codex_marketplace = documents.get(codex_marketplace_path)
    if codex_marketplace is not None:
        exact_json_object(
            codex_marketplace, codex_marketplace_path, CODEX_MARKETPLACE_KEYS, failures
        )
        require_json_strings(
            codex_marketplace, frozenset({"name"}), codex_marketplace_path, failures
        )
        interface = exact_json_object(
            codex_marketplace.get("interface"),
            f"{codex_marketplace_path}.interface",
            frozenset({"displayName"}),
            failures,
        )
        if interface is not None:
            require_json_strings(
                interface,
                frozenset({"displayName"}),
                f"{codex_marketplace_path}.interface",
                failures,
            )
        entry = exact_single_plugin(
            codex_marketplace,
            codex_marketplace_path,
            CODEX_MARKETPLACE_PLUGIN_KEYS,
            failures,
        )
        if entry is not None:
            require_json_strings(
                entry,
                frozenset({"name", "category"}),
                f"{codex_marketplace_path}.plugins[0]",
                failures,
            )
            source = exact_json_object(
                entry.get("source"),
                f"{codex_marketplace_path}.plugins[0].source",
                frozenset({"source", "path"}),
                failures,
            )
            if source is not None:
                require_json_strings(
                    source,
                    frozenset({"source", "path"}),
                    f"{codex_marketplace_path}.plugins[0].source",
                    failures,
                )
                if source != {"source": "local", "path": EXPECTED_PLUGIN_ROOT}:
                    failures.append(
                        f"{codex_marketplace_path}.plugins[0].source must remain the "
                        "owned local plugin root"
                    )
            policy = exact_json_object(
                entry.get("policy"),
                f"{codex_marketplace_path}.plugins[0].policy",
                frozenset(EXPECTED_CODEX_POLICY),
                failures,
            )
            if policy is not None:
                require_json_strings(
                    policy,
                    frozenset(EXPECTED_CODEX_POLICY),
                    f"{codex_marketplace_path}.plugins[0].policy",
                    failures,
                )
                if policy != EXPECTED_CODEX_POLICY:
                    failures.append(
                        f"{codex_marketplace_path}.plugins[0].policy must remain the "
                        "owned install policy"
                    )

    claude_marketplace_path = ".claude-plugin/marketplace.json"
    claude_marketplace = documents.get(claude_marketplace_path)
    if claude_marketplace is not None:
        exact_json_object(
            claude_marketplace,
            claude_marketplace_path,
            CLAUDE_MARKETPLACE_KEYS,
            failures,
        )
        require_json_strings(
            claude_marketplace,
            frozenset({"name", "description"}),
            claude_marketplace_path,
            failures,
        )
        owner = exact_json_object(
            claude_marketplace.get("owner"),
            f"{claude_marketplace_path}.owner",
            AUTHOR_KEYS,
            failures,
        )
        if owner is not None:
            require_json_strings(
                owner, AUTHOR_KEYS, f"{claude_marketplace_path}.owner", failures
            )
        entry = exact_single_plugin(
            claude_marketplace,
            claude_marketplace_path,
            CLAUDE_MARKETPLACE_PLUGIN_KEYS,
            failures,
        )
        if entry is not None:
            require_json_strings(
                entry,
                frozenset({"name", "source", "category"}),
                f"{claude_marketplace_path}.plugins[0]",
                failures,
            )
            require_json_string_list(
                entry.get("tags"),
                f"{claude_marketplace_path}.plugins[0].tags",
                failures,
            )


def check_manifest_versions(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    versions: dict[str, str] = {}
    for relative_path in MANIFEST_FILES:
        document = documents.get(relative_path)
        if document is None:
            continue
        version = document.get("version")
        if not isinstance(version, str):
            failures.append(f"{relative_path} must declare a string version")
            continue
        versions[relative_path] = version
        if parse_production_release_version(version) is None:
            failures.append(
                f"{relative_path} version {version!r} is not a stable numeric "
                "production release version"
            )

    if len(versions) == len(MANIFEST_FILES) and len(set(versions.values())) != 1:
        rendered = ", ".join(f"{path}={version!r}" for path, version in versions.items())
        failures.append(f"plugin manifest versions disagree: {rendered}")

    for relative_path, version in versions.items():
        if version != RELEASE_VERSION:
            failures.append(
                f"{relative_path} version is {version!r}; publication requires {RELEASE_VERSION!r}"
            )


def check_codex_interface(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    relative_path = ".codex-plugin/plugin.json"
    document = documents.get(relative_path)
    if document is None:
        return
    interface = document.get("interface")
    if not isinstance(interface, dict):
        failures.append(f"{relative_path} interface must be an object")
        return
    for field, expected in EXPECTED_CODEX_INTERFACE.items():
        if interface.get(field) != expected:
            failures.append(
                f"{relative_path} interface.{field} must remain {expected!r}"
            )


def marketplace_plugin(
    document: dict[str, Any], relative_path: str, failures: list[str]
) -> dict[str, Any] | None:
    plugins = document.get("plugins")
    if not isinstance(plugins, list):
        failures.append(f"{relative_path} must contain a plugins array")
        return None
    matches = [
        entry
        for entry in plugins
        if isinstance(entry, dict) and entry.get("name") == "axiom"
    ]
    if len(matches) != 1:
        failures.append(
            f"{relative_path} must contain exactly one 'axiom' plugin entry, found {len(matches)}"
        )
        return None
    return matches[0]


def check_distribution_identity(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    codex_manifest_path = ".codex-plugin/plugin.json"
    codex_manifest = documents.get(codex_manifest_path)
    if codex_manifest is not None:
        if codex_manifest.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(f"{codex_manifest_path} name must be {EXPECTED_PLUGIN_NAME!r}")
        if codex_manifest.get("description") != EXPECTED_TAGLINE:
            failures.append(f"{codex_manifest_path} description must be {EXPECTED_TAGLINE!r}")
        interface = codex_manifest.get("interface")
        if isinstance(interface, dict):
            if interface.get("displayName") != EXPECTED_DISPLAY_NAME:
                failures.append(
                    f"{codex_manifest_path} interface.displayName must be {EXPECTED_DISPLAY_NAME!r}"
                )
            if interface.get("category") != EXPECTED_CODEX_CATEGORY:
                failures.append(
                    f"{codex_manifest_path} interface.category must be {EXPECTED_CODEX_CATEGORY!r}"
                )

    claude_manifest_path = ".claude-plugin/plugin.json"
    claude_manifest = documents.get(claude_manifest_path)
    if claude_manifest is not None:
        if claude_manifest.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(f"{claude_manifest_path} name must be {EXPECTED_PLUGIN_NAME!r}")
        if claude_manifest.get("displayName") != EXPECTED_DISPLAY_NAME:
            failures.append(
                f"{claude_manifest_path} displayName must be {EXPECTED_DISPLAY_NAME!r}"
            )
        if claude_manifest.get("description") != EXPECTED_TAGLINE:
            failures.append(f"{claude_manifest_path} description must be {EXPECTED_TAGLINE!r}")

    codex_marketplace_path = ".agents/plugins/marketplace.json"
    codex_marketplace = documents.get(codex_marketplace_path)
    if codex_marketplace is not None:
        if codex_marketplace.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(
                f"{codex_marketplace_path} name must be {EXPECTED_PLUGIN_NAME!r}"
            )
        interface = codex_marketplace.get("interface")
        if not isinstance(interface, dict) or interface.get("displayName") != EXPECTED_DISPLAY_NAME:
            failures.append(
                f"{codex_marketplace_path} interface.displayName must be {EXPECTED_DISPLAY_NAME!r}"
            )
        entry = marketplace_plugin(codex_marketplace, codex_marketplace_path, failures)
        if entry is not None:
            if entry.get("policy") != EXPECTED_CODEX_POLICY:
                failures.append(
                    f"{codex_marketplace_path} axiom policy must be {EXPECTED_CODEX_POLICY!r}"
                )
            if entry.get("category") != EXPECTED_CODEX_CATEGORY:
                failures.append(
                    f"{codex_marketplace_path} axiom category must be {EXPECTED_CODEX_CATEGORY!r}"
                )

    claude_marketplace_path = ".claude-plugin/marketplace.json"
    claude_marketplace = documents.get(claude_marketplace_path)
    if claude_marketplace is not None:
        if claude_marketplace.get("name") != EXPECTED_PLUGIN_NAME:
            failures.append(
                f"{claude_marketplace_path} name must be {EXPECTED_PLUGIN_NAME!r}"
            )
        entry = marketplace_plugin(claude_marketplace, claude_marketplace_path, failures)
        if entry is not None and entry.get("category") != EXPECTED_CLAUDE_CATEGORY:
            failures.append(
                f"{claude_marketplace_path} axiom category must be {EXPECTED_CLAUDE_CATEGORY!r}"
            )


def check_shared_source_roots(
    documents: dict[str, dict[str, Any]], failures: list[str]
) -> None:
    for manifest_path in MANIFEST_FILES:
        document = documents.get(manifest_path)
        if document is None:
            continue
        skills = document.get("skills")
        if skills != EXPECTED_SKILLS_ROOT:
            failures.append(
                f"{manifest_path} skills is {skills!r}; expected the shared source "
                f"{EXPECTED_SKILLS_ROOT!r}"
            )

    codex_path = ".agents/plugins/marketplace.json"
    codex_document = documents.get(codex_path)
    if codex_document is not None:
        entry = marketplace_plugin(codex_document, codex_path, failures)
        if entry is not None:
            source = entry.get("source")
            if not isinstance(source, dict):
                failures.append(f"{codex_path} axiom source must be an object")
            elif source.get("path") != EXPECTED_PLUGIN_ROOT:
                failures.append(
                    f"{codex_path} axiom source.path is {source.get('path')!r}; "
                    f"expected shared plugin root {EXPECTED_PLUGIN_ROOT!r}"
                )

    claude_path = ".claude-plugin/marketplace.json"
    claude_document = documents.get(claude_path)
    if claude_document is not None:
        entry = marketplace_plugin(claude_document, claude_path, failures)
        if entry is not None and entry.get("source") != EXPECTED_PLUGIN_ROOT:
            failures.append(
                f"{claude_path} axiom source is {entry.get('source')!r}; "
                f"expected shared plugin root {EXPECTED_PLUGIN_ROOT!r}"
            )
