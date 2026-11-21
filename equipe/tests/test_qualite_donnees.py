"""Tests métier de l'outil qualite_donnees, sur le vrai tableau chargé par le kit (hors ligne, sans modèle).

Règle de l'équipe : les -1 sont comptés et signalés, jamais exclus ; le 9 n'est exclu
que pour les colonnes de COLONNES_9_NON_RENSEIGNE (equipe/outils/mesure.py).

Lancer : uv run pytest -q equipe/tests
"""

import pandas as pd

from equipe.outils import qualite_donnees as module
from equipe.outils.mesure import COLONNES_9_NON_RENSEIGNE
from equipe.outils.qualite_donnees import effectifs, qualite_donnees


def test_colonne_non_mesuree_par_la_puce():
    texte = qualite_donnees("Che_a", "ISAC_V1")
    assert "non mesurée par cette puce" in texte
    assert "structurelles" in texte


def test_colonne_mesuree_complete():
    texte = qualite_donnees("Che_a", "ALEX")
    assert "1139 cellules exploitables (100.0 %)" in texte
    assert "0 cellules vides" in texte


def test_clinique_dictionnaire_confirme():
    texte = qualite_donnees("Rural_or_urban_area", "toutes")
    assert "2980 sont au code 9" in texte
    assert "selon le dictionnaire" in texte
    assert "1291 cellules exploitables (30.2 %)" in texte


def test_clinique_sens_non_confirme():
    texte = qualite_donnees("Skin_Symptoms", "toutes")
    assert "traité comme non renseigné (sens non confirmé)" in texte
    assert "1826 cellules exploitables" in texte


def test_9_hors_liste_n_est_pas_exclu():
    # Age : 9 est une vraie valeur. Treatment_of_athsma : sens du 9 non confirmé, hors liste.
    assert "code 9" not in qualite_donnees("Age", "toutes")
    assert "Treatment_of_athsma" not in COLONNES_9_NON_RENSEIGNE
    assert "code 9" not in qualite_donnees("Treatment_of_athsma", "toutes")
    assert "4271 cellules exploitables" in qualite_donnees("Treatment_of_athsma", "toutes")


def test_moins_un_est_compte_et_jamais_exclu():
    texte = qualite_donnees("Act_d_1", "toutes")
    assert "Valeurs -1 : 1 (comptées, ni exclues ni recodées" in texte
    # Aucune cellule retirée : exploitables + vides = patients.
    effectif = int(texte.split(" patients")[0].split(", ")[-1])
    exploitables = int(texte.split(" : ")[1].split(" cellules exploitables")[0])
    vides = int(texte.split("exploitables")[1].split("%), ")[1].split(" cellules vides")[0])
    assert exploitables + vides == effectif


def test_effectifs_dosage_compte_sans_exclure():
    serie = pd.Series([-1.0, 9.0, 0.5, None])
    renseignees, vides, moins_un, neuf_exclus, neuf_signales = effectifs(serie, "Act_d_1", "dosage")
    assert (renseignees, vides, moins_un, neuf_exclus, neuf_signales) == (3, 1, 1, 0, 1)


def test_effectifs_clinique_exclut_le_9_de_la_liste_seulement():
    serie = pd.Series([9, 9, 1, 0])
    assert effectifs(serie, "Rural_or_urban_area", "clinique")[3] == 2
    assert effectifs(serie, "Treatment_of_athsma", "clinique")[3] == 0


def test_colonne_absente_et_puce_inconnue():
    assert "absente du tableau" in qualite_donnees("Conjonctivite", "toutes")
    assert "puce inconnue" in qualite_donnees("Age", "XYZ")


def test_resume_par_puce():
    texte = qualite_donnees("toutes", "ISAC_V2")
    assert "781 patients" in texte
    assert "colonnes mesurées par cette puce" in texte
    assert "sens non confirmé" in texte


def test_l_outil_ne_modifie_pas_le_tableau(monkeypatch):
    tableau = module.charger()
    original = tableau.copy(deep=True)
    monkeypatch.setattr(module, "charger", lambda: tableau)
    qualite_donnees("Rural_or_urban_area", "toutes")
    qualite_donnees("toutes", "ALEX")
    pd.testing.assert_frame_equal(tableau, original)
