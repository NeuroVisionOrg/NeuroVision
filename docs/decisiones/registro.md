# Registro de decisiones y estado de partida
Versión 1.9 | 26 de noviembre de 2026

## Decisiones vigentes
| Decisión | Estado | Fundamento |
|---|---|---|
| SOR como único solver obligatorio | Confirmada por el líder | Nueva indicación del profesor reportada en la conversación |
| Modos 2D y 3D | Confirmada por el líder | Alcance actualizado del proyecto |
| Intensidad escalar, escala de grises | Confirmada por el líder (D-06) | Evitar procesamiento multicanal; preservar niveles de gris |
| Cuatro integrantes y cinco capas | Se conserva | Acuerdo previo del equipo |
| Mantener repositorio e infraestructura | Se conserva | Avances técnicos ya verificados |
| Random Walker binario 2D/3D | Línea base de diseño aceptada por el líder (D-05) | Fundamento teórico condicionado; validación en datos reales y decisiones detalladas pendientes |
| NiBabel, scikit-image y Three.js | Candidatas | Evaluar antes de instalar y bloquear versiones |
| NIfTI y visor axial inicial para 3D | Propuesta | Verificar dataset y viabilidad |
| 80 horas-persona | Supuesto provisional | Confirmar horas consumidas y restantes |
| Arquitectura A-01 a A-07 | Aprobada como línea base de diseño por el líder (D-08) | Mantener validaciones, dependencias candidatas y decisiones detalladas pendientes |
| Contratos C-01 a C-09 | Aprobados como línea base de diseño por el líder (D-09) | Revisiones individuales, detalles abiertos y pruebas pendientes |
| Plan de pruebas | Línea base de verificación aceptada por el líder (D-10) | Conformidad interpretada al solicitar continuar; casos aún no ejecutados |
| Cronograma y backlog | Línea base v0.2 aprobada por el líder (D-11) | Estimación optimista de 65 h restantes necesarias (57 de trabajo + 8 de reserva); no saldo confirmado |

## Aprobaciones de ingeniería de requisitos (25 de noviembre de 2026)
- D-01: alcance funcional 2D y 3D con SOR como único solucionador, aprobado por el líder. La restricción a SOR procede de la indicación del profesor comunicada por el líder.
- D-02: organización de la documentación en siete documentos técnicos, aprobada por el líder. Sus rutas se reconciliarán con las existentes al preparar el PR de alineación.
- D-03: el líder manifiesta su conformidad con las propuestas de la ERS v0.1. Se adopta como línea base de planificación; se conserva una exportación básica de resultados numéricos (CSV o TXT) e imagen procesada. La exportación avanzada y los formatos volumétricos quedan por decidir. Se registra esta interpretación de la aprobación como decisión del líder, no como una nueva cita del profesor ni como aprobación individual de todos los integrantes.
- Continúan pendientes la validación del modelo, la inspección de los datos y licencias, los parámetros y límites de rendimiento, el tratamiento de geometría, la compatibilidad de dependencias, las posibles restricciones adicionales del docente sobre librerías y las horas restantes.

## Aprobación de casos de uso y análisis matemático (25 de noviembre de 2026)
- D-04: el líder manifiesta su conformidad con los cinco casos de uso y la continuación al modelo matemático. Se registra `02_Casos_de_uso_v0.2.md` como línea base funcional aprobada por el líder, conservando los flujos, prioridades y criterios de aceptación. No equivale a una nueva aprobación del profesor ni a una revisión individual de cada integrante.
- Se prepara `03_Modelo_matematico.md` v0.1 para revisión. Random Walker binario continúa como candidato técnico, con justificación de SPD bajo condiciones de conectividad y pesos positivos simétricos, y convergencia teórica de SOR para 0 < omega < 2. Se ejecutó una comprobación exploratoria sobre dos sistemas sintéticos de 2 y 8 incógnitas (12 ejecuciones convergentes y dos pruebas de límite de una iteración), fuera del repositorio; no son pruebas del producto ni benchmarks de tiempo/memoria. Las decisiones de normalización, anisotropía, parámetros, geometría, umbral y límites siguen pendientes de validación y aprobación.
- Próximo paso tras revisar el modelo: inspeccionar los datos 2D/3D y concretar arquitectura y contratos. No se reinicia el plazo ni se introducen cambios en GitHub o Jira.

