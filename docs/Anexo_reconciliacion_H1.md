# NeuroVision — Reconciliación de avances y puerta H1

**Fecha:** 26 de noviembre de 2026 · **Estado:** revisión preliminar de solo lectura; recomendaciones para el equipo.

## 1. Base de trabajo

Alcance aprobado: 2D y 3D escalares, Random Walker binario, un SOR propio en Métodos Numéricos, cinco capas, Control coordinador, NIfTI volumétrico condicionado a admisión geométrica, CSR, exportación básica y pruebas. Referencias: los siete documentos aprobados por el líder, el anexo de datos v0.2 y registro v1.9.

Repositorio: https://github.com/NeuroVisionOrg/NeuroVision. Develop protegida y predeterminada, HEAD `3f9d65c34d868721876e4a8308dd2e55153dc632`; main protegida, HEAD `7062533e9f15d697ffc5d42a68968b997ec82c3d`. PR #1/#2: CI oficial exitoso. PR #3: abierto; no se encontró CI oficial para ese PR en los últimos diez runs manuales desde develop. No se ejecutó código de las ramas ni se realizó revisión exhaustiva.

## 2. Inventario y acciones propuestas

| Rama / SHA revisado | Evidencia | Reutilizar | Corregir antes de integrar |
|---|---|---|---|
| `feat/interfaz-visor-3d` / `bd941ed608889e643f20e47c47cabe5b37d321ea` | [PR #3](https://github.com/NeuroVisionOrg/NeuroVision/pull/3), 11 archivos modificados/añadidos, autor `Jb20201204` | Konva, ROI, semillas, vistas, estilos y datos sintéticos útiles como fixtures | `solver3d.ts` contiene construcción del problema, cuatro métodos y métricas: retirar del flujo y sustituir por consumo de Control y dobles de contrato explícitos en tests; comparación por omega; actualizar DTO v2 y malla 3D proveniente de Servicios; revisar representación y pruebas. No tratar prototipo como resultado de SOR backend. |
| `feature/datos-conversion` / `49ab984720cbef8de03f5c8af10285c5a50c82f6` | [Comparación](https://github.com/NeuroVisionOrg/NeuroVision/compare/3f9d65c34d868721876e4a8308dd2e55153dc632...49ab984720cbef8de03f5c8af10285c5a50c82f6), 4 commits, `yendersonedwin-cloud` | `imagenes.py`, API pública, pruebas de lectura y reconstrucción gris | `cargar_imagen_gris` convierte cualquier RGB a L: exigir R=G=B y rechazar color real. Separar decodificación de normalización min–max de ROI según C-01; mantener precisión. `tests/test_conversion_imagenes.py` queda fuera del comando actual de CI de unit/architecture; mover a `tests/unit/` y agregar negativos. Adaptar a archivos recibidos por Control. |
| `feature/modelo-3d-sor` / `0fe740dd22c37a0a0fef8fa37637829c2bc17ccb` | [Comparación](https://github.com/NeuroVisionOrg/NeuroVision/compare/3f9d65c34d868721876e4a8308dd2e55153dc632...0fe740dd22c37a0a0fef8fa37637829c2bc17ccb), 5 commits, `jdosorio-dev` | `residuo.py`, fixtures `tests/apoyo/sistemas_3d.py`, `tests/unit/test_modelo_3d.py`, aportes matemáticos | ADR-007 propone apilar JPG/PNG, conservar enum de cuatro métodos y ordenamientos natural/rojo-negro, estimar omega óptimo; reconciliar con NIfTI y ambos modos, contrato exclusivamente SOR y barrido determinista aprobado. Rojo-negro/estimación de omega son propuestas adicionales, no necesarias ni rendimiento garantizado. Mantener `spsolve` solo como oráculo de tests. Revisar consistencia de fixtures, pesos y condiciones SPD. Falta implementación del resolver SOR. |

No atribuir las cuentas a personas sin confirmación del equipo. No se encontraron PR abiertos para las otras dos ramas en la consulta realizada. Confirmar head/base nuevamente antes de revisar/ejecutar CI. Las pruebas declaradas en PR #3 son evidencia reportada por su autor, no verificación independiente.

## 3. PR inicial de alineación: PL-01

Rama `chore/align-2d-3d-sor-scope` desde develop, sin integrar PR #3 ni las demás ramas antes de reconciliar. Preservar commits y autores; no realizar reset, force push ni squash de la historia. La rama de alineación debe contener cambios acotados a documentación, contratos, tipos y pruebas estructurales, no implementar solvers ni visores ficticios.

Rutas canónicas para esta incorporación (se conservan las tres rutas ya existentes, actualizando sus contenidos y manteniendo historial en Git; no crear dos especificaciones activas):

| Archivo aprobado | Ruta objetivo |
|---|---|
| `01_Requisitos_v0.2.md` | `docs/01_Requisitos.md` |
| `02_Casos_de_uso_v0.2.md` | `docs/02_Casos_de_uso.md` |
| `03_Modelo_matematico_v0.2.md` | `docs/modelo_matematico.md` (actualiza la ruta existente) |
| `04_Arquitectura_v0.2.md` | `docs/04_Arquitectura.md` |
| `05_Contratos_v0.2.md` | `docs/contratos.md` (actualiza la ruta existente) |
| `06_Plan_de_pruebas_v0.2.md` | `docs/plan_pruebas.md` (actualiza la ruta existente) |
| `07_Cronograma_v0.2.md` | `docs/07_Cronograma.md` |
| `Anexo_validacion_datos_v0.2.md`, `Anexo_reconciliacion_H1.md` | `docs/Anexo_validacion_datos.md`, `docs/Anexo_reconciliacion_H1.md` |
| Registro v1.9 | `docs/decisiones/registro.md` |

Revisar enlaces de README, CONTRIBUTING, pendientes, ADR-005/006 y documentación de infraestructura. ADR-007 existe en una rama de Jennifer: acordar su revisión con ella y no crear una decisión contradictoria duplicada. Conservar registro de evidencia original e histórica; no copiar imágenes o ZIP de investigación, fuentes privadas, ni datos médicos a GitHub. Revisar privacidad y permisos antes de publicar cualquier documento.

Contratos: conservar `LinearSystem` y tipos 2D útiles; añadir tipos volumétricos y contexto según C-01–09; limitar método a SOR, omega obligatorio, adaptar diagnóstico y pruebas de fallos numéricos, DTO TypeScript v2. No modificar lockfiles ni incorporar dependencias sin evaluar. Actualizar tests afectados, mantener tests válidos y controles de calidad. Revisar prohibiciones de dependencias médicas/UI en Métodos Numéricos al incorporar nuevas librerías.

## 4. Secuencia de integración

1. Confirmar con equipo los contratos, avances existentes y horas restantes; verificar handles/permisos y membresía bypass PR-only. Crear rama de alineación local a partir de develop limpio.
2. Preparar diff de PL-01, revisar con responsables y ejecutar `bash scripts/ci-local.sh todo`. Commit convencional y PR a develop. CI manual oficial `workflow_dispatch`, rama develop, PR y SHA head completo, `pruebas=todo`; comprobar base/head vigentes y resumen exitoso antes de merge. No es required status check automático.
3. Una vez integrada la base, cada autor incorpora develop a su rama mediante merge (sin reescribir historia), resuelve discrepancias, ajusta tests y aporta PR propio. Reutilizar trabajo ya realizado; no duplicar ramas/tareas.
4. Evaluar dependencias 3D con lockfiles y CI; continuar sintéticos mientras se verifica licencia/conversión/geométrica de datos reales.
5. Confirmar Jira y CODEOWNERS con cuentas reales y tareas trazables. Reestimar el cronograma a partir de los avances y horas disponibles. No se inventan claves Jira, aprobaciones ni resultados.

## 5. Primer comando local

```bash
git status --short --branch
git remote -v
git fetch origin --prune
```

Comprobar que no hay cambios locales pendientes antes de cambiar de rama; si los hay, revisarlos y conservarlos. Si está limpio y la rama propuesta no existe, continuar:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c chore/align-2d-3d-sor-scope
git status --short --branch
```

No se ha preparado todavía el diff de contratos ni ejecutado los comandos en el equipo local. No se han modificado ramas, PR, Jira ni datos originales.
