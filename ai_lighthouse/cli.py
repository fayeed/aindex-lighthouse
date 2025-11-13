import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def scan(url: str):
    console.print(f"[green]Scanning:[/green] {url}")
    # wire into fetcher/parser/rules...
    console.print("[yellow]Not implemented yet: run the pipeline to build audit.json[/yellow]")

if __name__ == "__main__":
    app()
