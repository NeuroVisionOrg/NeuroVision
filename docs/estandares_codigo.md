# Estándares de código y mantenibilidad — NeuroVision

**Versión 0.1.** Base técnica acordada para las cinco capas; las configuraciones específicas deberán validarse tras instalar las herramientas.

## Reglas fundamentales

1. Una responsabilidad identificable por función/módulo; Control coordina pero no reimplementa la lógica especializada.
2. Sin variables ni importaciones sin usar, funciones obsoletas, bloques comentados como respaldo ni código muerto.
3. Nombres claros, explícitos y estables; contratos tipados. Evitar `Any` y `any` injustificados.
4. No se permiten excepciones capturadas y omitidas silenciosamente.
5. No crear dependencias circulares ni importaciones prohibidas; `contratos/` no es una sexta capa.
6. Los solvers se implementan de forma independiente, con infraestructura compartida solo cuando haya un motivo real.
7. No modificar matrices del llamador, ni densificar sin justificar, ni presentar no convergencia como éxito.
8. No copiar credenciales ni imágenes médicas sensibles al repositorio.

## Automatización

| Herramienta | Alcance | Contrato de calidad |
| --- | --- | --- |
| Ruff | Python | `F401` import sin usar, `F841` variable sin usar, `C901` complejidad, orden de imports |
| mypy | Python 3.13 | `strict=true` y errores de tipado bloqueantes |
| Import Linter | Python | Control encima de tres capas hermanas independientes; contratos abajo |
| pytest | Python | Pruebas por componente, arquitectura y API |
| TypeScript | Frontend | `strict`, `noUnusedLocals`, `noUnusedParameters` |
| ESLint | Frontend | Variables sin usar, orden y límites de imports entre features |
| Prettier | Frontend | Formato estable |
| Vitest | Frontend | Geometría y comportamiento comprobables |
| pre-commit | Repositorio | Archivos, claves, formato y mensajes de commit |
| GitHub Actions | Integración | `workflow_dispatch` exclusivamente manual |

**Complejidad:** McCabe = 10 como regla inicial. Una excepción matemática debe ser localizada, revisada, probada y justificada. No deshabilitar globalmente el análisis.

**Convenciones:** Python `snake_case` para funciones/variables y `PascalCase` para tipos. TypeScript `camelCase` y `PascalCase`. Identificadores de contratos conservan sus nombres pactados. `ruff format` y Prettier son las fuentes de formato, evitando cambios estilísticos manuales en PR.

## Reglas arquitectónicas

- `capa_1_interfaz/` no importa código Python; solo HTTP.
- `capa_2_control/` valida y coordina mediante `api_publica` de cada capa especializada.
- `capa_3_traduccion/`, `capa_4_metodos/` y `capa_5_servicios/` son independientes.
- `capa_4_metodos/` no usa FastAPI, Pillow, gráficos ni código de interfaz.
- `contratos/` no importa ninguna de las cinco capas.

El comprobador AST identifica importaciones explícitas directas; Import Linter complementará dependencias transitivas. Ninguna herramienta garantiza por sí sola el diseño correcto: el PR debe revisarse.

## Añadir tecnologías más adelante

Evaluar necesidad, capa propietaria, impacto en contratos, compatibilidad Python/Node, rendimiento, seguridad, mantenibilidad, esfuerzo y pruebas. Incorporar dependencias nuevas mediante PR con trazabilidad y bloqueo de versiones cuando esté disponible.

## Revisión de PR y excepciones

Cada PR declara requisitos o tarea Jira, contratos afectados, evidencias, casos límite y resultado de calidad. No usar `noqa`, `type: ignore` ni desactivar reglas ESLint para ocultar errores: toda excepción requiere explicación precisa y revisión.
