from __future__ import annotations

import argparse
import re
from pathlib import Path

LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    failures: list[str] = []
    checked = 0
    for path in sorted(root.rglob("*.md")):
        if any(part in {".git", ".venv", "build", "dist"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            checked += 1
            resolved = (path.parent / clean).resolve()
            if root not in (resolved, *resolved.parents):
                failures.append(f"link escapes repository: {path.relative_to(root)} -> {target}")
            elif not resolved.exists():
                failures.append(f"missing link: {path.relative_to(root)} -> {target}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"markdown link audit passed: {checked} internal links checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
