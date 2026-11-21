"""Tests de variables_du_tableau.py, hors ligne, sur la table inventée de kit/exemple/.

Signé : équipe 5.
"""

from pathlib import Path

import pandas as pd
import pytest

from equipe.outils import variables_du_tableau as module
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(module.donnees, "charger", lambda: table)
    return table


def test_sans_motif_le_nombre_sans_les_noms(tableau):
    texte = module.variables_du_tableau()
    assert texte.startswith(f"Le tableau contient {len(tableau.columns)} variables")
    assert "ne sont pas listés" in texte
    assert "Age_of_onsets" not in texte  # aucun nom de colonne dans la réponse


def test_motif_vide_ou_espaces_comme_sans_motif(tableau):
    assert module.variables_du_tableau("   ") == module.variables_du_tableau()


def test_avec_motif(tableau):
    attendues = [c for c in tableau.columns if "age" in c.lower()]
    texte = module.variables_du_tableau("age")
    assert texte.startswith(f"{len(attendues)} variables contiennent 'age'")
    for nom in attendues:
        assert nom in texte
    assert "tronquée" not in texte


def test_motif_sans_resultat(tableau):
    texte = module.variables_du_tableau("zzz_inventee")
    assert texte.startswith("Aucune variable ne contient 'zzz_inventee'")
    assert f"{len(tableau.columns)} variables" in texte


def test_insensible_a_la_casse(tableau):
    assert module.variables_du_tableau("AGE") == module.variables_du_tableau("age").replace("'age'", "'AGE'")
    assert module.variables_du_tableau("chip_type").count("Chip_Type") == 1


def test_plafond_de_30_noms(monkeypatch):
    # Un tableau inventé de 45 colonnes dont le nom contient « dosage ».
    table = pd.DataFrame({f"Dosage_{i:02d}": [1.0] for i in range(45)})
    monkeypatch.setattr(module.donnees, "charger", lambda: table)
    texte = module.variables_du_tableau("dosage")
    assert texte.startswith("45 variables contiennent 'dosage' sur les 45 du tableau")
    assert "Liste tronquée : 30 noms affichés sur 45." in texte
    assert texte.count("Dosage_") == 30
    assert "Dosage_29" in texte and "Dosage_30" not in texte


def test_pile_30_pas_tronque(monkeypatch):
    table = pd.DataFrame({f"Dosage_{i:02d}": [1.0] for i in range(30)})
    monkeypatch.setattr(module.donnees, "charger", lambda: table)
    assert "tronquée" not in module.variables_du_tableau("dosage")


def test_aucune_valeur_de_patient_et_tableau_inchange(tableau):
    avant = tableau.copy(deep=True)
    textes = [module.variables_du_tableau(), module.variables_du_tableau("a"), module.variables_du_tableau("Age")]
    pd.testing.assert_frame_equal(tableau, avant)
    # Aucun identifiant de patient de la table inventée dans les réponses.
    for texte in textes:
        assert not any(str(identifiant) in texte for identifiant in tableau["Patient_ID"])
