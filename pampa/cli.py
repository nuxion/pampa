"""Command-line entry point for Pampa."""
import click
from pampa.core import chat_assistant

@click.command()
def main() -> None:
    """Start the interactive Pampa coding assistant."""
    chat_assistant()


if __name__ == "__main__":
    main()
