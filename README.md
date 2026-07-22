# conector-shodan

Conector Ruvic para Shodan: consultar información de una IP, buscar dispositivos/servicios expuestos por término, y obtener los puertos abiertos de un host.

## Capacidades

`get_host_info`, `search_devices`, `get_open_ports`. Conector de **solo lectura** — la API de Shodan usada aquí no tiene ninguna operación de escritura.

## Instalación

Requiere **Python ≥ 3.10**.

```bash
pip install git+https://github.com/tu-org/conector-shodan.git#subdirectory=lib
```

Para desarrollo local (editable, en un venv limpio):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_SHODAN_API_KEY` | Sí | API key de Shodan |
| `RUVIC_SHODAN_BASE_URL` | No | Default `https://api.shodan.io` |
| `RUVIC_SHODAN_REQUEST_TIMEOUT` | No | Segundos, default `20` |

## Permisos / prerrequisitos en Shodan

1. Crea una cuenta en [account.shodan.io](https://account.shodan.io) (tiene un nivel gratuito con créditos limitados).
2. Ve a la sección **"API"** de tu cuenta y copia tu API key.
3. No hay roles que configurar — el alcance depende de los créditos de búsqueda/escaneo de tu plan.

## Cómo correr las pruebas locales

Shodan no tiene una versión local/Docker (es un índice propietario de internet) — hace falta una API key real, aunque el **nivel gratuito** alcanza perfectamente para probar.

```bash
export RUVIC_SHODAN_API_KEY=tu_api_key_real

python test_connection.py
python validate_local.py
```

`validate_local.py` usa `8.8.8.8` (el DNS público de Google, siempre indexado en Shodan) para no depender de infraestructura propia.

Prueba también el caso de error:

```bash
RUVIC_SHODAN_API_KEY=clave-invalida python test_connection.py
# FALLO: Autenticación fallida: ...
```

## Limitaciones conocidas

- `search_devices` consume créditos de búsqueda de la cuenta — cada página de resultados es un costo.
- No implementa el endpoint de conteo/facetas (`/shodan/host/count`), que no consume créditos — podría agregarse en una versión futura si hace falta.
- No implementa la Streaming API (feed en tiempo real) — solo la REST API de consulta bajo demanda.
- No implementa gestión de alertas/monitoreo de Shodan — solo las 3 operaciones de consulta pedidas.

## Notas de integración

- El paquete pip es `ruvic-shodan-connector`; el import name es `ruvic_shodan_connector`.
- Única dependencia externa: `requests`.
- Ver `SKILL.md` para los ejemplos de uso que consume el agente.
