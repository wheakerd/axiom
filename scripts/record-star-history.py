#!/usr/bin/env python3
"""Record the repository's star history and render it as an SVG chart.

Standard library only. The script reads the repository's current star and fork
counts from the GitHub REST API, appends or replaces today's row in a CSV file
held on a data branch, renders a date/star line chart as a hand-drawn SVG, and
commits both files to that branch through the GraphQL ``createCommitOnBranch``
mutation so that every data commit is GitHub-signed. It commits when the data
or the rendered chart differs from the branch, so a renderer change reaches
the README on the next run.

The chart embeds a printable-ASCII subset of the Patrick Hand typeface
(``scripts/fonts/``, SIL Open Font License 1.1, copyright Patrick Wagesreiter)
so the handwriting renders the same everywhere; without that asset the SVG
falls back to the viewer's cursive fonts. Axes, line, and legend pass through
one SVG displacement filter for the sketched look, the technique of the upstream
star-history/star-history chart (``xkcdify``); the output is deterministic.

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
import math
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


def _tick_step(maximum: float, intervals: int = 7) -> float:
    """The smallest 1, 2, 2.5, or 5 times a power of ten that covers ``maximum`` in at most ``intervals`` steps."""
    if maximum <= intervals:
        return 1
    magnitude = 10 ** (len(str(int(maximum / intervals))) - 1)
    for factor in (1, 2, 2.5, 5, 10):
        step = factor * magnitude
        if step * intervals >= maximum:
            return step
    return 10 * magnitude


def _ticks(maximum: int, headroom: float = 1.06) -> tuple[list[float], float]:
    """Tick values below ``maximum`` times the headroom, and that scale top."""
    top = max(maximum, 1) * headroom
    step = _tick_step(max(maximum, 1))
    ticks = []
    value = step
    while value <= top:
        ticks.append(value)
        value += step
    return ticks, top


FONT_FAMILY = "Patrick Hand"
FONT_ASSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "PatrickHand-Regular.subset.woff2.b64")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")


def _embedded_font() -> str:
    """Return the @font-face rule for the bundled OFL handwriting font, or an empty string without the asset."""
    try:
        with open(FONT_ASSET, encoding="ascii") as handle:
            data = "".join(handle.read().split())
    except OSError:
        return ""
    return (f"@font-face{{font-family:'{FONT_FAMILY}';font-style:normal;font-weight:400;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def _count_label(value: float) -> str:
    if value < 1000:
        return str(int(value)) if float(value).is_integer() else f"{value:g}"
    if value < 1_000_000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return f"{value / 1_000_000:.1f}M".replace(".0M", "M")


def _date_ticks(first: dt.date, last: dt.date) -> list[tuple[dt.date, str]]:
    """Up to seven tick dates with labels: days for short spans, month names (the year at January) for longer ones."""
    span = max((last - first).days, 1)
    if span <= 21:
        step = 1 if span <= 7 else 2 if span <= 14 else 3
        return [(first + dt.timedelta(days=i), (first + dt.timedelta(days=i)).strftime("%b %d").replace(" 0", " "))
                for i in range(0, span + 1, step)]
    month_starts = []
    cursor = dt.date(first.year, first.month, 1)
    while cursor <= last:
        if cursor >= first:
            month_starts.append(cursor)
        cursor = dt.date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
    if span <= 120 and len(month_starts) < 3:
        mids = []
        for start in [dt.date(first.year, first.month, 1), *month_starts]:
            mid = dt.date(start.year, start.month, 15)
            if first <= mid <= last and mid not in mids:
                mids.append(mid)
        days = sorted(set(month_starts) | set(mids))
        return [(d, d.strftime("%b %d").replace(" 0", " ")) for d in days]
    if span > 1100:
        years = [d for d in month_starts if d.month == 1]
        stride = max(1, -(-len(years) // 7))
        return [(d, str(d.year)) for d in years[::stride]]
    stride = next(s for s in (1, 2, 3, 4, 6, 12) if sum((d.month - 1) % s == 0 for d in month_starts) <= 7)
    chosen = [d for d in month_starts if (d.month - 1) % stride == 0]
    return [(d, str(d.year) if d.month == 1 else MONTHS[d.month - 1]) for d in chosen]


def _star_path(cx: float, cy: float, outer: float, inner: float) -> str:
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = math.radians(-90 + 36 * i)
        points.append(f"{cx + radius * math.cos(angle):.1f},{cy + radius * math.sin(angle):.1f}")
    return "M" + " L".join(points) + " Z"


def render_svg(rows: list[dict[str, str]], repository: str) -> str:
    """Render the star history as a hand-drawn chart: wobbly axes and line, handwriting font, legend box."""
    rows = sorted(rows, key=lambda item: item["date"])
    width, height = 860, 560
    left, right, top, bottom = 76, 40, 64, 72
    plot_w, plot_h = width - left - right, height - top - bottom
    axis_y = top + plot_h
    dates = [dt.date.fromisoformat(row["date"]) for row in rows]
    stars = [int(row["stars"]) for row in rows]
    span_days = max((dates[-1] - dates[0]).days, 1)
    ticks, y_max = _ticks(max(stars))

    def x_of(date: dt.date) -> float:
        return left + plot_w * (date - dates[0]).days / span_days

    def y_of(value: float) -> float:
        return top + plot_h - plot_h * value / y_max

    points = [(x_of(d), y_of(s)) for d, s in zip(dates, stars)]
    if len(points) == 1:
        points = [(left, points[0][1]), (left + plot_w, points[0][1])]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)
    markers = "".join(f'<rect class="mark" x="{x - 2.5:.1f}" y="{y - 2.5:.1f}" width="5" height="5"/>' for x, y in points)
    y_axis = "".join(
        f'<line class="ink" x1="{left - 6}" y1="{y_of(t):.1f}" x2="{left}" y2="{y_of(t):.1f}"/>'
        f'<text class="tick" x="{left - 12}" y="{y_of(t) + 5:.1f}" text-anchor="end">{_count_label(t)}</text>'
        for t in ticks)
    x_axis = "".join(
        f'<line class="ink" x1="{x_of(d):.1f}" y1="{axis_y}" x2="{x_of(d):.1f}" y2="{axis_y + 6}"/>'
        f'<text class="tick" x="{x_of(d):.1f}" y="{axis_y + 26}" text-anchor="middle">{label}</text>'
        for d, label in _date_ticks(dates[0], dates[-1]))
    legend_w = 34 + int(8.4 * len(repository))
    legend = (f'<rect class="box" x="{left + 10}" y="{top + 6}" width="{legend_w}" height="30" rx="5"/>'
              f'<rect class="mark" x="{left + 20}" y="{top + 17}" width="8" height="8"/>'
              f'<text class="legend" x="{left + 36}" y="{top + 27}">{repository}</text>')
    latest = f"{dates[-1].isoformat()}: {stars[-1]} stars"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Star history of {repository}: {latest}">'
        "<style>"
        f"{_embedded_font()}"
        f"text{{font-family:'{FONT_FAMILY}','Comic Neue','Comic Sans MS','Chalkboard SE',cursive;fill:#070707}}"
        ".bg{fill:#d4d4d4}.title{font-size:26px;stroke:#070707;stroke-width:0.7;paint-order:stroke}.tick{font-size:16px}.axis{font-size:18px}.legend{font-size:16px}.note{font-size:13px;fill:#5f5f60}"
        ".ink{stroke:#070707;stroke-width:2.2;stroke-linecap:round;fill:none}.box{stroke:#070707;stroke-width:2;fill:#d4d4d4}"
        ".line{stroke:#ae4430;stroke-width:3.2;stroke-linecap:round;stroke-linejoin:round;fill:none}.mark{fill:#ae4430}.star{fill:#070707}"
        "@media (prefers-color-scheme: dark){text{fill:#e6edf3}.title{stroke:#e6edf3}.bg{fill:#2d333b}.note{fill:#9aa4ae}.ink,.box{stroke:#e6edf3}.box{fill:#2d333b}"
        ".line{stroke:#e4705a}.mark{fill:#e4705a}.star{fill:#e6edf3}}"
        "</style>"
        '<defs><filter id="sketch" x="-2%" y="-2%" width="104%" height="104%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="7" result="noise"/>'
        '<feDisplacementMap in="SourceGraphic" in2="noise" scale="4" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter></defs>"
        f'<rect class="bg" width="{width}" height="{height}" rx="8"/>'
        f'<g filter="url(#sketch)">'
        f'<path class="star" d="{_star_path(width / 2 - 86, 29, 11, 4.6)}"/>'
        f'<line class="ink" x1="{left}" y1="{axis_y}" x2="{left}" y2="{top - 10}"/>'
        f'<line class="ink" x1="{left}" y1="{axis_y}" x2="{left + plot_w + 12}" y2="{axis_y}"/>'
        f'{y_axis}{x_axis}{legend}'
        f'<path class="line" d="{line}"/>{markers}'
        "</g>"
        f'<text class="title" x="{width / 2 - 70}" y="38">Star History</text>'
        f'<text class="axis" transform="translate(26 {top + plot_h / 2:.1f}) rotate(-90)" text-anchor="middle">GitHub Stars</text>'
        f'<text class="axis" x="{left + plot_w / 2:.1f}" y="{height - 16}" text-anchor="middle">Date</text>'
        f'<text class="note" x="{width - 18}" y="{height - 14}" text-anchor="end">{latest}</text>'
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
        existing_svg = None
    else:
        stars, forks = fetch_counts(args.repository, token)
        existing = fetch_branch_file(args.repository, args.branch, args.csv_path, token)
        existing_svg = fetch_branch_file(args.repository, args.branch, args.svg_path, token)

    rows = read_rows(existing) if existing else []
    updated = upsert(rows, date, stars, forks)
    csv_text = write_rows(updated)
    svg_text = render_svg(updated, args.repository)
    changed = csv_text != (existing or "") or svg_text != (existing_svg or "")

    if args.write_dir:
        os.makedirs(args.write_dir, exist_ok=True)
        for name, text in ((args.csv_path, csv_text), (args.svg_path, svg_text)):
            with open(os.path.join(args.write_dir, os.path.basename(name)), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)

    print(f"{date} stars={stars} forks={forks} rows={len(updated)} changed={changed} "
          f"(data {'changed' if csv_text != (existing or '') else 'unchanged'}, chart {'changed' if svg_text != (existing_svg or '') else 'unchanged'})")
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
