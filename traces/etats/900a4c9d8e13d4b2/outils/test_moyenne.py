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
    assert "0.91 sur 12 patients" in moyenne.moyenne_colonne("Act_d_1")
    # Aca_m, ALEX seule : (1,7 + 0 + 0 + 0,9) / 4 = 0,65 ; les vides des autres puces ne comptent pas.
    assert "0.65 sur 4 patients" in moyenne.moyenne_colonne("Aca_m", "ALEX")


def test_valeurs_speciales_signalees_sans_recodage(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    tableau.loc[0, "Act_d_1"] = -1  # patient ALEX
    texte = moyenne.moyenne_colonne("Act_d_1")
    assert "1 valeurs -1" in texte and "pas été recodées" in texte
    # Laissée dans la moyenne : (-1 + 5,6 + 3 + 0,6 + 1,3) / 12 = 0,7917.
    assert "0.7917 sur 12 patients" in texte
