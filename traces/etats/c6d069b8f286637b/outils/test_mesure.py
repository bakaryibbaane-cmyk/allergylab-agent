"""Tests de mesure.py, hors ligne, sur la table inventée de kit/exemple/.

La table inventée compte 4 patients par puce. Le seuil réel (30) n'y est
jamais atteint : pour tester « effectif suffisant », on baisse le seuil le
temps d'un test. Le fichier réel n'est jamais ouvert. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    """La table inventée à la place du fichier réel, pour tout le module mesure."""
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def test_colonne_inconnue(tableau):
    assert mesure.effectif_mesure("Colonne_Inventee") == 0
    assert mesure.verifier_perimetre("Colonne_Inventee").startswith("abstention")
    # Connue du dictionnaire, absente de la table inventée : pas de devinette non plus.
    assert mesure.effectif_mesure("Ory_c_2") == 0
    assert mesure.valeurs_speciales("Colonne_Inventee") == [0, 0]


def test_puce_inconnue(tableau):
    assert mesure.effectif_mesure("Act_d_1", "ISAC_V3") == 0
    assert "inconnue" in mesure.verifier_perimetre("Act_d_1", "ISAC_V3")


def test_colonne_non_mesuree_par_la_puce(tableau):
    # Aca_m n'est renseignée que pour ALEX.
    assert mesure.effectif_mesure("Aca_m", "ISAC_V1") == 0
    assert "n'est mesurée par aucune puce" in mesure.verifier_perimetre("Aca_m", "ISAC_V1")
    assert mesure.effectif_mesure("Aca_m", "ALEX") == 4


def test_effectif_sous_le_seuil(tableau):
    # 4 patients ALEX mesurés, seuil de 30.
    texte = mesure.verifier_perimetre("Act_d_1", "ALEX")
    assert texte.startswith("abstention")
    assert "4 patients" in texte and "minimum 30" in texte


def test_effectif_suffisant(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    assert mesure.verifier_perimetre("Act_d_1", "ALEX") == 4
    assert mesure.verifier_perimetre("Act_d_1") == 12


def test_taux_de_renseignement(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # Api_m_1 : ALEX et ISAC_V1, soit 8 patients sur 12 : assez renseignée.
    assert mesure.verifier_perimetre("Api_m_1") == 8
    # Aca_m : ALEX seule, 4 patients sur 12 : trop vide pour tout le fichier.
    texte = mesure.verifier_perimetre("Aca_m")
    assert texte.startswith("abstention") and "33%" in texte
    # Un vide n'est pas un zéro : seuls les patients mesurés comptent.
    assert mesure.effectif_mesure("Aca_m") == 4


def test_valeurs_speciales_signalees_sans_recodage(tableau):
    tableau.loc[0, "Act_d_1"] = -1  # patient ALEX
    tableau.loc[1, "Act_d_1"] = -1  # patient ISAC_V1
    tableau.loc[3, "Age_of_onsets"] = "9"  # colonne restée en texte, patient ALEX
    assert mesure.valeurs_speciales("Act_d_1") == [2, 0]
    assert mesure.valeurs_speciales("Act_d_1", "ALEX") == [1, 0]
    assert mesure.valeurs_speciales("Age_of_onsets") == [0, 1]
    # Signalées, pas exclues : l'effectif les compte encore.
    assert mesure.effectif_mesure("Act_d_1") == 12
    assert tableau.loc[0, "Act_d_1"] == -1


def test_9_exclu_dans_les_colonnes_non_renseigne(tableau, monkeypatch):
    # Rural_or_urban_area : 9 = non renseigné (dictionnaire officiel).
    for ligne in (0, 1, 2):
        tableau.loc[ligne, "Rural_or_urban_area"] = 9
    assert mesure.effectif_mesure("Rural_or_urban_area") == 9
    assert mesure.valeurs_speciales("Rural_or_urban_area") == [0, 3]
    # Par puce : les lignes 0 (ALEX), 1 (ISAC_V1) et 2 (ISAC_V2) sont une par puce.
    assert mesure.valeurs_speciales("Rural_or_urban_area", "ALEX") == [0, 1]
    # La table elle-même n'est pas modifiée : le 9 reste écrit dans le tableau.
    assert tableau.loc[0, "Rural_or_urban_area"] == 9
    # Colonne en texte : « 9 » exclu aussi.
    tableau.loc[3, "Treatment_of_rhinitis"] = "9"
    assert mesure.effectif_mesure("Treatment_of_rhinitis") == 11


def test_seuil_applique_apres_exclusion_des_9(tableau, monkeypatch):
    for ligne in (0, 1, 2):
        tableau.loc[ligne, "Rural_or_urban_area"] = 9
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 10)
    # 12 lignes, mais 9 mesurés une fois les 9 exclus : sous le seuil de 10.
    texte = mesure.verifier_perimetre("Rural_or_urban_area")
    assert texte.startswith("abstention") and "9 patients mesurés" in texte
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 9)
    assert mesure.verifier_perimetre("Rural_or_urban_area") == 9


def test_9_est_une_vraie_valeur_ailleurs(tableau):
    # Age, un mois et un dosage : 9 n'y est ni exclu ni signalé.
    tableau.loc[0, "Age"] = 9
    tableau.loc[1, "Blood_Month_sample"] = 9
    tableau.loc[2, "Act_d_1"] = 9
    # Treatment_of_athsma : sens du 9 non confirmé, donc hors de la liste.
    tableau.loc[3, "Treatment_of_athsma"] = "9"
    for colonne in ("Age", "Blood_Month_sample", "Act_d_1", "Treatment_of_athsma"):
        assert mesure.valeurs_speciales(colonne)[1] == 0
        assert mesure.effectif_mesure(colonne) == 12
    assert "Treatment_of_athsma" not in mesure.COLONNES_9_NON_RENSEIGNE


def test_est_clinique(tableau):
    assert mesure.est_clinique("Rural_or_urban_area") and mesure.est_clinique("Age")
    assert not mesure.est_clinique("Act_d_1")
    assert not mesure.est_clinique("Colonne_Inventee")
