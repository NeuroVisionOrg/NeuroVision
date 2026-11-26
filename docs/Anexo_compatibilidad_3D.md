# Anexo de compatibilidad 3D — H1

Fecha: 26 de noviembre de 2026. Evidencia: salidas de terminal aportadas por el líder en la rama local `chore/align-2d-3d-sor-scope`. Esta evaluación tecnológica no valida el producto ni acredita una ejecución oficial de CI.

## Versiones y responsabilidad

| Paquete | Versión instalada | Licencia identificada | Uso previsto |
|---|---|---|---|
| NiBabel | 5.5.0 | MIT | Traducción: NIfTI y geometría |
| scikit-image | 0.26.0 | BSD | Servicios: Marching Cubes |
| Three.js | 0.187.0 | MIT | Interfaz: geometría y presentación 3D |
| @types/three | 0.187.0 | MIT | Desarrollo: declaraciones de tipos de Three.js |

Entorno informado: Windows, Python 3.13.17, NumPy 2.5.5, SciPy 1.18.1, Node.js 22.23.5 y npm 10.9.9. Los manifiestos y lockfiles incorporan las nuevas dependencias; se conservan las versiones existentes observadas. `pip check` no reportó requisitos rotos; `npm audit` reportó cero vulnerabilidades en esa ejecución, no una garantía de seguridad futura. Revisar licencias transitivas y cualquier restricción adicional del docente antes de distribución. Las licencias de datos médicos se verifican por separado.

## Pruebas reproducibles incorporadas

- `tests/unit/test_compatibilidad_nifti.py`: escritura/lectura NIfTI sintético, metadatos y reorientación.
- `tests/unit/test_compatibilidad_malla.py`: extracción de superficie sintética, índices y transformación física esperada.
- `capa_1_interfaz/src/shared/geometry/threeCompatibility.test.ts`: geometría de Three.js, sin contexto WebGL.

Resultado observado antes de las nuevas reglas de arquitectura: 215 pruebas unitarias/de arquitectura Python aprobadas (49 advertencias); Ruff, formato, mypy del código del proyecto y 3 contratos Import Linter aprobados. Frontend: ESLint y Prettier aprobados, 3 pruebas Vitest aprobadas y compilación TypeScript/Vite correcta. No se ha comprobado la aplicación final, el solver ni datos reales. El CI local completo y el CI oficial del candidato siguen pendientes.

## Limitaciones abiertas

| Hallazgo | Evidencia y tratamiento |
|---|---|
| Deprecación de Marching Cubes | 49 `DeprecationWarning` en scikit-image 0.26.0: 48 de asignación a `ar.shape` y una a `faces.shape` con NumPy 2.5.5. Las pruebas pasan. Mantener visibles; evaluar una versión corregida y repetir pruebas antes de actualizar. No modificar `site-packages` ni ocultar advertencias. |
| Tipado de NiBabel y scikit-image | El diagnóstico adicional `python -m mypy --strict tests/unit/test_compatibilidad_nifti.py tests/unit/test_compatibilidad_malla.py` falla con 7 `no-untyped-call`: seis en NiBabel (constructor, unidades, zooms, reorientación y códigos de ejes) y uno en `marching_cubes`. No es parte del conjunto de archivos del mypy oficial actual. No presentarlo como aprobado. |
| Adaptadores de producción | Traducción y Servicios deben delimitar y validar las llamadas a las bibliotecas, con tipos compatibles con mypy estricto. Evaluar declaraciones de tipos mantenidas o interfaces tipadas acotadas y verificables; no introducir `Any`, excepciones globales ni silenciamientos de errores para pasar el CI. La solución concreta requiere revisión de sus responsables. |
| Compatibilidad de ejecución | Faltan CI Linux con locks, renderizado WebGL real, tolerancias geométricas, política de admisión NIfTI, escala/orientación de mallas reales, rendimiento y pruebas de integración de ambos modos. |

## Límites arquitectónicos

Las bibliotecas de imágenes no son dependencias del solver. La importación directa de NiBabel se reserva a Traducción, la de scikit-image a Servicios. Control accede a operaciones públicas de ambas capas; su uso indirecto legítimo por composición no está prohibido. Métodos Numéricos mantiene su prohibición de importar HTTP, presentación o procesamiento de imágenes, incluida la dependencia transitiva detectada por Import Linter. Los tests de compatibilidad pueden importar bibliotecas directamente porque son sondas de infraestructura, no capas del producto. Three.js se usa en Interfaz, nunca como método de solución del sistema. No se incorpora un solver externo ni una sexta capa.
