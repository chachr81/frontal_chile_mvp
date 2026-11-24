"""Pruebas de los indicadores (HU-01, HU-02, HU-03, HU-05 y estados vacíos)."""
from datetime import date

import pandas as pd

from frontal.procesamiento import indicadores as ind
from frontal.procesamiento.cargador import tabla_vacia


def test_periodo_termina_en_ultimo_dia_con_datos(df_prueba):
    inicio, fin = ind.periodo(df_prueba, 7)
    assert fin == date(2026, 6, 15) and (fin - inicio).days == 6


def test_sin_datos_todo_vacio():
    vacio = tabla_vacia()
    assert ind.periodo(vacio, 7) is None
    assert ind.ranking_regiones(vacio, 7).empty
    assert ind.presion_minima_regiones(vacio, 7).empty
    assert ind.hidrologia_region(vacio, "Biobío", 7).empty


def test_ranking_ordenado_y_con_conteo(df_prueba):
    r = ind.ranking_regiones(df_prueba, 7)
    assert r["precip_media_mm"].is_monotonic_decreasing
    # Los datos sintéticos llueven más al sur: Los Lagos debe encabezar.
    assert r.iloc[0]["region"] == "Los Lagos"
    assert r.set_index("region").loc["Biobío", "n_estaciones"] == 3


def test_cobertura_insuficiente_excluye_estacion(df_prueba):
    # Se deja a una estación con solo 2 de 7 días: debe quedar fuera (cobertura < 0,8).
    f = df_prueba["fecha"].dt.date
    quitar = (
        (df_prueba["cod_estacion"] == "S00")
        & (df_prueba["variable"] == "precip_mm")
        & (f < date(2026, 6, 14))
    )
    est = ind.acumulado_por_estacion(df_prueba[~quitar], 7)
    assert "S00" not in set(est["cod_estacion"])


def test_estacion_sin_region_no_entra_al_ranking(df_prueba):
    df = df_prueba.copy()
    df["region"] = None
    assert ind.ranking_regiones(df, 7).empty


def test_presion_minima_es_la_menor_de_cada_region(df_prueba):
    p = ind.presion_minima_regiones(df_prueba, 7)
    esperado = (
        df_prueba[df_prueba["variable"] == "presion_hpa"]
        .query("fecha >= '2026-06-09'")
        .groupby("region")["valor"].min()
    )
    for _, fila in p.iterrows():
        assert fila["presion_min_hpa"] == esperado[fila["region"]]


def test_hidrologia_devuelve_caudal_y_nivel(df_prueba):
    s = ind.hidrologia_region(df_prueba, "Biobío", 7)
    assert set(s["variable"]) == {"caudal_m3s", "nivel_m"}
    assert s["fecha"].nunique() == 7


def test_hidrologia_region_sin_serie_es_vacia(df_prueba):
    df = df_prueba[~df_prueba["variable"].isin(["caudal_m3s", "nivel_m"])]
    assert ind.hidrologia_region(df, "Biobío", 7).empty


def test_resumen_cobertura(df_prueba):
    r = ind.resumen_cobertura(df_prueba)
    assert r["fuentes"] == ["DGA", "DMC"] and isinstance(r["fecha_max"], date)
    assert ind.resumen_cobertura(pd.DataFrame())["n_estaciones"] == 0
