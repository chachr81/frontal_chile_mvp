"""Almacenamiento: fusiona observaciones nuevas con las ya guardadas y escribe metadatos."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from frontal.config import ARCHIVO_OBSERVACIONES, COLUMNAS

# Una observación se identifica por estación, día y variable (no se duplica).
CLAVE_UNICA = ["fuente", "cod_estacion", "fecha", "variable"]


def actualizar_observaciones(
    nuevas: pd.DataFrame,
    citas: dict[str, str],
    ruta: Path | str | None = None,
) -> pd.DataFrame:
    """Agrega `nuevas` al archivo de observaciones y actualiza los metadatos.

    Si una observación ya existía, se conserva la más reciente (las lecturas provisorias
    pueden corregirse). Escribe `metadatos.json` junto al archivo con las citas de cada
    fuente y la fecha de actualización en UTC.

    Raises:
        ValueError: si el archivo existente es de datos sintéticos, para impedir mezclar
            datos de prueba con observaciones reales.
    """
    ruta = Path(ruta) if ruta else ARCHIVO_OBSERVACIONES
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta_meta = ruta.parent / "metadatos.json"

    meta: dict = {}
    if ruta_meta.exists():
        meta = json.loads(ruta_meta.read_text(encoding="utf-8"))
    if meta.get("sintetico"):
        raise ValueError(
            f"{ruta} contiene datos sintéticos; use otra ruta o bórrelos antes de cargar "
            "observaciones reales."
        )

    previas = pd.read_csv(ruta, dtype={"cod_estacion": str}) if ruta.exists() else None
    juntas = pd.concat([previas, nuevas], ignore_index=True) if previas is not None else nuevas
    juntas = juntas[COLUMNAS].copy()
    # Se uniformiza el formato de fecha antes de eliminar duplicados.
    juntas["fecha"] = pd.to_datetime(juntas["fecha"]).dt.strftime("%Y-%m-%d")
    juntas = (
        juntas.drop_duplicates(subset=CLAVE_UNICA, keep="last")
        .sort_values(["fuente", "cod_estacion", "variable", "fecha"])
        .reset_index(drop=True)
    )
    juntas.to_csv(ruta, index=False)

    meta["actualizado_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta["citas"] = {**meta.get("citas", {}), **citas}
    meta["cita"] = " ".join(meta["citas"].values())
    meta["sintetico"] = False
    ruta_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return juntas
