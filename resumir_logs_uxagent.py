#!/usr/bin/env python3
"""Gera um resumo seguro e compacto dos logs JSONL do protótipo UXAgent.

Execute colocando este arquivo na pasta do projeto, ao lado de run_uxagent_t1.py:
    python resumir_logs_uxagent.py
Opcionalmente:
    python resumir_logs_uxagent.py --all
    python resumir_logs_uxagent.py --logs logs --output resumo_logs_uxagent.txt
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_events(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_no, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    if isinstance(obj, dict):
                        events.append(obj)
                    else:
                        errors.append(f"linha {line_no}: JSON não é objeto")
                except json.JSONDecodeError as exc:
                    errors.append(f"linha {line_no}: JSON inválido ({exc.msg})")
    except OSError as exc:
        errors.append(f"não foi possível ler o arquivo ({exc})")
    return events, errors


def action_text(action: Any) -> str:
    if not isinstance(action, dict):
        return "(ação não registrada)"
    name = str(action.get("name", "ação desconhecida"))
    args = action.get("arguments")
    if isinstance(args, dict) and args:
        try:
            return f"{name} {json.dumps(args, ensure_ascii=False, sort_keys=True)}"
        except TypeError:
            return name
    return name


def compact(value: Any, limit: int = 180) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def read_json_after(note: Any, marker: str) -> dict[str, Any] | None:
    if not isinstance(note, str) or marker not in note:
        return None
    raw = note.split(marker, 1)[1].strip()
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def summarize(path: Path) -> str:
    events, parse_errors = load_events(path)
    if not events:
        return f"### {path.name}\n- Nenhum evento válido encontrado.\n"

    first = events[0]
    sid = first.get("sid", "desconhecida")
    task = first.get("tid", "?")
    condition = first.get("cond", "?")
    models = sorted({str(e.get("llm_model")) for e in events if e.get("llm_model")})
    model = ", ".join(models) if models else "sem modelo registrado (pode ser --mock ou o log não contém modelo)"
    counts = Counter(str(e.get("event", "evento_desconhecido")) for e in events)

    # A configuração completa é registrada na nota do evento inicial.
    config = None
    start_note = first.get("note")
    marker = "Configuração versionada: "
    if isinstance(start_note, str) and marker in start_note:
        try:
            config = json.loads(start_note.split(marker, 1)[1])
        except json.JSONDecodeError:
            config = None

    # Resultado do avaliador/controlador (não se confia no texto do LLM).
    final_events = [e for e in events if e.get("event") in {"task_evaluated", "task_end", "task_interrupted", "technical_failure"}]
    final = final_events[-1] if final_events else None
    outcome = final.get("outcome") if isinstance(final, dict) else None
    if isinstance(outcome, dict):
        status = outcome.get("status", "não informado")
        success = outcome.get("success")
        reason = outcome.get("reason")
        result_line = f"- **Resultado externo:** {status}; success={success}; motivo: {compact(reason or final.get('note')) or 'não registrado'}"
    elif final and final.get("event") == "technical_failure":
        result_line = f"- **Resultado externo:** falha técnica; tipo={final.get('tech_fail_reason') or 'não registrado'}"
    else:
        result_line = "- **Resultado externo:** não há evento final de avaliação; a sessão pode ter sido interrompida ou o log estar incompleto."

    proposals = [e for e in events if e.get("event") == "action_proposed"]
    executions = [e for e in events if e.get("event") == "action_executed"]
    rejections = [e for e in events if e.get("event") == "action_rejected"]
    errors = [e for e in events if e.get("event") == "error_recorded"]
    technical = [e for e in events if e.get("tech_fail") is True or e.get("event") == "technical_failure"]

    lines = [f"### {path.name}", f"- **Sessão:** {sid}", f"- **Tarefa/condição:** {task} / {condition}", f"- **Modelo:** {model}", f"- **Eventos válidos:** {len(events)}"]
    if config:
        lines.append(f"- **Configuração:** versão={config.get('config_version', '?')}; seed={config.get('seed', '?')}")
        mechanisms = config.get("mechanisms", {})
        if isinstance(mechanisms, dict):
            bits = []
            for key in ("R1", "R2", "R3", "R4"):
                item = mechanisms.get(key, {})
                if isinstance(item, dict):
                    bits.append(f"{key}={'ON' if item.get('enabled') else 'OFF'} ({item.get('parameter', '?')}={item.get('probability', '?')})")
            lines.append("- **Mecanismos configurados:** " + "; ".join(bits))

    lines.append(result_line)
    lines.append("- **Contagem de eventos:** " + (", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "nenhum"))
    lines.append(f"- **Propostas processadas:** {len(proposals)}; **ações executadas:** {len(executions)}; **rejeições:** {len(rejections)}; **eventos de erro:** {len(errors)}; **falhas técnicas:** {len(technical)}")

    if executions:
        trace = [action_text(e.get("act_exec")) for e in executions]
        lines.append("- **Sequência executada:** " + " → ".join(trace[:30]) + (" → …" if len(trace) > 30 else ""))
    if rejections:
        details = []
        for e in rejections[:10]:
            act = action_text(e.get("act_prop"))
            rej = e.get("reject") if isinstance(e.get("reject"), dict) else {}
            rule = rej.get("rule_id") or (e.get("error") or {}).get("rule_id") if isinstance(e.get("error"), dict) else rej.get("rule_id")
            reason = compact(rej.get("reason"), 120)
            details.append(f"passo {e.get('step')}: {act} (regra={rule or '?'}, motivo={reason or 'não informado'})")
        lines.append("- **Rejeições (até 10):** " + " | ".join(details))
    if errors:
        details = []
        seen = set()
        for e in errors:
            err = e.get("error") if isinstance(e.get("error"), dict) else {}
            tup = (err.get("category"), err.get("rule_id"), err.get("opp_id"))
            if tup not in seen:
                seen.add(tup)
                details.append(f"{tup[0] or '?'} / {tup[1] or '?'} / {tup[2] or '?'}")
        lines.append("- **Tipos de erro registrados:** " + ("; ".join(details[:12]) if details else "nenhum detalhado"))

    # Resumo das oportunidades/efeitos R1--R4 a partir de metadados e erros.
    observations = [e for e in events if e.get("event") == "observation_emitted"]
    exposed = Counter()
    stale = 0
    actual_pairs = []
    for e in observations:
        meta = read_json_after(e.get("note"), "metadados para auditoria: ")
        if not meta:
            continue
        for name, key in (("R2", "communication_exposed"), ("R4", "help_exposed")):
            if meta.get(key) is True:
                exposed[f"{name}=disponível"] += 1
            elif meta.get(key) is False:
                exposed[f"{name}=oculto"] += 1
        visible = meta.get("visible_feed_revision")
        actual = meta.get("actual_feed_revision")
        if visible is not None and actual is not None:
            actual_pairs.append((visible, actual))
            if visible != actual:
                stale += 1
    if exposed:
        lines.append("- **Exposição observada:** " + "; ".join(f"{k}: {v} observações" for k, v in sorted(exposed.items())))
    if actual_pairs:
        lines.append(f"- **Feed:** observações desatualizadas={stale}/{len(actual_pairs)}; revisão final visível/real={actual_pairs[-1][0]}/{actual_pairs[-1][1]}")
    r1_errors = [e for e in errors if isinstance(e.get("error"), dict) and e["error"].get("rule_id") == "R1-P-VALIDA"]
    if r1_errors:
        lines.append(f"- **R1:** deslizes registrados={len(r1_errors)}")
    if parse_errors:
        lines.append(f"- **Problemas de leitura do arquivo:** {len(parse_errors)} ({'; '.join(parse_errors[:3])})")
    lines.append("- **Privacidade:** este resumo omite estado completo, prompts e notas brutas do log; não inclui chave de API.\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume logs JSONL do protótipo UXAgent sem imprimir o conteúdo completo.")
    parser.add_argument("--logs", default="logs", help="Pasta dos logs (padrão: logs)")
    parser.add_argument("--output", default="resumo_logs_uxagent.txt", help="Arquivo de saída")
    parser.add_argument("--all", action="store_true", help="Resume todos os logs; por padrão usa as 10 sessões mais recentes")
    args = parser.parse_args()
    log_dir = Path(args.logs).expanduser()
    files = sorted(log_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"Nenhum arquivo .jsonl encontrado em: {log_dir.resolve()}")
        print("Confirme que você está na pasta do protótipo e já executou uma tarefa.")
        return 1
    if not args.all:
        files = files[:10]
    reports = [f"Resumo dos logs UXAgent\nPasta: {log_dir.resolve()}\nSessões resumidas: {len(files)}\n" ]
    for path in reversed(files):
        reports.append(summarize(path))
    output = Path(args.output).expanduser()
    output.write_text("\n".join(reports).strip() + "\n", encoding="utf-8")
    print(output.read_text(encoding="utf-8"))
    print(f"\nResumo salvo em: {output.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
