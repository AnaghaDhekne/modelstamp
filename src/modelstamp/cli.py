"""Command-line interface for inspecting modelstamp artifacts safely."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .core import check, inspect, verify
from .exceptions import ArtifactIntegrityError, ManifestError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="modelstamp")
    parser.add_argument(
        "--version", action="version", version=f"modelstamp {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("inspect", "print the manifest without loading the model"),
        ("check", "check integrity and runtime compatibility"),
        ("verify", "verify artifact size and SHA-256"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("path")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            print(json.dumps(inspect(args.path).to_dict(), indent=2))
            return 0
        if args.command == "verify":
            verify(args.path)
            print("Artifact integrity verified.")
            return 0
        report = check(args.path)
        print(report)
        return 1 if report else 0
    except (ArtifactIntegrityError, ManifestError) as exc:
        print(f"modelstamp: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
