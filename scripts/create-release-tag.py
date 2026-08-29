#!/usr/bin/env python3
"""Create one protected Axiom release tag through the closed controller."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from axiom_validation.release_tag_controller import (  # noqa: E402
    ControllerError,
    GitHubApi,
    ReleaseAppTokenIdentity,
    ReleaseTagRequest,
    canonical_result,
    run_controller,
    validate_request,
)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("validate-request", "create"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected-main-sha", required=True)
    parser.add_argument("--expected-app-id", required=True, type=_positive_int)
    parser.add_argument("--app-slug")
    parser.add_argument("--installation-id", type=_positive_int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    request = ReleaseTagRequest(
        repository=args.repository,
        version=args.version,
        tag=args.tag,
        expected_main_sha=args.expected_main_sha,
        expected_app_id=args.expected_app_id,
    )
    try:
        validate_request(request)
        if args.mode == "validate-request":
            print(
                canonical_result(
                    {
                        "outcome": "request-valid",
                        "repository": request.repository,
                        "version": request.version,
                        "tag": request.tag,
                        "commit": request.expected_main_sha,
                        "appId": request.expected_app_id,
                    }
                )
            )
            return 0

        read_token = os.environ.get("GITHUB_TOKEN", "")
        app_token = os.environ.get("AXIOM_RELEASE_APP_TOKEN", "")
        api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        if not read_token or not app_token:
            raise ControllerError("both read and dedicated release App tokens are required")
        if read_token == app_token:
            raise ControllerError("read and mutation tokens must use distinct identities")
        if args.app_slug is None or args.installation_id is None:
            raise ControllerError(
                "create mode requires the token action's App slug and installation ID"
            )
        result = run_controller(
            GitHubApi(api_url, read_token),
            GitHubApi(api_url, app_token),
            request,
            ReleaseAppTokenIdentity(
                app_slug=args.app_slug,
                installation_id=args.installation_id,
            ),
        )
    except ControllerError as error:
        print(f"Release tag controller rejected the request: {error}", file=sys.stderr)
        return 1
    print(canonical_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
