"""GitHub Actions graph and pull-request validation policy."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

from .context import REPOSITORY_ROOT, display_path
from .yaml_subset import (
    ActionUse,
    CanonicalYamlError,
    CanonicalYamlScalar,
    parse_canonical_yaml_document,
)


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
) -> Path | None:
    candidate_raw = raw if raw.startswith("./") else f"./{raw}"
    relative = canonical_local_path(candidate_raw, label, failures)
    if relative is None:
        return None
    candidate = (action_directory / Path(*relative.parts)).resolve()
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


def check_github_action_pins_from_root(root: Path, failures: list[str]) -> int:
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
                else:
                    local_action_file(
                        root,
                        action_directory,
                        image,
                        f"{label} runs.image",
                        failures,
                    )
        elif using is not None:
            failures.append(f"{label} runs.using {using!r} is not an accepted local action runtime")
        leave(path)

    for workflow in workflows:
        inspect_workflow(workflow)
    return pinned


def check_github_action_pins(failures: list[str]) -> int:
    pinned = check_github_action_pins_from_root(REPOSITORY_ROOT, failures)
    if pinned == 0:
        failures.append("no immutable third-party GitHub Action pins were found")
    return pinned


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
