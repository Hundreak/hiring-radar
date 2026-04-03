import typer

app = typer.Typer(no_args_is_help=True, help="Hiring Radar CLI")


@app.command()
def crawl() -> None:
    """Run configured job source crawls."""
    typer.echo("TODO: crawl command will be implemented in the next step.")


@app.command()
def export() -> None:
    """Export stored jobs to CSV."""
    typer.echo("TODO: export command will be implemented in a later step.")


@app.command()
def summary() -> None:
    """Show a short crawl / jobs summary."""
    typer.echo("TODO: summary command will be implemented in a later step.")


if __name__ == "__main__":
    app()
