"""Grava eventos JSONL e valida cada linha contra o contrato de eventos."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class EventLogger:
    def __init__(
        self,
        path: Path,
        event_schema_path: Path,
        model: str | None,
        *,
        task_id: str = "T1",
        condition: str = "calibration",
        config_version: str = "t1-baseline-v1",
    ) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with event_schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        Draft202012Validator.check_schema(schema)
        self.validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.model = model
        self.task_id = task_id
        self.condition = condition
        self.config_version = config_version
        self.sequence = 0

    def log(
        self,
        *,
        event: str,
        actor: str,
        session_id: str,
        step: int,
        state_pre: dict[str, Any] | None = None,
        state_post: dict[str, Any] | None = None,
        observation_id: str | None = None,
        proposed_action: dict[str, Any] | None = None,
        executed_action: dict[str, Any] | None = None,
        reject: dict[str, Any] | None = None,
        support: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        outcome: dict[str, Any] | None = None,
        technical_failure: bool = False,
        technical_failure_reason: str | None = None,
        note: str | None = None,
        opportunity_id: str | None = None,
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "schema_version": "1.0",
            "sid": session_id,
            "tid": self.task_id,
            "cond": self.condition,
            "actor": actor,
            "synthetic": True,
            "cfg_ver": self.config_version,
            "ui_ver": "cli-environment-v2",
            "llm_model": self.model if actor == "llm" else None,
            "llm_version": None,
            "prompt_ver": "uxagent-action-prompt-v2" if actor == "llm" else None,
            "step": step,
            "event": event,
            "ts_sys": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "obs_id": observation_id,
            "state_pre": state_pre,
            "state_post": state_post,
            "act_prop": proposed_action,
            "act_exec": executed_action,
            "reject": reject,
            "support": support,
            "error": error,
            "opp_id": opportunity_id,
            "outcome": outcome,
            "tech_fail": technical_failure,
            "tech_fail_reason": technical_failure_reason,
            "note": note,
        }
        errors = list(self.validator.iter_errors(entry))
        if errors:
            details = "; ".join(f"{e.json_path}: {e.message}" for e in errors[:5])
            raise ValueError(f"Evento não passa no schema: {details}")
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.sequence += 1
        return entry
