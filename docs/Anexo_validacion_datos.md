# NeuroVision — Anexo de selección e inspección de datos 2D/3D

**Versión:** 0.2 | **Fecha:** 25 de noviembre de 2026\
**Estado:** inspección estructural y de intensidades realizada sobre los ZIP aportados; admisión definitiva de casos y validación de segmentación pendientes.\
**Vinculación:** ERS v0.2, casos de uso v0.2, modelo matemático v0.2 y registro de decisiones v1.4. Sustituye la v0.1 del anexo, que describía los datos aún no disponibles. No es un octavo documento principal.

## 1. Objetivo y decisión de alcance

D-06: el líder limita el procesamiento de imágenes 2D y 3D a escala de grises (intensidad escalar, una modalidad por ejecución). No se implementará segmentación RGB ni fusión multimodal en el MVP. Escala de grises no significa umbralizar la resonancia: preservar sus niveles de intensidad hasta la normalización. Las máscaras de referencia y las máscaras producidas son datos diferentes; las últimas se obtienen exclusivamente del resultado de SOR. Los colores de una posible superposición, marcadores o malla son presentación y no añaden canales al cálculo.

Se inspeccionaron localmente los dos archivos ZIP proporcionados, sin incorporarlos al repositorio ni convertirlos. No se instaló una dependencia nueva del producto. La inspección utiliza Python, zipfile, Pillow, NumPy y lectura de cabeceras MetaImage con descompresión zlib. No constituye una ejecución de SOR, una prueba de la aplicación ni una certificación clínica.

## 2. Evidencias de entrada

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| BRISC 2025.zip (ZIP externo, nombre con emoji) | 256864086 | `de73c0aa6cad59ea74122164cbfbec389102fbb7852f06f00e8328cc43f8319c` |
| braintumor.zip | 9561141 | `3246d9f3f66d383125c3298167868492f7a9c7c93d83d7057352c7d46594db25` |

BRISC: el ZIP externo contiene `brisc2025.zip`; su ZIP interno tiene 15.586 archivos: 10.793 JPEG y 4.793 PNG. Hay 6.000 JPEG en la tarea de clasificación y 4.793 pares en la tarea de segmentación. No son 10.793 casos independientes. El ZIP interno no contiene manifiestos ni licencias. El artículo aportado, DOI 10.1038/s41597-026-06753-y, describe los 6.000 cortes y 4.793 pares en su página 4. No se reconstruirá un volumen anatómico a partir de BRISC: los cortes carecen de vinculación fiable entre pacientes y series.

## 3. BRISC: inspección real de la tarea de segmentación

| Comprobación | Resultado |
|---|---|
| Pares JPEG/PNG emparejados por nombre base y partición | 4.793 (3.933 train; 860 test) |
| Archivos sin pareja | 0 |
| Discrepancias de ancho/alto | 0 |
| JPEG en modo L | 2.866 |
| JPEG en modo RGB | 1.927 |
| RGB con R=G=B en todos sus píxeles | 1.927 de 1.927 |
| Errores de decodificación detectados en imágenes y máscaras | 0 |
| Dimensiones más frecuentes | 512 × 512 (4.504 pares) |
| Cantidad de dimensiones distintas | 140 |
| Máscaras en modo L | 4.793 |
| Valores observados en todas las máscaras | 0–10 y 246–255 (todos los enteros de ambos intervalos presentes en el conjunto) |
| Máscaras vacías después de aplicar umbral >=128 | 0 |

Método: enumeración del ZIP interno, correspondencia entre `images` y `masks` en cada partición, lectura de dimensiones/modos, decodificación de todos los JPEG de segmentación, comparación exacta de canales RGB y cálculo de histogramas de cada PNG. Primero se inspeccionó una muestra estratificada de 54 pares (tres por combinación partición/tipo/plano), luego se extendió la comprobación de canales y máscaras al conjunto completo de segmentación. No se comprobó el contenido de todos los JPEG de clasificación ni la alineación anatómica de los 4.793 pares. No se confrontaron checksums con un manifiesto oficial.

