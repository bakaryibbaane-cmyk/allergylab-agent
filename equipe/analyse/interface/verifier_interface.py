"""Vérification hors ligne de l'interface : chaque page se charge sans exception.

Lancement, depuis la racine du dépôt (streamlit et plotly hors verrouillage) :
    uv run --with streamlit --with plotly --with scikit-learn python equipe/analyse/interface/verifier_interface.py
N'appelle ni le modèle ni le réseau (sauf les polices, absentes en test).
"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent / "app.py")
PAGES_SANS_ACTION = ["Accueil", "Assistant IA", "Jeu de données", "Exploration", "Questionnaire d’analyse",
                     "Qualité des données", "Statistiques", "Comparaison des puces", "Corrélations",
                     "Machine Learning", "Historique"]

echecs = 0
for page in PAGES_SANS_ACTION:
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["navigation"] = page
    at.run()
    erreurs = [e.value for e in at.exception] + [e.value for e in at.error]
    etat = "OK " if not erreurs else "ÉCHEC"
    echecs += bool(erreurs)
    print(f"{etat}  {page}" + (f"  -> {erreurs[0][:150]}" if erreurs else ""))

# --- Interactions : boutons d'accès rapide et analyses guidées -------------------------
def exception_ou_erreur(at):
    return [e.value for e in at.exception] + [e.value for e in at.error]

at = AppTest.from_file(APP, default_timeout=120).run()
at.button(key="acces_Qualité des données").click().run()
ok = at.session_state["navigation"] == "Qualité des données" and not exception_ou_erreur(at)
print(("OK " if ok else "ÉCHEC") + "  bouton d'accès rapide -> page Qualité des données")
echecs += not ok

for objectif in ["Statistiques descriptives", "Distribution d’une variable", "Comparer les puces", "Qualité des données"]:
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["navigation"] = "Questionnaire d’analyse"
    at.run()
    at.selectbox[0].set_value(objectif)
    at.button[0].click().run()
    erreurs = exception_ou_erreur(at)
    print(("OK " if not erreurs else "ÉCHEC") + f"  analyse guidée : {objectif}" + (f" -> {erreurs[0][:150]}" if erreurs else ""))
    echecs += bool(erreurs)
sys.exit(1 if echecs else 0)