## Conformidad con el enfoque matemático y datos (D-05)
- El líder manifestó su conformidad con lo planteado en el análisis matemático y pidió continuar. Se interpreta como aceptación del enfoque general Random Walker binario (4/6 vecinos), SOR propio único y CSR. Se registra `03_Modelo_matematico_v0.2.md` como línea base de diseño condicionada. No se atribuye al profesor ni a los demás integrantes una aprobación no documentada.
- No se fijan beta, omega, normalización, anisotropía, límites de ROI, tolerancias definitivas, semántica de etiquetas ni formatos definitivos. La reconstrucción con Marching Cubes y sus dependencias requieren verificación.
- Selección de datos propuesta: sintéticos para verificación, BRISC para 2D, ITK-SNAP Brain Tumor para piloto 3D y MSD Task01 como ampliación o alternativa. Se verificaron descripciones y páginas públicas de distribución; no se inspeccionaron imágenes ni volúmenes reales en esta sesión. La descarga del ZIP de ITK-SNAP falló en el entorno de análisis. El archivo `.crdownload` adjunto tiene cabecera PDF y no constituye un volumen verificable.
- `Anexo_validacion_datos.md` documenta fuentes, condiciones pendientes, protocolo de inspección y propuestas de entrada. Es un anexo de trabajo, no un octavo documento principal ni una aprobación de datos. Solicitar el archivo de ejemplo 3D y un par imagen/máscara 2D autorizado; no publicar datos médicos en GitHub. A continuación concretar arquitectura y contratos sin cerrar supuestos de geometría no verificados.

## Restricción a escala de grises e inspección efectiva de datos (D-06)
- El líder confirma que el procesamiento de imágenes se limitará a escala de grises para reducir complejidad. Se registra una única intensidad por píxel/vóxel, una modalidad por ejecución, sin segmentación RGB ni fusión multimodal. No equivale a una conversión binaria de la resonancia. El color que pudiera emplearse para presentar semillas, contornos o malla no forma parte del modelo matemático.
- Se inspeccionaron los ZIP aportados. BRISC: 4.793 pares JPEG/PNG de segmentación, dimensiones coincidentes en todos, 2.866 JPEG L y 1.927 JPEG RGB acromáticos (canales idénticos verificados en todos); máscaras con valores 0–10 y 246–255. No se detectaron errores de decodificación en la tarea de segmentación. La propuesta es admitir L o RGB acromático y binarizar las referencias BRISC mediante umbral >=128.
- ITK-SNAP: cinco archivos MHA útiles del caso BRATS_HG0015, cuatro modalidades escalares y una referencia multietiqueta, forma XYZ 160×216×176, int16, geometría de cabecera coincidente, espaciado 1×1×1. Etiquetas 0 (fondo), 1 (edema) y 2 (tumor activo), según la máscara y la tabla LabelTable. Se propone T1C y evaluación de etiqueta 2, aún por aprobar.
- La v0.2 del anexo reemplaza la descripción anterior de datos no disponibles. Quedan pendientes las licencias exactas, conversión de MHA a NIfTI y verificación geométrica/visual, rendimiento y pruebas integrales. NIfTI continúa como candidato de entrada; no se aprueba añadir lector MHA al producto. No se deduce que SOR segmente correctamente las imágenes reales. Los resultados detallados y hashes están en `Anexo_validacion_datos_v0.2.md`.
- Siguiente documento: `04_Arquitectura.md`, seguido de los contratos; no cerrar los supuestos de orientación/espaciamiento ni admitir datos reales sin las verificaciones pendientes. No se cambia el repositorio ni se instalan dependencias.

