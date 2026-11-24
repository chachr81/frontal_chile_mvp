"""Indicadores del MVP: período, ranking regional, presión mínima e hidrología.

Todas las funciones son puras (reciben y devuelven DataFrames) para poder probarlas sin
interfaz. Cuando no hay datos devuelven tablas vacías: la interfaz las muestra como
estado vacío (HU-04) y nunca como cero.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from frontal.config import COBERTURA_MINIMA

CLAVE_ESTACION = ["fuente", "cod_estacion", "estacion", "region"]


def ultimo_dia_con_datos(df: pd.DataFrame, variable: str = "precip_mm") -> date | None:
    """HU-02: último día con al menos una observación de la variable (None si no hay)."""
    sub = df[df["variable"] == variable]
    if sub.empty:
        return None
    return sub["fecha"].max().date()


def periodo(
    df: pd.DataFrame, dias: int, variable: str = "precip_mm"
) -> tuple[date, date] | None:
    """HU-02: ventana de `dias` días que termina en el último día con datos.

    Devuelve (inicio, fin) inclusivos, o None si no hay datos.
    """
    fin = ultimo_dia_con_datos(df, variable)
    if fin is None:
        return None
    return fin - timedelta(days=dias - 1), fin


def _filtrar(df: pd.DataFrame, variable: str, inicio: date, fin: date) -> pd.DataFrame:
    """Filtra observaciones de una variable dentro de [inicio, fin] (inclusivo)."""
    f = df["fecha"].dt.date
    return df[(df["variable"] == variable) & (f >= inicio) & (f <= fin)]


def acumulado_por_estacion(
    df: pd.DataFrame,
    dias: int,
    cobertura_minima: float = COBERTURA_MINIMA,
) -> pd.DataFrame:
    """Precipitación acumulada por estación en el período, con control de cobertura.

    Una estación solo se usa si tiene datos en al menos `cobertura_minima` de los días
    del período; así una estación con pocos días no subestima artificialmente su región.
    """
    vacio = pd.DataFrame(columns=CLAVE_ESTACION + ["precip_mm", "n_dias", "cobertura"])
    p = periodo(df, dias)
    if p is None:
        return vacio
    sub = _filtrar(df, "precip_mm", *p)
    sub = sub[sub["region"].notna()]
    if sub.empty:
        return vacio
    acum = (
        sub.groupby(CLAVE_ESTACION)
        .agg(precip_mm=("valor", "sum"), n_dias=("fecha", "nunique"))
        .reset_index()
    )
    acum["cobertura"] = acum["n_dias"] / dias
    return acum[acum["cobertura"] >= cobertura_minima].reset_index(drop=True)


def ranking_regiones(
    df: pd.DataFrame,
    dias: int,
    cobertura_minima: float = COBERTURA_MINIMA,
) -> pd.DataFrame:
    """HU-01: ranking de regiones por precipitación acumulada (de mayor a menor).

    Regla de agregación propuesta: media del acumulado de las estaciones de la región
    (evita que una región con más estaciones domine). Se informa además la estación con
    el máximo y el número de estaciones, para que el usuario juzgue la representatividad.
    """
    est = acumulado_por_estacion(df, dias, cobertura_minima)
    columnas = ["region", "precip_media_mm", "precip_max_mm", "estacion_max", "n_estaciones"]
    if est.empty:
        return pd.DataFrame(columns=columnas)
    filas = []
    for region, g in est.groupby("region"):
        top = g.loc[g["precip_mm"].idxmax()]
        filas.append(
            {
                "region": region,
                "precip_media_mm": g["precip_mm"].mean(),
                "precip_max_mm": top["precip_mm"],
                "estacion_max": top["estacion"],
                "n_estaciones": len(g),
            }
        )
    out = pd.DataFrame(filas, columns=columnas)
    return out.sort_values("precip_media_mm", ascending=False).reset_index(drop=True)


def presion_minima_regiones(df: pd.DataFrame, dias: int) -> pd.DataFrame:
    """HU-03: presión mínima observada por región en el período (con estación y día)."""
    columnas = ["region", "presion_min_hpa", "estacion", "fecha"]
    p = periodo(df, dias)
    if p is None:
        return pd.DataFrame(columns=columnas)
    sub = _filtrar(df, "presion_hpa", *p)
    sub = sub[sub["region"].notna()]
    if sub.empty:
        return pd.DataFrame(columns=columnas)
    # Para cada región se toma la fila con el menor valor de presión.
    idx = sub.groupby("region")["valor"].idxmin()
    out = sub.loc[idx, ["region", "valor", "estacion", "fecha"]].rename(
        columns={"valor": "presion_min_hpa"}
    )
    out["fecha"] = out["fecha"].dt.date
    return out.sort_values("presion_min_hpa").reset_index(drop=True)


def hidrologia_region(df: pd.DataFrame, region: str, dias: int) -> pd.DataFrame:
    """HU-05: series diarias de caudal y nivel de las estaciones de una región.

    La ventana termina en el último día con datos de lluvia, para poder comparar
    la respuesta de los ríos con el mismo período del ranking.
    """
    columnas = ["estacion", "variable", "fecha", "valor"]
    p = periodo(df, dias)
    if p is None:
        return pd.DataFrame(columns=columnas)
    f = df["fecha"].dt.date
    sub = df[
        (df["region"] == region)
        & df["variable"].isin(["caudal_m3s", "nivel_m"])
        & (f >= p[0])
        & (f <= p[1])
    ]
    return sub[columnas].sort_values(["variable", "estacion", "fecha"]).reset_index(drop=True)


def resumen_cobertura(df: pd.DataFrame) -> dict:
    """Resumen para el encabezado: fuentes, número de estaciones y rango de fechas."""
    if df.empty:
        return {"fuentes": [], "n_estaciones": 0, "fecha_min": None, "fecha_max": None}
    return {
        "fuentes": sorted(df["fuente"].dropna().unique().tolist()),
        "n_estaciones": df[["fuente", "cod_estacion"]].drop_duplicates().shape[0],
        "fecha_min": df["fecha"].min().date(),
        "fecha_max": df["fecha"].max().date(),
    }
