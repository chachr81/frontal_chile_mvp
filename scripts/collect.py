"""Línea de comandos para recolectar datos y dejarlos en data/processed.

Uso:
  python scripts/collect.py dmc --inspect          # muestra los campos reales del servicio
  python scripts/collect.py dmc                    # descarga el resumen diario de la DMC
  python scripts/collect.py dga-csv ruta.csv       # importa un CSV exportado de la DGA
  python scripts/collect.py dga-dgasat --region "Región Metropolitana de Santiago" \
      --inicio 2026-06-01 --fin 2026-11-23         # extrae series diarias reales de la DGA

Las credenciales de la DMC se leen de las variables DMC_USUARIO y DMC_TOKEN (archivo .env).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from frontal.collectors import dga_csv, dga_dgasat, dmc
from frontal.collectors.almacen import actualizar_observaciones
from frontal.config import DATOS_CRUDOS, RAIZ, ZONA_HORARIA, normalizar_region


def _leer_env() -> None:
    """Carga variables desde .env (formato CLAVE=valor) sin dependencias externas."""
    archivo = RAIZ / ".env"
    if not archivo.exists():
        return
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


def _comando_dmc(inspeccionar: bool) -> None:
    """Descarga el resumen diario de la DMC, lo guarda crudo y lo normaliza."""
    usuario, token = os.environ.get("DMC_USUARIO"), os.environ.get("DMC_TOKEN")
    if not usuario or not token:
        raise SystemExit("Faltan DMC_USUARIO y DMC_TOKEN (cópielos en .env, ver .env.example).")
    geojson = dmc.descargar_resumen_diario(usuario, token)

    # Se guarda la respuesta cruda para trazabilidad (data/raw está en .gitignore).
    ahora = datetime.now(ZoneInfo(ZONA_HORARIA))
    destino = DATOS_CRUDOS / "dmc"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{ahora:%Y%m%d_%H%M}.json").write_text(json.dumps(geojson), encoding="utf-8")

    if inspeccionar:
        primera = (geojson.get("features") or [{}])[0]
        print("Campos de la primera estación:", sorted((primera.get("properties") or {})))
        return

    nuevas = dmc.parsear_resumen_diario(geojson, ahora.date())
    total = actualizar_observaciones(nuevas, {"DMC": dmc.CITA_DMC})
    print(f"DMC: {len(nuevas)} observaciones nuevas; total en archivo: {len(total)}.")


def _comando_dga(ruta: Path) -> None:
    """Importa un CSV de la DGA y lo agrega al archivo de observaciones."""
    nuevas = dga_csv.importar_csv_dga(ruta)
    total = actualizar_observaciones(nuevas, {"DGA": dga_csv.CITA_DGA})
    print(f"DGA: {len(nuevas)} observaciones diarias; total en archivo: {len(total)}.")


def _comando_dgasat(region: str, inicio: date, fin: date, limite: int | None) -> None:
    """Extrae series diarias de la DGA (DGASAT) para las estaciones vigentes de una región.

    El catálogo de estaciones proviene del servidor MCP "Red de Monitoreo Chile" y está
    versionado en data/catalogo/dga_estaciones.json.
    """
    catalogo = json.loads((RAIZ / "data" / "catalogo" / "dga_estaciones.json").read_text(encoding="utf-8"))
    objetivo = normalizar_region(region)
    estaciones = [e for e in catalogo["estaciones"] if normalizar_region(e["region"]) == objetivo]
    if limite:
        estaciones = estaciones[:limite]
    print(f"Región {objetivo}: {len(estaciones)} estaciones; periodo {inicio} a {fin}.")

    nuevas, bitacora = dga_dgasat.recolectar(
        estaciones, inicio, fin, carpeta_crudos=DATOS_CRUDOS / "dga_dgasat" / "html")

    # Se guarda la bitácora de cobertura (qué entregó cada estación) para auditoría.
    ahora = datetime.now(ZoneInfo(ZONA_HORARIA))
    destino = DATOS_CRUDOS / "dga_dgasat"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"bitacora_{ahora:%Y%m%d_%H%M}.json").write_text(
        json.dumps(bitacora, ensure_ascii=False, indent=2), encoding="utf-8")

    if nuevas.empty:
        raise SystemExit("La DGA no entregó observaciones para el periodo solicitado.")
    total = actualizar_observaciones(nuevas, {"DGA": dga_dgasat.CITA_DGA})
    print(f"DGA (DGASAT): {len(nuevas)} observaciones; total en archivo: {len(total)}.")


def main() -> None:
    """Interpreta los argumentos y ejecuta el comando elegido."""
    _leer_env()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)
    p_dmc = sub.add_parser("dmc", help="Descarga el resumen diario de la DMC")
    p_dmc.add_argument("--inspect", action="store_true", help="Solo muestra los campos")
    p_dga = sub.add_parser("dga-csv", help="Importa un CSV exportado de la DGA")
    p_dga.add_argument("ruta", type=Path)
    p_sat = sub.add_parser("dga-dgasat", help="Extrae series diarias reales de la DGA (DGASAT)")
    p_sat.add_argument("--region", default="Región Metropolitana de Santiago")
    p_sat.add_argument("--inicio", type=date.fromisoformat, required=True)
    p_sat.add_argument("--fin", type=date.fromisoformat, required=True)
    p_sat.add_argument("--limite", type=int, default=None, help="Máximo de estaciones (pruebas)")
    args = parser.parse_args()
    if args.comando == "dga-dgasat":
        _comando_dgasat(args.region, args.inicio, args.fin, args.limite)
    elif args.comando == "dmc":
        _comando_dmc(args.inspect)
    else:
        _comando_dga(args.ruta)


if __name__ == "__main__":
    main()