## Conformidad con el piloto de datos y propuesta de arquitectura (25 de noviembre de 2026)
- D-07: el líder expresa conformidad con la inspección de datos y solicita continuar. Se interpreta como aceptación condicionada del piloto BRISC 2D e ITK-SNAP 3D con una única secuencia T1C y evaluación de la etiqueta 2 (tumor activo), manteniendo escala de grises. No equivale a admisión definitiva: las licencias específicas, conversión MHA a NIfTI, orientación, unidades y alineación visual siguen pendientes. La referencia no se usa para construir el resultado evaluado. Si la conversión no supera la verificación, mantener pruebas sintéticas y estudiar una alternativa autorizada; no incorporar MHA al MVP sin acuerdo.
- Se verificó nuevamente `develop` en el repositorio GitHub: HEAD `3f9d65c34d868721876e4a8308dd2e55153dc632`, rama protegida. Se revisó el árbol, contratos de imagen/sistema/solver/resultados, validaciones de Control, DTO TypeScript y prueba de dependencias. El esqueleto conserva contratos 2D y menciones a cuatro métodos. No hay evidencia de nuevas implementaciones ni se ejecutó CI en esta revisión.
- Se prepara `04_Arquitectura.md` v0.1 para revisión. Se mantienen las cinco capas y sus responsables, con Control como único coordinador por APIs públicas, contratos compartidos y un SOR independiente reutilizado en 2D/3D. Se propone una sesión en memoria del navegador, backend sin persistencia, previsualización acotada y reenvío del original para segmentar; el coste, los formatos, la identidad y límites requieren validación y diseño de contratos. No se aprueba automáticamente ninguna caché, dependencia ni ruta HTTP nueva.
- La arquitectura y sus decisiones A-01 a A-07 están pendientes de revisión del líder. Se conserva como siguiente documento `05_Contratos.md`. Las decisiones previas se mantienen como historial; la inspección de datos v0.2 sustituye los estados anteriores en que no estaban disponibles. No se han modificado GitHub, fuentes activas, Jira ni responsabilidades.

## Aprobación de arquitectura y diseño de contratos (25 de noviembre de 2026)
- D-08: el líder expresa conformidad con la arquitectura propuesta A-01 a A-07. Se adopta `04_Arquitectura_v0.2.md` como línea base de diseño: cinco capas, Control coordinador por APIs públicas, un SOR, sesión en navegador, backend sin persistencia, solicitudes síncronas, NIfTI/visor axial inicial condicionados, servicios separados y las tres dependencias candidatas. No equivale a aprobación del profesor, revisión individual de todos los integrantes ni comprobación de rendimiento/compatibilidad.
- La observación del líder de que no debemos preocuparnos por memoria se interpreta como que la RAM no es una restricción prioritaria, sin datos de capacidad o benchmark. Mantener CSR y límites verificables de carga, ROI, tiempos, iteraciones, concurrencia y respuesta; no asumir recursos ilimitados ni reiniciar presupuesto.
- Se prepara `05_Contratos.md` v0.1 para revisión: C-01 a C-09, coordenadas y tipos escalares, dominio RAS+ inicial restringido, preparación, CSR y contexto de reconstrucción, un `resolver_sor` independiente, diagnóstico de fallos con residuos ausentes cuando no disponibles, malla/servicios, API HTTP con DTO versión 2 y Base64 para arrays, snapshots de sesión y códigos de error. Son propuestas detalladas aún no aprobadas ni implementadas. El snapshot reenviado no certifica autenticidad y el formato se validará con pruebas de recursos. Se mantiene la exportación CSV/PNG básica y la referencia exclusivamente para evaluación.
- Pendientes: validaciones geométricas, anisotropía, parámetros/márgenes y límites, licencia/conversión de datos, compatibilidad de dependencias, revisión de contratos por equipo y horas restantes. Siguiente documento: `06_Plan_de_pruebas.md`, tras revisar los contratos. No se ha modificado GitHub, Jira, fuentes activas ni dependencias; no se ha ejecutado CI ni implementado SOR. El estado pendiente de aprobación de arquitectura de v1.5 queda superado por D-08.

## Aprobación de contratos y propuesta de verificación (D-09)
- El líder expresa conformidad con los contratos y solicita continuar. Se adopta `05_Contratos_v0.2.md` como línea base de diseño: tipos internos escalares, coordenadas y dominio de trabajo, SOR único con CSR, errores/diagnóstico, reconstrucción y servicios, DTO HTTP versión 2, identidad de sistema y sesión sin persistencia. Esto supera el estado anterior de propuesta pendiente de aprobación del líder; no equivale a revisión por cada integrante, nueva aprobación docente ni validación operativa.
- Se prepara `06_Plan_de_pruebas.md` v0.1 para aprobación. Incluye trazabilidad RF-01–14, RNF-01–10, CU-01–05, RC-01–10 y C-01–09, oráculos sintéticos, pruebas por capa, integración 2D/3D, admisión de datos, rendimiento, aceptación y CI. Las prioridades y fixtures adicionales son propuestas para revisión; no se ejecutaron estas pruebas ni se obtuvo un nuevo resultado de CI.
- Mantener pendientes licencias, conversión y geometría de datos, dependencias, parámetros y límites, revisión individual de contratos y horas restantes. Continuar con `07_Cronograma.md` tras aprobar el plan. Conservar autoría, responsabilidades y plazo, no reiniciar las 80 horas. No modificar GitHub, Jira, fuentes activas, archivos originales ni código por esta fase documental.

