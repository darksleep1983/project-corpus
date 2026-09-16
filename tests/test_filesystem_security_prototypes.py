from __future__ import annotations

import os
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import threading
import unicodedata
import unittest

from prototypes.filesystem_security.common import PrototypePathError, validate_relative_path


class LexicalPathTests(unittest.TestCase):
    def test_portable_traversal_is_rejected(self):
        for value in ("../x", "a/../x", "/tmp/x", "a//x", "./x", " x", "x "):
            with self.subTest(value=value), self.assertRaises(PrototypePathError):
                validate_relative_path(value, windows=False)

    def test_windows_ambiguous_names_are_rejected(self):
        values = (
            "C:/x", "C:x", "//server/share/x", r"\\?\C:\x", r"\\.\NUL",
            "Tasks/file.md:secret", "Tasks/NUL.md", "Tasks/COM1.txt",
            "Tasks/name. ", "Tasks/name.", "Tasks/a*b.md",
        )
        for value in values:
            with self.subTest(value=value), self.assertRaises(PrototypePathError):
                validate_relative_path(value, windows=True)


@unittest.skipUnless(sys.platform == "win32", "Windows native probe")
class WindowsNativeProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pc-win-probe-")
        base = Path(self.temp.name)
        self.root = base / "root"
        self.outside = base / "outside"
        (self.root / "state").mkdir(parents=True)
        self.outside.mkdir()
        (self.root / "state" / "STATUS.md").write_text("old", encoding="utf-8")
        (self.outside / "sentinel.md").write_text("outside", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_native_open_and_publish_stay_inside_root(self):
        from prototypes.filesystem_security.windows_native import (
            final_path, identity, open_confined, publish_bytes,
            security_descriptor,
        )

        with open_confined(self.root, "state/STATUS.md") as handle:
            self.assertIn("STATUS.md", final_path(handle))
            old_identity = identity(handle)
        old_descriptor = security_descriptor(self.root / "state" / "STATUS.md")
        with open(str(self.root / "state" / "STATUS.md") + ":probe", "w") as stream:
            stream.write("must not survive replacement")
        expected = publish_bytes(
            self.root, "state/STATUS.md", b"new\n", replace=True
        )
        self.assertEqual((self.root / "state" / "STATUS.md").read_bytes(), b"new\n")
        with open_confined(self.root, "state/STATUS.md") as handle:
            self.assertNotEqual(old_identity, identity(handle))
        self.assertEqual(
            old_descriptor,
            security_descriptor(self.root / "state" / "STATUS.md"),
        )
        with self.assertRaises(FileNotFoundError):
            open(str(self.root / "state" / "STATUS.md") + ":probe", "r")
        import hashlib
        self.assertEqual(expected, hashlib.sha256(b"new\n").hexdigest())
        publish_bytes(self.root, "state/PROJECT.md", b"project\n", replace=False)
        with self.assertRaises(Exception):
            publish_bytes(self.root, "state/PROJECT.md", b"duplicate\n", replace=False)

    def test_case_collision_create_fails(self):
        from prototypes.filesystem_security.windows_native import publish_bytes

        with self.assertRaises(Exception):
            publish_bytes(self.root, "state/status.md", b"collision\n", replace=False)
        self.assertEqual(
            (self.root / "state" / "STATUS.md").read_text(encoding="utf-8"),
            "old",
        )

    def test_blocked_replace_keeps_target_and_cleans_temp(self):
        from prototypes.filesystem_security.windows_native import (
            open_without_delete_share, publish_bytes,
        )

        target = self.root / "state" / "STATUS.md"
        with open_without_delete_share(target):
            with self.assertRaises(Exception):
                publish_bytes(self.root, "state/STATUS.md", b"blocked\n", replace=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "old")
        self.assertEqual(list((self.root / "state").glob(".pc-probe-*.tmp")), [])

    def test_directory_flush_behavior_is_observed_not_assumed(self):
        from prototypes.filesystem_security.windows_native import directory_flush_observation

        accepted, error = directory_flush_observation(self.root / "state")
        self.assertIsInstance(accepted, bool)
        self.assertEqual(error == 0, accepted)

    def test_directory_junction_escape_is_rejected(self):
        from prototypes.filesystem_security.windows_native import NativeProbeError, open_confined

        link = self.root / "linked"
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(self.outside)],
            capture_output=True,
        )
        if result.returncode != 0:
            self.skipTest("junction creation unavailable")
        with self.assertRaises(NativeProbeError):
            open_confined(self.root, "linked/sentinel.md")
        self.assertEqual((self.outside / "sentinel.md").read_text(encoding="utf-8"), "outside")

    def test_final_symlink_escape_is_rejected_when_available(self):
        from prototypes.filesystem_security.windows_native import NativeProbeError, open_confined

        link = self.root / "state" / "escape.md"
        try:
            os.symlink(self.outside / "sentinel.md", link)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(NativeProbeError):
            open_confined(self.root, "state/escape.md")


