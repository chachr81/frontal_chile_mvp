"""Pruebas del importador DGA y del almacenamiento (datos de prueba sintéticos)."""
import json

import pandas as pd
import pytest

from frontal.collectors.almacen import actualizar_observaciones
from frontal.collectors.dga_csv import importar_csv_dga
from frontal.config import COLUMNAS

CSV = (
    "cod_bna;nombre;region;lat;lon;fecha_hora;precipitacion_mm;caudal_m3s;nivel_m\n"
    "123;Río Prueba;Biobío;-37,0;-72,0;2026-06-14 00:00;1,0;10,0;1,0\n"
    "123;Río Prueba;Biobío;-37,0;-72,0;2026-06-14 12:00;2,0;20,0;2,0\n"
    "123;Río Prueba;Biobío;-37,0;-72,0;2026-06-15 00:00;0,5;30,0;3,0\n"
)


def test_importar_agrega_por_dia(tmp_path):
    ruta = tmp_path / "dga.csv"
    ruta.write_text(CSV, encoding="utf-8")
    df = importar_csv_dga(ruta)
    assert list(df.columns) == COLUMNAS
    dia = df[df["fecha"] == pd.Timestamp("2026-06-14")].set_index("variable")["valor"]
    assert dia["precip_mm"] == 3.0       # se suma
    assert dia["caudal_m3s"] == 15.0     # se promedia
    assert (df["fuente"] == "DGA").all() and (df["region"] == "Biobío").all()


def test_importar_sin_columnas_falla(tmp_path):
    ruta = tmp_path / "malo.csv"
    ruta.write_text("a;b\n1;2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        importar_csv_dga(ruta)


def test_almacen_deduplica_y_escribe_metadatos(tmp_path):
    ruta = tmp_path / "observaciones.csv"
    base = {"fuente": "DMC", "cod_estacion": "1", "estacion": "A", "region": "Biobío",
            "lat": 0, "lon": 0, "fecha": "2026-06-14", "variable": "precip_mm"}
    actualizar_observaciones(pd.DataFrame([{**base, "valor": 1.0}]), {"DMC": "cita"}, ruta)
    total = actualizar_observaciones(pd.DataFrame([{**base, "valor": 2.0}]), {"DMC": "cita"}, ruta)
    assert len(total) == 1 and total.iloc[0]["valor"] == 2.0   # se conserva la última lectura
    meta = json.loads((tmp_path / "metadatos.json").read_text(encoding="utf-8"))
    assert meta["sintetico"] is False and "cita" in meta["cita"]


def test_almacen_rechaza_mezclar_con_sinteticos(ruta_prueba):
    with pytest.raises(ValueError, match="sintéticos"):
        actualizar_observaciones(pd.DataFrame(columns=COLUMNAS), {}, ruta_prueba)
