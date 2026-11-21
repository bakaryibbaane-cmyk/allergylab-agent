import pytest

from kit.donnees import colonnes
from equipe.outils import puces_qui_mesurent as outil


@pytest.mark.parametrize("nombre", [1, 2, 3])
def test_puces_nombre_de_puces(nombre):
    df = colonnes()
    puces = [c for c in df.columns if c.startswith("puce_")]

    df["nombre_puces"] = df[puces].sum(axis=1)
    exemples = df[df["nombre_puces"] == nombre]

    assert not exemples.empty

    ligne = exemples.iloc[0]
    nom = ligne["colonne"]

    resultat = outil.puces_qui_mesurent(str(nom))

    mesurees = [
        c.replace("puce_", "")
        for c in puces if ligne[c]
    ]
    non_mesurees = [
        c.replace("puce_", "")
        for c in puces if not ligne[c]
    ]

    assert "mesurée par " + ", ".join(mesurees) in resultat

    if non_mesurees:
        assert "non mesurée par " + ", ".join(non_mesurees) in resultat


def test_puces_colonne_inexistante():
    resultat = outil.puces_qui_mesurent("Molecule_Inexistante")
    assert "colonne absente du tableau" in resultat
