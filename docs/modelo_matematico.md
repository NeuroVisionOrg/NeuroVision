# NeuroVision — Modelo matemático 2D y 3D con SOR

**Versión:** 0.2 — línea base matemática aceptada por el líder, condicionada a validación\
**Fecha:** 25 de noviembre de 2026\
**Base:** `01_Requisitos.md`, `02_Casos_de_uso.md`, registro de decisiones v1.3.\
**Estado:** demostración teórica condicionada y verificación exploratoria de dos sistemas sintéticos. No acredita implementación del producto ni rendimiento en resonancias reales.

## 1. Propósito y separación matemática

El alcance aprobado por el líder comprende segmentación asistida de regiones tumorales en 2D y 3D. La indicación docente reportada exige SOR como único solucionador numérico. Se adopta Random Walker binario como línea base matemática de diseño, con Marching Cubes como candidato de reconstrucción. La conformidad del líder expresada tras revisar v0.1 se interpreta como aprobación del enfoque general, no de cada parámetro ni de la compatibilidad de las dependencias. No son requisitos textuales nuevos del profesor. La validación sobre datos reales sigue pendiente.

| Componente | Entrada | Salida | Responsable principal |
|---|---|---|---|
| Formulación Random Walker | Intensidades, ROI, semillas y geometría | Sistema lineal disperso y correspondencia de incógnitas | Yenderson — Traducción |
| Solución SOR | A, b, configuración | Vector aproximado, estado y evidencia numérica | Jennifer — Métodos Numéricos |
| Reconstrucción | Solución válida, semillas y correspondencia | Probabilidades, máscara y contorno/cortes | Yenderson — Traducción |
| Superficie y métricas | Máscara válida, geometría, referencia opcional | Malla, métricas y gráficas | Yenderson — Servicios |

Control (Jherson) coordina las operaciones a través de contratos y verifica las entradas y resultados. Interfaz (Johan) recoge la selección y presenta las salidas, sin implementar el solver. Las tres capas especializadas no se importan entre sí. Se conserva una única implementación propia de SOR, independiente de la dimensión espacial. No se implementan Jacobi, Gauss-Seidel o SSOR como solucionadores adicionales.

## 2. Dominio, coordenadas y preparación

Sea Ω la ROI rectangular (2D) o cuboidal (3D), formada por una cuadrícula finita. Los límites inferior y superior de cada eje son inclusivo y exclusivo respectivamente. La ROI no está vacía, queda dentro de los datos y cumple los límites de recursos que se medirán. La geometría de pantalla nunca sustituye las coordenadas de los datos.

Propuesta para contratos (todavía no aprobada):

- En 2D se conserva el arreglo `(alto, ancho)` indexado `(fila, columna)`, con coordenadas externas `(x, y) = (columna, fila)` de la imagen original.
- En 3D se propone indexar el arreglo `(i, j, k)` en el orden de ejes del volumen de trabajo, y conservar una transformación explícita hacia el archivo original si se permutan o invierten ejes. El visor debe convertir sus coordenadas de pantalla al índice del vóxel. Para la primera versión, evaluar la reorientación por permutaciones e inversiones hacia RAS+ sin interpolación; si el plano es oblicuo o existe cizallamiento, no llamarlo axial real sin justificación. Rechazar explícitamente geometrías no soportadas en el MVP antes que alterar silenciosamente datos. La estrategia exacta se decidirá tras inspeccionar NIfTI.
- La transformación afín espacial H es de 4 × 4, finita, con bloque lineal B no singular y unidades conocidas o documentadas. Se preservan el espacio de referencia, la convención de ejes y el desplazamiento de recorte. No asumir que todos los archivos tienen vóxeles isotrópicos o unidades mm.
- Propuesta inicial: trabajar con una única intensidad escalar por píxel/vóxel. Una modalidad de MRI por ejecución. Un archivo de cuatro dimensiones no se interpreta automáticamente como un volumen de tres dimensiones; se exige selección explícita de modalidad o se rechaza hasta admitirla.

