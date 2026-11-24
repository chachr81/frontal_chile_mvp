"""Publica planning/plan.json en un repositorio de GitHub (etiquetas, hitos e issues).

Es idempotente: no duplica lo que ya existe (compara por nombre o título).
Requiere la CLI `gh` autenticada con permiso de escritura en el repositorio.

Uso:
  python scripts/publicar_plan_github.py usuario/repositorio --dry-run   # solo muestra
  python scripts/publicar_plan_github.py usuario/repositorio             # publica
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PLAN = Path(__file__).resolve().parents[1] / "planning" / "plan.json"


def gh(*args: str, entrada: str | None = None) -> str:
    """Ejecuta `gh` y devuelve su salida; aborta con el error si el comando falla."""
    r = subprocess.run(["gh", *args], input=entrada, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Error en 'gh {' '.join(args[:3])}...': {r.stderr.strip()}")
    return r.stdout


def existentes(repo: str, ruta: str, campo: str) -> set[str]:
    """Devuelve el conjunto de valores de `campo` de los recursos ya creados."""
    salida = gh("api", "--paginate", f"repos/{repo}/{ruta}?per_page=100&state=all")
    # --paginate concatena arreglos JSON; se separan para leerlos todos.
    texto, valores = salida.replace("][", ",").strip(), set()
    for item in json.loads(texto or "[]"):
        valores.add(item[campo])
    return valores


def publicar(repo: str, seco: bool) -> None:
    """Crea etiquetas, hitos e issues que falten en `repo`."""
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    accion = "[simulación] " if seco else ""

    ya_labels = set() if seco else existentes(repo, "labels", "name")
    for lb in plan["labels"]:
        if lb["name"] in ya_labels:
            continue
        print(f"{accion}etiqueta: {lb['name']}")
        if not seco:
            campos = [f"-f name={lb['name']}", f"-f color={lb['color']}"]
            if lb.get("description"):
                campos.append(f"-f description={lb['description'][:100]}")
            gh("api", f"repos/{repo}/labels", "-X", "POST", *sum(([*c.split(" ", 1)] for c in campos), []))

    numeros = {}  # título del hito -> número asignado por GitHub
    if not seco:
        for m in json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100") or "[]"):
            numeros[m["title"]] = m["number"]
    for ms in plan["milestones"]:
        if ms["title"] in numeros:
            continue
        print(f"{accion}hito: {ms['title']}")
        if not seco:
            r = gh("api", f"repos/{repo}/milestones", "-X", "POST",
                   "-f", f"title={ms['title']}", "-f", f"description={ms['description']}")
            numeros[ms["title"]] = json.loads(r)["number"]

    ya_issues = set() if seco else existentes(repo, "issues", "title")
    for it in plan["issues"]:
        if it["title"] in ya_issues:
            continue
        print(f"{accion}issue: {it['title']}  [{it['milestone']}]")
        if not seco:
            cuerpo = json.dumps({"title": it["title"], "body": it["body"], "labels": it["labels"],
                                 "milestone": numeros[it["milestone"]]})
            gh("api", f"repos/{repo}/issues", "-X", "POST", "--input", "-", entrada=cuerpo)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo", help="usuario/repositorio")
    p.add_argument("--dry-run", action="store_true", help="solo muestra lo que haría")
    a = p.parse_args()
    publicar(a.repo, a.dry_run)
