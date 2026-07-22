"""Excepciones propias del conector Shodan.

Separan los tipos de fallo que el usuario debe distinguir: configuración
inválida, autenticación, red, y datos (IP no encontrada, consulta
inválida, límite de peticiones alcanzado).
"""


class ShodanConnectorError(Exception):
    """Error base del conector."""


class ShodanConfigError(ShodanConnectorError):
    """Configuración inválida: falta un campo requerido."""


class ShodanAuthError(ShodanConnectorError):
    """API key inválida o revocada."""


class ShodanNetworkError(ShodanConnectorError):
    """No se pudo alcanzar la API de Shodan (DNS, timeout, red)."""


class ShodanDataError(ShodanConnectorError):
    """La operación es válida pero la IP no está indexada, la consulta no
    tiene resultados, o se alcanzó el límite de peticiones/créditos de
    la cuenta."""
