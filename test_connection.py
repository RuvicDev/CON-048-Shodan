"""Prueba de conexión estándar del conector shodan.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_SHODAN_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Verifica la API key consultando la información de la cuenta."""
    try:
        from ruvic_shodan_connector import (
            ShodanAuthError,
            ShodanClient,
            ShodanDataError,
            ShodanNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-shodan-connector no está instalada. "
            "Instala con: pip install git+https://github.com/tu-org/"
            "conector-shodan.git#subdirectory=lib",
        )

    try:
        client = ShodanClient()  # valida config
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except ShodanAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except ShodanNetworkError as exc:
        return False, f"Error de red: {exc}"
    except ShodanDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return True, f"Conexión exitosa a {client.config.base_url}"


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
