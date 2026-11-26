# NeuroVision — Plan de pruebas 2D + 3D / SOR

**Versión:** 0.2 — línea base de verificación aceptada por el líder\
**Fecha de actualización:** 26 de noviembre de 2026\
**Estado:** conformidad del líder interpretada a partir de su solicitud de continuar; pendiente revisión de responsables y ejecución sobre el producto.\
**Alcance:** requisitos aprobados, Random Walker binario 4/6 vecinos, intensidad escalar, SOR propio único y arquitectura de cinco capas.

## 1. Propósito y fuentes de control

Verificar corrección matemática, integración y funcionamiento observable, con trazabilidad de RF-01–14, RNF-01–10, CU-01–05, RC-01–10 y contratos C-01–09. Fuentes: `01_Requisitos.md`, `02_Casos_de_uso.md`, `modelo_matematico.md`, `Anexo_validacion_datos.md`, `04_Arquitectura.md`, `contratos.md` y registro de decisiones v1.7. Se conserva la autoría y responsabilidades de los cuatro integrantes. Este plan sustituirá, tras PR de alineación y revisión de responsables, el alcance anterior de `docs/plan_pruebas.md` referido a cuatro métodos; no reemplaza pruebas útiles sin revisión.

**Evidencia anterior, no repetida aquí.** La base anterior registró 26 pruebas locales aprobadas (24 Python, 2 TypeScript), tres contratos de Import Linter respetados y una prueba negativa de arquitectura; CI completo de los PR #1 y #2. Los ejemplos matemáticos exploratorios de `modelo_matematico.md` son cálculos independientes con dos sistemas pequeños, no pruebas del solver definitivo. La inspección de ZIP confirmó características de BRISC e ITK-SNAP, no calidad de segmentación. No se ha ejecutado ningún caso nuevo del presente plan ni un nuevo CI.

## 2. Estrategia, prioridades y herramientas

| Nivel | Evidencia | Herramienta o procedimiento |
|---|---|---|
| Unitario | Funciones y errores aislados, geometría, álgebra, servicios | pytest / Vitest |
| Contratos | Invariantes de tipos, formas, estados, validación de DTO, serialización | pytest / Vitest / Pydantic |
| Arquitectura | Dependencias permitidas y prohibidas, un único SOR | Import Linter, AST, revisión de código |
| Integración | HTTP y secuencia real de capas; fallos aislados por mocks | pytest / HTTPX; fixtures sintéticos |
| Aceptación | CU completos en navegador; resultados, errores, exportaciones | Guion manual reproducible, capturas autorizadas |
| Experimentos | Exactitud, omega, escalamiento, recursos | Temporizador monotónico, medición documentada de memoria; no requiere añadir framework |
| Calidad | Formato, tipado estricto, construcción y seguridad | Ruff, mypy, scipy-stubs, ESLint, Prettier, TypeScript/Vite, pre-commit, detect-secrets, pip check, lockfiles |

P0: puerta de integración del componente y del núcleo de ambos modos. P1: evidencia previa a entrega, incluida evaluación y experimentación (RF-12/13 de prioridad alta). P2: extensiones fuera del producto mínimo, solo si sobra tiempo y hay autorización. No relegar el modo 3D, exportación básica o controles esenciales a P2. Todo caso abajo empieza **pendiente**; los datos reales están bloqueados hasta su admisión. Una fila puede agrupar subcasos parametrizados, no equivale a un número de funciones de prueba ni a cobertura ejecutada.

Usar valores exactos en índices, etiquetas, formas, estados y conteos; para floats usar tolerancias explícitas y justificadas. Recalcular residuos independientemente del solver. Separar pruebas de interfaz con dobles de contrato de las integraciones con componentes reales. Las primeras no demuestran segmentación. No usar `xfail` o `skip` para ocultar requisitos incumplidos; un bloqueo documentado no es una aprobación.

## 3. Datos de prueba reproducibles y oráculos