Se propone normalización min–max sobre la ROI: g_i = (I_i − I_min)/(I_max − I_min), en [0,1]. Rechazar intensidades no finitas; calcular diferencias con precisión suficiente y comprobar salida finita. Si todas las intensidades coinciden, usar g_i=0 para todo i y advertir que el resultado dependerá de geometría y semillas, no de contrastes. No normalizar cada corte 3D por separado. El uso de percentiles u otras normalizaciones deberá justificarse y registrarse antes de aprobarse. Para una comparación exclusiva de omega se congela el sistema ya construido.

## 3. Grafo ponderado de píxeles y vóxeles

Sea G=(V,E) un grafo finito no dirigido. Cada nodo corresponde a una posición de Ω. En 2D se usan vecinos inmediatos por fila y columna (hasta 4); en 3D, vecinos inmediatos en los tres ejes (hasta 6). No se crean diagonales ni conexiones periódicas. Propuesta de frontera: solo aristas cuyos extremos estén dentro de Ω; no se fijan automáticamente a fondo los bordes de ROI. Fuera de Ω no se afirma que se haya segmentado.

Para datos isotrópicos, la propuesta es:

$$
w_{ij}=\exp[-\beta(g_i-g_j)^2],\quad \beta\ge 0,\quad \{i,j\}\in E.
$$

A mayor diferencia de intensidad, menor conexión, para beta positivo. Con beta=0 se obtienen pesos unitarios, útiles para verificar la estructura. Para una primera extensión anisotrópica se propone:

$$
h_k=\|B e_k\|_2,\qquad c_k=(h_{\min}/h_k)^2,\qquad w_{ij}=c_k\exp[-\beta(g_i-g_j)^2].
$$

Aquí e_k es el vector unitario del eje que conecta los vecinos, h_k es la distancia física entre centros y h_min el mínimo espaciamiento. El factor c_k es adimensional, positivo y simétrico; se reduce a 1 si el espaciamiento es isotrópico. Es una propuesta de ponderación espacial de un grafo, no una afirmación de que reproduzca exactamente la difusión continua para cualquier afín. Verificar su efecto con fantomas anisotrópicos antes de adoptarla; restringir el dominio geométrico si no se valida. En 2D sin metadatos físicos usar la cuadrícula de píxeles con c_k=1 y no inferir medidas físicas.

**Condiciones obligatorias del modelo:** beta finito y no negativo; pesos reales finitos estrictamente positivos en las aristas admitidas, simétricos, sin autoaristas. Calcular una vez cada peso no dirigido y usarlo en ambas direcciones. El valor teóricamente positivo puede redondear a cero o perder efecto en float64. Verificar pesos y sumas en representación efectiva; registrar escalas extremas y rechazar configuraciones que incumplan las condiciones. No recortar pesos ni añadir regularización silenciosamente: eso modificaría el problema. Los valores de beta y los límites numéricos se fijarán después de medir condicionamiento y segmentación. Probar beta=0 y contrastes controlados antes de elegir un valor de producción.

## 4. Semillas y formulación del problema

Particionar V en el conjunto marcado M y el desconocido U, disjuntos. M contiene semillas de primer plano (1) y de fondo (0). Deben estar dentro de Ω, sin posiciones contradictorias ni duplicados según el contrato; se exige al menos una de cada clase y una incógnita. Cada componente conexa de U debe estar conectada a una semilla mediante aristas de peso positivo. Validar esta condición antes de resolver. En una cuadrícula rectangular/cuboidal completa, con todas las aristas efectivas positivas y al menos una semilla, la conectividad es suficiente; mantener igualmente el criterio explícito para controlar futuros dominios o conexiones inválidas.

W es la matriz simétrica de pesos, con w_ij=0 si no hay arista; D es diagonal con d_i=Σ_j w_ij. El Laplaciano L=D−W satisface Lp=0 en nodos desconocidos, con valores de Dirichlet p_M fijos. La energía de una configuración es

