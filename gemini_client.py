"""Cliente Gemini para propor uma ação estruturada do UXAgent (T1)."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

BASE_DIR = Path(__file__).resolve().parent
ACTION_SCHEMA_PATH = BASE_DIR / "uxagent_action.schema.json"
DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiClientError(RuntimeError):
    """Erro de chamada/parse à API; nunca inclui a chave de API."""


def load_action_schema() -> dict[str, Any]:
    with ACTION_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    Draft202012Validator.check_schema(schema)
    return schema


def _remove_unsupported_api_keywords(node: Any) -> None:
    """Deixa algumas restrições para a validação local, mais completa."""
    if isinstance(node, dict):
        node.pop("uniqueItems", None)
        for value in node.values():
            _remove_unsupported_api_keywords(value)
    elif isinstance(node, list):
        for item in node:
            _remove_unsupported_api_keywords(item)


def to_gemini_schema(local_schema: dict[str, Any]) -> dict[str, Any]:
    """Adapta o schema local à saída estruturada; validação completa é local."""
    branches: list[dict[str, Any]] = []
    for original in local_schema.get("oneOf", []):
        branch = copy.deepcopy(original)
        props = branch.get("properties", {})
        action_name = props.get("name", {})
        if "const" in action_name:
            action_name["enum"] = [action_name.pop("const")]
        args = props.get("arguments", {})
        args.pop("maxProperties", None)
        if args.get("type") == "object" and not args.get("properties"):
            args.setdefault("required", [])
        _remove_unsupported_api_keywords(branch)
        branches.append(branch)
    if not branches:
        raise ValueError("O schema de ações não possui alternativas em 'oneOf'.")
    return {
        "type": "object",
        "properties": {
            "action": {
                "anyOf": branches,
                "description": "Uma única ação válida do vocabulário do UXAgent.",
            }
        },
        "required": ["action"],
    }


class GeminiActionPolicy:
    """Pede uma única ação ao Gemini, sem executar ou avaliar a ação por conta própria."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise GeminiClientError(
                "GEMINI_API_KEY não está definida. Configure-a no terminal antes de executar."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise GeminiClientError(
                "SDK ausente. Execute: python -m pip install google-genai jsonschema"
            ) from exc
        self.model = model or os.environ.get("UXAGENT_MODEL", DEFAULT_MODEL)
        self.client = genai.Client(api_key=api_key)
        self.local_schema = load_action_schema()
        self.api_schema = to_gemini_schema(self.local_schema)
        self.validator = Draft202012Validator(self.local_schema)

    def propose_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        instructions = (
            "Você é a política de ações do UXAgent, em uma tarefa sintética controlada. "
            "Escolha exatamente uma ação do schema por chamada. Não afirme que executou "
            "uma ação, não declare sucesso e não invente integrantes ou valores. Use apenas "
            "o estado visível e as ações presentes em available_actions. Siga o objetivo da "
            "tarefa recebida, corrija atribuições incompatíveis, consulte/atualize o feed "
            "quando necessário, comunique a próxima etapa se send_ping estiver disponível, "
            "revise o plano e só então confirme. Se uma ação for rejeitada, leia o feedback "
            "atualizado e tente uma alternativa válida. Mecanismos de controle podem afetar "
            "a disponibilidade de informações ou ações; não suponha que uma ação oculta está disponível."
        )
        prompt = (
            f"{instructions}\n\nEstado visível da interface (JSON):\n"
            f"{json.dumps(observation, ensure_ascii=False, indent=2)}\n\n"
            "Retorne somente a ação seguinte no formato especificado."
        )
        try:
            response = self.client.interactions.create(
                model=self.model,
                input=prompt,
                response_format=[
                    {
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": self.api_schema,
                    }
                ],
            )
            raw = getattr(response, "output_text", None)
            if not raw:
                raise GeminiClientError("A API não retornou texto de saída.")
            wrapper = json.loads(raw)
            action = wrapper["action"]
            errors = list(self.validator.iter_errors(action))
            if errors:
                detail = "; ".join(e.message for e in errors[:3])
                raise GeminiClientError(f"Ação retornada não passa no schema local: {detail}")
            return action
        except GeminiClientError:
            raise
        except Exception as exc:  # evita exibir chave ou objeto de cliente
            raise GeminiClientError(
                f"Falha na chamada/parse do Gemini ({type(exc).__name__}): {exc}"
            ) from exc