| ID | Fixture y construcción propuesta | Resultado u oráculo |
|---|---|---|
| FX-01 | 2x2 uniforme, semillas externas (x,y)=(0,0) fondo y (1,0) primer plano, incógnitas fila inferior en orden C; beta=0. | A=[[2,-1],[-1,2]], b=[0,1], x*=[1/3,2/3]. P=[[0,1],[1/3,2/3]], máscara [[0,1],[0,1]] para umbral 0.5. SPD: eigenvalores 1 y 3. |
| FX-02 | Volumen (4,2,2), planos i=0 y 3 sembrados fondo/primer plano respectivamente; g=0 en i=0,1 y g=1 en i=2,3; beta=ln(4), espaciado isotrópico. | Ocho incógnitas; matriz por bloques de la sección 8.2 del modelo (diagonal 13/4, vecinos intraplano -1, entre planos -1/4), b=(0,0,0,0,1,1,1,1). x*=1/6 en i=1, 5/6 en i=2; máscara 0 en i=0,1 y 1 en i=2,3. Toca frontera: no es prueba de malla cerrada. |
| FX-03 | Imagen h=80,w=120 con patrón asimétrico y ROI x=[20,60),y=[10,50). Semilla (34,25). | Local (14,15), índice plano C=614; zoom/pan reversible; máscara de forma (40,40) superpuesta con origen correcto. |
| FX-04 | Volumen no cúbico con patrón de coordenadas y afín ortogonal isotrópica de ejes permutados/invertidos, traslación no nula y unidades mm; ROI i=[10,14),j=[20,25),k=[30,36) dentro del dominio de trabajo; semilla (12,23,34). | Local (2,3,4), índice plano C=82; H_work=H_original@T_work_to_original, coordenadas físicas iguales antes/después. Vista axial `volume[:,:,k].T`. Probar límites exclusivos y transformaciones inversas. |
| FX-05 | Fantoma escalar 8x8x8, bloque interior [2,6)^3 de intensidad 1 y exterior 0; todas las caras externas sembradas fondo, una o más semillas interiores fijas foreground; beta=ln(100), umbral 0.5, configuración experimental explícita. Crear también 16^3 escalado. | El sistema conserva semillas y alcanza una solución contrastable con referencia lineal independiente. Si converge, máscara no vacía con frontera exterior de fondo, malla procedente de esa máscara. La máscara geométrica conocida sirve para medir, no garantiza Dice=1 ni se usa para fabricar resultado. Las semillas del fantoma se fijan por construcción, no por referencia médica. |
| FX-06 | Máscara sintética aislada con bloque interior [2,5)x[3,6)x[1,4) en un dominio de forma (8,9,7); origen ROI (10,20,30), H_work con B=2I mm y traslación (5,-7,11) mm. | Extremos locales de superficie a nivel 0.5: [1.5,4.5]x[2.5,5.5]x[0.5,3.5]; extremos RAS+ físicos [28,34]x[38,44]x[72,78] mm. El cálculo incluye recorte y espaciado una sola vez. Usar geometría interior también para probar normales/orientación; no comparar una lista exacta de triángulos dependiente de versión. |
| FX-07 | Variantes inválidas: color real, archivo truncado, 4D, afines singulares/ambiguas, anisotropía, geometría/forma incompatible, semillas duplicadas o sin clases, ROI vacía, grafo desconectado, pesos no positivos, máscara vacía/llena y objeto truncado. | Rechazo tipado o resultado parcial/no disponible según contrato, nunca un éxito fingido. |
| FX-08 | Máscaras pequeñas binarias con conteos predeterminados: TP=2, FP=1, FN=1; idénticas no vacías; disjuntas; una vacía; ambas vacías. | Dice=2/3 e IoU=1/2 en primer caso; idénticas=1/1, disjuntas o una vacía=0/0, ambas vacías=None/None. |
| FX-09 | Pares BRISC autorizados, independientes de la selección de semillas; política BRISC_BIN_128. | Misma identidad documentada, dimensiones/orientación compatibles; referencia >=128. Dice/IoU medidos dentro de ROI, sin umbral clínico inventado. |
| FX-10 | ITK-SNAP T1C y truth del caso inspeccionado, convertidos fuera del producto a NIfTI escalar, referencia ITKSNAP_LABEL_2. | Preservar voxeles, intensidad, etiquetas discretas, afín/espaciado y correspondencia espacial. Probar solo tras admisión; no utilizar MHA como nuevo formato de producto. |

FX-01/02 tienen solución analítica. Para exactitud del solver en estos casos usar x0=0, rtol=1e-6, atol=1e-10, max_iterations=2000 y omega=1.2 como parámetros **de prueba**, no defaults de producción. Exigir ||b−Ax||₂ <= tau y error infinito <=1e-6 respecto de x* en estos dos fixtures; registrar tau (1e-6 y 2e-6). No exigir los recuentos exactos de los ensayos exploratorios como criterio universal. Para otros sistemas pequeños se permite solución de referencia independiente (p. ej. NumPy/SciPy en tests únicamente) y comparación con tolerancia derivada de la escala y el condicionamiento, acordada antes de ejecutar. No asumir que un residuo pequeño implica error pequeño para toda A, ni que la convergencia garantiza segmentación correcta. Evitar matrices densas grandes, incluso en verificación.

