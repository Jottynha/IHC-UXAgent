"""Fachada de aplicação do UXAgent para CLI e futuras interfaces."""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controller import ActionResult, T1Controller
from environment import T1Environment, T2Environment, T3Environment, T4Environment
from event_logger import EventLogger
from mechanisms import MechanismConfig
from uxagent_actions import (
    PROMPT_VERSION,
    UI_VERSION,
    action_templates,
    validate_action,
    validate_view_model,
)


@dataclass(frozen=True)
class SessionEvent:
    """Evento leve para uma camada de apresentação ou adaptador de log."""

    name: str
    step: int
    action: dict[str, Any] | None
    result: ActionResult | None
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        result = self.result.to_dict() if self.result else None
        return {
            "event": self.name,
            "step": self.step,
            "action": copy.deepcopy(self.action),
            "accepted": bool(result and result["accepted"]),
            "reason": result["reason"] if result else "",
            "timestamp": self.timestamp,
            "error": result["error"] if result else None,
            "executed_action": result["executed_action"] if result else None,
        }


class UXAgentSession:
    """Coordena uma sessão sem acoplar o domínio a uma tecnologia de interface.

    A sessão sempre constrói a visão a partir do canal de observação do controlador.
    Assim, uma futura interface web não acessa diretamente o estado verdadeiro do
    ambiente nem precisa duplicar as regras de disponibilidade das ações.
    """

    def __init__(
        self,
        task_id: str = "T1",
        *,
        config: MechanismConfig | None = None,
        session_id: str | None = None,
        log_path: Path | None = None,
    ) -> None:
        if task_id not in {"T1", "T2", "T3", "T4"}:
            raise ValueError("Tarefa desconhecida; use T1, T2, T3 ou T4.")
        self.session_id = session_id or f"{task_id.lower()}-{uuid.uuid4().hex[:12]}"
        self.config = config or MechanismConfig()
        environments = {
            "T1": T1Environment,
            "T2": T2Environment,
            "T3": T3Environment,
            "T4": T4Environment,
        }
        self._environment = environments[task_id](session_id=self.session_id)
        self.controller = T1Controller(self._environment, self.config)
        self.step = 0
        self.events: list[SessionEvent] = []
        self.logger = (
            EventLogger(
                log_path,
                Path(__file__).resolve().parent / "uxagent_event.schema.json",
                "web-human",
                task_id=task_id,
                condition="validation" if task_id in {"T3", "T4"} else "calibration",
                config_version=self.config.log_version,
            )
            if log_path
            else None
        )
        if self.logger:
            self.logger.log(
                event="task_start",
                actor="controller",
                session_id=self.session_id,
                step=0,
                state_post=self._environment.snapshot(),
                note="Sessão web sintética iniciada.",
            )

    @property
    def task_id(self) -> str:
        return self._environment.task_id

    @property
    def completed(self) -> bool:
        return self._environment.plan_confirmed

    def trigger_feed_update(self) -> None:
        """Aplica o evento externo predefinido de T2 sem expor o ambiente."""
        if not isinstance(self._environment, T2Environment):
            raise RuntimeError("Atualização de feed só existe nas tarefas T2, T3 e T4.")
        before = self._environment.snapshot()
        self._environment.trigger_feed_update()
        if self.logger:
            self.logger.log(
                event="state_changed",
                actor="controller",
                session_id=self.session_id,
                step=self.step,
                state_pre=before,
                state_post=self._environment.snapshot(),
                note="Atualização externa predefinida do feed.",
                opportunity_id="T2-FEED-UPDATE",
            )

    def observe(self) -> dict[str, Any]:
        """Retorna somente a observação que pode ser entregue à política/interface."""
        base = {
            "task_id": self.task_id,
            "task": f"{self.task_id} — {self._environment.task_objective}",
            "state": self._environment.snapshot(),
            "available_actions": action_templates(),
        }
        observation, metadata = self.controller.build_observation(base)
        return {
            "session_id": self.session_id,
            "step": self.step,
            "task_id": self.task_id,
            "objective": self._environment.task_objective,
            "state": observation["state"],
            "available_actions": observation["available_actions"],
            "metadata": metadata,
        }

    def view_model(self) -> dict[str, Any]:
        """Modelo serializável para renderização da interface."""
        observation = self.observe()
        state = observation["state"]
        assignments = state.get("assignments", {})
        members = state.get("members", {})
        assigned_roles = set(assignments.values())
        required_roles = state.get("required_roles", [])
        view_model = {
            "session_id": self.session_id,
            "ui_version": UI_VERSION,
            "task_id": self.task_id,
            "step": self.step,
            "status": "completed" if self.completed else "active",
            "objective": observation["objective"],
            "members": copy.deepcopy(members),
            "assignments": copy.deepcopy(assignments),
            "required_roles": required_roles,
            "missing_roles": [role for role in required_roles if role not in assigned_roles],
            "step_order": copy.deepcopy(state.get("step_order", [])),
            "reviewed": bool(state.get("reviewed")),
            "plan_confirmed": bool(state.get("plan_confirmed")),
            "checklist_open": bool(state.get("checklist_open")),
            "help_topic": state.get("help_topic"),
            "feed": {
                "revision": state.get("feed_revision", 0),
                "message": state.get("feed_message", ""),
                "completed_steps": copy.deepcopy(state.get("completed_steps", [])),
            },
            "feedback": state.get("feedback", ""),
            "available_actions": observation["available_actions"],
            "metadata": observation["metadata"],
            "history": [event.to_dict() for event in self.events],
        }
        validation_error = validate_view_model(view_model)
        if validation_error:
            raise RuntimeError(f"Modelo da interface inválido: {validation_error}")
        return view_model

    def dispatch(self, action: Any) -> ActionResult:
        """Valida e executa uma ação, registrando um evento em memória."""
        self.step += 1
        validation_error = validate_action(action)
        before = self._environment.snapshot()
        if self.logger and not validation_error:
            self.logger.log(
                event="action_proposed",
                actor="controller",
                session_id=self.session_id,
                step=self.step,
                state_pre=before,
                state_post=before,
                proposed_action=action if isinstance(action, dict) and not validation_error else None,
            )
        result = self.controller.apply(action)
        if validation_error and result.accepted:
            raise RuntimeError("O controlador aceitou uma ação que falhou na validação local.")
        self.events.append(SessionEvent(
            name="action_executed" if result.accepted else "action_rejected",
            step=self.step,
            action=copy.deepcopy(action) if isinstance(action, dict) else None,
            result=result,
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        ))
        if self.logger:
            after = self._environment.snapshot()
            if result.accepted:
                self.logger.log(
                    event="action_executed",
                    actor="controller",
                    session_id=self.session_id,
                    step=self.step,
                    state_pre=before,
                    state_post=after,
                    proposed_action=action if isinstance(action, dict) and not validation_error else None,
                    executed_action=result.executed_action,
                    support=result.support,
                    error=result.error,
                    note=result.reason,
                )
                if result.support:
                    self.logger.log(
                        event="support_opened",
                        actor="controller",
                        session_id=self.session_id,
                        step=self.step,
                        state_pre=before,
                        state_post=after,
                        proposed_action=action if isinstance(action, dict) and not validation_error else None,
                        executed_action=result.executed_action,
                        support=result.support,
                        note=result.reason,
                    )
                if result.changed:
                    self.logger.log(
                        event="state_changed",
                        actor="controller",
                        session_id=self.session_id,
                        step=self.step,
                        state_pre=before,
                        state_post=after,
                        proposed_action=action if isinstance(action, dict) and not validation_error else None,
                        executed_action=result.executed_action,
                        note=result.reason,
                    )
            else:
                self.logger.log(
                    event="action_rejected",
                    actor="controller",
                    session_id=self.session_id,
                    step=self.step,
                    state_pre=before,
                    state_post=after,
                    proposed_action=action if isinstance(action, dict) and not validation_error else None,
                    reject=result.reject,
                    error=result.error,
                    note=result.reason,
                )
        return result

    def evaluate(self) -> dict[str, Any]:
        """Avalia o estado verdadeiro, sem depender de texto da política."""
        success, reason = self._environment.externally_evaluate()
        outcome = {
            "status": "success" if success else "failure",
            "success": success,
            "reason": reason,
        }
        if self.logger:
            self.logger.log(
                event="task_evaluated",
                actor="evaluator",
                session_id=self.session_id,
                step=self.step,
                state_pre=self._environment.snapshot(),
                state_post=self._environment.snapshot(),
                outcome=outcome,
            )
            self.logger.log(
                event="task_end",
                actor="controller",
                session_id=self.session_id,
                step=self.step,
                state_pre=self._environment.snapshot(),
                state_post=self._environment.snapshot(),
                outcome=outcome,
            )
        return {
            **outcome,
            "ui_version": UI_VERSION,
            "prompt_version": PROMPT_VERSION,
        }

    def history(self) -> list[dict[str, Any]]:
        """Retorna eventos de interação em formato seguro para a interface."""
        return [event.to_dict() for event in self.events]
