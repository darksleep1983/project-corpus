from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib
import unittest

from project_corpus.validation import validate_state_pair


PROJECT_METADATA = ("Protocol-Version", "Project-ID", "Logical-Name")
STATUS_METADATA = (
    "Protocol-Version", "Project-ID", "Lifecycle-Status", "Active-Task-ID",
    "Last-Verified-At", "Evidence-Class",
)
PROJECT_SECTIONS = (
    "Objective", "Invariants", "Durable Scope Boundaries", "Non-Goals",
)
STATUS_SECTIONS = (
    "Current Verified Baseline", "Blockers", "Evidence References",
    "Exact Next Action",
)
PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


def parse_document(path: Path) -> tuple[dict[str, str], list[str], str]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):\s*(\S.*)$", line)
        if match:
            metadata[match.group(1)] = match.group(2)
    sections = re.findall(r"^## ([^\r\n]+)$", text, re.MULTILINE)
    return metadata, sections, text


def validate_pair(project_path: Path, status_path: Path) -> list[str]:
    errors: set[str] = set()
    project_meta, project_sections, project_text = parse_document(project_path)
    status_meta, status_sections, _ = parse_document(status_path)

    for required in PROJECT_METADATA:
        if required not in project_meta:
            errors.add("MISSING_METADATA")
    for required in STATUS_METADATA:
        if required not in status_meta:
            errors.add("MISSING_METADATA")
    for required in PROJECT_SECTIONS:
        if required not in project_sections:
            errors.add("MISSING_SECTION")
    for required in STATUS_SECTIONS:
        if required not in status_sections:
            errors.add("MISSING_SECTION")

    if all(project_sections.count(item) == 1 for item in PROJECT_SECTIONS):
        filtered = [item for item in project_sections if item in PROJECT_SECTIONS]
        if tuple(filtered) != PROJECT_SECTIONS:
            errors.add("SECTION_ORDER")
    if all(status_sections.count(item) == 1 for item in STATUS_SECTIONS):
        filtered = [item for item in status_sections if item in STATUS_SECTIONS]
        if tuple(filtered) != STATUS_SECTIONS:
            errors.add("SECTION_ORDER")
    if any(project_sections.count(item) > 1 for item in PROJECT_SECTIONS):
        errors.add("DUPLICATE_SECTION")
    if any(status_sections.count(item) > 1 for item in STATUS_SECTIONS):
        errors.add("DUPLICATE_SECTION")

    if project_meta.get("Project-ID") != status_meta.get("Project-ID"):
        errors.add("PROJECT_ID_MISMATCH")
    for value in (project_meta.get("Project-ID"), status_meta.get("Project-ID")):
        if value is not None and not PROJECT_ID.fullmatch(value):
            errors.add("INVALID_METADATA")
    if project_meta.get("Protocol-Version") != "2.0" or status_meta.get(
        "Protocol-Version"
    ) != "2.0":
        errors.add("INVALID_METADATA")

    if any(item in status_sections for item in PROJECT_SECTIONS):
        errors.add("ROLE_OVERLAP")
    if any(item in project_sections for item in STATUS_SECTIONS):
        errors.add("ROLE_OVERLAP")

    root_field = re.compile(
        r"(?im)^(?:Filesystem-Root|Project-Root|Physical-Root):\s*"
        r"(?:[A-Za-z]:[\\/]|\\\\|/)"
    )
    if root_field.search(project_text):
        errors.add("PROJECT_ABSOLUTE_ROOT")
    return sorted(errors)


class ProtocolV2ConformanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_published_state_fixtures_have_exact_outcomes(self):
        fixtures = self.root / "tests" / "fixtures" / "protocol_v2"
        for case in sorted(path for path in fixtures.iterdir() if path.is_dir()):
            with self.subTest(case=case.name):
                expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
                errors = validate_pair(case / "PROJECT.md", case / "STATUS.md")
                self.assertEqual(errors, expected["errors"])
                self.assertEqual(not errors, expected["valid"])
                runtime_errors = sorted({
                    issue.code for issue in validate_state_pair(
                        (case / "PROJECT.md").read_bytes(),
                        (case / "STATUS.md").read_bytes(),
                    )
                })
                self.assertEqual(runtime_errors, expected["errors"])

    def test_minimal_v2_template_is_conforming(self):
        state = self.root / "templates" / "v2" / "minimal" / ".project-corpus" / "state"
        self.assertEqual(validate_pair(state / "PROJECT.md", state / "STATUS.md"), [])

    def test_portable_policy_has_no_physical_root_or_write_grant(self):
        path = self.root / "templates" / "v2" / "minimal" / ".project-corpus" / "policy.toml"
        raw = path.read_text(encoding="utf-8")
        policy = tomllib.loads(raw)
        self.assertNotRegex(raw, r"(?im)^(?:root|path)\s*=")
        self.assertEqual(policy["project_id"], "example-project")
        self.assertEqual(policy["profile"], "READ_ONLY")
        self.assertEqual(policy["scopes"]["write"], [])
        self.assertNotIn("state.update", policy["capabilities"]["allow"])


if __name__ == "__main__":
    unittest.main()
