"""Vocabulário compartilhado de ações e validação local."""
from __future__ import annotations

import json
import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BASE_DIR = Path(__file__).resolve().parent
ACTION_SCHEMA_PATH = BASE_DIR / "uxagent_action.schema.json"
UI_SCHEMA_PATH = BASE_DIR / "uxagent_ui.schema.json"
UI_VERSION = "ui-contract-v2"
PROMPT_VERSION = "uxagent-action-prompt-v4"

ACTION_TEMPLATES: tuple[dict[str, Any], ...] = (
    {"name": "select_role", "arguments": {"member": "um integrante visível", "role": "uma função do conjunto permitido"}},
    {"name": "remove_assignment", "arguments": {"member": "um integrante com atribuição"}},
    {"name": "set_step_order", "arguments": {"steps": ["LOCATE_RESOURCE", "ACTIVATE_CHECKPOINT", "TRANSPORT_RESOURCE"]}},
    {"name": "open_checklist", "arguments": {}},
    {"name": "open_help", "arguments": {"topic": "mission_requirements | role_constraints | task_dependencies"}},
    {"name": "refresh_feed", "arguments": {}},
    {"name": "send_ping", "arguments": {"code": "PLAN_UPDATED | NEXT_STEP_ACTIVATE_CHECKPOINT"}},
    {"name": "review_plan", "arguments": {}},
    {"name": "confirm_plan", "arguments": {}},
)


def load_action_schema() -> dict[str, Any]:
    with ACTION_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


ACTION_VALIDATOR = Draft202012Validator(load_action_schema())


def load_ui_schema() -> dict[str, Any]:
    with UI_SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


UI_VALIDATOR = Draft202012Validator(load_ui_schema())


def validate_action(action: Any) -> str | None:
    """Retorna uma mensagem curta ou ``None`` quando a ação é válida."""
    errors = sorted(ACTION_VALIDATOR.iter_errors(action), key=lambda error: list(error.path))
    if not errors:
        return None
    return "; ".join(error.message for error in errors[:3])


def validate_view_model(view_model: Any) -> str | None:
    errors = sorted(UI_VALIDATOR.iter_errors(view_model), key=lambda error: list(error.path))
    if not errors:
        return None
    return "; ".join(error.message for error in errors[:3])


def action_templates() -> list[dict[str, Any]]:
    """Retorna cópias para que uma camada de apresentação não altere o contrato."""
    return copy.deepcopy(list(ACTION_TEMPLATES))
