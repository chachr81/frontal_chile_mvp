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

**No verificado**: formato exacto de las tablas y si su extracción automatizada está permitida.
Por eso el MVP importa un CSV exportado por el equipo.

## Obligaciones para el visor

- Citar a la DMC y a la DGA como fuentes y declarar que los datos son provisorios.
- No publicar el token. `.env` está en `.gitignore`.
- Mantener un ritmo de solicitudes bajo (una descarga diaria).
- Confirmar con la DMC y la DGA las condiciones de reutilización antes de desplegar públicamente.
