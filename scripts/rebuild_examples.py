from __future__ import annotations

import argparse
import filecmp
import shutil
import tempfile
from pathlib import Path

from business_analytics_casebook.runner import build_demo

FIXED_TIME = "2026-09-01T00:00:00Z"


def compare_trees(left: Path, right: Path) -> list[str]:
    failures: list[str] = []
    left_files = {p.relative_to(left).as_posix() for p in left.rglob("*") if p.is_file()}
    right_files = {p.relative_to(right).as_posix() for p in right.rglob("*") if p.is_file()}
    if left_files != right_files:
        failures.append(f"file-set mismatch left_only={sorted(left_files-right_files)} right_only={sorted(right_files-left_files)}")
    for relative in sorted(left_files & right_files):
        if (left / relative).read_bytes() != (right / relative).read_bytes():
            failures.append(f"content mismatch: {relative}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("examples/synthetic_company"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp) / "synthetic_company"
            build_demo(generated, FIXED_TIME, overwrite=True)
            failures = compare_trees(args.root.resolve(), generated)
            if failures:
                print("\n".join(failures))
                return 1
            print("committed synthetic example matches deterministic rebuild")
            return 0
    build_demo(args.root, FIXED_TIME, overwrite=True)
    print(f"rebuilt {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
