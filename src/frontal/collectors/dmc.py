"""Cliente del servicio GeoJSON 'Resumen diario de la red de estaciones automáticas' (DMC).

Fuente: Dirección Meteorológica de Chile, portal https://climatologia.meteochile.gob.cl
El portal declara los datos de acceso y uso público y solicita citar a la DMC como fuente.
El servicio exige un usuario (correo) y un token personal.

ESTADO DE VERIFICACIÓN (ver docs/fuentes_datos.md):
  - Verificado en la documentación oficial: la URL, los parámetros `usuario` y `token`, y
    los campos `aguaCaidaAyer`, `aguaCaidaAyerDatos` y `presion`.
  - NO verificado: los nombres de los campos de código, nombre y región de la estación.
    El analizador prueba nombres candidatos y, si no encuentra ninguno, falla con la lista
    de campos reales para ajustarlos tras la primera descarga (`collect.py dmc --inspect`).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import requests

from frontal.config import COLUMNAS, normalizar_region

URL_RESUMEN_DIARIO = (
    "https://climatologia.meteochile.gob.cl/application/geoservicios/getEmaResumenDiarioGeo"
)
CITA_DMC = "Fuente: Dirección Meteorológica de Chile (DMC), datos de acceso y uso público."

# Nombres candidatos (NO verificados) para los campos de identificación de la estación.
CAMPOS_CODIGO = ("codigoNacional", "codigo", "codNacional", "idEstacion", "id")
CAMPOS_NOMBRE = ("nombreEstacion", "nombre", "estacion", "nombreEma")
CAMPOS_REGION = ("region", "nombreRegion", "regionNombre")


def descargar_resumen_diario(usuario: str, token: str, timeout: int = 60) -> dict:
    """Descarga el GeoJSON del resumen diario.

    Raises:
        requests.HTTPError: si el servicio responde con error (p. ej. credenciales inválidas).
    """
    respuesta = requests.get(
        URL_RESUMEN_DIARIO,
        params={"usuario": usuario, "token": token},
        timeout=timeout,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def _a_numero(valor: Any) -> float | None:
    """Convierte un valor del servicio a float; devuelve None si no es un número válido.

    La documentación muestra la presión como texto con coma de miles ('1,010.7'), por lo
    que se eliminan las comas antes de convertir.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace(",", "")
    if texto in ("", "-", "null", "None"):
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _primer_campo(props: dict, candidatos: tuple[str, ...]) -> Any:
    """Devuelve el valor del primer campo candidato presente en `props` (o None)."""
    for nombre in candidatos:
        if nombre in props and props[nombre] not in (None, ""):
            return props[nombre]
    return None


def parsear_resumen_diario(
    geojson: dict,
    fecha_descarga: date,
    regiones_por_codigo: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Convierte el GeoJSON en filas del esquema normalizado.

    Reglas:
      - `aguaCaidaAyer` se asigna al día anterior a la descarga (es el total de 'ayer').
      - `presion` es el valor del momento de la descarga y se asigna al día de descarga;
        por ello la 'presión mínima' del MVP es el mínimo de las lecturas diarias
        guardadas, no el mínimo instantáneo real del día.
      - Si el servicio no entrega región, se usa `regiones_por_codigo` (catálogo oficial);
        sin región la estación queda fuera de los cálculos regionales.

    Raises:
        ValueError: si el GeoJSON no trae estaciones o no se reconoce el campo de código.
    """
    features = geojson.get("features") or []
    if not features:
        raise ValueError("El GeoJSON de la DMC no contiene estaciones (features vacío).")

    ayer = fecha_descarga - timedelta(days=1)
    filas: list[dict] = []
    for f in features:
        props = f.get("properties") or {}
        codigo = _primer_campo(props, CAMPOS_CODIGO)
        if codigo is None:
            # Se informa con los campos reales para que el equipo ajuste los candidatos.
            raise ValueError(
                "No se reconoce el campo de código de estación. Campos presentes: "
                f"{sorted(props)}. Ajuste CAMPOS_CODIGO en collectors/dmc.py."
            )
        codigo = str(codigo)
        nombre = _primer_campo(props, CAMPOS_NOMBRE) or codigo
        region = normalizar_region(_primer_campo(props, CAMPOS_REGION))
        if region is None and regiones_por_codigo:
            region = normalizar_region(regiones_por_codigo.get(codigo))
        coords = (f.get("geometry") or {}).get("coordinates") or [None, None]
        base = {
            "fuente": "DMC",
            "cod_estacion": codigo,
            "estacion": str(nombre),
            "region": region,
            "lon": coords[0],
            "lat": coords[1],
        }
        lluvia = _a_numero(props.get("aguaCaidaAyer"))
        if lluvia is not None:
            filas.append({**base, "fecha": ayer, "variable": "precip_mm", "valor": lluvia})
        presion = _a_numero(props.get("presion"))
        if presion is not None:
            filas.append(
                {**base, "fecha": fecha_descarga, "variable": "presion_hpa", "valor": presion}
            )
    return pd.DataFrame(filas, columns=COLUMNAS)
