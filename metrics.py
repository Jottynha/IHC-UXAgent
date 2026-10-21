"""Cálculo auditável das métricas mínimas do UXAgent.

As funções operam sobre registros já validados pelo schema de eventos. Eventos
com falha técnica não são convertidos silenciosamente em erro funcional.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def _events(records: Iterable[dict[str, Any]], event_name: str) -> list[dict[str, Any]]:
    return [record for record in records if record.get("event") == event_name]


def summarize_session(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Agrega uma sessão sem inferir sucesso a partir do texto do agente."""
    materialized = list(records)
    evaluations = _events(materialized, "task_evaluated")
    endings = _events(materialized, "task_end")
    technical_failures = [record for record in materialized if record.get("tech_fail")]
    executed = _events(materialized, "action_executed")
    supports = [record for record in materialized if record.get("event") == "support_opened"]
    errors = [record for record in materialized if record.get("error")]
    opportunities = [
        record.get("opp_id") or (record.get("error") or {}).get("opp_id")
        for record in materialized
    ]

    outcome = (evaluations[-1] if evaluations else endings[-1] if endings else {}).get("outcome")
    if technical_failures or outcome is None or outcome.get("status") in {"unknown", "interrupted"}:
        success: bool | None = None if technical_failures or outcome is None else False
    else:
        success = outcome.get("success")

    error_instances = {
        (
            error.get("category"),
            error.get("opp_id") or record.get("opp_id") or f"event-{index}",
        )
        for index, record in enumerate(errors)
        if isinstance(error := record.get("error"), dict) and error.get("category")
    }
    error_categories = Counter(category for category, _ in error_instances)
    distinct_opportunities = {opportunity for opportunity in opportunities if opportunity}

    return {
        "status": "unknown" if success is None else "success" if success else "failure",
        "success": success,
        "actions_executed": len(executed),
        "supports_used": len(supports),
        "errors_by_category": dict(error_categories),
        "errors": len(error_instances),
        "error_opportunities": len(distinct_opportunities),
        "error_rate": len(error_instances) / len(distinct_opportunities) if distinct_opportunities else None,
        "technical_failures": len(technical_failures),
    }


def summarize_sessions(sessions: Iterable[Iterable[dict[str, Any]]]) -> dict[str, Any]:
    """Agrega sessões e preserva o caso de denominador nulo."""
    summaries = [summarize_session(session) for session in sessions]
    started = len(summaries)
    known = [summary for summary in summaries if summary["success"] is not None]
    successful = sum(summary["success"] is True for summary in known)
    return {
        "sessions": summaries,
        "success_rate": successful / started if started else None,
        "known_success_rate": successful / len(known) if known else None,
        "started": started,
        "known_outcomes": len(known),
        "unknown_outcomes": started - len(known),
    }