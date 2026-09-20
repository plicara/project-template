import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("export", Path(__file__).resolve().parents[1] / "tools/export_snapshot.py")
export = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(export)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        (self.root / "result.json").write_text('{"measured": true}\n')
        self.manifest = {"project": "study", "files": [{"source": "result.json", "destination": "evidence/result.json"}]}

    def git(self, root, *args):
        return {("rev-parse", "--show-toplevel"): str(self.root), ("status", "--porcelain", "--untracked-files=normal"): "", ("rev-parse", "HEAD"): "abc123", ("ls-files", "-z"): "result.json\0", ("remote", "get-url", "origin"): "git@github.com:plicara/example.git"}[args]

    def test_export_preserves_provenance_and_hash(self):
        target = self.root.parent / "release"
        with patch.object(export, "git", side_effect=self.git):
            record = export.plan(self.root, self.manifest)
            export.stage(self.root, target, record)
        self.assertEqual((target / "evidence/result.json").read_bytes(), (self.root / "result.json").read_bytes())
        self.assertTrue((target / "SOURCE.json").is_file())
        self.assertEqual(record["revision"], "abc123")
        self.assertEqual(len(record["files"][0]["sha256"]), 64)

    def test_private_and_escape_paths_rejected(self):
        for path in ("../secret", "/absolute", ".env", "project/.env.local", ".plicara/project.yaml", "notes/private.md", "credentials.json"):
            with self.assertRaises(ValueError):
                export.relative(path)

    def test_dirty_source_rejected(self):
        def dirty(root, *args):
            return " M result.json" if args[0] == "status" else self.git(root, *args)
        with patch.object(export, "git", side_effect=dirty), self.assertRaisesRegex(ValueError, "clean"):
            export.plan(self.root, self.manifest)

    def test_nonempty_destination_is_never_overwritten(self):
        with patch.object(export, "git", side_effect=self.git):
            record = export.plan(self.root, self.manifest)
            with self.assertRaisesRegex(ValueError, "empty"):
                export.stage(self.root, self.root, record)

    def test_untracked_source_and_conflicting_destinations_fail(self):
        self.manifest["files"][0]["source"] = "untracked.json"
        with patch.object(export, "git", side_effect=self.git), self.assertRaisesRegex(ValueError, "tracked"):
            export.plan(self.root, self.manifest)
        self.manifest["files"] = [{"source": "result.json", "destination": name} for name in ("output", "output/file.json")]
        with patch.object(export, "git", side_effect=self.git), self.assertRaisesRegex(ValueError, "conflicting"):
            export.plan(self.root, self.manifest)
