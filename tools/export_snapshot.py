# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Stage an allowlisted release from a clean Git revision into an empty directory.

Default is a read-only preview. --apply stages files locally; it never publishes.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlsplit, urlunsplit


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def relative(value):
    if not isinstance(value, str) or not value:
        raise ValueError("file paths must be nonempty strings")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or value == ".":
        raise ValueError(f"unsafe relative path: {value}")
    if any(p in {".git", ".plicara", ".agents", "notes", "data", "node_modules", ".venv"} or p.startswith(".env") for p in path.parts):
        raise ValueError(f"private or generated path cannot be exported: {value}")
    if path.suffix == ".pem" or path.name == "credentials.json":
        raise ValueError(f"credential path cannot be exported: {value}")
    return path


def plan(root, manifest):
    root = root.resolve()
    if not isinstance(manifest, dict) or set(manifest) != {"project", "files"}:
        raise ValueError("manifest requires project and files")
    if not isinstance(manifest["project"], str) or not manifest["project"].strip():
        raise ValueError("project must be a stable project ID")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise ValueError("files must be a nonempty explicit file allowlist")
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("source root must be the repository root")
    if git(root, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("source checkout must be clean; commit the reviewed source first")
    revision = git(root, "rev-parse", "HEAD")
    tracked = set(git(root, "ls-files", "-z").split("\0"))
    origin = git(root, "remote", "get-url", "origin")
    if origin.startswith("git@github.com:"):
        origin = "https://github.com/" + origin.split(":", 1)[1].removesuffix(".git")
    elif "://" in origin:
        parsed = urlsplit(origin)
        origin = urlunsplit((parsed.scheme, parsed.hostname or "", parsed.path, "", ""))
    files, destinations = [], set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict) or set(entry) != {"source", "destination"}:
            raise ValueError("each file requires source and destination")
        source, target = relative(entry["source"]), relative(entry["destination"])
        path = root / source
        if source.as_posix() not in tracked or not path.is_file() or path.is_symlink():
            raise ValueError(f"source must be a tracked regular file: {source}")
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"source escapes repository: {source}")
        if target.as_posix() == "SOURCE.json" or target in destinations:
            raise ValueError(f"duplicate or reserved destination: {target}")
        destinations.add(target)
        files.append({"source": source.as_posix(), "destination": target.as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    for left in destinations:
        if any(right != left and left in right.parents for right in destinations):
            raise ValueError(f"conflicting file/directory destinations: {left}")
    return {"schema_version": 1, "project": manifest["project"], "repository": origin, "revision": revision, "files": files}


def stage(root, destination, record):
    if destination.exists() and (not destination.is_dir() or destination.is_symlink() or any(destination.iterdir())):
        raise ValueError("destination must be a new or empty directory")
    if destination.resolve().is_relative_to(root.resolve()):
        raise ValueError("stage outside the source repository")
    # Recheck before writing: a preview is not proof the source stayed unchanged.
    manifest = {"project": record["project"], "files": [{"source": f["source"], "destination": f["destination"]} for f in record["files"]]}
    if plan(root, manifest) != record:
        raise ValueError("source changed after preview")
    destination.mkdir(parents=True, exist_ok=True)
    for file in record["files"]:
        target = destination / file["destination"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / file["source"], target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != file["sha256"]:
            raise ValueError("source changed while staging; do not publish this staging directory")
    (destination / "SOURCE.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source", type=Path, default=Path.cwd())
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        record = plan(args.source, json.loads(args.manifest.read_text()))
        if args.apply:
            if args.destination is None:
                raise ValueError("--apply requires --destination")
            stage(args.source, args.destination, record)
        print(json.dumps(record, indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
