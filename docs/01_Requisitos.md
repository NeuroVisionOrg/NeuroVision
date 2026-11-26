# NeuroVision — Especificación de requisitos de software (ERS)

**Versión:** 0.2 — línea base de requisitos aprobada por el líder; validaciones técnicas pendientes\
**Fecha:** 25 de noviembre de 2026\
**Alcance aprobado:** 2D + 3D; SOR como único solucionador numérico.\
**Repositorio:** https://github.com/NeuroVisionOrg/NeuroVision

## 1. Control de decisiones y fuentes

- D-01: el líder aprueba el alcance funcional 2D/3D y un único método numérico, SOR, de acuerdo con la aclaración del profesor que reportó. No se cuenta con una nueva cita textual del docente en este borrador.
- D-02: el líder aprueba la organización en siete documentos: requisitos, casos de uso, modelo matemático, arquitectura, contratos, plan de pruebas y cronograma. Los nombres son provisionales hasta reconciliarlos con los archivos existentes del repositorio.
- D-03: el líder acepta las propuestas de la ERS v0.1 el 25 de noviembre de 2026. Se conserva una exportación básica como parte del producto mínimo. Esta versión registra la conformidad del líder; no sustituye la revisión del equipo ni acredita una nueva aprobación docente.
- Se conservan las cinco capas, las responsabilidades, el plazo original y la infraestructura previa. Los resultados de CI iniciales no constituyen evidencia de segmentación funcional.
- Fuentes de partida: cuatro fotografías del enunciado/rúbrica original; `Transcripcion-audio.txt`; ficha de contexto, registro de decisiones y roles/cronograma v1.0; aprobación del líder en la conversación. Las fotografías mencionan los cuatro métodos originales; en ese punto prevalece la aclaración posterior reportada. Las anotaciones originales se conservan sin modificaciones.
- La rúbrica original contempla exportación de resultados numéricos (CSV o TXT), imágenes procesadas, gráficas de convergencia, manual de usuario, integración y contribuciones individuales. Aunque RF-14 se planteó como secundario en la lista inicial, se conserva una exportación mínima como obligatoria en esta línea base, de acuerdo con la conformidad del líder. Los formatos volumétricos y otras exportaciones avanzadas siguen pendientes. No se considera retirada esa exigencia docente.
- Random Walker, NIfTI, NiBabel, scikit-image, Three.js, Marching Cubes y los parámetros numéricos detallados son decisiones técnicas candidatas; no se registran como tecnologías ya incorporadas.

## 2. Planteamiento del problema

El proyecto académico requiere aplicar un método iterativo para resolver un sistema de ecuaciones lineales Ax=b en un problema práctico de procesamiento de imágenes. En una resonancia cerebral, los límites de una región tumoral de interés no se representan directamente como una máscara binaria. Una aplicación de segmentación asistida puede aprovechar indicaciones del usuario y relaciones espaciales entre intensidades para construir un sistema matemático cuya solución permita delimitar la región.

En dos dimensiones se dispone de píxeles de un corte; en tres dimensiones, de vóxeles de un volumen con geometría espacial. Un corte aislado no basta para inferir la forma anatómica real en profundidad. El problema se limita a segmentar una región seleccionada por el usuario, no a detectar, clasificar ni diagnosticar un tumor automáticamente.

## 3. Justificación

NeuroVision vincula el estudio de SOR con la resolución de sistemas lineales dispersos en imágenes médicas. La visualización de las máscaras y la reconstrucción de una superficie volumétrica permiten examinar el resultado del cálculo. Los experimentos controlados con omega, tolerancias y tamaños de ROI permiten estudiar convergencia, exactitud numérica y rendimiento. Las máscaras de referencia, cuando existan y sean compatibles, permiten evaluar el solapamiento de la segmentación sin atribuirle precisión clínica.

## 4. Objetivos

### Objetivo general

Desarrollar una aplicación web educativa para la segmentación asistida de regiones tumorales en resonancias magnéticas cerebrales 2D y 3D, mediante una implementación propia del método iterativo de sobrerrelajación sucesiva (SOR) para resolver sistemas lineales dispersos, que permita visualizar las regiones segmentadas y analizar el comportamiento numérico del método.

