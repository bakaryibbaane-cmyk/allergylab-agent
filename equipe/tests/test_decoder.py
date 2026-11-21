import pytest

from equipe.outils import decoder


@pytest.mark.parametrize(
    ("colonne", "valeur", "attendu"),
    [
        ("Gender", "1", "1 = masculin"),
        ("Gender", "0", "0 = féminin"),
        ("Rural_or_urban_area", "9", "9 = non renseigné"),
        ("Rural_or_urban_area", "0", "0 = rural"),
        ("Rural_or_urban_area", "1", "1 = urbain"),
    ],
)
def test_decoder_codes_documentes(colonne, valeur, attendu):
    assert attendu in decoder.decoder(colonne, valeur)


def test_decoder_code_inconnu():
    texte = decoder.decoder("Gender", "7")
    assert "non documenté" in texte


def test_decoder_colonne_inconnue():
    texte = decoder.decoder("Colonne_Inconnue", "1")
    assert "colonne non documentée" in texte


def test_decoder_plusieurs_codes():
    texte = decoder.decoder("General_cofactors", "1,3")
    assert "effort" in texte
    assert "alcool" in texte


def test_decoder_valeur_manquante():
    assert decoder.decoder("Gender", None) == "valeur manquante"


def test_decoder_code_numerique_decimal():
    texte = decoder.decoder("Gender", 1.0)
    assert "1 = masculin" in texte


def test_decoder_9_rural_documente():
    assert "9 = non renseigné (dictionnaire)" in decoder.decoder("Rural_or_urban_area", "9")


@pytest.mark.parametrize(
    "colonne",
    ["Treatment_of_atopic_dematitis", "General_cofactors", "Age_of_onsets"],
)
def test_decoder_9_autres_colonnes_non_confirme(colonne):
    texte = decoder.decoder(colonne, "9")
    assert "sens non confirmé" in texte
    assert "non renseigné" not in texte


def test_decoder_code_10_cofacteurs_non_confirme():
    assert "sens non confirmé" in decoder.decoder("General_cofactors", "10")


def test_decoder_moins_un_non_documente():
    assert "non documenté" in decoder.decoder("Gender", "-1")
    assert "non documenté" in decoder.decoder("General_cofactors", "-1")
