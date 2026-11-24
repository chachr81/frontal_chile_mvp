"""Visor mínimo público (MVP): pantalla comparativa del impacto de un sistema frontal.

Ejecutar con:  streamlit run src/frontal/app/streamlit_app.py

Cubre HU-01 (ranking), HU-02 (período automático), HU-03 (presión mínima),
HU-04 (estados vacío, de carga y de error) y HU-05 (caudal y nivel de ríos).
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from frontal.app.graficos import grafico_hidrologia, grafico_presion, grafico_ranking
from frontal.config import (
    ARCHIVO_OBSERVACIONES,
    VENTANA_DIAS_DEFECTO,
    VENTANA_DIAS_MAX,
    VENTANA_DIAS_MIN,
)
from frontal.procesamiento.cargador import cargar_observaciones
from frontal.procesamiento.indicadores import (
    hidrologia_region,
    periodo,
    presion_minima_regiones,
    ranking_regiones,
    resumen_cobertura,
)

# La ruta de datos puede sustituirse con una variable de entorno (útil en pruebas).
RUTA_DATOS = Path(os.environ.get("FRONTAL_DATOS", ARCHIVO_OBSERVACIONES))


@st.cache_data(show_spinner="Cargando observaciones...")
def _cargar(ruta: str, marca_tiempo: float):
    """Carga con caché; `marca_tiempo` invalida la caché cuando el archivo cambia."""
    return cargar_observaciones(ruta)


def _estado_vacio(mensaje: str) -> None:
    """HU-04: mensaje explícito cuando no hay datos, para no interpretar un blanco como cero."""
    st.info(f"Sin datos: {mensaje}")


def _encabezado(df: pd.DataFrame, meta: dict, dias: int) -> None:
    """HU-02: muestra el período calculado automáticamente y la fuente de los datos."""
    cobertura = resumen_cobertura(df)
    p = periodo(df, dias)
    if p is None:
        _estado_vacio("no hay observaciones de precipitación para calcular el período.")
    else:
        st.markdown(
            f"**Período:** {p[0]:%d-%m-%Y} a {p[1]:%d-%m-%Y} ({dias} días, hasta el último "
            f"día con datos)."
        )
    fuentes = ", ".join(cobertura["fuentes"]) or "sin fuente cargada"
    cita = meta.get("cita", "Cite a la institución que publica cada dato.")
    descarga = meta.get("actualizado_utc", "fecha de descarga no registrada")
    st.caption(
        f"Fuente: {fuentes} ({cobertura['n_estaciones']} estaciones). {cita} "
        f"Última actualización: {descarga}. Datos provisorios, sujetos a modificación."
    )


def main() -> None:
    """Construye la pantalla comparativa."""
    st.set_page_config(page_title="Frontal Chile", layout="wide")
    st.title("Frontal Chile: impacto observado de un sistema frontal")
    st.write("Compare regiones con datos observados de estaciones públicas.")

    # HU-04 (error): cualquier falla de lectura se informa; la app no se cae.
    try:
        marca = RUTA_DATOS.stat().st_mtime if RUTA_DATOS.exists() else 0.0
        df, meta = _cargar(str(RUTA_DATOS), marca)
    except Exception as exc:  # noqa: BLE001  (se informa al usuario, no se oculta)
        st.error(f"No se pudieron leer los datos: {exc}")
        return

    if meta.get("sintetico"):
        st.warning(
            "DATOS SINTÉTICOS DE PRUEBA: no corresponden a observaciones reales y no "
            "deben usarse para análisis ni para evidencia de la entrega."
        )

    dias = st.sidebar.slider(
        "Días del período", VENTANA_DIAS_MIN, VENTANA_DIAS_MAX, VENTANA_DIAS_DEFECTO
    )
    _encabezado(df, meta, dias)

    # --- HU-01: ranking ---------------------------------------------------
    st.subheader("1. Ranking de regiones por precipitación acumulada")
    ranking = ranking_regiones(df, dias)
    if ranking.empty:
        _estado_vacio("ninguna región tiene estaciones con cobertura suficiente en el período.")
    else:
        st.pyplot(grafico_ranking(ranking))
        st.dataframe(
            ranking.rename(
                columns={
                    "region": "Región",
                    "precip_media_mm": "Media (mm)",
                    "precip_max_mm": "Máximo (mm)",
                    "estacion_max": "Estación con el máximo",
                    "n_estaciones": "N.º de estaciones",
                }
            ).round(1),
            hide_index=True,
        )

    # --- HU-03: presión mínima ---------------------------------------------
    st.subheader("2. Presión mínima por región")
    presion = presion_minima_regiones(df, dias)
    if presion.empty:
        _estado_vacio("no hay observaciones de presión en el período.")
    else:
        st.pyplot(grafico_presion(presion))

    # --- HU-05: caudal y nivel -----------------------------------------------
    st.subheader("3. Caudal y nivel de ríos de la región")
    regiones = sorted(df["region"].dropna().unique().tolist())
    if not regiones:
        _estado_vacio("no hay regiones con datos para consultar.")
        return
    region = st.selectbox("Región", regiones)
    serie = hidrologia_region(df, region, dias)
    if serie.empty:
        _estado_vacio(
            f"la región {region} no tiene caudal ni nivel en el período; una serie vacía "
            "no equivale a caudal cero."
        )
    else:
        st.pyplot(grafico_hidrologia(serie))


main()
