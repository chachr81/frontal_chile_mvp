"""Fixtures compartidas: datos SINTÉTICOS escritos en un directorio temporal."""
import pytest

from frontal.datos_prueba import escribir_datos_prueba
from frontal.procesamiento.cargador import cargar_observaciones


@pytest.fixture()
def ruta_prueba(tmp_path):
    """Ruta a un observaciones.csv sintético (con metadatos 'sintetico')."""
    return escribir_datos_prueba(tmp_path)


@pytest.fixture()
def df_prueba(ruta_prueba):
    """DataFrame cargado desde los datos sintéticos."""
    df, _ = cargar_observaciones(ruta_prueba)
    return df
