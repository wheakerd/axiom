"""Focused tests for manifest and marketplace policy."""

import copy
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from axiom_validation.context import RELEASE_VERSION, release_version
from axiom_validation.manifests import (
    BRANDING_IMAGE_MAX_BYTES,
    EXPECTED_CODEX_DEFAULT_PROMPTS,
    JSON_FILES,
    check_branding_image_file,
    check_codex_interface,
    check_manifest_capability_schema,
    check_manifest_versions,
    load_json,
    resolve_declared_asset,
)
from tests.fixtures.manifests import check_manifest_schema_fixtures


def png_bytes(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b""))
        + chunk(b"IEND", b"")
    )


def jpeg_bytes(width: int, height: int) -> bytes:
    frame = (
        b"\xff\xc0\x00\x0b\x08"
        + struct.pack(">HH", height, width)
        + b"\x01\x01\x11\x00"
    )
    scan = b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
    return b"\xff\xd8" + frame + scan + b"\xff\xd9"


def webp_bytes(width: int, height: int) -> bytes:
    payload = (
        b"\x00\x00\x00\x00"
        + (width - 1).to_bytes(3, "little")
        + (height - 1).to_bytes(3, "little")
    )
    body = b"WEBP" + b"VP8X" + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", len(body)) + body


def svg_bytes(width: str = "48", height: str = "48", body: str = "") -> bytes:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'
    ).encode()


class ManifestPolicyTests(unittest.TestCase):
    def documents(self):
        failures = []
        documents = {}
        from axiom_validation.context import REPOSITORY_ROOT

        for relative_path in JSON_FILES:
            document = load_json(REPOSITORY_ROOT / relative_path, failures)
            if document is not None:
                documents[relative_path] = document
        self.assertEqual([], failures)
        return documents

    def test_synchronized_manifests_are_the_release_source(self):
        self.assertEqual(RELEASE_VERSION, release_version())
        self.assertIsNotNone(release_version())

    def test_checked_in_schema_and_versions(self):
        failures = []
        documents = self.documents()
        check_manifest_capability_schema(documents, failures)
        check_manifest_versions(documents, failures)
        check_codex_interface(documents, failures)
        self.assertEqual([], failures)

    def test_schema_mutations_are_rejected(self):
        failures = []
        count = check_manifest_schema_fixtures(self.documents(), failures)
        self.assertEqual(21, count)
        self.assertEqual([], failures)

    def test_official_prompt_scalar_shape_is_accepted_but_is_not_checked_in_contract(self):
        documents = copy.deepcopy(self.documents())
        documents[".codex-plugin/plugin.json"]["interface"]["defaultPrompt"] = (
            EXPECTED_CODEX_DEFAULT_PROMPTS[0]
        )

        schema_failures = []
        check_manifest_capability_schema(documents, schema_failures)
        self.assertEqual([], schema_failures)

        exact_failures = []
        check_codex_interface(documents, exact_failures)
        self.assertTrue(any("defaultPrompt" in failure for failure in exact_failures))

    def test_exact_current_interface_values_are_closed(self):
        documents = copy.deepcopy(self.documents())
        documents[".codex-plugin/plugin.json"]["interface"]["brandColor"] = "#000000"

        schema_failures = []
        check_manifest_capability_schema(documents, schema_failures)
        self.assertEqual([], schema_failures)

        exact_failures = []
        check_codex_interface(documents, exact_failures)
        self.assertTrue(any("brandColor" in failure for failure in exact_failures))


