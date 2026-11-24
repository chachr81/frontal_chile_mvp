"""Pruebas de la interfaz: gráficos y ejecución completa de la app con AppTest."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from frontal.app.graficos import grafico_hidrologia, grafico_presion, grafico_ranking
from frontal.procesamiento import indicadores as ind

APP = Path(__file__).resolve().parents[1] / "src" / "frontal" / "app" / "streamlit_app.py"


def test_graficos_se_construyen(df_prueba):
    assert grafico_ranking(ind.ranking_regiones(df_prueba, 7)) is not None
    assert grafico_presion(ind.presion_minima_regiones(df_prueba, 7)) is not None
    assert grafico_hidrologia(ind.hidrologia_region(df_prueba, "Biobío", 7)) is not None


def test_app_con_datos_muestra_periodo_y_advertencia_sintetica(ruta_prueba, monkeypatch):
    monkeypatch.setenv("FRONTAL_DATOS", str(ruta_prueba))
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("SINTÉTICOS" in w.value for w in at.warning)
    assert any("Período:" in m.value for m in at.markdown)


def test_app_sin_archivo_muestra_estado_vacio(tmp_path, monkeypatch):
    monkeypatch.setenv("FRONTAL_DATOS", str(tmp_path / "no_existe.csv"))
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("Sin datos" in i.value for i in at.info)


def test_app_con_archivo_corrupto_muestra_error(tmp_path, monkeypatch):
    ruta = tmp_path / "observaciones.csv"
    ruta.write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setenv("FRONTAL_DATOS", str(ruta))
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert any("No se pudieron leer" in e.value for e in at.error)
