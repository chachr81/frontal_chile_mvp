"""Pruebas de la normalización de regiones."""
import pytest

from frontal.config import REGIONES, normalizar_region


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("De Los Lagos", "Los Lagos"),
        ("Región Metropolitana", "Metropolitana de Santiago"),
        ("VALPARAÍSO", "Valparaíso"),
        ("Región del Libertador General Bernardo O'Higgins", REGIONES[7]),
        ("Ñuble", "Ñuble"),
        ("Bío Bío", "Biobío"),
        ("Magallanes", REGIONES[15]),
    ],
)
def test_normalizar_region_reconoce(texto, esperado):
    assert normalizar_region(texto) == esperado


@pytest.mark.parametrize("texto", [None, "", "Antártica sin región", "xyz"])
def test_normalizar_region_no_reconoce(texto):
    # Un nombre desconocido debe dar None, nunca una región adivinada.
    assert normalizar_region(texto) is None
