from __future__ import annotations

import argparse
import gzip
import os
import tarfile
import tomllib
import zipfile
from pathlib import Path

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".bootstrap",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def project_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def source_files(root: Path, output_dir: Path) -> list[Path]:
    output_dir = output_dir.resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if output_dir == resolved or output_dir in resolved.parents:
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def normalized_mode(path: Path) -> int:
    return 0o755 if os.access(path, os.X_OK) and path.suffix in {".py", ".sh"} else 0o644


def build_tar(root: Path, files: list[Path], destination: Path, prefix: str, epoch: int) -> None:
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in files:
                    relative = path.relative_to(root).as_posix()
                    info = archive.gettarinfo(str(path), arcname=f"{prefix}/{relative}")
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = epoch
                    info.mode = normalized_mode(path)
                    info.pax_headers = {}
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)


def build_zip(root: Path, files: list[Path], destination: Path, prefix: str, epoch: int) -> None:
    import datetime as dt

    stamp = dt.datetime.fromtimestamp(max(epoch, 315532800), tz=dt.timezone.utc)
    date_time = (stamp.year, stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = normalized_mode(path) << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    version = project_version(root)
    prefix = f"business-analytics-simulation-casebook-{version}"
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", "1788220800"))
    files = source_files(root, output_dir)
    build_tar(root, files, output_dir / f"{prefix}.tar.gz", prefix, epoch)
    build_zip(root, files, output_dir / f"{prefix}.zip", prefix, epoch)
    print(f"release_source_files={len(files)} version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
