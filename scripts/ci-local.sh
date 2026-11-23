#!/usr/bin/env bash
# Punto único de calidad para desarrollo local y GitHub Actions.
# El CI oficial se ejecuta SOLO mediante workflow_dispatch.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

# Verificacion offline: muestra los artefactos necesarios antes del primer CI.
run_preflight() {
  cd "$ROOT"
  local faltantes=0
  for archivo in requirements.lock capa_1_interfaz/package-lock.json .secrets.baseline; do
    if [[ -s "$archivo" ]]; then
      printf '[preflight] OK %s\n' "$archivo"
    else
      printf '[preflight] PENDIENTE %s\n' "$archivo" >&2
      faltantes=$((faltantes + 1))
    fi
  done
  if command -v python >/dev/null 2>&1 &&
     python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)'; then
    printf '[preflight] OK Python 3.13\n'
  else
    printf '[preflight] PENDIENTE Python 3.13\n' >&2
    faltantes=$((faltantes + 1))
  fi
  if command -v node >/dev/null 2>&1 &&
     [[ "$(node -p 'process.versions.node.split(".")[0]')" == "22" ]]; then
    printf '[preflight] OK Node.js 22\n'
  else
    printf '[preflight] PENDIENTE Node.js 22\n' >&2
    faltantes=$((faltantes + 1))
  fi
  if command -v npm >/dev/null 2>&1; then
    printf '[preflight] OK npm\n'
  else
    printf '[preflight] PENDIENTE npm\n' >&2
    faltantes=$((faltantes + 1))
  fi
  [[ "$faltantes" -eq 0 ]] || fail "$faltantes requisito(s) de preparacion pendientes; consulta docs/CONFIGURAR_GITHUB.md"
  printf '[preflight] Artefactos basicos presentes; aun deben ejecutarse los controles completos.\n'
}

run_python() {
  cd "$ROOT"
  [[ -s requirements.lock ]] || fail "Falta requirements.lock: genera un bloqueo real antes del CI"
  command -v python >/dev/null 2>&1 || fail "Falta Python"
  python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)' \
    || fail "NeuroVision requiere Python 3.13"
  for tool in ruff mypy lint-imports pytest; do
    command -v "$tool" >/dev/null 2>&1 || fail "Falta $tool: instala pip install -e '.[dev]'"
  done
  printf '[python] Ruff lint\n'
  ruff check .
  printf '[python] Ruff formato\n'
  ruff format --check .
  printf '[python] mypy\n'
  mypy
  printf '[python] Import Linter\n'
  lint-imports
  printf '[python] pytest unitarias y arquitectura\n'
  pytest -q tests/unit tests/architecture
}

run_integration() {
  cd "$ROOT"
  [[ -s requirements.lock ]] || fail "Falta requirements.lock para reproducir las pruebas de integracion"
  command -v pytest >/dev/null 2>&1 || fail "Falta pytest"
  printf '[integracion] pytest\n'
  pytest -q tests/integration
}

run_frontend() {
  cd "$ROOT/capa_1_interfaz"
  [[ -s package-lock.json ]] || fail "Falta package-lock.json: ejecuta npm install con acceso a npm y confirma el resultado"
  command -v node >/dev/null 2>&1 || fail "Falta Node.js"
  command -v npm >/dev/null 2>&1 || fail "Falta npm"
  major="$(node -p 'process.versions.node.split(".")[0]')"
  [[ "$major" == "22" ]] || fail "NeuroVision requiere Node.js 22"
  [[ -d node_modules ]] || fail "Faltan dependencias; ejecuta npm ci"
  printf '[frontend] ESLint\n'
  npm run lint
  printf '[frontend] Prettier\n'
  npm run format:check
  printf '[frontend] Vitest\n'
  npm test
  printf '[frontend] TypeScript y Vite\n'
  npm run build
}

run_precommit() {
  cd "$ROOT"
  [[ -s .secrets.baseline ]] || fail "Falta .secrets.baseline: genera y audita la linea base con detect-secrets"
  command -v pre-commit >/dev/null 2>&1 || fail "Falta pre-commit"
  printf '[pre-commit] validando archivos\n'
  SKIP=no-commit-to-branch pre-commit run --all-files --show-diff-on-failure
}

[[ "$#" -eq 1 ]] || fail "uso: bash scripts/ci-local.sh preflight|python|frontend|integracion|precommit|todo"
case "$1" in
  preflight) run_preflight ;;
  python) run_python ;;
  frontend) run_frontend ;;
  integracion) run_integration ;;
  precommit) run_precommit ;;
  todo)
    run_preflight
    run_python
    run_frontend
    run_integration
    run_precommit
    ;;
  *) fail "opción desconocida: $1" ;;
esac
printf 'Verificaciones solicitadas completadas.\n'
