# Frontal Chile: visor mínimo público (MVP)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![seaborn](https://img.shields.io/badge/seaborn-4C72B0)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C)
![Requests](https://img.shields.io/badge/Requests-2C5BB4)
![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green)
![Datos DMC](https://img.shields.io/badge/Datos-DMC-005A9C)
![Datos DGA](https://img.shields.io/badge/Datos-DGA-0077B6)

Proyecto de Innovación Tecnológica, Universidad Mayor (Ingeniería en Informática).
Unidades 1 y 2. Equipo 2.

Visor web que permite a un analista de gestión de riesgo responder una pregunta: **qué
región fue más afectada por un sistema frontal en el último período con datos**, usando
observaciones de estaciones públicas (DMC y DGA) y mostrando siempre la fuente y el período.

## Stack técnico

| Capa | Herramienta | Uso en el proyecto |
|---|---|---|
| Lenguaje | Python 3.10 o superior | Todo el código |
| Interfaz | Streamlit | Pantalla comparativa del visor |
| Gráficos | seaborn y Matplotlib | Ranking, presión mínima y series hidrológicas |
| Datos | pandas | Carga, indicadores y almacenamiento en CSV |
| Recolección | Requests | Cliente del servicio GeoJSON de la DMC |
| Calidad | pytest y GitHub Actions | 38 pruebas, ejecutadas en cada push |
| Fuentes | DMC y DGA | Datos públicos de estaciones (ver `docs/fuentes_datos.md`) |

## Alcance del MVP (Product Backlog v2.0)

| Historia | Funcionalidad | Dónde está |
|---|---|---|
| HU-01 | Ranking de regiones por precipitación acumulada | `procesamiento/indicadores.py::ranking_regiones` |
| HU-02 | Período calculado desde el último día con datos | `indicadores.py::periodo` |
| HU-03 | Presión mínima por región | `indicadores.py::presion_minima_regiones` |
| HU-04 | Estados vacío, de carga y de error | `app/streamlit_app.py` |
| HU-05 | Caudal y nivel de ríos junto con la lluvia | `indicadores.py::hidrologia_region` |

Fuera del MVP: HU-06 a HU-10 (detalle por pestañas, mapa de apoyo, serie con agregación,
metadatos en pop-up, rosa de vientos).

## Puesta en marcha (Windows)

```powershell
.\setup.ps1                                  # crea .venv, instala dependencias y corre las pruebas
.\.venv\Scripts\Activate.ps1
streamlit run src/frontal/app/streamlit_app.py
```

Sin datos reales, el visor muestra el estado vacío (HU-04). Para probar la interfaz con
datos **sintéticos** (advertencia permanente en pantalla, nunca para evidencia):

```powershell
python scripts/generar_datos_prueba.py $env:TEMP\frontal_prueba
$env:FRONTAL_DATOS = "$env:TEMP\frontal_prueba\observaciones.csv"
streamlit run src/frontal/app/streamlit_app.py
```

## Datos reales

1. **DMC**: copie `.env.example` como `.env` y complete `DMC_USUARIO` y `DMC_TOKEN`.
   Luego `python scripts/collect.py dmc --inspect` (revisa los campos reales) y
   `python scripts/collect.py dmc` (descarga y guarda). El servicio entrega el resumen
   diario vigente, por lo que debe ejecutarse todos los días para acumular historia.
2. **DGA**: exporte las series a CSV desde el portal y use
   `python scripts/collect.py dga-csv ruta.csv` (columnas en `collectors/dga_csv.py`).

**Verificado vs. pendiente**: lea `docs/fuentes_datos.md`. Varios supuestos (nombres de
campos de la DMC, unidad de precipitación, formato del CSV de la DGA) deben confirmarse
con la primera descarga real, y es una tarea explícita del Sprint 1.

## Arquitectura

Ver `docs/arquitectura.md`. En breve: recolectores -> `data/processed/observaciones.csv`
(formato largo) -> indicadores puros con pandas -> visor Streamlit con gráficos seaborn.
No hay base de datos ni servidor propio.

## Pruebas

```powershell
python -m pytest -q
```

## Definición de terminado (Anexo B de la entrega)

1. Código revisado por otro Developer (pull request con revisión).
2. Todo dato mostrado declara su fuente y su período.
3. Estados vacío, de carga y de error implementados.
4. Funciona en escritorio y móvil, y se puede usar con teclado.
5. Desplegado en entorno de prueba y aceptado por el Product Owner.

## Gestión del trabajo

El backlog, los Sprints y los impedimentos se registran en GitHub (Issues, Milestones y
Projects) a partir de `planning/plan.json`; ver `docs/gestion_en_github.md`.

## Licencia

Código bajo licencia MIT (propuesta del equipo, por confirmar). La licencia del código
**no** cubre los datos: cada fuente tiene sus propios términos (ver `docs/fuentes_datos.md`).
