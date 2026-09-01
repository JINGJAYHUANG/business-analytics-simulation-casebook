from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Callable

from business_analytics_casebook.integrity import verify_run


def _expect_failure(source: Path, name: str, mutate: Callable[[Path], None]) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "run"
        shutil.copytree(source, target)
        mutate(target)
        try:
            verify_run(target)
        except Exception as exc:  # deliberate adversarial test
            return {"attack": name, "detected": "true", "error": type(exc).__name__}
        return {"attack": name, "detected": "false", "error": ""}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source = args.run_dir.resolve()
    attacks = [
        _expect_failure(source, "alter_input", lambda root: (root / "inputs" / "orders.csv").write_text("tampered\n", encoding="utf-8")),
        _expect_failure(source, "alter_summary", lambda root: (root / "executive" / "summary.json").write_text("{}\n", encoding="utf-8")),
        _expect_failure(source, "delete_event", _delete_first_event),
        _expect_failure(source, "reorder_events", _swap_events),
        _expect_failure(source, "alter_sqlite", _alter_sqlite),
        _expect_failure(source, "inject_undeclared_output", lambda root: (root / "undeclared.txt").write_text("unexpected", encoding="utf-8")),
    ]
    payload = {
        "attacks": attacks,
        "detected": sum(1 for item in attacks if item["detected"] == "true"),
        "total": len(attacks),
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if payload["detected"] == payload["total"] else 1


def _delete_first_event(root: Path) -> None:
    path = root / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[1:]) + "\n", encoding="utf-8")


def _swap_events(root: Path) -> None:
    path = root / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[1], lines[2] = lines[2], lines[1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _alter_sqlite(root: Path) -> None:
    path = root / "casebook.sqlite"
    connection = sqlite3.connect(path)
    try:
        connection.execute("UPDATE metadata SET value='false' WHERE key='synthetic'")
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
