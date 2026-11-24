"""Colector de la DGA: valores sinópticos diarios del sistema DGASAT.

El catálogo de estaciones (código BNA, nombre, región y coordenadas) se obtiene del servidor MCP
"Red de Monitoreo Chile" y se guarda en `data/catalogo/dga_estaciones.json`. Las series de tiempo
NO las entrega el MCP: su protocolo indica consultarlas directamente en el portal DGASAT
(https://snia.mop.gob.cl/dgasat), que no requiere credenciales pero sí:
  - un User-Agent de navegador (el WAF rechaza los de librerías),
  - una sesión con cookie,
  - un pacing entre solicitudes (el portal se satura bajo carga).

Flujo por estación (el mismo que describe el protocolo del MCP):
  1. GET  dgasat_param.jsp?param=1            -> crea la sesión.
  2. POST dgasat_param_1.jsp (accion=refresca) -> parámetros disponibles de la estación.
  3. POST dgasat_param_tablas.jsp (tiporep=S)  -> tabla sinóptica diaria (mínimo, máximo y media).

SUPUESTOS A VERIFICAR (documentados en docs/fuentes_datos.md):
  - La precipitación diaria se deriva del contador "Pptación Acum." como el máximo del día menos
    el máximo del día anterior; los valores negativos (reinicio del contador) se descartan.
  - Caudal y nivel se informan con la media diaria que entrega el portal.
  - La presión atmosférica de la DGA es presión de estación (mb), no reducida a nivel del mar;
    por eso NO se incorpora al MVP.
  - Los códigos de dato faltante del portal (p. ej. -99999) se descartan.
  - Las fechas están en hora local de Chile y los datos son provisorios.
"""
from __future__ import annotations

import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

from frontal.config import COLUMNAS, normalizar_region

CITA_DGA = "Fuente: Dirección General de Aguas (DGA), sistema DGASAT; datos provisorios no validados."

URL_BASE = "https://snia.mop.gob.cl/dgasat/pages/dgasat_param"
# El WAF de la DGA rechaza los User-Agent de librerías; se usa el de un navegador común.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
PAUSA_SEGUNDOS = 0.7   # Pacing entre solicitudes para no saturar el portal.
TIMEOUT_SEGUNDOS = 90

# Parámetro del portal (texto normalizado) -> variable del esquema común.
# Se evalúa en orden; el primer patrón que calza gana.
PATRONES_PARAMETRO = [
    ("precip_acum", re.compile(r"pptacion acum\.")),
    ("caudal_m3s", re.compile(r"^caudal")),
    ("nivel_m", re.compile(r"^nivel de agua")),
    # La presión atmosférica de la DGA es presión de ESTACIÓN (no reducida a nivel del mar) y
    # las estaciones están a altitudes muy distintas (p. ej. 789 a 960 hPa en la región), por
    # lo que no es comparable entre estaciones: se excluye del MVP (HU-03 depende de la DMC).
]
# Código con que el portal marca un dato faltante (p. ej. -99999 en nivel de agua).
VALOR_FALTANTE_MAXIMO = -9990

_FILA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_CELDA = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)


def _normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples (para comparar nombres de parámetros)."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


