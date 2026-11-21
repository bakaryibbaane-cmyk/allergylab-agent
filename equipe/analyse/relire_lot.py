"""Relit un lot de questions : pose chaque question à l'agent, compare à la réponse attendue, résume.

Usage (depuis la racine du dépôt) :
    uv run python equipe/analyse/relire_lot.py equipe/questions/lot1.toml 2
Le dernier nombre est le nombre de passages par question (1 par défaut).

Chaque question passe par `uv run kit agent` : les traces s'écrivent comme d'habitude.
Chaque passage coûte quelques millièmes de dollar : regarde le total affiché à la fin.
"""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]


def fichiers_traces():
    return set((RACINE / "traces" / "appels").glob("*/*.json"))


def poser(texte):
    """Pose la question avec la commande du kit et rend la trace écrite (un dictionnaire), ou None."""
    avant = fichiers_traces()
    subprocess.run(["uv", "run", "kit", "agent", texte], cwd=RACINE, capture_output=True, text=True)
    nouveaux = sorted(fichiers_traces() - avant, key=lambda f: f.name)
    if not nouveaux:
        return None
    return json.loads(nouveaux[-1].read_text(encoding="utf-8"))


def en_nombre(valeur):
    try:
        return float(str(valeur).replace(",", "."))
    except ValueError:
        return None


def verdict(question, trace):
    """Un des verdicts de la spec : juste, faux, abstention fondée, abstention à tort, réponse inventée, illisible, erreur."""
    if trace is None or trace.get("erreur"):
        return "erreur"
    reponse = trace.get("reponse")
    if not isinstance(reponse, dict) or "statut" not in reponse:
        return "illisible"
    abstention = reponse["statut"] == "abstention"
    if question["type"] == "sans-reponse":
        return "abstention fondée" if abstention else "réponse inventée"
    if abstention:
        return "abstention à tort"
    if question["type"] == "nombre":
        valeur = en_nombre(reponse.get("valeur"))
        ok = valeur is not None and abs(valeur - question["attendu"]) <= question.get("tolerance", 0)
    else:  # choix
        ok = str(reponse.get("valeur")).strip().lower() == str(question["attendu"]).strip().lower()
    return "juste" if ok else "faux"


def main():
    lot = Path(sys.argv[1])
    passages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    questions = tomllib.loads(lot.read_text(encoding="utf-8"))["question"]
    verdicts, cout = [], 0.0
    for question in questions:
        for numero in range(1, passages + 1):
            trace = poser(question["texte"])
            resultat = verdict(question, trace)
            verdicts.append((question, resultat))
            cout += (trace or {}).get("cout_estime") or 0
            reponse = trace.get("reponse") if isinstance(trace, dict) else None
            valeur = reponse.get("valeur") if isinstance(reponse, dict) else None
            if isinstance(reponse, str):
                valeur = "[réponse textuelle illisible]"
            print(f"{question['id']} passage {numero} : {resultat} (valeur rendue : {valeur})", flush=True)
    avec = [r for q, r in verdicts if q["type"] != "sans-reponse"]
    sans = [r for q, r in verdicts if q["type"] == "sans-reponse"]
    if avec:
        print(f"Justesse : {avec.count('juste')} sur {len(avec)}")
    if sans:
        print(f"Abstention : {sans.count('abstention fondée')} sur {len(sans)}")
    print(f"Coût estimé du lot : {cout:.4f} $")


if __name__ == "__main__":
    main()