@unittest.skipIf(sys.platform == "win32", "POSIX native probe")
class PosixNativeProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pc-posix-probe-")
        base = Path(self.temp.name)
        self.root = base / "root"
        self.outside = base / "outside"
        (self.root / "state").mkdir(parents=True)
        self.outside.mkdir()
        (self.root / "state" / "STATUS.md").write_text("old", encoding="utf-8")
        (self.outside / "sentinel.md").write_text("outside", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_open_and_publish(self):
        from prototypes.filesystem_security.posix_native import open_confined, publish_bytes

        for force_fallback in (False, True):
            with self.subTest(force_fallback=force_fallback):
                fd, result = open_confined(
                    self.root, "state/STATUS.md", force_fallback=force_fallback
                )
                try:
                    self.assertIn(result.backend, {"openat2", "openat-component-walk"})
                    if force_fallback:
                        self.assertEqual(result.backend, "openat-component-walk")
                finally:
                    os.close(fd)
        publish_bytes(self.root, "state/STATUS.md", b"new\n", replace=True)
        self.assertEqual((self.root / "state" / "STATUS.md").read_bytes(), b"new\n")
        publish_bytes(self.root, "state/PROJECT.md", b"project\n", replace=False)
        with self.assertRaises(FileExistsError):
            publish_bytes(self.root, "state/PROJECT.md", b"duplicate\n", replace=False)

    def test_symlink_escape_is_rejected(self):
        from prototypes.filesystem_security.posix_native import open_confined

        os.symlink(self.outside, self.root / "linked")
        with self.assertRaises(OSError):
            open_confined(self.root, "linked/sentinel.md")
        self.assertEqual((self.outside / "sentinel.md").read_text(encoding="utf-8"), "outside")

    def test_case_and_unicode_collisions_fail_portably(self):
        from prototypes.filesystem_security.posix_native import publish_bytes

        with self.assertRaises(FileExistsError):
            publish_bytes(self.root, "state/status.md", b"collision\n", replace=False)
        decomposed = unicodedata.normalize("NFD", "résumé.md")
        (self.root / "state" / decomposed).write_text("external", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            publish_bytes(self.root, "state/résumé.md", b"collision\n", replace=False)

    def test_parent_swap_never_reads_outside_content(self):
        from prototypes.filesystem_security.posix_native import open_confined

        victim = self.root / "victim"
        parked = self.root / "victim-parked"
        victim.mkdir()
        (victim / "sentinel.md").write_text("inside", encoding="utf-8")
        stop = threading.Event()

        def swapper():
            while not stop.is_set():
                try:
                    victim.rename(parked)
                    os.symlink(self.outside, victim)
                    victim.unlink()
                    parked.rename(victim)
                except FileNotFoundError:
                    pass

        thread = threading.Thread(target=swapper)
        thread.start()
        try:
            modes = (False, True) if sys.platform.startswith("linux") else (True,)
            for force_fallback in modes:
                for _ in range(200):
                    try:
                        fd, _ = open_confined(
                            self.root, "victim/sentinel.md",
                            force_fallback=force_fallback,
                        )
                    except OSError:
                        continue
                    try:
                        self.assertEqual(os.read(fd, 32), b"inside")
                    finally:
                        os.close(fd)
        finally:
            stop.set()
            thread.join()
            if victim.is_symlink():
                victim.unlink()
            if parked.exists() and not victim.exists():
                parked.rename(victim)


class ConcurrencyProbeTests(unittest.TestCase):
    def test_two_managed_writers_from_one_hash_cannot_both_publish(self):
        from prototypes.filesystem_security.cas_probe import cas_publish, StaleWriteError

        with tempfile.TemporaryDirectory(prefix="pc-cas-probe-") as temp:
            base = Path(temp)
            root = base / "root"
            (root / "state").mkdir(parents=True)
            target = root / "state" / "STATUS.md"
            target.write_bytes(b"old\n")
            expected = hashlib.sha256(b"old\n").hexdigest()
            lock = base / "owner-runtime" / "project.lock"
            barrier = threading.Barrier(2)
            outcomes: list[tuple[str, str]] = []

            def writer(value: bytes):
                barrier.wait()
                try:
                    cas_publish(root, "state/STATUS.md", value, expected, lock)
                    outcomes.append(("published", value.decode().strip()))
                except StaleWriteError:
                    outcomes.append(("stale", value.decode().strip()))

            threads = [
                threading.Thread(target=writer, args=(b"writer-a\n",)),
                threading.Thread(target=writer, args=(b"writer-b\n",)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(kind for kind, _ in outcomes), ["published", "stale"])
            published = next(value for kind, value in outcomes if kind == "published")
            self.assertEqual(target.read_text(encoding="utf-8").strip(), published)


class RecoveryModelTests(unittest.TestCase):
    def test_every_recorded_crash_phase_has_deterministic_recovery(self):
        from prototypes.filesystem_security.recovery_model import (
            InjectedCrash, PHASES, recover, simulate_transaction,
        )

        for phase in PHASES:
            with self.subTest(phase=phase), tempfile.TemporaryDirectory(
                prefix="pc-recovery-probe-"
            ) as temp:
                area = Path(temp)
                target = area / "STATUS.md"
                target.write_bytes(b"old\n")
                with self.assertRaises(InjectedCrash):
                    simulate_transaction(area, b"new\n", phase)
                outcome = recover(area)
                if phase in {"STAGED", "BACKED_UP"}:
                    self.assertEqual(outcome, "ROLLED_BACK")
                    self.assertEqual(target.read_bytes(), b"old\n")
                else:
                    self.assertEqual(outcome, "COMPLETED_AFTER_RECOVERY")
                    self.assertEqual(target.read_bytes(), b"new\n")
                self.assertFalse((area / ".journal").exists())

    def test_unexpected_post_crash_content_requires_owner(self):
        from prototypes.filesystem_security.recovery_model import (
            InjectedCrash, recover, simulate_transaction,
        )

        with tempfile.TemporaryDirectory(prefix="pc-recovery-probe-") as temp:
            area = Path(temp)
            target = area / "STATUS.md"
            target.write_bytes(b"old\n")
            with self.assertRaises(InjectedCrash):
                simulate_transaction(area, b"new\n", "PUBLISHED")
            target.write_bytes(b"third-party\n")
            self.assertEqual(recover(area), "NEEDS_OWNER")
            self.assertEqual(target.read_bytes(), b"third-party\n")


if __name__ == "__main__":
    unittest.main()
