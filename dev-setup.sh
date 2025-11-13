#!/usr/bin/env bash
set -euo pipefail

echo "1) Create seeded venv (uv venv --seed)"
uv venv --seed

echo "2) Add runtime deps via uv"
uv add typer rich httpx[http2] beautifulsoup4 lxml extruct pyld pydantic jsonschema tldextract

echo "3) Add dev deps"
uv add --dev pytest ruff black isort pre-commit diskcache

echo "4) Install package in editable mode"
uv pip install -e .

echo ""
echo "Dev environment ready."
echo "Use 'uvx <tool>' to run tools (e.g. uvx ruff ., uvx pytest)."
