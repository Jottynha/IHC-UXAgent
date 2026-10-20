"""Configuração versionada dos mecanismos de engenharia R1--R4.

Os mecanismos alteram o estado/canal de observação no controlador; seus parâmetros
nunca são interpolados no prompt do modelo.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PROBABILITIES = {
    "R1": ("p_valida", 0.90),
    "R2": ("p_comunicar", 0.65),
    "R3": ("p_estado_fresco", 0.70),
    "R4": ("p_ajuda_exposta", 0.25),
}


@dataclass
class MechanismConfig:
    version: str = "uxagent-r1-r4-v2"
    seed: int = 42
    enabled: dict[str, bool] = field(default_factory=lambda: {k: False for k in DEFAULT_PROBABILITIES})
    probabilities: dict[str, float] = field(default_factory=lambda: {k: v[1] for k, v in DEFAULT_PROBABILITIES.items()})

    @classmethod
    def from_file(cls, path: str | Path) -> "MechanismConfig":
        with Path(path).open("r", encoding="utf-8") as f:
            raw = json.load(f)
        enabled: dict[str, bool] = {}
        probabilities: dict[str, float] = {}
        mechanisms = raw.get("mechanisms", {})
        for key, (parameter, default_probability) in DEFAULT_PROBABILITIES.items():
            item = mechanisms.get(key, {})
            enabled[key] = bool(item.get("enabled", False))
            probabilities[key] = float(item.get("probability", default_probability))
            if not 0.0 <= probabilities[key] <= 1.0:
                raise ValueError(f"Probabilidade de {key} deve estar entre 0 e 1.")
        return cls(
            version=str(raw.get("config_version", "uxagent-r1-r4-v2")),
            seed=int(raw.get("seed", 42)),
            enabled=enabled,
            probabilities=probabilities,
        )

    def enable(self, names: list[str]) -> None:
        for name in names:
            if name not in DEFAULT_PROBABILITIES:
                raise ValueError(f"Mecanismo desconhecido: {name}. Use R1, R2, R3 ou R4.")
            self.enabled[name] = True

    def probability(self, mechanism: str) -> float:
        return self.probabilities[mechanism]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_version": self.version,
            "seed": self.seed,
            "mechanisms": {
                key: {
                    "enabled": self.enabled[key],
                    "parameter": DEFAULT_PROBABILITIES[key][0],
                    "probability": self.probabilities[key],
                }
                for key in DEFAULT_PROBABILITIES
            },
        }

    @property
    def fingerprint(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:10]

    @property
    def log_version(self) -> str:
        return f"{self.version}-{self.fingerprint}"