$$
E(p)=\frac12\sum_{\{i,j\}\in E} w_{ij}(p_i-p_j)^2.
$$

Al minimizar respecto de p_U manteniendo p_M fija, se obtiene:

$$
L_{UU}p_U+L_{UM}p_M=0,
\qquad A=L_{UU},\quad x=p_U,\quad b=-L_{UM}p_M.
$$

El sistema Ax=b expresa que cada incógnita es la media de sus vecinos ponderada por los pesos. Para cada i∈U, A_ii es la suma de los pesos de **todos** los vecinos (incluidas semillas); A_ij=−w_ij cuando j∈U es vecino de i, y b_i es la suma de pesos a semillas de primer plano. Las semillas de fondo contribuyen a la diagonal, aunque aporten cero al término independiente. No borrar esas contribuciones al reducir L.

La solución exacta p_i es la probabilidad, bajo el paseo aleatorio definido por el grafo, de alcanzar una semilla de primer plano antes que una de fondo. No es una probabilidad clínica de tumor ni de enfermedad. El principio de máximo discreto garantiza 0≤p_i≤1 bajo las condiciones del modelo. El valor exacto de una región depende de los datos, los pesos, las semillas y la frontera.

## 5. Existencia, unicidad y convergencia

Para cualquier vector z sobre U, extenderlo por cero en M. Se obtiene

$$
z^TAz=\sum_{\{i,j\}\in E,\ i,j\in U}w_{ij}(z_i-z_j)^2+\sum_{\{i,j\}\in E,\ i\in U,j\in M}w_{ij}z_i^2.
$$

En el segundo sumatorio cada arista desconocida–semilla se cuenta una vez. Todos los términos son no negativos. Si la suma es cero, los z_i coinciden dentro de cada componente de U; los que están conectados directamente con una semilla tienen valor cero. Por conectividad, cada componente tiene ese valor cero. Por tanto, para z≠0 se cumple zᵀAz>0: A es simétrica definida positiva (SPD), tiene diagonal positiva y el sistema posee solución única.

Para A real SPD, el teorema de convergencia de SOR garantiza convergencia desde cualquier aproximación inicial en aritmética exacta cuando 0<ω<2. No afirma que todas las matrices SPD converjan en pocas iteraciones ni que todo sistema arbitrario con diagonal positiva sea SPD. Traducción debe garantizar las hipótesis; una validación estructural del contrato LinearSystem no basta para certificar SPD en matrices arbitrarias. Verificar simetría, diagonal, estructura, pesos y acceso a semillas; en sistemas pequeños, comprobar eigenvalores positivos como prueba adicional, no como requisito costoso de cada ROI.

En aritmética finita, pesos extremos y redondeo pueden producir mal condicionamiento o estancamiento. Un residuo pequeño no asegura por sí solo un error de solución pequeño: e=A⁻¹r (con e=x_exacto−x_aproximado). En pruebas con solución conocida medir también error directo. No garantizar exactitud clínica, rapidez ni convergencia dentro de un máximo de iteraciones.

## 6. SOR: única implementación de resolución

Con orden fijo de incógnitas, la actualización es

$$
x_i^{(k+1)}=(1-\omega)x_i^{(k)}+\frac{\omega}{a_{ii}}\left(b_i-\sum_{j<i}a_{ij}x_j^{(k+1)}-\sum_{j>i}a_{ij}x_j^{(k)}\right).
$$

Se actualiza cada componente en sitio, en el orden pactado, utilizando inmediatamente las componentes ya actualizadas y las anteriores para las restantes. Un barrido completo equivale a una iteración. No vectorizar toda la actualización como si fuera simultánea. Con ω=1 se obtiene el caso límite ordinario de la relajación (equivalente a Gauss-Seidel); se permite estudiar ese valor dentro del mismo SOR, sin implementar otro solver. Con 0<ω<1 hay subrelajación y con 1<ω<2 sobrerrelajación. El mayor ω no necesariamente mejora el rendimiento.

