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


def test_colonne_clinique_abstention(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    for colonne in ("Rural_or_urban_area", "Age"):
        texte = proportion.proportion_positifs(colonne)
        assert texte.startswith("abstention : colonne clinique codée")
        assert "répartition par catégorie" in texte


def test_9_dans_un_dosage_ni_exclu_ni_signale(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    tableau.loc[1, "Act_d_1"] = 9  # patient ISAC_V1 (0 avant), une vraie valeur de dosage
    texte = proportion.proportion_positifs("Act_d_1")
    # 9 > 0 : il compte parmi les positifs (6 au lieu de 5), sur 12 mesurés, sans signalement.
    assert "6 positifs sur 12 mesurés" in texte
    assert "valeurs 9" not in texte


def test_puce_non_precisee_perimetre_des_puces_qui_mesurent(tableau, monkeypatch):
    # Aca_m : ALEX seule, 2 positifs sur 4 mesurés ; ni 2 sur 12 lignes, ni abstention à 33 %.
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    texte = proportion.proportion_positifs("Aca_m")
    assert texte.startswith("Calculé sur ALEX seule : 50,0 % (IC 95 % : ")
    assert "2 positifs sur 4 mesurés" in texte and "(ALEX seule)" in texte
    # Sous le seuil de 30 dans ce périmètre : abstention qui cite le périmètre.
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    texte = proportion.proportion_positifs("Aca_m")
    assert texte.startswith("abstention") and "4 patients" in texte and "ALEX seule" in texte
