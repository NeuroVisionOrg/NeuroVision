# Registro de verificación del esqueleto — revisión v0.2

**Fecha:** 22 de noviembre de 2026. **Alcance:** entorno temporal local. No equivale a ejecutar GitHub Actions ni garantiza que los cuatro métodos funcionen.

## Comprobaciones realizadas

| Comprobación | Resultado |
| --- | --- |
| `python --version` | Python 3.13.5 |
| `node --version` | Node 22.16.0 |
| `python -m pytest -q` | **24 pruebas aprobadas**, incluidas 2 pruebas para conservar el CI exclusivamente manual |
| `python -m compileall -q ...` | Compilación sintáctica Python correcta |
| `bash -n scripts/ci-local.sh` | Sintaxis correcta |
| `bash -n scripts/validar-candidato-ci.sh` | Sintaxis correcta |
| `tomllib` sobre `pyproject.toml` | Correcto |
| Lectura JSON de `capa_1_interfaz/package.json` | Correcto |
| Lectura YAML de workflow y pre-commit | Correcta |
| Disparadores de `.github/workflows/ci.yml` | **Solo `workflow_dispatch`**, comprobado con prueba automática |
| Candidato Git de dos padres con SHA esperados (repositorio temporal sintético) | Aceptado |
| Mismo candidato con SHA de cabeza incorrecto | Rechazado (salida distinta de cero) |
| `bash scripts/ci-local.sh preflight` | Falla correctamente por 3 archivos de preparación pendientes |

## Bloqueos detectados y no subsanados

- **`requirements.lock` ausente.** Es necesario resolver y bloquear dependencias reales desde PyPI. Los trabajos de Python e integración del CI instalarán desde ese archivo, no desde intervalos abiertos.
- **`capa_1_interfaz/package-lock.json` ausente.** Debe generarse con npm desde un registro accesible, revisarse y confirmarse.
- **`.secrets.baseline` ausente.** Debe generarse y auditarse con `detect-secrets` para habilitar su hook de seguridad.
- No pudieron descargarse paquetes adicionales de PyPI o npm en este entorno: ambos dominios devolvieron errores de resolución DNS. No se ejecutaron Ruff, Ruff Format, mypy, Import Linter, pre-commit, detect-secrets, ESLint, Prettier, TypeScript/Vite ni Vitest.
- No se creó ni modificó repositorio remoto. La organización destino no está confirmada y las acciones GitHub disponibles no incluyen creación de repositorios.

**No se han implementado** Random Walker, Jacobi, Gauss-Seidel, SOR, SSOR, el endpoint de segmentación ni las pantallas definitivas. Estos resultados solo certifican la base estructural y las pruebas descritas.

## Próximo paso operativo

Seguir `docs/CONFIGURAR_GITHUB.md` para elegir la organización correcta, crear el repositorio, preparar los tres artefactos pendientes y completar un primer PR con CI manual. La aprobación final requiere ejecutar `bash scripts/ci-local.sh todo` y GitHub Actions real con `pruebas=todo`.