Propuesta de orden reproducible: enumeración lexicográfica de posiciones de ROI en orden C, omitiendo semillas, y correspondencia bijectiva índice de incógnita ↔ coordenada local. Conservar el origen de ROI por separado. Cualquier cambio de orden debe documentarse porque puede alterar las iteraciones.

### 6.1. Criterio de parada y estados

$$
r^{(k)}=b-Ax^{(k)},\qquad \tau=\max(\mathrm{atol},\mathrm{rtol}\|b\|_2).
$$

La ejecución converge según el criterio operativo cuando ||r^(k)||₂≤τ. Calcular el residuo inicial antes de iterar y el verdadero residuo del sistema después de cada barrido. Si x0 ya cumple el criterio, devolver convergencia con cero iteraciones e historial de longitud uno. No usar únicamente el cambio entre iteraciones ni declarar convergencia por llegar al límite.

| Parámetro | Propuesta experimental inicial |
|---|---|
| x0 | Vector cero float64 |
| rtol | 1e-6 (heredado, provisional) |
| atol | 1e-10 (heredado, provisional) |
| max_iterations | 2000 (heredado, provisional) |
| omega | 0<ω<2; estudiar 0.8, 1.0, 1.2, 1.5, 1.8, 1.9 inicialmente |
| Umbral de máscara | 0.5 provisional, empate al primer plano |

Validar que parámetros, matriz, b, x0, residuo y actualizaciones sean finitos; tolerancias no negativas y al menos una positiva (si se permite rtol=0/atol=0 individualmente), y τ efectivo positivo y finito para el sistema; máximo entero positivo. Para b=0 se requiere un umbral absoluto positivo. Si se alcanza el máximo sin cumplir τ, informar `max_iterations`; ante actualización/residuo no finito o fallo numérico, `numerical_failure`; cuando se cumple el criterio, `converged`. Nombres y estructuras finales se fijarán en contratos. Registrar estado, omega, tolerancias, x0 o regla de inicialización, iteraciones=barridos, residuo inicial/final, historial desde iteración 0 y tiempo de solver. En fallo, conservar evidencia finita disponible y no fabricar historial ni salida válida.

La rutina de Métodos Numéricos desconoce imágenes, semillas, ROI y HTTP. Usa SciPy CSR como almacenamiento y operaciones básicas de matrices/vectores, no como sustituto del método. Resolver por librerías externas está permitido únicamente en pruebas de referencia y con restricciones del docente confirmadas.

## 7. Almacenamiento disperso y complejidad

Si N=|Ω|, s=|M| y n=N−s, entonces A es n×n. En 2D, nnz(A)≤5n; en 3D, nnz(A)≤7n. Construir directamente las entradas de A y b sin formar una matriz densa N×N o el Laplaciano completo denso. CSR canónica, float64 para valores y vectores; elegir tipo de índices según tamaño. El almacenamiento de A es O(nnz+n), y cada barrido y recálculo de residuo son O(nnz+n) para la estructura descrita. El costo total depende de los barridos necesarios, del orden y de la implementación real. Evitar construir estructuras auxiliares enormes y verificar límites antes de asignar memoria.

| ROI sintética | N antes de descontar semillas | Uso |
|---|---:|---|
| 32×32 | 1024 | Primer ensayo 2D |
| 64×64 | 4096 | Escalamiento 2D |
| 8×8×8 | 512 | Primer ensayo volumétrico |
| 16×16×16 | 4096 | Escalamiento 3D |
| 32×32×32 | 32768 | Solo tras medir tamaños menores |

Estas dimensiones son casos de ensayo, no límites operativos aprobados ni garantías de rendimiento.

## 8. Verificación analítica y exploratoria efectuada

### 8.1. Caso 2D uniforme

