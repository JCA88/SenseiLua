"""Command line interface for the SenseiLua analyzer."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyzer import analyze_file, format_issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Static analysis helper for Lua scripts")
    parser.add_argument("paths", nargs="+", type=Path, help="Lua files to analyze")
    parser.add_argument("--indent-size", type=int, default=4, help="Expected indentation width (spaces)")
    parser.add_argument(
        "--allow-tabs",
        action="store_true",
        help="Allow tabs in indentation (default disallows them)",
    )
    parser.add_argument("--color", action="store_true", help="Colorize the output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exit_code = 0
    for path in args.paths:
        if not path.exists():
            print(f"{path}: file not found", file=sys.stderr)
            exit_code = 2
            continue
        issues = analyze_file(path, prefer_spaces=not args.allow_tabs, indent_size=args.indent_size)
        header = f"== {path} =="
        print(header)
        print(format_issues(issues, color=args.color))
        if issues:
            exit_code = 1
    return exit_code


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