## 4. Matriz de pruebas por capa

### 4.1. Interfaz — Johan

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| UI-01 | P0 | Cargar PNG/JPEG y mostrar dimensiones decodificadas; volumen con cortes válidos, primero/último y fuera de rango controlado. Formas no cuadradas/cúbicas detectan transposición. | RF-01/02/03, CU-01/02 |
| UI-02 | P0 | FX-03/04: zoom, pan y cambio de corte; convertir pantalla→datos→pantalla, ROI exclusiva y semilla con índices exactos. Rechazar posiciones fuera de ROI. | RF-03/04/05, RNF-05, RC-02/03 |
| UI-03 | P0 | Dos clases, editar/quitar semillas sin duplicar posiciones, semilla 3D conserva k tras cambiar corte. Validar omega/tolerancias/iteraciones antes del envío; no selector de cuatro métodos. | RF-05/07, CU-01–03, RC-03/04 |
| UI-04 | P0 | Mostrar original, máscara/contorno y desplazamiento en 2D, cortes de máscara 3D; exterior ROI indicado como no evaluado. Malla con escala/proporciones conservadas, rotación/zoom; parcial identificado. | RF-08/09/10, RNF-05/09, RC-08 |
| UI-05 | P0 | Estados loading/error/convergencia; MAX_ITERATIONS, NUMERICAL_FAILURE, reconstrucción o malla fallida y gráfica indisponible separados. No renderizar máscara inválida; conservar diagnóstico disponible. | RF-07/11, CU-01–03, RC-06/07 |
| UI-06 | P0 | Respuesta obsoleta: cambiar archivo/ROI/semillas/parámetros durante solicitud y devolver respuesta antigua; usar request_id, no sustituir la vista actual. Cambiar caso libera datos de sesión; sin persistencia en navegador. | RNF-04/06/09, RC-05/10 |
| UI-07 | P1 | Comparar dos ejecuciones del mismo sistema con omega distinto y no mezclar identidades; métricas ausentes o incompatibles se explican; exportar CSV y PNG asociados a la ejecución y corte correctos. | RF-12/13/14, CU-03–05 |

