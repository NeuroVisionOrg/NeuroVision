# Modelo matemático — Random Walker binario 2D

**Estado:** candidato principal seleccionado para implementación y validación experimental. No están verificados aún rendimiento ni calidad en imágenes cerebrales.

## Formulación

Para una ROI de píxeles en escala de grises normalizada, definir un grafo no dirigido con conectividad inicial de cuatro vecinos. Cada arista tiene peso simétrico positivo:

\[
w_{ij}=\exp\bigl[-\beta(g_i-g_j)^2\bigr],\quad \beta\ge 0.
\]

El Laplaciano ponderado es \(L=D-W\). Las semillas están en \(M\) y los píxeles desconocidos en \(U\). Fijando las semillas de primer plano a 1 y las de fondo a 0, la ecuación de Dirichlet discreta es:

\[
L_{UU}p_U=-L_{UM}p_M,
\qquad A=L_{UU},\qquad b=-L_{UM}p_M.
\]

El objetivo de los cuatro métodos es resolver **el mismo** sistema \(Ax=b\) y reconstruir el mapa de probabilidades en la ROI.

## Condiciones de validez

- Cada arista tendrá peso finito, positivo y simétrico.
- Cada componente de incógnitas estará conectada a una semilla mediante pesos positivos.
- Cada clase binaria contará con semillas y existirá al menos una incógnita.
- Se evitarán subdesbordamientos que conviertan pesos positivos teóricos en ceros efectivos.
- El borde de la ROI no conectará con nodos externos en la primera versión.

Para \(z\ne0\), la forma cuadrática reducida es:

\[
z^T A z = \sum_{\{i,j\}\subseteq U} w_{ij}(z_i-z_j)^2
+\sum_{i\in U,j\in M} w_{ij}z_i^2.
\]

Bajo las condiciones de conectividad, esta expresión es positiva; por tanto \(A\) es simétrica definida positiva. Jacobi necesita además la estructura de dominancia diagonal del Laplaciano reducido; no se debe afirmar que converge para cualquier matriz SPD. Gauss-Seidel, SOR y SSOR se justifican para SPD; SOR y SSOR requieren \(0<\omega<2\).

## Comparación

Registrar tiempo de solución **sin decodificación de imágenes**, residuos calculados sobre el sistema original, número de iteraciones completas y barridos, estado de convergencia y parámetros. SSOR realiza dos barridos por iteración completa.

El número de incógnitas será \(n=N-s\), con \(N\) píxeles de ROI y \(s\) semillas. La cuadrícula de cuatro vecinos tiene a lo sumo cinco elementos no nulos por fila, es decir, \(\mathrm{nnz}(A)\le5n\). Esto no garantiza que las iteraciones converjan rápidamente.

## Caso de prueba base

\[
A=\begin{pmatrix}2&-1\\-1&2\end{pmatrix},\qquad
b=\begin{pmatrix}0\\1\end{pmatrix},\qquad
x=\begin{pmatrix}1/3\\2/3\end{pmatrix}.
\]

En este esqueleto existe una prueba de validación estructural y una solución de referencia usando NumPy; aún falta implementar la generación real del laplaciano y los cuatro algoritmos.

## Medición pendiente

ROIs sugeridas: 32 × 32, 64 × 64 y 128 × 128. Medir residual, barridos, tiempo y memoria en hardware identificado; elegir beta, omega y límite de ROI a partir de evidencias, no arbitrariamente.

**Referencia:** Grady, L. (2006). *Random Walks for Image Segmentation*. IEEE TPAMI. DOI: https://doi.org/10.1109/TPAMI.2006.233.
