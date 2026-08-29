"""GitHub Actions graph and pull-request validation policy."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

from .context import REPOSITORY_ROOT, display_path
from .yaml_subset import (
    ActionUse,
    CanonicalYamlError,
    CanonicalYamlScalar,
    parse_canonical_yaml_document,
)


DOCKER_NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
DOCKER_DOMAIN_COMPONENT = (
    r"(?:[A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9-]*[A-Za-z0-9])"
)
DOCKER_DOMAIN = rf"{DOCKER_DOMAIN_COMPONENT}(?:\.{DOCKER_DOMAIN_COMPONENT})*(?::[0-9]+)?"
DOCKER_IMAGE_DIGEST_PATTERN = re.compile(
    rf"^(?:{DOCKER_DOMAIN}/)?{DOCKER_NAME_COMPONENT}"
    rf"(?:/{DOCKER_NAME_COMPONENT})*"
    r"(?::[A-Za-z0-9_][A-Za-z0-9_.-]{0,127})?"
    r"@sha256:[0-9a-fA-F]{64}$"
)
DOCKER_REPOSITORY_NAME_MAX_LENGTH = 255
DOCKER_STAGE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
DOCKER_PLATFORM_PATTERN = re.compile(
    r"^--platform=[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$"
)
DOCKER_PARSER_DIRECTIVE_PATTERN = re.compile(
    r"^[ \t]*#[ \t]*(?:escape|syntax|check)[ \t]*=",
    re.IGNORECASE,
)
DOCKER_REMOTE_ADD_SOURCE_PATTERN = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9+.-]*://|[^/@\s]+@[^:/\s]+:)"
)
DOCKERFILE_INSTRUCTIONS = frozenset(
    {
        "add",
        "arg",
        "cmd",
        "copy",
        "entrypoint",
        "env",
        "expose",
        "from",
        "healthcheck",
        "label",
        "maintainer",
        "onbuild",
        "run",
        "shell",
        "stopsignal",
        "user",
        "volume",
        "workdir",
    }
)


@dataclass(frozen=True)
class DockerfilePinCounts:
    base_images: int
    other_inputs: int

    @property
    def total(self) -> int:
        return self.base_images + self.other_inputs


@dataclass(frozen=True)
class ActionGraphPinCounts:
    total: int
    dockerfile_base_images: int
    dockerfile_other_inputs: int


def walk_yaml_uses(
    value: Any,
    path: tuple[str | int, ...] = (),
) -> Iterator[tuple[tuple[str | int, ...], Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = (*path, key)
            if key == "uses":
                yield child_path, child
            yield from walk_yaml_uses(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_yaml_uses(child, (*path, index))


def workflow_uses_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    allowed_paths: set[tuple[str | int, ...]] = set()
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        failures.append(f"{label} must contain a jobs mapping")
        return declarations

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            failures.append(f"{label} jobs.{job_name} must be a mapping")
            continue
        if "uses" in job:
            path = ("jobs", job_name, "uses")
            allowed_paths.add(path)
            scalar = job["uses"]
            if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                failures.append(f"{label} jobs.{job_name}.uses must be a non-empty scalar")
            else:
                declarations.append(
                    ActionUse(scalar.value, scalar.comment, scalar.line, "workflow-job")
                )
        steps = job.get("steps")
        if steps is None:
            continue
        if not isinstance(steps, list):
            failures.append(f"{label} jobs.{job_name}.steps must be a sequence")
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                failures.append(f"{label} jobs.{job_name}.steps[{index}] must be a mapping")
                continue
            if "uses" not in step:
                continue
            path = ("jobs", job_name, "steps", index, "uses")
            allowed_paths.add(path)
            scalar = step["uses"]
            if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                failures.append(
                    f"{label} jobs.{job_name}.steps[{index}].uses must be a non-empty scalar"
                )
            else:
                declarations.append(
                    ActionUse(scalar.value, scalar.comment, scalar.line, "workflow-step")
                )

    for path, scalar in walk_yaml_uses(document):
        if path not in allowed_paths:
            line = scalar.line if isinstance(scalar, CanonicalYamlScalar) else "?"
            failures.append(
                f"{label}:{line} uses is outside jobs.<job>.uses or jobs.<job>.steps[*].uses"
            )
    return declarations


def workflow_container_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return declarations

    def append_image(value: Any, image_label: str) -> None:
        if not isinstance(value, CanonicalYamlScalar) or not value.value:
            failures.append(f"{label} {image_label} must be a non-empty scalar")
            return
        declarations.append(
            ActionUse(value.value, value.comment, value.line, "workflow-container")
        )

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        container = job.get("container")
        if container is not None:
            if isinstance(container, CanonicalYamlScalar):
                append_image(container, f"jobs.{job_name}.container")
            elif isinstance(container, dict):
                append_image(
                    container.get("image"), f"jobs.{job_name}.container.image"
                )
            else:
                failures.append(
                    f"{label} jobs.{job_name}.container must be an image scalar or mapping"
                )
        services = job.get("services")
        if services is None:
            continue
        if not isinstance(services, dict):
            failures.append(f"{label} jobs.{job_name}.services must be a mapping")
            continue
        for service_name, service in services.items():
            if not isinstance(service, dict):
                failures.append(
                    f"{label} jobs.{job_name}.services.{service_name} must be a mapping"
                )
                continue
            append_image(
                service.get("image"),
                f"jobs.{job_name}.services.{service_name}.image",
            )
    return declarations


def action_uses_declarations(
    document: dict[str, Any],
    label: str,
    failures: list[str],
) -> list[ActionUse]:
    declarations: list[ActionUse] = []
    allowed_paths: set[tuple[str | int, ...]] = set()
    runs = document.get("runs")
    if not isinstance(runs, dict):
        failures.append(f"{label} must contain a runs mapping")
        return declarations
    steps = runs.get("steps")
    if steps is not None:
        if not isinstance(steps, list):
            failures.append(f"{label} runs.steps must be a sequence")
        else:
            for index, step in enumerate(steps):
                if not isinstance(step, dict):
                    failures.append(f"{label} runs.steps[{index}] must be a mapping")
                    continue
                if "uses" not in step:
                    continue
                path = ("runs", "steps", index, "uses")
                allowed_paths.add(path)
                scalar = step["uses"]
                if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
                    failures.append(
                        f"{label} runs.steps[{index}].uses must be a non-empty scalar"
                    )
                else:
                    declarations.append(
                        ActionUse(scalar.value, scalar.comment, scalar.line, "action-step")
                    )

    for path, scalar in walk_yaml_uses(document):
        if path not in allowed_paths:
            line = scalar.line if isinstance(scalar, CanonicalYamlScalar) else "?"
            failures.append(f"{label}:{line} uses is outside runs.steps[*].uses")
    return declarations


def canonical_local_path(raw: str, label: str, failures: list[str]) -> PurePosixPath | None:
    if raw == "./":
        return PurePosixPath(".")
    if (
        not raw.startswith("./")
        or raw.startswith(".//")
        or "\\" in raw
        or "\x00" in raw
        or any(character in raw for character in "?#@")
        or re.fullmatch(r"\./[A-Za-z0-9._/-]+", raw) is None
    ):
        failures.append(f"{label} local uses path {raw!r} is ambiguous or non-canonical")
        return None
    tail = raw[2:]
    pure = PurePosixPath(tail)
    if (
        not tail
        or pure.is_absolute()
        or pure.as_posix() != tail
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        failures.append(f"{label} local uses path {raw!r} contains traversal or ambiguity")
        return None
    return pure


def contained_path(
    root: Path,
    relative: PurePosixPath,
    label: str,
    failures: list[str],
) -> Path | None:
    resolved_root = root.resolve()
    candidate = (resolved_root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError:
        failures.append(f"{label} resolves outside the repository: {relative.as_posix()!r}")
        return None
    return candidate


def local_action_metadata(
    root: Path,
    raw: str,
    label: str,
    failures: list[str],
) -> Path | None:
    relative = canonical_local_path(raw, label, failures)
    if relative is None:
        return None
    directory = contained_path(root, relative, label, failures)
    if directory is None:
        return None
    if not directory.is_dir():
        failures.append(f"{label} local action directory does not exist: {raw!r}")
        return None
    candidates = [
        path
        for path in (directory / "action.yml", directory / "action.yaml")
        if path.is_file()
    ]
    if len(candidates) != 1:
        failures.append(
            f"{label} local action {raw!r} must contain exactly one action.yml or action.yaml; "
            f"found {len(candidates)}"
        )
        return None
    metadata = candidates[0].resolve()
    try:
        metadata.relative_to(root.resolve())
        metadata.relative_to(directory)
    except ValueError:
        failures.append(f"{label} local action metadata escapes its repository directory")
        return None
    return metadata


def local_action_file(
    root: Path,
    action_directory: Path,
    raw: str,
    label: str,
    failures: list[str],
    *,
    reject_symlink: bool = False,
) -> Path | None:
    candidate_raw = raw if raw.startswith("./") else f"./{raw}"
    relative = canonical_local_path(candidate_raw, label, failures)
    if relative is None:
        return None
    lexical_candidate = action_directory / Path(*relative.parts)
    if reject_symlink and lexical_candidate.is_symlink():
        failures.append(
            f"{label} local action file must not be a symbolic link: {raw!r}"
        )
        return None
    candidate = lexical_candidate.resolve()
    try:
        candidate.relative_to(root.resolve())
        candidate.relative_to(action_directory.resolve())
    except ValueError:
        failures.append(f"{label} local action file escapes its action directory: {raw!r}")
        return None
    if not candidate.is_file():
        failures.append(f"{label} local action file does not exist: {raw!r}")
        return None
    return candidate


def strip_dockerfile_comment(line: str) -> str:
    """Remove Dockerfile comment lines while retaining inline hash data."""
    return "" if line.lstrip(" \t").startswith("#") else line


def is_digest_pinned_docker_source(source: str) -> bool:
    """Accept a bounded Docker reference with one exact SHA-256 digest."""
    if DOCKER_IMAGE_DIGEST_PATTERN.fullmatch(source) is None:
        return False
    name_and_tag = source.rsplit("@", 1)[0]
    last_slash = name_and_tag.rfind("/")
    last_colon = name_and_tag.rfind(":")
    name = name_and_tag[:last_colon] if last_colon > last_slash else name_and_tag
    first, separator, remainder = name.partition("/")
    has_domain = separator and (
        "." in first
        or ":" in first
        or first == "localhost"
        or first.lower() != first
    )
    repository_name = remainder if has_domain else name
    return len(repository_name) <= DOCKER_REPOSITORY_NAME_MAX_LENGTH


def dockerfile_logical_lines(
    text: str,
    label: str,
    failures: list[str],
) -> list[tuple[int, str]]:
    """Join the default Dockerfile escape continuation without interpreting shell."""
    logical_lines: list[tuple[int, str]] = []
    continued: list[str] = []
    continued_from: int | None = None

    if "\x00" in text or text.startswith("\ufeff"):
        failures.append(f"{label} contains an unsupported NUL byte or byte-order mark")

    for line_number, physical_line in enumerate(text.splitlines(), start=1):
        if DOCKER_PARSER_DIRECTIVE_PATTERN.match(physical_line):
            failures.append(
                f"{label}:{line_number} uses an unsupported Dockerfile parser directive"
            )
        commentless = strip_dockerfile_comment(physical_line)
        if not commentless:
            continue
        content = commentless.rstrip(" \t")
        content_backslashes = len(content) - len(content.rstrip("\\"))
        if commentless != content and content_backslashes == 1:
            failures.append(
                f"{label}:{line_number} has whitespace after a Dockerfile line continuation"
            )
            continued = []
            continued_from = None
            continue
        trailing_backslashes = len(content) - len(content.rstrip("\\"))
        has_continuation = trailing_backslashes == 1

        if has_continuation:
            segment = content[:-1]
            if not segment.strip():
                failures.append(
                    f"{label}:{line_number} has a malformed Dockerfile line continuation"
                )
                continued = []
                continued_from = None
                continue
            if continued_from is None:
                continued_from = line_number
                segment = segment.lstrip(" \t")
            continued.append(segment)
            continue

        segment = content
        if continued:
            if not segment.strip():
                failures.append(
                    f"{label}:{line_number} has a malformed Dockerfile line continuation"
                )
            else:
                continued.append(segment)
                logical_lines.append(
                    (continued_from or line_number, "".join(continued).strip())
                )
            continued = []
            continued_from = None
        elif segment.strip():
            logical_lines.append((line_number, segment.strip()))

    if continued:
        failures.append(
            f"{label}:{continued_from or '?'} has an unterminated Dockerfile line continuation"
        )
    return logical_lines


def docker_source_kind(
    source: str,
    stages: set[str],
    instruction: str,
    location: str,
    failures: list[str],
    *,
    allow_scratch: bool = False,
) -> str | None:
    """Classify one literal stage or digest-pinned image source."""
    if not source or any(character in source for character in "$'\"`"):
        failures.append(
            f"{location} {instruction} variables, expressions, and quoted "
            "values are unsupported"
        )
        return None

    source_key = source.casefold()
    if allow_scratch and source_key == "scratch":
        return "scratch"
    if source_key in stages:
        return "stage"
    if is_digest_pinned_docker_source(source):
        return "remote"
    failures.append(
        f"{location} remote {instruction} source {source!r} must use "
        "@sha256:<64 hex> or reference a previously validated stage"
    )
    return None


def canonical_docker_local_source(
    raw: str,
    instruction: str,
    location: str,
    failures: list[str],
) -> PurePosixPath | None:
    """Accept one literal source relative to the local action directory."""
    if raw == ".":
        return PurePosixPath(".")
    tail = raw[2:] if raw.startswith("./") else raw
    if (
        not tail
        or raw.startswith("/")
        or raw.startswith(".//")
        or "\\" in raw
        or "\x00" in raw
        or re.fullmatch(r"[A-Za-z0-9._/-]+", tail) is None
    ):
        failures.append(
            f"{location} {instruction} local source {raw!r} uses traversal, "
            "expansion, or unsupported path syntax"
        )
        return None
    relative = PurePosixPath(tail)
    if (
        relative.is_absolute()
        or relative.as_posix() != tail
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        failures.append(
            f"{location} {instruction} local source {raw!r} uses traversal, "
            "expansion, or unsupported path syntax"
        )
        return None
    return relative


def check_docker_local_source(
    action_directory: Path,
    relative: PurePosixPath,
    raw: str,
    instruction: str,
    location: str,
    failures: list[str],
) -> bool:
    """Require a contained ordinary source tree without symbolic links."""
    root = action_directory.resolve()
    lexical = root / Path(*relative.parts)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            failures.append(
                f"{location} {instruction} local source {raw!r} must not use "
                "a symbolic link"
            )
            return False

    candidate = lexical.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        failures.append(
            f"{location} {instruction} local source {raw!r} resolves outside "
            "the action directory"
        )
        return False
    if not candidate.exists():
        failures.append(
            f"{location} {instruction} local source {raw!r} does not exist "
            "in the action directory"
        )
        return False
    if not candidate.is_file() and not candidate.is_dir():
        failures.append(
            f"{location} {instruction} local source {raw!r} is not an ordinary "
            "file or directory"
        )
        return False
    if candidate.is_file():
        return True

    try:
        descendants = candidate.rglob("*")
        for descendant in descendants:
            relative_descendant = descendant.relative_to(root).as_posix()
            if descendant.is_symlink():
                failures.append(
                    f"{location} {instruction} local source {raw!r} contains "
                    f"symbolic link {relative_descendant!r}"
                )
                return False
            if not descendant.is_file() and not descendant.is_dir():
                failures.append(
                    f"{location} {instruction} local source {raw!r} contains "
                    f"non-ordinary entry {relative_descendant!r}"
                )
                return False
    except OSError as error:
        failures.append(
            f"{location} cannot inspect {instruction} local source {raw!r}: {error}"
        )
        return False
    return True


def check_docker_copy_or_add(
    arguments: str | None,
    instruction: str,
    stages: set[str],
    action_directory: Path,
    location: str,
    failures: list[str],
) -> int:
    """Validate bounded COPY or ADD syntax and return non-base remote pins."""
    tokens = arguments.split() if arguments is not None else []
    if not tokens:
        failures.append(f"{location} {instruction} must name a source and destination")
        return 0
    if any(
        any(character in token for character in "$'\"`\\") for token in tokens
    ):
        failures.append(
            f"{location} {instruction} variables, expressions, quoted values, "
            "and escapes are unsupported"
        )
        return 0

    from_source: str | None = None
    invalid_flag = False
    while tokens and tokens[0].startswith("--"):
        flag = tokens.pop(0)
        if instruction == "COPY" and flag.startswith("--from="):
            if from_source is not None:
                failures.append(f"{location} COPY repeats the --from flag")
                invalid_flag = True
            else:
                from_source = flag.removeprefix("--from=")
        else:
            failures.append(
                f"{location} {instruction} uses unsupported or noncanonical flag {flag!r}"
            )
            invalid_flag = True
    if invalid_flag:
        return 0
    if len(tokens) < 2:
        failures.append(f"{location} {instruction} must name a source and destination")
        return 0
    if any(token.startswith("--") for token in tokens):
        failures.append(f"{location} {instruction} has a misplaced instruction flag")
        return 0

    sources = tokens[:-1]
    if from_source is not None:
        if any(any(character in source for character in "*?[]{}") for source in sources):
            failures.append(
                f"{location} COPY --from uses unsupported source expansion"
            )
            return 0
        source_kind = docker_source_kind(
            from_source,
            stages,
            "COPY --from",
            location,
            failures,
        )
        return int(source_kind == "remote")

    for source in sources:
        if instruction == "ADD" and DOCKER_REMOTE_ADD_SOURCE_PATTERN.match(source):
            failures.append(
                f"{location} ADD remote URL or Git source {source!r} is prohibited"
            )
            continue
        relative = canonical_docker_local_source(
            source,
            instruction,
            location,
            failures,
        )
        if relative is not None:
            check_docker_local_source(
                action_directory,
                relative,
                source,
                instruction,
                location,
                failures,
            )
    return 0


def check_docker_run_mount(
    arguments: str | None,
    stages: set[str],
    location: str,
    failures: list[str],
) -> int:
    """Validate the bounded RUN --mount=from form and return remote pins."""
    tokens = arguments.split() if arguments is not None else []
    if not tokens:
        failures.append(f"{location} RUN must name a command")
        return 0

    flags: list[str] = []
    while tokens and tokens[0].startswith("--"):
        flags.append(tokens.pop(0))
    if not flags:
        return 0
    if not tokens:
        failures.append(f"{location} RUN flags must be followed by a command")
        return 0
    if len(flags) != 1:
        failures.append(
            f"{location} RUN uses duplicate or multiple Dockerfile flags"
        )
        return 0

    flag = flags[0]
    if not flag.startswith("--mount="):
        failures.append(
            f"{location} RUN uses unsupported or noncanonical flag {flag!r}"
        )
        return 0
    raw_options = flag.removeprefix("--mount=")
    if not raw_options or any(
        character in raw_options for character in "$'\"`\\"
    ):
        failures.append(
            f"{location} RUN --mount variables, expressions, quoted values, "
            "and escapes are unsupported"
        )
        return 0

    aliases = {
        "destination": "target",
        "dst": "target",
        "readwrite": "rw",
        "readonly": "ro",
        "src": "source",
    }
    options: dict[str, str | None] = {}
    invalid_option = False
    for raw_option in raw_options.split(","):
        if not raw_option:
            failures.append(f"{location} RUN --mount contains an empty option")
            invalid_option = True
            continue
        key, separator, value = raw_option.partition("=")
        if key != key.casefold():
            failures.append(
                f"{location} RUN --mount option {key!r} is noncanonical"
            )
            invalid_option = True
            continue
        key = aliases.get(key, key)
        if key not in {"type", "from", "source", "target", "ro", "rw"}:
            failures.append(
                f"{location} RUN --mount uses unsupported option {key!r}"
            )
            invalid_option = True
            continue
        if key in options:
            failures.append(f"{location} RUN --mount repeats option {key!r}")
            invalid_option = True
            continue
        if key in {"ro", "rw"}:
            if separator:
                failures.append(
                    f"{location} RUN --mount boolean option {key!r} must not have a value"
                )
                invalid_option = True
                continue
            options[key] = None
        else:
            if not separator or not value:
                failures.append(
                    f"{location} RUN --mount option {key!r} must have one literal value"
                )
                invalid_option = True
                continue
            options[key] = value
    if invalid_option:
        return 0
    if options.get("type", "bind") != "bind":
        failures.append(f"{location} RUN --mount supports only type=bind")
        return 0
    if "ro" in options and "rw" in options:
        failures.append(f"{location} RUN --mount cannot combine ro and rw")
        return 0
    from_source = options.get("from")
    if not isinstance(from_source, str):
        failures.append(
            f"{location} RUN --mount must name one explicit from source"
        )
        return 0
    for key in ("source", "target"):
        value = options.get(key)
        if isinstance(value, str) and any(
            character in value for character in "$'\"`\\"
        ):
            failures.append(
                f"{location} RUN --mount option {key!r} must be literal"
            )
            return 0
    source_kind = docker_source_kind(
        from_source,
        stages,
        "RUN --mount=from",
        location,
        failures,
    )
    return int(source_kind == "remote")


def check_dockerfile_inputs(
    path: Path,
    label: str,
    failures: list[str],
) -> DockerfilePinCounts:
    """Validate every declared source in one referenced local Docker action."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        failures.append(f"cannot read {label}: {error}")
        return DockerfilePinCounts(0, 0)

    stages: set[str] = set()
    from_count = 0
    current_stage_is_valid = False
    base_image_pins = 0
    other_input_pins = 0
    logical_lines = dockerfile_logical_lines(
        text,
        label,
        failures,
    )
    for line_number, logical_line in logical_lines:
        if "<<" in logical_line:
            failures.append(
                f"{label}:{line_number} uses unsupported Dockerfile heredoc syntax"
            )
            return DockerfilePinCounts(0, 0)

    for line_number, logical_line in logical_lines:
        location = f"{label}:{line_number}"
        instruction_match = re.fullmatch(
            r"([A-Za-z]+)(?:[ \t]+(.*))?",
            logical_line,
        )
        if instruction_match is None:
            failures.append(f"{location} has malformed Dockerfile instruction syntax")
            continue
        instruction, arguments = instruction_match.groups()
        instruction_key = instruction.casefold()
        if instruction_key not in DOCKERFILE_INSTRUCTIONS:
            failures.append(
                f"{location} uses unsupported Dockerfile instruction {instruction!r}"
            )
            continue
        if instruction_key == "onbuild":
            failures.append(
                f"{location} uses unsupported ONBUILD deferred input context"
            )
            continue
        if instruction_key != "from":
            if instruction_key == "arg":
                continue
            if not current_stage_is_valid:
                failures.append(
                    f"{location} {instruction.upper()} must follow a validated FROM"
                )
                continue
            if instruction_key in {"copy", "add"}:
                other_input_pins += check_docker_copy_or_add(
                    arguments,
                    instruction_key.upper(),
                    stages,
                    path.parent,
                    location,
                    failures,
                )
            elif instruction_key == "run":
                other_input_pins += check_docker_run_mount(
                    arguments,
                    stages,
                    location,
                    failures,
                )
            continue

        from_count += 1
        current_stage_is_valid = False
        tokens = arguments.split() if arguments is not None else []
        if not tokens:
            failures.append(f"{location} FROM must name one immutable source")
            continue
        if any(
            any(character in token for character in "$'\"`")
            for token in tokens
        ):
            failures.append(
                f"{location} FROM variables, expressions, and quoted values "
                "are unsupported"
            )
            continue

        if tokens[0].startswith("--"):
            if DOCKER_PLATFORM_PATTERN.fullmatch(tokens[0]) is None:
                failures.append(
                    f"{location} FROM uses an unsupported or variable platform selector"
                )
                continue
            tokens = tokens[1:]
        if len(tokens) not in {1, 3} or (
            len(tokens) == 3 and tokens[1].casefold() != "as"
        ):
            failures.append(f"{location} has malformed or ambiguous FROM syntax")
            continue

        source = tokens[0]
        stage_name = tokens[2] if len(tokens) == 3 else None
        if stage_name is not None and DOCKER_STAGE_PATTERN.fullmatch(stage_name) is None:
            failures.append(f"{location} has an invalid Docker build stage name")
            continue

        source_kind = docker_source_kind(
            source,
            stages,
            "FROM",
            location,
            failures,
            allow_scratch=True,
        )
        accepted_source = source_kind is not None
        current_stage_is_valid = accepted_source
        if source_kind == "remote":
            base_image_pins += 1

        if stage_name is not None and accepted_source:
            stage_key = stage_name.casefold()
            if stage_key == "scratch" or stage_key in stages:
                failures.append(
                    f"{location} Docker build stage name {stage_name!r} is ambiguous"
                )
            else:
                stages.add(stage_key)

    if from_count == 0:
        failures.append(f"{label} must contain at least one FROM instruction")
    return DockerfilePinCounts(base_image_pins, other_input_pins)