ROI de 2×2, con coordenadas (fila,columna). Semillas (0,0)=0 y (0,1)=1. Incógnitas (1,0), (1,1), en ese orden. Intensidad constante, pesos unitarios. Cada incógnita tiene dos vecinos (una semilla y la otra incógnita).

$$
A=\begin{pmatrix}2&-1\\-1&2\end{pmatrix},\qquad b=\begin{pmatrix}0\\1\end{pmatrix},\qquad x^*=\begin{pmatrix}1/3\\2/3\end{pmatrix}.
$$

A es SPD (eigenvalores 1 y 3). La probabilidad y máscara esperadas, incluyendo las semillas, son

$$
P=\begin{pmatrix}0&1\\1/3&2/3\end{pmatrix},\qquad M_{bin}=\begin{pmatrix}0&1\\0&1\end{pmatrix}.
$$

### 8.2. Caso 3D con contraste

ROI isotrópica de forma (4,2,2), índices (i,j,k). Todas las posiciones del plano i=0 son semillas de fondo y las del plano i=3 son semillas de primer plano. Planos i=1 e i=2 desconocidos (4 vóxeles por plano). Intensidades normalizadas g=0 para i=0,1 y g=1 para i=2,3. Fijar β=ln(4) en este ensayo: pesos 1 dentro de cada región de igual intensidad y 1/4 entre los dos planos desconocidos. Por simetría y unicidad, las cuatro incógnitas de cada plano tienen la misma probabilidad p y q, respectivamente.

$$
\frac54p-\frac14q=0,\qquad -\frac14p+\frac54q=1.
$$

Se deduce p=1/6 y q=5/6. La matriz completa A de ocho incógnitas (no la reducida por simetría para la explicación) es

$$
A=\begin{pmatrix}C&-\frac14 I_4\\-\frac14 I_4&C\end{pmatrix},\qquad C=\begin{pmatrix}13/4&-1&-1&0\\-1&13/4&0&-1\\-1&0&13/4&-1\\0&-1&-1&13/4\end{pmatrix},
\qquad b=(0,0,0,0,1,1,1,1)^T.
$$

El orden por plano es (j,k)=(0,0),(0,1),(1,0),(1,1). La diagonal 13/4 incorpora los cuatro vecinos de cada incógnita. La máscara umbralizada tiene los dos primeros planos a 0 y los dos últimos a 1; la región toca los bordes del dominio, por lo que esta prueba verifica formulación y reconstrucción, no una superficie cerrada de un tumor completo.

### 8.3. Experimento ejecutado en la sesión de análisis

Se construyeron A y b mediante los vecinos del grafo y la regla de pesos descrita; se aplicaron barridos SOR secuenciales sobre CSR en orden C. Se usó una rutina descartable de experimentación, no el código de producción del equipo. Entorno del análisis: Python 3.13.5, NumPy 2.3.5 y SciPy 1.17.0; no corresponde necesariamente a los lockfiles de NeuroVision. Se compararon soluciones con las analíticas, se comprobó simetría y eigenvalor mínimo positivo de las dos matrices pequeñas y se recalculó el residuo. Solo para esa verificación de matrices diminutas se usó su representación densa; no se propone hacerlo en el producto.

Condiciones: x0=0, rtol=1e-6, atol=1e-10, max_iterations=2000, norma 2 del residuo. n=2 y nnz=4 en 2D; n=8 y nnz=32 en 3D. Tolerancias efectivas 1e-6 y 2e-6 respectivamente. Resultados reales de la rutina exploratoria (redondeados a tres cifras significativas):

