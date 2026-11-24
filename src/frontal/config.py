"""Configuración central: rutas, constantes del MVP y normalización de regiones.

Todo valor que el equipo pueda querer ajustar (ventana, cobertura mínima, regiones)
vive aquí, para no repartir números mágicos por el código.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

# --- Rutas ---------------------------------------------------------------
# Raíz del repositorio: tres niveles sobre este archivo (src/frontal/config.py).
RAIZ = Path(__file__).resolve().parents[2]
DATOS_CRUDOS = RAIZ / "data" / "raw"
DATOS_PROCESADOS = RAIZ / "data" / "processed"
ARCHIVO_OBSERVACIONES = DATOS_PROCESADOS / "observaciones.csv"
ARCHIVO_METADATOS = DATOS_PROCESADOS / "metadatos.json"

# --- Parámetros del MVP (propuestas del Product Owner, a confirmar en Sprint 1) ---
ZONA_HORARIA = "America/Santiago"
VENTANA_DIAS_DEFECTO = 7      # Días del período mostrado por defecto (HU-02).
VENTANA_DIAS_MIN = 1
VENTANA_DIAS_MAX = 30
COBERTURA_MINIMA = 0.8        # Fracción mínima de días con dato para usar una estación.

# --- Esquema de datos normalizado -----------------------------------------
# Cada fila es UNA observación diaria de UNA variable en UNA estación (formato largo).
COLUMNAS = [
    "fuente",        # 'DMC' o 'DGA'.
    "cod_estacion",  # Código oficial de la estación en su fuente.
    "estacion",      # Nombre de la estación.
    "region",        # Región (nombre canónico, ver REGIONES) o vacío si se desconoce.
    "lat",           # Latitud en grados decimales (EPSG:4326).
    "lon",           # Longitud en grados decimales (EPSG:4326).
    "fecha",         # Día de la observación (YYYY-MM-DD, hora local de Chile).
    "variable",      # Una clave de VARIABLES.
    "valor",         # Valor numérico en la unidad de VARIABLES.
]

# Variables soportadas: clave -> (etiqueta legible, unidad).
VARIABLES = {
    "precip_mm": ("Precipitación diaria", "mm"),
    "presion_hpa": ("Presión reducida a nivel del mar", "hPa"),
    "caudal_m3s": ("Caudal", "m³/s"),
    "nivel_m": ("Nivel del río", "m"),
}

# --- Regiones --------------------------------------------------------------
# Nombres canónicos ordenados de norte a sur.
REGIONES = [
    "Arica y Parinacota",
    "Tarapacá",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaíso",
    "Metropolitana de Santiago",
    "Libertador General Bernardo O'Higgins",
    "Maule",
    "Ñuble",
    "Biobío",
    "La Araucanía",
    "Los Ríos",
    "Los Lagos",
    "Aysén del General Carlos Ibáñez del Campo",
    "Magallanes y de la Antártica Chilena",
]

# Fragmentos (sin tildes, en minúscula) que identifican cada región en textos libres.
_CLAVES_REGION = [
    ("arica", REGIONES[0]),
    ("tarapaca", REGIONES[1]),
    ("antofagasta", REGIONES[2]),
    ("atacama", REGIONES[3]),
    ("coquimbo", REGIONES[4]),
    ("valparaiso", REGIONES[5]),
    ("metropolitana", REGIONES[6]),
    ("higgins", REGIONES[7]),
    ("libertador", REGIONES[7]),
    ("maule", REGIONES[8]),
    ("nuble", REGIONES[9]),
    ("biobio", REGIONES[10]),
    ("bio bio", REGIONES[10]),
    ("araucania", REGIONES[11]),
    ("los rios", REGIONES[12]),
    ("los lagos", REGIONES[13]),
    ("aysen", REGIONES[14]),
    ("magallanes", REGIONES[15]),
]


def _sin_tildes(texto: str) -> str:
    """Devuelve el texto en minúscula y sin tildes ni diacríticos (ñ pasa a n)."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower().strip()


def normalizar_region(texto: str | None) -> str | None:
    """Convierte un nombre de región en texto libre a su nombre canónico.

    Ejemplos: 'De Los Lagos' -> 'Los Lagos'; 'Region Metropolitana' -> 'Metropolitana
    de Santiago'. Devuelve None si el texto está vacío o no se reconoce, de modo que
    la estación se excluya de los cálculos regionales en vez de asignarse por error.
    """
    if not texto:
        return None
    limpio = _sin_tildes(str(texto))
    for clave, canonico in _CLAVES_REGION:
        if clave in limpio:
            return canonico
    return None
