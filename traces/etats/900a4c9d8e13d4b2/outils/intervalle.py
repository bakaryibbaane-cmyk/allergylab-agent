"""Intervalle de confiance de Wilson pour une proportion, sans dépendance.

Pourquoi Wilson plutôt que la formule « p ± 1,96 racine(p(1-p)/n) » : celle-ci
donne un intervalle de largeur nulle à 0 % ou à 100 %, et déborde de 0-100 sur
les petits effectifs. Wilson reste fiable sur les petits effectifs et sur les
proportions proches de 0 %, qui sont fréquentes pour les allergènes rares.
Signé : équipe 5.
"""

import math

Z_95 = 1.96  # quantile de la loi normale pour un niveau de confiance de 95 %


def intervalle_wilson(positifs, effectif):
    """Rend (borne basse, borne haute) en %, intervalle de confiance à 95 % de Wilson.

    effectif est le nombre de patients mesurés (le dénominateur), jamais le
    nombre de lignes du tableau.
    """
    if effectif <= 0 or not 0 <= positifs <= effectif:
        raise ValueError("il faut 0 <= positifs <= effectif et un effectif > 0.")
    p = positifs / effectif
    z2 = Z_95**2
    centre = (p + z2 / (2 * effectif)) / (1 + z2 / effectif)
    demi_largeur = Z_95 * math.sqrt(p * (1 - p) / effectif + z2 / (4 * effectif**2)) / (1 + z2 / effectif)
    # Aux extrémités la borne exacte est 0 ou 1 ; on l'impose pour éviter un
    # écart d'arrondi qui mettrait la proportion hors de son intervalle.
    basse = 0.0 if positifs == 0 else max(0.0, centre - demi_largeur)
    haute = 100.0 if positifs == effectif else min(1.0, centre + demi_largeur) * 100
    return basse * 100, haute