Regla propuesta de admisión: JPEG/PNG escalar o RGB acromático verificado; convertir RGB acromático a L sin pérdida de información. Rechazar RGB con canales diferentes, en vez de introducir procesamiento de color sin acuerdo. Validar forma, tipo, finitud, orientación EXIF, límites y errores de decodificación. Conservar la forma original; no imponer 512 × 512. Para las referencias BRISC comprobadas, convertir por `M_ref = (mask >= 128)`. No generalizar esta regla a máscaras de otros datasets sin examinar su semántica. Mantener referencias separadas de las semillas, ROI y ajuste de parámetros de evaluación.

## 4. ITK-SNAP Brain Tumor: inspección real

El README incluido identifica el origen en el desafío MICCAI BraTS 2012 y declara datos anonimizados. No contiene una licencia específica. Se ignoraron archivos auxiliares de macOS, archivos swap y demás archivos no necesarios; no se ejecutaron. Los cinco archivos de imagen útiles pertenecen al caso BRATS_HG0015. Son MetaImage (.mha), no NIfTI.

Los cinco encabezados coinciden en DimSize (X,Y,Z) = (160,216,176), NDims=3, ElementSpacing=(1,1,1), TransformMatrix identidad y Offset=(-76.994,-135.424,-90.2048). El encabezado declara AnatomicalOrientation=RAI. No se interpreta esa cadena de forma aislada como una afín NIfTI RAS+. El tipo es MET_SHORT (int16 con signo), little endian, comprimido zlib y LOCAL. Cada carga contiene 6.082.560 valores escalares finitos. El espaciado de 1 mm es la interpretación física prevista del volumen médico; verificar las unidades y convenciones en el lector/conversor antes de publicar medidas físicas.

| Archivo | Mínimo | Máximo |
|---|---:|---:|
| BRATS_HG0015_FLAIR.mha | 0 | 1610 |
| BRATS_HG0015_T1.mha | 0 | 1537 |
| BRATS_HG0015_T1C.mha | 0 | 2592 |
| BRATS_HG0015_T2.mha | 0 | 2275 |
| BRATS_HG0015_truth.mha | 0 | 2 |

La tabla LabelTable del archivo de proyecto `BRATS_HG0015.itksnap` asigna el índice 1 a Edema y el índice 2 a Active tumor. Se observaron exactamente las etiquetas 0, 1 y 2.

| Etiqueta | Interpretación | Vóxeles |
|---|---|---:|
| 0 | Fondo | 5.901.544 |
| 1 | Edema (Edema) | 108.706 |
| 2 | Tumor activo (Active tumor) | 72.310 |

**Propuesta pendiente de aprobación:** seleccionar T1C para el primer piloto binario y evaluar `M_ref = (truth == 2)`; no confundir tumor activo con la unión edema + tumor. Definir semillas de forma independiente de la referencia. La geometría coincidente en cabeceras no certifica alineación anatómica. El volumen completo puede cargarse y visualizarse, pero la segmentación utilizará ROI de tamaño justificado por benchmarks. No inferir el tiempo de SOR a partir del tamaño del ZIP.

## 5. Consecuencias sobre arquitectura y contratos

| Elemento | Propuesta |
|---|---|
| ImageData | Matriz escalar `(alto, ancho)`, sin eje de canales |
| VolumeData | Tres ejes espaciales; una secuencia por ejecución; convención de ejes acordada en contratos |
| Intensidades | Mantener rango original para validación y normalización; float32 normalizado [0,1] como línea base; no reducir NIfTI a uint8 antes del cálculo |
| Máscaras | Binarias en el algoritmo; conversión de referencia específica por dataset |
| Formato 3D de entrada | Mantener NIfTI como candidato del MVP; convertir MHA externamente con herramienta médica validada (por ejemplo ITK-SNAP) antes de admitir ese caso |
| Conversión | Sin interpolación cuando se conserva la cuadrícula; verificar correspondencia de índices, valores, afín, orientación, unidades y etiquetas después de conversión, incluyendo ROI desplazada |
| ROI | Limitar por resultados de rendimiento; no fijar máximo a partir de los tamaños nominales |
| Modelo numérico | Random Walker escalar 4/6 vecinos y un SOR CSR para ambos modos |
| Visor | Escala de grises para la resonancia; marcador/contorno de contraste opcional exclusivamente visual |

