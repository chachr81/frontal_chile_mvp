"""Pruebas de carga: archivo ausente, vacío, mal formado y válido."""
import pytest

from frontal.config import COLUMNAS
from frontal.procesamiento.cargador import cargar_observaciones


def test_archivo_ausente_da_tabla_vacia(tmp_path):
    df, meta = cargar_observaciones(tmp_path / "no_existe.csv")
    assert df.empty and list(df.columns) == COLUMNAS and meta == {}


def test_archivo_sin_filas_da_tabla_vacia(tmp_path):
    ruta = tmp_path / "observaciones.csv"
    ruta.write_text(",".join(COLUMNAS) + "\n", encoding="utf-8")
    df, _ = cargar_observaciones(ruta)
    assert df.empty


def test_archivo_mal_formado_falla(tmp_path):
    ruta = tmp_path / "observaciones.csv"
    ruta.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cargar_observaciones(ruta)


def test_archivo_valido_marca_sintetico(ruta_prueba):
    df, meta = cargar_observaciones(ruta_prueba)
    assert not df.empty and meta["sintetico"] is True
