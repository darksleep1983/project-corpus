from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from project_corpus.doctor import doctor
from project_corpus.platform import open_native_backend


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_v2_doctor_is_read_only_and_does_not_claim_controlled_mode(self):
        with tempfile.TemporaryDirectory(prefix="pc-doctor-v2-") as temp:
            project = Path(temp) / "project"
            shutil.copytree(self.root / "templates" / "v2" / "minimal", project)
            before = tree_hashes(project)
            report = doctor(project)
            self.assertEqual(tree_hashes(project), before)
        self.assertTrue(report.ok)
        self.assertEqual(report.project_format, "V2")
        self.assertEqual(report.project_id, "example-project")
        self.assertEqual(report.guarantee_level, "DIRECT_FOLDER_OBSERVABLE")
        self.assertIn("OWNER_TRUST_NOT_EVALUATED", {item.code for item in report.checks})

    def test_v1_en_and_ru_remain_compatible_and_unchanged(self):
        for language in ("en", "ru"):
            with self.subTest(language=language):
                project = self.root / "template" / language
                before = tree_hashes(project)
                report = doctor(project)
                self.assertEqual(tree_hashes(project), before)
                self.assertTrue(report.ok)
                self.assertEqual(report.project_format, "V1")
                self.assertEqual(report.guarantee_level, "MARKDOWN_COMPATIBLE")

    def test_invalid_v2_identity_fails_diagnostic_only(self):
        with tempfile.TemporaryDirectory(prefix="pc-doctor-invalid-") as temp:
            project = Path(temp) / "project"
            shutil.copytree(self.root / "templates" / "v2" / "minimal", project)
            status = project / ".project-corpus" / "state" / "STATUS.md"
            status.write_text(
                status.read_text(encoding="utf-8").replace(
                    "Project-ID: example-project", "Project-ID: different-project"
                ),
                encoding="utf-8",
            )
            report = doctor(project)
        self.assertFalse(report.ok)
        self.assertEqual(report.guarantee_level, "DIAGNOSTIC_ONLY")
        self.assertIn("PROJECT_ID_MISMATCH", {item.code for item in report.checks})

    def test_unmarked_generated_view_fails(self):
        with tempfile.TemporaryDirectory(prefix="pc-doctor-view-") as temp:
            project = Path(temp) / "project"
            shutil.copytree(self.root / "templates" / "v2" / "minimal", project)
            generated = project / ".project-corpus" / "generated"
            generated.mkdir()
            (generated / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
            report = doctor(project)
        self.assertFalse(report.ok)
        self.assertIn("GENERATED_VIEW_UNMARKED", {item.code for item in report.checks})

    def test_trust_root_identity_and_filesystem_are_verified_natively(self):
        with tempfile.TemporaryDirectory(prefix="pc-doctor-trust-") as temp:
            base = Path(temp)
            project = base / "project"
            shutil.copytree(self.root / "templates" / "v2" / "minimal", project)
            policy = (project / ".project-corpus" / "policy.toml").read_bytes()
            with open_native_backend(project) as backend:
                identity = backend.root_identity
                filesystem = backend.filesystem
            trust = base / "trust.toml"
            trust.write_text(
                f'''grant_version = "1"
project_id = "example-project"
physical_root = "{project.as_posix()}"
root_identity = "{identity}"
policy_sha256 = "{hashlib.sha256(policy).hexdigest()}"
capability_ceiling = ["corpus.read", "corpus.validate"]
filesystem = "{filesystem}"
transports = ["cli"]
approved_at = "2026-09-16T00:00:00Z"
protocol_version = "2.0"
''', encoding="utf-8"
            )
            report = doctor(project, trust_grant_path=trust)
        self.assertTrue(report.ok)
        self.assertEqual(report.guarantee_level, "DIRECT_FOLDER_OBSERVABLE")
        codes = {item.code for item in report.checks}
        self.assertIn("ROOT_IDENTITY", codes)
        self.assertIn("FILESYSTEM_QUALIFIED", codes)


if __name__ == "__main__":
    unittest.main()
