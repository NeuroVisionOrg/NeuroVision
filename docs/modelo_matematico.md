# Modelo matemático de NeuroVision

**Segmentación 3D de un tumor con Random Walker, resuelta con SOR**

Versión 0.3. Entregable 1 de la capa 4 (métodos numéricos).
Proyecto académico sin uso clínico. Las pruebas usan solo datos sintéticos.

---

## 1. Objetivo

Dado un conjunto de cortes de una resonancia, decidir para cada vóxel si pertenece al tumor
o al tejido sano. El usuario marca algunos vóxeles seguros (semillas) y el modelo calcula el
resto resolviendo un sistema lineal $`Ax=b`$.

## 2. Datos de entrada

La capa 3 (función `cargar_imagen_gris`) recibe cada corte en JPG o PNG. Si la imagen está en
color, Pillow la pasa a gris con

```math
L = 0.299\,R + 0.587\,G + 0.114\,B .
```

Después, `imagen_a_matriz` divide cada píxel entre 255 para dejarlo entre 0 y 1:

```math
g = \frac{L}{255}, \qquad 0 \le g \le 1 .
```

El resultado de cada corte es una matriz `float32` de tamaño $`Y \times X`$.

## 3. Volumen 3D

Se apilan $`Z`$ cortes del mismo tamaño, uno detrás de otro:

```math
V \in [0,1]^{Z \times Y \times X}, \qquad g_i = V[z, y, x] .
```

Cada vóxel recibe un número único $`i`$, en el mismo orden que usa NumPy (`ravel`):

```math
i = z\,(Y X) + y\,X + x .
```

El total de vóxeles es $`N = Z\,Y\,X`$.

## 4. Grafo y pesos

Cada vóxel se conecta con sus **6 vecinos**: izquierda y derecha ($`x \pm 1`$), arriba y abajo
($`y \pm 1`$), y los cortes anterior y siguiente ($`z \pm 1`$).

Cada conexión tiene un peso que indica qué tan parecidos son los dos vóxeles:

```math
w_{ij} = e^{-\beta\,(g_i - g_j)^2} + \varepsilon .
```

- Si los brillos son parecidos, $`w_{ij} \approx 1`$.
- Si son muy distintos (un borde del tumor), $`w_{ij} \approx 0`$.
- $`\beta`$ controla qué tan fuertes son los bordes. El valor inicial de pruebas es $`\beta = 90`$.
- $`\varepsilon = 10^{-6}`$ es un peso mínimo para que ninguna zona quede aislada.

El peso es simétrico ($`w_{ij} = w_{ji}`$) y siempre positivo.

## 5. Semillas

El usuario marca dos grupos de vóxeles:

- semillas de tumor $`M_T`$, con valor $`1`$;
- semillas de fondo $`M_F`$, con valor $`0`$.

El resto son las incógnitas $`U`$. Se necesitan semillas de los dos tipos y al menos una
incógnita.

## 6. Construcción del sistema $`Ax = b`$

**Idea.** $`x_i`$ es la probabilidad de que un caminante que sale del vóxel $`i`$ y se mueve al
azar, prefiriendo los pesos grandes, llegue primero a una semilla de tumor.

**Paso 1. Ecuación de cada vóxel.** La probabilidad de un vóxel es el promedio ponderado de
la de sus vecinos:

```math
x_i = \frac{\sum_{j \sim i} w_{ij}\,x_j}{\sum_{j \sim i} w_{ij}} .
```

**Paso 2. Pasar todo a un lado.** Con el grado $`d_i = \sum_{j \sim i} w_{ij}`$:

```math
d_i\,x_i - \sum_{j \sim i} w_{ij}\,x_j = 0 .
```

**Paso 3. Matriz Laplaciana.** Escribiendo esas ecuaciones para todos los vóxeles se obtiene
la matriz $`L = D - W`$:

```math
L_{ii} = d_i, \qquad L_{ij} = -w_{ij} \;\text{ si } i \sim j, \qquad L_{ij} = 0 \;\text{ en otro caso.}
```

**Paso 4. Separar lo conocido de lo desconocido.** Las semillas ya tienen valor. Ordenando
primero las incógnitas $`U`$ y después las semillas $`M`$:

