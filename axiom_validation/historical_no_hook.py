"""Replay frozen v0.10.1 experiments separately from the current installation.

Six superseded runtime, identity and context inputs come from the immutable release.
Experiment documents, implementations, and other Skills come from the inspected
tree so their existing drift checks still run. The later planning, clarification,
and delegation Skills are outside that historical inventory. No result becomes
current evidence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .context import REPOSITORY_ROOT

SOURCE_COMMIT = "79be4a893549c9b8e390f416cb5f8dad1739493e"
FIXTURE_ROOT = Path("tests/fixtures/no-hook-v0.10.1")
FROZEN_INPUTS = {
    ".codex-plugin/plugin.json": (
        "plugin.json.txt",
        "6b4b9d50cda95957684db97d7d4caefd7fc6e02e30e65964a5ae453ffc715ad1",
    ),
    "skills/using-axiom/SKILL.md": (
        "using-axiom.md.txt",
        "34ff05c32ed17a3ced506f3cced49a3bdca7aa30e0cb79326a4d0d0953deeb9c",
    ),
    "skills/using-axiom/references/updating.md": (
        "updating.md.txt",
        "e99a497b2415d4069abc69ec714fca8d89d17529f8bc464b014c3b19dd305a8d",
    ),
    "evidence/runtime-identity.json": (
        "runtime-identity.json.txt",
        "ed85c95a8c66ad86f796567ea539811455237311db16f260c835b741ce5a648b",
    ),
    "evidence/release-status.json": (
        "release-status.json.txt",
        "4cd1e82cf6e0904f8f3103b06460fd5cb0375445f2e075be78fea4e1b2548514",
    ),
    "axiom_validation/context.py": (
        "context.py.txt",
        "cef91c5c8a48f9acf66886db6f3beedb8bf01ee46dae4658f8d2392c2e3e0d39",
    ),
}


def restore_frozen_inputs(root: Path, destination: Path, *, runtime_only: bool = False) -> None:
    """Copy source-bound text fixtures into an already disposable replay tree."""
    if destination.resolve() == root.resolve():
        raise ValueError("historical replay requires a separate disposable destination")
    for relative, (name, digest) in FROZEN_INPUTS.items():
        if runtime_only and relative in {"evidence/release-status.json", "axiom_validation/context.py"}:
            continue
        source = root / FIXTURE_ROOT / name
        if (source.is_symlink() or not source.is_file()
                or any(parent.is_symlink() for parent in source.parents)):
            raise ValueError(f"historical fixture must be a regular file: {name}")
        data = source.read_text(encoding="utf-8").encode("utf-8")
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"historical fixture differs from {SOURCE_COMMIT}: {name}")
        target = destination / relative
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
            raise ValueError(f"historical replay path contains a symbolic link: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    # These exact public Skills did not exist in the frozen v0.10.1 inventory.
    # Current package checks own them; this disposable replay retains the old set.
    for name in ("task-planning", "clarify-intent", "delegate-simple-task"):
        later_skill = destination / "skills" / name
        if later_skill.is_symlink() or any(parent.is_symlink() for parent in later_skill.parents):
            raise ValueError(f"historical replay path contains a symbolic link: skills/{name}")
        if later_skill.exists():
            shutil.rmtree(later_skill)
    if not runtime_only:
        # Preserve the inspected historical prefix, including any drift. The
        # frozen protocol checks its original revision range; current identity
        # validation owns later revisions.
        ledger_path = destination / "evidence/repository-policy-revisions-v1.json"
        if ledger_path.is_symlink():
            raise ValueError("historical policy ledger must not be a symbolic link")
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        if type(ledger) is not dict or type(ledger.get("revisions")) is not list:
            raise ValueError("historical policy ledger must contain a revisions array")
        ledger["revisions"] = ledger["revisions"][:30]
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


@contextmanager
def historical_snapshot(root: Path = REPOSITORY_ROOT):
    """Make a disposable replay tree without following links or copying Git state."""
    with tempfile.TemporaryDirectory(prefix="axiom-historical-no-hook-") as temporary:
        destination = Path(temporary) / "repository"
        shutil.copytree(root, destination, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        restore_frozen_inputs(root, destination)
        yield destination


def check_no_hook_profile(failures: list[str], root: Path = REPOSITORY_ROOT) -> tuple[int, int]:
    """Validate the frozen profile against its original public Skill inventory."""
    from .no_hook_profile import check_no_hook_profile as check_frozen
    try:
        with historical_snapshot(root) as snapshot:
            return check_frozen(failures, snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        failures.append(f"historical no-Hook profile: {error}")
        return (0, 0)


def check_no_hook_bundle(failures: list[str], root: Path = REPOSITORY_ROOT) -> tuple[int, int]:
    """Validate historical bundle bytes with their original runtime inputs."""
    from .no_hook_bundle import check_no_hook_bundle as check_frozen
    try:
        with historical_snapshot(root) as snapshot:
            return check_frozen(failures, snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        failures.append(f"historical no-Hook bundle: {error}")
        return (0, 0)


def check_no_hook_observation(failures: list[str], root: Path = REPOSITORY_ROOT) -> tuple[int, int]:
    """Validate the frozen offline protocol without executing an observation."""
    from .no_hook_observation import check_no_hook_observation as check_frozen
    try:
        with historical_snapshot(root) as snapshot:
            return check_frozen(failures, snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        failures.append(f"historical no-Hook observation: {error}")
        return (0, 0)


def validate_native_protocol(root: Path = REPOSITORY_ROOT) -> list[str]:
    """Check native experiment bindings against their historical context input."""
    from .no_hook_native_observation import validate_native_protocol as check_frozen
    try:
        with historical_snapshot(root) as snapshot:
            return check_frozen(snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"historical native protocol: {error}"]


def check_clarification(root: Path) -> list[str]:
    """Validate original clarification evidence within its native protocol binding."""
    from .no_hook_clarification import check as check_frozen
    try:
        with historical_snapshot(root) as snapshot:
            return check_frozen(snapshot)
    except (OSError, UnicodeError, ValueError) as error:
        return [f"historical clarification evidence: {error}"]
