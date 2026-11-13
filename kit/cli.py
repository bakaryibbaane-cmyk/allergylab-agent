"""La commande `uv run kit` : une seule entrée, un verbe par action.

Codes de sortie : 0 pour une réussite, 1 pour un échec. Une erreur
inattendue s'affiche en une phrase ; --detail montre la trace Python.
"""

import platform
import sys
import traceback
from importlib.metadata import version

from kit import cle, controle

AIDE = """Kit AllergyLab. Usage : uv run kit <commande>

  installer                 installe le kit, vérifie les données, demande la clé
  cle                       enregistre ou remplace la clé d'API
  controle                  vérifie l'installation point par point
  controle --hors-ligne     la même chose, sans appeler le modèle
  agent "question"          pose une question à l'agent de l'équipe

Ajoute --detail à une commande pour voir le détail d'une erreur inattendue."""


def regler_console():
    """Écrit en UTF-8 sur les trois systèmes, pour que les accents passent sous Windows."""
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8", errors="replace")


def installer(options):
    """Python et les dépendances sont déjà installés par `uv run` ; on le confirme, puis la clé."""
    print("Installation du kit AllergyLab")
    print(f"  OK     Python {platform.python_version()}")
    paquets = ", ".join(f"{nom} {version(nom)}" for nom in ("pandas", "smolagents", "anthropic"))
    print(f"  OK     dépendances : {paquets}")
    lignes = controle.verifier_donnees(controle.RACINE, controle.lire_attendu(controle.RACINE))
    for ligne in lignes:
        controle.afficher(*ligne)
    cle_acceptee = cle.installer()  # la demande si elle manque, et seulement dans un terminal
    if all(bon for bon, _, _ in lignes) and cle_acceptee:
        print("Installation terminée. Étape suivante : uv run kit controle")
        return 0
    print("Installation incomplète : corrige la ligne en échec, puis relance uv run kit installer.")
    return 1


def verifier(options):
    return controle.controler(hors_ligne="--hors-ligne" in options)


def enregistrer_cle(options):
    return cle.commande()


def agent(mots):
    if not mots:
        print('Il manque la question, entre guillemets : uv run kit agent "Combien de lignes compte le tableau ?"')
        return 1
    from kit import question  # importé ici seulement : smolagents et litellm sont longs à charger

    return question.poser(" ".join(mots))


# Chaque verbe : la fonction qui le traite, et les options qu'il accepte
# (None : le verbe prend un texte libre, la question).
VERBES = {
    "installer": (installer, []),
    "cle": (enregistrer_cle, []),
    "controle": (verifier, ["--hors-ligne"]),
    "agent": (agent, None),
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
    inconnues = [o for o in options if permises is not None and o not in permises]
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