```math
L_{UU}\,x_U = -L_{UM}\,x_M .
```

**Paso 5. Resultado.**

```math
A = L_{UU}, \qquad
b_i = \sum_{j \in M_T,\; j \sim i} w_{ij} .
```

Es decir, $`b_i`$ es la suma de los pesos que unen al vóxel $`i`$ con semillas de tumor. Las
semillas de fondo valen 0 y no aportan nada a $`b`$.

## 7. Propiedades de la matriz $`A`$

**Simétrica.** $`A_{ij} = A_{ji}`$, porque $`w_{ij} = w_{ji}`$.

**Dispersa.** Cada fila tiene como máximo 7 valores distintos de cero (el vóxel y sus 6
vecinos):

```math
\mathrm{nnz}(A) \le 7n, \qquad n = N - |M| .
```

Se guarda en formato CSR y nunca como matriz completa.

**Definida positiva.** Para cualquier vector $`z \neq 0`$:

```math
z^{T} A z = \sum_{\{i,j\} \subseteq U} w_{ij}\,(z_i - z_j)^2
+ \sum_{i \in U} \Big( \sum_{j \in M,\; j \sim i} w_{ij} \Big) z_i^2 .
```

Los dos términos son sumas de cuadrados con pesos positivos, así que $`z^T A z \ge 0`$. Solo
podría valer 0 si todos los $`z_i`$ de una zona fueran iguales y esa zona no tocara ninguna
semilla. Por eso, **si cada zona de incógnitas toca al menos una semilla**, $`z^T A z > 0`$ y
$`A`$ es **simétrica definida positiva (SPD)**. Comprobar esa condición le corresponde a la capa 3.

**Diagonal dominante (M-matriz).** La diagonal es positiva, los valores fuera de ella son
$`\le 0`$, y en cada fila

```math
a_{ii} \ge \sum_{j \ne i} |a_{ij}| ,
```

con desigualdad estricta en las filas que tocan semillas.

**Bipartita.** Moverse a un vecino cambia $`x + y + z`$ en una unidad. Si se pintan de rojo los
vóxeles con $`x + y + z`$ par y de negro los impares, ningún vecino comparte color. Esto permite
recorrer las incógnitas en orden **rojo-negro**.

## 8. Método de solución: SOR

SOR parte de una solución inicial (por ejemplo, todo en cero) y la mejora en cada vuelta $`k`$,
recorriendo las incógnitas una por una y usando los valores que acaba de actualizar:

```math
x_i^{(k+1)} = (1 - \omega)\,x_i^{(k)} + \frac{\omega}{a_{ii}}
\Big( b_i - \sum_{j < i} a_{ij}\,x_j^{(k+1)} - \sum_{j > i} a_{ij}\,x_j^{(k)} \Big).
```

Con $`\omega = 1`$ es Gauss-Seidel. Con $`1 < \omega < 2`$ se acelera la convergencia.

**Por qué converge.** Como $`A`$ es SPD, el teorema de Ostrowski–Reich garantiza que SOR
converge para cualquier $`0 < \omega < 2`$. Fuera de ese rango no converge (teorema de Kahan).

**Mejor $`\omega`$.** Con el orden rojo-negro vale la fórmula de Young:

```math
\omega_{opt} = \frac{2}{1 + \sqrt{1 - \rho_J^{\,2}}},
```

donde $`\rho_J`$ es el radio espectral de la matriz de Jacobi $`I - D^{-1}A`$. Su estimación y la
validación experimental son parte del Entregable 2.

**Por qué no un método directo.** Un volumen de $`64^3`$ da unas 236 000 incógnitas. Como matriz
completa ocuparía unos 440 GB; en CSR ocupa unos 20 MB. SOR solo necesita la matriz dispersa y
unos pocos vectores.

## 9. Criterio de parada

El residuo mide cuánto falla la solución actual:

```math
r^{(k)} = b - A\,x^{(k)} .
```

SOR se detiene cuando

```math
\lVert r^{(k)} \rVert_2 \le \max\big(\text{atol},\; \text{rtol}\,\lVert b \rVert_2\big),
```

