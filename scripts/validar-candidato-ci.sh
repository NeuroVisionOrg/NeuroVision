#!/usr/bin/env bash
# Confirmar que checkout es el merge temporal del PR y los SHA revisados.
set -euo pipefail

[[ "${EXPECTED_BASE_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || {
  echo 'SHA de base ausente o inválido' >&2
  exit 1
}
[[ "${EXPECTED_HEAD_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || {
  echo 'SHA de PR ausente o inválido' >&2
  exit 1
}

read -r commit base head extra <<< "$(git rev-list --parents -n 1 HEAD)"
if [[ -z "${commit:-}" || -z "${base:-}" || -z "${head:-}" || -n "${extra:-}" ]]; then
  echo 'HEAD debe ser un merge de dos padres' >&2
  exit 1
fi
if [[ "$base" != "$EXPECTED_BASE_SHA" || "$head" != "$EXPECTED_HEAD_SHA" ]]; then
  echo 'El candidato no coincide con los SHA revisados' >&2
  exit 1
fi
printf 'Candidato de integración validado: %s\n' "$commit"