### Objetivos específicos

1. Preparar imágenes y volúmenes de resonancia, regiones de interés (ROI) y semillas, conservando la correspondencia entre coordenadas de visualización y datos.
2. Formular y validar un modelo matemático que transforme la segmentación asistida 2D/3D en sistemas lineales dispersos compatibles con SOR.
3. Implementar y verificar un único solucionador SOR, independiente de imágenes, HTTP y la interfaz, que informe convergencia, residuos, iteraciones y tiempo.
4. Reconstruir mapas de probabilidades, máscaras y contornos 2D, y máscaras volumétricas con visualización tridimensional de su superficie.
5. Evaluar el comportamiento de SOR mediante experimentos reproducibles, y la segmentación mediante referencias compatibles cuando estén disponibles.
6. Integrar y documentar el software respetando las cinco capas, los contratos y los controles de calidad existentes.

## 5. Alcance y exclusiones

| Elemento | Producto mínimo previsto |
|---|---|
| 2D | Carga de corte, visor, ROI, semillas de ambas clases, sistema Ax=b, SOR, máscara y contorno superpuesto. |
| 3D | Carga de volumen de una secuencia, visor de cortes axiales, ROI volumétrica, semillas, mismo SOR, máscara volumétrica y malla interactiva. |
| Común | Configuración y validación de SOR; estado de convergencia, historial de residuo, iteraciones/barridos y tiempo; comparación original/procesado; experimentación controlada. |
| Evaluación | Datos sintéticos primero; después casos de investigación autorizados. Dice/IoU únicamente con referencias compatibles. |
| Arquitectura | Cinco capas independientes; Control coordina Traducción, Métodos y Servicios. Contratos compartidos sin constituir una sexta capa. |

Fuera del alcance inicial: diagnóstico, detección automática, IA, entrenamiento de redes, otros solucionadores independientes, DICOM, autenticación, bases de datos persistentes, procesamiento masivo, reconstrucción anatómica desde un JPG aislado y edición avanzada de mallas. No se garantiza el procesamiento interactivo de un cerebro completo. Ambos modos son parte del alcance; se reducirán tamaños de ROI y funcionalidades secundarias antes de sacrificar el núcleo.

## 6. Actores

- Usuario académico: carga datos, delimita la región, marca semillas, configura SOR, ejecuta y consulta resultados. No se presupone un rol médico ni autenticación.
- Equipo de desarrollo: realiza pruebas, mantiene la aplicación y reproduce experimentos.
- Docente/evaluador: revisa resultados, evidencias, arquitectura y aportes del equipo; no requiere un perfil de software distinto.

## 7. Requisitos funcionales y criterios de aceptación

Prioridades: **O** = obligatorio para el núcleo; **A** = alta, prevista para evaluación. Los criterios son la línea base aceptada por el líder, con valores y decisiones técnicas pendientes donde se indica. No representan pruebas ejecutadas.

