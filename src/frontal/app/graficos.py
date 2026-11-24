"""Gráficos del visor, construidos con seaborn sobre matplotlib.

Cada función recibe una tabla ya calculada (ver procesamiento.indicadores) y devuelve una
figura de matplotlib que Streamlit puede mostrar con st.pyplot. No calculan indicadores.
"""
from __future__ import annotations

import matplotlib

# Backend sin ventana: necesario para servidores y pruebas automáticas.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (se importa tras fijar el backend)
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from frontal.config import VARIABLES  # noqa: E402

# Paleta apta para daltonismo, para no depender solo del color (criterio de la DoD).
_COLOR = sns.color_palette("colorblind")[0]


def _estilo() -> None:
    """Aplica un estilo sobrio y legible a todos los gráficos."""
    sns.set_theme(style="whitegrid", context="notebook", palette="colorblind")


def grafico_ranking(ranking: pd.DataFrame) -> Figure:
    """HU-01: barras horizontales de precipitación media por región, de mayor a menor."""
    _estilo()
    alto = max(2.5, 0.45 * len(ranking) + 1.2)  # Altura proporcional al número de regiones.
    fig, ax = plt.subplots(figsize=(8, alto))
    sns.barplot(data=ranking, y="region", x="precip_media_mm", color=_COLOR, ax=ax)
    # Se rotula el valor en cada barra para no depender de leer el eje.
    for contenedor in ax.containers:
        ax.bar_label(contenedor, fmt="%.1f", padding=3)
    ax.set_xlabel("Precipitación media acumulada de las estaciones de la región (mm)")
    ax.set_ylabel("")
    ax.set_title("Regiones ordenadas por precipitación acumulada en el período")
    fig.tight_layout()
    return fig


def grafico_presion(presion: pd.DataFrame) -> Figure:
    """HU-03: presión mínima por región (la más baja arriba, señal de paso de un frente)."""
    _estilo()
    alto = max(2.5, 0.45 * len(presion) + 1.2)
    fig, ax = plt.subplots(figsize=(8, alto))
    sns.scatterplot(
        data=presion, y="region", x="presion_min_hpa", s=90, color=_COLOR, ax=ax
    )
    ax.invert_yaxis()  # La región con la presión más baja queda arriba.
    ax.set_xlabel("Presión mínima observada en el período (hPa)")
    ax.set_ylabel("")
    ax.set_title("Presión mínima por región")
    fig.tight_layout()
    return fig


def grafico_hidrologia(serie: pd.DataFrame) -> Figure:
    """HU-05: una columna de gráficos por variable (caudal y nivel), una línea por estación."""
    _estilo()
    variables = [v for v in ("caudal_m3s", "nivel_m") if v in set(serie["variable"])]
    fig, ejes = plt.subplots(
        1, len(variables), figsize=(6 * len(variables), 4), squeeze=False
    )
    for ax, var in zip(ejes[0], variables):
        sub = serie[serie["variable"] == var]
        # Marcadores y estilos de línea distintos: la lectura no depende solo del color.
        sns.lineplot(
            data=sub, x="fecha", y="valor", hue="estacion", style="estacion",
            markers=True, dashes=True, ax=ax,
        )
        etiqueta, unidad = VARIABLES[var]
        ax.set_title(etiqueta)
        ax.set_ylabel(f"{etiqueta} ({unidad})")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(fontsize="small", title="")
    fig.tight_layout()
    return fig
