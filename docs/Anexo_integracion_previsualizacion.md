# PL-02 — Frontera de previsualización de Control

**Estado:** propuesta de integración técnica para revisión con Traducción. No acredita lectura ni segmentación real. El esquema HTTP v2 vigente se conserva.

## Operaciones públicas que debe proporcionar Traducción

- `leer_datos(content: bytes, mode: InputMode, *, limits: DataReadLimits) -> DecodedData`
- `previsualizar(data: DecodedData) -> PreviewData`

Los tipos compartidos están en `contratos/admision.py`, `contratos/datos.py` y `contratos/geometria.py`. `DataReadLimits` concreta el presupuesto C-06/C-09: bytes descomprimidos, tamaño máximo de un eje y número de elementos. Traducción debe verificar estos límites **antes** de expandir datos o asignar arreglos, además de la admisión escalar y geométrica. El lector comunica fallos previstos mediante `DataReadError(DataReadCode...)`, sin importar HTTP ni Control. Control traduce códigos a HTTP; los errores inesperados son 500 sin trazas en la respuesta.

El lector calcula `source_digest` del archivo original y la vista conserva ese SHA-256 como `input_id`. Control lo recalcula para detectar inconsistencias y exige que modo y geometría de vista coincidan con los datos decodificados. Las advertencias públicas no deben contener datos privados, rutas ni identificadores personales. El identificador no acredita procedencia clínica ni autenticación.

## Composición de la aplicación

`create_app(limits, translation=operaciones)` registra `POST /api/v1/previsualizar` solo si se proporcionan la política explícita y las dos operaciones. `main.py` continúa usando `create_app()` sin proveedor; por ello la aplicación principal publica únicamente health (además de la documentación HTTP). No se habilita una ruta con datos inventados. Los dobles que generan `DecodedData` y `PreviewData` viven únicamente en pruebas.

La ruta recibe multipart `image` como archivo y `request` como texto JSON v2. Rechaza partes adicionales, duplicados y formas incompatibles. El cuerpo completo está acotado por la frontera ASGI antes del parser; el JSON se comprueba como texto recodificado a UTF-8 antes de Pydantic. Se limita el archivo antes del lector, se vuelve a verificar el dominio tras la lectura, se limita la respuesta y se utiliza `Cache-Control: no-store`. El cupo no bloqueante de previsualización se mantiene durante el parsing y el procesamiento, se libera al terminar o fallar, y los archivos se cierran al salir del formulario. El trabajo síncrono de lectura y preparación se delega a un hilo; no se prometen cancelación ni tiempo máximo. No hay persistencia ni cache nueva.

## Puertas pendientes

1. Acordar con Yenderson la firma concreta y los códigos de admisión; publicar las funciones reales en `capa_3_traduccion/api_publica.py`.
2. Verificar admisión antes de asignar memoria, incluida expansión NIfTI comprimida; la segunda defensa de Control no sustituye esta prueba.
3. Definir una política local de recursos basada en medidas. No hay valores de producción predeterminados. El cuerpo acotado puede existir en memoria antes de adquirir el cupo y puede haber copias de los datos: el cupo no implica una cota global de RAM ni un límite global entre procesos. Coordinar también los cupos de las futuras rutas.
4. Conectar el proveedor real y comprobar JPEG/PNG escalar y NIfTI sintéticos de extremo a extremo; validar con Johan la carga multipart y los DTO. No publicar datos médicos en el repositorio.
5. Mantener pendientes las validaciones de CT-01/02/03/06/07/10 que dependan del proveedor, políticas definitivas o pruebas en navegador. No confundir el resultado de las pruebas con dobles con la aceptación funcional del MVP.
