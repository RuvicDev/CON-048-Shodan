"""Conector Ruvic para Shodan (búsqueda de dispositivos/servicios expuestos, solo lectura)."""

from .client import ShodanClient
from .config import ENV_PREFIX, ShodanConfig
from .exceptions import (
    ShodanAuthError,
    ShodanConfigError,
    ShodanConnectorError,
    ShodanDataError,
    ShodanNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "ShodanAuthError",
    "ShodanClient",
    "ShodanConfig",
    "ShodanConfigError",
    "ShodanConnectorError",
    "ShodanDataError",
    "ShodanNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
