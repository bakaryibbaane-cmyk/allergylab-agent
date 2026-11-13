"""La commande `uv run kit` : une seule entrée, un verbe par action.

Codes de sortie : 0 pour une réussite, 1 pour un échec. Une erreur
inattendue s'affiche en une phrase ; --detail montre la trace Python.
"""

import platform
import sys
import traceback
from importlib.metadata import version

from kit import controle

AIDE = """Kit AllergyLab. Usage : uv run kit <commande>

  installer                 installe le kit et vérifie les données
  controle                  vérifie l'installation point par point
  controle --hors-ligne     la même chose, sans appeler le modèle

Ajoute --detail à une commande pour voir le détail d'une erreur inattendue."""


def regler_console():
    """Écrit en UTF-8 sur les trois systèmes, pour que les accents passent sous Windows."""
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8", errors="replace")


def installer(options):
    """Python et les dépendances sont déjà installés par `uv run` ; on le confirme."""
    print("Installation du kit AllergyLab")
    print(f"  OK     Python {platform.python_version()}")
    paquets = ", ".join(f"{nom} {version(nom)}" for nom in ("pandas", "smolagents", "anthropic"))
    print(f"  OK     dépendances : {paquets}")
    lignes = controle.verifier_donnees(controle.RACINE, controle.lire_attendu(controle.RACINE))
    for ligne in lignes:
        controle.afficher(*ligne)
    if all(bon for bon, _, _ in lignes):
        print("Installation terminée. Étape suivante : uv run kit controle")
        return 0
    print("Installation incomplète : corrige la ligne en échec, puis relance uv run kit installer.")
    return 1


def verifier(options):
    return controle.controler(hors_ligne="--hors-ligne" in options)


# Chaque verbe : la fonction qui le traite, et les options qu'il accepte.
VERBES = {
    "installer": (installer, []),
    "controle": (verifier, ["--hors-ligne"]),
}


def main(argv=None):
    regler_console()
    arguments = sys.argv[1:] if argv is None else list(argv)
    detail = "--detail" in arguments
    arguments = [a for a in arguments if a != "--detail"]
    if not arguments or arguments[0] in ("-h", "--help", "aide"):
        print(AIDE)
        return 0
    verbe, options = arguments[0], arguments[1:]
    if verbe not in VERBES:
        print(f"Commande inconnue : {verbe}. Voici les commandes du kit.\n")
        print(AIDE)
        return 1
    fonction, permises = VERBES[verbe]
    inconnues = [o for o in options if o not in permises]
    if inconnues:
        print(f"Option inconnue pour {verbe} : {' '.join(inconnues)}. Lance uv run kit pour voir les options.")
        return 1
    try:
        return fonction(options)
    except KeyboardInterrupt:
        print("\nInterrompu.")
        return 1
    except Exception as erreur:
        if detail:
            traceback.print_exc()
        else:
            print(f"Erreur inattendue : {erreur}")
            print("Relance la même commande avec --detail, et montre le résultat à l'animateur.")
        return 1
