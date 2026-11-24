"""Importador de series de la DGA exportadas a CSV (caudal, nivel y precipitación).

La DGA no publica una API oficial documentada; su Sistema Hidrométrico en Línea
(https://snia.mop.gob.cl/dgasat) se consulta mediante formularios web. Por eso el MVP
parte de un CSV exportado por el equipo desde el portal, con las columnas de
COLUMNAS_ENTRADA, y lo normaliza al esquema común. Automatizar la descarga queda como
tarea del Sprint 1 (ver docs/fuentes_datos.md).

SUPUESTOS A VERIFICAR contra el portal antes de usar los resultados:
  - La precipitación del CSV es el monto de cada intervalo y se SUMA por día.
  - Caudal y nivel se promedian por día.
  - Las fechas están en hora local de Chile.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from frontal.config import COLUMNAS, normalizar_region

CITA_DGA = "Fuente: Dirección General de Aguas (DGA), datos provisorios no validados."

# Columnas que debe traer el CSV de entrada.
COLUMNAS_ENTRADA = ["cod_bna", "nombre", "region", "lat", "lon", "fecha_hora"]
# Variables opcionales del CSV -> (variable normalizada, forma de agregar por día).
VARIABLES_ENTRADA = {
    "precipitacion_mm": ("precip_mm", "sum"),
    "caudal_m3s": ("caudal_m3s", "mean"),
    "nivel_m": ("nivel_m", "mean"),
}


def importar_csv_dga(ruta: Path | str, sep: str = ";", decimal: str = ",") -> pd.DataFrame:
    """Lee el CSV exportado y devuelve filas diarias del esquema normalizado.

    Raises:
        ValueError: si faltan columnas obligatorias o no trae ninguna variable conocida.
    """
    crudo = pd.read_csv(ruta, sep=sep, decimal=decimal, dtype={"cod_bna": str})
    faltantes = [c for c in COLUMNAS_ENTRADA if c not in crudo.columns]
    if faltantes:
        raise ValueError(f"Al CSV de la DGA le faltan columnas: {faltantes}")
    presentes = [v for v in VARIABLES_ENTRADA if v in crudo.columns]
    if not presentes:
        raise ValueError(f"El CSV no trae ninguna variable de {list(VARIABLES_ENTRADA)}.")

    crudo["fecha"] = pd.to_datetime(crudo["fecha_hora"], errors="coerce").dt.normalize()
    crudo["region"] = crudo["region"].map(normalizar_region)
    clave = ["cod_bna", "nombre", "region", "lat", "lon", "fecha"]

    partes = []
    for columna in presentes:
        variable, how = VARIABLES_ENTRADA[columna]
        # dropna=False conserva las estaciones sin región (quedarán fuera de los cálculos).
        diario = (
            crudo.dropna(subset=["fecha", columna])
            .groupby(clave, dropna=False)[columna]
            .agg(how)
            .reset_index()
            .rename(columns={columna: "valor"})
        )
        diario["variable"] = variable
        partes.append(diario)

    out = pd.concat(partes, ignore_index=True)
    out = out.rename(columns={"cod_bna": "cod_estacion", "nombre": "estacion"})
    out["fuente"] = "DGA"
    return out[COLUMNAS]