class BrandingAssetPolicyTests(unittest.TestCase):
    def validate(self, path: Path) -> list[str]:
        failures = []
        check_branding_image_file(path, path.name, failures)
        return failures

    def test_supported_square_asset_formats_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets = {
                "mark.svg": svg_bytes(),
                "mark.png": png_bytes(48, 48),
                "mark.jpg": jpeg_bytes(48, 48),
                "mark.jpeg": jpeg_bytes(48, 48),
                "mark.webp": webp_bytes(48, 48),
            }
            for name, data in assets.items():
                with self.subTest(name=name):
                    path = root / name
                    path.write_bytes(data)
                    self.assertEqual([], self.validate(path))

    def test_svg_contract_rejects_unsafe_or_unusable_content(self):
        cases = {
            "malformed.svg": (b"<svg", "malformed XML"),
            "wrong-root.svg": (b"<html width='48' height='48'/>", "root"),
            "missing-namespace.svg": (
                b'<svg width="48" height="48"/>',
                "standard <svg> element",
            ),
            "units.svg": (svg_bytes("48px", "48px"), "numeric without units"),
            "small.svg": (svg_bytes("47", "47"), "at least 48x48"),
            "nonsquare.svg": (svg_bytes("48", "49"), "must be square"),
            "missing-size.svg": (
                b'<svg xmlns="http://www.w3.org/2000/svg"/>',
                "numeric viewBox or width and height",
            ),
            "script.svg": (svg_bytes(body="<script/>"), "unsafe or unsupported"),
            "event.svg": (
                svg_bytes(body='<rect width="48" height="48" onclick="run()"/>'),
                "unsafe 'onclick' metadata",
            ),
            "external.svg": (
                svg_bytes(body='<path d="M0 0" fill="url(https://example.com/a.svg)"/>'),
                "active or external content",
            ),
            "doctype.svg": (
                b'<!DOCTYPE svg><svg xmlns="http://www.w3.org/2000/svg" '
                b'width="48" height="48"/>',
                "DTD or entity",
            ),
            "processing-instruction.svg": (
                b'<?xml-stylesheet href="https://example.com/style.css"?>'
                + svg_bytes(),
                "processing instructions",
            ),
            "aspect.svg": (
                b'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" '
                b'viewBox="0 0 48 49"/>',
                "same aspect ratio",
            ),
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for name, (data, expected) in cases.items():
                with self.subTest(name=name):
                    path = root / name
                    path.write_bytes(data)
                    self.assertTrue(
                        any(expected in failure for failure in self.validate(path)),
                        self.validate(path),
                    )

    def test_raster_dimensions_integrity_and_size_limits_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cases = {
                "small.png": (png_bytes(47, 47), "at least 48x48"),
                "nonsquare.png": (png_bytes(48, 49), "must be square"),
                "oversize-dimensions.png": (
                    png_bytes(4097, 4097),
                    "must not exceed 4096x4096",
                ),
                "bad-checksum.png": (png_bytes(48, 48)[:-1] + b"\x00", "checksum"),
                "wrong-content.webp": (b"not webp", "does not match WebP"),
            }
            for name, (data, expected) in cases.items():
                with self.subTest(name=name):
                    path = root / name
                    path.write_bytes(data)
                    self.assertTrue(
                        any(expected in failure for failure in self.validate(path)),
                        self.validate(path),
                    )

            oversized = root / "oversized.png"
            oversized.write_bytes(b"0" * (BRANDING_IMAGE_MAX_BYTES + 1))
            self.assertTrue(
                any("5 MiB" in failure for failure in self.validate(oversized))
            )

            unsupported = root / "mark.gif"
            unsupported.write_bytes(b"GIF89a")
            self.assertTrue(
                any(
                    "unsupported image extension" in failure
                    for failure in self.validate(unsupported)
                )
            )

    def test_declared_asset_paths_must_resolve_to_regular_in_package_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            assets = root / "assets"
            assets.mkdir()
            mark = assets / "mark.svg"
            mark.write_bytes(svg_bytes())

            failures = []
            self.assertEqual(
                mark,
                resolve_declared_asset(root, "./assets/mark.svg", "logo", failures),
            )
            self.assertEqual([], failures)

            bad_paths = {
                "assets/mark.svg": "start with './'",
                "./assets/../assets/mark.svg": "traversal segments",
                "./assets/missing.svg": "existing regular file",
            }
            for declared, expected in bad_paths.items():
                with self.subTest(declared=declared):
                    path_failures = []
                    self.assertIsNone(
                        resolve_declared_asset(root, declared, "logo", path_failures)
                    )
                    self.assertTrue(
                        any(expected in failure for failure in path_failures),
                        path_failures,
                    )

            directory = assets / "directory.svg"
            directory.mkdir()
            directory_failures = []
            self.assertIsNone(
                resolve_declared_asset(
                    root, "./assets/directory.svg", "logo", directory_failures
                )
            )
            self.assertTrue(any("regular file" in failure for failure in directory_failures))

            symlink = assets / "symlink.svg"
            symlink.symlink_to(mark)
            symlink_failures = []
            self.assertIsNone(
                resolve_declared_asset(
                    root, "./assets/symlink.svg", "logo", symlink_failures
                )
            )
            self.assertTrue(any("symlink" in failure for failure in symlink_failures))


if __name__ == "__main__":
    unittest.main()
