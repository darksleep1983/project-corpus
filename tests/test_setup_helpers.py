import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SetupHelperTests(unittest.TestCase):
    def test_setup_project_and_client_config(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            fake_repo = Path(td) / "repo"
            fake_repo.mkdir()
            for name in ("scripts", "template"):
                source = repo / name
                target = fake_repo / name
                if name == "scripts":
                    target.mkdir()
                    for file in ("setup_project.py", "init_corpus.py", "print_client_config.py"):
                        (target / file).write_bytes((source / file).read_bytes())
                else:
                    import shutil
                    shutil.copytree(source, target)
            home = Path(td) / "Project"
            result = subprocess.run([
                sys.executable, str(fake_repo / "scripts/setup_project.py"),
                "--project-home", str(home), "--repo-root", str(fake_repo)
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads((fake_repo / ".project-corpus.local.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(config["corpusRoot"]), (home / "Corpus").resolve())
            self.assertEqual(config["language"], "en")
            self.assertTrue((home / "Corpus" / "AGENTS.md").is_file())

    def test_setup_project_creates_russian_corpus(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            fake_repo = Path(td) / "repo"
            fake_repo.mkdir()
            scripts = fake_repo / "scripts"
            scripts.mkdir()
            for file in ("setup_project.py", "init_corpus.py"):
                (scripts / file).write_bytes((repo / "scripts" / file).read_bytes())
            import shutil
            shutil.copytree(repo / "template", fake_repo / "template")
            home = Path(td) / "Project"
            result = subprocess.run([
                sys.executable, str(fake_repo / "scripts/setup_project.py"),
                "--project-home", str(home), "--repo-root", str(fake_repo), "--language", "ru"
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            agents = (home / "Corpus" / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Дисциплина полного чтения", agents)
            config = json.loads((fake_repo / ".project-corpus.local.json").read_text(encoding="utf-8"))
            self.assertEqual(config["language"], "ru")


if __name__ == "__main__":
    unittest.main()
