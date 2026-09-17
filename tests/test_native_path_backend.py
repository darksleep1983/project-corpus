from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unicodedata

from project_corpus.platform import BackendError, open_native_backend
from project_corpus.platform.common import PathValidationError


class NativePathBackendTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(dir=repository)
        self.base = Path(self.temporary.name)
        self.root = self.base / "root"
        self.outside = self.base / "outside"
        self.root.mkdir()
        self.outside.mkdir()
        (self.root / "state").mkdir()
        (self.root / "state" / "STATUS.md").write_bytes(b"old")
        (self.outside / "sentinel.md").write_bytes(b"outside")

    def tearDown(self):
        self.temporary.cleanup()

    def test_backend_is_qualified_only_for_measured_local_filesystem(self):
        with open_native_backend(self.root) as backend:
            if sys.platform == "win32":
                self.assertEqual(backend.filesystem, "ntfs")
                self.assertEqual(
                    backend.durability_level,
                    "file-flush-atomic-namespace-no-directory-flush",
                )
            elif sys.platform == "darwin":
                self.assertEqual(backend.filesystem, "apfs")
                self.assertEqual(backend.durability_level, "file-and-parent-fsync")
            elif sys.platform.startswith("linux"):
                self.assertEqual(backend.filesystem, "ext4")
                self.assertEqual(backend.durability_level, "file-and-parent-fsync")
            self.assertTrue(backend.root_identity)

    def test_unqualified_filesystem_fails_closed(self):
        if sys.platform == "win32":
            from project_corpus.platform.windows import WindowsNativeBackend as backend_type
        else:
            from project_corpus.platform.posix import PosixNativeBackend as backend_type

        original = backend_type.QUALIFIED
        backend_type.QUALIFIED = frozenset()
        try:
            with self.assertRaisesRegex(BackendError, "FILESYSTEM_UNQUALIFIED"):
                backend_type(self.root)
        finally:
            backend_type.QUALIFIED = original

    def test_read_stat_limit_and_atomic_publication(self):
        with open_native_backend(self.root) as backend:
            old = backend.stat("state/STATUS.md")
            self.assertEqual(backend.read_bytes("state/STATUS.md"), b"old")
            self.assertEqual(old.sha256, hashlib.sha256(b"old").hexdigest())
            with self.assertRaisesRegex(BackendError, "READ_LIMIT"):
                backend.read_bytes("state/STATUS.md", max_bytes=2)

            staged = backend.stage_bytes("state/STATUS.md", b"new")
            replaced = backend.publish(staged, replace=True)
            self.assertEqual(replaced.sha256, hashlib.sha256(b"new").hexdigest())
            self.assertNotEqual(old.identity, replaced.identity)

            staged = backend.stage_bytes("state/CREATED.md", b"created")
            created = backend.publish(staged, replace=False)
            self.assertEqual(created.size, 7)

            root_stage = backend.stage_bytes("PROJECT.md", b"project")
            root_file = backend.publish(root_stage, replace=False)
            self.assertEqual(root_file.relative_path, "PROJECT.md")

        self.assertEqual((self.root / "state" / "STATUS.md").read_bytes(), b"new")
        self.assertEqual((self.root / "PROJECT.md").read_bytes(), b"project")

    def test_failed_create_preserves_target_and_discard_removes_stage(self):
        with open_native_backend(self.root) as backend:
            staged = backend.stage_bytes("state/STATUS.md", b"must-not-win")
            with self.assertRaises(Exception):
                backend.publish(staged, replace=False)
            backend.discard(staged)
        self.assertEqual((self.root / "state" / "STATUS.md").read_bytes(), b"old")
        self.assertEqual(list((self.root / "state").glob(".pc-stage-*")), [])

    def test_explicit_discard_removes_stage(self):
        with open_native_backend(self.root) as backend:
            staged = backend.stage_bytes("state/DROP.md", b"drop")
            backend.discard(staged)
        self.assertFalse((self.root / "state" / "DROP.md").exists())
        self.assertEqual(list((self.root / "state").glob(".pc-stage-*")), [])

    def test_malformed_paths_fail_before_io(self):
        candidates = [
            "../outside/sentinel.md",
            "/absolute.md",
            "C:/device.md",
            "state//double.md",
            "state/./dot.md",
            "state/line\nfeed.md",
        ]
        if sys.platform == "win32":
            candidates.extend(
                ["state/file.md:stream", "//server/share/file", "state/CON.txt"]
            )
        with open_native_backend(self.root) as backend:
            for candidate in candidates:
                with self.subTest(candidate=candidate):
                    with self.assertRaises(PathValidationError):
                        backend.read_bytes(candidate)

    def test_case_and_unicode_ambiguity_fails_portably(self):
        (self.root / "state" / "Report.md").write_bytes(b"existing")
        decomposed = unicodedata.normalize("NFD", "café.md")
        with open_native_backend(self.root) as backend:
            with self.assertRaisesRegex(BackendError, "PORTABLE_NAME_COLLISION"):
                backend.stage_bytes("state/report.md", b"collision")
            with self.assertRaises(PathValidationError):
                backend.stage_bytes(f"state/{decomposed}", b"collision")

    def test_symlink_or_junction_escape_is_rejected(self):
        link = self.root / "linked"
        if sys.platform == "win32":
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(self.outside)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                self.skipTest("junction creation unavailable")
        else:
            os.symlink(self.outside, link)
        with open_native_backend(self.root) as backend:
            with self.assertRaises(BackendError):
                backend.read_bytes("linked/sentinel.md")
        self.assertEqual((self.outside / "sentinel.md").read_bytes(), b"outside")

    def test_parent_topology_change_cannot_publish_new_target(self):
        moved = self.outside / "moved-state"
        with open_native_backend(self.root) as backend:
            staged = backend.stage_bytes("state/ESCAPE.md", b"escape")
            if sys.platform == "win32":
                with self.assertRaises(PermissionError):
                    (self.root / "state").rename(moved)
            else:
                (self.root / "state").rename(moved)
                with self.assertRaisesRegex(BackendError, "PARENT_IDENTITY_CHANGED"):
                    backend.publish(staged, replace=False)
            backend.discard(staged)
        self.assertFalse((moved / "ESCAPE.md").exists())
        if moved.exists():
            moved.rename(self.root / "state")

    def test_production_backend_does_not_import_prototype_modules(self):
        platform_root = (
            Path(__file__).resolve().parents[1] / "src" / "project_corpus" / "platform"
        )
        for source in platform_root.glob("*.py"):
            self.assertNotIn("prototypes.", source.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
