# NeuroVision — base de arquitectura y desarrollo (v0.2)

**Prototipo académico, no clínico.** Aplicación educativa para segmentación interactiva de imágenes cerebrales 2D y comparación de Jacobi, Gauss-Seidel, SOR y SSOR sobre el mismo sistema lineal.

**Estado de este paquete:** esqueleto inicial y contratos; **no es una aplicación de segmentación terminada**. El visor, la construcción Random Walker, los cuatro solucionadores, las métricas y las exportaciones están pendientes.

## Responsabilidades y cinco capas

| Carpeta | Dueño | Responsabilidad |
| --- | --- | --- |
| `capa_1_interfaz/` | Johan | TypeScript, Vite, Konva, visor, ROI, semillas y comparación |
| `capa_2_control/` | Jherson | FastAPI, validaciones, coordinación y API |
| `capa_3_traduccion/` | Yenderson | Imágenes, laplaciano, Ax=b, reconstrucción |
| `capa_4_metodos/` | Jennifer | Jacobi, Gauss-Seidel, SOR y SSOR |
| `capa_5_servicios/` | Yenderson | Métricas, reportes, gráficas y exportaciones |

`contratos/` es un módulo auxiliar compartido, **no una sexta capa**. `tests/`, `docs/`, `.github/` y `scripts/` tampoco son capas funcionales.

## Requisitos del entorno

- Python **3.13** (`.python-version`).
- Node.js **22** (`.nvmrc`).
- Git, Bash y acceso a los registros de paquetes durante la instalación.

## Preparación del backend

```bash
python -m venv .venv
source .venv/bin/activate
# Con acceso a PyPI, generar el lockfile en un entorno controlado (uv es una herramienta de preparacion)
uv pip compile pyproject.toml --extra dev --python-version 3.13 -o requirements.lock
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
python -m pytest -q
uvicorn main:app --reload
```

La API implementada por ahora es solo `GET /api/v1/health`. Responde `{"service":"neurovision","status":"ok"}`. No existe aún `POST /api/v1/segmentar`.

## Preparación del frontend

```bash
cd capa_1_interfaz
npm install
npm run dev
```

**IMPORTANTE:** el primer `npm install` con acceso al registro crea `package-lock.json`; **debe revisarse y registrarse en Git antes de usar `npm ci` o el CI oficial**. Este paquete no trae un lockfile inventado porque el registro npm no estuvo disponible en el entorno de generación.

En instalaciones posteriores, usa `npm ci`. El frontend contiene únicamente una pantalla provisional de estado y una utilidad probada de conversión de coordenadas; Konva está declarado como dependencia para el desarrollo futuro.

## Pruebas y calidad

```bash
python -m pytest -q
bash scripts/ci-local.sh preflight
bash scripts/ci-local.sh python
bash scripts/ci-local.sh frontend
bash scripts/ci-local.sh integracion
bash scripts/ci-local.sh todo
```

`ci-local.sh` exige tener instaladas las dependencias de desarrollo. `todo` no omite categorías silenciosamente: falla si faltan herramientas o archivos de instalación.

Antes del primer commit, con las dependencias instaladas:

```bash
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

La configuración inicial de Python permite intervalos de versiones. Antes del CI oficial debe generarse y aprobarse `requirements.lock`; no hay un archivo de resolución inventado. La generación requiere acceso al registro y su resultado se revisa en un PR. La configuración debe probarse realmente tras obtener los paquetes.

## Publicación en GitHub

La preparación de la organización, las ramas, los permisos y el primer PR se explica en [`docs/CONFIGURAR_GITHUB.md`](docs/CONFIGURAR_GITHUB.md). No se asume que la organización o el repositorio ya existan.

## CI oficial manual

El archivo `.github/workflows/ci.yml` tiene **únicamente `workflow_dispatch`**; no se ejecuta por `push` ni por `pull_request`.

Para activarlo después de crear el repositorio en GitHub:

1. Publica el workflow en la rama `develop`, de la que se ejecutará su definición oficial.
2. Configura la variable de repositorio `NEUROVISION_CI_OPERATOR` con el usuario autorizado por el equipo.
3. Genera y confirma el `package-lock.json` y un bloqueo reproducible de dependencias Python.
4. Abre un PR; el responsable del CI introduce su número y SHA completo de 40 caracteres.
5. Ejecuta `pruebas=todo` antes de autorizar la integración.
6. Si cambia el HEAD del PR o la base de integración, vuelve a comprobar el candidato y repite el CI.

El workflow debe existir también en la **rama predeterminada** del repositorio para que GitHub permita iniciarlo manualmente desde la interfaz. Se seleccionará `develop` para la ejecución oficial.

El workflow verifica que el candidato temporal de integración tenga los dos SHA examinados. **Un workflow manual no equivale automáticamente a un required status check del PR**: configurar protección de ramas y un mecanismo de autorización efectivo es una tarea pendiente que debe probarse.

## Documentación

- `docs/contratos.md`: convenios y contratos compartidos.
- `docs/modelo_matematico.md`: formulación candidata de Random Walker.
- `docs/plan_pruebas.md`: criterios de aceptación y pruebas.
- `docs/estandares_codigo.md`: calidad, tipado, imports y revisiones.
- `docs/decisiones/ADR-005.md` y `ADR-006.md`: registro de decisiones.
- `docs/pendientes.md`: elementos que no deben anunciarse como terminados.
- `docs/CONFIGURAR_GITHUB.md`: procedimiento para crear el repositorio oficial y habilitar el CI manual.
- `docs/VERIFICACION_INICIAL.md`: evidencia local de las 24 pruebas y bloqueos pendientes.

## Restricciones

No incorporar archivos de resonancia identificables, credenciales ni datos sensibles al repositorio. Las pruebas iniciales utilizan datos sintéticos. Los cuatro métodos numéricos deben implementarse por el equipo; un solucionador externo solo puede usarse como referencia de prueba.