No ampliar automáticamente el producto a MHA, 4D, RGB, DICOM o fusión de secuencias por el hecho de recibir este ZIP. Una conversión externa del caso de investigación no implica añadir una librería al producto. Mantener una escala de normalización coherente en el volumen/ROI; no renormalizar cada corte por separado para la construcción del grafo. El tratamiento preciso de intensidad constante, anisotropía y límites queda para el diseño matemático y pruebas.

## 6. Estado de validación

| Comprobación | Estado |
|---|---|
| Acceso a los ZIP, inventario y lectura de datos útiles | Realizado |
| Canales, dimensiones y etiquetas BRISC | Realizado en la tarea de segmentación |
| Estructura, intensidades y etiquetas del caso MHA | Realizado |
| Licencia exacta y edición de cada ZIP | Pendiente de corroborar; licencia del artículo no equivale a licencia de datos |
| Correspondencia anatómica visual, orientación EXIF y contraste de un par de prueba | Pendiente |
| Conversión MHA a NIfTI, validación afín/espacial y carga por NiBabel | Pendiente |
| Validación de SOR, máscaras producidas, métricas y malla | Pendiente |
| Rendimiento y límites de ROI | Pendiente |

Se pueden diseñar arquitectura y contratos provisionales con estas evidencias. No declarar los casos reales definitivamente admitidos hasta resolver permisos, geometría y verificación de referencia. No incluir imágenes ni máscaras en GitHub. Conservar únicamente referencias, metadatos técnicos no identificadores, hashes e instrucciones de adquisición; usar fixtures sintéticos en CI.

## 7. Fuentes de referencia registradas en la versión 0.1

Se conservan las fuentes documentales previas; la inspección actual corresponde a los ZIP del usuario. La licencia específica de cada copia permanece pendiente.

- BRISC, artículo: https://doi.org/10.1038/s41597-026-06753-y ; edición del dataset: https://data.mendeley.com/datasets/c7dj4pwhcv/1 (DOI 10.17632/c7dj4pwhcv.1); edición candidata Kaggle indicada en las fuentes del proyecto: https://www.kaggle.com/datasets/briscdataset/brisc2025/ . No trasladar automáticamente las condiciones de una edición a otra; registrar la edición exacta.
- ITK-SNAP, página de datos: https://itksnap.org/pmwiki/pmwiki.php?n=Downloads.Data ; enlace oficial del ejemplo: https://www.nitrc.org/frs/download.php/6161/braintumor.zip ; listado NITRC: https://www.nitrc.org/frs/?group_id=110&release_id=10087 . La licencia particular del archivo no quedó comprobada; verificar antes de usar o redistribuir. La descarga es un ZIP, no necesariamente un único NIfTI.
- MSD: https://medicaldecathlon.com/ ; https://medicaldecathlon.com/dataaws/ ; https://registry.opendata.aws/msd/ ; artículo https://doi.org/10.1038/s41467-022-30695-9 . Los 4 canales corresponden a modalidades, no al eje de profundidad adicional. No es necesario descargar toda la colección para el piloto.


## 8. Fixtures sintéticos que se propondrán al plan de pruebas

| Fixture | Propósito |
|---|---|
| Cuadrícula 2D pequeña con semillas y solución conocida | Validar índices, A,b y SOR |
| Imagen rectangular no cuadrada y ROI desplazada | Detectar intercambio fila/columna y errores de origen |
| Volumen 3D pequeño (8³ o 16³, no límites de producción) con objeto interior | Verificar grafo 6 vecinos, máscara, cortes y malla |
| Volumen con escala anisótropa, ejes invertidos y origen desplazado | Verificar transformación física y política de geometrías |
| Máscara que toca frontera, máscara vacía, geometría incompatible y archivo inválido | Estados de error y resultados parciales explícitos |

Son diseños de prueba pendientes; no se han ejecutado como pruebas de producto. Si se emplean máscaras sintéticas para comprobar Marching Cubes de forma aislada, diferenciarlas de las máscaras producidas por SOR en la prueba integral.


## 9. Siguiente hito

Preparar `04_Arquitectura.md` y después `contratos.md`, con los puntos de admisión de datos todavía abiertos y una sola modalidad escalar. Antes de admitir casos reales, verificar licencia, realizar conversión externa de los dos archivos MHA seleccionados con su geometría intacta y examinar visualmente la alineación. Mantener las responsabilidades, herramientas y presupuesto acordados; no se modificó GitHub, Jira ni las fuentes activas del proyecto.