| ω | Barridos 2D | Residuo final 2D | Error máximo 2D | Barridos 3D | Residuo final 3D | Error máximo 3D |
|---:|---:|---:|---:|---:|---:|---:|
| 0.8 | 19 | 7.95e-7 | 5.83e-7 | 32 | 1.52e-6 | 6.58e-7 |
| 1.0 | 11 | 4.77e-7 | 3.18e-7 | 20 | 1.17e-6 | 5.22e-7 |
| 1.2 | 10 | 2.61e-7 | 1.66e-7 | 10 | 1.14e-6 | 3.18e-7 |
| 1.5 | 21 | 8.61e-7 | 4.16e-7 | 22 | 1.01e-6 | 3.93e-7 |
| 1.8 | 62 | 8.67e-7 | 6.40e-7 | 63 | 1.73e-6 | 7.65e-7 |
| 1.9 | 131 | 9.48e-7 | 6.92e-7 | 137 | 1.17e-6 | 4.63e-7 |

Las doce ejecuciones cumplieron el criterio de residuo y coincidieron con la clasificación analítica a umbral 0.5 de las incógnitas. Los errores máximos fueron inferiores a 1e-6 en estos casos. Al repetir con ω=1.2 y max_iterations=1, ambos casos no convergieron (residuos ≈0.632456 y ≈1.155008), como era esperado. No se midieron tiempos ni memoria. No se ejecutó el solver del repositorio, ni sus pruebas ni su CI. No se ha verificado manejo de todos los errores, mallas, geometría real, calidad de segmentación o rendimiento de producción.

Reproducción independiente del cálculo: construir A y b por las reglas de las secciones 3–4 para cada entrada especificada; comenzar en x=0; calcular τ; recorrer filas CSR en orden fijo aplicando la ecuación de SOR en sitio, excluyendo la diagonal de la suma; recalcular ||b−Ax||₂ tras cada barrido; detener si satisface τ o alcanza el límite; registrar ||x−x*||∞. Usar las matrices explícitas anteriores como referencia para detectar errores en el constructor. Los valores son evidencias preliminares, no umbrales de aceptación universales. La rutina de prueba no constituye una entrega definitiva del solver.

**Conclusión limitada:** se demuestra coherencia del modelo en ambos ejemplos, y que un mismo procedimiento SOR puede resolverlos. ω=1.2 requirió menos barridos entre los valores ensayados en estos dos sistemas; no justifica adoptarlo como óptimo general. Random Walker es matemáticamente viable bajo las condiciones descritas; falta aprobación del diseño y validación experimental en datos representativos.

## 9. Reconstrucción de probabilidades y máscara

Tras convergencia operativa, reconstruir p en Ω con el mapa índice↔coordenada, restituir exactamente las semillas a 0/1 y verificar forma, finitud y correspondencia geométrica. Los iterados de SOR pueden salir de [0,1]; no recortarlos durante el solver, porque alteraría el método. Tras converger, comprobar rango con margen numérico justificado por pruebas; solo admitir correcciones diminutas documentadas de redondeo, conservando evidencia del vector original. Valores materialmente fuera de rango o inconsistencias requieren fallo de reconstrucción, aunque el residuo cumpla τ. El margen definitivo está pendiente.

Propuesta M_bin(i)=1 si p_i≥0.5, y 0 en otro caso. Conservar ambas clases de semillas y el umbral usado; representar el mapa de probabilidades como propiedad del grafo, no como confianza diagnóstica. En 2D extraer el contorno mediante vecinos dentro de Ω, y mostrarlo superpuesto al original con el desplazamiento correcto; indicar contacto con frontera. No presentar posiciones no evaluadas como fondo calculado. En 3D reconstruir el arreglo en orden (i,j,k) y mostrar sus cortes asociados al original.

Una ejecución no convergente o con fallo numérico puede informar/exportar resultados numéricos disponibles (CU-03 y CU-05), pero no una máscara válida. Un fallo de malla posterior no invalida automáticamente una máscara correctamente calculada: comunicar por separado los estados.

## 10. Geometría tridimensional y malla

Se propone Marching Cubes sobre M_bin, nivel 0.5, para obtener vértices en coordenadas de índices y caras triangulares. No reemplaza Random Walker ni SOR. Validar forma y finitud de vértices, índices de caras, área de triángulos y tratamiento de mallas vacías. Con un volumen en orden (i,j,k) y vértice local v, la coordenada física es

