"""Tests de classer_allergenes.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : on le baisse
le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import classer_allergenes as outil
from equipe.outils import communs, mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def _lignes(texte):
    """Les noms de colonnes du classement, dans l'ordre."""
    corps = texte.split("\n")[1].rstrip(".")
    return [partie.split(". ", 1)[1].split(" : ")[0] for partie in corps.split(" ; ")]


def test_arguments_invalides(tableau):
    assert outil.classer_allergenes("moyenne", 0, False).startswith("abstention")
    assert outil.classer_allergenes("taux", 0, False, rang_max=0).startswith("abstention")
    assert outil.classer_allergenes("taux", 0, False, puce="PUCE_INVENTEE").startswith("abstention")


def test_taux_calcule_sur_les_seuls_patients_mesures(tableau):
    texte = outil.classer_allergenes("taux", 0, False, rang_max=20)
    for colonne in _lignes(texte):
        mesures = tableau[colonne].dropna()
        attendu = f"{colonne} : {communs.fr(100 * (mesures > 0).sum() / len(mesures), 2)} %"
        assert attendu in texte


def test_effectif_et_rang_max(tableau):
    texte = outil.classer_allergenes("effectif", 0, False, rang_max=2)
    assert len(_lignes(texte)) == 2
    premier = _lignes(texte)[0]
    nombres = {c: int((tableau[c] > 0).sum()) for c in communs.dosages() if c in tableau.columns}
    assert f"{premier} : {nombres[premier]} positifs" in texte
    assert nombres[premier] == max(nombres.values())


def test_strict_ou_inclusif(tableau):
    # Act_d_1 compte des 0 : avec >= 0, tous les patients mesurés sont positifs.
    strict = outil.classer_allergenes("effectif", 0, False, rang_max=20)
    large = outil.classer_allergenes("effectif", 0, True, rang_max=20)
    assert "(strict)" in strict and "(inclusif)" in large
    assert "Act_d_1 : 12 positifs (sur 12 mesurés)" in large
    assert "Act_d_1 : 12 positifs" not in strict


def test_ex_aequo_signales(tableau):
    # Avec un seuil très haut, aucune colonne n'a de positif : tout le monde est ex æquo à 0.
    texte = outil.classer_allergenes("effectif", 1000, False, rang_max=3)
    assert "ex æquo" in texte


def test_une_puce_ecarte_les_colonnes_non_mesurees(tableau):
    texte = outil.classer_allergenes("taux", 0, False, rang_max=20, puce="ISAC_V1")
    assert "Aca_m" not in texte.split("\n")[1]
    assert "colonnes écartées" in texte


def test_valeurs_moins_un_signalees(tableau, monkeypatch):
    table = tableau.copy()
    table.loc[0, "Act_d_1"] = -1.0
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    texte = outil.classer_allergenes("taux", 0, False)
    assert "valeurs -1" in texte and "non recodées" in texte


def test_effectif_sous_le_seuil_partout(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    assert outil.classer_allergenes("taux", 0, False).startswith("abstention")


def test_le_fichier_est_restitue(tableau):
    avant = mesure.donnees.charger
    outil.classer_allergenes("taux", 0, False)
    assert mesure.donnees.charger is avant
