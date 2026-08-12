#!/usr/bin/env python3
"""Guard public artifacts for hygiene leaks before commit or CI publication."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

PUBLIC_TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".ini",
    ".md",
    ".rst",
    ".txt",
    ".toml",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", "dist", "build"}

LITERAL_ESCAPED_NEWLINE_SUFFIXES = {"", ".md", ".rst", ".txt", ".yaml", ".yml"}
PLACEHOLDER_VALUES = {
    "",
    "pass",
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "public_key",
    "example",
    "example_password",
    "dummy",
    "test",
    "setdata",
    "changeme",
    "redacted",
    "placeholder",
    "user",
}

INTERNAL_AUTOMATION_NAME = "open" + "claw"
RUNTIME_CONTEXT_NAME = "Subagent" + " Context"
KANBAN_TOOLING_RE = "pl" + "anka|board" + "Id|list" + "Id|card" + "Id"

LOCAL_OR_INTERNAL_PATTERNS = [
    ("internal automation marker", re.compile(r"\b" + INTERNAL_AUTOMATION_NAME + r"\b", re.IGNORECASE)),
    ("local state path", re.compile(r"(?:~|/home/[^\s`'\"]+)/\." + INTERNAL_AUTOMATION_NAME + r"\b", re.IGNORECASE)),
    ("local home path", re.compile(r"/home/[A-Za-z0-9._-]+/[^\s`'\"]*", re.IGNORECASE)),
    ("mac local path", re.compile(r"/Users/[A-Za-z0-9._-]+/[^\s`'\"]*", re.IGNORECASE)),
    ("windows local path", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s`'\"]+", re.IGNORECASE)),
]

PROMPT_OR_BOARD_PATTERNS = [
    ("prompt leakage", re.compile(r"\b(system|developer|subagent) prompt\b", re.IGNORECASE)),
    ("runtime context leakage", re.compile(r"\b" + RUNTIME_CONTEXT_NAME + r"\b", re.IGNORECASE)),
    ("kanban tooling leakage", re.compile(r"\b(" + KANBAN_TOOLING_RE + r")\b", re.IGNORECASE)),
    ("private board/card id", re.compile(r"\b176\d{16}\b")),
]

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("aws access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b")),
    ("github fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("gitlab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("openai token", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("bearer token", re.compile(r"\bBearer\s+(?!<|\$\{|TOKEN\b|REDACTED\b)[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE)),
]

SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(?P<key>api[_-]?key|auth[_-]?token|access[_-]?token|secret|password|priv(?:ate)?[_-]?key)\b"
    r"\s*[:=]\s*"
    r"(?P<quote>[\"'])?(?P<value>[^\s,\"'`#}]+)",
    re.IGNORECASE,
)

HEX_VALUE_RE = re.compile(r"^[0-9a-fA-F]{32,}$")
HIGH_ENTROPY_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9_./+=-]{24,}$")


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz"}:
        return False
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def git_files() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line for line in proc.stdout.splitlines() if line]


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if not path.is_file():
        return True
    return not is_probably_text(path)


def is_placeholder(value: str) -> bool:
    clean = value.strip().strip("'\"`<>{}[](),.;")
    normalized = clean.lower().replace("-", "_")
    return normalized in PLACEHOLDER_VALUES or normalized.startswith("example_")


def suspicious_assignment_value(value: str) -> bool:
    clean = value.strip().strip("'\"`<>{}[](),.;")
    if is_placeholder(clean):
        return False
    if clean.startswith(("$", "${", "os.environ", "env.")):
        return False
    return bool(HEX_VALUE_RE.match(clean) or HIGH_ENTROPY_RE.match(clean))


def iter_findings(label: str, text: str, suffix: str) -> Iterable[tuple[int, str, str]]:
    if suffix in LITERAL_ESCAPED_NEWLINE_SUFFIXES:
        for line_no, line in enumerate(text.splitlines(), start=1):
            if r"\n" in line:
                yield line_no, "literal escaped newline", "replace backslash-n text with a real line break"

    for name, pattern in LOCAL_OR_INTERNAL_PATTERNS + PROMPT_OR_BOARD_PATTERNS + SECRET_PATTERNS:
        for match in pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            yield line_no, name, "remove or redact this before publishing"

    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        value = match.group("value")
        if suspicious_assignment_value(value):
            line_no = text.count("\n", 0, match.start()) + 1
            yield line_no, "secret-looking assignment", "use a placeholder or environment variable"


def check_text(label: str, text: str, suffix: str = "") -> list[str]:
    findings = []
    for line_no, name, advice in iter_findings(label, text, suffix.lower()):
        findings.append(f"{label}:{line_no}: {name}: {advice}")
    return findings


def check_paths(paths: Sequence[str]) -> list[str]:
    findings: list[str] = []
    for raw_path in paths:
        path = Path(raw_path)
        if should_skip(path):
            continue
        suffix = path.suffix.lower()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            findings.append(f"{raw_path}:0: read error: {exc}")
            continue
        findings.extend(check_text(raw_path, text, suffix))
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Files to scan; defaults to git-tracked files with --all")
    parser.add_argument("--all", action="store_true", help="Scan all git-tracked files")
    parser.add_argument("--stdin", action="store_true", help="Scan text from standard input")
    parser.add_argument("--label", default="stdin", help="Label to display for --stdin findings")
    args = parser.parse_args(argv)

    if args.stdin:
        findings = check_text(args.label, sys.stdin.read(), Path(args.label).suffix)
    else:
        files = git_files() if args.all or not args.files else list(args.files)
        findings = check_paths(files)

    if findings:
        print("Public artifact hygiene guard found issues:", file=sys.stderr)
        for finding in findings:
            print(f"  {finding}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