| ID | Prioridad | Requisito | Criterio de aceptación verificable |
|---|---|---|---|
| RF-01 | O | Cargar imágenes 2D. | Un archivo válido de los formatos aprobados se decodifica y visualiza con sus dimensiones correctas; uno corrupto o no admitido se rechaza con un error comprensible. |
| RF-02 | O | Cargar volúmenes 3D. | Un volumen de prueba válido se carga con dimensiones y geometría verificables; formatos, dimensiones o geometrías no admitidos se rechazan. NIfTI es el formato candidato. |
| RF-03 | O | Visualizar imágenes y navegar por cortes. | El visor muestra el corte seleccionado y permite recorrer los índices válidos; zoom y desplazamiento no alteran coordenadas de datos. |
| RF-04 | O | Delimitar una ROI 2D o 3D. | El sistema acepta una ROI no vacía dentro de los límites, conserva su origen y rechaza regiones inválidas o superiores al límite configurado. |
| RF-05 | O | Marcar semillas de primer plano y fondo. | Se registran posiciones en datos, no en pantalla; se exigen ambas clases, sin posiciones contradictorias y con al menos una incógnita. |
| RF-06 | O | Construir Ax=b. | En casos sintéticos, A y b tienen dimensiones coherentes, valores finitos, almacenamiento disperso y propiedades requeridas por el modelo; se rechazan componentes sin acceso a semillas. |
| RF-07 | O | Configurar y ejecutar SOR. | Ambos modos invocan la misma implementación propia; una prueba con solución conocida verifica exactitud. Se validan omega, tolerancias y máximo de iteraciones; se informa explícitamente si no converge. |
| RF-08 | O | Generar máscara y contorno 2D. | Tras convergencia, se reconstruyen probabilidades y máscara en las coordenadas correctas, se respetan las semillas y se muestra el resultado sobre el original. Fuera de la ROI no se afirma que se haya segmentado. |
| RF-09 | O | Generar máscara volumétrica. | Se reconstruye la máscara 3D con geometría y desplazamiento de ROI correctos y se pueden visualizar sus cortes. Se conservan las semillas. |
| RF-10 | O | Reconstruir y visualizar una superficie 3D. | Una máscara válida de prueba con geometría conocida produce una malla correspondiente, con orientación y escala verificadas; el usuario puede rotarla y acercarla. Los casos vacíos, degenerados o truncados se manejan explícitamente. |
| RF-11 | O | Mostrar resultados numéricos. | Cada ejecución informa estado, parámetros, iteraciones/barridos, residuos inicial/final e historial, tiempo del solver y gráfica de convergencia. Una ejecución fallida no se presenta como segmentación válida. |
| RF-12 | A | Comparar ejecuciones SOR. | Se pueden reproducir al menos dos ejecuciones con distintos omega, manteniendo constantes sistema, semillas, x0, tolerancias y condiciones de medición; se registran también los fallos. No exige un comparador interactivo avanzado. |
| RF-13 | A | Evaluar Dice e IoU. | Si existe una referencia compatible en geometría y semántica de etiquetas, se calculan métricas con casos de prueba de solapamiento conocido. Sin referencia se muestran como no disponibles. La referencia no genera la máscara evaluada. |
| RF-14 | O (mínimo) | Exportar resultados. | Una exportación mínima permite recuperar parámetros, historial y resultados numéricos en CSV o TXT, y una imagen procesada válida (en 3D, al menos un corte con su máscara superpuesta). Se verificará apertura y correspondencia de datos. No se exportará una máscara como válida ante no convergencia. Formato volumétrico, formato de imagen y exportaciones avanzadas por definir. |

## 8. Requisitos no funcionales y restricciones

| ID | Requisito | Evidencia esperada |
|---|---|---|
| RNF-01 | Modularidad: cinco capas, sin dependencia directa entre las tres capas especializadas ni entre interfaz y solver. | Import Linter, pruebas de arquitectura y revisión de APIs públicas. |
| RNF-02 | Corrección numérica: SOR propio; no delegar la resolución a un solver externo. | Pruebas con soluciones conocidas, residuos recalculados y casos inválidos. Solvers de referencia permitidos solo en verificación. |
| RNF-03 | Rendimiento: matrices CSR y ROI acotadas. | Benchmarks de tiempo y memoria con hardware identificado; límites de tamaño y tiempo se fijarán a partir de mediciones, no de promesas. |
| RNF-04 | Robustez: validar archivos, parámetros, tamaños y geometría; manejar fallos numéricos. | Casos negativos y estados de error controlados; límites de carga y descompresión por definir. |
| RNF-05 | Integridad geométrica: mantener ejes, orientación y transformación espacial. | Pruebas de recorte, correspondencia visor-datos y malla, con geometrías sintéticas conocidas. |
| RNF-06 | Privacidad y uso de datos: solo datos sintéticos o autorizados; no publicar datos médicos ni credenciales en GitHub. | Revisión de licencias, procedencia, archivos versionados y escaneo de secretos. |
| RNF-07 | Reproducibilidad: registrar configuración, identificador no sensible del caso, ROI, semillas, condiciones experimentales y versión del código. | Repetición documentada de experimentos; dependencias bloqueadas. |
| RNF-08 | Calidad: conservar stack y controles de calidad, sin debilitarlos para aprobar CI. | CI manual completo desde develop para el candidato final; revisión de SHA de base y head, pruebas y registro de integración. |
| RNF-09 | Usabilidad: interacción clara y retroalimentación del estado del proceso. | Demostración de carga, selección, ejecución, resultados y errores; etiquetas que eviten interpretar el producto como diagnóstico. |
| RNF-10 | Trazabilidad académica: contribución individual continua y documentada. | Historial de commits por responsable, PR revisados, manual de usuario y documentación reproducible; no concentrar commits al final. |

