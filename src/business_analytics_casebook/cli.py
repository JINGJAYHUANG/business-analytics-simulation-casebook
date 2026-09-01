from __future__ import annotations

import argparse
import json
import shutil
from importlib import resources
from pathlib import Path

from . import __version__
from .canonical import canonical_json_bytes, read_json, write_json
from .contracts import validate_data_directory
from .integrity import verify_run
from .runner import build_demo, compare_runs, run_casebook
from .synthetic import generate_synthetic_company


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="basc",
        description="Run original synthetic business analytics cases with auditable outputs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate and run the complete synthetic company casebook.")
    demo.add_argument("--root", type=Path, required=True)
    demo.add_argument("--fixed-time", required=True)
    demo.add_argument("--overwrite", action="store_true")

    generate = sub.add_parser("generate", help="Generate deterministic synthetic source data.")
    generate.add_argument("--data-dir", type=Path, required=True)
    generate.add_argument("--overwrite", action="store_true")

    run = sub.add_parser("run", help="Run all four analytical cases from a data directory.")
    run.add_argument("--data-dir", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--fixed-time", required=True)
    run.add_argument("--overwrite", action="store_true")

    validate = sub.add_parser("validate", help="Validate source files and metric contracts.")
    validate.add_argument("--data-dir", type=Path, required=True)
    validate.add_argument("--json", action="store_true")

    verify = sub.add_parser("verify", help="Verify an output bundle, hashes, event chain, and SQLite semantics.")
    verify.add_argument("--run-dir", type=Path, required=True)

    inspect = sub.add_parser("inspect", help="Inspect the public case catalog.")
    inspect.add_argument("case_id", nargs="?")
    inspect.add_argument("--json", action="store_true")

    compare = sub.add_parser("compare", help="Compare two complete run directories.")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--output", type=Path)

    init = sub.add_parser("init", help="Preview or create an empty project data directory.")
    init.add_argument("--target", type=Path, required=True)
    init.add_argument("--apply", action="store_true")
    return parser


def _catalog() -> dict[str, object]:
    text = resources.files("business_analytics_casebook").joinpath("catalog/cases.json").read_text(encoding="utf-8")
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "demo":
            result = build_demo(args.root, args.fixed_time, overwrite=args.overwrite)
            print(canonical_json_bytes(result).decode("utf-8"), end="")
            return 0
        if args.command == "generate":
            if args.data_dir.exists() and any(args.data_dir.iterdir()):
                if not args.overwrite:
                    raise FileExistsError(f"data directory is not empty: {args.data_dir}")
                shutil.rmtree(args.data_dir)
            result = generate_synthetic_company(args.data_dir)
            print(canonical_json_bytes(result).decode("utf-8"), end="")
            return 0
        if args.command == "run":
            result = run_casebook(args.data_dir, args.output_dir, args.fixed_time, overwrite=args.overwrite)
            print(canonical_json_bytes(result).decode("utf-8"), end="")
            return 0
        if args.command == "validate":
            findings = validate_data_directory(args.data_dir)
            payload = {
                "errors": sum(1 for item in findings if item["severity"] == "error"),
                "warnings": sum(1 for item in findings if item["severity"] == "warning"),
                "findings": findings,
            }
            if args.json:
                print(canonical_json_bytes(payload).decode("utf-8"), end="")
            else:
                print(f"errors={payload['errors']} warnings={payload['warnings']}")
                for item in findings:
                    print(f"{item['severity'].upper()} {item['rule_id']} {item['file']}: {item['message']}")
            return 1 if payload["errors"] else 0
        if args.command == "verify":
            print(canonical_json_bytes(verify_run(args.run_dir)).decode("utf-8"), end="")
            return 0
        if args.command == "inspect":
            catalog = _catalog()
            cases = catalog["cases"]
            if args.case_id:
                matches = [item for item in cases if item["case_id"] == args.case_id]
                if not matches:
                    raise KeyError(f"unknown case_id: {args.case_id}")
                payload = matches[0]
            else:
                payload = catalog
            if args.json:
                print(canonical_json_bytes(payload).decode("utf-8"), end="")
            else:
                if args.case_id:
                    print(f"{payload['case_id']}: {payload['title']}\nDecision: {payload['decision']}\nUnit: {payload['unit_of_analysis']}")
                else:
                    for item in cases:
                        print(f"{item['case_id']}: {item['title']}")
            return 0
        if args.command == "compare":
            payload = compare_runs(args.baseline, args.candidate)
            if args.output:
                write_json(args.output, payload)
            print(canonical_json_bytes(payload).decode("utf-8"), end="")
            return 0
        if args.command == "init":
            preview = {
                "target": args.target.as_posix(),
                "will_create": [
                    "casebook_config.json",
                    "metric_contracts.json",
                    "supply_chain_lanes.csv",
                    "orders.csv",
                    "order_lines.csv",
                    "invoices.csv",
                    "payments.csv",
                    "returns.csv",
                    "experiment_cells.csv",
                    "qa_events.csv",
                ],
                "applied": bool(args.apply),
            }
            if args.apply:
                if args.target.exists() and any(args.target.iterdir()):
                    raise FileExistsError(f"target directory is not empty: {args.target}")
                generate_synthetic_company(args.target)
            print(canonical_json_bytes(preview).decode("utf-8"), end="")
            return 0
    except (FileNotFoundError, FileExistsError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2
    return 2
