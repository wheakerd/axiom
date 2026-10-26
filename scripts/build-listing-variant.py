#!/usr/bin/env python3
"""Build the hook-less Codex directory listing variant of Axiom from a Git tree.

Standard library only. The OpenAI plugin directory does not accept lifecycle
hooks, while Axiom's marketplace package keeps its startup Hook. This script
derives the listing variant from the ``plugin/`` tree of one tree-ish, normally
an immutable release tag, without a second maintained Skill tree:

- ``.codex-plugin/plugin.json`` keeps every field except ``hooks``;
- ``skills/``, ``assets/``, and ``LICENSE`` are copied byte for byte;
- ``hooks/`` and ``.claude-plugin/`` are excluded (the directory lists Codex
  plugins only).

The output is a deterministic ZIP (sorted entries, stored without compression,
fixed timestamps, Unix file modes) and a JSON build manifest that records the
source commit, the ``plugin/`` tree, the plugin version, every file digest, the
removed paths and manifest fields, and the archive digest. Two clean builds of
the same tree produce identical bytes. The variant is a derived distribution
artifact, not an Axiom installed-runtime identity; building it installs and
publishes nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path

VARIANT = "codex-directory-skills-only"
EXCLUDED_PREFIXES = ("hooks/", ".claude-plugin/")
CODEX_MANIFEST = ".codex-plugin/plugin.json"
REMOVED_MANIFEST_FIELDS = ("hooks",)
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MODES = {"100644": 0o644, "100755": 0o755}


class BuildError(Exception):
    """A condition that makes the variant non-reproducible or incomplete."""


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise BuildError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump_manifest(document: OrderedDict) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_plugin_tree(repository: Path, tree_ish: str) -> tuple[str, str, list[tuple[str, str, str]]]:
    """Return the source commit, the plugin/ tree OID, and (mode, blob, path) entries."""
    commit = _git(repository, "rev-parse", "--verify", f"{tree_ish}^{{commit}}").decode().strip()
    tree = _git(repository, "rev-parse", "--verify", f"{tree_ish}:plugin").decode().strip()
    raw = _git(repository, "ls-tree", "-r", "-z", tree)
    entries: list[tuple[str, str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, blob = meta.decode().split(" ")
        relative = path.decode("utf-8")
        if kind != "blob" or mode not in MODES:
            raise BuildError(f"{relative}: unsupported tree entry {mode} {kind}")
        entries.append((mode, blob, relative))
    if not entries:
        raise BuildError(f"{tree_ish}:plugin is empty")
    return commit, tree, sorted(entries, key=lambda entry: entry[2])


def strip_manifest_hooks(source: bytes) -> tuple[bytes, list[str]]:
    """Remove the hook declaration from the Codex manifest while proving byte stability."""
    document = json.loads(source.decode("utf-8"), object_pairs_hook=OrderedDict)
    if _dump_manifest(document) != source:
        raise BuildError(f"{CODEX_MANIFEST} is not byte-stable under the canonical two-space form")
    removed = [field for field in REMOVED_MANIFEST_FIELDS if field in document]
    for field in removed:
        del document[field]
    return _dump_manifest(document), removed


def build(repository: Path, tree_ish: str, output: Path) -> OrderedDict:
    commit, tree, entries = read_plugin_tree(repository, tree_ish)
    files: list[OrderedDict] = []
    members: list[tuple[str, int, bytes]] = []
    manifest_change: OrderedDict | None = None
    version: str | None = None
    for mode, blob, relative in entries:
        if relative.startswith(EXCLUDED_PREFIXES):
            continue
        data = _git(repository, "cat-file", "blob", blob)
        source_sha = _sha256(data)
        if relative == CODEX_MANIFEST:
            data, removed = strip_manifest_hooks(data)
            version = json.loads(data.decode("utf-8"))["version"]
            manifest_change = OrderedDict(
                path=relative,
                removedFields=removed,
                sourceSha256=source_sha,
                variantSha256=_sha256(data),
            )
        files.append(
            OrderedDict(path=relative, mode=mode, blob=blob, bytes=len(data), sha256=_sha256(data))
        )
        members.append((relative, MODES[mode], data))
    if manifest_change is None or version is None:
        raise BuildError(f"{tree_ish}:plugin has no {CODEX_MANIFEST}")
    if not any(member[0].startswith("skills/") for member in members):
        raise BuildError(f"{tree_ish}:plugin has no skills/ tree")

    output.mkdir(parents=True, exist_ok=True)
    stem = f"axiom-{version}-codex-directory-variant"
    archive_path = output / f"{stem}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for relative, mode, data in members:
            info = zipfile.ZipInfo(relative, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100000 | mode) << 16
            archive.writestr(info, data)
    archive_bytes = archive_path.read_bytes()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if names != [member[0] for member in members]:
            raise BuildError("archive member order drifted from the sorted source order")
        for relative, _mode, data in members:
            if archive.read(relative) != data:
                raise BuildError(f"{relative}: archive bytes differ from the built bytes")

    manifest = OrderedDict(
        schemaVersion="1",
        variant=VARIANT,
        pluginVersion=version,
        source=OrderedDict(treeIsh=tree_ish, commit=commit, pluginTree=tree),
        excludedPaths=list(EXCLUDED_PREFIXES),
        manifestChanges=[manifest_change],
        archive=OrderedDict(
            name=archive_path.name,
            bytes=len(archive_bytes),
            sha256=_sha256(archive_bytes),
            fileCount=len(members),
            compression="stored",
            timestamp="1980-01-01T00:00:00",
        ),
        files=files,
        boundary=OrderedDict(
            runtimeIdentity="not-an-axiom-installed-runtime-identity",
            startupHook="absent; the routing gate loads only on explicit invocation or description match",
            publication="none; building the variant installs and publishes nothing",
        ),
    )
    (output / f"{stem}.json").write_bytes(_dump_manifest(manifest))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", default=".", help="Git repository that holds the plugin/ tree (default: current directory)")
    parser.add_argument("--tree-ish", required=True, help="commit, tag, or branch whose plugin/ tree is built")
    parser.add_argument("--output", required=True, help="directory that receives the ZIP and the build manifest")
    args = parser.parse_args(argv)
    try:
        manifest = build(Path(args.repository), args.tree_ish, Path(args.output))
    except (BuildError, OSError, ValueError, KeyError) as error:
        print(f"build-listing-variant: {error}", file=sys.stderr)
        return 1
    archive = manifest["archive"]
    print(
        f"{archive['name']} {archive['bytes']} bytes sha256 {archive['sha256']} "
        f"({archive['fileCount']} files from {manifest['source']['commit'][:12]} plugin tree "
        f"{manifest['source']['pluginTree'][:12]}; removed {', '.join(manifest['excludedPaths'])} "
        f"and manifest {', '.join(manifest['manifestChanges'][0]['removedFields']) or 'nothing'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
