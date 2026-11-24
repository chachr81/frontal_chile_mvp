"""Lectura y validación del archivo de observaciones y de sus metadatos."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from frontal.config import ARCHIVO_METADATOS, ARCHIVO_OBSERVACIONES, COLUMNAS, VARIABLES


def tabla_vacia() -> pd.DataFrame:
    """Devuelve una tabla sin filas con el esquema normalizado (estado 'sin datos')."""
    df = pd.DataFrame({c: pd.Series(dtype="object") for c in COLUMNAS})
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["valor"] = df["valor"].astype(float)
    return df


def cargar_observaciones(
    ruta: Path | str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Carga las observaciones y sus metadatos.

    Si el archivo no existe o no tiene filas, devuelve una tabla vacía con el esquema
    correcto en lugar de fallar: la interfaz decide cómo informar la ausencia de datos.

    Raises:
        ValueError: si el archivo existe pero le faltan columnas del esquema, porque un
            archivo mal formado debe detectarse y no mostrarse como 'sin datos'.
    """
    ruta = Path(ruta) if ruta else ARCHIVO_OBSERVACIONES
    # Los metadatos viven junto al archivo de datos (mismo directorio).
    ruta_meta = ruta.parent / ARCHIVO_METADATOS.name

    meta: dict = {}
    if ruta_meta.exists():
        meta = json.loads(ruta_meta.read_text(encoding="utf-8"))

    if not ruta.exists():
        return tabla_vacia(), meta

    df = pd.read_csv(ruta, dtype={"cod_estacion": str})
    faltantes = [c for c in COLUMNAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Al archivo {ruta.name} le faltan columnas: {faltantes}")
    if df.empty:
        return tabla_vacia(), meta

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    # Se descartan filas ilegibles o de variables no soportadas: no deben contarse.
    df = df.dropna(subset=["fecha", "valor"])
    df = df[df["variable"].isin(VARIABLES)].reset_index(drop=True)
    return df, meta
