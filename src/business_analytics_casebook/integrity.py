from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable

from .canonical import canonical_json_bytes, read_json, sha256_bytes, sha256_file, write_json
from .sqlite_export import sqlite_semantic_digest


class EventChain:
    def __init__(self, generated_at: str) -> None:
        self.generated_at = generated_at
        self.events: list[dict[str, Any]] = []
        self.previous_hash = "0" * 64

    def add(self, event_type: str, payload: dict[str, Any]) -> str:
        event = {
            "sequence": len(self.events) + 1,
            "generated_at": self.generated_at,
            "event_type": event_type,
            "previous_hash": self.previous_hash,
            "payload": payload,
        }
        event_hash = sha256_bytes(canonical_json_bytes(event))
        event["event_hash"] = event_hash
        self.events.append(event)
        self.previous_hash = event_hash
        return event_hash

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in self.events:
                handle.write(canonical_json_bytes(event).decode("utf-8"))


def verify_event_chain(path: Path) -> str:
    previous = "0" * 64
    expected_sequence = 1
    final_hash = previous
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            event = json.loads(line)
            event_hash = event.pop("event_hash")
            if event["sequence"] != expected_sequence:
                raise ValueError(f"event sequence mismatch at {expected_sequence}")
            if event["previous_hash"] != previous:
                raise ValueError(f"event previous_hash mismatch at sequence {expected_sequence}")
            calculated = sha256_bytes(canonical_json_bytes(event))
            if calculated != event_hash:
                raise ValueError(f"event hash mismatch at sequence {expected_sequence}")
            previous = event_hash
            final_hash = event_hash
            expected_sequence += 1
    return final_hash


def build_artifact_manifest(run_dir: Path, exclusions: set[str] | None = None) -> dict[str, Any]:
    exclusions = exclusions or set()
    artifacts = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        relative = path.relative_to(run_dir).as_posix()
        if relative in exclusions:
            continue
        artifacts.append({
            "path": relative,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {"schema_version": "1.0", "artifact_count": len(artifacts), "artifacts": artifacts}


def verify_run(run_dir: Path) -> dict[str, Any]:
    run_manifest_path = run_dir / "run_manifest.json"
    artifact_manifest_path = run_dir / "artifact_manifest.json"
    if not run_manifest_path.exists() or not artifact_manifest_path.exists():
        raise ValueError("run_manifest.json and artifact_manifest.json are required")
    run_manifest = read_json(run_manifest_path)
    artifact_manifest = read_json(artifact_manifest_path)
    expected_paths = {item["path"] for item in artifact_manifest["artifacts"]}
    actual_paths = {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.rglob("*")
        if path.is_file() and path.name not in {"artifact_manifest.json", "run_manifest.json"}
    }
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)
        raise ValueError(f"artifact set mismatch; missing={missing}; unexpected={unexpected}")
    for item in artifact_manifest["artifacts"]:
        path = run_dir / item["path"]
        if path.stat().st_size != item["size"]:
            raise ValueError(f"artifact size mismatch: {item['path']}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"artifact digest mismatch: {item['path']}")
    manifest_digest = sha256_file(artifact_manifest_path)
    if manifest_digest != run_manifest["artifact_manifest_sha256"]:
        raise ValueError("artifact manifest digest mismatch")
    final_hash = verify_event_chain(run_dir / "events.jsonl")
    if final_hash != run_manifest["final_event_hash"]:
        raise ValueError("final event hash mismatch")
    database = run_dir / "casebook.sqlite"
    if database.exists():
        semantic = sqlite_semantic_digest(database)
        if semantic != run_manifest["sqlite_semantic_sha256"]:
            raise ValueError("SQLite semantic digest mismatch")
    return {
        "status": "verified",
        "artifact_count": artifact_manifest["artifact_count"],
        "final_event_hash": final_hash,
        "run_id": run_manifest["run_id"],
    }


def copy_clean(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
