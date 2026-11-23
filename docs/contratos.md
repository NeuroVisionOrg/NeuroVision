# Contratos entre módulos — NeuroVision

**Versión de diseño:** 0.3 (fases 1, 2 y 3). **Estado:** base acordada; algunos parámetros siguen pendientes de validación científica o de rendimiento. El código incluido en el esqueleto implementa los **tipos y validaciones estructurales iniciales**, pero todavía no los procesamientos.

## Regla de arquitectura

- La Interfaz de Johan se comunica con Control por HTTP.
- Control, bajo responsabilidad de Jherson, valida y coordina las APIs públicas de Traducción, Métodos y Servicios.
- Traducción, Métodos y Servicios son **independientes entre sí**.
- `contratos/` solo define estructuras compartidas y nunca importa otras capas.

## Fase 1: imagen, ROI y semillas

| Tipo | Campos | Regla esencial |
| --- | --- | --- |
| `ImageData` | `pixels`, `source_format`, `normalization`; dimensiones derivadas | `float32`, escala gris 2D, valores finitos en `[0,1]` |
| `ROISelection` | `x_min`, `y_min`, `x_max`, `y_max` | Origen arriba-izquierda; X=columna, Y=fila; máximos exclusivos |
| `Seed` | `x`, `y`, `label` | Coordenadas originales y `foreground` / `background` |
| `SeedSelection` | `seeds` | Sin posiciones duplicadas y con ambas clases |

Control comprueba que la ROI esté dentro de la imagen, que todas las semillas estén dentro de la ROI y que queden incógnitas. En Konva, el zoom y el desplazamiento afectan a la pantalla, **no** a las coordenadas guardadas.

Ejemplo de prueba: imagen 120 × 80; ROI `[20,60) × [10,50)` de 40 × 40; semillas `(34,25)` y `(22,12)`, que localmente son `(14,15)` y `(2,2)`.

**Transporte HTTP futuro:** `multipart/form-data`, con archivo `image` y JSON `selection`. El backend compara las dimensiones declaradas con las dimensiones decodificadas. El frontend nunca envía matrices CSR.

## Fase 2: sistemas lineales

| Tipo | Campos | Restricciones |
| --- | --- | --- |
| `LinearSystem` | `A`, `b` | `A` CSR canónica `float64` de dimensión `(n,n)`, `b` vector `(n,)`, diagonal positiva y valores finitos |
| `SolverConfig` | `method`, `rtol`, `atol`, `max_iterations`, `omega`, `x0` | Tolerancias válidas; SOR y SSOR requieren `0 < omega < 2` |
| `SolverResult` | método, estado, solución, iteraciones, barridos, residuos, historial, tiempo | Estado coherente, historial desde iteración 0; SSOR = dos barridos por iteración completa |

`LinearSystem` no comprueba por sí solo que una matriz arbitraria sea SPD. **Traducción** debe garantizar conectividad y propiedades matemáticas al construir el Laplaciano reducido, y las pruebas matemáticas deben verificarlas.

Para todas las implementaciones se utilizará la misma condición de residuo:

\[
\lVert b-Ax^{(k)}\rVert_2 \le \max(\mathrm{atol},\mathrm{rtol}\lVert b\rVert_2)
\]

**Valores experimentales provisionales:** `rtol=1e-6`, `atol=1e-10`, `max_iterations=2000`. No constituyen una garantía de rendimiento.

## Fase 3: reconstrucción y servicios

| Tipo | Información prevista | Estado |
| --- | --- | --- |
| `SegmentationResult` | Resultado de solver, probabilidades, máscara, contorno y umbral | Estructura creada; reconstrucción pendiente |
| `MetricsResult` | Primer plano, Dice, IoU y conteos relativos a referencia | Estructura creada; cálculo pendiente |
| `ExportResult` | Nombre, MIME, bytes | Estructura creada; exportación pendiente |
| `SegmentationRunResult` | Agrupa configuración y cuatro resultados | Pendiente de diseño concreto de API |

Las máscaras y mapas seguirán la forma `(alto_roi, ancho_roi)`; una ejecución no convergente no generará una máscara declarada válida. Dice e IoU solo aparecerán si existe una máscara de referencia compatible. Si ambas máscaras están vacías, se informarán como no definidos según esta propuesta.

Exportaciones previstas: PNG para máscaras/gráficas, CSV para comparaciones y JSON para configuración y resumen.

## Errores y validación

Se distinguirán errores de entrada (`INVALID_ROI`, `SEED_OUT_OF_BOUNDS`, `MISSING_SEED_CLASS`, etc.), fallo de construcción matemática y estados de ejecución numérica (`CONVERGED`, `MAX_ITERATIONS`, `NUMERICAL_FAILURE`). Los códigos de error HTTP externos se formalizarán al implementar `/api/v1/segmentar`.

## Pendientes de esta especificación

Normalización definitiva, soporte 16 bits/DICOM/NIfTI, valor predeterminado de beta, límite de ROI, tamaño máximo de payload, formatos de exportación y pruebas sobre datos autorizados. No se afirma que estos componentes estén terminados.
