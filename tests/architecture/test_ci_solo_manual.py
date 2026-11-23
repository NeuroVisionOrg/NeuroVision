"""Protege la decisión explícita del equipo: el CI oficial no se dispara por PR/push."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WORKFLOW = RAIZ / ".github" / "workflows" / "ci.yml"


def test_ci_solo_usa_workflow_dispatch() -> None:
    contenido = WORKFLOW.read_text(encoding="utf-8")
    disparadores = contenido.split("\non:\n", maxsplit=1)[1].split(
        "\npermissions:\n", maxsplit=1
    )[0]
    declarados = re.findall(r"^  ([a-z_]+):\s*$", disparadores, flags=re.MULTILINE)
    assert declarados == ["workflow_dispatch"]


def test_ci_exige_pr_sha_y_una_revision_completa() -> None:
    contenido = WORKFLOW.read_text(encoding="utf-8")
    assert "NEUROVISION_CI_OPERATOR" in contenido
    assert "sha_revision:" in contenido
    assert "ref: refs/pull/${{ inputs.pr_number }}/merge" in contenido
    assert "resumen:" in contenido
    assert "needs: [validar, python, frontend, integracion, precommit]" in contenido
