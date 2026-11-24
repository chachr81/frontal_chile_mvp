"""Escribe datos SINTÉTICOS de prueba en el directorio indicado (no en data/processed).

Uso:  python scripts/generar_datos_prueba.py ruta/carpeta
Luego: set FRONTAL_DATOS=ruta/carpeta/observaciones.csv  y ejecute el visor.
"""
import sys

from frontal.datos_prueba import escribir_datos_prueba

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
print("Escrito:", escribir_datos_prueba(sys.argv[1]))
