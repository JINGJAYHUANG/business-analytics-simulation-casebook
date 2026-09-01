from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .accounting import analyze_accounting
from .canonical import canonical_json_bytes, parse_timestamp, read_json, sha256_bytes, sha256_file, write_csv, write_json
from .clustering import analyze_supply_chain
from .contracts import raise_for_errors, validate_data_directory
from .experiment import analyze_experiment
from .integrity import EventChain, build_artifact_manifest, copy_clean, verify_run
from .quality import analyze_quality
from .reporting import render_accounting, render_executive, render_experiment, render_quality, render_supply_chain
from .sqlite_export import export_sqlite, sqlite_semantic_digest
from .synthetic import generate_synthetic_company


def _prepare_directory(path: Path, overwrite: bool) -> None:
    if path.exists():
        if any(path.iterdir()) and not overwrite:
            raise FileExistsError(f"output directory is not empty: {path}")
        if overwrite:
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _copy_inputs(data_dir: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for source in sorted(path for path in data_dir.iterdir() if path.is_file()):
        target = destination / source.name
        shutil.copy2(source, target)
        files.append({
            "path": source.name,
            "size": target.stat().st_size,
            "sha256": sha256_file(target),
        })
    manifest = {"schema_version": "1.0", "files": files, "file_count": len(files)}
    write_json(destination / "input_manifest.json", manifest)
    return manifest


def _normalize_findings(results: dict[str, dict[str, Any]], validation: list[dict[str, str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in validation:
        findings.append({
            "case_id": "data_contract",
            "finding_id": f"DATA-{len(findings)+1:03d}",
            "severity": item.get("severity", "warning"),
            "rule_id": item.get("rule_id", "DATA_VALIDATION"),
            "message": item.get("message", ""),
            "impact": f"Data contract issue in {item.get('file', 'unknown file')}.",
            "remediation": "Correct the source contract or quarantine the affected row before decision use.",
        })
    for case_id, result in results.items():
        for item in result.get("findings", []):
            findings.append({
                "case_id": case_id,
                "finding_id": item.get("finding_id", f"{case_id.upper()}-{len(findings)+1:03d}"),
                "severity": item.get("severity", "info"),
                "rule_id": item.get("rule_id", "CASE_FINDING"),
                "message": item.get("message", item.get("title", "")),
                "impact": item.get("impact", item.get("detail", "")),
                "remediation": item.get("remediation", "Preserve the limitation in the decision record."),
            })
    return findings


def run_casebook(data_dir: Path, output_dir: Path, fixed_time: str, overwrite: bool = False) -> dict[str, Any]:
    generated_at = parse_timestamp(fixed_time).isoformat().replace("+00:00", "Z")
    validation = validate_data_directory(data_dir)
    raise_for_errors(validation)
    _prepare_directory(output_dir, overwrite=overwrite)
    inputs_dir = output_dir / "inputs"
    input_manifest = _copy_inputs(data_dir, inputs_dir)

    identity_payload = {"generated_at": generated_at, "inputs": input_manifest["files"]}
    run_id = "BASC-" + sha256_bytes(canonical_json_bytes(identity_payload))[:16]
    chain = EventChain(generated_at)
    chain.add("run_started", {"run_id": run_id, "input_file_count": input_manifest["file_count"]})
    chain.add("data_contract_validated", {
        "errors": 0,
        "warnings": sum(1 for item in validation if item.get("severity") == "warning"),
    })

    supply = analyze_supply_chain(inputs_dir / "supply_chain_lanes.csv")
    chain.add("case_completed", {"case_id": "supply_chain", "selected_k": supply["selected_k"]})
    accounting = analyze_accounting(inputs_dir)
    chain.add("case_completed", {"case_id": "accounting", "completed_orders": accounting["summary"]["completed_orders"]})
    experiment = analyze_experiment(inputs_dir / "experiment_cells.csv")
    chain.add("case_completed", {"case_id": "experiment", "decision": experiment["decision"]["status"]})
    quality = analyze_quality(inputs_dir / "qa_events.csv")
    chain.add("case_completed", {"case_id": "quality", "decision": quality["decision"]["status"]})
    results = {
        "supply_chain": supply,
        "accounting": accounting,
        "experiment": experiment,
        "quality": quality,
    }
    findings = _normalize_findings(results, validation)

    _write_supply_chain(output_dir / "supply_chain", supply)
    _write_accounting(output_dir / "accounting", accounting)
    _write_experiment(output_dir / "experiment", experiment)
    _write_quality(output_dir / "quality", quality)

    executive_md, executive_html, decisions = render_executive(results, findings)
    executive_dir = output_dir / "executive"
    executive_dir.mkdir(parents=True, exist_ok=True)
    (executive_dir / "quarterly_report.md").write_text(executive_md, encoding="utf-8", newline="\n")
    (executive_dir / "quarterly_report.html").write_text(executive_html, encoding="utf-8", newline="\n")
    write_csv(executive_dir / "decision_register.csv", decisions)
    write_csv(executive_dir / "findings.csv", findings)
    write_json(executive_dir / "summary.json", _executive_summary(run_id, generated_at, results, findings))
    chain.add("executive_report_generated", {"decision_count": len(decisions), "finding_count": len(findings)})

    output_tables = {
        "supply_chain_assignments": supply["assignments"],
        "supply_chain_profiles": supply["profiles"],
        "accounting_order_fact": accounting["order_fact"],
        "accounting_channel_summary": accounting["channel_summary"],
        "experiment_segments": experiment["segments"],
        "quality_weekly_metrics": quality["weekly_metrics"],
        "quality_workflow_details": quality["workflow_details"],
        "quality_root_causes": quality["root_causes"],
        "decision_register": decisions,
        "findings": findings,
    }
    database_path = output_dir / "casebook.sqlite"
    export_sqlite(database_path, inputs_dir, output_tables)
    sqlite_digest = sqlite_semantic_digest(database_path)
    chain.add("sqlite_exported", {"table_count": len(output_tables) + len(list(inputs_dir.glob('*.csv'))) + 1, "semantic_sha256": sqlite_digest})
    final_event_hash = chain.add("run_completed", {"run_id": run_id, "status": "complete"})
    chain.write(output_dir / "events.jsonl")

    artifact_manifest = build_artifact_manifest(
        output_dir,
        exclusions={"artifact_manifest.json", "run_manifest.json"},
    )
    write_json(output_dir / "artifact_manifest.json", artifact_manifest)
    run_manifest = {
        "schema_version": "1.0",
        "project": "business-analytics-simulation-casebook",
        "version": "0.1.0",
        "run_id": run_id,
        "generated_at": generated_at,
        "synthetic": True,
        "input_manifest_sha256": sha256_file(inputs_dir / "input_manifest.json"),
        "artifact_manifest_sha256": sha256_file(output_dir / "artifact_manifest.json"),
        "sqlite_semantic_sha256": sqlite_digest,
        "final_event_hash": final_event_hash,
        "case_ids": ["supply_chain", "accounting", "experiment", "quality"],
        "artifact_count": artifact_manifest["artifact_count"],
    }
    write_json(output_dir / "run_manifest.json", run_manifest)
    verification = verify_run(output_dir)
    return {
        "run_id": run_id,
        "generated_at": generated_at,
        "output_dir": output_dir.as_posix(),
        "artifact_count": verification["artifact_count"],
        "findings": len(findings),
        "decisions": len(decisions),
        "verification": verification["status"],
    }


def _write_supply_chain(directory: Path, result: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "summary.json", {
        "selected_k": result["selected_k"],
        "selected_silhouette": result["selected_silhouette"],
        "lane_count": len(result["assignments"]),
        "segment_count": len(result["profiles"]),
    })
    write_csv(directory / "k_selection.csv", result["k_selection"])
    write_csv(directory / "lane_assignments.csv", result["assignments"])
    write_csv(directory / "cluster_profiles.csv", result["profiles"])
    write_csv(directory / "policy_actions.csv", result["policies"])
    write_json(directory / "findings.json", result["findings"])
    md, html_text = render_supply_chain(result)
    (directory / "report.md").write_text(md, encoding="utf-8", newline="\n")
    (directory / "report.html").write_text(html_text, encoding="utf-8", newline="\n")


def _write_accounting(directory: Path, result: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "summary.json", result["summary"])
    write_csv(directory / "order_fact.csv", result["order_fact"])
    write_csv(directory / "channel_summary.csv", result["channel_summary"])
    write_json(directory / "rejected_rows.json", result["rejected_rows"])
    write_json(directory / "findings.json", result["findings"])
    md, html_text = render_accounting(result)
    (directory / "report.md").write_text(md, encoding="utf-8", newline="\n")
    (directory / "report.html").write_text(html_text, encoding="utf-8", newline="\n")


def _write_experiment(directory: Path, result: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "aggregate.json", result["aggregate"])
    write_csv(directory / "segment_effects.csv", result["segments"])
    write_json(directory / "decision.json", result["decision"])
    write_json(directory / "findings.json", result["findings"])
    md, html_text = render_experiment(result)
    (directory / "report.md").write_text(md, encoding="utf-8", newline="\n")
    (directory / "report.html").write_text(html_text, encoding="utf-8", newline="\n")


def _write_quality(directory: Path, result: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_csv(directory / "weekly_metrics.csv", result["weekly_metrics"])
    write_csv(directory / "workflow_details.csv", result["workflow_details"])
    write_csv(directory / "root_causes.csv", result["root_causes"])
    write_json(directory / "decision.json", result["decision"])
    write_json(directory / "findings.json", result["findings"])
    md, html_text = render_quality(result)
    (directory / "report.md").write_text(md, encoding="utf-8", newline="\n")
    (directory / "report.html").write_text(html_text, encoding="utf-8", newline="\n")


def _executive_summary(
    run_id: str,
    generated_at: str,
    results: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "generated_at": generated_at,
        "synthetic": True,
        "supply_chain": {
            "selected_k": results["supply_chain"]["selected_k"],
            "selected_silhouette": results["supply_chain"]["selected_silhouette"],
        },
        "accounting": results["accounting"]["summary"],
        "experiment": results["experiment"]["decision"],
        "quality": results["quality"]["decision"],
        "finding_counts": {
            severity: sum(1 for item in findings if item["severity"] == severity)
            for severity in ("critical", "high", "medium", "warning", "info")
        },
    }


def build_demo(root: Path, fixed_time: str, overwrite: bool = False) -> dict[str, Any]:
    data_dir = root / "data"
    output_dir = root / "output"
    if root.exists() and overwrite:
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    counts = generate_synthetic_company(data_dir)
    result = run_casebook(data_dir, output_dir, fixed_time=fixed_time, overwrite=overwrite)
    return {"generated_rows": counts, **result}


def compare_runs(baseline_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    baseline = read_json(baseline_dir / "executive" / "summary.json")
    candidate = read_json(candidate_dir / "executive" / "summary.json")
    return {
        "schema_version": "1.0",
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "accounting_net_revenue_delta": float(candidate["accounting"]["net_revenue"]) - float(baseline["accounting"]["net_revenue"]),
        "experiment_stratified_effect_delta": float(candidate["experiment"]["stratified_effect"]) - float(baseline["experiment"]["stratified_effect"]),
        "quality_corrected_failure_change_delta": float(candidate["quality"]["corrected_week_over_week_change"]) - float(baseline["quality"]["corrected_week_over_week_change"]),
        "supply_chain_silhouette_delta": float(candidate["supply_chain"]["selected_silhouette"]) - float(baseline["supply_chain"]["selected_silhouette"]),
        "note": "Deltas compare synthetic analytical outputs; they are not business forecasts.",
    }