## Aprobación del plan de pruebas y propuesta de cronograma (D-10)
- El líder manifiesta conformidad al indicar «Excelente» y solicitar continuar después del documento 06. Se interpreta como aceptación del plan de pruebas para planificación y se registra `06_Plan_de_pruebas_v0.2.md` como línea base, sin afirmar ejecución, aprobación individual del equipo ni nueva autorización docente.
- Se prepara `07_Cronograma.md` v0.1. Estimación optimista propuesta: Jherson 16 h, Johan 17 h, Yenderson 19 h, Jennifer 13 h (65 h-persona, de las cuales 8 h de reserva). Los saldos individuales, horas previas y fecha de entrega deben confirmarse; las 80 h originales no se reinician. Las tareas, identificadores locales, ramas, hitos y horas son propuestas, no tickets Jira ni compromisos efectivos.
- Mantener ambas dimensiones obligatorias, SOR único, exportación básica, calidad y responsabilidades acordadas. Priorizar pruebas sintéticas, integración 2D y 3D, después experimentación real autorizada. Si no cabe el esfuerzo, recortar extras y negociar con el equipo/docente, no esconder incumplimientos. Próximo paso: confirmar cronograma, revisión de contratos por responsables y PR de alineación, verificación de accesos/CODEOWNERS/Jira y dependencias.
- No se modifica el repositorio, las fuentes activas ni Jira; no se añaden resultados de pruebas ni dependencias instaladas.

## Infraestructura verificada previamente
- PR #1 integrado en develop: merge 3f9d65c34d868721876e4a8308dd2e55153dc632. CI completo: https://github.com/NeuroVisionOrg/NeuroVision/actions/runs/45405678530
- PR #2 integrado en main: merge 7062533e9f15d697ffc5d42a68968b997ec82c3d. CI completo: https://github.com/NeuroVisionOrg/NeuroVision/actions/runs/45410287420
- En la validación inicial se registraron 26 pruebas locales aprobadas (24 Python, 2 TypeScript), 3 contratos de Import Linter respetados, una prueba negativa arquitectónica, 0 hallazgos del escaneo de secretos y 6 jobs remotos aprobados por CI. Estos resultados pertenecen a la base anterior, no a SOR ni a segmentación 3D implementados.
- Develop se configuró como rama predeterminada. Ambas ramas protegidas. Excepción de equipo solo para PR verificada anteriormente; membresía exclusiva del líder pendiente de confirmar. No consta aprobación externa del PR #1.
- Lockfiles y baseline presentes; hooks locales validados en el entorno del líder. Advertencia de HTTPX/Starlette pendiente de evaluar.
- CODEOWNERS con responsables individuales y Jira no confirmados.

## Migración propuesta
1. Actualizar requisitos y criterios de aceptación, incluido el uso de SOR en ambos modos.
2. Verificar datos 2D/3D, modelo matemático, condiciones de convergencia, ROI y rendimiento.
3. Conservar LinearSystem, SolverConfig/SolverResult con adaptaciones a SOR y contratos 2D que sigan siendo pertinentes. Diseñar contratos volumétricos y de mallas sin duplicar el solver. Acordar coordenadas e interfaces HTTP.
4. Preparar PR de alineación (rama sugerida chore/align-2d-3d-sor-scope) para actualizar README, ADR, modelo, contratos, pendientes y pruebas afectadas. No modificar el historial ni eliminar código sin revisarlo.
5. Incorporar nuevas dependencias mediante PR revisado; actualizar locks y ejecutar CI completo. Distribuir tareas solo con contratos acordados.

No hay evidencia aquí de que se haya implementado el solver SOR, el constructor de sistemas real o la reconstrucción 3D. Este registro describe el estado previamente verificado y las decisiones de alcance, no una auditoría remota nueva.

## D-11 — Aprobación del cronograma y verificación de avances (26 de noviembre de 2026)

