from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from project_corpus.cli import main
from project_corpus.security_scan import scan_git_history


def git(root: Path, *arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=root, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout


class SecurityScanTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pc-security-scan-")
        self.root = Path(self.temporary.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Release Test")
        git(self.root, "config", "user.email", "release@example.invalid")

    def tearDown(self):
        self.temporary.cleanup()

    def commit_all(self, message: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)

    def test_scans_deleted_history_patches_and_unreachable_objects_without_values(self):
        credential = b"AKIA" + b"ABCDEFGHIJKLMNOP"
        historical = self.root / "historical.txt"
        historical.write_bytes(credential + b"\n")
        self.commit_all("add historical fixture")
        historical.unlink()
        self.commit_all("delete historical fixture")

        dangling = b"https://" + b"127.0.0.1" + b":7443/private\n"
        dangling_id = git(
            self.root, "hash-object", "-w", "--stdin", input_bytes=dangling
        ).decode().strip()

        report = scan_git_history(self.root)
        self.assertFalse(report.release_gate_pass)
        self.assertTrue(report.coverage_complete)
        self.assertGreaterEqual(report.unreachable_object_count, 1)
        self.assertEqual(report.commit_patch_count, 2)
        categories = {item.category for item in report.findings}
        self.assertIn("credential", categories)
        self.assertIn("private_url", categories)
        self.assertTrue(any(
            item.object_id == dangling_id for item in report.findings
        ))
        serialized = str(report.public_receipt())
        self.assertNotIn(credential.decode(), serialized)
        self.assertNotIn(dangling.decode().strip(), serialized)

    def test_clean_complete_repository_passes(self):
        (self.root / "README.md").write_text("# Public project\n", encoding="utf-8")
        self.commit_all("initial public content")
        report = scan_git_history(self.root)
        self.assertTrue(report.release_gate_pass)
        self.assertEqual(report.findings, ())

    def test_cli_returns_release_gate_exit_code_and_redacted_receipt(self):
        credential = b"AKIA" + b"ABCDEFGHIJKLMNOP"
        (self.root / "historical.txt").write_bytes(credential + b"\n")
        self.commit_all("add historical fixture")

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["security", "scan-history", str(self.root)])

        self.assertEqual(code, 3)
        receipt = json.loads(stdout.getvalue())
        self.assertFalse(receipt["release_gate_pass"])
        self.assertNotIn(credential.decode(), stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
