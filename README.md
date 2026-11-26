# NeuroVision — segmentación asistida 2D y 3D con SOR

**Prototipo académico, no clínico.** Aplicación web educativa para segmentación asistida de regiones tumorales en resonancias magnéticas cerebrales de intensidad escalar. El objetivo es formular sistemas lineales dispersos mediante Random Walker binario y resolverlos con una única implementación propia de sobrerrelajación sucesiva (SOR).

**Estado:** infraestructura de desarrollo validada en los PR #1 y #2; diseño inicial actualizado al alcance 2D/3D. La integración de funcionalidades sigue pendiente. Los avances en ramas de tarea no son funcionalidades aprobadas de `develop`. Consultar el [anexo de reconciliación H1](docs/Anexo_reconciliacion_H1.md).

## Alcance

- 2D: cargar un corte JPEG/PNG gris, elegir ROI y semillas de primer plano/fondo, ejecutar SOR, obtener máscara y contorno.
- 3D: cargar un volumen escalar NIfTI (formato de diseño inicial), navegar cortes axiales, definir ROI volumétrica y semillas, ejecutar el mismo SOR, reconstruir máscara y superficie 3D conservando la geometría.
- Consultar convergencia, iteraciones/barridos, tiempo, residuo e historial; comparar configuraciones de SOR. Evaluar Dice/IoU solo con referencia compatible y exportar resultados básicos.
- No implementar métodos adicionales, segmentación multicanal, clasificación, diagnóstico, IA, DICOM ni almacenamiento médico persistente en el MVP. Un JPG aislado no representa profundidad anatómica real.

Los parámetros definitivos, límites de ROI y datos de investigación requieren validación. Las dependencias 3D se han probado localmente con datos sintéticos; consultar sus limitaciones en el [anexo de compatibilidad 3D](docs/Anexo_compatibilidad_3D.md). El profesor solicitó SOR como único método según la aclaración comunicada por el líder; el alcance 2D/3D y las decisiones de diseño se documentan en el [registro](docs/decisiones/registro.md).

## Responsabilidades y cinco capas

| Carpeta | Responsable | Responsabilidad |
|---|---|---|
| `capa_1_interfaz/` | Johan | Visores, ROI, semillas, configuración, comparación y presentación de resultados 2D/3D |
| `capa_2_control/` | Jherson | API, validaciones, coordinación de casos de uso e integración |
| `capa_3_traduccion/` | Yenderson | Lectura, normalización, geometría, grafo, sistema CSR y reconstrucción de máscaras |
| `capa_4_metodos/` | Jennifer | SOR único, convergencia, residuos, iteraciones, tiempo y pruebas numéricas |
| `capa_5_servicios/` | Yenderson | Mallas, métricas, gráficas y exportaciones |

Control coordina las capas especializadas por sus API públicas. Traducción, Métodos y Servicios no se importan entre sí. Interfaz no ejecuta SOR. `contratos/` es un módulo auxiliar compartido, no una sexta capa. Pruebas, revisión y documentación son responsabilidades compartidas.

## Entorno reproducible

- Python **3.13**, Node.js **22**, npm y Git Bash (o Bash en Linux/macOS).
- Backend: FastAPI, Pydantic, Uvicorn, python-multipart, NumPy, SciPy CSR, Pillow, Matplotlib.
- Frontend: HTML/CSS/TypeScript vanilla, Konva y Vite.
- NiBabel 5.5.0 (Traducción), scikit-image 0.26.0 (Servicios) y Three.js 0.187.0 (Interfaz), con `@types/three` 0.187.0 en desarrollo: incorporadas en la rama H1; [evidencia local y pendientes](docs/Anexo_compatibilidad_3D.md).

Los lockfiles de Python y npm ya existen en la base validada. No regenerarlos para una instalación normal. Desde la raíz, en Windows/Git Bash:

```bash
py -3.13 -m venv .venv  # solo si no existe el entorno
source .venv/Scripts/activate
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
python -m pip check
(cd capa_1_interfaz && npm ci)
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

En Linux/macOS, usar `python3.13 -m venv .venv` y `source .venv/bin/activate`. Verificar que `python --version` y `node --version` corresponden a las versiones requeridas. Las modificaciones de dependencias se revisan con sus lockfiles en un PR.

## Ejecutar la base actual

```bash
uvicorn main:app --reload
```

La ruta implementada de disponibilidad es `GET /api/v1/health`, que devuelve `{"service":"neurovision","status":"ok"}`. No demuestra segmentación funcional. Las operaciones de segmentación y demás DTO se especifican en [contratos.md](docs/contratos.md).

En otra terminal, desde la raíz:

```bash
cd capa_1_interfaz
npm run dev
```

## Calidad e integración

```bash
bash scripts/ci-local.sh todo
```

Conservar Ruff, mypy estricto, scipy-stubs, Import Linter, pytest, HTTPX, ESLint, Prettier, Vitest, pre-commit y detect-secrets. No deshabilitar controles ni regenerar la línea base de secretos indiscriminadamente para conseguir un CI verde.

El repositorio oficial es [NeuroVisionOrg/NeuroVision](https://github.com/NeuroVisionOrg/NeuroVision). `develop` es la rama predeterminada de trabajo; `main` se reserva para versiones estables. Ambas están protegidas. Usar ramas por tarea, Conventional Commits, PR hacia `develop` y merge commits. La promoción a `main` se hace mediante PR separado. No realizar push directo ni reescribir el historial de otras ramas.

El CI oficial se inicia exclusivamente mediante `workflow_dispatch` desde `develop`, por el operador autorizado (Jherson). Introducir `pr_number`, SHA completo de cabeza en `sha_revision` y `pruebas=todo`. Exigir éxito de la suite completa y revisión documentada, y verificar cabeza y base antes de integrar. Si cambia cualquiera de los SHA, repetir revisión y CI. El CI manual no constituye por sí mismo un required status check automático. Consultar [CONTRIBUTING.md](CONTRIBUTING.md) y [ADR-006](docs/decisiones/ADR-006.md).

## Documentación y datos

El [índice técnico](docs/README.md) enlaza los siete documentos aprobados por el líder y sus anexos. Los [pendientes](docs/pendientes.md) distinguen verificaciones de infraestructura realizadas de funcionalidades todavía por construir. El registro inicial y la configuración fundacional se conservan como antecedentes.

No publicar datasets médicos, imágenes o máscaras de investigación, datos identificables, archivos originales del docente, credenciales ni secretos. Usar datos sintéticos versionables; comprobar licencias y geometría antes de usar datos reales localmente. Los solucionadores externos solo pueden utilizarse como referencia en pruebas, nunca sustituir SOR en el producto.
