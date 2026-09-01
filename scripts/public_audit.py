from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".toml", ".yml", ".yaml", ".sql", ".txt", ".cff"}
EXCLUDED_DIRS = {".git", ".venv", "build", "dist", "__pycache__", ".local"}
PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "user_path": re.compile(r"(?:[A-Za-z]:\\Users\\[^\\\s]+|/Users/[^/\s]+|/home/[^/\s]+)"),
    "private_identity": re.compile(r"\b(?:HuangJingjie|Jingjie Huang|Buhi Supply)\b", re.I),
}


def scan(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "scripts/public_audit.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                if name == "email" and match.group(0).endswith("@example.invalid"):
                    continue
                findings.append({
                    "rule": name,
                    "path": path.relative_to(root).as_posix(),
                    "line": text.count("\n", 0, match.start()) + 1,
                })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()
    findings = scan(args.root.resolve())
    if findings:
        for finding in findings:
            print(f"{finding['rule']} {finding['path']}:{finding['line']}")
        return 1
    count = sum(
        1
        for path in args.root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and not any(part in EXCLUDED_DIRS for part in path.parts)
    )
    print(f"public audit passed: {count} text files scanned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