def scalar_field(
    mapping: dict[str, Any],
    key: str,
    label: str,
    failures: list[str],
) -> str | None:
    scalar = mapping.get(key)
    if not isinstance(scalar, CanonicalYamlScalar) or not scalar.value:
        failures.append(f"{label} {key} must be a non-empty scalar")
        return None
    return scalar.value


def check_github_action_pin_counts_from_root(
    root: Path,
    failures: list[str],
) -> ActionGraphPinCounts:
    github_action = re.compile(
        r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?@([0-9a-fA-F]{40})$"
    )
    docker_image = re.compile(
        r"^docker://[A-Za-z0-9._:/-]+@sha256:[0-9a-fA-F]{64}$"
    )
    workflow_container = re.compile(
        r"^[A-Za-z0-9._:/-]+@sha256:[0-9a-fA-F]{64}$"
    )
    workflows = sorted((root / ".github" / "workflows").glob("*.y*ml"))
    scanned: set[Path] = set()
    visiting: list[Path] = []
    pinned = 0
    dockerfile_base_images = 0
    dockerfile_other_inputs = 0

    def read_yaml(path: Path) -> tuple[dict[str, Any] | None, str]:
        label = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {label}: {error}")
            return None, label
        try:
            return parse_canonical_yaml_document(text, label), label
        except CanonicalYamlError as error:
            failures.append(str(error))
            return None, label

    def enter(path: Path, label: str) -> bool:
        resolved = path.resolve()
        if resolved in visiting:
            start = visiting.index(resolved)
            cycle = visiting[start:] + [resolved]
            failures.append(
                f"{label} local uses cycle detected: "
                + " -> ".join(item.relative_to(root.resolve()).as_posix() for item in cycle)
            )
            return False
        if resolved in scanned:
            return False
        visiting.append(resolved)
        return True

    def leave(path: Path) -> None:
        resolved = path.resolve()
        if visiting and visiting[-1] == resolved:
            visiting.pop()
        scanned.add(resolved)

    def check_external(use: ActionUse, source_label: str) -> None:
        nonlocal pinned
        declaration = use.declaration
        location = f"{source_label}:{use.line}"
        if use.scope == "workflow-container":
            if workflow_container.fullmatch(declaration) is None:
                failures.append(
                    f"{location} workflow container {declaration!r} must use an immutable "
                    "sha256 digest"
                )
            else:
                pinned += 1
            return
        if declaration.startswith("docker://"):
            if docker_image.fullmatch(declaration) is None:
                failures.append(
                    f"{location} external container action must use an immutable sha256 digest"
                )
            else:
                pinned += 1
            return
        action_match = github_action.fullmatch(declaration)
        if action_match is None:
            failures.append(
                f"{location} external action {declaration!r} must be pinned to a full "
                "40-character commit SHA"
            )
            return
        action_path = declaration.rsplit("@", 1)[0]
        if any(part in {".", ".."} for part in action_path.split("/")):
            failures.append(f"{location} external action path contains traversal")
            return
        if re.search(r"\bv[0-9]", use.comment) is None:
            failures.append(
                f"{location} pinned action must retain a human-readable version comment"
            )
        pinned += 1

    def inspect_use(use: ActionUse, source_label: str) -> None:
        declaration = use.declaration
        location = f"{source_label}:{use.line}"
        if not declaration.startswith("./"):
            check_external(use, source_label)
            return
        if use.scope == "workflow-job":
            relative = canonical_local_path(declaration, location, failures)
            if relative is None:
                return
            if not re.fullmatch(r"\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml", relative.as_posix()):
                failures.append(
                    f"{location} local reusable workflow must name one file directly under "
                    ".github/workflows"
                )
                return
            lexical_candidate = root.resolve() / Path(*relative.parts)
            if lexical_candidate.is_symlink():
                failures.append(
                    f"{location} local reusable workflow must not be a symbolic link"
                )
                return
            candidate = contained_path(root, relative, location, failures)
            if candidate is None or not candidate.is_file():
                failures.append(f"{location} local reusable workflow is missing: {declaration!r}")
                return
            inspect_workflow(candidate)
            return
        metadata = local_action_metadata(root, declaration, location, failures)
        if metadata is not None:
            inspect_action(metadata)

    def inspect_workflow(path: Path) -> None:
        label = path.relative_to(root).as_posix()
        if path.is_symlink():
            failures.append(f"{label} workflow file must not be a symbolic link")
            return
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            failures.append(f"{label} workflow file escapes the repository")
            return
        if not path.is_file():
            failures.append(f"{label} workflow file is missing")
            return
        if not enter(path, label):
            return
        document, label = read_yaml(path)
        if document is not None:
            for use in workflow_uses_declarations(document, label, failures):
                inspect_use(use, label)
            for container in workflow_container_declarations(document, label, failures):
                check_external(container, label)
        leave(path)

    def inspect_action(path: Path) -> None:
        nonlocal pinned, dockerfile_base_images, dockerfile_other_inputs
        label = path.relative_to(root).as_posix()
        if not enter(path, label):
            return
        document, label = read_yaml(path)
        if document is None:
            leave(path)
            return
        declarations = action_uses_declarations(document, label, failures)
        runs = document.get("runs")
        if not isinstance(runs, dict):
            leave(path)
            return
        using = scalar_field(runs, "using", f"{label} runs", failures)
        action_directory = path.parent.resolve()
        if using == "composite":
            if not isinstance(runs.get("steps"), list):
                failures.append(f"{label} composite action must declare runs.steps")
            for use in declarations:
                inspect_use(use, label)
        elif using in {"node12", "node16", "node20", "node24"}:
            if "steps" in runs:
                failures.append(f"{label} JavaScript action must not declare runs.steps")
            main = scalar_field(runs, "main", f"{label} runs", failures)
            if main is not None:
                local_action_file(root, action_directory, main, f"{label} runs.main", failures)
            for optional in ("pre", "post"):
                if optional not in runs:
                    continue
                value = scalar_field(runs, optional, f"{label} runs", failures)
                if value is not None:
                    local_action_file(
                        root,
                        action_directory,
                        value,
                        f"{label} runs.{optional}",
                        failures,
                    )
        elif using == "docker":
            if "steps" in runs:
                failures.append(f"{label} Docker action must not declare runs.steps")
            image = scalar_field(runs, "image", f"{label} runs", failures)
            if image is not None:
                if image.startswith("docker://"):
                    check_external(ActionUse(image, "", 0, "action-image"), label)
                elif image != "Dockerfile":
                    failures.append(
                        f"{label} runs.image must name Dockerfile or an immutable "
                        "docker:// image"
                    )
                else:
                    dockerfile = local_action_file(
                        root,
                        action_directory,
                        image,
                        f"{label} runs.image",
                        failures,
                        reject_symlink=True,
                    )
                    if dockerfile is not None:
                        dockerfile_label = dockerfile.relative_to(
                            root.resolve()
                        ).as_posix()
                        dockerfile_pins = check_dockerfile_inputs(
                            dockerfile,
                            dockerfile_label,
                            failures,
                        )
                        pinned += dockerfile_pins.total
                        dockerfile_base_images += dockerfile_pins.base_images
                        dockerfile_other_inputs += dockerfile_pins.other_inputs
        elif using is not None:
            failures.append(f"{label} runs.using {using!r} is not an accepted local action runtime")
        leave(path)

    for workflow in workflows:
        inspect_workflow(workflow)
    return ActionGraphPinCounts(
        pinned,
        dockerfile_base_images,
        dockerfile_other_inputs,
    )


