.PHONY: help setup dev-install install-edit lint format test build clean

PY = python
UV = uv
UVX = uvx

help:
	@echo "Makefile targets:"
	@echo "  make setup        -> create uv venv and install runtime + dev deps (dev only)"
	@echo "  make dev-install  -> install dev deps into venv"
	@echo "  make install-edit -> pip install -e . into venv"
	@echo "  make lint         -> run ruff"
	@echo "  make format       -> run black + isort"
	@echo "  make test         -> run pytest"
	@echo "  make build        -> build wheel & sdist"
	@echo "  make clean        -> remove build artifacts"

setup:
	@echo "Creating seeded virtualenv with uv..."
	$(UV) venv --seed
	@echo "Installing runtime deps (via uv add)..."
	$(UV) add --yes $(shell python - <<'PY'
import toml, sys
data = toml.load("pyproject.toml")
deps = data.get("project", {}).get("dependencies", [])
print(" ".join(deps))
PY
)

dev-install:
	$(UV) add --dev pytest ruff black isort pre-commit diskcache

install-edit:
	@echo "Installing package in editable mode into venv..."
	$(UV) pip install -e .

lint:
	@echo "Running ruff..."
	$(UVX) ruff .

format:
	@echo "Formatting with black + isort..."
	$(UVX) isort .
	$(UVX) black .

test:
	@echo "Running tests (pytest)..."
	$(UVX) pytest -q

build:
	@echo "Building wheel & sdist..."
	$(PY) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache
