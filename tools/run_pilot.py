"""Executa o piloto sintético de calibração e empacota o E3."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def run_case(output: Path, task: str, seed: int) -> dict:
    case = output / f"{task.lower()}-seed-{seed}"
    logs = case / "logs"
    logs.mkdir(parents=True)
    env = dict(__import__("os").environ)
    env["UXAGENT_LOG_DIR"] = str(logs)
    command = [
        sys.executable, str(BASE / "uxagent_cli.py"), "--mock",
        "--task", task, "--seed", str(seed), "--max-steps", "30",
    ]
    result = subprocess.run(command, cwd=BASE, env=env, text=True, capture_output=True, check=False)
    log_files = sorted(logs.glob("*.jsonl"))
    if len(log_files) != 1:
        raise RuntimeError(f"{task} seed {seed}: esperado um log, encontrados {len(log_files)}")
    records = load_records(log_files[0])
    (case / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (case / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    target = case / "events.jsonl"
    shutil.copyfile(log_files[0], target)
    return {
        "case": case.name,
        "task": task,
        "seed": seed,
        "return_code": result.returncode,
        "events": len(records),
        "log": str(target.relative_to(output)),
        "outcome": records[-1].get("outcome"),
        "actions_executed": sum(record["event"] == "action_executed" for record in records),
        "supports_used": sum(record["event"] == "support_opened" for record in records),
        "errors": sum(bool(record.get("error")) for record in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(BASE / "pilot_e3"))
    parser.add_argument("--seeds", default="42,43,44")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copyfile(BASE / "docs" / "e3_field_dictionary.md", output / "field_dictionary.md")
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    cases = [run_case(output, task, seed) for task in ("T1", "T2") for seed in seeds]
    manifest = {
        "package_version": "e3-pilot-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "synthetic": True,
        "tasks": ["T1", "T2"],
        "seeds": seeds,
        "cases": cases,
        "note": "Mock policy pilot. No LLM prompt is sent in this run; real Gemini traces are captured separately via UXAGENT_TRACE_DIR.",
    }
    (output / "pilot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