def check_github_action_pins_from_root(root: Path, failures: list[str]) -> int:
    """Compatibility wrapper for callers that need only the aggregate total."""
    return check_github_action_pin_counts_from_root(root, failures).total


def check_github_action_pin_counts(failures: list[str]) -> ActionGraphPinCounts:
    counts = check_github_action_pin_counts_from_root(REPOSITORY_ROOT, failures)
    if counts.total == 0:
        failures.append("no immutable third-party GitHub Action pins were found")
    return counts


def check_github_action_pins(failures: list[str]) -> int:
    """Compatibility wrapper for callers that need only the aggregate total."""
    return check_github_action_pin_counts(failures).total


def check_distribution_workflow_contract(
    failures: list[str],
) -> dict[str, Any] | None:
    path = REPOSITORY_ROOT / ".github" / "workflows" / "distribution-drift.yml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None

    label = display_path(path)
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

    def scalar_values(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, CanonicalYamlScalar) for item in value
        ):
            return None
        return [item.value for item in value]

    if set(document) != {"name", "on", "permissions", "jobs"}:
        failures.append(f"{label} must contain only name, on, permissions, and jobs")
    if scalar(document.get("name")) != "Distribution and publication guards":
        failures.append(f"{label} must keep its exact public workflow name")

    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {
        "pull_request",
        "push",
        "workflow_dispatch",
    }:
        failures.append(
            f"{label} must structurally declare only pull_request, push, and "
            "workflow_dispatch triggers"
        )
    else:
        pull_request = triggers.get("pull_request")
        if not isinstance(pull_request, dict) or scalar_values(
            pull_request.get("branches")
        ) != ["main"]:
            failures.append(f"{label} pull_request trigger must target only main")
        for event_name in ("push", "workflow_dispatch"):
            event = triggers.get(event_name)
            if not isinstance(event, CanonicalYamlScalar) or event.value:
                failures.append(f"{label} {event_name} trigger must not accept filters")

    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"contents"}:
        failures.append(f"{label} must grant only the contents permission")
    elif scalar(permissions.get("contents")) != "read":
        failures.append(f"{label} contents permission must be read-only")

    jobs = document.get("jobs")
    job = jobs.get("repository-guards") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"repository-guards"}:
        failures.append(f"{label} must declare only the repository-guards job")
    if not isinstance(job, dict) or set(job) != {
        "runs-on",
        "timeout-minutes",
        "steps",
    }:
        failures.append(
            f"{label} repository-guards must contain only runner, timeout, and steps"
        )
    elif (
        scalar(job.get("runs-on")) != "ubuntu-latest"
        or scalar(job.get("timeout-minutes")) != "5"
    ):
        failures.append(f"{label} repository-guards runner or timeout changed")

    steps = job.get("steps") if isinstance(job, dict) else None
    if not isinstance(steps, list) or len(steps) != 3 or any(
        not isinstance(step, dict) for step in steps
    ):
        failures.append(f"{label} must contain exactly three canonical validation steps")
    else:
        checkout, distribution, publication = steps
        checkout_with = checkout.get("with")
        if (
            set(checkout) != {"name", "uses", "with"}
            or scalar(checkout.get("name")) != "Check out repository"
            or scalar(checkout.get("uses"))
            != "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
            or not isinstance(checkout_with, dict)
            or set(checkout_with) != {"persist-credentials"}
            or scalar(checkout_with.get("persist-credentials")) != "false"
        ):
            failures.append(
                f"{label} checkout must remain immutable and must not persist credentials"
            )
        expected_commands = (
            (
                distribution,
                "Check distribution agreement",
                "python3 scripts/check-distribution-drift.py",
            ),
            (
                publication,
                "Check publication invariants",
                "python3 scripts/check-publication.py",
            ),
        )
        for step, expected_name, expected_command in expected_commands:
            if (
                set(step) != {"name", "run"}
                or scalar(step.get("name")) != expected_name
                or scalar(step.get("run")) != expected_command
            ):
                failures.append(
                    f"{label} must run exact read-only validator step {expected_name!r}"
                )

    for forbidden in (
        "pull_request_target",
        "${{ secrets.",
        "${{ github.token",
        "GITHUB_TOKEN",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden pull-request surface {forbidden!r}")
    return document


def check_unit_test_workflow_text(
    text: str,
    failures: list[str],
    *,
    label: str = ".github/workflows/unit-and-integration-tests.yml",
) -> dict[str, Any] | None:
    """Validate the exact read-only full-suite workflow contract."""
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

    def scalar_values(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, CanonicalYamlScalar) for item in value
        ):
            return None
        return [item.value for item in value]

    if set(document) != {"name", "on", "permissions", "jobs"}:
        failures.append(f"{label} must contain only name, on, permissions, and jobs")
    if scalar(document.get("name")) != "Unit and integration tests":
        failures.append(f"{label} must keep its exact public workflow name")

    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {"pull_request", "push"}:
        failures.append(
            f"{label} must structurally declare only pull_request and push triggers"
        )
    else:
        for event_name in ("pull_request", "push"):
            event = triggers.get(event_name)
            if not isinstance(event, dict) or scalar_values(event.get("branches")) != [
                "main"
            ]:
                failures.append(f"{label} {event_name} trigger must target only main")

    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"contents"}:
        failures.append(f"{label} must grant only the contents permission")
    elif scalar(permissions.get("contents")) != "read":
        failures.append(f"{label} contents permission must be read-only")

    jobs = document.get("jobs")
    job = jobs.get("unit-and-integration-tests") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {"unit-and-integration-tests"}:
        failures.append(f"{label} must declare only the unit-and-integration-tests job")
    if not isinstance(job, dict) or set(job) != {
        "name",
        "runs-on",
        "timeout-minutes",
        "steps",
    }:
        failures.append(
            f"{label} unit-and-integration-tests must contain only name, runner, "
            "timeout, and steps"
        )
    elif (
        scalar(job.get("name")) != "unit-and-integration-tests"
        or scalar(job.get("runs-on")) != "ubuntu-24.04"
        or scalar(job.get("timeout-minutes")) != "10"
    ):
        failures.append(f"{label} stable check name, runner, or timeout changed")

    steps = job.get("steps") if isinstance(job, dict) else None
    if not isinstance(steps, list) or len(steps) != 5 or any(
        not isinstance(step, dict) for step in steps
    ):
        failures.append(f"{label} must contain exactly five canonical test steps")
    else:
        checkout, python, node, environment, tests = steps
        checkout_with = checkout.get("with")
        if (
            set(checkout) != {"name", "uses", "with"}
            or scalar(checkout.get("name")) != "Check out repository"
            or scalar(checkout.get("uses"))
            != "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
            or not isinstance(checkout_with, dict)
            or set(checkout_with) != {"persist-credentials"}
            or scalar(checkout_with.get("persist-credentials")) != "false"
        ):
            failures.append(
                f"{label} checkout must remain immutable and must not persist credentials"
            )

        python_with = python.get("with")
        if (
            set(python) != {"name", "uses", "with"}
            or scalar(python.get("name")) != "Set up Python"
            or scalar(python.get("uses"))
            != "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
            or not isinstance(python_with, dict)
            or set(python_with) != {"python-version"}
            or scalar(python_with.get("python-version")) != "3.14.7"
        ):
            failures.append(f"{label} must pin the exact Python 3.14.7 environment")

        node_with = node.get("with")
        if (
            set(node) != {"name", "uses", "with"}
            or scalar(node.get("name")) != "Set up Node.js"
            or scalar(node.get("uses"))
            != "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
            or not isinstance(node_with, dict)
            or set(node_with) != {"node-version", "package-manager-cache"}
            or scalar(node_with.get("node-version")) != "24.19.0"
            or scalar(node_with.get("package-manager-cache")) != "false"
        ):
            failures.append(
                f"{label} must pin Node.js 24.19.0 with package-manager caching disabled"
            )

        expected_environment_block = (
            "      - name: Report canonical environment\n"
            "        run: |\n"
            "          cat /etc/os-release\n"
            "          python3 --version\n"
            "          node --version\n"
            "          git --version\n"
            "\n"
            "      - name: Run unit and integration tests\n"
        )
        if (
            set(environment) != {"name", "run"}
            or scalar(environment.get("name")) != "Report canonical environment"
            or scalar(environment.get("run")) != "|"
            or expected_environment_block not in text
        ):
            failures.append(
                f"{label} must report the exact Ubuntu, Python, Node.js, and Git environment"
            )

        if (
            set(tests) != {"name", "run"}
            or scalar(tests.get("name")) != "Run unit and integration tests"
            or scalar(tests.get("run"))
            != "python3 -m unittest discover -s tests -p 'test_*.py' -v"
        ):
            failures.append(f"{label} must run the exact complete unittest discovery command")

    for forbidden in (
        "pull_request_target",
        "${{",
        "GITHUB_TOKEN",
        "permissions: write",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden pull-request surface {forbidden!r}")
    return document


def check_unit_test_workflow_contract(
    failures: list[str],
) -> dict[str, Any] | None:
    path = (
        REPOSITORY_ROOT
        / ".github"
        / "workflows"
        / "unit-and-integration-tests.yml"
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None
    return check_unit_test_workflow_text(text, failures, label=display_path(path))


def check_hook_runtime_workflow_text(
    text: str,
    failures: list[str],
    *,
    label: str = ".github/workflows/hook-runtime-integration.yml",
) -> dict[str, Any] | None:
    """Validate the read-only native hook matrix and its stable aggregate gate."""
    try:
        document = parse_canonical_yaml_document(text, label)
    except CanonicalYamlError as error:
        failures.append(str(error))
        return None

    def scalar(value: Any) -> str | None:
        return value.value if isinstance(value, CanonicalYamlScalar) else None

    def scalar_values(value: Any) -> list[str] | None:
        if not isinstance(value, list) or any(
            not isinstance(item, CanonicalYamlScalar) for item in value
        ):
            return None
        return [item.value for item in value]

    if set(document) != {"name", "on", "permissions", "jobs"}:
        failures.append(f"{label} must contain only name, on, permissions, and jobs")
    if scalar(document.get("name")) != "Cross-platform hook runtime integration":
        failures.append(f"{label} must keep its exact public workflow name")

    triggers = document.get("on")
    if not isinstance(triggers, dict) or set(triggers) != {
        "pull_request",
        "push",
        "schedule",
    }:
        failures.append(
            f"{label} must structurally declare only pull_request, push, and the "
            "bounded weekly schedule"
        )
    else:
        for event_name in ("pull_request", "push"):
            event = triggers.get(event_name)
            if not isinstance(event, dict) or scalar_values(event.get("branches")) != [
                "main"
            ]:
                failures.append(f"{label} {event_name} trigger must target only main")
        schedule = triggers.get("schedule")
        if (
            not isinstance(schedule, list)
            or len(schedule) != 1
            or not isinstance(schedule[0], dict)
            or set(schedule[0]) != {"cron"}
            or scalar(schedule[0].get("cron")) != "17 6 * * 1"
        ):
            failures.append(
                f"{label} must keep the exact bounded weekly compatibility schedule"
            )

    permissions = document.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != {"contents"}:
        failures.append(f"{label} must grant only the contents permission")
    elif scalar(permissions.get("contents")) != "read":
        failures.append(f"{label} contents permission must be read-only")

    jobs = document.get("jobs")
    job = jobs.get("hook-runtime") if isinstance(jobs, dict) else None
    gate = jobs.get("hook-runtime-gate") if isinstance(jobs, dict) else None
    if not isinstance(jobs, dict) or set(jobs) != {
        "hook-runtime",
        "hook-runtime-gate",
    }:
        failures.append(
            f"{label} must declare only hook-runtime and hook-runtime-gate jobs"
        )
    expected_job_keys = {
        "name",
        "strategy",
        "runs-on",
        "timeout-minutes",
        "steps",
    }
    if not isinstance(job, dict) or set(job) != expected_job_keys:
        failures.append(
            f"{label} hook-runtime must contain only name, strategy, runner, "
            "timeout, and steps"
        )
    elif (
        scalar(job.get("name")) != "hook-runtime-${{ matrix.os }}"
        or scalar(job.get("runs-on")) != "${{ matrix.os }}"
        or scalar(job.get("timeout-minutes")) != "10"
    ):
        failures.append(f"{label} stable matrix check name, runner, or timeout changed")

    strategy = job.get("strategy") if isinstance(job, dict) else None
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    if (
        not isinstance(strategy, dict)
        or set(strategy) != {"fail-fast", "matrix"}
        or scalar(strategy.get("fail-fast")) != "false"
        or not isinstance(matrix, dict)
        or set(matrix) != {"os"}
        or scalar_values(matrix.get("os"))
        != ["ubuntu-24.04", "windows-2025", "macos-15"]
    ):
        failures.append(
            f"{label} must keep the exact Ubuntu, Windows, and macOS runner matrix"
        )

    steps = job.get("steps") if isinstance(job, dict) else None
    if not isinstance(steps, list) or len(steps) != 5 or any(
        not isinstance(step, dict) for step in steps
    ):
        failures.append(f"{label} must contain exactly five canonical runtime steps")
    else:
        checkout, python, node, environment, runtime = steps
        checkout_with = checkout.get("with")
        if (
            set(checkout) != {"name", "uses", "with"}
            or scalar(checkout.get("name")) != "Check out repository"
            or scalar(checkout.get("uses"))
            != "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
            or not isinstance(checkout_with, dict)
            or set(checkout_with) != {"persist-credentials"}
            or scalar(checkout_with.get("persist-credentials")) != "false"
        ):
            failures.append(
                f"{label} checkout must remain immutable and must not persist credentials"
            )

        python_with = python.get("with")
        if (
            set(python) != {"name", "uses", "with"}
            or scalar(python.get("name")) != "Set up Python"
            or scalar(python.get("uses"))
            != "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
            or not isinstance(python_with, dict)
            or set(python_with) != {"python-version"}
            or scalar(python_with.get("python-version")) != "3.14.7"
        ):
            failures.append(f"{label} must pin the exact Python 3.14.7 environment")

        node_with = node.get("with")
        if (
            set(node) != {"name", "uses", "with"}
            or scalar(node.get("name")) != "Set up Node.js"
            or scalar(node.get("uses"))
            != "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
            or not isinstance(node_with, dict)
            or set(node_with) != {"node-version", "package-manager-cache"}
            or scalar(node_with.get("node-version")) != "24.19.0"
            or scalar(node_with.get("package-manager-cache")) != "false"
        ):
            failures.append(
                f"{label} must pin Node.js 24.19.0 with caching disabled"
            )

        expected_commands = (
            (
                environment,
                "Report canonical environment",
                "python -B -m tests.hook_runtime_integration --report-environment",
            ),
            (
                runtime,
                "Execute exact SessionStart hooks",
                "python -B -m unittest tests.hook_runtime_integration -v",
            ),
        )
        for step, expected_name, expected_command in expected_commands:
            if (
                set(step) != {"name", "run"}
                or scalar(step.get("name")) != expected_name
                or scalar(step.get("run")) != expected_command
            ):
                failures.append(
                    f"{label} must run exact local step {expected_name!r}"
                )

    expected_gate_keys = {
        "name",
        "if",
        "needs",
        "runs-on",
        "timeout-minutes",
        "steps",
    }
    if not isinstance(gate, dict) or set(gate) != expected_gate_keys:
        failures.append(
            f"{label} hook-runtime-gate must contain only stable name, always "
            "condition, dependency, runner, timeout, and steps"
        )
    elif (
        scalar(gate.get("name")) != "hook-runtime-gate"
        or scalar(gate.get("if")) != "${{ always() }}"
        or scalar_values(gate.get("needs")) != ["hook-runtime"]
        or scalar(gate.get("runs-on")) != "ubuntu-24.04"
        or scalar(gate.get("timeout-minutes")) != "2"
    ):
        failures.append(
            f"{label} hook-runtime-gate must keep its stable name, use if: always(), "
            "depend only on the full hook-runtime matrix, and keep its fixed runner "
            "and timeout"
        )

    gate_steps = gate.get("steps") if isinstance(gate, dict) else None
    if (
        not isinstance(gate_steps, list)
        or len(gate_steps) != 1
        or not isinstance(gate_steps[0], dict)
    ):
        failures.append(
            f"{label} hook-runtime-gate must contain exactly one fail-closed step"
        )
    else:
        gate_step = gate_steps[0]
        gate_env = gate_step.get("env")
        if (
            set(gate_step) != {"name", "env", "run"}
            or scalar(gate_step.get("name")) != "Require successful native matrix"
            or not isinstance(gate_env, dict)
            or set(gate_env) != {"HOOK_RUNTIME_RESULT"}
            or scalar(gate_env.get("HOOK_RUNTIME_RESULT"))
            != "${{ needs.hook-runtime.result }}"
            or scalar(gate_step.get("run"))
            != 'test "$HOOK_RUNTIME_RESULT" = success'
        ):
            failures.append(
                f"{label} hook-runtime-gate must fail closed on every current-run "
                "matrix result other than success"
            )

    allowed_expressions = {
        "${{ matrix.os }}": 2,
        "${{ always() }}": 1,
        "${{ needs.hook-runtime.result }}": 1,
    }
    expression_free = text
    for expression, expected_count in allowed_expressions.items():
        if text.count(expression) != expected_count:
            failures.append(
                f"{label} must use {expression!r} exactly {expected_count} time(s)"
            )
        expression_free = expression_free.replace(expression, "")
    if "${{" in expression_free:
        failures.append(
            f"{label} may use only the exact matrix, always, and current-result expressions"
        )
    for forbidden in (
        "pull_request_target",
        "${{ secrets.",
        "${{ github.token",
        "GITHUB_TOKEN",
        "permissions: write",
    ):
        if forbidden in text:
            failures.append(f"{label} exposes forbidden pull-request surface {forbidden!r}")
    return document


def check_hook_runtime_workflow_contract(
    failures: list[str],
) -> dict[str, Any] | None:
    path = (
        REPOSITORY_ROOT
        / ".github"
        / "workflows"
        / "hook-runtime-integration.yml"
    )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read {display_path(path)}: {error}")
        return None
    return check_hook_runtime_workflow_text(text, failures, label=display_path(path))
