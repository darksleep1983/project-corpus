import subprocess
import sys
from pathlib import Path
import tempfile
import unittest


class ScriptTests(unittest.TestCase):
    def test_init_and_validate(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            destination = Path(td) / "Corpus"
            mcp_root = Path(td) / "mcp"
            init = subprocess.run(
                [sys.executable, str(repo / "scripts/init_corpus.py"),
                 "--template", str(repo / "template" / "en"),
                 "--destination", str(destination),
                 "--mcp-root", str(mcp_root)],
                capture_output=True, text=True,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            validate = subprocess.run(
                [sys.executable, str(repo / "scripts/validate_corpus.py"), str(destination)],
                capture_output=True, text=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
            self.assertIn("VALID", validate.stdout)


if __name__ == "__main__":
    unittest.main()
