"""Generador de datos SINTÉTICOS para pruebas y desarrollo de la interfaz.

Estos datos NO son observaciones reales. El archivo de metadatos que se escribe lleva
`sintetico: true`, y la aplicación muestra una advertencia permanente cuando lo detecta.
Nunca deben usarse como evidencia ni en capturas de la entrega.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from frontal.config import COLUMNAS


def generar_observaciones(fin: date = date(2026, 6, 15), dias: int = 14, semilla: int = 7):
    """Devuelve un DataFrame sintético con precipitación, presión, caudal y nivel."""
    rng = np.random.default_rng(semilla)  # Semilla fija: resultados reproducibles.
    regiones = {
        "Valparaíso": ["Estación V1", "Estación V2", "Estación V3"],
        "Metropolitana de Santiago": ["Estación M1", "Estación M2"],
        "Biobío": ["Estación B1", "Estación B2", "Estación B3"],
        "Los Lagos": ["Estación L1", "Estación L2"],
    }
    filas = []
    for k, (region, estaciones) in enumerate(regiones.items()):
        for j, nombre in enumerate(estaciones):
            cod = f"S{k}{j}"
            base = {
                "fuente": "DMC", "cod_estacion": cod, "estacion": nombre,
                "region": region, "lat": -33.0 - 3 * k, "lon": -71.0 - 0.1 * j,
            }
            for d in range(dias):
                dia = fin - timedelta(days=dias - 1 - d)
                # Más lluvia hacia el sur y un pulso frontal en los últimos días.
                lluvia = max(0.0, rng.normal(2 + 3 * k, 1.5) + (8 * k if d >= dias - 3 else 0))
                presion = 1015 - 4 * k - (6 if d >= dias - 3 else 0) + rng.normal(0, 0.8)
                filas.append({**base, "fecha": dia, "variable": "precip_mm", "valor": lluvia})
                filas.append({**base, "fecha": dia, "variable": "presion_hpa", "valor": presion})
                if j == 0:  # Una estación fluviométrica por región.
                    filas.append({**base, "fuente": "DGA", "fecha": dia,
                                  "variable": "caudal_m3s", "valor": 10 + k + lluvia * 0.8})
                    filas.append({**base, "fuente": "DGA", "fecha": dia,
                                  "variable": "nivel_m", "valor": 1 + 0.05 * lluvia})
    return pd.DataFrame(filas, columns=COLUMNAS)


def escribir_datos_prueba(directorio: Path | str) -> Path:
    """Escribe observaciones.csv y metadatos.json sintéticos; devuelve la ruta del CSV."""
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / "observaciones.csv"
    generar_observaciones().to_csv(ruta, index=False)
    (directorio / "metadatos.json").write_text(
        json.dumps({"sintetico": True, "cita": "Datos sintéticos de prueba."}, ensure_ascii=False),
        encoding="utf-8",
    )
    return ruta
