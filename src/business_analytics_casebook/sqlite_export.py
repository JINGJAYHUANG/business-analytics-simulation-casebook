from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, slugify_identifier


def export_sqlite(database_path: Path, input_dir: Path, output_tables: dict[str, list[dict[str, Any]]]) -> None:
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        for csv_path in sorted(input_dir.glob("*.csv")):
            rows = _read_csv(csv_path)
            _write_table(connection, "raw_" + slugify_identifier(csv_path.stem), rows)
        for table_name, rows in sorted(output_tables.items()):
            _write_table(connection, slugify_identifier(table_name), rows)
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            [
                ("schema_version", "1.0"),
                ("synthetic", "true"),
                ("project", "business-analytics-simulation-casebook"),
            ],
        )
        connection.commit()
    finally:
        connection.close()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_table(connection: sqlite3.Connection, table_name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = list(rows[0].keys())
    quoted_columns = ", ".join(f'"{column}" TEXT' for column in columns)
    connection.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    connection.execute(f'CREATE TABLE "{table_name}" ({quoted_columns})')
    placeholders = ",".join("?" for _ in columns)
    connection.executemany(
        f'INSERT INTO "{table_name}" VALUES ({placeholders})',
        [[_text(row.get(column)) for column in columns] for row in rows],
    )


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def sqlite_semantic_digest(database_path: Path) -> str:
    connection = sqlite3.connect(database_path)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        payload: list[dict[str, Any]] = []
        for table in tables:
            columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            rows = [list(row) for row in connection.execute(f'SELECT * FROM "{table}"')]
            rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, default=str))
            payload.append({"table": table, "columns": columns, "rows": rows})
        return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    finally:
        connection.close()
