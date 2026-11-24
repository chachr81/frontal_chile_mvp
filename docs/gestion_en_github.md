# Gestión del trabajo en GitHub

- **Milestones**: Sprint 1, Sprint 2 y Sprint 3 (planificación tentativa de la Unidad 1).
- **Issues de historia** (etiqueta `historia`): HU-01 a HU-10 del Product Backlog v2.0,
  con prioridad, épica y estimación en puntos.
- **Issues de tarea** (etiqueta `tarea`): tareas del Sprint 1 con estimación en horas.
- **Impedimentos**: un issue con etiqueta `impedimento` (plantilla incluida) abierto el mismo
  día en que aparece. La fecha de creación y de cierre de GitHub sirve de evidencia.
- **Estado de las tareas**: tablero de Projects con columnas Pendiente, En Progreso y Terminado.
- **Pull requests**: obligatorios y con revisión de otro Developer (definición de terminado).

`planning/plan.json` contiene el plan; `scripts/publicar_plan_github.py` lo publica de forma
idempotente (`--dry-run` para revisar antes).
