from pathlib import Path
import subprocess
import sys
import unittest


class McpIntegrationTests(unittest.TestCase):
    def test_official_sdk_verifier(self):
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(repo / "scripts" / "verify_mcp.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"status": "ok"', result.stdout)
        self.assertIn('"hostileOriginStatus": 403', result.stdout)
