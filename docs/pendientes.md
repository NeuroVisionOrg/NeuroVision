# Pendientes explícitos de la base inicial

## Bloqueantes antes del CI completo

- Instalar dependencias con acceso a los registros de PyPI y npm.
- Generar y confirmar un `package-lock.json` real (`cd capa_1_interfaz && npm install`). **No fabricar lockfiles.**
- Bloquear las versiones exactas de dependencias Python con un `requirements.lock` real: `uv pip compile pyproject.toml --extra dev --python-version 3.13 -o requirements.lock`, revisar y confirmar el resultado.
- Generar y auditar `.secrets.baseline` mediante `detect-secrets scan` antes de habilitar el hook correspondiente.
- Ejecutar Ruff, Ruff Format, mypy, Import Linter, ESLint, Prettier, Vitest y Vite en el entorno definitivo; corregir cualquier incompatibilidad.
- Verificar mediante una importación intencionalmente prohibida que Import Linter realmente falla.
- Crear el repositorio público de la organización que el equipo elija, establecer la rama `develop` y publicar el workflow allí y en la rama predeterminada, requisito para `workflow_dispatch`. Ver `docs/CONFIGURAR_GITHUB.md`.
- Configurar `NEUROVISION_CI_OPERATOR` en GitHub y comprobar permisos y protección real de `main` y `develop`.
- Ejecutar un CI manual de prueba sobre un PR real y demostrar que no autoriza un SHA desactualizado.

## Implementación futura de las capas

- **Johan:** carga visual, ROI y semillas en Konva, visor, resultados y comparación.
- **Jherson:** petición HTTP real, validación Pydantic, casos de uso, coordinar contratos y pruebas de integración.
- **Yenderson:** decodificar MRI 2D, grafo, pesos, Laplaciano y sistema; reconstruir máscaras; métricas y exportaciones.
- **Jennifer:** Jacobi, Gauss-Seidel, SOR, SSOR, criterios de parada y rendimiento.

## Decisiones matemáticas pendientes

Normalización de intensidades, beta, estabilidad ante pesos muy pequeños, límites de tamaño de ROI, tolerancias finales y omega; pruebas en imágenes sintéticas primero, después resonancias autorizadas. La comparación numérica no valida diagnóstico médico.

## Lo que NO está completado

No hay algoritmos de segmentación, endpoint de segmentación, exportaciones, imágenes médicas de prueba ni CI ejecutado oficialmente en GitHub. Solo hay estructura, contratos iniciales y pruebas mínimas.
