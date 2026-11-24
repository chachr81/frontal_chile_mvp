"""Pruebas del colector DGASAT con una tabla sinóptica mínima (sin acceso a la red)."""
import pandas as pd

from frontal.collectors import dga_dgasat as g

ESTACION = {
    "cod_bna": "05701009-6", "nombre": "Rio Maipo En Queltehues",
    "region": "Región Metropolitana de Santiago", "lat": -33.8, "lon": -70.2,
}


def _html(filas: list[tuple[str, float, float, float]]) -> str:
    """Arma una tabla con el mismo formato que entrega el portal (acumulado + caudal)."""
    cuerpo = "".join(
        f"<tr bgcolor=#E4E2E1><td class=txt>{i}</td><td class=txt>{f}</td>"
        f"<td class=txt align=right>{acum:.3f}</td><td class=txt align=right>{q:.3f}</td></tr>"
        for i, (f, acum, q, _) in enumerate(filas, 1)
    )
    return (
        "<table id=datos><thead><tr><th>Nro.</th><th>Fecha-Hora de Medicion</th>"
        "<th class=txt_form nowrap>RIO MAIPO EN<br>Pptación Acum.   \n(mm)Max</th>"
        "<th class=txt_form nowrap>RIO MAIPO EN<br>Caudal   \n(m3/s)Media</th></tr></thead>"
        f"<tbody>{cuerpo}</tbody></table>"
    )


def test_parsear_y_derivar_precipitacion():
    # Día 3 reinicia el contador (negativo, se descarta); día 5 tiene un salto de fecha (se omite).
    html = _html([
        ("01/06/2026", 100.0, 5.0, 0), ("02/06/2026", 102.5, 5.5, 0),
        ("03/06/2026", 1.0, 6.0, 0), ("05/06/2026", 3.0, 7.0, 0),
    ])
    tabla = g.parsear_sinoptico(html)
    assert list(tabla.index.strftime("%Y-%m-%d")) == ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-05"]

    obs = g.a_observaciones(tabla, ESTACION)
    precip = obs[obs.variable == "precip_mm"].set_index("fecha")["valor"]
    assert precip.to_dict() == {pd.Timestamp("2026-06-02"): 2.5}
    caudal = obs[obs.variable == "caudal_m3s"]
    assert len(caudal) == 4 and set(caudal.region) == {"Metropolitana de Santiago"}
    assert list(obs.columns) == g.COLUMNAS


def test_tabla_vacia_no_genera_observaciones():
    assert g.parsear_sinoptico("<html>sin datos</html>").empty
    assert g.a_observaciones(pd.DataFrame(), ESTACION).empty


def test_normalizar_nombres_de_parametro():
    assert g._normalizar("Pptación  Acum.  (mm)") == "pptacion acum. (mm)"
    assert g.PATRONES_PARAMETRO[0][1].search(g._normalizar("Pptación Acum.   (mm)"))


def test_descarta_codigo_de_dato_faltante():
    # El portal marca faltantes con -99999; no deben llegar a las observaciones.
    html = _html([("01/06/2026", 1.0, -99999.0, 0), ("02/06/2026", 1.0, 4.0, 0)])
    obs = g.a_observaciones(g.parsear_sinoptico(html), ESTACION)
    caudal = obs[obs.variable == "caudal_m3s"]
    assert list(caudal.valor) == [4.0]
