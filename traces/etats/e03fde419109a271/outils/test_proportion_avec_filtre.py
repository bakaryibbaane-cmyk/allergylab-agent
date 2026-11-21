"""Tests de proportion_avec_filtre.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : on le baisse
le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import mesure
from equipe.outils import proportion_avec_filtre as outil
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def test_arguments_invalides(tableau):
    assert outil.proportion_avec_filtre("Act_d_1", 0, "Age", "~", 10).startswith("abstention")
    assert outil.proportion_avec_filtre("Age", 0, "Age", "<", 10).startswith("abstention")
    assert outil.proportion_avec_filtre("Act_d_1", 0, "Rural_or_urban_area", "==", 1).startswith("abstention")
    assert outil.proportion_avec_filtre("Colonne_Inventee", 0, "Age", "<", 10).startswith("abstention")


def test_proportion_parmi_les_patients_du_filtre(tableau):
    retenus = tableau[tableau["Age"] < 30]
    mesures = retenus["Act_d_1"].dropna()
    positifs = int((mesures > 0).sum())
    texte = outil.proportion_avec_filtre("Act_d_1", 0, "Age", "<", 30)
    assert f"{positifs} positifs sur {len(mesures)} patients mesurés" in texte
    assert "strictement inférieur à 30 (<)" in texte


def test_filtre_sur_un_dosage(tableau):
    # Filtre : Act_d_1 > 0 ; on cherche les positifs d'Aln_g_1 parmi eux.
    retenus = tableau[tableau["Act_d_1"] > 0]
    mesures = retenus["Aln_g_1"].dropna()
    positifs = int((mesures > 0).sum())
    texte = outil.proportion_avec_filtre("Aln_g_1", 0, "Act_d_1", ">", 0)
    assert f"{positifs} positifs sur {len(mesures)} patients mesurés" in texte


def test_patients_du_filtre_sans_dosage_exclus_et_comptes(tableau):
    # Aca_m est vide pour les puces ISAC_V1 : ces patients du filtre sont exclus et comptés.
    retenus = tableau[tableau["Age"] >= 0]
    sans = int(retenus["Aca_m"].isna().sum())
    texte = outil.proportion_avec_filtre("Aca_m", 0, "Age", ">=", 0)
    assert f"{sans} patients du filtre exclus faute de mesure" in texte


def test_effectif_sous_le_seuil(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    texte = outil.proportion_avec_filtre("Act_d_1", 0, "Age", "<", 30)
    assert texte.startswith("abstention") and "minimum 30" in texte


def test_filtre_trop_restrictif(tableau):
    texte = outil.proportion_avec_filtre("Act_d_1", 0, "Age", ">", 1000)
    assert texte.startswith("abstention") and "0 patients" in texte


def test_moins_un_signales(tableau, monkeypatch):
    table = tableau.copy()
    table.loc[0, "Act_d_1"] = -1.0
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    texte = outil.proportion_avec_filtre("Act_d_1", 0, "Age", ">=", 0)
    assert "valeurs -1" in texte and "pas été recodées" in texte


def test_le_fichier_est_restitue(tableau):
    avant = mesure.donnees.charger
    outil.proportion_avec_filtre("Act_d_1", 0, "Age", ">=", 0)
    assert mesure.donnees.charger is avant
