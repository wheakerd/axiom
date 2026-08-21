"""Plugin manifest and marketplace policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context import RELEASE_VERSION, REPOSITORY_ROOT, STRICT_SEMVER, display_path

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
CODEX_INTERFACE_KEYS = frozenset(
    {
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "defaultPrompt",
        "brandColor",
    }
)
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
    documents: dict[str, dict[str, Any]], failures: list[str]
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
        author = exact_json_object(codex.get("author"), f"{codex_path}.author", AUTHOR_KEYS, failures)
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
            require_json_string_list(
                interface.get("defaultPrompt"), f"{codex_path}.interface.defaultPrompt", failures
            )
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
        if STRICT_SEMVER.fullmatch(version) is None:
            failures.append(
                f"{relative_path} version {version!r} is not strict SemVer"
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
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list):
        failures.append(f"{relative_path} interface.defaultPrompt must be an array")
        return
    if not 1 <= len(prompts) <= CODEX_DEFAULT_PROMPT_MAX_ITEMS:
        failures.append(
            f"{relative_path} interface.defaultPrompt must contain 1-"
            f"{CODEX_DEFAULT_PROMPT_MAX_ITEMS} entries; found {len(prompts)}"
        )
    for index, prompt in enumerate(prompts):
        label = f"{relative_path} interface.defaultPrompt[{index}]"
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{label} must be a non-empty string")
        elif len(prompt) > CODEX_DEFAULT_PROMPT_MAX_CHARACTERS:
            failures.append(
                f"{label} is {len(prompt)} characters; Codex caps starter prompts at "
                f"{CODEX_DEFAULT_PROMPT_MAX_CHARACTERS}"
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
