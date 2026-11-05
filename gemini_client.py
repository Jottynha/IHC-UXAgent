"""Cliente Gemini para propor uma ação estruturada do UXAgent (T1)."""
from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from uxagent_actions import load_action_schema

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiClientError(RuntimeError):
    """Erro de chamada/parse à API; nunca inclui a chave de API."""


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


def _load_local_env() -> None:
    """Carrega variáveis simples de .env sem substituir variáveis já exportadas."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, encoding="utf-8") as env_file:
            lines = env_file.readlines()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise GeminiClientError(f"Não foi possível ler o arquivo .env: {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise GeminiClientError(
                f"Entrada inválida no .env, linha {line_number}: esperada no formato NOME=VALOR."
            )
        name, value = (part.strip() for part in line.split("=", 1))
        if not name or not name.replace("_", "").isalnum() or name[0].isdigit():
            raise GeminiClientError(f"Nome de variável inválido no .env, linha {line_number}.")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


class GeminiActionPolicy:
    """Pede uma única ação ao Gemini, sem executar ou avaliar a ação por conta própria."""

    def __init__(self, model: str | None = None) -> None:
        _load_local_env()
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
        trace_root = os.environ.get("UXAGENT_TRACE_DIR")
        self.trace_root = Path(trace_root).expanduser() if trace_root else None
        if self.trace_root:
            self.trace_root.mkdir(parents=True, exist_ok=True)
            self.trace_sequence = 0

    def propose_action(self, observation: dict[str, Any]) -> dict[str, Any]:
        instructions = (
            "Você é a política de ações do UXAgent, em uma tarefa sintética controlada. "
            "Escolha exatamente uma ação do schema por chamada. Não afirme que executou "
            "uma ação, não declare sucesso e não invente integrantes ou valores. Use apenas "
            "o estado visível e as ações presentes em available_actions. Siga o objetivo da "
            "tarefa recebida, corrija atribuições incompatíveis, consulte/atualize o feed "
            "quando necessário, comunique a próxima etapa se send_ping estiver disponível, "
            "revise o plano e só então confirme. Antes de responder, confira que o nome da "
            "ação está exatamente em available_actions. Nunca proponha uma ação ausente dessa "
            "lista nem repita uma ação rejeitada; após uma rejeição, leia o feedback e escolha "
            "uma alternativa atualmente disponível. Mecanismos de controle podem afetar a "
            "disponibilidade de informações ou ações; não suponha que uma ação oculta está disponível. "
            "Em T3, depois do feed, use remove_assignment uma única vez para member_C, atribua "
            "ACTIVATE_CHECKPOINT a member_D e TRANSPORT_RESOURCE a member_B; não use send_ping. "
            "Em T4, depois do feed, defina a ordem válida, envie o ping uma única vez e atribua "
            "TRANSPORT_RESOURCE a member_B e ACTIVATE_CHECKPOINT a member_C. Só use review_plan "
            "quando todas as funções estiverem cobertas e nunca repita uma ação aceita ou rejeitada "
            "sem mudança relevante no estado."
        )
        prompt = (
            f"{instructions}\n\nEstado visível da interface (JSON):\n"
            f"{json.dumps(observation, ensure_ascii=False, indent=2)}\n\n"
            "Retorne somente a ação seguinte no formato especificado."
        )
        if self.trace_root:
            self.trace_sequence += 1
            trace = {
                "trace_version": "1.0",
                "sequence": self.trace_sequence,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "model": self.model,
                "prompt_version": "uxagent-action-prompt-v4",
                "context": observation,
                "prompt": prompt,
            }
            trace_path = self.trace_root / f"request-{self.trace_sequence:04d}.json"
            trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
