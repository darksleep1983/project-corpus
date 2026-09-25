from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import os
import shutil
import tempfile
import unittest

from project_corpus.cli import main
from project_corpus.trust import load_trust_grant
from project_corpus.validation import validate_v2_project


def invoke(arguments: list[str]) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(arguments)
    return code, json.loads(stdout.getvalue() if code == 0 else stderr.getvalue())


def hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


class MigrationApplyTests(unittest.TestCase):
    def setUp(self):
        repository = Path(__file__).resolve().parents[1]
        self.temporary = tempfile.TemporaryDirectory(prefix="pc-migration-")
        self.base = Path(self.temporary.name)
        self.source = self.base / "v1"
        shutil.copytree(repository / "template" / "en", self.source)
        self.destination = self.base / "v2-destination"
        self.authorization = self.base / "owner" / "migration.json"
        self.trust = self.base / "owner" / "trust" / "migrated.toml"

    def tearDown(self):
        self.temporary.cleanup()

    def authorize(self) -> dict[str, object]:
        code, result = invoke([
            "migration", "authorize", str(self.source),
            "--destination", str(self.destination),
            "--authorization", str(self.authorization),
            "--project-id", "migrated-project",
            "--logical-name", "Migrated Project",
        ])
        self.assertEqual(code, 0, result)
        return result

    def test_authorized_apply_publishes_separate_v2_and_preserves_v1(self):
        before = hashes(self.source)
        authorization = self.authorize()
        self.assertFalse(self.destination.exists())
        code, result = invoke([
            "migration", "apply", str(self.source),
            "--authorization", str(self.authorization),
            "--trust", str(self.trust),
            "--allow", "corpus.read", "--allow", "corpus.validate",
        ])
        self.assertEqual(code, 0, result)
        self.assertTrue(result["source_preserved"])
        self.assertEqual(hashes(self.source), before)
        self.assertTrue(validate_v2_project(self.destination).valid)
        archived = self.destination / ".project-corpus" / "history" / "v1-source"
        for relative, digest in before.items():
            self.assertEqual(
                hashlib.sha256((archived / relative).read_bytes()).hexdigest(),
                digest,
            )
        grant = load_trust_grant(self.trust)
        self.assertEqual(grant.physical_root, self.destination)
        self.assertEqual(grant.project_id, "migrated-project")
        self.assertEqual(grant.capability_ceiling, {"corpus.read", "corpus.validate"})
        self.assertEqual(result["plan_sha256"], authorization["plan_sha256"])

        code, repeated = invoke([
            "migration", "apply", str(self.source),
            "--authorization", str(self.authorization),
            "--trust", str(self.trust),
            "--allow", "corpus.read", "--allow", "corpus.validate",
        ])
        self.assertEqual(code, 0, repeated)
        self.assertEqual(repeated["root_identity"], result["root_identity"])

    def test_source_drift_fails_without_destination_publication(self):
        self.authorize()
        (self.source / "PROJECT_ROADMAP_CURRENT.md").write_bytes(b"changed\n")
        code, error = invoke([
            "migration", "apply", str(self.source),
            "--authorization", str(self.authorization),
            "--trust", str(self.trust),
        ])
        self.assertEqual(code, 2)
        self.assertIn("changed after owner authorization", error["detail"])
        self.assertFalse(self.destination.exists())
        self.assertFalse(self.trust.exists())

    def test_existing_destination_and_embedded_authority_fail_closed(self):
        self.destination.mkdir()
        code, error = invoke([
            "migration", "authorize", str(self.source),
            "--destination", str(self.destination),
            "--authorization", str(self.authorization),
            "--project-id", "migrated-project",
            "--logical-name", "Migrated Project",
        ])
        self.assertEqual(code, 2)
        self.assertIn("must not exist", error["detail"])

        embedded = self.source / "owner" / "migration.json"
        code, error = invoke([
            "migration", "authorize", str(self.source),
            "--destination", str(self.base / "other-v2"),
            "--authorization", str(embedded),
            "--project-id", "migrated-project",
            "--logical-name", "Migrated Project",
        ])
        self.assertEqual(code, 2)
        self.assertIn("MIGRATION_AUTH_NOT_EXTERNAL", error["detail"])
        self.assertFalse(embedded.exists())

    def test_destination_race_after_authorization_fails_without_overwrite(self):
        self.authorize()
        self.destination.mkdir()
        sentinel = self.destination / "sentinel.txt"
        sentinel.write_bytes(b"owner data")
        code, error = invoke([
            "migration", "apply", str(self.source),
            "--authorization", str(self.authorization),
            "--trust", str(self.trust),
        ])
        self.assertEqual(code, 2)
        self.assertIn("unexpected entries", error["detail"])
        self.assertEqual(sentinel.read_bytes(), b"owner data")
        self.assertFalse(self.trust.exists())

    def test_confined_source_rejects_symlinked_canonical_file(self):
        target = self.source / "AGENTS.md"
        target.unlink()
        outside = self.base / "outside-secret.txt"
        outside.write_bytes(b"must not migrate")
        try:
            os.symlink(outside, target)
        except OSError:
            self.skipTest("symlink creation unavailable")
        code, _ = invoke([
            "migration", "authorize", str(self.source),
            "--destination", str(self.destination),
            "--authorization", str(self.authorization),
            "--project-id", "migrated-project",
            "--logical-name", "Migrated Project",
        ])
        self.assertEqual(code, 2)
        self.assertFalse(self.authorization.exists())
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
