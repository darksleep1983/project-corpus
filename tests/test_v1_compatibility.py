from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from project_corpus.compatibility import (
    LegacyCorpusError, V1_CURRENT_FILES, load_v1_corpus,
)
from project_corpus.migration import plan_v1_migration


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


class V1CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_en_and_ru_v1_templates_plan_without_source_mutation(self):
        for language in ("en", "ru"):
            with self.subTest(language=language):
                source = self.root / "template" / language
                before = tree_hashes(source)
                snapshot = load_v1_corpus(source)
                plan = plan_v1_migration(
                    snapshot,
                    project_id=f"fixture-{language}",
                    logical_name=f"Fixture {language.upper()}",
                )
                self.assertEqual(tree_hashes(source), before)
                self.assertEqual(len(snapshot.files), len(V1_CURRENT_FILES))
                self.assertEqual(snapshot.language, language)
                self.assertEqual(plan.trust_root_suggestion, None)
                self.assertEqual(plan.source_manifest, before)
                planned = {item.relative_path: item for item in plan.planned_files}
                project = planned[".project-corpus/state/PROJECT.md"].content.decode()
                status = planned[".project-corpus/state/STATUS.md"].content.decode()
                self.assertNotIn("Filesystem-Root:", project)
                self.assertNotIn("Project-Root:", project)
                self.assertIn(f"Project-ID: fixture-{language}", project)
                self.assertIn("Lifecycle-Status: PAUSED", status)
                for item in (*snapshot.files, *snapshot.artifacts):
                    archived = planned[
                        f".project-corpus/history/v1-source/{item.relative_path}"
                    ]
                    self.assertEqual(archived.content, item.content)
                    self.assertEqual(archived.sha256, item.sha256)
                receipt = plan.public_receipt_json()
                self.assertNotIn(str(source.absolute()), receipt)
                self.assertNotIn("content", receipt)

    def test_missing_current_file_fails_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="pc-v1-missing-") as temp:
            target = Path(temp) / "corpus"
            shutil.copytree(self.root / "template" / "en", target)
            (target / "SESSION_HANDOFF_CURRENT.md").unlink()
            before = tree_hashes(target)
            with self.assertRaises(LegacyCorpusError) as raised:
                load_v1_corpus(target)
            self.assertEqual(raised.exception.code, "V1_MISSING_CURRENT_FILE")
            self.assertEqual(tree_hashes(target), before)

    def test_conflicting_v1_status_is_reported_for_owner_review(self):
        with tempfile.TemporaryDirectory(prefix="pc-v1-conflict-") as temp:
            target = Path(temp) / "corpus"
            shutil.copytree(self.root / "template" / "en", target)
            handoff = target / "SESSION_HANDOFF_CURRENT.md"
            handoff.write_text(
                handoff.read_text(encoding="utf-8").replace(
                    "`NO_ACTIVE_PROJECT`", "`ACTIVE_PROJECT`", 1
                ),
                encoding="utf-8",
            )
            snapshot = load_v1_corpus(target)
            plan = plan_v1_migration(
                snapshot, project_id="conflict-project", logical_name="Conflict"
            )
            self.assertIn("V1_STATUS_CONFLICT_OWNER_REVIEW_REQUIRED", plan.warnings)


if __name__ == "__main__":
    unittest.main()
