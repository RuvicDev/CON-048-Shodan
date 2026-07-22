---
name: shodan
description: "Usa la librería ruvic_shodan_connector para consultar dispositivos y servicios expuestos en internet vía Shodan - consultar toda la información indexada de una IP (get_host_info), buscar dispositivos/servicios por término con la sintaxis de búsqueda de Shodan (search_devices), y obtener solo los puertos abiertos de un host (get_open_ports). Úsala cuando el usuario pida investigar qué expone una IP, buscar dispositivos de cierto tipo expuestos en internet, o revisar qué puertos tiene abiertos un host. Conector de solo lectura, sin operaciones de escritura."
triggers:
- shodan
- puertos abiertos
- dispositivos expuestos
- osint
- reconocimiento de red
---

# Conector Shodan (ruvic_shodan_connector)

Librería Python para consultar el motor de búsqueda de dispositivos conectados a internet Shodan, autenticada con una API key. Está **preinstalada en el runtime** cuando el conector está configurado (si no, instálala con `pip install git+https://github.com/tu-org/conector-shodan.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de variables de entorno, disponibles cuando el conector `shodan` está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_SHODAN_API_KEY` | Siempre requerida |
| `RUVIC_SHODAN_BASE_URL` | (opcional) default `https://api.shodan.io` |
| `RUVIC_SHODAN_REQUEST_TIMEOUT` | (opcional) segundos, default `20` |

Si estas variables NO existen, el conector no está configurado: no generes código que lo use; indica al usuario que lo configure en **Settings → Conectores**.

El código generado **NUNCA** usa nombres de variable con segmento de alias (`_DEFAULT_`, `_TEST_`, `_PRODUCCION_`, etc.) — siempre `{ENV_PREFIX}{CAMPO}` tal cual, sin importar cuántas instancias de este conector haya configuradas. Esto aplica salvo que dichos nombres aparezcan explícitamente en una sección autogenerada al final de este skill.

## Conexión (siempre igual)

```python
from ruvic_shodan_connector import ShodanClient

client = ShodanClient()  # lee RUVIC_SHODAN_* del entorno automáticamente
```

## Capacidad 1 — Consultar información de una IP

```python
info = client.get_host_info("8.8.8.8")
print(info["org"], info["ports"])
for banner in info.get("data", []):
    print(banner.get("port"), banner.get("product"))
```

## Capacidad 2 — Buscar dispositivos por término

Usa la sintaxis de búsqueda de Shodan (filtros tipo `filtro:valor` combinables con texto libre):

```python
resultado = client.search_devices("apache country:DE", max_results=10)
print(f"{resultado['total']} coincidencias totales")
for m in resultado["matches"]:
    print(m["ip_str"], m["port"], m.get("org"))
```

⚠️ Cada página de resultados de búsqueda consume **créditos de búsqueda** de la cuenta de Shodan configurada — no llames a `search_devices` en un loop sin necesidad real.

## Capacidad 3 — Obtener los puertos abiertos de una IP

Más liviano que `get_host_info` si solo necesitas los puertos:

```python
puertos = client.get_open_ports("8.8.8.8")
print(puertos["ports"])  # ej. [53, 443]
```

## Este conector es de solo lectura

No tiene ningún método de escritura/modificación — Shodan es un motor de búsqueda de un índice ya recolectado, no una herramienta de escaneo activo bajo demanda desde este conector. Si el usuario pide "escanear" una IP en tiempo real, aclara que este conector consulta el índice existente de Shodan, no ejecuta un escaneo nuevo.

## Manejo de errores

```python
from ruvic_shodan_connector import ShodanAuthError, ShodanNetworkError, ShodanDataError

try:
    client.get_host_info("8.8.8.8")
except ShodanAuthError:
    print("API key inválida — revisa la configuración del conector")
except ShodanNetworkError:
    print("No se pudo conectar a Shodan — revisa la red")
except ShodanDataError as e:
    print(f"Error de datos: {e}")  # ej. IP no indexada, limite de creditos alcanzado
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_SHODAN_*` (el constructor de `ShodanClient` ya lo hace).
2. Nunca imprimas `RUVIC_SHODAN_API_KEY` en logs ni en la salida.
3. Ten presente que `search_devices` consume créditos de búsqueda — no lo llames repetidamente sin necesidad.
4. Si `get_host_info`/`get_open_ports` fallan con "no encontrado", significa que Shodan no tiene esa IP indexada (no necesariamente que el host esté caído) — comunícalo así al usuario.
5. No presentes los resultados como "vulnerabilidades confirmadas" — Shodan reporta banners/servicios detectados, la interpretación de riesgo la debe hacer una persona.
