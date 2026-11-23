# Cómo contribuir a NeuroVision

## Flujo de trabajo

- Crear una rama de tarea desde `develop` actualizado.
- Asociar la rama, el commit y el PR con la tarea de Jira cuando el proyecto y su clave existan.
- Mantener commits individuales identificables y utilizar mensajes Conventional Commits en inglés.
- Abrir PR hacia `develop`; la promoción `develop` → `main` se controla por separado.
- Registrar criterios de aceptación y pruebas en la plantilla de PR.
- Solicitar revisión y obtener autorización de integración después de ejecutar el CI manual completo.
- No hacer push directo a `main` o `develop`.

Ejemplo de mensaje antes de establecer la clave Jira: `test: cover invalid ROI bounds`.

Cuando se cree el proyecto Jira, la forma recomendada será `test(CLAVE-123): cover invalid ROI bounds`. No se asigna una clave ficticia de Jira en este paquete.

## Código y contratos

- Respetar las cinco capas y sus APIs públicas.
- Traducción, Métodos y Servicios no se importan entre sí; Control los coordina.
- Contratos no importan ninguna capa.
- Mantener Ruff, mypy, ESLint, Prettier e Import Linter limpios.
- Una modificación de contrato requiere pruebas y revisión de las capas afectadas.
- No introducir funciones obsoletas, variables sin uso o comentarios de código muerto.

## Seguridad y datos

- Nunca subir `.env`, claves, tokens, volúmenes de datos médicos, modelos clínicos ni imágenes sin licencia.
- Utilizar datos sintéticos para pruebas reproducibles.
- Los archivos generados, cachés y `node_modules/` están ignorados.
- Si se filtra un secreto, avisar al responsable del repositorio: borrar el archivo en un commit nuevo no elimina el historial.

## CI oficial

La ejecución es exclusivamente manual mediante `workflow_dispatch`. Solo `pruebas=todo` exitoso, sobre el candidato de integración revisado y con revisión documentada, puede servir como evidencia de autorización. La revisión humana y las protecciones de GitHub son controles distintos.