$$
\begin{pmatrix}r\\1\end{pmatrix}=H\begin{pmatrix}v+o\\1\end{pmatrix},
$$

con o el origen del recorte en el volumen de trabajo. Si hubo reorientación, H corresponde al volumen reorientado (o se compone la transformación de reorientación con la afín original). Si se aplica la afín completa a los vértices, generar en índices de vóxel con spacing unitario: no aplicar el espaciamiento dos veces. Si se usa relleno auxiliar, restar su desplazamiento antes de transformar. Si cambia la orientación de la base, verificar orden de caras y normales (invertir winding cuando corresponda). Three.js debe representar la geometría sin sustituirla por escalas arbitrarias; cualquier transformación visual conserva la referencia de datos.

Si la máscara toca la frontera de ROI o volumen, marcar posible truncamiento. No cerrar artificialmente el tumor con fondo supuesto sin declarar la aproximación. En el MVP se propone advertir y solicitar ampliación de ROI cuando sea viable, o mostrar superficie parcial explícitamente identificada como tal. Si no existe superficie válida (máscara vacía, volumen insuficiente o degenerado), comunicar el estado. Las reglas exactas se fijarán en contratos y pruebas.

Si la información espacial es válida en milímetros, se puede estimar el volumen segmentado V=N_fg |det B| en mm³. Se trata del volumen de los vóxeles de la máscara dentro de Ω; no de una medición clínica, y no debe presentarse como volumen total si el objeto está truncado. Sin unidades válidas, reportar solo número de vóxeles. Esta métrica física no es requisito obligatorio adicional.

## 11. Evaluación y evidencia experimental futura

Si existe una referencia R compatible, comparar M_bin y R sobre el mismo dominio evaluable y la misma semántica binaria. La geometría, orientación, afín y correspondencia de índices deben coincidir según tolerancias acordadas; dimensiones iguales por sí solas no bastan. No realizar un registro/re-muestreo silencioso. Definir qué etiquetas forman la región objetivo antes de evaluar. En la primera versión se propone evaluar sobre la ROI común, indicando expresamente que no es una evaluación de todo el volumen. No emplear la referencia para fijar automáticamente semillas/ROI, generar la máscara o ajustar los parámetros sobre el mismo caso que se reporta como evaluación independiente. Registrar procedencia y configuración sin datos sensibles.

$$
\mathrm{Dice}=\frac{2|M_{bin}\cap R|}{|M_{bin}|+|R|},\qquad \mathrm{IoU}=\frac{|M_{bin}\cap R|}{|M_{bin}\cup R|}.
$$

Si ambas máscaras están vacías, se propone declarar las métricas no definidas y documentar esa convención; si una es vacía y la otra no, ambas son cero. Sin referencia, informar no disponible. Distinguir exactitud del sistema lineal de solapamiento de segmentación. La primera depende del solver; la segunda depende además del modelo, intensidades, semillas y referencia.

| Serie | Control y variable | Evidencia esperada |
|---|---|---|
| SOR conocido | Sistemas de §8, variando omega | Solución, residual y error independiente; límite de iteraciones y casos inválidos |
| Sintéticos 2D | Cuadrículas, objetos y semillas documentadas | Pesos, sistema, máscara y contorno; geometría y escala |
| Sintéticos 3D | Fantomas 8³/16³, isotrópicos y anisotrópicos | Sistema, máscara, cortes y malla; transformaciones y bordes |
| Comparación omega | Mismo A,b,x0, orden, tolerancias y máximo, cambiar solo omega | Residuos, barridos, tiempos y fallos, mismo entorno |
| Escalamiento | ROI creciente con protocolo documentado | Tiempo y memoria, límites seguros; controlar otros parámetros cuando sea posible |
| Datos autorizados | BRISC 2D, ITK-SNAP/MSD 3D candidatos | Métricas si referencia compatible, limitaciones, evidencia reproducible |

