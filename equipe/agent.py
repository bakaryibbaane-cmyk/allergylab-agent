"""L'agent de l'équipe. Le kit n'en appelle qu'une fonction : repondre(question).

C'est un CodeAgent de smolagents : à chaque étape, le modèle écrit du code
Python, et ce code s'exécute sur ta machine. Avant de modifier ce fichier,
lis la rubrique « Ce qu'un agent ouvert peut faire » du README.
"""

from pathlib import Path

from smolagents import CodeAgent

from kit import modele, reponse
from equipe.outils.compter_patients import compter_patients
from equipe.outils.agregat_dosages import agregat_dosages
from equipe.outils.classer_allergenes import classer_allergenes
from equipe.outils.compter_par_code import compter_par_code
from equipe.outils.compter_selon_condition import compter_selon_condition
from equipe.outils.croiser_colonnes import croiser_colonnes
from equipe.outils.decoder import decoder
from equipe.outils.moyenne import moyenne_colonne
from equipe.outils.patients_selon_dosages import patients_selon_dosages
from equipe.outils.proportion import proportion_positifs
from equipe.outils.proportion_avec_filtre import proportion_avec_filtre
from equipe.outils.puces_qui_mesurent import puces_qui_mesurent
from equipe.outils.qualite_donnees import qualite_donnees
from equipe.outils.repartition import repartition_categories

CONSIGNE = (Path(__file__).parent / "consigne.md").read_text(encoding="utf-8")


def repondre(question):
    agent = CodeAgent(
        model=modele.ModeleKit(),  # le modèle de kit/reglages.toml
        tools=[proportion_positifs, moyenne_colonne, repartition_categories, compter_patients, puces_qui_mesurent, qualite_donnees, decoder, compter_selon_condition, compter_par_code, classer_allergenes, agregat_dosages, proportion_avec_filtre, croiser_colonnes, patients_selon_dosages],  # les outils de equipe/outils/, testés hors ligne
        instructions=reponse.consigne(CONSIGNE),  # ta consigne, puis le format de réponse du kit
        max_steps=modele.REGLAGES["agent"]["etapes_max"],
        max_print_outputs_length=modele.REGLAGES["agent"]["sortie_max"],
        step_callbacks=[modele.noter_etape],  # recopie chaque étape dans la trace
    )
    return agent.run(question)