def _limpiar(html_celda: str) -> str:
    """Quita etiquetas HTML y espacios sobrantes de una celda."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_celda)).replace("&nbsp;", " ").strip()


def abrir_sesion() -> requests.Session:
    """Crea la sesión con cookie y User-Agent de navegador que exige el portal."""
    sesion = requests.Session()
    sesion.headers["User-Agent"] = USER_AGENT
    sesion.get(f"{URL_BASE}/dgasat_param.jsp?param=1", timeout=TIMEOUT_SEGUNDOS).raise_for_status()
    return sesion


def _decodificar(respuesta: requests.Response) -> str:
    """El portal declara windows-1252 pero responde en UTF-8; se decodifica como UTF-8."""
    return respuesta.content.decode("utf-8", errors="replace")


def parametros_estacion(sesion: requests.Session, cod_bna: str) -> dict[str, str]:
    """Devuelve {variable_normalizada: valor_del_checkbox} de los parámetros que usa el MVP."""
    resp = sesion.post(
        f"{URL_BASE}/dgasat_param_1.jsp",
        data={
            "accion": "refresca", "estacion1": cod_bna, "estacion2": "-1", "estacion3": "-1",
            "EsDL1": "0", "param": "1",
        },
        timeout=TIMEOUT_SEGUNDOS,
    )
    resp.raise_for_status()
    valores = re.findall(r'name="parametros"\s+value="([^"]+)"', _decodificar(resp))
    elegidos: dict[str, str] = {}
    for valor in valores:
        # Formato del valor: <cod_bna>_<id_parametro>_<nombre (unidad)>.
        nombre = _normalizar(valor.split("_", 2)[-1])
        for variable, patron in PATRONES_PARAMETRO:
            if patron.search(nombre) and variable not in elegidos:
                elegidos[variable] = valor
    return elegidos


def descargar_sinoptico(
    sesion: requests.Session, cod_bna: str, parametros: list[str], inicio: date, fin: date
) -> str:
    """Descarga el HTML de la tabla sinóptica diaria de una estación para [inicio, fin]."""
    datos: list[tuple[str, str]] = [
        ("accion", "tabla"), ("param", "1"), ("tipo", "ANO"), ("estacion1", cod_bna),
        ("estacion2", "-1"), ("estacion3", "-1"), ("EsDL1", "0"), ("tiporep", "S"),
        ("period", "rango"), ("fechaInicioTabla", f"{inicio:%d/%m/%Y}"),
        ("fechaFinTabla", f"{fin:%d/%m/%Y}"), ("fechaFinGrafico", f"{fin:%d/%m/%Y}"),
        ("hora_fin", "0"), ("UserID", "nobody"),
    ] + [("parametros", p) for p in parametros]
    resp = sesion.post(f"{URL_BASE}/dgasat_param_tablas.jsp", data=datos, timeout=TIMEOUT_SEGUNDOS)
    resp.raise_for_status()
    return _decodificar(resp)


def parsear_sinoptico(html: str) -> pd.DataFrame:
    """Convierte la tabla sinóptica en un DataFrame con una columna por parámetro y estadístico.

    Las columnas se llaman '<parametro normalizado>|<min|max|media>'; el índice es la fecha.
    Devuelve una tabla vacía si el portal no entregó filas.
    """
    filas = _FILA.findall(html)
    encabezados: list[str] = []
    datos: list[list[str]] = []
    for fila in filas:
        celdas = [_limpiar(c) for c in _CELDA.findall(fila)]
        if len(celdas) >= 3 and celdas[0] == "Nro.":
            encabezados = celdas[2:]
        elif len(celdas) >= 3 and re.fullmatch(r"\d{2}/\d{2}/\d{4}", celdas[1] or ""):
            datos.append(celdas[1:])
    if not encabezados or not datos:
        return pd.DataFrame()

    nombres = []
    for enc in encabezados:
        # El encabezado es '<estación> <parámetro> (unidad)<Min|Max|Media>'.
        m = re.search(r"\)(Min|Max|Media)$", enc)
        estadistico = m.group(1).lower() if m else "valor"
        nombres.append(f"{_normalizar(re.sub(r'(Min|Max|Media)$', '', enc))}|{estadistico}")
    tabla = pd.DataFrame(
        [fila[1:1 + len(nombres)] + [None] * (len(nombres) - len(fila[1:])) for fila in datos],
        columns=nombres,
    )
    tabla.index = pd.to_datetime([fila[0] for fila in datos], format="%d/%m/%Y")
    tabla.index.name = "fecha"
    return tabla.apply(pd.to_numeric, errors="coerce")


def _columna(tabla: pd.DataFrame, fragmento: str, estadistico: str) -> pd.Series | None:
    """Busca la columna cuyo parámetro contiene `fragmento` y cuyo estadístico es `estadistico`."""
    for nombre in tabla.columns:
        parametro, est = nombre.rsplit("|", 1)
        if fragmento in parametro and est == estadistico:
            return tabla[nombre]
    return None


def a_observaciones(tabla: pd.DataFrame, estacion: dict) -> pd.DataFrame:
    """Normaliza una tabla sinóptica al esquema común (formato largo, un día por fila)."""
    if tabla.empty:
        return pd.DataFrame(columns=COLUMNAS)
    series: dict[str, pd.Series] = {}

    acum = _columna(tabla, "pptacion acum", "max")
    if acum is not None:
        # Precipitación del día = máximo acumulado del día menos el del día anterior.
        # Se exige que el día anterior sea consecutivo; los negativos son reinicios del contador.
        dia = acum.diff()
        consecutivo = acum.index.to_series().diff().dt.days == 1
        valida = dia.where(consecutivo & (dia >= 0))
        series["precip_mm"] = valida

    for variable, fragmento in (("caudal_m3s", "caudal"), ("nivel_m", "nivel de agua")):
        media = _columna(tabla, fragmento, "media")
        if media is not None:
            series[variable] = media

    partes = []
    for variable, serie in series.items():
        # Se descartan nulos y los códigos de dato faltante del portal (p. ej. -99999).
        s = serie.dropna()
        s = s[s > VALOR_FALTANTE_MAXIMO]
        if s.empty:
            continue
        partes.append(pd.DataFrame({"fecha": s.index, "variable": variable, "valor": s.values}))
    if not partes:
        return pd.DataFrame(columns=COLUMNAS)
    out = pd.concat(partes, ignore_index=True)
    out["fuente"] = "DGA"
    out["cod_estacion"] = estacion["cod_bna"]
    out["estacion"] = estacion["nombre"]
    out["region"] = normalizar_region(estacion["region"])
    out["lat"] = estacion["lat"]
    out["lon"] = estacion["lon"]
    return out[COLUMNAS]


def _recolectar_estacion(
    est: dict, inicio: date, fin: date, pausa: float, carpeta_crudos: Path | None
) -> tuple[pd.DataFrame, dict]:
    """Descarga y normaliza una estación (con su propia sesión); reutiliza el HTML crudo si existe."""
    registro: dict = {"cod_bna": est["cod_bna"], "nombre": est["nombre"], "variables": {}}
    cache = carpeta_crudos / f"{est['cod_bna']}_{inicio:%Y%m%d}_{fin:%Y%m%d}.html" if carpeta_crudos else None
    try:
        if cache is not None and cache.exists():
            html = cache.read_text(encoding="utf-8")
        else:
            sesion = abrir_sesion()
            disponibles = parametros_estacion(sesion, est["cod_bna"])
            time.sleep(pausa)
            if not disponibles:
                return pd.DataFrame(columns=COLUMNAS), registro
            html = descargar_sinoptico(sesion, est["cod_bna"], list(disponibles.values()), inicio, fin)
            if cache is not None:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(html, encoding="utf-8")   # trazabilidad: respuesta cruda del portal
        obs = a_observaciones(parsear_sinoptico(html), est)
        if not obs.empty:
            registro["variables"] = obs.groupby("variable")["fecha"].nunique().to_dict()
        return obs, registro
    except requests.RequestException as exc:
        registro["error"] = str(exc)
        return pd.DataFrame(columns=COLUMNAS), registro


def recolectar(
    estaciones: list[dict],
    inicio: date,
    fin: date,
    pausa: float = PAUSA_SEGUNDOS,
    trabajadores: int = 4,
    carpeta_crudos: Path | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Descarga y normaliza las series de una lista de estaciones del catálogo.

    Usa concurrencia acotada (`trabajadores` hilos, cada uno con su propia sesión) porque el
    portal responde lento; el pacing por sesión evita saturarlo. Devuelve (observaciones,
    bitácora); la bitácora registra, por estación, los días con dato por variable y los errores.
    """
    partes: list[pd.DataFrame] = []
    bitacora: list[dict] = []
    with ThreadPoolExecutor(max_workers=trabajadores) as pool:
        futuros = [pool.submit(_recolectar_estacion, e, inicio, fin, pausa, carpeta_crudos) for e in estaciones]
        for futuro in tqdm(as_completed(futuros), total=len(futuros), desc="Estaciones DGA"):
            obs, registro = futuro.result()
            bitacora.append(registro)
            if not obs.empty:
                partes.append(obs)
    todo = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUMNAS)
    return todo, sorted(bitacora, key=lambda r: r["cod_bna"])
