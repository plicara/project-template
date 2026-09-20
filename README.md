# Plicara project template

A small repository contract for research that can be resumed and verified in its own checkout. The [contract](docs/contract.md) defines metadata, local instructions, skills, Python environments, and publication provenance.

```sh
make setup
make check
uv run --locked python tools/new_project.py ../my-study --id my-study --name 'My study' --description 'The question this study investigates.' --kind study --profile python
cd ../my-study
uv lock
make setup
make check
```

Profiles are `python`, `node`, and `docs`. For Node, run `npm install --package-lock-only --ignore-scripts` before setup; for docs, no project environment is required. Initialization refuses a nonempty destination and never changes an existing project. Python projects start without a package layout so an experiment does not need packaging boilerplate.

For a clean repository created with GitHub's template button, run `uv run --script tools/new_project.py . --in-place --id my-study --name 'My study' --description 'The question this study investigates.' --profile python`, then `uv lock`, `make setup`, and `make check`. Initialization replaces the template identity and removes the starter's own tools/tests; it refuses an already initialized or dirty checkout. Template updates do not overwrite consuming projects.

The shared validator lives in [.plicara/check.py](.plicara/check.py). It is vendored into each repository so checks do not depend on another checkout or the lab index. New project files and tooling are Apache-2.0; choose the appropriate project license before publishing.