Separar tiempo de decodificación, construcción de A,b, solver (incluye cálculo de residuo e historial con una convención constante), reconstrucción y malla. Medir hardware, versiones, orden, tamaños, repeticiones y condiciones; informar estadísticos y fallos sin excluir ejecuciones desfavorables. No afirmar rapidez en volúmenes completos antes de medir. Establecer los límites de ROI, bytes, tiempo, memoria, parámetros y criterios de exactitud con los experimentos del equipo. Mantener las 80 horas-persona como presupuesto inicial, descontando esfuerzo ya consumido.

## 12. Trazabilidad y cierre

| Requisitos / casos de uso | Evidencia de este documento y pendiente |
|---|---|
| RF-04–RF-06, CU-01/02, RNF-02/03 | Grafo, semillas, SPD y CSR; verificar constructor real, casos negativos y escalamiento |
| RF-07, RF-11–RF-12, CU-03 | SOR, criterio, registros, ejemplos; implementar solver real y medir |
| RF-08–RF-10, CU-01/02, RNF-05 | Reconstrucción y transformación; probar máscara, malla y orientación |
| RF-13, CU-04 | Métricas y dominio comparable; comprobar datos y convenciones |
| RF-14, CU-05, RNF-07 | Información que debe exportarse; definir formato en contratos |

**Línea base de diseño aceptada por el líder (D-05):** Random Walker binario con 4/6 vecinos y SOR único en CSR; se mantienen como propuestas de diseño la frontera de ROI sin conexiones externas, el criterio de residuo detallado y la reconstrucción separada. Marching Cubes continúa como candidato técnico de reconstrucción, sujeto a validación. Son candidatos detallados la normalización, ponderación anisotrópica, orden de ejes, umbral 0.5, tratamiento de geometrías y convenciones de evaluación. No dar por aprobado un valor de beta/omega, un formato volumétrico definitivo o un límite de rendimiento mediante este documento.

**Siguiente paso:** inspeccionar datos 2D/3D autorizados y confirmar formatos, modalidades, geometría y etiquetas; contrastar las decisiones propuestas con esa inspección; acordar arquitectura y contratos antes del PR de alineación. Conservar avances de infraestructura y pruebas que sigan siendo pertinentes. No se modifica GitHub ni se crea código definitivo mediante esta especificación.

## 13. Referencias verificadas para el fundamento

1. Grady, L. (2006). *Random Walks for Image Segmentation*. IEEE Transactions on Pattern Analysis and Machine Intelligence, 28(11), 1768–1783. DOI: [10.1109/TPAMI.2006.233](https://doi.org/10.1109/TPAMI.2006.233). [Registro y resumen](https://pubmed.ncbi.nlm.nih.gov/17063682/). Fundamenta Random Walker en grafos de dimensión arbitraria y segmentación por semillas.
2. Hanke, M.; Neumann, M.; Niethammer, W. (1991). *On the spectrum of the SOR operator for symmetric positive definite matrices*. Linear Algebra and its Applications, 457–472. DOI: [10.1016/0024-3795(91)90389-E](https://doi.org/10.1016/0024-3795(91)90389-E). El resumen explicita el teorema de convergencia para SPD y 0<ω<2 y la dificultad de determinar omega óptimo en general.
3. NiBabel. [Coordinate systems and affines](https://nipy.org/nibabel/coordinate_systems.html). Documentación de coordenadas de vóxel y transformación afín a espacio de referencia. Orientación y geometría deben conservarse.
4. scikit-image. [API skimage.measure.marching_cubes](https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.marching_cubes). Orden de coordenadas, parámetros de espaciamiento y salidas de vértices/caras.

Referencias consultadas para fundamentar el diseño. No se ha instalado ni validado la compatibilidad de NiBabel, scikit-image o Three.js con el entorno bloqueado del proyecto. Las derivaciones, los ejemplos y las propuestas de diseño anteriores se elaboraron para NeuroVision, no son citas textuales del docente ni resultados de esos artículos.