- El líder aprueba expresamente la propuesta de cronograma. Se adopta `07_Cronograma_v0.2.md` como línea base, no como compromiso de horas ni aprobación de cada integrante. Confirmar saldos y fecha de entrega; reestimar después de reconciliar los avances.
- Revisión remota de solo lectura: `develop` predeterminada y protegida, HEAD `3f9d65c34d868721876e4a8308dd2e55153dc632`; `main` protegida, HEAD `7062533e9f15d697ffc5d42a68968b997ec82c3d`. CI oficial PR #1 y #2 exitoso; sin ejecución encontrada para PR #3 en la consulta de los últimos diez workflow_dispatch desde develop.
- PR #3 abierto: `feat/interfaz-visor-3d` (`bd941ed608889e643f20e47c47cabe5b37d321ea`), autor GitHub `Jb20201204`. Contiene UI útil, solver Random Walker de cuatro métodos y métricas en TypeScript; no integrar así.
- `feature/datos-conversion` (`49ab984720cbef8de03f5c8af10285c5a50c82f6`), cuatro commits adicionales, autor asociado `yendersonedwin-cloud`: lector 2D y pruebas. Ajustar RGB acromático, normalización por ROI y ubicación de pruebas para CI.
- `feature/modelo-3d-sor` (`0fe740dd22c37a0a0fef8fa37637829c2bc17ccb`), cinco commits adicionales, autor asociado `jdosorio-dev`: documentos, ADR-007, criterio de residuo y fixtures/pruebas 3D. Reconciliar entrada NIfTI, ambos modos, contrato SOR único y ordenamiento; no afirmar que existe el solver definitivo.
- Identidades GitHub observadas en commits/PR; confirmar su asociación con cada integrante y permisos antes de actualizar CODEOWNERS. No se ha verificado la membresía exclusiva del bypass ni el estado de Jira.
- Se prepara `Anexo_reconciliacion_H1.md`, guía de integración y revisión, no aprobación de ramas. Conservar autorías, no ejecutar merge ni modificar remoto sin el procedimiento establecido. No se han ejecutado pruebas nuevas, instalado dependencias ni modificado GitHub/Jira. Los estados históricos anteriores se complementan con esta auditoría de ramas.

## Nota de incorporación documental H1

La rama local de alineación se creó correctamente desde `3f9d65c`, según la salida de Git aportada por el líder. Los archivos aprobados se preparan para incorporarse con rutas canónicas en `docs/`, detalladas en [el índice](../README.md). Los nombres históricos de los documentos en este registro se conservan. No se acredita todavía incorporación local, commit, push, CI ni modificación remota.

## Ajustes editoriales durante H1 (26 de noviembre de 2026)

- Se corrige la ruta de disponibilidad documentada a `GET /api/v1/health`, verificada en `capa_2_control/api/app.py`, `health.py` y `tests/integration/test_health.py` de la base `3f9d65c34d868721876e4a8308dd2e55153dc632`. No se modifica el endpoint ni se introduce una decisión funcional nueva.
- Se eliminan espacios finales de Markdown preservando saltos de línea explícitos. Se actualiza el README raíz y los pendientes; se añaden notas de vigencia a los antecedentes de infraestructura y ADR-005/006. Se reserva ADR-007 para reconciliar la propuesta de la rama numérica, sin asignar una aprobación inexistente.


## Evidencia local de alineación H1 (26 de noviembre de 2026)

- El líder aporta salidas de terminal de la rama local `chore/align-2d-3d-sor-scope`: documentación incorporada, contratos internos adaptados a SOR y ambos modos, contratos TypeScript v2 y dependencias 3D instaladas con lockfiles actualizados.
- Antes del cierre arquitectónico se registran 215 pruebas unitarias/de arquitectura de Python y 3 pruebas Vitest aprobadas, Ruff y mypy del código del proyecto sin errores, 3 reglas Import Linter respetadas y compilación frontend correcta. No se acredita aún CI completo ni ejecución oficial para H1.
- Se documenta la evaluación de dependencias en [Anexo_compatibilidad_3D.md](../Anexo_compatibilidad_3D.md), incluidas advertencias de deprecación y el diagnóstico adicional de mypy no aprobado. No se modifica el alcance ni se relajan controles.
- Para el cierre de H1 se incorporan restricciones de importación de NiBabel y scikit-image por responsabilidad de capa. La validación de estas nuevas reglas y la revisión por los responsables están pendientes; no se acredita un nuevo resultado de CI con esta modificación.
