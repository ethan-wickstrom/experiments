"""frond: an RLM-centric coding agent for the terminal, built on DSPy."""

__version__ = "0.1.0"


def main() -> None:
    from frond.cli import main as cli_main

    raise SystemExit(cli_main())
