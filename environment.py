"""Ambientes fictícios das tarefas de calibração T1 e T2 (sem interface gráfica)."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

ROLES = ("LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE")
T1_OBJECTIVE = "Atribuir as três funções complementares a três integrantes disponíveis."
T2_OBJECTIVE = (
    "Revisar o plano após uma atualização do feed, atualizar o estado observado, "
    "comunicar a próxima etapa se a ação de ping estiver disponível, atribuir todas as funções, "
    "revisar e confirmar o plano."
)


@dataclass
class T1Environment:
    session_id: str
    members: dict[str, dict[str, Any]] = field(default_factory=lambda: {
        "member_A": {"available": True, "capabilities": ["LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT"]},
        "member_B": {"available": True, "capabilities": ["TRANSPORT_RESOURCE"]},
        "member_C": {"available": True, "capabilities": ["ACTIVATE_CHECKPOINT"]},
    })
    assignments: dict[str, str] = field(default_factory=dict)
    step_order: list[str] = field(default_factory=lambda: [
        "LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE"
    ])
    reviewed: bool = False
    plan_confirmed: bool = False
    checklist_open: bool = False
    help_topic: str | None = None
    feed_refreshes: int = 0
    pings: list[str] = field(default_factory=list)
    action_count: int = 0  # Ações realmente aceitas/executadas.
    proposal_count: int = 0  # Ações propostas e processadas, incluindo rejeições.
    last_feedback: str = "Missão iniciada. Leia os requisitos e atribua as funções."

    @property
    def task_id(self) -> str:
        return "T1"

    @property
    def task_objective(self) -> str:
        return T1_OBJECTIVE

    def snapshot(self) -> dict[str, Any]:
        return deepcopy({
            "task_id": self.task_id,
            "objective": self.task_objective,
            "members": self.members,
            "assignments": self.assignments,
            "required_roles": list(ROLES),
            "step_order": self.step_order,
            "reviewed": self.reviewed,
            "plan_confirmed": self.plan_confirmed,
            "checklist_open": self.checklist_open,
            "help_topic": self.help_topic,
            "feed_refreshes": self.feed_refreshes,
            "pings": self.pings,
            "actions_executed": self.action_count,
            "actions_proposed": self.proposal_count,
            "feedback": self.last_feedback,
            "rules": [
                "Cada uma das três funções deve ser atribuída exatamente uma vez.",
                "Cada integrante atribuído deve estar disponível.",
                "A função atribuída deve constar nas capacidades do integrante.",
                "A ordem de etapas deve conter as três funções sem duplicação.",
                "TRANSPORT_RESOURCE deve ocorrer depois de LOCATE_RESOURCE e ACTIVATE_CHECKPOINT.",
                "É preciso revisar o plano antes de confirmá-lo.",
            ],
        })

    def observation_snapshot(self) -> dict[str, Any]:
        return self.snapshot()

    def is_assignment_complete(self) -> bool:
        return (
            len(self.assignments) == len(self.members)
            and set(self.assignments.keys()) == set(self.members.keys())
            and set(self.assignments.values()) == set(ROLES)
        )

    def validate_plan(self) -> tuple[bool, str]:
        if not self.is_assignment_complete():
            return False, "Atribua todas as três funções a integrantes distintos, sem deixar nenhuma de fora."
        for member, role in self.assignments.items():
            record = self.members.get(member)
            if not record or not record["available"]:
                return False, f"{member} está indisponível; escolha outro integrante."
            if role not in record["capabilities"]:
                return False, f"{member} não possui a capacidade exigida para {role}; reveja a atribuição."
        if set(self.step_order) != set(ROLES) or len(self.step_order) != len(ROLES):
            return False, "A ordem deve conter cada etapa exatamente uma vez."
        transport = self.step_order.index("TRANSPORT_RESOURCE")
        if transport < self.step_order.index("LOCATE_RESOURCE") or transport < self.step_order.index("ACTIVATE_CHECKPOINT"):
            return False, "TRANSPORT_RESOURCE só pode ocorrer depois de LOCATE_RESOURCE e ACTIVATE_CHECKPOINT."
        return True, "Plano válido: funções cobertas, integrantes disponíveis e dependências respeitadas."

    def externally_evaluate(self) -> tuple[bool, str]:
        """Oráculo externo. Não consulta uma declaração de sucesso feita pelo LLM."""
        valid, reason = self.validate_plan()
        if not self.plan_confirmed:
            return False, "O plano não foi confirmado."
        if not self.reviewed:
            return False, "O plano não foi revisado antes da confirmação."
        if not valid:
            return False, reason
        return True, "T1 concluída: plano revisado e confirmado com atribuições válidas."


@dataclass
class T2Environment(T1Environment):
    """Tarefa de calibração para atualizar o feed, comunicar e revisar o plano."""
    feed_revision: int = 0
    completed_steps: list[str] = field(default_factory=list)
    feed_message: str = "Nenhuma atualização de progresso recebida."
    observed_feed_revision: int = 0
    observed_completed_steps: list[str] = field(default_factory=list)
    observed_feed_message: str = "Nenhuma atualização de progresso recebida."
    update_applied: bool = False
    communication_available: bool | None = None

    def __post_init__(self) -> None:
        # T2 começa com uma atribuição parcial, conforme a especificação da tarefa.
        if not self.assignments:
            self.assignments["member_A"] = "LOCATE_RESOURCE"

    @property
    def task_id(self) -> str:
        return "T2"

    @property
    def task_objective(self) -> str:
        return T2_OBJECTIVE

    def trigger_feed_update(self) -> None:
        if self.update_applied:
            return
        self.feed_revision += 1
        self.completed_steps = ["LOCATE_RESOURCE"]
        self.feed_message = (
            "Atualização da equipe: LOCATE_RESOURCE foi concluída. "
            "A próxima etapa que precisa ser ativada é ACTIVATE_CHECKPOINT; depois será possível transportar o recurso."
        )
        self.update_applied = True
        self.last_feedback = "Uma atualização de progresso chegou ao feed. Confira/atualize o feed antes de confirmar o plano."

    def sync_observation(self) -> None:
        self.observed_feed_revision = self.feed_revision
        self.observed_completed_steps = list(self.completed_steps)
        self.observed_feed_message = self.feed_message
        self.last_feedback = "Feed atualizado; a observação agora reflete o último estado recebido."

    def snapshot(self) -> dict[str, Any]:
        state = super().snapshot()
        state.update({
            "task_id": "T2",
            "objective": self.task_objective,
            "feed_revision": self.feed_revision,
            "completed_steps": list(self.completed_steps),
            "feed_message": self.feed_message,
            "observed_feed_revision": self.observed_feed_revision,
            "observed_completed_steps": list(self.observed_completed_steps),
            "observed_feed_message": self.observed_feed_message,
            "update_applied": self.update_applied,
            "communication_available": self.communication_available,
            "required_communication": "NEXT_STEP_ACTIVATE_CHECKPOINT",
            "rules": state["rules"] + [
                "Após a atualização, a observação precisa refletir o estado mais recente do feed.",
                "Depois da atualização, comunicar NEXT_STEP_ACTIVATE_CHECKPOINT quando a ação send_ping estiver disponível.",
                "O plano deve ser revisto depois da atualização e antes de confirmar.",
            ],
        })
        return state

    def observation_snapshot(self) -> dict[str, Any]:
        # Não revela o estado verdadeiro do feed ao modelo: apenas a cópia observada/cacheada.
        state = super().snapshot()
        state.update({
            "task_id": "T2",
            "objective": self.task_objective,
            "feed_revision": self.observed_feed_revision,
            "completed_steps": list(self.observed_completed_steps),
            "feed_message": self.observed_feed_message,
            "required_communication": "NEXT_STEP_ACTIVATE_CHECKPOINT",
            "rules": state["rules"] + [
                "Após a atualização, confira o estado do feed antes de confirmar.",
                "Se send_ping estiver disponível após a atualização, envie NEXT_STEP_ACTIVATE_CHECKPOINT.",
                "O plano deve ser revisto depois da atualização e antes de confirmar.",
            ],
        })
        # Campos internos/verdadeiros removidos para evitar vazamento de estado ao modelo.
        state.pop("observed_feed_revision", None)
        state.pop("observed_completed_steps", None)
        state.pop("observed_feed_message", None)
        state.pop("update_applied", None)
        state.pop("communication_available", None)
        return state

    def externally_evaluate(self) -> tuple[bool, str]:
        valid, reason = self.validate_plan()
        if not self.plan_confirmed:
            return False, "O plano não foi confirmado."
        if not self.reviewed:
            return False, "O plano não foi revisado antes da confirmação."
        if not valid:
            return False, reason
        if not self.update_applied:
            return False, "A atualização predefinida do feed não ocorreu."
        if self.observed_feed_revision != self.feed_revision:
            return False, "O plano foi confirmado sem atualizar a observação ao estado mais recente do feed."
        if "NEXT_STEP_ACTIVATE_CHECKPOINT" not in self.pings:
            return False, "A mudança do feed não foi comunicada com NEXT_STEP_ACTIVATE_CHECKPOINT."
        return True, "T2 concluída: feed atualizado, comunicação registrada e plano válido revisado e confirmado."
