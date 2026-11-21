"""Tests de moyenne.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : pour le
cas normal, on le baisse le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import mesure, moyenne
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def test_colonne_inconnue(tableau):
    assert moyenne.moyenne_colonne("Colonne_Inventee").startswith("abstention")


def test_colonne_non_mesuree_par_la_puce(tableau):
    texte = moyenne.moyenne_colonne("Aca_m", "ISAC_V1")
    assert texte.startswith("abstention") and "aucune puce" in texte


def test_effectif_sous_le_seuil(tableau):
    texte = moyenne.moyenne_colonne("Act_d_1", "ALEX")
    assert texte.startswith("abstention") and "minimum 30" in texte


def test_cas_normal_denominateur_mesure(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # Tout le fichier : (0,42 + 5,6 + 3 + 0,6 + 1,3) / 12 = 0,91.
    assert "0.9100 sur 12 patients" in moyenne.moyenne_colonne("Act_d_1")
    # Aca_m, ALEX seule : (1,7 + 0 + 0 + 0,9) / 4 = 0,65 ; les vides des autres puces ne comptent pas.
    assert "0.6500 sur 4 patients" in moyenne.moyenne_colonne("Aca_m", "ALEX")


def test_valeurs_speciales_signalees_sans_recodage(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    tableau.loc[0, "Act_d_1"] = -1  # patient ALEX
    texte = moyenne.moyenne_colonne("Act_d_1")
    assert "1 valeurs -1" in texte and "pas été recodées" in texte
    # Laissée dans la moyenne : (-1 + 5,6 + 3 + 0,6 + 1,3) / 12 = 0,7917.
    assert "0.7917 sur 12 patients" in texte


def test_colonne_clinique_abstention(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    for colonne in ("Rural_or_urban_area", "Skin_Symptoms", "Blood_Month_sample"):
        texte = moyenne.moyenne_colonne(colonne)
        assert texte.startswith("abstention : colonne clinique codée, une moyenne de codes")
        assert "repartition_categories" in texte


def test_age_reste_calculable(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # Age est une vraie mesure : (34 + 8 + 51 + 27 + 63 + 15 + 42 + 19 + 70 + 38 + 6 + 23) / 12 = 33.
    texte = moyenne.moyenne_colonne("Age")
    assert "33.0000 sur 12 patients mesurés" in texte
    # Et un 9 y est un âge, ni exclu ni signalé.
    tableau.loc[0, "Age"] = 9
    texte = moyenne.moyenne_colonne("Age")
    assert "30.9167 sur 12 patients mesurés" in texte and "valeurs 9" not in texte


def test_9_reste_une_valeur_dans_un_dosage(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    tableau.loc[1, "Act_d_1"] = 9  # 0 avant : (10,92 + 9) / 12 = 1,66
    texte = moyenne.moyenne_colonne("Act_d_1")
    assert "1.6600 sur 12 patients mesurés" in texte
    assert "valeurs 9" not in texte


def test_quatre_decimales_pas_de_double_arrondi(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # 4 ALEX : (26,8 + 26,8 + 26,8 + 26,9996) / 4 = 26,8499, que 2 décimales arrondiraient à 26,85.
    tableau["Age"] = tableau["Age"].astype(float)
    tableau.loc[tableau["Chip_Type"] == "ALEX", "Age"] = [26.8, 26.8, 26.8, 26.9996]
    texte = moyenne.moyenne_colonne("Age", "ALEX")
    assert "26.8499 sur 4 patients mesurés" in texte


def test_puce_non_precisee_cite_le_perimetre(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # Aca_m : ALEX seule, 4 patients mesurés, (1,7 + 0 + 0 + 0,9) / 4 = 0,65.
    texte = moyenne.moyenne_colonne("Aca_m")
    assert texte.startswith("Calculé sur ALEX seule : ")
    assert "0.6500 sur 4 patients mesurés" in texte
