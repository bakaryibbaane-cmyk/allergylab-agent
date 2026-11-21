"""Tests de croiser_colonnes.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : on le baisse
le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pandas as pd
import pytest

from equipe.outils import croiser_colonnes as outil
from equipe.outils import mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def _avec(monkeypatch, table, **colonnes):
    """Remplace des colonnes de la table inventée, le temps du test."""
    table = table.copy()
    for nom, valeurs in colonnes.items():
        table[nom] = valeurs
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def test_arguments_invalides(tableau):
    assert outil.croiser_colonnes("French_Region", "French_Region").startswith("abstention")
    assert outil.croiser_colonnes("French_Region", "French_Residence_Department", 0).startswith("abstention")
    assert outil.croiser_colonnes("Colonne_Inventee", "French_Region").startswith("abstention")
    assert outil.croiser_colonnes("French_Region", "Colonne_Inventee").startswith("abstention")
    # Un dosage n'est pas une colonne clinique.
    assert outil.croiser_colonnes("Act_d_1", "French_Region").startswith("abstention")


def test_valeurs_associees_a_plusieurs_valeurs(tableau, monkeypatch):
    # Trois valeurs de la première colonne : « a » avec x et y, « b » avec x seul, « c » avec x, y et z.
    n = len(tableau)
    premiere = ["a", "a", "b", "b", "b", "c", "c", "c", "c", "a", "b", "c"]
    seconde = ["x", "y", "x", "x", "x", "x", "y", "z", "x", "y", "x", "x"]
    assert len(premiere) == n
    _avec(monkeypatch, tableau, French_Residence_Department=premiere, French_Region=seconde)
    texte = outil.croiser_colonnes("French_Residence_Department", "French_Region")
    assert texte.startswith("2 valeurs distinctes de 'French_Residence_Department' sur 3 sont associées à au moins 2")
    assert texte.count("\n") == 1  # une ligne de résultat, une ligne de définition
    # Le minimum se règle ; 1 compte toutes les valeurs, 3 seulement celle qui a trois voisines.
    assert outil.croiser_colonnes("French_Residence_Department", "French_Region", 1).startswith("3 valeurs distinctes")
    assert outil.croiser_colonnes("French_Residence_Department", "French_Region", 3).startswith("1 valeurs distinctes")
    assert outil.croiser_colonnes("French_Residence_Department", "French_Region", 4).startswith("0 valeurs distinctes")


def test_le_croisement_n_est_pas_symetrique(tableau, monkeypatch):
    premiere = ["a", "a", "b", "b", "b", "c", "c", "c", "c", "a", "b", "c"]
    seconde = ["x", "y", "x", "x", "x", "x", "y", "z", "x", "y", "x", "x"]
    _avec(monkeypatch, tableau, French_Residence_Department=premiere, French_Region=seconde)
    # Dans l'autre sens : x est avec a, b et c ; y avec a et c ; z avec c seul.
    texte = outil.croiser_colonnes("French_Region", "French_Residence_Department")
    assert texte.startswith("2 valeurs distinctes de 'French_Region' sur 3")


def test_cellules_vides_ecartees(tableau, monkeypatch):
    premiere = ["a", "a", "b", "b", "b", "c", "c", "c", "c", "a", "b", "c"]
    seconde = ["x", "y", "x", "x", "x", "x", "y", "z", "x", "y", "x", "x"]
    # Une cellule vide est écartée avec son patient : elle ne crée pas une valeur de plus.
    premiere[2], seconde[2] = "b", None
    seconde[3] = "w"
    _avec(monkeypatch, tableau, French_Residence_Department=premiere, French_Region=seconde)
    texte = outil.croiser_colonnes("French_Residence_Department", "French_Region")
    assert "vide (1) sont écartés" in texte and "11 patients renseignés" in texte
    # « b » a maintenant x et w : il compte, comme « a » et « c ».
    assert texte.startswith("3 valeurs distinctes de 'French_Residence_Department' sur 3")


def test_trop_peu_de_patients_renseignes(tableau, monkeypatch):
    seconde = [None] * 10 + ["x", "y"]
    _avec(monkeypatch, tableau, French_Region=seconde)
    assert outil.croiser_colonnes("French_Residence_Department", "French_Region").startswith("abstention")


def test_valeurs_numeriques_lues_comme_du_texte():
    # Une colonne lue en nombres : 1.0 et 1 sont la même valeur, 1.5 reste 1.5.
    assert outil._texte(pd.Series([1.0, 10.0, 1.5])).tolist() == ["1", "10", "1.5"]
    assert outil._texte(pd.Series([" a ", "b"])).tolist() == ["a", "b"]


def test_le_texte_rendu_n_est_jamais_le_tableau(tableau):
    assert "EX01" not in outil.croiser_colonnes("French_Residence_Department", "French_Region")
