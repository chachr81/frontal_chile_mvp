# Criterios de aceptación y planificación de Sprints

Propuesta del Product Owner derivada de decisiones del repositorio (cobertura mínima 0,8, ventana de 7 días,
definición de terminado y tareas de validación T1 a T5). El equipo las confirma en la planificación de cada Sprint.

## Sprints

| Sprint | Fechas | Historias (puntos) | Objetivo |
|---|---|---|---|
| 1 | 23 nov. 2026 al 29 nov. 2026 | HU-01 a HU-04 (13) | Permitir que un analista identifique, con datos observados de estaciones públicas, qué región acumuló más precipitación en el último período con datos, con estados vacío, de carga y de error explícitos. |
| 2 | 30 nov. 2026 al 6 dic. 2026 | HU-05 a HU-07 (18) | Conectar la lluvia con su impacto hidrológico y permitir el análisis regional: caudal y nivel de ríos de la región, una pestaña de detalle por variable y un mapa de apoyo que seleccione regiones. |
| 3 | 7 dic. 2026 al 9 dic. 2026 | HU-08 a HU-10 (13) | Habilitar la revisión de una estación y de variables complementarias: serie con agregación seleccionable, metadatos de la estación en un pop-up y rosa de vientos por región. |

El último Sprint termina antes del 10 de diciembre de 2026.

## Criterios por historia

### HU-01 Ranking de regiones por precipitación acumulada

- [ ] La pantalla lista las regiones con datos de mayor a menor precipitación acumulada del período, con el valor medio, el máximo y el número de estaciones.
- [ ] El valor regional es la media del acumulado de las estaciones de la región que tienen datos en al menos el 80 % de los días del período.
- [ ] Una región sin estaciones con cobertura suficiente no aparece con 0 mm; si ninguna región cumple, se muestra el estado vacío.
- [ ] Un usuario nombra la región que encabeza el ranking sin ayuda (tarea T1, hipótesis H1).

**Verificación:** Pruebas automatizadas del cálculo (orden, cobertura, estaciones sin región) y sesión de validación.

### HU-02 Período calculado desde el último día con datos

- [ ] El período termina en el último día con al menos una observación de precipitación, no en la fecha de consulta.
- [ ] La ventana es de 7 días por defecto y el usuario puede ajustarla entre 1 y 30 días.
- [ ] La pantalla muestra las fechas de inicio y término del período y la fuente de los datos.
- [ ] Un usuario indica correctamente el período mostrado (tarea T2, hipótesis H2).

**Verificación:** Prueba automatizada del período y sesión de validación.

### HU-03 Presión mínima por región

- [ ] El indicador entrega, por región, la presión mínima del período en hPa con la estación y el día en que se registró.
- [ ] Las regiones se presentan desde la presión más baja y la vista indica que el valor es una observación de la estación, no un promedio.
- [ ] Si no hay observaciones de presión en el período, se muestra el estado vacío y no un gráfico en blanco.
- [ ] Un usuario relaciona el valor con un frente o con baja presión (tarea T3, hipótesis H3).

**Verificación:** Prueba automatizada de la presión mínima y sesión de validación.

### HU-04 Estado vacío explícito

- [ ] Cuando un indicador, una serie o una región no tiene datos, la pantalla muestra un mensaje que comienza con «Sin datos» y explica el motivo.
- [ ] Una serie sin datos nunca se dibuja ni se informa como cero.
- [ ] Durante la lectura se muestra un indicador de carga y, si el archivo no puede leerse, un mensaje de error sin que la aplicación se detenga.
- [ ] Un usuario entiende que no hay datos y no que llovió cero (tarea T4, hipótesis H4).

**Verificación:** Pruebas automatizadas de la aplicación (sin archivo, archivo corrupto) y sesión de validación.

### HU-05 Caudal y nivel de ríos de la región

- [ ] El usuario elige una región y ve las series diarias de caudal (m³/s) y de nivel (m) de sus estaciones, en el mismo período del ranking.
- [ ] Cada serie indica su estación y su fuente.
- [ ] Si la región no tiene caudal ni nivel en el período, se informa que no hay datos y que ello no equivale a caudal cero.
- [ ] Un usuario describe una relación con la lluvia o declara con razones que no puede inferirla (tarea T5, hipótesis H5).

**Verificación:** Prueba automatizada de la serie hidrológica y sesión de validación.

### HU-06 Detalle de región con una pestaña por variable

- [ ] Al seleccionar una región se muestra una pestaña por cada variable con datos (precipitación, presión, caudal y nivel).
- [ ] Las variables sin datos en la región se indican como sin datos y no se ocultan.
- [ ] Todas las pestañas usan el período definido en HU-02.

**Verificación:** Revisión del Product Owner en el entorno de prueba y sesión de validación.

### HU-07 Mapa de apoyo que selecciona regiones

- [ ] El mapa muestra las 16 regiones y su selección actualiza la región consultada en el detalle.
- [ ] El mapa es de apoyo (tamaño reducido) y la información queda disponible sin usarlo, también con teclado.
- [ ] Se atribuyen las fuentes cartográficas utilizadas.

**Verificación:** Revisión del Product Owner en el entorno de prueba y verificación de uso con teclado.

### HU-08 Serie de una estación con agregación seleccionable

- [ ] El usuario elige una estación y una agregación (cruda, diaria, semanal o mensual) y la serie se actualiza.
- [ ] Al agregar, los períodos con cobertura inferior al 80 % se marcan como sin datos y no se completan con ceros.
- [ ] La serie indica la variable, la unidad y la fuente.

**Verificación:** Pruebas automatizadas de la agregación y revisión del Product Owner.

### HU-09 Pop-up con los metadatos de la estación

- [ ] Al seleccionar una estación se muestra su código, nombre, fuente, coordenadas y cobertura de datos.
- [ ] El pop-up se puede cerrar con teclado.
- [ ] Los campos que la fuente no entrega se indican como no disponibles.

**Verificación:** Revisión del Product Owner en el entorno de prueba.

### HU-10 Rosa de vientos por región

- [ ] El usuario ve, para la región elegida, la dirección del viento en el pico del evento.
- [ ] La historia requiere incorporar una variable de viento al conjunto de datos, que hoy no existe.
- [ ] Si la región no tiene datos de viento, se muestra el estado vacío.

**Verificación:** Prueba automatizada de la rosa de vientos y revisión del Product Owner.
