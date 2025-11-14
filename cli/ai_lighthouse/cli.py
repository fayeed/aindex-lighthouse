# ai_lighthouse/ai_lighthouse/cli.py
import typer
from typing import Optional
import importlib
import pkgutil

app = typer.Typer(help="AI Lighthouse CLI")

@app.command("version")
def version():
    """
    Print package versions and module info for quick verification.
    """
    try:
        core = importlib.import_module("ai_lighthouse_core")
        core_info = getattr(core, "__file__", "ai_lighthouse_core (no __file__)")
    except Exception as e:
        core_info = f"Import error: {e}"

    try:
        lighthouse = importlib.import_module("ai_lighthouse")
        lh_info = getattr(lighthouse, "__file__", "ai_lighthouse (no __file__)")
    except Exception as e:
        lh_info = f"Import error: {e}"

    typer.echo(f"ai_lighthouse_core -> {core_info}")
    typer.echo(f"ai_lighthouse -> {lh_info}")

@app.command("audit")
def audit(url: str, depth: int = 1):
    """
    Placeholder audit command — replace with real audit runner later.
    """
    typer.echo(f"Would run audit on: {url} (depth={depth})")
    # Example: import your crawler or runner here:
    # from ai_lighthouse.audit import run_audit
    # run_audit(url, depth=depth)
