# Creación del repositorio oficial y primer CI de NeuroVision

**Estado:** procedimiento acordado, **no ejecutado en GitHub**. La organización propietaria del repositorio debe ser confirmada por el equipo; no utilizar la organización de Posgrados sin autorización expresa.

## 1. Crear el repositorio público en la organización correcta

1. En GitHub, entrar con la cuenta responsable y seleccionar **New repository**: <https://github.com/new>.
2. Seleccionar la organización que el equipo haya decidido usar (o crear previamente una organización propia para NeuroVision).
3. Nombre sugerido: `neurovision` (confirmar disponibilidad); descripción: `NeuroVision — segmentación interactiva 2D y comparación de métodos numéricos`.
4. Seleccionar **Public**, comprobar que no contiene datos médicos personales, archivos sensibles ni secretos.
5. Crear el repositorio **vacío**, sin README ni `.gitignore` automáticos, porque ambos están en el paquete.
6. Confirmar permisos administrativos del líder y acceso de los otros tres integrantes. No inventar identificadores de usuario GitHub.

> No publicar el ZIP de NeuroVision en `POSGRADOS-UP/ingsoft2gb01-posgrados`: es otro proyecto.

## 2. Preparar la primera publicación local

Descomprimir el ZIP y entrar a la carpeta `NeuroVision/`. Después, con Git configurado con la identidad real del autor del commit:

```bash
# Sustituir <ORGANIZACION> por el propietario real del repositorio.
git init -b main
git add .
git commit -m "chore: initialize neurovision project skeleton"
git remote add origin https://github.com/<ORGANIZACION>/neurovision.git
git push -u origin main

git switch -c develop
git push -u origin develop
```

El commit inicial corresponde a quien lo realice efectivamente. Los demás integrantes usarán sus propios commits en ramas de trabajo. No activar los hooks que prohíben commits en `main` hasta después del commit fundacional; en adelante no realizar commits directos a `main` o `develop`.

**Importante:** el esqueleto todavía tiene los lockfiles y la línea base de secretos pendientes. Pueden existir ramas iniciales con esa condición documentada, pero ningún PR se declarará validado hasta completar los requisitos.

## 3. Configurar seguridad y forma de colaboración

En **Settings → General → Pull Requests**:

- Permitir **merge commits** para conservar los commits individuales.
- Deshabilitar *squash merge* y *rebase merge* si la política del equipo así lo mantiene.

En **Settings → Rules → Rulesets** (o la opción equivalente de protección de ramas disponible):

- Aplicar reglas a `main` y `develop`.
- Exigir pull request y al menos una aprobación de alguien distinto del autor.
- Bloquear cambios directos y *force push*; comprobar los posibles permisos de bypass.
- No activar `Require linear history`, ya que contradice la política de *merge commits*.
- **No configurar un required status check inexistente**: el workflow oficial es manual y su ejecución sobre `develop` no demuestra por sí sola un estado requerido en el commit del PR.
- Comprobar con una rama de prueba que la protección realmente impide integraciones no autorizadas.

En **Settings → Secrets and variables → Actions → Variables** crear:

- `NEUROVISION_CI_OPERATOR` = nombre de usuario GitHub del responsable autorizado para iniciar y repetir el CI oficial.

Revisar `.github/CODEOWNERS` cuando se disponga de los usuarios GitHub reales de Johan, Yenderson y Jennifer. Los responsables técnicos de las capas no cambian.

## 4. Preparar dependencias reproducibles y hooks

Con acceso a los registros de paquetes, desde la raíz del proyecto:

```bash
# Bloqueo Python real y revisable. uv es herramienta de preparación;
# los agentes de CI instalan con pip a partir del lockfile.
uv pip compile pyproject.toml --extra dev --python-version 3.13 -o requirements.lock
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps

# Bloqueo frontend real creado por npm.
cd capa_1_interfaz
npm install
cd ..

# Línea base de secretos real, auditar y conservar únicamente hallazgos justificables.
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline

bash scripts/ci-local.sh preflight
bash scripts/ci-local.sh todo
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

Confirmar `requirements.lock`, `capa_1_interfaz/package-lock.json` y `.secrets.baseline` en una rama de tarea, revisarlos en PR y no introducir resultados o archivos de bloqueo inventados.

**Regla:** todo el CI oficial se ejecutará con `workflow_dispatch`, nunca por `push` o `pull_request`.

## 5. Ejecutar el primer CI manual

1. Confirmar que `.github/workflows/ci.yml` existe tanto en la rama predeterminada `main` como en `develop`.
2. Abrir un PR de una rama de tarea hacia `develop`, con pruebas pertinentes y revisión documentada.
3. Comprobar en GitHub el SHA de **40 caracteres** del último commit de la rama del PR.
4. Ir a **Actions → NeuroVision CI → Run workflow**. Seleccionar **develop**.
5. Indicar `pr_number`, `sha_revision` y `pruebas=todo`.
6. Verificar que los trabajos `validar`, `python`, `frontend`, `integracion`, `precommit` y `resumen` terminen en `success`.
7. Revisar el candidato de integración y autorizar la fusión solo si el PR y el SHA base no han cambiado.
8. Si cambia el HEAD o `develop`, repetir la ejecución completa para el nuevo candidato.

La aprobación del CI manual y las aprobaciones de código se registran en el PR. La ejecución parcial nunca autoriza una integración.

## 6. Lista de verificación inicial

- [ ] Organización y nombre del repositorio confirmados.
- [ ] Repositorio público creado con permisos correctos.
- [ ] Ramas `main` y `develop` publicadas.
- [ ] Protección de ramas probada, con revisión de PR.
- [ ] Merge commits habilitados; no se borran los commits individuales.
- [ ] Operador de CI configurado en las variables de GitHub.
- [ ] Bloqueos Python/npm y línea base de secretos generados y revisados.
- [ ] Herramientas ejecutadas satisfactoriamente en el entorno definitivo.
- [ ] Primer `workflow_dispatch` completo exitoso sobre PR real.

**No marcar un punto como completado sin evidencia.**
