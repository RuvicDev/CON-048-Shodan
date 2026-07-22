"""Cliente para consultar dispositivos y servicios expuestos en Shodan.

Capacidades:
- get_host_info():    consultar toda la información que Shodan tiene de una IP.
- search_devices():   buscar dispositivos/servicios por término (sintaxis de búsqueda de Shodan).
- get_open_ports():   obtener solo la lista de puertos abiertos de una IP (más liviano que get_host_info).

Este conector es de solo lectura por naturaleza — la API de Shodan usada
aquí no tiene ninguna operación de escritura/modificación; solo consulta
un índice de dispositivos ya escaneados por Shodan.

Autenticación: API key de Shodan, enviada como parámetro de query `key`
(no como header — es la convención de esta API). Las credenciales
SIEMPRE provienen de variables de entorno RUVIC_SHODAN_* (ver
config.ShodanConfig.from_env). Prohibido hardcodearlas.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from .config import ShodanConfig
from .exceptions import ShodanAuthError, ShodanDataError, ShodanNetworkError
from .logging_utils import get_logger


class ShodanClient:
    """Cliente de Shodan autenticado con una API key.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_SHODAN_* (comportamiento estándar
            en el runtime de la plataforma).

    Ejemplo:
        >>> client = ShodanClient()  # lee RUVIC_SHODAN_* del entorno
        >>> client.get_open_ports("8.8.8.8")
        {'ip_str': '8.8.8.8', 'ports': [53, 443]}
    """

    def __init__(self, config: ShodanConfig | None = None) -> None:
        self.config = config or ShodanConfig.from_env()
        self._logger = get_logger()

    # ------------------------------------------------------------------ #
    # Peticiones HTTP
    # ------------------------------------------------------------------ #

    def _request(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        url = f"{self.config.base_url}{path}"
        query = dict(params or {})
        query["key"] = self.config.api_key
        try:
            return requests.get(url, params=query, timeout=self.config.timeout)
        except Timeout as exc:
            raise ShodanNetworkError(
                f"Tiempo de espera agotado ({self.config.timeout}s) llamando a {path}."
            ) from exc
        except RequestsConnectionError as exc:
            raise ShodanNetworkError(f"No se pudo conectar a {url}: {exc}") from exc
        except RequestException as exc:
            raise ShodanNetworkError(f"Error de red: {exc}") from exc

    def _raise_for_error(self, resp: requests.Response, context: str) -> None:
        try:
            payload = resp.json()
            message = payload.get("error", resp.text[:300])
        except ValueError:
            message = resp.text[:300] or "Error desconocido"

        if resp.status_code == 401:
            raise ShodanAuthError(f"API key inválida o revocada en {context}: {message}")
        if resp.status_code == 404:
            raise ShodanDataError(f"No encontrado en {context}: {message}")
        if resp.status_code == 429:
            raise ShodanDataError(
                f"Límite de peticiones/créditos alcanzado en {context}: {message}. "
                "Espera antes de reintentar, o revisa el plan de tu cuenta de Shodan."
            )
        raise ShodanDataError(f"Error de Shodan en {context} (HTTP {resp.status_code}): {message}")

    # ------------------------------------------------------------------ #
    # Ping / prueba de conexión
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """Verifica la API key consultando la información de la cuenta."""
        resp = self._request("/api-info")
        if resp.status_code != 200:
            self._raise_for_error(resp, "ping")
        self._logger.info("Ping exitoso a Shodan")
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: consultar información de una IP
    # ------------------------------------------------------------------ #

    def get_host_info(self, ip: str, include_history: bool = False) -> dict[str, Any]:
        """Consulta toda la información que Shodan tiene indexada de una IP.

        Args:
            ip: dirección IP a consultar (ej. "8.8.8.8").
            include_history: si es True, incluye banners históricos (no
                solo el escaneo más reciente). Default False.

        Returns:
            Dict con los datos del host: "ip_str", "org", "isp", "country_name",
            "hostnames", "ports" (lista de puertos abiertos), "data" (lista
            de banners/servicios detectados por puerto), entre otros campos
            que Shodan reporte.

        Ejemplo:
            >>> client.get_host_info("8.8.8.8")
            {'ip_str': '8.8.8.8', 'org': 'Google LLC', 'ports': [53, 443], ...}
        """
        if not ip or not ip.strip():
            raise ShodanDataError("La IP no puede estar vacía.")

        resp = self._request(f"/shodan/host/{ip.strip()}", params={"history": str(include_history).lower()})
        if resp.status_code != 200:
            self._raise_for_error(resp, f"get_host_info {ip}")

        data = resp.json()
        self._logger.info("get_host_info %s: %d puerto(s)", ip, len(data.get("ports", [])))
        return data

    # ------------------------------------------------------------------ #
    # Capacidad 2: buscar dispositivos/servicios por término
    # ------------------------------------------------------------------ #

    def search_devices(self, query: str, max_results: int = 20, page: int = 1) -> dict[str, Any]:
        """Busca dispositivos/servicios expuestos por término.

        Args:
            query: consulta con la sintaxis de búsqueda de Shodan (ej.
                "apache country:DE", "port:22 org:\"Acme Corp\"").
            max_results: máximo de resultados a retornar de esta página
                (Shodan pagina en bloques de 100; este parámetro recorta
                localmente si pides menos).
            page: página de resultados (cada página consume créditos de
                búsqueda de la cuenta).

        Returns:
            Dict con "total" (resultados totales que coinciden) y "matches"
            (lista de dispositivos encontrados, cada uno con "ip_str",
            "port", "org", "hostnames", "data" con el banner).

        Ejemplo:
            >>> client.search_devices("apache country:DE", max_results=5)
            {'total': 15234, 'matches': [{'ip_str': '...', 'port': 80, ...}, ...]}
        """
        if not query or not query.strip():
            raise ShodanDataError("La consulta de búsqueda no puede estar vacía.")

        resp = self._request("/shodan/host/search", params={"query": query.strip(), "page": page})
        if resp.status_code != 200:
            self._raise_for_error(resp, f"search_devices {query!r}")

        payload = resp.json()
        matches = payload.get("matches", [])[:max_results]
        self._logger.info(
            "search_devices %r: %d total, %d retornado(s)",
            query, payload.get("total", 0), len(matches),
        )
        return {"total": payload.get("total", 0), "matches": matches}

    # ------------------------------------------------------------------ #
    # Capacidad 3: obtener los puertos abiertos de una IP
    # ------------------------------------------------------------------ #

    def get_open_ports(self, ip: str) -> dict[str, Any]:
        """Obtiene solo la lista de puertos abiertos de una IP (más liviano
        que `get_host_info`, usa el modo "minify" de Shodan).

        Args:
            ip: dirección IP a consultar.

        Returns:
            Dict con "ip_str" y "ports" (lista de enteros).

        Ejemplo:
            >>> client.get_open_ports("8.8.8.8")
            {'ip_str': '8.8.8.8', 'ports': [53, 443]}
        """
        if not ip or not ip.strip():
            raise ShodanDataError("La IP no puede estar vacía.")

        resp = self._request(f"/shodan/host/{ip.strip()}", params={"minify": "true"})
        if resp.status_code != 200:
            self._raise_for_error(resp, f"get_open_ports {ip}")

        data = resp.json()
        result = {"ip_str": data.get("ip_str", ip.strip()), "ports": data.get("ports", [])}
        self._logger.info("get_open_ports %s: %d puerto(s)", ip, len(result["ports"]))
        return result
