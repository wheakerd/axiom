"""Strict routing-history data and append-only protection tests."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from axiom_validation.routing_evals.history import (
    HISTORY_INDEX,
    HISTORY_INDEX_PATH,
    HISTORY_INDEX_SHA256,
    HistoryIndexError,
    load_history_index,
)


class RoutingHistoryTests(unittest.TestCase):
    def write_document(self, directory: Path, document: dict) -> tuple[Path, str]:
        payload = (json.dumps(document, indent=2) + "\n").encode("utf-8")
        path = directory / "routing-history-v1.json"
        path.write_bytes(payload)
        return path, hashlib.sha256(payload).hexdigest()

    def test_checked_in_history_is_byte_protected_and_strictly_loaded(self):
        self.assertEqual(
            HISTORY_INDEX_SHA256,
            hashlib.sha256(HISTORY_INDEX_PATH.read_bytes()).hexdigest(),
        )
        self.assertEqual(HISTORY_INDEX, load_history_index())
        self.assertEqual(11, len(HISTORY_INDEX["entries"]))

    def test_history_rejects_duplicate_json_keys(self):
        payload = HISTORY_INDEX_PATH.read_text(encoding="utf-8").replace(
            '  "kind": "routing-history-index",',
            '  "kind": "routing-history-index",\n  "kind": "routing-history-index",',
            1,
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "routing-history-v1.json"
            path.write_bytes(payload)
            with self.assertRaisesRegex(HistoryIndexError, "duplicate JSON key"):
                load_history_index(
                    path, expected_sha256=hashlib.sha256(payload).hexdigest()
                )

    def test_history_rejects_unknown_fields_and_malformed_bindings(self):
        mutations = []

        unknown = copy.deepcopy(HISTORY_INDEX)
        unknown["unexpected"] = False
        mutations.append(("unknown", unknown, "unknown unexpected"))

        escaped = copy.deepcopy(HISTORY_INDEX)
        escaped["entries"][0]["path"] = "../outside.json"
        mutations.append(("path", escaped, "must remain under evals/results"))

        invalid_run = copy.deepcopy(HISTORY_INDEX)
        invalid_run["entries"][0]["runId"] = "Uppercase-Run"
        mutations.append(("run ID", invalid_run, "strict lowercase identifier"))

        invalid_oid = copy.deepcopy(HISTORY_INDEX)
        invalid_oid["entries"][0]["subject"]["commit"] = "a" * 39
        mutations.append(("OID", invalid_oid, "lowercase Git OID"))

        invalid_digest = copy.deepcopy(HISTORY_INDEX)
        invalid_digest["entries"][0]["outcomeSha256"] = "b" * 63
        mutations.append(("digest", invalid_digest, "lowercase SHA-256"))

        duplicate_path = copy.deepcopy(HISTORY_INDEX)
        duplicate_path["entries"][1]["path"] = duplicate_path["entries"][0]["path"]
        mutations.append(("duplicate", duplicate_path, ".path duplicates"))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, document, expected in mutations:
                with self.subTest(name=name):
                    path, digest = self.write_document(root, document)
                    with self.assertRaisesRegex(HistoryIndexError, expected):
                        load_history_index(path, expected_sha256=digest)

    def test_history_rejects_symlink_and_oversized_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            symlink = root / "history-link.json"
            symlink.symlink_to(HISTORY_INDEX_PATH)
            with self.assertRaisesRegex(HistoryIndexError, "non-symlink"):
                load_history_index(symlink, expected_sha256=None)

            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (64 * 1024 + 1))
            with self.assertRaisesRegex(HistoryIndexError, "byte limit"):
                load_history_index(oversized, expected_sha256=None)

    def test_history_digest_detects_deletion_and_reassignment(self):
        deleted = copy.deepcopy(HISTORY_INDEX)
        deleted["entries"].pop()
        reassigned = copy.deepcopy(HISTORY_INDEX)
        reassigned["entries"][0]["subject"]["tree"] = "f" * 40

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, document in (("deletion", deleted), ("reassignment", reassigned)):
                with self.subTest(name=name):
                    path, _digest = self.write_document(root, document)
                    with self.assertRaisesRegex(HistoryIndexError, "digest drifted"):
                        load_history_index(path)


if __name__ == "__main__":
    unittest.main()
