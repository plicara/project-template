import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


contract = module(ROOT / ".plicara/check.py")
scaffold = module(ROOT / "tools/new_project.py")


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "example"
        scaffold.create(self.root, "example", "Example", "A bounded experiment.", "study", "docs")

    def write(self, **updates):
        data = contract.read_metadata(self.root)
        data.update(updates)
        (self.root / ".plicara/project.yaml").write_text(yaml.safe_dump(data))

    def test_generated_docs_project_validates(self):
        self.assertEqual(len(contract.validate(self.root)), 1)

    def test_invalid_profile_writes_nothing(self):
        root = self.root.parent / "invalid"
        with self.assertRaises(ValueError):
            scaffold.create(root, "invalid", "Invalid", "Invalid.", "study", "unknown")
        self.assertFalse(root.exists())

    def test_initialize_refuses_dirty_and_existing_projects(self):
        with self.assertRaisesRegex(ValueError, "uninitialized"):
            scaffold.initialize(self.root, "new", "New", "New.", "study", "docs")
        self.write(id="plicara-project-template")
        with patch.object(scaffold.subprocess, "check_output", return_value=" M README.md"), self.assertRaisesRegex(ValueError, "clean"):
            scaffold.initialize(self.root, "new", "New", "New.", "study", "docs")

    def test_initialize_fresh_template(self):
        self.write(id="plicara-project-template")
        with patch.object(scaffold.subprocess, "check_output", return_value=""):
            scaffold.initialize(self.root, "new", "New", "New.", "study", "docs")
        self.assertEqual(contract.validate(self.root)[0][1]["id"], "new")

    def test_refuses_nonempty_destination(self):
        original = (self.root / "README.md").read_bytes()
        with self.assertRaisesRegex(ValueError, "empty"):
            scaffold.create(self.root, "other", "Other", "Other.", "study", "docs")
        self.assertEqual((self.root / "README.md").read_bytes(), original)

    def test_unknown_fields_and_duplicate_yaml_keys_fail(self):
        self.write(stauts="active")
        with self.assertRaisesRegex(ValueError, "unknown"):
            contract.validate(self.root)
        path = self.root / ".plicara/project.yaml"
        path.write_text(path.read_text() + "id: duplicate\n")
        with self.assertRaisesRegex(ValueError, "duplicate YAML"):
            contract.validate(self.root)

    def test_missing_artifact_and_escape_fail(self):
        for path in ("missing.md", "../outside"):
            self.write(artifacts=[{"kind": "evidence", "path": path}])
            with self.assertRaises(ValueError):
                contract.validate(self.root)

    def test_symlink_escape_fails(self):
        (self.root / "outside").symlink_to(self.root.parent)
        self.write(artifacts=[{"kind": "evidence", "path": "outside"}])
        with self.assertRaisesRegex(ValueError, "escapes"):
            contract.validate(self.root)

    def test_child_project_list_is_retired(self):
        self.write(kind="collection", projects=["child"])
        with self.assertRaisesRegex(ValueError, "projects is retired"):
            contract.validate(self.root)

    def test_nested_lab_metadata_fails(self):
        for nested in ("child/AGENTS.md", "child/.plicara/project.yaml", "child/.agents/skills/README.md"):
            path = self.root / nested
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("copy\n")
            with self.assertRaisesRegex(ValueError, "only at the repository root: child/"):
                contract.validate(self.root)
            path.unlink()
        contract.validate(self.root)

    def test_vendored_directories_are_exempt(self):
        upstream = self.root / "third_party/upstream"
        upstream.mkdir(parents=True)
        (upstream / "AGENTS.md").write_text("Upstream's own rules.\n")
        with self.assertRaisesRegex(ValueError, "third_party/upstream/AGENTS.md"):
            contract.validate(self.root)
        self.write(vendored=["third_party/upstream"])
        contract.validate(self.root)

    def test_paused_requires_reason_and_resume_condition(self):
        self.write(status="paused", reason="Waiting for data")
        with self.assertRaisesRegex(ValueError, "resume_when"):
            contract.validate(self.root)
        self.write(resume_when="The dataset becomes available")
        contract.validate(self.root)

    def test_python_profile_requires_lockfile(self):
        root = self.root.parent / "python-project"
        scaffold.create(root, "python-project", "Python", "Python study.", "study", "python")
        with self.assertRaisesRegex(ValueError, "uv.lock"):
            contract.validate(root)

    def test_boolean_schema_and_bad_list_rejected(self):
        self.write(schema_version=True)
        with self.assertRaisesRegex(ValueError, "schema_version"):
            contract.validate(self.root)
        self.write(schema_version=1, artifacts="README.md")
        with self.assertRaisesRegex(ValueError, "list"):
            contract.validate(self.root)


if __name__ == "__main__":
    unittest.main()
