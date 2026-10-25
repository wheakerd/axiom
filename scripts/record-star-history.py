#!/usr/bin/env python3
"""Record the repository's star history and render it as an SVG chart.

Standard library only. The script reads the repository's current star and fork
counts from the GitHub REST API, appends or replaces today's row in a CSV file
held on a data branch, renders a date/star line chart as SVG, and commits both
files to that branch through the GraphQL ``createCommitOnBranch`` mutation so
that every data commit is GitHub-signed.

The data branch is never checked out: the current CSV is read through the
contents API and the new files are sent as base64 additions. When the branch
does not exist yet, the script creates it with a parentless root commit that
holds only the branch README (Git Data API, unsigned, authored by the token
identity); every data commit after that is GitHub-signed. Offline runs
(``--offline-stars``) skip the network and the commit.
"""
from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import io
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
API_VERSION = "2022-11-28"
CSV_HEADER = ("date", "stars", "forks")


def _request(url: str, token: str | None, *, method: str = "GET", payload: dict | None = None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
               "User-Agent": "axiom-star-history"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def read_rows(text: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(text)))
    for row in rows:
        if tuple(row) != CSV_HEADER:
            raise SystemExit(f"unexpected CSV columns {tuple(row)!r}")
        dt.date.fromisoformat(row["date"])
        int(row["stars"])
        int(row["forks"])
    return rows


def write_rows(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADER, lineterminator="\n")
    writer.writeheader()
    for row in sorted(rows, key=lambda item: item["date"]):
        writer.writerow(row)
    return buffer.getvalue()


def upsert(rows: list[dict[str, str]], date: str, stars: int, forks: int) -> list[dict[str, str]]:
    kept = [row for row in rows if row["date"] != date]
    kept.append({"date": date, "stars": str(stars), "forks": str(forks)})
    return kept


def _ticks(maximum: int, count: int = 4) -> list[int]:
    if maximum <= count:
        return list(range(0, max(maximum, 1) + 1))
    raw = maximum / count
    magnitude = 10 ** (len(str(int(raw))) - 1)
    for factor in (1, 2, 5, 10):
        step = factor * magnitude
        if step * count >= maximum:
            break
    return list(range(0, maximum + step, step))


