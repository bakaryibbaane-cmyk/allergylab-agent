# Mesure de départ : agent d'origine (sans consigne ni outils), lot 1

| Question | Attendu | Réponse de l'agent | Verdict | Étapes |
|---|---|---|---|---|
| q01 nombre de patients | 4271 | 4271 | juste | 2 |
| q02 puce ALEX | 1139 | 1139 | juste | 3 |
| q03 sexe féminin | 2070 | abstention | abstention à tort | 2 |
| q04 âge moyen | 23,08 | 23,077 | juste | 2 |
| q05 rural | 325 | 966 (passage 1), abstention (passage 2) | faux, puis abstention à tort | 3 |
| q06 % urbain | 74,83 | 74,83 (code deviné) | juste | 3 |
| q07 valeurs Che_a | 1139 | 1139 | juste | 2 |
| q08 Che_a x ISAC_V1 | abstention | abstention | abstention fondée | 3 |
| q09 conjonctivite | abstention | abstention | abstention fondée | 3 |

Justesse : 5 sur 7. Abstention : 2 sur 2. Coût du tour : environ 0,0136 $.
Cause de tous les échecs : l'agent ne connaît pas les codes du dictionnaire (Gender, Rural_or_urban_area).
