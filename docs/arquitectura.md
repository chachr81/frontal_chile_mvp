# Arquitectura (liviana)

```
 DMC (GeoJSON, usuario+token) --\
                                  >-- collectors/ --> data/processed/observaciones.csv
 DGA (CSV exportado del portal) -/        |                  + metadatos.json
                                          v
                        procesamiento/ (pandas, funciones puras)
                                          v
                   app/ (Streamlit + seaborn): una pantalla comparativa
```

## Decisiones

| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| Un CSV en formato largo versionado en el repositorio | Base de datos (PostGIS) | El MVP maneja pocas estaciones y días; un CSV es auditable, se revisa en un pull request y no requiere servidor. Costo: no escala a series largas. |
| Streamlit | API REST + front separado | Un solo proceso Python, sin JavaScript, y acepta figuras de matplotlib/seaborn (requisito del curso). Costo: menos control del diseño y de la accesibilidad. |
| Indicadores como funciones puras | Lógica dentro de la interfaz | Se prueban sin interfaz (`tests/test_indicadores.py`). |
| Regla de agregación: media de estaciones con cobertura >= 80 % | Suma o máximo regional | Evita que una región con más estaciones domine. Es una propuesta a validar con usuarios (hipótesis H1). |
| DGA por CSV exportado | Scraping automatizado | No hay API oficial documentada; automatizarlo es una tarea del Sprint 1 una vez verificado el flujo. |

## Limitaciones conocidas

- El servicio de resumen diario de la DMC entrega el día vigente: el historial se construye
  guardando una descarga por día. Hasta entonces, el período será corto.
- La "presión mínima" es el mínimo de las lecturas diarias guardadas, no el mínimo
  instantáneo real del día.
- Las estaciones sin región reconocida quedan fuera de los cálculos regionales.
