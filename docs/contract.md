# Plicara project contract, version 1

Each maintained repository owns its instructions, code, evidence, and metadata. Ordinary project work never requires a change to a central board, website, organization profile, or sibling checkout. The lab index is generated and disposable.

## Files

Every repository has `README.md`, `AGENTS.md`, `.agents/skills/README.md`, `.plicara/project.yaml`, `.plicara/README.md`, `.plicara/check.py`, and a Makefile with `setup` and `check` targets. The public README explains usage; the lab README links research context and evidence without copying it. Significant decisions are dated, append-only records under `.plicara/decisions/`; notes are optional and explicitly exploratory.

The validator is a versioned, vendored copy of this template's `.plicara/check.py`. This lets an isolated checkout validate itself. Its script dependencies are exactly pinned. Change the canonical script here, test it, and explicitly copy that version into repositories adopting the change. Existing projects do not require routine template synchronization.

## Metadata

Required fields are `schema_version: 1`, a stable kebab-case `id`, `name`, a one-sentence `description`, `kind`, and `status`. IDs identify a project across moves; directory and repository names need not match them.

- Kinds: `study`, `tool`, `benchmark`, `dataset`, `publication`, `collection`, `operations`.
- Statuses: `planned` (not started), `active` (under investigation/development), `maintained` (usable and maintained), `paused` (deliberately suspended), `completed` (bounded work concluded), `archived` (frozen).
- Paused and archived projects carry a `reason`; paused projects also carry `resume_when`.
- `repository` is an optional HTTPS repository URL. Local clones may live anywhere.
- `readme` optionally identifies an existing project README at another relative path. Preserve an ongoing documentation reorganization rather than creating a competing README.
- `artifacts` is a list of `{kind, path}` or `{kind, url}` mappings. Paths are relative to the project and must exist; URLs use HTTPS. No automatic network check is implied.
- `related` is a list of `{id, relationship}` mappings. A published snapshot has its own ID and relates to its source with `published-snapshot-of`.
- `projects` lists explicit child project directories in a collection. Children have their own metadata, READMEs, AGENTS.md, and skills folder. They inherit repository tooling; do not duplicate the validator. Vendored dependencies, run folders, and archived interiors are not automatically projects.
- `python` lists independently managed Python environment directories, relative to this project. Each has `pyproject.toml`, `uv.lock`, and `.python-version`. Declare an environment once, at its owning project.

Do not store package versions, test counts, CI state, Git synchronization, file lists, or maintenance timestamps in metadata. Those already have authoritative sources. Published is an artifact property rather than a lifecycle status.

## Working conventions

Use uv for maintained Python work. `make setup` installs the locked default development environment; `make check` runs local metadata checks and the repository's normal offline verification. Lockfile changes are intentional. Additional model, GPU, browser, dataset, and research environments may have explicit setup targets. Preserve compatibility test matrices instead of reducing supported Python versions to the development interpreter.

CI should invoke the same commands or their documented components. No routine check starts paid inference, long training, deployment, or publication. Reproduction that needs external datasets states that prerequisite explicitly.

AGENTS.md contains scope, constraints, and commands. Repeatable procedures belong in `.agents/skills/<name>/SKILL.md`; leave the folder unpopulated until there is a procedure to preserve. Existing scientific constraints and upstream contribution rules take precedence over generic template defaults.

## Publication and provenance

Private workbench projects own their drafts and research. Public article/benchmark repositories hold reviewed release snapshots. Export a defined allowlist of tracked files from a clean source revision; record the source repository, project path, commit, and output hashes in the release. Hidden `.plicara` files are not a privacy boundary. Private notes and local metadata do not ship unless explicitly selected for public disclosure.

Corrections start in the source project and produce a new reviewed snapshot. Preserve existing dataset hashes, scoring checks, source manifests, and publication tests. A metadata migration is not authorization to republish research.

## Template lifecycle

A GitHub template supplies initial files, not ongoing inheritance. `tools/new_project.py` creates a new project in an empty directory with a Python, Node, or documentation profile. Its explicit `--in-place` mode initializes a clean template clone, replaces the starter identity, and removes template-only tools/tests. It does not create a GitHub repository or push anything. Review the generated identity and license before publishing. An existing research repository is migrated explicitly; never overwrite its AGENTS.md or skills with template defaults.

## Lab views

`foundation_lab` owns shared conventions, lab-level decisions, and the read-only inventory tool. Discovery reads project metadata; Git state is measured separately. A cached upstream comparison must be labelled cached. A failed fetch or unavailable GitHub inventory is unknown, not synchronized or complete. Generated private inventory is ignored by Git. Public views require an explicit publication allowlist.
