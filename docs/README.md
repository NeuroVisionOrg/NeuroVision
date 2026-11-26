# Documentación técnica de NeuroVision

Línea base de diseño aprobada por el líder; integración, revisión de responsables y validaciones técnicas pendientes. Alcance: segmentación asistida 2D/3D escalar, Random Walker binario, SOR propio único y cinco capas. No es evidencia de implementación ni de validación clínica.

## Documentos vigentes

| Documento | Ruta canónica | Archivo de origen |
|---|---|---|
| 01. Requisitos | [01_Requisitos.md](01_Requisitos.md) | `01_Requisitos_v0.2.md` |
| 02. Casos de uso | [02_Casos_de_uso.md](02_Casos_de_uso.md) | `02_Casos_de_uso_v0.2.md` |
| 03. Modelo matemático | [modelo_matematico.md](modelo_matematico.md) | `03_Modelo_matematico_v0.2.md` |
| 04. Arquitectura | [04_Arquitectura.md](04_Arquitectura.md) | `04_Arquitectura_v0.2.md` |
| 05. Contratos | [contratos.md](contratos.md) | `05_Contratos_v0.2.md` |
| 06. Plan de pruebas | [plan_pruebas.md](plan_pruebas.md) | `06_Plan_de_pruebas_v0.2.md` |
| 07. Cronograma | [07_Cronograma.md](07_Cronograma.md) | `07_Cronograma_v0.2.md` |
| Anexo de datos | [Anexo_validacion_datos.md](Anexo_validacion_datos.md) | `Anexo_validacion_datos_v0.2.md` |
| Anexo de reconciliación | [Anexo_reconciliacion_H1.md](Anexo_reconciliacion_H1.md) | `Anexo_reconciliacion_H1.md` |
| Anexo de compatibilidad 3D | [Anexo_compatibilidad_3D.md](Anexo_compatibilidad_3D.md) | Evidencia local de H1 |
| Registro de decisiones | [decisiones/registro.md](decisiones/registro.md) | `03_Registro_de_decisiones_v1.9.md` |

Se conservan las rutas existentes de modelo matemático, contratos y plan de pruebas para evitar duplicidad y facilitar la reconciliación de la rama numérica. Esta elección ajusta únicamente la propuesta de nombres del anexo H1, no el alcance. Los nombres versionados y versiones anteriores citados en el registro identifican documentos históricos, no especificaciones activas adicionales. El historial Git conserva el contenido anterior de las tres rutas reemplazadas.

## Documentación de infraestructura conservada

- [Estándares de código](estandares_codigo.md)
- [Configuración de GitHub](CONFIGURAR_GITHUB.md)
- [Verificación inicial](VERIFICACION_INICIAL.md)
- [Pendientes](pendientes.md)
- [ADR-005](decisiones/ADR-005.md) y [ADR-006](decisiones/ADR-006.md)

El README raíz y los pendientes reflejan el alcance vigente. La configuración fundacional, la verificación inicial y el ADR-005 conservan su contenido histórico con notas de vigencia; ADR-006 mantiene la política de CI manual. Las aprobaciones y CI anteriores no validan la nueva funcionalidad. No integrar esta rama hasta completar contratos, pruebas y revisión.

Las fuentes originales del docente, datos médicos, ZIP y otros archivos de investigación quedan fuera de este paquete. No publicar datos de pacientes, secretos ni resultados sin autorización.
