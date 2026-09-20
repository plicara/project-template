.PHONY: setup metadata test check

setup:
	uv sync --locked

metadata:
	uv run --python 3.12 --locked --script .plicara/check.py

test:
	uv run --locked python -m unittest discover -s tests -v

check: metadata test
	uv lock --check