con $`\text{rtol} = 10^{-6}`$ y $`\text{atol} = 10^{-10}`$ como valores iniciales. Si se alcanza el
máximo de iteraciones sin cumplirlo, el resultado se reporta como `MAX_ITERATIONS`, nunca como
éxito.

## 10. Ejemplo resuelto

Cuatro vóxeles en línea: `T – a – c – F`. `T` es semilla de tumor y `F` semilla de fondo. Sus
valores de gris, tal como los entrega `imagen_a_matriz`, son:

```math
g_T = \tfrac{204}{255} = 0.800,\quad
g_a = \tfrac{199}{255} = 0.780,\quad
g_c = \tfrac{51}{255} = 0.200,\quad
g_F = \tfrac{46}{255} = 0.180 .
```

**Pesos** con $`\beta = 90`$:

```math
w_{Ta} = e^{-90(0.02)^2} + \varepsilon \approx 0.966, \qquad
w_{ac} = e^{-90(0.58)^2} + \varepsilon \approx 0.000001, \qquad
w_{cF} \approx 0.966 .
```

Entre `a` y `c` hay un borde (de 0.78 a 0.20), así que el peso es casi cero.

**Ecuaciones:**

```math
\begin{aligned}
(w_{Ta} + w_{ac})\,x_a - w_{ac}\,x_c &= w_{Ta}\cdot 1 \\
-w_{ac}\,x_a + (w_{ac} + w_{cF})\,x_c &= w_{cF}\cdot 0
\end{aligned}
```

**Sistema:**

```math
A = \begin{pmatrix} 0.966001 & -0.000001 \\ -0.000001 & 0.966001 \end{pmatrix},
\qquad
b = \begin{pmatrix} 0.966 \\ 0 \end{pmatrix}.
```

**Solución:** $`x_a \approx 0.999999`$ y $`x_c \approx 0.000001`$. Con el umbral 0.5, `a` es
tumor y `c` es fondo. El borde detuvo al caminante, como se esperaba.

## 11. Reconstrucción del resultado

1. Se crea un vector de tamaño $`N`$ y se colocan las semillas: 1 para tumor y 0 para fondo.
2. Se colocan los valores $`x_i`$ en las posiciones de las incógnitas.
3. Se reorganiza en forma $`Z \times Y \times X`$: es el **mapa de probabilidades**.
4. Máscara del tumor: un vóxel es tumor si $`x_i \ge 0.5`$.
5. Como las probabilidades están entre 0 y 1, cada corte se puede volver imagen con la función
   `matriz_a_imagen` de la capa 3, que calcula $`\mathrm{redondeo}(255 \cdot x)`$.

## 12. Estructura base de la capa 4

- `capa_4_metodos/residuo.py`: calcula $`\lVert b - Ax \rVert_2`$ y el umbral de parada de la
  sección 9.
- `capa_4_metodos/api_publica.py`: única puerta de entrada para la capa 2.
- `tests/apoyo/sistemas_3d.py`: crea volúmenes sintéticos y su sistema $`Ax=b`$ siguiendo las
  secciones 3 a 6, para probar la capa 4 sin depender de la capa 3.
- `tests/unit/test_modelo_3d.py`: comprueba con números las propiedades de la sección 7
  (simetría, máximo 7 no nulos por fila, M-matriz, SPD), que las probabilidades quedan entre 0
  y 1, y el cálculo del residuo.

La capa 4 solo recibe `LinearSystem` (contrato $`A`$, $`b`$). No usa Pillow ni FastAPI, y no
cambia si el problema es 2D o 3D.

## 13. Pendientes para las otras capas

- Adaptar los contratos `ImageData`, `ROISelection` y `Seed` a volúmenes $`(Z, Y, X)`$.
- La capa 3 debe construir $`A`$ y $`b`$ como en la sección 6 y verificar que cada zona de
  incógnitas toque una semilla.

## Referencias

- Grady, L. (2006). *Random Walks for Image Segmentation*. IEEE TPAMI. DOI
  10.1109/TPAMI.2006.233.
- Young, D. M. (1971). *Iterative Solution of Large Linear Systems*. Academic Press.
- Saad, Y. (2003). *Iterative Methods for Sparse Linear Systems*, cap. 4. SIAM.
