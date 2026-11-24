# Fuentes de datos: qué está verificado y qué no

Revisión realizada el 23-11-2026.

## DMC (Dirección Meteorológica de Chile)

**Verificado en el portal oficial** (https://climatologia.meteochile.gob.cl):
- Los datos publicados son "de acceso y uso público" y el portal solicita citar a la DMC.
- No se nombra una licencia ni límites de uso.
- El servicio `getEmaResumenDiarioGeo` devuelve un GeoJSON y requiere los parámetros
  `usuario` (correo) y `token` (clave personal). La documentación no explica cómo obtener el token.
- Campos documentados: `aguaCaidaHoy`, `aguaCaidaAyer` (y sus `...Datos`) y `presion`
  (texto con coma de miles, por ejemplo "1,010.7").

**No verificado** (pendiente de la primera descarga real):
- Unidad de `aguaCaidaAyer` y `presion` (se asumen mm y hPa).
- Nombres de los campos de código, nombre y región de la estación.
- Cómo obtener el token y si su uso en una aplicación pública está permitido.

## DGA (Dirección General de Aguas)

**Verificado**:
- El Sistema Hidrométrico en Línea (https://snia.mop.gob.cl/dgasat) publica datos de
  estaciones (caudal, nivel, precipitación, entre otros) sin costo (ficha ChileAtiende 1207).
- Los boletines de la DGA advierten que los valores son provisorios y no validados.
- El acceso técnico es por formularios web con sesión; el portal rechaza clientes sin
  User-Agent de navegador y se satura con ráfagas de solicitudes.
- No se encontró una licencia explícita de reutilización.

**Verificado en la práctica (23-11-2026)**: la tabla sinóptica diaria de DGASAT se extrae sin credenciales
(sesión con cookie, User-Agent de navegador, pacing entre solicitudes) con `scripts/collect.py dga-dgasat`.

**No verificado**: si la extracción automatizada está permitida por los términos del portal (no se encontró
una cláusula explícita) y la unidad exacta de cada contador. El importador de CSV (`dga-csv`) se mantiene
como alternativa.

## Obligaciones para el visor

- Citar a la DMC y a la DGA como fuentes y declarar que los datos son provisorios.
- No publicar el token. `.env` está en `.gitignore`.
- Mantener un ritmo de solicitudes bajo (una descarga diaria).
- Confirmar con la DMC y la DGA las condiciones de reutilización antes de desplegar públicamente.


# Piloto con datos reales: Región Metropolitana

## Alcance del piloto
Región Metropolitana de Santiago, periodo 2 de junio al 23 de noviembre de 2026 (el último día es parcial).
Una sola región: el ranking entre regiones (HU-01) no se demuestra con este piloto; se muestra a nivel de estación.

## Dirección General de Aguas (DGA)
- Catálogo de estaciones: servidor MCP "Red de Monitoreo Chile" (`data/catalogo/dga_estaciones.json`, 53 estaciones vigentes de la región).
- Series diarias: portal DGASAT (sinóptico diario), extraídas con `scripts/collect.py dga-dgasat`. El portal no requiere credenciales; exige User-Agent de navegador, sesión con cookie y pacing entre solicitudes.
- Variables incorporadas: precipitación diaria, caudal medio diario, nivel medio diario.

## Supuestos y limitaciones (a verificar)
- Los datos son provisorios, no validados por la DGA.
- Precipitación diaria = máximo diario del contador acumulado menos el del día anterior (solo días consecutivos); los negativos (reinicios del contador) se descartan.
- Se descartan los códigos de dato faltante del portal (p. ej. -99999).
- La presión atmosférica de la DGA es presión de estación, no reducida a nivel del mar, y las estaciones están a altitudes distintas; por eso no se incorpora (HU-03 queda pendiente de la DMC).
- DMC (Dirección Meteorológica de Chile): requiere token personal; no se utilizó en este piloto.
- Estaciones sin respuesta del portal o sin parámetros de interés quedan fuera; la bitácora de cobertura se guarda en `data/raw/dga_dgasat/` (no versionada).
