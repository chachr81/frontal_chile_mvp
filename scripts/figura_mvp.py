"""Genera la figura estática del MVP a partir de las observaciones reales de data/processed.

Uso:
  python scripts/figura_mvp.py                 # escribe docs/figuras/mvp_metropolitana.png

La figura combina dos indicadores del MVP para la región piloto:
  (A) precipitación acumulada de los últimos 7 días por estación (HU-01, nivel estación);
  (B) caudal medio diario de las estaciones fluviométricas con mejor cobertura (HU-05).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Backend sin ventana: permite generar la figura en servidores.
import matplotlib.pyplot as plt
import seaborn as sns

from frontal.config import RAIZ
from frontal.procesamiento import indicadores as ind
from frontal.procesamiento.cargador import cargar_observaciones

DIAS_PRECIP = 7        # Ventana del indicador de precipitación (HU-01).
DIAS_CAUDAL = 30       # Ventana de las series de caudal (HU-05).
N_ESTACIONES = 10      # Estaciones mostradas en el panel A.
N_RIOS = 5             # Series de caudal mostradas en el panel B.


def construir_figura(df) -> plt.Figure:
    """Arma la figura de dos paneles con seaborn a partir del DataFrame de observaciones."""
    sns.set_theme(style="whitegrid", context="notebook", palette="colorblind")
    fin = ind.ultimo_dia_con_datos(df)

    # Panel A: acumulado de precipitación por estación (con control de cobertura >= 80 %).
    acum = ind.acumulado_por_estacion(df, DIAS_PRECIP).nlargest(N_ESTACIONES, "precip_mm")

    # Panel B: caudal diario de las estaciones con más días de dato en la ventana.
    region = df["region"].dropna().iloc[0]
    serie = ind.hidrologia_region(df, region, DIAS_CAUDAL)
    caudal = serie[serie["variable"] == "caudal_m3s"]
    top = caudal.groupby("estacion")["fecha"].nunique().nlargest(N_RIOS).index
    caudal = caudal[caudal["estacion"].isin(top)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1, 1.25]})
    if acum.empty:
        ax1.text(0.5, 0.5, "Sin estaciones con cobertura suficiente", ha="center", va="center")
        ax1.set_axis_off()
    else:
        sns.barplot(data=acum, y="estacion", x="precip_mm", color=sns.color_palette()[0], ax=ax1)
        ax1.set_xlabel(f"Precipitación acumulada, {DIAS_PRECIP} días (mm)")
        ax1.set_ylabel("")
    ax1.set_title("A. Precipitación por estación")

    if caudal.empty:
        ax2.text(0.5, 0.5, "Sin series de caudal", ha="center", va="center")
        ax2.set_axis_off()
    else:
        sns.lineplot(data=caudal, x="fecha", y="valor", hue="estacion", ax=ax2)
        ax2.set_xlabel("Fecha")
        ax2.set_ylabel("Caudal medio diario (m³/s)")
        ax2.legend(title="", fontsize=7, loc="upper left")
        ax2.tick_params(axis="x", rotation=30)
    ax2.set_title("B. Caudal diario, últimos 30 días")

    fig.suptitle(f"Región {region}: observaciones reales DGA al {fin:%d-%m-%Y}", fontsize=13)
    fig.tight_layout()
    return fig


def main() -> None:
    """Carga los datos reales y guarda la figura como PNG."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, default=RAIZ / "docs" / "figuras" / "mvp_metropolitana.png")
    args = parser.parse_args()
    df, meta = cargar_observaciones()
    if df.empty or meta.get("sintetico"):
        raise SystemExit("No hay observaciones reales en data/processed; ejecute scripts/collect.py primero.")
    fig = construir_figura(df)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=200)
    print(f"Figura guardada en {args.salida}")


if __name__ == "__main__":
    main()
