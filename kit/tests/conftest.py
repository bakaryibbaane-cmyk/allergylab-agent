"""Outils communs aux tests : copier le kit ailleurs et l'y faire tourner.

Les tests ne touchent jamais à donnees/ : ce qu'ils altèrent, ils l'altèrent
dans une copie, sous un dossier temporaire.
"""

import os
import shutil
import subprocess
import sys

from kit.donnees import RACINE

# Lance la commande kit depuis le dossier courant, après avoir vérifié que
# c'est bien le kit de ce dossier qui est importé, et pas celui du dépôt.
LANCEUR = (
    "import pathlib, sys, kit; "
    "assert pathlib.Path(kit.__file__).resolve().parent.parent == pathlib.Path.cwd().resolve(); "
    "from kit.cli import main; sys.exit(main(sys.argv[1:]))"
)


def copier_kit(destination):
    """Copie dans destination ce qu'il faut pour faire tourner le kit, sans .git."""
    shutil.copytree(RACINE / "kit", destination / "kit", ignore=shutil.ignore_patterns("__pycache__", "tests"))
    shutil.copytree(RACINE / "donnees", destination / "donnees")
    shutil.copy2(RACINE / "equipe.toml", destination / "equipe.toml")
    return destination


def lancer_kit(dossier, *arguments, env=None):
    """Lance `kit <arguments>` dans dossier ; rend le code de sortie et la sortie décodée."""
    resultat = subprocess.run(
        [sys.executable, "-c", LANCEUR, *arguments],
        cwd=dossier,
        capture_output=True,
        env=env or os.environ.copy(),
    )
    return resultat.returncode, resultat.stdout.decode("utf-8") + resultat.stderr.decode("utf-8")
