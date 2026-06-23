"""Backward-compatible wrapper for the legacy city-name CLI."""

from __future__ import annotations

import sys

from cli import main as cli_main


def main() -> int:
    if len(sys.argv) < 2:
        print("Pass 'city name' as an argument.")
        print("Example: python customizesvg.py \"Your City Name\"")
        print("For full options, use: python cli.py generate --help")
        return 1

    city = sys.argv[1]
    sys.argv = ["customizesvg.py", "generate", "--quick", "--city", city]
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())