### 4.2. Control — Jherson

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| CT-01 | P0 | Conservar integración de GET /api/v1/health. Probar cuatro POST /api/v1/* según C-07, multipart con JSON contract_version=2, mode explícito. Rechazar v1 de payload, claves desconocidas y mezcla de campos 2D/3D. | CU-01–05, RNF-04/08 |
| CT-02 | P0 | ROI dentro de geometría real decodificada, límites exclusivos, enteros no booleanos; semillas únicas, ambas clases, al menos una incógnita. Casos nulos, negativos, duplicados y dimensiones declaradas falsas no llaman a solver. | RF-04/05/06, RC-03 |
| CT-03 | P0 | Validar configuración beta/threshold/omega/tolerancias/máximo/recursos y composición. Verificar que archivos distintos, mode, input_id, preparation_version o work_shape incompatibles impiden ejecutar. | RF-06/07, RNF-04/07 |
| CT-04 | P0 | Dobles de APIs públicas registran orden leer→preparar→construir→resolver→reconstruir→servicios; ambos modos llaman a resolver_sor con LinearSystem/SolverConfig. No se llama a reconstrucción con fallo de SOR ni a malla con reconstrucción fallida. Malla 2D NOT_APPLICABLE. | RF-06–11, RNF-01/02, RC-07 |
| CT-05 | P0 | Resultados por etapas: 200 con MAX_ITERATIONS/NUMERICAL_FAILURE y diagnóstico sin máscara; fallo de reconstrucción conserva solver; fallo de malla conserva máscara; fallo de gráfica no inventa puntos. Error HTTP inesperado sin traceback, no falsa convergencia. | RF-08–11, RNF-04/09 |
| CT-06 | P0 | ArrayDTO: Base64 inválido, dtype/orden/forma incorrectos, longitud no exacta, máscara fuera de 0/1, vértices no finitos o índices de caras inválidos; comprobar bytes antes de asignar; sin CSR ni NaN/Infinity JSON. Ida/vuelta con TS, incluidos endian y C-order. | C-07, RNF-04/05 |
| CT-07 | P0 | Límite de archivo, bytes descomprimidos, ROI, semillas, iteraciones, payload y concurrencia: parametrizar valores pequeños en test (no defaults del producto); tamaño superior→413, formato→415, ocupado→503, otros según C-08. Limpieza de temporales incluso en excepción; CPU fuera del event loop; no prometer cancelación. | RNF-03/04/06, C-09 |
| CT-08 | P1 | Evaluar y exportar snapshot válido; referencia/original y geometría se revalidan donde corresponda. Rechazar snapshot mal formado o identidad discordante; CSV diagnóstico sin original permitido; no llamar SOR de nuevo. No prometer autenticidad del snapshot reenviado. | RF-13/14, CU-04/05, C-07 |
| CT-09 | P0 | Identidad reproducible: mismas A,b CSR canónicas→mismo system_id; alterar un coeficiente→otro id; cambiar omega no cambia system_id, cada run_id diferente. Definir serialización canónica con longitudes y endian antes de prueba. | RF-12, RNF-07, RC-05/10 |
| CT-10 | P0 | Cache-Control: no-store; errores/logs sin imágenes, rutas privadas, nombres, hashes de casos reales ni credenciales. Revisar temporales, archivos versionados, respuesta de error y nombres de descarga. | RNF-06, RC-01/10 |

### 4.3. Traducción de Datos — Yenderson

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| TR-01 | P0 | JPEG/PNG L y RGB con canales exactamente iguales producen mismo escalar decodificado (usar PNG sin pérdida para comparar valores exactos); rechazar RGB verdadero, alfa/modos no admitidos, archivo corrupto y formato falseado. No reescalar ni orientar silenciosamente. | RF-01, RNF-04, C-01/02 |
| TR-02 | P0 | NIfTI 3D sintético, .nii y .nii.gz, aplicar escala de encabezado sin convertir datos de cálculo a uint8; rechazar 4D, valores no finitos, unidades inválidas, afín singular/ambigua, anisotropía u oblicuidad no admitidas. | RF-02, RNF-04/05 |
| TR-03 | P0 | FX-04: permutar/invertir a RAS+, conservar formas, afines, transformaciones y coordenadas físicas; afín única válida documentada; conflicto sform/qform rechazado. Corte axial e índices coinciden con patrón asimétrico. | RF-03/09, RNF-05 |
| TR-04 | P0 | Min–max en ROI completa: extremo 0/1, rango cero→g=0 y CONSTANT_INTENSITY, no dividir por cero; vista uint8 independiente. Comparar corte de volumen con normalización de toda ROI (no normalizar cada corte). Registrar min/max y política. | RF-06, RNF-04/07 |
| TR-05 | P0 | Grafo 4/6 vecinos sin diagonales, borde periódico ni fuera de ROI. Pesos positivos, finitos y simétricos, cada arista una vez; probar beta=0, contraste y subdesbordamiento. Rechazar pesos no válidos, sin regularización silenciosa. | RF-06, RNF-02 |
| TR-06 | P0 | FX-01/02: construir CSR canónica float64 y b correctos, orden C, n=N−s, nnz<=5n/7n; comparar entradas con oráculo y comprobar SPD en matrices diminutas. Fila de incógnita y contexto coinciden; no Laplaciano denso. | RF-06, RNF-02/03/07 |
| TR-07 | P0 | Componente de incógnitas sin acceso a semillas, índices inválidos, b/diagonal inválidos o partición incompleta: error de dominio previo a SOR. Caso desconectado sintético específico del constructor/validador, no asumir que una cuadrícula válida rectangular se desconecta sola. | RF-05/06, RNF-04 |
| TR-08 | P0 | FX-01/02/03/04: restaurar semillas exactamente, reconstruir forma/origen, umbral >=0.5 incluido empate, contorno ortogonal interno, contacto con frontera. Rechazar longitud incorrecta, solución no finita/materialmente fuera de rango y estado no convergente. Margen de redondeo por validar; no modificar iterados. | RF-08/09, RNF-05, RC-07/08 |
| TR-09 | P1 | Referencia alineada y semántica correcta: BRISC_BIN_128, ITKSNAP_LABEL_2; rechazar etiqueta desconocida o geometría/identidad no compatible. Recortar solo a ROI; demostrar que referencia no interviene en semillas, modelo ni máscara. | RF-13, CU-04, RC-09 |

### 4.4. Métodos Numéricos — Jennifer

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| MT-01 | P0 | FX-01/02 con la misma función resolver_sor, comprobar solución y residuo contra oráculos de sección 3. A CSR, b float64; no importar imágenes ni llamar solver externo en producto. | RF-06/07, RNF-01/02 |
| MT-02 | P0 | Un barrido FX-01 con omega=1.2 y x0=0: x=(0,0.6), residuo=sqrt(0.4)≈0.6324555; comprueba orden de actualización y límite de un barrido. Probar también x0 no nulo contra actualización manual. | RF-07/11, C-03 |
| MT-03 | P0 | omega=0,2,negativo,NaN,Inf; tolerancias inválidas, ambas cero, máximo 0/no entero/booleano; x0 de longitud/tipo/finitud incorrectos, A inválida. Rechazar antes de barrer; no fabricar resultados. | RF-07, RNF-04 |
| MT-04 | P0 | x0 exacto: CONVERGED con cero barridos e historial de un punto; b=0 y x0=0 con atol>0 válido; b=0 y atol=0→tau=0 inválido. Convergencia en último barrido tiene prioridad sobre MAX_ITERATIONS. | RF-07/11 |
| MT-05 | P0 | Límite de una iteración FX-01/02 con omega=1.2: MAX_ITERATIONS, final>tau, solution=None, historial de dos puntos. No declarar convergencia por diferencia pequeña de iterados. | RF-07/11, RC-07 |
| MT-06 | P0 | Fallo numérico inicial o intermedio: fixture reproducible que desborde/cause no finitud o doble controlado del cálculo de residuo para cubrir rama. NUMERICAL_FAILURE, solution=None, historial solo de residuos finitos evaluados, failed_at_sweep coherente, nulos si no hay residuo inicial; nunca NaN en DTO. Distinguir fallo de precondición. | RF-07/11, RNF-04, C-03 |
| MT-07 | P0 | No mutación de A.data, indices, indptr, b ni x0; copiar aproximación inicial; historial empieza en r0, longitud=iterations+1 cuando inicial válido; iterations=sweeps; tiempo finito no negativo medido con reloj monotónico. Verificar invariantes y recalcular residuo independiente. | RF-11, RNF-02/07 |
| MT-08 | P1 | Barrido experimental de omega con parámetros comunes y filas fijas; comparar residuo/error/tiempo, incluir no convergencia. omega=1 usa la misma implementación, no segundo algoritmo. No exigir descenso monótono del residuo. | RF-12, RNF-03/07 |

### 4.5. Servicios — Yenderson

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| SV-01 | P0 | FX-06: Marching Cubes nivel 0.5 sobre máscara válida; vértices finitos, caras índices base 0 dentro de rango, triángulos no degenerados, normales/orientación coherentes; comprobar extremos RAS+ y escala con afín aplicada una vez. Validar precisión al transportar float32 según tolerancia acordada. | RF-10, RNF-05 |
| SV-02 | P0 | Vacío, lleno sin cruce, dimensión insuficiente, objeto toca frontera, error de extracción y exceso de límite. PARTIAL si superficie abierta válida, UNAVAILABLE/FAILED con motivo si no; no tapas ficticias. Preservar máscara válida. | RF-10, RNF-04/05 |
| SV-03 | P0 | FX-08: Dice/IoU y conteos exactos, nulos para ambas vacías; referencia ausente→no disponible; dominio ROI explícito; misma forma no prueba correspondencia. | RF-13, CU-04 |
| SV-04 | P0 | Gráfica de convergencia PNG decodificable, historial real incluido cero; historial vacío→indisponibilidad explícita, sin curva inventada. | RF-11 |
| SV-05 | P0 | CSV UTF-8 legible por parser: parámetros, estados, residuo por fila e identidad corresponden al snapshot; fallo sin historial→fila con vacíos; ausencia métrica no es 0; nombres seguros y prevención de inyección de fórmulas. | RF-14, RNF-06/07, CU-05 |
| SV-06 | P0 | PNG de corte procesado válido, dimensiones/origen/índice k correctos y superposición en ROI; conservar imagen de vista; exportación segmentada bloqueada en fallo. No exigir STL/NIfTI para MVP. | RF-14, RNF-05, CU-05 |

### 4.6. Arquitectura, integración y aceptación — Jherson coordina; todos verifican

| ID | Pri. | Caso y criterio de aceptación | Trazabilidad |
|---|---|---|---|
| AR-01 | P0 | Mantener reglas Import Linter y AST: Control solo APIs públicas, hermanas sin imports directos/transitivos, contratos sin capas/HTTP, Métodos sin I/O de imágenes/HTTP/gráficas/visualización. Ampliar prohibiciones a nuevas dependencias donde corresponda. | RNF-01/08 |
| AR-02 | P0 | Prueba negativa aislada de dependencia prohibida: introducir import temporal en copia/fixture, verificar fallo por regla esperada y limpiar; ejecución limpia vuelve a aprobar. No confirmar el archivo temporal. | RNF-01/08 |
| AR-03 | P0 | Revisión de fuentes y pruebas: una función resolver_sor, otros métodos retirados de selección, contratos, documentación y expectativas; ningún solver externo en runtime. Mantener tests reutilizables, explicar cada modificación de tests anteriores. | RF-07, RNF-02/08 |
| IN-01 | P0 | FX-01 y FX-03 por flujo real HTTP 2D: previsualizar, seleccionar, construir, SOR, máscara/contorno, diagnóstico/gráfica, CSV y PNG; verificar solución conocida para FX-01. Sin sustituir constructor/solver con mocks. | CU-01/05, RF-01/03–08/11/14 |
| IN-02 | P0 | FX-02 por flujo real 3D: misma función SOR, valores analíticos, cortes/semillas/ROI, estado de malla parcial o indisponible coherente con frontera. FX-05: máscara obtenida por SOR y malla válida interior; exportar corte/diagnóstico. | CU-02/05, RF-02–07/09–11/14 |
| IN-03 | P0 | Flujo de fallos con contratos reales y dobles acotados: archivo/ROI inválidos, no convergencia real, fallo de reconstrucción, malla o gráfica. Verificar llamadas omitidas, estados y preservación de evidencia. | CU-01–05, RC-06/07, RNF-04 |
| IN-04 | P1 | Repetir SOR con dos omega y sistema idéntico; evaluar la misma máscara con referencia compatible e incompatible; reemplazar referencia no modifica resultado. Exportar snapshot seleccionado, no el más reciente por accidente. | CU-03–05, RF-12/13/14 |
| AC-01 | P0 | Recorrido manual navegador 2D con fixture, original y procesado visibles, ROI/semillas, configuración, diagnóstico, errores y exportación; documentar captura/resultado y SHA. | CU-01/05, RNF-09 |
| AC-02 | P0 | Recorrido manual navegador 3D con fixture, cortes axiales, ROI, semillas en cortes, SOR, máscara y malla interactiva con rotación/zoom, PNG de corte y CSV; explicar parcial y fallo. | CU-02/05, RNF-05/09 |
| AC-03 | P1 | Casos reales FX-09/10 autorizados y admitidos; repetir flujo 2D/3D en ROI de investigación, medir Dice/IoU y limitaciones, sin usar referencia como entrada de la segmentación. Bloqueado hasta verificar licencia y datos. | CU-01/02/04, RF-13, RNF-06/07 |
| AC-04 | P1 | Manual de usuario reproducible desde entorno limpio, ayuda de errores, explicación académica/no clínica, registros de resultados, contribuciones individuales y revisión de PR; confirmar pruebas y dependencias. | RNF-06/07/08/09/10 |

No hay pruebas de diagnóstico ni clasificación clínica. No afirmar que una gráfica de convergencia demuestra una segmentación anatómica válida.

## 5. Puerta de admisión de datos de investigación

Antes de AC-03 o cualquier experimentación real: verificar la licencia de las copias específicas (la licencia del artículo BRISC no implica licencia del dataset), uso autorizado, origen/versión y emparejamiento documentado. BRISC: confirmar política de referencia >=128, dimensiones y orientación; seleccionar casos sin mirar la máscara de referencia para establecer ROI/semillas. ITK-SNAP: T1C escalar y verdad con etiqueta 2 como foreground, resto 0/1; convertir MHA→NIfTI fuera del producto mediante herramienta acordada y comprobada. Comparar formas, intensidades decodificadas, etiquetas y coordenadas de esquinas/puntos internos; verificar orientación, unidades, afines y superposición visual de referencia. No reinterpretar las etiquetas. Si no pasa, mantener pruebas sintéticas y seleccionar alternativa autorizada; no cambiar formatos admitidos sin decisión. Mantener archivos reales, identificadores y registros sensibles fuera de GitHub. No introducir datos médicos en fixtures públicos ni CI. Las inspecciones anteriores no sustituyen esta puerta.

## 6. Experimentos y rendimiento

| ID | Ensayo | Condición controlada y evidencia | Pri. |
|---|---|---|---|
| PF-01 | SOR aislado FX-01/02 | omega=[0.8,1,1.2,1.5,1.8,1.9], mismas A,b,x0,tau,orden y máximo; residuo verdadero y error frente a analítica. | P0 |
| PF-02 | Escalamiento | 2D 32x32,64x64; 3D 8^3,16^3 y solo si resulta viable 32^3. Registrar N, semillas, n, nnz, tiempos por etapa, memoria y estado. No son límites de producción. | P1 |
| PF-03 | Transporte y operación | Medir bytes originales, descompresión, vista Base64, JSON, máscaras/mallas, pico de memoria y tiempo de solicitud en navegador/backend; concurrencia y rechazo sobre límites. | P1 |
| PF-04 | Casos reales admitidos | Repetir comparación de omega con ROI y semillas predefinidas independientemente, informar estado, métricas ROI y limitaciones; no comparar tiempos entre máquinas sin indicarlo. | P1 |

Protocolo propuesto: documentar CPU/RAM/SO, Python/Node y dependencias bloqueadas, commit, versión de preparación/modelo/contrato, fixture o caso autorizado seudonimizado, ROI, semillas, beta, threshold, x0, omega, rtol/atol, tau, máximo, n, nnz y orden. Separar construcción, tiempo del solver, reconstrucción, malla, transferencia y total. Medir tiempo con reloj monotónico; registrar método de medición de memoria y si incluye memoria nativa (tracemalloc solo no equivale a RSS total). Una repetición inicial de calentamiento y tres medidas por configuración si presupuesto lo permite, registrar todas y mediana/rango; si se reduce el número, justificarlo y reportarlo, no fingir estadística. No descartar silenciosamente fallos ni runs lentos. Registrar residuo inicial/final, historial, iteraciones/barridos, estado y error de referencia cuando exista. Fijar un omega predeterminado únicamente tras evidencia representativa. Cambiar beta/ROI implica otro sistema; no atribuir ese efecto solo a omega. Seleccionar límites operativos finitos por medición y revisión del equipo antes de admitir cargas reales; capacidad RAM no garantiza tiempo aceptable. No prometer latencia ni valor Dice/IoU mínimo sin fundamento. Si no es viable, reducir ROI o extras y documentar restricciones; no sustituir SOR ni abandonar 3D sin acuerdo.

## 7. Trazabilidad consolidada (cobertura de diseño, no ejecución)

| Requisito | Casos principales |
|---|---|
| RF-01 | TR-01, UI-01, IN-01 |
| RF-02 | TR-02/03, UI-01, IN-02 |
| RF-03 | UI-01/02, TR-03, AC-02 |
| RF-04 | UI-02, CT-02, TR-08 |
| RF-05 | UI-02/03, CT-02, TR-07/08 |
| RF-06 | TR-05/06/07, CT-04, MT-01 |
| RF-07 | MT-01–07, CT-03/04, AR-03 |
| RF-08 | TR-08, UI-04, IN-01 |
| RF-09 | TR-03/08, UI-04, IN-02 |
| RF-10 | SV-01/02, UI-04, IN-02, AC-02 |
| RF-11 | MT-04–07, SV-04, CT-05, UI-05 |
| RF-12 | MT-08, CT-09, IN-04, PF-01/02/04 |
| RF-13 | TR-09, SV-03, CT-08, IN-04, AC-03 |
| RF-14 | SV-05/06, CT-08, UI-07, IN-01/02 |
| RNF-01 | AR-01/02, CT-04 |
| RNF-02 | MT-01/02/07, TR-06, AR-03 |
| RNF-03 | TR-06, CT-07, PF-01–04 |
| RNF-04 | TR-01/02/07, MT-03–06, CT-02/03/05–07, IN-03 |
| RNF-05 | TR-03/08/09, UI-02/04, SV-01/02/06 |
| RNF-06 | CT-10, UI-06, AC-03/04 y puerta de datos |
| RNF-07 | CT-09, MT-07/08, SV-05, PF-01–04 |
| RNF-08 | AR-01–03, CT-01, AC-04, CI de sección 8 |
| RNF-09 | UI-04–07, AC-01/02/04 |
| RNF-10 | AC-04, registro de evidencias, PR y manual |

| Caso de uso | Integración/aceptación |
|---|---|
| CU-01 | IN-01/03, AC-01/03 |
| CU-02 | IN-02/03, AC-02/03 |
| CU-03 | MT-08, CT-09, UI-05/07, IN-04, PF-01–04 |
| CU-04 | TR-09, SV-03, CT-08, IN-04, AC-03 |
| CU-05 | SV-05/06, CT-08, IN-01/02/04, AC-01/02 |

C-01→UI-02/TR-03; C-02→TR-01–07; C-03→MT-01–08; C-04→TR-08/CT-05; C-05→SV-01–06; C-06→CT-04/AR-01; C-07→CT-01/06/08/09, UI-06; C-08→CT-05/07/10, IN-03; C-09→CT-07/PF-02/03. RC-01 y RC-10: privacidad/identidad y admisión; RC-02/03: UI-02/03 y CT-02/TR-07; RC-04: MT-03/04; RC-05: UI-06/CT-09; RC-06/07: UI-05/CT-05/IN-03; RC-08: UI-04/TR-08/SV-02; RC-09: TR-09/IN-04/AC-03.

## 8. Integración, comandos y CI

Conservar los comandos del repositorio y sus entornos (Python 3.13, Node 22, .venv, lockfiles). En la raíz, ejecutar las comprobaciones locales correspondientes y al terminar `bash scripts/ci-local.sh todo`. Los subcomandos existentes son `python`, `frontend`, `integracion`, `precommit`; no modificar scripts para ocultar errores. Python: Ruff check/format, mypy estricto, lint-imports, pytest unit/architecture/integration; frontend: ESLint, Prettier, Vitest y compilación TypeScript/Vite. Verificar dependencias nuevas candidatas y tipado/licencias/locks por PR. Los tests nuevos de CI deben ser pequeños, deterministas, sintéticos y sin depender de descarga de datos. Experimentos pesados y aceptación manual se registran aparte con SHA y evidencia; no introducir umbrales de tiempo frágiles en CI.

Flujo: rama por tarea desde develop actualizado; commits convencionales por autor; PR a develop; revisar cambios y pruebas, documentar revisión o excepción autorizada según política verificada; operador Jherson ejecuta workflow_dispatch oficial **desde develop**, `pr_number`, SHA de head final de 40 caracteres, `pruebas=todo`. Verificar que head y base actuales coinciden con los SHA del candidato evaluado (si cambian, volver a revisar y ejecutar), todos los jobs exigidos y resumen exitoso. Conservar merge commits. La excepción de equipo es solo por PR, su membresía exclusiva sigue por confirmar; no inventar aprobaciones ni asumir que existe required status check automático. CI parcial no autoriza integrar; promoción a main por PR según misma política. No ejecutar ahora CI ni crear ramas por este documento.

## 9. Evidencia y manejo de defectos

Plantilla de registro por caso o subcaso (sin resultados ficticios):

| Campo | Contenido a registrar |
|---|---|
| ID / requisito / CU | Identificador del caso y trazabilidad |
| Responsable / fecha | Autor real de la ejecución |
| SHA / rama / entorno | Commit exacto, hardware y versiones cuando aplique |
| Entrada / parámetros | Fixture y valores reproducibles; no información clínica identificable |
| Procedimiento / comando | Pasos y configuración efectiva |
| Esperado / observado | Afirmaciones comprobadas, tolerancia y datos de ejecución |
| Estado | PENDIENTE / BLOQUEADA / APROBADA / FALLIDA |
| Evidencia | Ruta de test, log sanitizado, captura sintética o referencia de artefacto autorizado |
| Defecto / revalidación | Impacto, corrección y SHA nuevo; clave Jira solo cuando exista |

Un defecto crítico de exactitud, geometría, seguridad, dependencia o funcionamiento de ambos modos bloquea la entrega relacionada. Corregir y repetir caso y regresiones; no cambiar oráculos para acomodar el resultado. Registrar problemas de rendimiento y segmentación aunque el solver converja. Si la prueba queda bloqueada por datos/licencia, dependencia o falta de horas, explicitarlo y negociar con líder/equipo; no darla por aprobada. No declarar un número de pruebas superadas por contar filas de este plan.

## 10. Definición de terminado y pendientes

- Componente: contratos acordados, código del responsable, unitarias/negativas P0 correspondientes, interfaces públicas documentadas, revisión y CI manual completo del candidato. Sin dependencias prohibidas ni resultados simulados como producto.
- Integración: IN-01/02/03 y AC-01/02 con datos sintéticos, mismos contratos y único SOR real; diagnóstico y exportación básica; malla de máscara calculada, geometría válida. Cumplir el resto de requisitos obligatorios y documentar fallos.
- Entrega: P0 y P1 aplicables, pruebas reales tras admisión, experimentos de omega y tamaño, documentación de limitaciones, manual de usuario, historial de contribuciones y CI completo del candidato final. Si algún criterio no puede completarse, registrar explícitamente la desviación y buscar acuerdo antes de entregar; no afirmar que fue superado. P2 no condiciona MVP.

Pendientes de cerrar con evidencia: tolerancias geométricas, margen de probabilidades y precisión de malla, beta/omega por defecto, límites de recursos, compatibilidad y licencia de nuevas dependencias, licencias de datos/conversión MHA→NIfTI, tiempo restante, revisión de contratos por los cuatro responsables y condiciones adicionales del docente sobre librerías. Este plan no altera las responsabilidades, no instala dependencias ni acredita pruebas ejecutadas. Siguiente: revisar `07_Cronograma.md`, confirmar horas realmente disponibles y dependencias; después PR de alineación, CODEOWNERS/Jira verificados y desarrollo paralelo.
