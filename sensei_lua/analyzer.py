"""Static analysis utilities for Lua source files.

This module implements lightweight heuristics to find a few common mistakes in
Lua scripts without relying on a full parser.  The goal is to provide quick
feedback for learners by highlighting indentation issues, trailing whitespace
and obvious block mismatches (e.g. a missing ``end``).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

__all__ = ["Issue", "analyze_source", "analyze_file", "format_issues"]


@dataclass(slots=True)
class Issue:
    """Represents a problem found in a Lua source file."""

    line: int
    column: int
    message: str
    code: str = "GENERIC"

    def __str__(self) -> str:  # pragma: no cover - trivial wrapper
        return f"L{self.line}:C{self.column} {self.code} {self.message}"


_BLOCK_PAIRS = {
    "function": "end",
    "do": "end",
    "then": "end",
    "repeat": "until",
}

_BLOCK_ENDINGS = {"end", "until"}


def analyze_file(path: Path | str, *, prefer_spaces: bool = True, indent_size: int = 4) -> List[Issue]:
    """Analyze the given Lua file and return the list of discovered issues."""

    source = Path(path).read_text(encoding="utf8")
    return analyze_source(source, prefer_spaces=prefer_spaces, indent_size=indent_size)


def analyze_source(source: str, *, prefer_spaces: bool = True, indent_size: int = 4) -> List[Issue]:
    """Analyze a Lua source string and return a list of :class:`Issue` objects."""

    issues: List[Issue] = []
    lines = source.splitlines()
    if source and not source.endswith("\n"):
        issues.append(Issue(len(lines) or 1, len(lines[-1]) + 1 if lines else 1, "Missing final newline", "FORMAT"))

    issues.extend(_check_indentation(lines, prefer_spaces, indent_size))
    issues.extend(_check_trailing_whitespace(lines))
    issues.extend(_check_block_balance(lines))
    return issues


def format_issues(issues: Sequence[Issue], *, color: bool = False) -> str:
    """Format the issues in a human-readable table."""

    if not issues:
        return "No issues found."

    parts = []
    for issue in issues:
        prefix = f"L{issue.line}:C{issue.column}"
        code = issue.code
        message = issue.message
        if color:
            prefix = f"\033[94m{prefix}\033[0m"
            code = f"\033[91m{code}\033[0m"
        parts.append(f"{prefix} {code} {message}")
    return "\n".join(parts)


def _check_indentation(lines: Sequence[str], prefer_spaces: bool, indent_size: int) -> Iterable[Issue]:
    for idx, line in enumerate(lines, start=1):
        stripped = line.lstrip(" \t")
        indent = line[: len(line) - len(stripped)]
        if not stripped:
            continue
        if " " in indent and "\t" in indent:
            yield Issue(idx, 1, "Mixed tabs and spaces in indentation", "INDENT")
            continue
        if prefer_spaces and "\t" in indent:
            first_tab = indent.index("\t") + 1
            yield Issue(idx, first_tab, "Tab indentation found (expected spaces)", "INDENT")
        if indent and indent.replace(" ", "") == indent:
            # Only tabs, already handled above when prefer_spaces is True.
            continue
        if indent and set(indent) == {" "} and (len(indent) % indent_size) != 0:
            yield Issue(idx, len(indent), f"Indentation width should be a multiple of {indent_size}", "INDENT")


def _check_trailing_whitespace(lines: Sequence[str]) -> Iterable[Issue]:
    for idx, line in enumerate(lines, start=1):
        if line.rstrip(" \t") != line:
            yield Issue(idx, len(line), "Trailing whitespace", "FORMAT")


def _check_block_balance(lines: Sequence[str]) -> Iterable[Issue]:
    stack: List[tuple[str, int]] = []
    for idx, raw_line in enumerate(lines, start=1):
        line = _strip_comments(raw_line)
        tokens = list(_tokenize(line))
        for token in tokens:
            if token in _BLOCK_PAIRS:
                stack.append((_BLOCK_PAIRS[token], idx))
            elif token in _BLOCK_ENDINGS:
                if not stack:
                    yield Issue(idx, _find_column(raw_line, token), f"Unexpected '{token}'", "SYNTAX")
                    continue
                expected, start_line = stack[-1]
                if expected != token:
                    yield Issue(idx, _find_column(raw_line, token), f"Expected '{expected}' opened at line {start_line}", "SYNTAX")
                    continue
                stack.pop()
    for expected, start_line in stack:
        yield Issue(start_line, 1, f"Unclosed block expecting '{expected}'", "SYNTAX")


def _strip_comments(line: str) -> str:
    result = []
    in_string: str | None = None
    i = 0
    while i < len(line):
        ch = line[i]
        nxt = line[i + 1] if i + 1 < len(line) else ""
        if not in_string and ch == "-" and nxt == "-":
            break
        if not in_string and ch in {'"', "'"}:
            in_string = ch
            result.append(" ")
        elif in_string:
            if ch == "\\":
                i += 1  # Skip escaped char
            elif ch == in_string:
                in_string = None
            result.append(" ")
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def _tokenize(line: str) -> Iterable[str]:
    word = []
    for ch in line:
        if ch.isalpha() or ch == "_":
            word.append(ch)
        else:
            if word:
                yield "".join(word)
                word.clear()
    if word:
        yield "".join(word)


def _find_column(line: str, token: str) -> int:
    idx = line.find(token)
    return idx + 1 if idx >= 0 else 1
