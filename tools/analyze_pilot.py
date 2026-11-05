"""Calcula métricas do pacote E3 e comparação com a referência KLM."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
KLM_ACTIONS = {"T1": 5, "T2": 6}


def records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def summarize(case: Path) -> dict:
    data = records(case / "events.jsonl")
    evaluated = next((item for item in reversed(data) if item["event"] == "task_evaluated"), {})
    outcome = evaluated.get("outcome") or {}
    errors = [item for item in data if item.get("error")]
    executed = [item for item in data if item["event"] == "action_executed"]
    supports = [item for item in data if item["event"] == "support_opened"]
    successful_recovery = bool(outcome.get("success")) and bool(errors)
    return {
        "case": case.name,
        "task": data[0]["tid"],
        "success": outcome.get("success"),
        "S": int(bool(outcome.get("success"))),
        "R": int(successful_recovery) if errors else None,
        "E": len(errors),
        "A": len(executed),
        "help_used": len(supports),
        "klm_actions": KLM_ACTIONS[data[0]["tid"]],
        "delta_actions_vs_klm": len(executed) - KLM_ACTIONS[data[0]["tid"]],
        "technical_failures": sum(item["tech_fail"] for item in data),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(BASE / "pilot_e3"))
    args = parser.parse_args()
    root = Path(args.input)
    summaries = [summarize(path) for path in sorted(root.glob("t*-seed-*"))]
    grouped = {}
    for item in summaries:
        grouped.setdefault(item["task"], []).append(item)
    aggregate = {}
    for task, items in grouped.items():
        aggregate[task] = {
            "n": len(items),
            "S_rate": sum(item["S"] for item in items) / len(items),
            "R_rate": None if not any(item["R"] is not None for item in items) else sum(item["R"] or 0 for item in items) / sum(item["R"] is not None for item in items),
            "mean_E": sum(item["E"] for item in items) / len(items),
            "mean_A": sum(item["A"] for item in items) / len(items),
            "mean_help": sum(item["help_used"] for item in items) / len(items),
            "mean_delta_actions_vs_klm": sum(item["delta_actions_vs_klm"] for item in items) / len(items),
        }
    result = {
        "metric_definitions": {
            "S": "sucesso externo por sessão (0/1)",
            "R": "recuperação: sessão bem-sucedida após erro funcional; nulo quando não houve oportunidade",
            "E": "número de eventos com erro funcional",
            "A": "ações executadas",
            "help_used": "eventos support_opened",
        },
        "klm_reference_actions": KLM_ACTIONS,
        "sessions": summaries,
        "aggregate": aggregate,
        "caveat": "Piloto sintético com política mock; não é evidência humana nem estima tempo KLM.",
    }
    (root / "metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "metrics.md").write_text(
        "# Métricas do piloto E3\n\n"
        + "Definições: S = sucesso externo; R = recuperação após erro; "
        "E = erros funcionais; A = ações executadas; ajuda = `support_opened`.\n\n"
        + "```json\n" + json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n```\n\n"
        + "A referência KLM é uma contagem de ações de especialista, não tempo "
        "humano. O piloto é sintético e não substitui participantes.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
