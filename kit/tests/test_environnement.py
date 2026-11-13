"""Environnement : ce qui change d'une machine à l'autre, et les règles du dépôt."""

import ast
import os
import re
import shutil
import subprocess
import tomllib

from kit.donnees import RACINE

from conftest import copier_kit, lancer_kit

# Les deux scripts d'avant la semaine sont rangés dans kit/ tels quels.
SCRIPTS_FOURNIS = {"tester-la-stack.py", "verifier-ma-machine.py"}


def test_chemin_avec_espaces_et_accents(tmp_path):
    dossier = copier_kit(tmp_path / "Dossier de l'élève" / "kit à tester")
    code, sortie = lancer_kit(dossier, "controle", "--hors-ligne")
    assert code == 0, sortie
    assert sortie.strip().splitlines()[-1] == "RÉUSSITE"


def test_dossier_sans_git(tmp_path):
    dossier = copier_kit(tmp_path / "archive")
    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(tmp_path)  # git ne cherche pas de dépôt plus haut
    assert not (dossier / ".git").exists()
    if shutil.which("git"):
        hors_depot = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=dossier, env=env, capture_output=True)
        assert hors_depot.returncode != 0
    for commande in (["installer"], ["controle", "--hors-ligne"]):
        code, sortie = lancer_kit(dossier, *commande, env=env)
        assert code == 0, sortie


def test_affichage_des_accents(tmp_path):
    # Une console réglée sur un encodage sans accents, comme certaines sous Windows.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "ascii"
    env.pop("PYTHONUTF8", None)
    code, sortie = lancer_kit(RACINE, env=env)
    assert code == 0
    assert "vérifie l'installation" in sortie


def test_gitignore():
    motifs = (RACINE / ".gitignore").read_text(encoding="utf-8").splitlines()
    for motif in (".venv/", "__pycache__/", ".pytest_cache/", ".DS_Store", ".env"):
        assert motif in motifs


def test_dependances_figees():
    projet = tomllib.loads((RACINE / "pyproject.toml").read_text(encoding="utf-8"))
    assert sorted(projet["project"]["dependencies"]) == ["anthropic", "pandas", "smolagents[litellm]==1.26.0"]
    assert projet["dependency-groups"] == {"dev": ["pytest"]}
    verrou = tomllib.loads((RACINE / "uv.lock").read_text(encoding="utf-8"))
    versions = {paquet["name"]: paquet["version"] for paquet in verrou["package"]}
    assert versions["smolagents"] == "1.26.0"
    assert (RACINE / ".python-version").read_text(encoding="utf-8").strip() == "3.12"


def test_fichiers_texte_ouverts_en_utf8():
    for fichier in (RACINE / "kit").rglob("*.py"):
        if fichier.name in SCRIPTS_FOURNIS:
            continue
        for noeud in ast.walk(ast.parse(fichier.read_text(encoding="utf-8"))):
            if not isinstance(noeud, ast.Call):
                continue
            nom = getattr(noeud.func, "attr", getattr(noeud.func, "id", None))
            mode = [a.value for a in noeud.args[1:2] if isinstance(a, ast.Constant)]
            if nom in ("open", "read_text", "write_text") and not any("b" in m for m in mode):
                cles = {mot.arg for mot in noeud.keywords}
                assert "encoding" in cles, f"{fichier.name}, ligne {noeud.lineno} : encoding manquant"


def test_aucun_script_shell():
    for fichier in RACINE.rglob("*"):
        if set(fichier.relative_to(RACINE).parts) & {".git", ".venv"}:
            continue
        assert fichier.suffix not in (".sh", ".bat", ".cmd", ".ps1"), fichier


def test_aucune_adresse_electronique():
    adresse = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    for fichier in RACINE.rglob("*"):
        parties = set(fichier.relative_to(RACINE).parts)
        if parties & {".git", ".venv", "__pycache__", ".pytest_cache", "donnees"} or not fichier.is_file():
            continue
        texte = fichier.read_bytes().decode("utf-8", errors="ignore")
        assert not adresse.search(texte), fichier
