"""Controlador UXAgent com mecanismos parametrizados R1--R4 fora do prompt."""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any

from environment import ROLES, T1Environment, T2Environment
from mechanisms import MechanismConfig


@dataclass
class ActionResult:
    accepted: bool
    changed: bool
    reason: str
    executed_action: dict[str, Any] | None = None
    reject: dict[str, Any] | None = None
    support: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    completed: bool = False
    mechanism_effect: dict[str, Any] | None = None


class T1Controller:
    """Nome legado mantido para compatibilidade; controla as tarefas de calibração T1/T2."""

    def __init__(self, environment: T1Environment, config: MechanismConfig | None = None) -> None:
        self.env = environment
        self.config = config or MechanismConfig()
        self.rng = random.Random(self.config.seed)
        self._help_exposed: bool | None = None
        self._last_r3_processed_revision = 0
        if self.env.task_id == "T1":
            self._resolve_help_exposure()
        self._communication_exposed: bool | None = True if self.env.task_id == "T1" else None

    def _enabled(self, name: str) -> bool:
        return bool(self.config.enabled.get(name, False))

    def _sample(self, mechanism: str) -> bool:
        return self.rng.random() < self.config.probability(mechanism)

    def _resolve_help_exposure(self) -> None:
        if self._help_exposed is None:
            self._help_exposed = (
                self._sample("R4") if self._enabled("R4") else True
            )

    def _resolve_communication_exposure(self) -> None:
        if self._communication_exposed is None and isinstance(self.env, T2Environment) and self.env.update_applied:
            self._communication_exposed = (
                self._sample("R2") if self._enabled("R2") else True
            )
            self.env.communication_available = self._communication_exposed

    def build_observation(self, base: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Aplica R2--R4 ao que fica visível; retorna observação e metadados apenas para o log."""
        if isinstance(self.env, T2Environment) and self.env.update_applied:
            if self._enabled("R3"):
                # Uma probabilidade por atualização; se perder a oportunidade, o cache só muda ao usar refresh_feed.
                if self.env.feed_revision > self._last_r3_processed_revision:
                    if self._sample("R3"):
                        self.env.sync_observation()
                    self._last_r3_processed_revision = self.env.feed_revision
            else:
                self.env.sync_observation()
                self._last_r3_processed_revision = self.env.feed_revision
            self._resolve_communication_exposure()
            self._resolve_help_exposure()

        observation = copy.deepcopy(base)
        observation["state"] = self.env.observation_snapshot()
        available = copy.deepcopy(base.get("available_actions", []))
        if isinstance(self.env, T2Environment):
            # Ping is a one-time opportunity after the external feed update.
            if not self.env.update_applied or not self._communication_exposed:
                available = [x for x in available if x.get("name") != "send_ping"]
        if isinstance(self.env, T2Environment) and not self.env.update_applied:
            # A ajuda contextual em T2 pertence à oportunidade de incerteza após o update.
            available = [x for x in available if x.get("name") != "open_help"]
        if isinstance(self.env, T2Environment) and "NEXT_STEP_ACTIVATE_CHECKPOINT" in self.env.pings:
            # T2 pede uma comunicação predefinida, não repetição de mensagens.
            # Depois do ping correto, a oportunidade se encerra e sai do menu visível.
            available = [x for x in available if x.get("name") != "send_ping"]
        if self._help_exposed is False:
            # R4 controla especificamente a affordance open_help; checklist é separado.
            available = [x for x in available if x.get("name") != "open_help"]
        observation["available_actions"] = available
        observed_metadata = {
            "visible_feed_revision": observation["state"].get("feed_revision"),
            "actual_feed_revision": self.env.feed_revision if isinstance(self.env, T2Environment) else None,
            "communication_exposed": self._communication_exposed,
            "help_exposed": self._help_exposed,
            "active_mechanisms": dict(self.config.enabled),
            "mechanism_parameters": dict(self.config.probabilities),
            "available_action_names": [item.get("name") for item in observation["available_actions"]],
        }
        return observation, observed_metadata

    def _r1_transform(self, proposed: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Com R1, injeta em oportunidades válidas uma escolha de papel incompatível."""
        if not self._enabled("R1") or proposed.get("name") != "select_role":
            return copy.deepcopy(proposed), None
        args = proposed.get("arguments", {})
        member = args.get("member")
        role = args.get("role")
        record = self.env.members.get(member) if isinstance(member, str) else None
        # Não confundir deslize injetado com uma proposta que já era inválida.
        if not record or not record.get("available") or role not in record.get("capabilities", []):
            return copy.deepcopy(proposed), None
        if any(existing_role == role and other_member != member for other_member, existing_role in self.env.assignments.items()):
            return copy.deepcopy(proposed), None
        if self._sample("R1"):
            retained = {
                "mechanism": "R1",
                "parameter": "p_valida",
                "configured_probability": self.config.probability("R1"),
                "effect": "candidate_retained",
                "opp_id": "R1-role-selection",
                "original_action": copy.deepcopy(proposed),
                "transformed_action": copy.deepcopy(proposed),
                "reason": "A proposta válida foi mantida pelo mecanismo R1.",
            }
            return copy.deepcopy(proposed), retained
        incompatible_roles = [candidate for candidate in ROLES if candidate not in record["capabilities"]]
        if not incompatible_roles:
            return copy.deepcopy(proposed), None
        # Prefere uma função que ainda não esteja atribuída, para que o deslize seja isolado.
        unassigned = [r for r in incompatible_roles if r not in self.env.assignments.values()]
        injected_role = (unassigned or incompatible_roles)[0]
        transformed = {"name": "select_role", "arguments": {"member": member, "role": injected_role}}
        effect = {
            "mechanism": "R1",
            "parameter": "p_valida",
            "configured_probability": self.config.probability("R1"),
            "effect": "slip_injected",
            "opp_id": "R1-role-selection",
            "original_action": copy.deepcopy(proposed),
            "transformed_action": copy.deepcopy(transformed),
            "reason": "Alternativa válida no vocabulário, mas incompatível com a capacidade/regra do plano.",
        }
        return transformed, effect

    def apply(self, action: dict[str, Any]) -> ActionResult:
        proposed_action = copy.deepcopy(action)
        action, mechanism_effect = self._r1_transform(action)
        injected_r1 = bool(mechanism_effect and mechanism_effect.get("effect") == "slip_injected")
        name = action["name"]
        args = action["arguments"]
        self.env.proposal_count += 1
        accepted = False
        changed = False
        reason = ""
        support = None
        error = None

        if self.env.plan_confirmed:
            reason = "A tarefa já foi confirmada; nenhuma ação adicional é permitida."
            error = {"category": "invalid_action", "opp_id": f"{self.env.task_id}-after-confirmation", "rule_id": "TASK-TERMINAL"}
        elif name == "select_role":
            member, role = args["member"], args["role"]
            if member not in self.env.members:
                reason = f"Integrante desconhecido: {member}. Escolha um integrante dos cartões visíveis."
                error = {"category": "invalid_action", "opp_id": f"{self.env.task_id}-role-member", "rule_id": "MEMBER-EXISTS"}
            elif not self.env.members[member]["available"]:
                reason = f"{member} está indisponível. Escolha um integrante disponível."
                error = {"category": "invalid_plan", "opp_id": f"{self.env.task_id}-availability", "rule_id": "AVAILABLE"}
            elif injected_r1:
                # O erro é executado como deslize de interação; o avaliador externo detecta o plano ruim.
                self.env.assignments[member] = role
                self.env.reviewed = False
                accepted = True
                changed = True
                error = {"category": "operational_slip", "opp_id": "R1-role-selection", "rule_id": "R1-P-VALIDA"}
                reason = f"R1 injetou um deslize: a interface aceitou {member} → {role}, mas a atribuição viola a capacidade declarada."
            elif role not in self.env.members[member]["capabilities"]:
                reason = f"{member} não tem a capacidade {role}. Escolha uma função compatível com o cartão."
                error = {"category": "skill_constraint_violation", "opp_id": f"{self.env.task_id}-role-capability", "rule_id": "CAPABILITY"}
            else:
                other = next((m for m, r in self.env.assignments.items() if r == role and m != member), None)
                if other:
                    reason = f"A função {role} já está atribuída a {other}. Remova ou substitua a atribuição duplicada."
                    error = {"category": "role_missing_or_duplicated", "opp_id": f"{self.env.task_id}-role-unique", "rule_id": "UNIQUE-ROLE"}
                else:
                    previous = self.env.assignments.get(member)
                    if previous != role:
                        self.env.assignments[member] = role
                        self.env.reviewed = False
                        changed = True
                    accepted = True
                    reason = f"Atribuição registrada: {member} → {role}."
        elif name == "set_step_order":
            steps = args["steps"]
            if len(steps) != len(ROLES) or set(steps) != set(ROLES):
                reason = "A ordem precisa conter cada uma das três etapas exatamente uma vez."
                error = {"category": "dependency_violation", "opp_id": f"{self.env.task_id}-step-order", "rule_id": "STEP-COVERAGE"}
            else:
                transport = steps.index("TRANSPORT_RESOURCE")
                if transport < steps.index("LOCATE_RESOURCE") or transport < steps.index("ACTIVATE_CHECKPOINT"):
                    reason = "Transporte deve ocorrer depois de localizar o recurso e ativar o ponto de controle."
                    error = {"category": "dependency_violation", "opp_id": f"{self.env.task_id}-step-dependency", "rule_id": "STEP-DEPENDENCY"}
                else:
                    changed = steps != self.env.step_order
                    self.env.step_order = list(steps)
                    if changed:
                        self.env.reviewed = False
                    accepted = True
                    reason = "Ordem das etapas atualizada e compatível com as dependências."
        elif name == "review_plan":
            valid, reason = self.env.validate_plan()
            self.env.reviewed = valid
            accepted = True
            changed = True
            if not valid:
                error = {"category": "invalid_plan", "opp_id": f"{self.env.task_id}-review", "rule_id": "PLAN-VALID"}
        elif name == "confirm_plan":
            valid, validation_reason = self.env.validate_plan()
            if not valid:
                reason = f"Confirmação rejeitada: {validation_reason}"
                error = {"category": "invalid_plan", "opp_id": f"{self.env.task_id}-confirm", "rule_id": "PLAN-VALID"}
            elif not self.env.reviewed:
                reason = "Confirmação rejeitada: revise o plano antes de confirmá-lo."
                error = {"category": "invalid_plan", "opp_id": f"{self.env.task_id}-review-required", "rule_id": "REVIEW-FIRST"}
            else:
                self.env.plan_confirmed = True
                accepted = True
                changed = True
                reason = "Plano confirmado. O avaliador externo vai verificar o estado final."
        elif name == "open_checklist":
            self.env.checklist_open = True
            accepted = True
            changed = True
            support = {"resource": "checklist", "opened": True, "topic": None}
            reason = "Checklist aberto: atribua cada função uma vez e respeite as capacidades dos integrantes."
        elif name == "open_help":
            if (isinstance(self.env, T2Environment) and not self.env.update_applied) or self._help_exposed is False:
                reason = "R4: ajuda contextual não está exposta nesta oportunidade de suporte."
                error = {"category": "invalid_action", "opp_id": "R4-support-opportunity", "rule_id": "R4-HELP-EXPOSED"}
            else:
                topic = args["topic"]
                self.env.help_topic = topic
                accepted = True
                changed = True
                support = {"resource": "contextual_help", "opened": True, "topic": topic}
                reason = f"Ajuda contextual aberta para: {topic}."
        elif name == "refresh_feed":
            self.env.feed_refreshes += 1
            if isinstance(self.env, T2Environment):
                self.env.sync_observation()
            accepted = True
            changed = True
            reason = "Feed atualizado; a observação reflete o estado mais recente disponível."
        elif name == "send_ping":
            code = args["code"]
            if isinstance(self.env, T2Environment) and (not self.env.update_applied or not self._communication_exposed):
                reason = "R2: a oportunidade de comunicação não está disponível nesta tarefa/estado."
                error = {"category": "invalid_action", "opp_id": "R2-communication-opportunity", "rule_id": "R2-COMMUNICATE"}
            elif isinstance(self.env, T2Environment) and code != "NEXT_STEP_ACTIVATE_CHECKPOINT":
                reason = "T2 exige o ping NEXT_STEP_ACTIVATE_CHECKPOINT; o código proposto não satisfaz a comunicação da tarefa."
                error = {"category": "invalid_action", "opp_id": "T2-ping-code", "rule_id": "T2-COMMUNICATION-CODE"}
            elif isinstance(self.env, T2Environment) and code in self.env.pings:
                reason = "A comunicação exigida já foi enviada; não envie o mesmo ping novamente."
                error = {"category": "redundant_action", "opp_id": "T2-ping-once", "rule_id": "T2-PING-ONCE"}
            else:
                self.env.pings.append(code)
                accepted = True
                changed = True
                reason = f"Ping enviado: {code}."
        else:
            reason = f"Ação não implementada pelo controlador: {name}."
            error = {"category": "invalid_action", "opp_id": f"{self.env.task_id}-action-vocabulary", "rule_id": "ACTION-VOCABULARY"}

        self.env.last_feedback = reason
        if accepted:
            self.env.action_count += 1
        if not accepted:
            return ActionResult(
                accepted=False, changed=False, reason=reason,
                executed_action=None, reject={"reason": reason, "rule_id": error["rule_id"] if error else None},
                error=error, mechanism_effect=mechanism_effect,
            )
        return ActionResult(
            accepted=True, changed=changed, reason=reason,
            executed_action=copy.deepcopy(action), support=support, error=error,
            completed=self.env.plan_confirmed, mechanism_effect=mechanism_effect,
        )
