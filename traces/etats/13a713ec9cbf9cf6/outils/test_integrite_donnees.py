import pandas as pd

from kit import donnees
from equipe.outils import mesure, moyenne, proportion


def test_les_calculs_ne_modifient_pas_le_tableau_source(monkeypatch):
    tableau = donnees.charger()
    original = tableau.copy(deep=True)

    monkeypatch.setattr(mesure.donnees, "charger", lambda: tableau)

    moyenne.moyenne_colonne("Act_d_1")
    proportion.proportion_positifs("Act_d_1")

    pd.testing.assert_frame_equal(tableau, original)
