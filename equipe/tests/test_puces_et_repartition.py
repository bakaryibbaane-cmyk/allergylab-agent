"""Tests des outils d'identification des puces et de répartition."""

import pandas as pd
import pytest

from equipe.outils import puces_qui_mesurent, repartition_colonne


@pytest.fixture
def donnees_fictives(monkeypatch):
    dictionnaire = pd.DataFrame([
        {
            "colonne": "Che_a",
            "bloc": "allergene",
            "puce_ALEX": True,
            "puce_ISAC_V1": False,
            "puce_ISAC_V2": False,
        }
    ])

    tableau = pd.DataFrame({
        "Chip_Type": ["ALEX", "ALEX", "ALEX", "ISAC_V1", "ISAC_V2"],
        "Che_a": [0.0, 0.03, 0.05, None, None],
    })

    monkeypatch.setattr(
        puces_qui_mesurent,
        "colonnes",
        lambda: dictionnaire,
    )
    monkeypatch.setattr(
        repartition_colonne,
        "colonnes",
        lambda: dictionnaire,
    )
    monkeypatch.setattr(
        repartition_colonne,
        "charger",
        lambda: tableau,
    )

    return tableau


def test_puces_qui_mesurent_identifie_che_a(donnees_fictives):
    texte = puces_qui_mesurent.puces_qui_mesurent("Che_a")

    assert "mesurée par ALEX" in texte
    assert "non mesurée par ISAC_V1, ISAC_V2" in texte


def test_puces_qui_mesurent_colonne_absente(donnees_fictives):
    texte = puces_qui_mesurent.puces_qui_mesurent("Colonne_Inconnue")

    assert "colonne absente" in texte


def test_repartition_refuse_puce_non_mesurante(donnees_fictives):
    texte = repartition_colonne.repartition_colonne("Che_a", "ISAC_V1")

    assert "non mesurée par ISAC_V1" in texte
    assert "répartition non calculée" in texte


def test_repartition_compte_uniquement_les_patients_mesures(
    donnees_fictives,
):
    texte = repartition_colonne.repartition_colonne("Che_a", "ALEX")

    assert "3 patients (ALEX)" in texte
    assert "cellules vides -> 0" in texte


def test_repartition_toutes_exclut_les_puces_non_mesurantes(
    donnees_fictives,
):
    texte = repartition_colonne.repartition_colonne("Che_a", "toutes")

    assert "3 patients" in texte
    assert "ALEX" in texte
    assert "cellules vides -> 0" in texte
