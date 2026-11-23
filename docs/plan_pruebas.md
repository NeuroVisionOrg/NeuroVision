# Plan de pruebas — NeuroVision

**Versión 0.1.** Las pruebas incluidas en este esqueleto son solamente el inicio. Los casos pendientes no se consideran aprobados.

## Priorización

- **P0:** obligatorio para integrar el comportamiento relacionado.
- **P1:** obligatorio antes de la entrega final del MVP.
- **P2:** ampliación opcional, condicionada al presupuesto de horas.

## Casos de prueba por capa

| ID | Responsable | Caso | Resultado esperado | Prioridad | Estado |
| --- | --- | --- | --- | --- | --- |
| UI-01 | Johan | Carga PNG | Imagen y dimensiones correctas | P0 | Pendiente |
| UI-02 | Johan | ROI tras zoom y pan | Coordenadas originales constantes | P0 | Prueba unitaria de coordenadas escrita; Vitest pendiente de ejecutar |
| UI-03 | Johan | Semillas FG/BG | Etiquetas y posiciones válidas | P0 | Contrato Python probado; UI pendiente |
| UI-04 | Johan | Máscara y contornos | Superposición correcta en imagen | P0 | Pendiente |
| UI-05 | Johan | Estados no convergentes | No se presenta máscara inválida | P0 | Pendiente |
| CT-01 | Jherson | `GET /api/v1/health` | HTTP 200 y JSON correcto | P0 | Prueba ejecutada |
| CT-02 | Jherson | ROI, dimensiones y semillas | Errores explícitos | P0 | Pruebas unitarias ejecutadas |
| CT-03 | Jherson | Comparación de cuatro métodos | Mismo sistema, configuración comparable | P0 | Pendiente |
| CT-04 | Jherson | Petición de segmentación | Esquema y manejo de errores | P0 | Pendiente |
| TR-01 | Yenderson | Decodificar PNG y JPEG | Matriz gris normalizada válida | P0/P1 | Pendiente |
| TR-02 | Yenderson | Grafo 4 vecinos | Pesos y adyacencias verificables | P0 | Pendiente |
| TR-03 | Yenderson | Sistema de cadena 4 píxeles | A y b exactos | P0 | Contrato validado; construcción pendiente |
| TR-04 | Yenderson | Componente sin semillas | Rechazo antes del solver | P0 | Pendiente |
| TR-05 | Yenderson | Reconstrucción | Valores de semillas, forma y posición | P0 | Pendiente |
| MT-01 | Jennifer | Jacobi | Solución exacta aproximada y residuo válido | P0 | Pendiente |
| MT-02 | Jennifer | Gauss-Seidel | Solución exacta aproximada y residuo válido | P0 | Pendiente |
| MT-03 | Jennifer | SOR | Solución exacta aproximada y residuo válido | P0 | Pendiente |
| MT-04 | Jennifer | SSOR | Solución exacta aproximada y dos barridos | P0 | Contrato de conteo probado; solver pendiente |
| MT-05 | Jennifer | No convergencia, omega inválido, NaN | Estados y errores explícitos | P0 | Validación de omega probada; resto pendiente |
| MT-06 | Jennifer | No mutación de A y b | Entradas intactas | P0 | Pendiente |
| SV-01 | Yenderson | Dice e IoU conocidos | Cálculos correctos | P0 | Pendiente |
| SV-02 | Yenderson | Referencia ausente | Métricas ausentes | P0 | Pendiente |
| SV-03 | Yenderson | PNG, CSV y JSON | Archivos reproducibles | P1 | Pendiente |
| AR-01 | Jherson | Importación entre capas prohibida | Análisis estático falla | P0 | Prueba de reglas AST ejecutada; Import Linter sin ejecutar |
| IN-01 | Todos | ROI → Ax=b → cuatro métodos → máscara | Flujo correcto completo | P0 | Pendiente |
| PF-01 | Jennifer/Yenderson | ROI 32, 64, 128 | Medidas reproducibles | P1 | Pendiente |

## Tipos de comprobación

- **Unitarias:** pytest y Vitest para lógica pura y errores esperados.
- **Contratos:** dataclasses/Pydantic, dimensiones y estados.
- **Arquitectura:** Import Linter + pruebas AST para accesos prohibidos.
- **Integración:** HTTPX/pytest y recorrido entre capas.
- **Rendimiento:** `perf_counter` y tamaño real de cada ROI, sobre hardware documentado.
- **Calidad estática:** Ruff, formato, mypy, ESLint, TypeScript y Prettier.

## Evidencia mínima por PR

Cada PR debe señalar qué IDs prueba, los comandos utilizados, su resultado, el SHA del código evaluado y los casos inválidos cubiertos. **Un CI manual parcial no autoriza la integración.** Un CI completo solo valida el código y la base específicos que examinó.

## Definición de terminado

El código deberá pasar sus pruebas correspondientes, mantener contratos y dependencias, respetar calidad estática, documentar cambios y obtener revisión aprobada y validación completa del CI manual para el commit definitivo.

## Presupuesto

El presupuesto provisional es de 80 horas-persona en tres semanas, sujeto a confirmación. Se priorizan P0; no se obliga a automatizar pruebas E2E complejas antes de contar con el flujo básico funcional.
