#!/usr/bin/env python3
"""Run one deterministic stage of Axiom's CI release pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.release_pipeline import (  # noqa: E402
    Clock,
    GitHubClient,
    PipelineError,
    Reporter,
    run_candidate,
    run_catalog,
    run_publish,
    utc_today,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    candidate = commands.add_parser(
        "candidate", help="classify a pull request and preview its Release"
    )
    candidate.add_argument("--repository", required=True)
    candidate.add_argument("--base-sha", required=True)
    candidate.add_argument("--head-sha", required=True)
    publish = commands.add_parser(
        "publish", help="tag, publish, and observe the version main declares"
    )
    publish.add_argument("--repository", required=True)
    publish.add_argument("--commit", required=True)
    catalog = commands.add_parser(
        "catalog", help="open, verify, and merge the marketplace catalog handoff"
    )
    catalog.add_argument("--repository", required=True)
    catalog.add_argument("--tag", required=True)
    return parser.parse_args(argv)


def _environment_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    reporter = Reporter(
        _environment_path("GITHUB_STEP_SUMMARY"), _environment_path("GITHUB_OUTPUT")
    )
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    try:
        read_api = GitHubClient(os.environ.get("GITHUB_TOKEN", ""), api_url=api_url)
        if args.command == "candidate":
            run_candidate(
                root=REPOSITORY_ROOT,
                api=read_api,
                repository=args.repository,
                base_commit=args.base_sha,
                head_commit=args.head_sha,
                reporter=reporter,
            )
        elif args.command == "publish":
            run_publish(
                root=REPOSITORY_ROOT,
                api=read_api,
                repository=args.repository,
                commit=args.commit,
                reporter=reporter,
                clock=Clock(),
            )
        else:
            write_api = GitHubClient(
                os.environ.get("AXIOM_RELEASE_APP_TOKEN", ""), api_url=api_url
            )
            server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
            run_id = os.environ.get("GITHUB_RUN_ID", "local")
            run_catalog(
                root=REPOSITORY_ROOT,
                read_api=read_api,
                write_api=write_api,
                repository=args.repository,
                tag=args.tag,
                reporter=reporter,
                clock=Clock(),
                today=utc_today(),
                run_url=f"{server}/{args.repository}/actions/runs/{run_id}",
            )
    except PipelineError as error:
        print(f"Release pipeline stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