## 9. Casos de uso iniciales

| ID | Caso de uso | Requisitos relacionados |
|---|---|---|
| CU-01 | Segmentar un corte 2D | RF-01, 03–08, 11 |
| CU-02 | Segmentar una región volumétrica y visualizarla | RF-02–07, 09–11 |
| CU-03 | Configurar y evaluar el comportamiento de SOR | RF-07, 11–12 |
| CU-04 | Evaluar contra una referencia compatible | RF-13 |
| CU-05 | Exportar resultados de una ejecución | RF-14 |

Los flujos principales, alternativos, precondiciones y postcondiciones se detallarán en `02_Casos_de_uso.md`.

## 10. Criterios de salida del producto mínimo

1. Un mismo solver SOR resuelve un caso lineal pequeño de solución conocida y reporta estados coherentes, incluido el caso de no convergencia.
2. Se demuestra el flujo 2D completo en un caso sintético y un caso de investigación autorizado, sujeto a disponibilidad de datos.
3. Se demuestra el flujo 3D completo en un volumen sintético y una ROI de un caso de investigación autorizado, sujeto a disponibilidad de datos. La malla proviene de la máscara obtenida por SOR.
4. La reconstrucción conserva coordenadas y geometría; los datos no procesados y los fallos se distinguen de resultados válidos.
5. Se reproducen experimentos de omega/tamaño y se documentan resultados y limitaciones, sin inventar valores.
6. Se verifica la arquitectura, las pruebas esenciales, la documentación de uso y el CI completo del candidato. Se verifica la exportación mínima de RF-14; las exportaciones adicionales quedan sujetas a revisión de la rúbrica y viabilidad.

## 11. Decisiones técnicas pendientes y dependencias

| Tema | Decisión por cerrar |
|---|---|
| Datos | BRISC para 2D e ITK-SNAP/MSD para 3D como candidatos: comprobar licencia, formato, etiquetas, modalidad, privacidad y geometría. |
| Modelo | Validar Random Walker binario en grafos de cuatro/seis vecinos, frontera de ROI, conectividad, pesos positivos simétricos y matriz SPD; justificar elección. |
| SOR | Estudiar omega en (0,2), tolerancias, máximo de iteraciones y aproximación inicial. Criterio candidato: norma 2 del residuo <= max(atol, rtol*norma 2 de b); valores heredados rtol=1e-6, atol=1e-10, max_iterations=2000 son provisionales. |
| Geometría | Convención de ejes, transformación afín, unidades, anisotropía y tratamiento de máscara en borde de ROI. |
| Librerías | Evaluar NiBabel, scikit-image y Three.js; no instaladas por este documento. La indicación original de independencia de librerías del método debe respetarse en el sentido de implementar la matemática de SOR; confirmar si el docente impone restricciones adicionales sobre NumPy/SciPy como soporte de datos. |
| Límites | Tamaños de archivo, ROI, presupuesto temporal/memoria, tolerancias y aceptación cuantitativa de segmentación, según datos y experimentos. |
| Gestión | Confirmar horas restantes, CODEOWNERS, Jira, invitaciones del equipo y del docente, y la membresía exclusiva del equipo autorizado para bypass de PR. |

## 12. Responsables y siguiente paso

Se mantienen Johan (Interfaz), Jherson (Control), Yenderson (Traducción y Servicios) y Jennifer (Métodos Numéricos). Todos colaboran en pruebas, revisión y documentación. El presupuesto de 80 horas-persona fue provisional; no representa el tiempo restante.

Compartir esta línea base con el equipo para revisión. Documentar casos de uso y validar el modelo matemático y los datos; acordar arquitectura y contratos antes de implementar. Registrar las decisiones aprobadas y preparar el PR de alineación hacia develop. Este documento no modifica el repositorio ni crea tareas en Jira.
