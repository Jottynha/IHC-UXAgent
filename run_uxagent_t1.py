#!/usr/bin/env python3
"""Executa tarefas de calibração T1/T2 com Gemini ou política local (--mock)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controller import T1Controller
from environment import T1Environment, T2Environment
from event_logger import EventLogger
from gemini_client import DEFAULT_MODEL, GeminiActionPolicy, GeminiClientError, load_action_schema
from jsonschema import Draft202012Validator
from mechanisms import MechanismConfig

BASE = Path(__file__).resolve().parent
ACTION_SCHEMA = load_action_schema()
ACTION_VALIDATOR = Draft202012Validator(ACTION_SCHEMA)
ACTION_TEMPLATES = [
    {"name": "select_role", "arguments": {"member": "um integrante visível", "role": "uma função do conjunto permitido"}},
    {"name": "set_step_order", "arguments": {"steps": ["LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE"]}},
    {"name": "open_checklist", "arguments": {}},
    {"name": "open_help", "arguments": {"topic": "mission_requirements | role_constraints | task_dependencies"}},
    {"name": "refresh_feed", "arguments": {}},
    {"name": "send_ping", "arguments": {"code": "PLAN_UPDATED | NEXT_STEP_ACTIVATE_CHECKPOINT"}},
    {"name": "review_plan", "arguments": {}},
    {"name": "confirm_plan", "arguments": {}},
]


class MockPolicy:
    """Política adaptativa e determinística para testar os fluxos sem chamar API."""
    def propose_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        state = observation["state"]
        task_id = observation["task_id"]
        available_names = {item.get("name") for item in observation["available_actions"]}

        if task_id == "T2" and state.get("actions_proposed", 0) >= 1:
            if state.get("feed_revision", 0) == 0:
                return {"name": "refresh_feed", "arguments": {}}
            if "send_ping" in available_names and "NEXT_STEP_ACTIVATE_CHECKPOINT" not in state.get("pings", []):
                return {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}}

        assignments = state.get("assignments", {})
        members = state.get("members", {})
        roles = state.get("required_roles", [])

        # Corrige qualquer atribuição cujo papel não esteja nas capacidades do integrante.
        for member, current_role in assignments.items():
            if current_role not in members.get(member, {}).get("capabilities", []):
                for replacement_role in members[member].get("capabilities", []):
                    occupied_by_other = any(m != member and r == replacement_role for m, r in assignments.items())
                    if not occupied_by_other:
                        return {"name": "select_role", "arguments": {"member": member, "role": replacement_role}}

        # Preenche funções ausentes, preferindo integrantes ainda sem atribuição.
        assigned_roles = set(assignments.values())
        for role in roles:
            if role in assigned_roles:
                continue
            candidates = [
                member for member, record in members.items()
                if record.get("available") and role in record.get("capabilities", [])
                and assignments.get(member) != role
            ]
            candidates.sort(key=lambda member: member in assignments)
            for member in candidates:
                previous_role = assignments.get(member)
                if previous_role is None or previous_role not in (set(roles) - assigned_roles):
                    return {"name": "select_role", "arguments": {"member": member, "role": role}}
            if candidates:
                return {"name": "select_role", "arguments": {"member": candidates[0], "role": role}}

        if task_id == "T2" and "send_ping" in available_names and "NEXT_STEP_ACTIVATE_CHECKPOINT" not in state.get("pings", []):
            return {"name": "send_ping", "arguments": {"code": "NEXT_STEP_ACTIVATE_CHECKPOINT"}}
        if not state.get("reviewed"):
            return {"name": "review_plan", "arguments": {}}
        return {"name": "confirm_plan", "arguments": {}}


def _parse_enabled(values: str | None) -> list[str]:
    if not values:
        return []
    return [name.strip().upper() for name in values.split(",") if name.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="UXAgent protótipo de calibração T1/T2")
    parser.add_argument("--mock", action="store_true", help="Executa sem API/custo para testar o ciclo")
    parser.add_argument("--task", choices=("T1", "T2"), default="T1", help="Tarefa de calibração (T1 ou T2)")
    parser.add_argument("--max-steps", type=int, default=20, help="Limite de ações propostas (padrão: 20)")
    parser.add_argument("--config", default=str(BASE / "uxagent_mechanisms.json"), help="Arquivo JSON com parâmetros R1–R4")
    parser.add_argument("--enable", help="Ativar mecanismos específicos, separados por vírgula: R1,R2,R3,R4")
    parser.add_argument("--seed", type=int, help="Sobrescrever a semente RNG para reproduzir as injeções")
    args = parser.parse_args()
    if args.max_steps < 1:
        parser.error("--max-steps precisa ser maior que zero")

    try:
        config = MechanismConfig.from_file(args.config)
        config.enable(_parse_enabled(args.enable))
        if args.seed is not None:
            config.seed = args.seed
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(f"Configuração inválida: {exc}")

    model = "mock-policy" if args.mock else os.environ.get("UXAGENT_MODEL", DEFAULT_MODEL)
    session_id = args.task.lower() + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    log_root = Path(os.environ.get("UXAGENT_LOG_DIR", str(BASE / "logs"))).expanduser()
    log_path = log_root / f"{session_id}.jsonl"
    logger = EventLogger(
        log_path, BASE / "uxagent_event.schema.json", model,
        task_id=args.task, condition="calibration", config_version=config.log_version,
    )

    try:
        policy = MockPolicy() if args.mock else GeminiActionPolicy(model=model)
    except GeminiClientError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2

    env = T1Environment(session_id=session_id) if args.task == "T1" else T2Environment(session_id=session_id)
    controller = T1Controller(env, config)
    enabled = [name for name, state in config.enabled.items() if state]
    print(f"UXAgent — {args.task}: {env.task_objective}")
    print(f"Modo: {'mock (sem API/custo)' if args.mock else 'Gemini API'}")
    print(f"Modelo: {model}")
    print(f"Sessão: {session_id}")
    print(f"Mecanismos ativos: {', '.join(enabled) if enabled else 'nenhum (linha de base)'}")
    if args.task == "T1" and (config.enabled.get("R2") or config.enabled.get("R3")):
        print("AVISO: R2/R3 só têm oportunidade definida em T2; nesta T1 não alteram o comportamento.")
    print("Parâmetros:", json.dumps(config.to_dict(), ensure_ascii=False))
    print()

    logger.log(
        event="task_start", actor="controller", session_id=session_id, step=0,
        state_pre=None, state_post=env.snapshot(),
        note="Tarefa sintética de calibração iniciada. Configuração versionada: " + json.dumps(config.to_dict(), sort_keys=True),
    )

    def trigger_t2_update_after_first_proposal(step_number: int, obs_id: str) -> None:
        """Evento externo predefinido ocorre após a primeira tentativa, mesmo se o schema falhar."""
        if isinstance(env, T2Environment) and step_number == 1 and not env.update_applied:
            update_pre = env.snapshot()
            env.trigger_feed_update()
            update_post = env.snapshot()
            logger.log(event="state_changed", actor="controller", session_id=session_id, step=step_number,
                       state_pre=update_pre, state_post=update_post, observation_id=obs_id,
                       note="Atualização externa predefinida do feed após a primeira tentativa; a política só a verá na próxima observação.",
                       opportunity_id="T2-FEED-UPDATE")
            print("Evento externo: o feed da equipe foi atualizado.")

    for step in range(1, args.max_steps + 1):
        observation_id = f"obs-{step:03d}"
        before = env.snapshot()
        base_observation = {
            "task_id": args.task,
            "task": f"{args.task} — {env.task_objective}",
            "state": before,
            "available_actions": ACTION_TEMPLATES,
        }
        observation, mechanism_metadata = controller.build_observation(base_observation)
        visible_state = observation["state"]
        logger.log(
            event="observation_emitted", actor="controller", session_id=session_id, step=step,
            state_pre=before, state_post=visible_state, observation_id=observation_id,
            note="Estado visível entregue à política; metadados para auditoria: " + json.dumps(mechanism_metadata, ensure_ascii=False, sort_keys=True),
            opportunity_id=("R2-communication-opportunity" if args.task == "T2" and env.update_applied else None),
        )

        try:
            action = policy.propose_action(observation)
            action_errors = list(ACTION_VALIDATOR.iter_errors(action))
            if action_errors:
                msg = "; ".join(e.message for e in action_errors[:3])
                logger.log(
                    event="action_rejected", actor="controller", session_id=session_id, step=step,
                    state_pre=before, state_post=env.snapshot(), observation_id=observation_id,
                    proposed_action=action, reject={"reason": f"Schema inválido: {msg}", "rule_id": "JSON-SCHEMA"},
                    error={"category": "invalid_action", "opp_id": f"{args.task}-json-schema", "rule_id": "JSON-SCHEMA"},
                    opportunity_id=f"{args.task}-json-schema",
                )
                env.proposal_count += 1
                print(f"Passo {step}: ação rejeitada pelo schema local: {msg}")
                env.last_feedback = f"Ação rejeitada pelo schema local: {msg}"
                trigger_t2_update_after_first_proposal(step, observation_id)
                continue

            logger.log(
                event="action_proposed", actor="controller" if args.mock else "llm", session_id=session_id, step=step,
                state_pre=before, state_post=before, observation_id=observation_id,
                proposed_action=action, note="Ação proposta pela política; o controlador permanece responsável por validá-la.",
            )
            result = controller.apply(action)
            after = env.snapshot()
            opportunity = (result.error or {}).get("opp_id") or (result.mechanism_effect or {}).get("opp_id")
            if result.accepted:
                logger.log(
                    event="action_executed", actor="controller", session_id=session_id, step=step,
                    state_pre=before, state_post=after, observation_id=observation_id,
                    proposed_action=action, executed_action=result.executed_action,
                    support=result.support, error=result.error,
                    note=result.reason + (" | mecanismo=" + json.dumps(result.mechanism_effect, ensure_ascii=False) if result.mechanism_effect else ""),
                    opportunity_id=opportunity,
                )
                if result.support:
                    logger.log(event="support_opened", actor="controller", session_id=session_id, step=step,
                               state_pre=before, state_post=after, observation_id=observation_id,
                               proposed_action=action, executed_action=result.executed_action,
                               support=result.support, note=result.reason, opportunity_id=opportunity)
                if result.changed:
                    logger.log(event="state_changed", actor="controller", session_id=session_id, step=step,
                               state_pre=before, state_post=after, observation_id=observation_id,
                               proposed_action=action, executed_action=result.executed_action,
                               note=result.reason, opportunity_id=opportunity)
                if result.error:
                    logger.log(event="error_recorded", actor="controller", session_id=session_id, step=step,
                               state_pre=before, state_post=after, observation_id=observation_id,
                               proposed_action=action, executed_action=result.executed_action,
                               error=result.error, note=result.reason, opportunity_id=opportunity)
                print(f"Passo {step}: {action['name']}" + (f" → {result.executed_action['arguments']}" if result.executed_action else "") + f" — {result.reason}")
            else:
                logger.log(event="action_rejected", actor="controller", session_id=session_id, step=step,
                           state_pre=before, state_post=after, observation_id=observation_id,
                           proposed_action=action, reject=result.reject, error=result.error, note=result.reason,
                           opportunity_id=opportunity)
                logger.log(event="error_recorded", actor="controller", session_id=session_id, step=step,
                           state_pre=before, state_post=after, observation_id=observation_id,
                           proposed_action=action, reject=result.reject, error=result.error, note=result.reason,
                           opportunity_id=opportunity)
                print(f"Passo {step}: {action['name']} REJEITADA — {result.reason}")

            # Evento externo predefinido da T2: a política só verá a versão observada na próxima chamada.
            trigger_t2_update_after_first_proposal(step, observation_id)

            if result.completed:
                success, reason = env.externally_evaluate()
                outcome = {"status": "success" if success else "failure", "success": success, "reason": reason}
                logger.log(event="task_evaluated", actor="evaluator", session_id=session_id, step=step,
                           state_pre=before, state_post=env.snapshot(), outcome=outcome,
                           note="Resultado calculado pelo estado real, não por declaração do LLM.")
                logger.log(event="task_end", actor="controller", session_id=session_id, step=step,
                           state_pre=before, state_post=env.snapshot(), outcome=outcome, note=reason)
                print("\nRESULTADO:", "SUCESSO" if success else "FALHA")
                print(reason)
                print(f"Propostas processadas: {env.proposal_count}; ações aceitas/executadas: {env.action_count}")
                print(f"Log JSONL: {log_path}")
                return 0 if success else 1
        except GeminiClientError as exc:
            logger.log(event="technical_failure", actor="controller", session_id=session_id, step=step,
                       state_pre=before, state_post=env.snapshot(), observation_id=observation_id,
                       technical_failure=True, technical_failure_reason=type(exc).__name__,
                       outcome={"status": "unknown", "success": None, "reason": "A API não completou a proposta de ação."},
                       note=str(exc))
            print(f"\nFALHA TÉCNICA: {exc}", file=sys.stderr)
            print(f"Log JSONL: {log_path}", file=sys.stderr)
            return 1
        except Exception as exc:
            logger.log(event="technical_failure", actor="controller", session_id=session_id, step=step,
                       state_pre=before, state_post=env.snapshot(), observation_id=observation_id,
                       technical_failure=True, technical_failure_reason=type(exc).__name__,
                       outcome={"status": "unknown", "success": None, "reason": "Falha técnica durante o protótipo."},
                       note=f"Falha técnica: {type(exc).__name__}: {exc}")
            print(f"\nFALHA TÉCNICA: {type(exc).__name__}: {exc}", file=sys.stderr)
            print(f"Log JSONL: {log_path}", file=sys.stderr)
            return 1

    final_state = env.snapshot()
    outcome = {"status": "interrupted", "success": False, "reason": "Limite de propostas atingido sem confirmação válida."}
    logger.log(event="task_interrupted", actor="controller", session_id=session_id, step=args.max_steps,
               state_pre=final_state, state_post=final_state, outcome=outcome, note="Limite de propostas atingido.")
    print("\nRESULTADO: INCOMPLETO — limite de passos atingido.")
    print(f"Log JSONL: {log_path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
