"""Validación local del conector shodan: ejercita las 3 capacidades.

Requiere la env var RUVIC_SHODAN_API_KEY exportada con una API key real
de Shodan (hay un nivel gratuito al crear una cuenta). Usa 8.8.8.8 (DNS
público de Google, siempre indexado en Shodan) para no depender de
infraestructura propia.
"""

from ruvic_shodan_connector import ShodanClient, setup_logging

setup_logging("INFO")
client = ShodanClient()

IP_PRUEBA = "8.8.8.8"

print(f"== 1. Consultar informacion de {IP_PRUEBA} ==")
info = client.get_host_info(IP_PRUEBA)
print(f"  org={info.get('org')} pais={info.get('country_name')} puertos={info.get('ports')}")

print(f"== 2. Obtener solo los puertos abiertos de {IP_PRUEBA} ==")
puertos = client.get_open_ports(IP_PRUEBA)
print(f"  {puertos}")

print("== 3. Buscar dispositivos por termino ==")
resultado = client.search_devices("nginx country:US", max_results=3)
print(f"  {resultado['total']} coincidencias totales, mostrando {len(resultado['matches'])}")
for m in resultado["matches"]:
    print(f"    {m.get('ip_str')}:{m.get('port')} - {m.get('org')}")

print("\nValidación completa.")
