# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.2"]
# ///
"""Generate a project in an empty directory or initialize a fresh template clone."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml

TEMPLATE = Path(__file__).resolve().parents[1]


def create(destination: Path, identity: str, name: str, description: str, kind: str, profile: str) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identity):
        raise ValueError("id must use lowercase kebab-case")
    if not name.strip() or not description.strip():
        raise ValueError("name and description are required")
    if profile not in {"python", "node", "docs"}:
        raise ValueError(f"unknown profile: {profile}")
    if kind not in {"study", "tool", "benchmark", "dataset", "publication", "collection", "operations"}:
        raise ValueError(f"unknown kind: {kind}")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("destination must be a new or empty directory")
    destination.mkdir(parents=True, exist_ok=True)
    for file in (".plicara/check.py", ".plicara/check.py.lock", ".agents/skills/README.md", ".gitignore", "LICENSE"):
        target = destination / file
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATE / file, target)
    metadata = dict(schema_version=1, id=identity, name=name, description=description, kind=kind, status="planned")
    setup, check = "\tuv run --python 3.12 --locked --script .plicara/check.py\n", ""
    if profile == "python":
        metadata["python"] = ["."]
        (destination / "pyproject.toml").write_text(
            f'[project]\nname = {json.dumps(identity)}\nversion = "0.1.0"\n'
            f'description = {json.dumps(description)}\nrequires-python = ">=3.11"\ndependencies = []\n\n'
            '[tool.uv]\npackage = false\n'
        )
        (destination / ".python-version").write_text("3.12\n")
        setup = "\tuv sync --locked\n"
        check = "\tuv lock --check\n"
    elif profile == "node":
        (destination / "package.json").write_text(json.dumps({"name": identity, "version": "0.1.0", "private": True, "scripts": {"test": "node --test"}}, indent=2) + "\n")
        setup = "\tnpm ci --ignore-scripts\n"
        check = "\tnpm test\n"
    (destination / ".plicara/project.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (destination / "README.md").write_text(f"# {name}\n\n{description}\n\nStart with `make setup` and `make check`. Record reproduction commands and evidence as work develops. Lifecycle metadata is in `.plicara/project.yaml`.\n")
    (destination / ".plicara/README.md").write_text(f"# {name}: lab context\n\nStatus lives in [project.yaml](project.yaml). Keep implementation docs beside the code and link protocols and evidence here when they exist. Add dated decisions under `decisions/` only when needed.\n")
    (destination / "AGENTS.md").write_text(
        f"# Working in {name}\n\nRead `.plicara/project.yaml`, `.plicara/README.md`, and `README.md`. Work stays in this project unless the task explicitly includes another repository. Use `make setup` and `make check`; add relevant offline tests to `check` as code is introduced. The initial checks validate structure and environment only.\n\n"
        "Use uv for Python and the native locked package manager for other languages. Paid inference, long training, publication, and deployment are separate explicit operations. Keep scientific limitations and failed controls visible.\n\n"
        "Metadata changes only when project facts change. No central board update is required. Procedures belong in `.agents/skills/`; significant decisions are dated, append-only records in `.plicara/decisions/`. Preserve pre-existing changes and report verification limits.\n\n"
        "Use conventional branch prefixes and short kebab-case descriptions. Inspect staged changes for secrets before committing. Ask before destructive operations, publishing, or deployment. Write Markdown with one paragraph or list item per line.\n"
    )
    (destination / "Makefile").write_text(".PHONY: setup check\n\nsetup:\n" + setup + "\ncheck:\n\tuv run --python 3.12 --locked --script .plicara/check.py\n" + check)
    workflow = destination / ".github/workflows/check.yml"
    workflow.parent.mkdir(parents=True)
    node_setup = "      - uses: actions/setup-node@v4\n        with:\n          node-version: '22'\n" if profile == "node" else ""
    workflow.write_text("name: Check\non: [push, pull_request]\npermissions:\n  contents: read\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: astral-sh/setup-uv@v6\n" + node_setup + "      - run: make setup\n      - run: make check\n")


def initialize(destination: Path, identity: str, name: str, description: str, kind: str, profile: str) -> None:
    """Replace only starter files in a clean clone carrying the template identity."""
    metadata = destination / ".plicara/project.yaml"
    if yaml.safe_load(metadata.read_text()).get("id") != "plicara-project-template":
        raise ValueError("--in-place is only for an uninitialized template clone")
    if subprocess.check_output(["git", "-C", str(destination), "status", "--porcelain"], text=True).strip():
        raise ValueError("template clone must be clean before initialization")
    with tempfile.TemporaryDirectory(prefix="plicara-starter-") as temporary:
        staged = Path(temporary) / "project"
        create(staged, identity, name, description, kind, profile)
        for path in staged.rglob("*"):
            if path.is_file():
                target = destination / path.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    starter_only = ["tools/new_project.py", "tools/export_snapshot.py", "tests/test_contract.py", "tests/test_export.py", "docs/contract.md", "uv.lock"]
    if profile != "python":
        starter_only += ["pyproject.toml", ".python-version"]
    for file in starter_only:
        (destination / file).unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--kind", choices=["study", "tool", "benchmark", "dataset", "publication", "collection", "operations"], default="study")
    parser.add_argument("--profile", choices=["python", "node", "docs"], default="python")
    parser.add_argument("--in-place", action="store_true", help="initialize a clean repository made with GitHub's template button")
    args = parser.parse_args()
    try:
        action = initialize if args.in_place else create
        action(args.destination, args.id, args.name, args.description, args.kind, args.profile)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    print(f"Created {args.destination}. Generate the profile's lockfile, then run make setup and make check.")


if __name__ == "__main__":
    main()
