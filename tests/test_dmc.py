"""Pruebas del analizador DMC con un GeoJSON SINTÉTICO que sigue los campos documentados."""
from datetime import date

import pytest

from frontal.collectors.dmc import _a_numero, parsear_resumen_diario

HOY = date(2026, 6, 15)


def _feature(**props):
    return {"geometry": {"coordinates": [-71.5, -33.0]}, "properties": props}


def test_a_numero_maneja_coma_de_miles():
    assert _a_numero("1,010.7") == 1010.7
    assert _a_numero(None) is None and _a_numero("") is None and _a_numero("x") is None


def test_parseo_asigna_fechas_y_variables():
    gj = {"features": [_feature(codigoNacional="330020", nombreEstacion="Quinta Normal",
                                region="Región Metropolitana", aguaCaidaAyer="4.5",
                                presion="1,008.2")]}
    df = parsear_resumen_diario(gj, HOY)
    lluvia = df[df["variable"] == "precip_mm"].iloc[0]
    presion = df[df["variable"] == "presion_hpa"].iloc[0]
    assert lluvia["fecha"] == date(2026, 6, 14) and lluvia["valor"] == 4.5
    assert presion["fecha"] == HOY and presion["valor"] == 1008.2
    assert lluvia["region"] == "Metropolitana de Santiago"


def test_valores_ausentes_no_generan_filas():
    gj = {"features": [_feature(codigoNacional="1", nombreEstacion="A", aguaCaidaAyer=None,
                                presion="")]}
    assert parsear_resumen_diario(gj, HOY).empty


def test_region_desde_catalogo_externo():
    gj = {"features": [_feature(codigoNacional="1", nombreEstacion="A", aguaCaidaAyer="1")]}
    df = parsear_resumen_diario(gj, HOY, regiones_por_codigo={"1": "Biobío"})
    assert df.iloc[0]["region"] == "Biobío"


def test_sin_features_falla_con_mensaje():
    with pytest.raises(ValueError, match="vacío"):
        parsear_resumen_diario({"features": []}, HOY)


def test_campo_de_codigo_desconocido_lista_los_campos_reales():
    gj = {"features": [_feature(campoRaro="x", aguaCaidaAyer="1")]}
    with pytest.raises(ValueError, match="campoRaro"):
        parsear_resumen_diario(gj, HOY)
