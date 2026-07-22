"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_SHODAN_.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_SHODAN_"

_DEFAULT_BASE_URL = "https://api.shodan.io"


@dataclass(frozen=True)
class ShodanConfig:
    """Parámetros de conexión a la API de Shodan."""

    api_key: str
    base_url: str = _DEFAULT_BASE_URL
    timeout: int = 20

    @classmethod
    def from_env(cls) -> "ShodanConfig":
        """Construye la configuración desde las variables RUVIC_SHODAN_*.

        Raises:
            ValueError: si falta RUVIC_SHODAN_API_KEY.
        """
        api_key = os.environ.get(f"{ENV_PREFIX}API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                f"Falta la variable de entorno del conector shodan: "
                f"{ENV_PREFIX}API_KEY. Configura el conector en Settings → Conectores."
            )

        base_url = os.environ.get(f"{ENV_PREFIX}BASE_URL", "").strip() or _DEFAULT_BASE_URL

        return cls(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            timeout=int(os.environ.get(f"{ENV_PREFIX}REQUEST_TIMEOUT", "20")),
        )
