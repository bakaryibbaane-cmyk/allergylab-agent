"""Tests de intervalle.py : cas connus et propriétés, sans réseau. Signé : équipe 5."""

import pytest

from equipe.outils.intervalle import intervalle_wilson


def test_zero_positif():
    basse, haute = intervalle_wilson(0, 100)
    assert basse == 0.0
    assert haute == pytest.approx(3.70, abs=0.01)


def test_tous_positifs():
    basse, haute = intervalle_wilson(100, 100)
    assert basse == pytest.approx(96.30, abs=0.01)
    assert haute == 100.0


def test_cinquante_pour_cent_sur_cent():
    basse, haute = intervalle_wilson(50, 100)
    assert basse == pytest.approx(40.38, abs=0.01)
    assert haute == pytest.approx(59.62, abs=0.01)


def test_petit_effectif_intervalle_large():
    # 3 positifs sur 10 : valeurs de référence de Wilson, 10,8 % à 60,3 %.
    basse, haute = intervalle_wilson(3, 10)
    assert basse == pytest.approx(10.8, abs=0.1)
    assert haute == pytest.approx(60.3, abs=0.1)


def test_effectif_plus_grand_intervalle_plus_etroit():
    petit = intervalle_wilson(3, 10)
    grand = intervalle_wilson(300, 1000)
    assert (grand[1] - grand[0]) < (petit[1] - petit[0])


@pytest.mark.parametrize("effectif", [1, 2, 7, 30, 100, 3132])
def test_bornes_dans_0_100_et_autour_de_la_proportion(effectif):
    for positifs in range(0, effectif + 1, max(1, effectif // 20)):
        basse, haute = intervalle_wilson(positifs, effectif)
        proportion = 100 * positifs / effectif
        assert 0 <= basse <= proportion <= haute <= 100


def test_entrees_invalides():
    for positifs, effectif in [(0, 0), (5, 4), (-1, 10)]:
        with pytest.raises(ValueError):
            intervalle_wilson(positifs, effectif)
