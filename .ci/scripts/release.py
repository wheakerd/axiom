#!/usr/bin/env python3
"""Release one Axiom version from its tag.

Commands:
  run      gate the tag, build the release branch commit and the Draft, and
           publish the immutable Release (the Release workflow runs this)
  subject  derive the release subject and plugin zip the publisher verifies
  build    offline: stamp a commit's plugin tree and print its tree ID, zip
           digest, runtime digest, and notes, without reading GitHub
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


CI_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = CI_ROOT.parent
if str(CI_ROOT) not in sys.path:
    sys.path.insert(0, str(CI_ROOT))

from axiom_validation.release import (  # noqa: E402
    Clock,
    GitHubClient,
    ReleaseError,
    Reporter,
    build_plugin_zip,
    git,
    input_manifest_at,
    read_release_files,
    release_notes,
    run_release,
    runtime_digest,
    stamp_files,
    subject_for_publisher,
    tree_sha,
    validate_tag,
    zip_name,
)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "subject"):
        command = commands.add_parser(name)
        command.add_argument("--repository", required=True)
        command.add_argument("--tag", required=True)
        if name == "subject":
            command.add_argument("--output", type=Path, required=True)
    build = commands.add_parser("build")
    build.add_argument("--commit", required=True)
    build.add_argument("--tag", required=True)
    build.add_argument("--message-file", type=Path, required=True)
    build.add_argument("--previous-tag")
    build.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def _client() -> GitHubClient:
    return GitHubClient(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "")


def offline_build(arguments: argparse.Namespace) -> dict[str, object]:
    version = validate_tag(arguments.tag)
    commit = git(REPOSITORY_ROOT, "rev-parse", "--verify", f"{arguments.commit}^{{commit}}").decode().strip()
    files = stamp_files(read_release_files(REPOSITORY_ROOT, commit), version)
    archive = build_plugin_zip(files)
    notes = release_notes(
        arguments.message_file.read_text(encoding="utf-8"), arguments.tag, arguments.previous_tag
    )
    arguments.output.mkdir(parents=True, exist_ok=True)
    (arguments.output / zip_name(version)).write_bytes(archive)
    (arguments.output / "notes.md").write_text(notes, encoding="utf-8")
    return {
        "tag": arguments.tag,
        "commit": commit,
        "releaseTree": tree_sha(files),
        "zip": {
            "name": zip_name(version),
            "sha256": hashlib.sha256(archive).hexdigest(),
            "size": len(archive),
        },
        "runtimeDigest": runtime_digest(files, input_manifest_at(REPOSITORY_ROOT, commit)),
        "notesSha256": hashlib.sha256(notes.encode("utf-8")).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        if arguments.command == "run":
            summary = os.environ.get("GITHUB_STEP_SUMMARY")
            run_release(
                root=REPOSITORY_ROOT,
                api=_client(),
                repository=arguments.repository,
                tag=arguments.tag,
                reporter=Reporter(Path(summary) if summary else None),
                clock=Clock(),
            )
        elif arguments.command == "subject":
            subject = subject_for_publisher(
                REPOSITORY_ROOT, _client(), arguments.repository, arguments.tag, arguments.output
            )
            print(json.dumps(subject, sort_keys=True))
        else:
            print(json.dumps(offline_build(arguments), indent=2, sort_keys=True))
    except (ReleaseError, OSError, UnicodeError) as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
