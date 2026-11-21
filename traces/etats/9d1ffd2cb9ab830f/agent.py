"""L'agent de l'équipe. Le kit n'en appelle qu'une fonction : repondre(question).

C'est un CodeAgent de smolagents : à chaque étape, le modèle écrit du code
Python, et ce code s'exécute sur ta machine. Avant de modifier ce fichier,
lis la rubrique « Ce qu'un agent ouvert peut faire » du README.
"""

from pathlib import Path

from smolagents import CodeAgent

from kit import modele, reponse
from equipe.outils.compter_patients import compter_patients
from equipe.outils.decoder import decoder
from equipe.outils.moyenne import moyenne_colonne
from equipe.outils.proportion import proportion_positifs
from equipe.outils.puces_qui_mesurent import puces_qui_mesurent
from equipe.outils.qualite_donnees import qualite_donnees
from equipe.outils.repartition import repartition_categories
from equipe.outils.variables_du_tableau import variables_du_tableau

CONSIGNE = (Path(__file__).parent / "consigne.md").read_text(encoding="utf-8")


def repondre(question):
    agent = CodeAgent(
        model=modele.ModeleKit(),  # le modèle de kit/reglages.toml
        tools=[proportion_positifs, moyenne_colonne, repartition_categories, compter_patients, puces_qui_mesurent, qualite_donnees, decoder, variables_du_tableau],  # les outils de equipe/outils/, testés hors ligne
        instructions=reponse.consigne(CONSIGNE),  # ta consigne, puis le format de réponse du kit
        max_steps=modele.REGLAGES["agent"]["etapes_max"],
        max_print_outputs_length=modele.REGLAGES["agent"]["sortie_max"],
        step_callbacks=[modele.noter_etape],  # recopie chaque étape dans la trace
    )
    return agent.run(question)