def render_svg(rows: list[dict[str, str]], repository: str) -> str:
    rows = sorted(rows, key=lambda item: item["date"])
    width, height = 880, 360
    left, right, top, bottom = 64, 24, 44, 52
    plot_w, plot_h = width - left - right, height - top - bottom
    dates = [dt.date.fromisoformat(row["date"]) for row in rows]
    stars = [int(row["stars"]) for row in rows]
    span_days = max((dates[-1] - dates[0]).days, 1)
    peak = max(stars + [1])
    ticks = _ticks(peak)
    y_max = ticks[-1] if ticks[-1] > 0 else 1

    def x_of(date: dt.date) -> float:
        return left + plot_w * (date - dates[0]).days / span_days

    def y_of(value: int) -> float:
        return top + plot_h - plot_h * value / y_max

    points = [(x_of(d), y_of(s)) for d, s in zip(dates, stars)]
    if len(points) == 1:
        points = [(left, points[0][1]), (left + plot_w, points[0][1])]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"M{points[0][0]:.1f},{top + plot_h} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points) + f" L{points[-1][0]:.1f},{top + plot_h} Z"
    grid = "".join(
        f'<line class="grid" x1="{left}" y1="{y_of(t):.1f}" x2="{left + plot_w}" y2="{y_of(t):.1f}"/>'
        f'<text class="label" x="{left - 8}" y="{y_of(t) + 4:.1f}" text-anchor="end">{t}</text>'
        for t in ticks)
    label_dates = sorted({dates[0], dates[-1], *(dates[i] for i in range(0, len(dates), max(len(dates) // 4, 1)))})
    x_labels = "".join(
        f'<text class="label" x="{x_of(d):.1f}" y="{top + plot_h + 20}" text-anchor="middle">{d.isoformat()}</text>'
        for d in label_dates)
    last_x, last_y = points[-1]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Star history of {repository}">'
        "<style>"
        ".bg{fill:#ffffff}.title{font:600 16px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:#1f2328}"
        ".label{font:12px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:#59636e}.grid{stroke:#d1d9e0;stroke-width:1}"
        ".line{fill:none;stroke:#0969da;stroke-width:2.5;stroke-linejoin:round}.area{fill:#0969da;fill-opacity:0.08}.dot{fill:#0969da}"
        "@media (prefers-color-scheme: dark){.bg{fill:#0d1117}.title{fill:#f0f6fc}.label{fill:#9198a1}.grid{stroke:#3d444d}.line{stroke:#4493f8}.area{fill:#4493f8}.dot{fill:#4493f8}}"
        "</style>"
        f'<rect class="bg" width="{width}" height="{height}" rx="6"/>'
        f'<text class="title" x="{left}" y="26">{repository} stars</text>'
        f'<text class="label" x="{width - right}" y="26" text-anchor="end">{dates[-1].isoformat()}: {stars[-1]} stars</text>'
        f"{grid}{x_labels}"
        f'<path class="area" d="{area}"/><polyline class="line" points="{polyline}"/>'
        f'<circle class="dot" cx="{last_x:.1f}" cy="{last_y:.1f}" r="4"/>'
        "</svg>\n"
    )


def fetch_counts(repository: str, token: str | None) -> tuple[int, int]:
    document = _request(f"{API}/repos/{repository}", token)
    return int(document["stargazers_count"]), int(document["forks_count"])


def fetch_branch_file(repository: str, branch: str, path: str, token: str | None) -> str | None:
    try:
        document = _request(f"{API}/repos/{repository}/contents/{path}?ref={branch}", token)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    return base64.b64decode(document["content"]).decode("utf-8")


BRANCH_README = """# Axiom stats branch

This branch holds only data recorded by the `Record star history` workflow of
[wheakerd/axiom](https://github.com/wheakerd/axiom): `stars.csv` (one row per
UTC date with the star and fork counts) and `stars.svg` (the rendered chart that
the repository README embeds). It is not part of the plugin or any release.
See the repository's governance document for the branch policy.
"""


def branch_head(repository: str, branch: str, token: str | None) -> str | None:
    try:
        return _request(f"{API}/repos/{repository}/git/ref/heads/{branch}", token)["object"]["sha"]
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def bootstrap_branch(repository: str, branch: str, token: str) -> str:
    """Create ``branch`` from a parentless root commit holding the branch README."""
    tree = _request(f"{API}/repos/{repository}/git/trees", token, method="POST", payload={
        "tree": [{"path": "README.md", "mode": "100644", "type": "blob", "content": BRANCH_README}]})
    root = _request(f"{API}/repos/{repository}/git/commits", token, method="POST", payload={
        "message": f"stats: initialize the {branch} branch", "tree": tree["sha"], "parents": []})
    _request(f"{API}/repos/{repository}/git/refs", token, method="POST", payload={
        "ref": f"refs/heads/{branch}", "sha": root["sha"]})
    return root["sha"]


def commit(repository: str, branch: str, files: dict[str, str], headline: str, body: str, token: str) -> str:
    head = branch_head(repository, branch, token)
    if head is None:
        head = bootstrap_branch(repository, branch, token)
        print(f"created {branch} with root commit {head}")
    payload = {
        "query": "mutation($input: CreateCommitOnBranchInput!) { createCommitOnBranch(input: $input) { commit { oid } } }",
        "variables": {"input": {
            "branch": {"repositoryNameWithOwner": repository, "branchName": branch},
            "expectedHeadOid": head,
            "fileChanges": {"additions": [
                {"path": path, "contents": base64.b64encode(text.encode("utf-8")).decode("ascii")}
                for path, text in sorted(files.items())]},
            "message": {"headline": headline, "body": body},
        }},
    }
    document = _request(f"{API}/graphql", token, method="POST", payload=payload)
    if document.get("errors"):
        raise SystemExit(f"createCommitOnBranch failed: {json.dumps(document['errors'])}")
    return document["data"]["createCommitOnBranch"]["commit"]["oid"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, help="owner/name")
    parser.add_argument("--branch", default="stats", help="data branch (default: stats)")
    parser.add_argument("--csv-path", default="stars.csv")
    parser.add_argument("--svg-path", default="stars.svg")
    parser.add_argument("--date", help="UTC date to record (default: today)")
    parser.add_argument("--offline-stars", type=int, help="skip the API and record this star count")
    parser.add_argument("--offline-forks", type=int, default=0)
    parser.add_argument("--offline-csv", help="offline mode: read the existing CSV from this file")
    parser.add_argument("--write-dir", help="also write the CSV and SVG into this directory")
    parser.add_argument("--no-commit", action="store_true", help="render only; do not commit")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or None
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    dt.date.fromisoformat(date)

    if args.offline_stars is not None:
        stars, forks = args.offline_stars, args.offline_forks
        existing = open(args.offline_csv, encoding="utf-8").read() if args.offline_csv else None
    else:
        stars, forks = fetch_counts(args.repository, token)
        existing = fetch_branch_file(args.repository, args.branch, args.csv_path, token)

    rows = read_rows(existing) if existing else []
    updated = upsert(rows, date, stars, forks)
    csv_text = write_rows(updated)
    svg_text = render_svg(updated, args.repository)
    changed = csv_text != (existing or "")

    if args.write_dir:
        os.makedirs(args.write_dir, exist_ok=True)
        for name, text in ((args.csv_path, csv_text), (args.svg_path, svg_text)):
            with open(os.path.join(args.write_dir, os.path.basename(name)), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)

    print(f"{date} stars={stars} forks={forks} rows={len(updated)} changed={changed}")
    if args.offline_stars is not None or args.no_commit:
        return 0
    if not changed:
        print("no change; nothing to commit")
        return 0
    if not token:
        raise SystemExit("GITHUB_TOKEN is required to commit")
    oid = commit(args.repository, args.branch, {args.csv_path: csv_text, args.svg_path: svg_text},
                 f"stats: record {date} stars={stars} forks={forks}",
                 "Recorded by the Record star history workflow through createCommitOnBranch.", token)
    print(f"committed {oid} to {args.branch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
