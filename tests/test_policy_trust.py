from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from project_corpus.authority import evaluate_authority
from project_corpus.policy import PolicyError, parse_project_policy
from project_corpus.trust import TrustError, grant_path, load_trust_grant


def policy_bytes(*, profile: str = "SAFE_EDIT", extra: str = "") -> bytes:
    return f'''policy_version = "2.0"
project_id = "fixture-project"
profile = "{profile}"
{extra}
[capabilities]
allow = ["corpus.read", "corpus.stat", "corpus.validate", "state.update"]

[scopes]
read = [".project-corpus/state/**"]
write = [".project-corpus/state/STATUS.md"]

[requirements]
expected_hash = true
verified_readback = true
audit_receipt = true
'''.encode()


class PolicyTrustTests(unittest.TestCase):
    def make_grant(self, directory: Path, policy: bytes):
        root = directory / "project"
        root.mkdir()
        path = directory / "trust" / "fixture-project.toml"
        path.parent.mkdir()
        path.write_text(
            f'''grant_version = "1"
project_id = "fixture-project"
physical_root = "{root.as_posix()}"
root_identity = "volume:fixture"
policy_sha256 = "{hashlib.sha256(policy).hexdigest()}"
capability_ceiling = ["corpus.read", "corpus.stat", "corpus.validate", "state.update"]
filesystem = "test-local"
transports = ["cli", "stdio-mcp"]
approved_at = "2026-09-16T00:00:00Z"
protocol_version = "2.0"
''',
            encoding="utf-8",
        )
        return load_trust_grant(path), root, path

    def test_effective_authority_is_four_way_intersection(self):
        content = policy_bytes()
        policy = parse_project_policy(content)
        with tempfile.TemporaryDirectory(prefix="pc-trust-") as temp:
            trust, _, _ = self.make_grant(Path(temp), content)
            decision = evaluate_authority(
                trust=trust,
                policy=policy,
                session_capabilities={
                    "corpus.read", "state.update", "git.commit", "shell.exec",
                },
                observed_root_identity="volume:fixture",
                transport="cli",
            )
        self.assertEqual(decision.effective, {"corpus.read", "state.update"})
        self.assertFalse(decision.permits("git.commit"))
        self.assertFalse(decision.permits("shell.exec"))
        self.assertIn("RUNTIME_HARD_LIMIT", decision.reasons)

    def test_policy_drift_keeps_only_read_inspection(self):
        approved = policy_bytes()
        changed = approved + b"\n"
        policy = parse_project_policy(changed)
        with tempfile.TemporaryDirectory(prefix="pc-trust-") as temp:
            trust, _, _ = self.make_grant(Path(temp), approved)
            decision = evaluate_authority(
                trust=trust,
                policy=policy,
                session_capabilities={"corpus.read", "corpus.validate", "state.update"},
                observed_root_identity="volume:fixture",
                transport="cli",
            )
        self.assertTrue(decision.policy_drift)
        self.assertEqual(decision.effective, {"corpus.read", "corpus.validate"})
        self.assertIn("POLICY_DRIFT", decision.reasons)

    def test_root_identity_mismatch_leaves_diagnostic_only(self):
        content = policy_bytes()
        policy = parse_project_policy(content)
        with tempfile.TemporaryDirectory(prefix="pc-trust-") as temp:
            trust, _, _ = self.make_grant(Path(temp), content)
            decision = evaluate_authority(
                trust=trust,
                policy=policy,
                session_capabilities={"corpus.read", "corpus.validate", "state.update"},
                observed_root_identity="different",
                transport="cli",
            )
        self.assertEqual(decision.effective, {"corpus.validate"})
        self.assertIn("ROOT_IDENTITY_MISMATCH", decision.reasons)

    def test_project_cannot_embed_physical_root_or_weaken_write_requirements(self):
        with self.assertRaises(PolicyError) as root_error:
            parse_project_policy(policy_bytes(extra='physical_root = "/tmp/project"'))
        self.assertEqual(root_error.exception.code, "POLICY_UNKNOWN_KEY")
        weak = policy_bytes().replace(b"expected_hash = true", b"expected_hash = false")
        with self.assertRaises(PolicyError) as weak_error:
            parse_project_policy(weak)
        self.assertEqual(weak_error.exception.code, "POLICY_WRITE_REQUIREMENTS")

    def test_read_only_profile_cannot_request_mutation(self):
        with self.assertRaises(PolicyError) as raised:
            parse_project_policy(policy_bytes(profile="READ_ONLY"))
        self.assertEqual(raised.exception.code, "POLICY_PROFILE_CAPABILITY")

    def test_external_grant_is_strict_and_transport_can_only_narrow(self):
        content = policy_bytes()
        policy = parse_project_policy(content)
        with tempfile.TemporaryDirectory(prefix="pc-trust-") as temp:
            base = Path(temp)
            trust, root, path = self.make_grant(base, content)
            self.assertEqual(trust.physical_root, root)
            self.assertEqual(
                grant_path("fixture-project", base / "owner-config"),
                base / "owner-config" / "fixture-project.toml",
            )
            denied = evaluate_authority(
                trust=trust,
                policy=policy,
                session_capabilities={"corpus.read"},
                observed_root_identity="volume:fixture",
                transport="http",
            )
            path.write_text(path.read_text(encoding="utf-8") + "unknown = true\n", encoding="utf-8")
            with self.assertRaises(TrustError) as malformed:
                load_trust_grant(path)
        self.assertEqual(denied.effective, frozenset())
        self.assertIn("TRANSPORT_NOT_GRANTED", denied.reasons)
        self.assertEqual(malformed.exception.code, "TRUST_SCHEMA")


if __name__ == "__main__":
    unittest.main()
