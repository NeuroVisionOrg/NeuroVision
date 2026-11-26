# Pendientes vigentes — alineación H1

Fecha de revisión: 26 de noviembre de 2026. Base remota observada: `develop` en `3f9d65c34d868721876e4a8308dd2e55153dc632`. Esta lista no constituye una declaración de implementación ni de aprobación de PR.

## Infraestructura ya comprobada

- Repositorio oficial NeuroVisionOrg/NeuroVision, `develop` predeterminada, `main` y `develop` protegidas.
- `requirements.lock`, `capa_1_interfaz/package-lock.json` y `.secrets.baseline` presentes en la base aprobada.
- CI oficial manual completo exitoso en [PR #1](https://github.com/NeuroVisionOrg/NeuroVision/pull/1) y [PR #2](https://github.com/NeuroVisionOrg/NeuroVision/pull/2). Se conserva el flujo, los lockfiles y las pruebas pertinentes; repetir el CI para cada candidato nuevo.

## H1: bloqueantes de alineación

- Revisar y aprobar el PR de alcance 2D/3D, escala de grises, Random Walker y SOR único; adaptar contratos internos y DTO, pruebas afectadas, README y ADR.
- Dependencias 3D instaladas y probadas localmente con datos sintéticos; consultar [compatibilidad 3D](Anexo_compatibilidad_3D.md). Revisar los locks en el PR y comprobar el CI Linux. Resolver el tipado de las operaciones reales en sus adaptadores sin relajar mypy; vigilar la deprecación de Marching Cubes y verificar el renderizado WebGL.
- Reconciliar [ramas de los compañeros](Anexo_reconciliacion_H1.md) sin borrar su historial; adaptar el PR #3 y las propuestas de Traducción y Métodos al alcance vigente. Confirmar autoría, permisos y CODEOWNERS; verificar la membresía y autorización de cualquier excepción de ruleset.
- Verificar Jira y sus claves reales, registrar las tareas y reestimar las horas disponibles por integrante.
- Ejecutar `bash scripts/ci-local.sh todo`, revisión documentada y CI oficial completo para head/base definitivos. No presentar los CI históricos como validación de H1.

## Implementación y validación del producto

- Johan: cargar/visualizar cortes y volumen, ROI, semillas, controles y resultados de la API, malla interactiva; sin solver en frontend.
- Jherson: contratos, validaciones, API y casos de uso, integración y errores.
- Yenderson: lectura y normalización escalar 2D/3D, geometría, sistema CSR, reconstrucción; mallas, métricas y exportación básica.
- Jennifer: implementación propia y única de SOR con criterio de parada, historial de residuo y verificación matemática; experimentos de omega/tamaño.
- Equipo: flujos sintéticos completos en ambos modos, casos reales autorizados, demostración, manual de usuario y documentación de pruebas.

## Verificaciones científicas y de datos

- Licencias y autorización específicas de los datasets; conversión MHA a NIfTI y comprobación de geometría, etiquetas y alineación. No publicar datos médicos ni usar la referencia como entrada de la segmentación evaluada.
- Confirmar normalización, beta, pesos positivos finitos, frontera de ROI, anisotropía y conectividad a semillas; garantizar las condiciones SPD del sistema construido.
- Experimentar con tolerancias, omega y límites de ROI; registrar fallos, tiempos, memoria y tamaño. No prometer convergencia rápida ni precisión clínica.

Las especificaciones vigentes están en el [índice técnico](README.md); los siete documentos aprobados por el líder no implican que las funcionalidades estén implementadas. Las ramas de tarea contienen avances pendientes de revisión, no versiones estables.
