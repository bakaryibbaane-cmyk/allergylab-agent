"""Tests de proportion.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée (4 patients
par puce) : pour le cas normal, on le baisse le temps du test.
Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import mesure, proportion
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def test_colonne_inconnue(tableau):
    assert proportion.proportion_positifs("Colonne_Inventee").startswith("abstention")


def test_colonne_non_mesuree_par_la_puce(tableau):
    texte = proportion.proportion_positifs("Aca_m", "ISAC_V1")
    assert texte.startswith("abstention") and "aucune puce" in texte


def test_effectif_sous_le_seuil(tableau):
    texte = proportion.proportion_positifs("Act_d_1", "ALEX")
    assert texte.startswith("abstention") and "minimum 30" in texte


def test_cas_normal_denominateur_mesure(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    # Act_d_1 sur tout le fichier : 5 valeurs > 0 sur 12 patients mesurés.
    texte = proportion.proportion_positifs("Act_d_1")
    assert texte.startswith("41,7 % (IC 95 % : ")
    assert "5 positifs sur 12 mesurés" in texte
    # Aca_m, ALEX seule : 2 sur 4 mesurés, pas 2 sur 12 lignes.
    texte = proportion.proportion_positifs("Aca_m", "ALEX")
    assert texte.startswith("50,0 % (IC 95 % : 15,0 à 85,0)")
    assert "2 positifs sur 4 mesurés" in texte


def test_valeurs_speciales_signalees_sans_recodage(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    tableau.loc[1, "Act_d_1"] = -1  # patient ISAC_V1
    texte = proportion.proportion_positifs("Act_d_1")
    assert "1 valeurs -1" in texte and "pas été recodées" in texte
    # Ni recodée ni exclue : -1 n'est pas > 0, mais reste dans les 12 mesurés.
    assert "5 positifs sur 12 mesurés" in texte


def test_format_francais_des_milliers(tableau):
    # Format du texte rendu : virgule décimale, espace entre les milliers.
    assert proportion._fr(3.74) == "3,7"
    assert proportion._entier(3132) == "3 132"
