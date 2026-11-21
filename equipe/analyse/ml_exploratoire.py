# Nécessite scikit-learn, non installé dans le verrouillage du projet (règle 6, test_dependances_figees) ; lancer avec uv run --with scikit-learn
"""Méthodes ML exploratoires. Résultats non diagnostiques et non causaux."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

SPECIAL = (-1, 9)


def _prepare(df: pd.DataFrame, columns: list[str], exclude_special: bool = False):
    if not columns:
        raise ValueError("Sélectionner au moins une variable.")
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Colonnes absentes : {missing}")
    x = df[columns].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if exclude_special:
        x = x.mask(x.isin(SPECIAL))
    valid = x.notna().any(axis=1)
    x = x.loc[valid]
    if len(x) < 3:
        raise ValueError("Au moins trois lignes avec des données sont nécessaires.")
    imputer = SimpleImputer(strategy="median")
    arr = imputer.fit_transform(x)
    arr = StandardScaler().fit_transform(arr)
    return arr, x.index, int((~valid).sum())


def pca_projection(df: pd.DataFrame, columns: list[str], exclude_special: bool = False):
    arr, index, excluded = _prepare(df, columns, exclude_special)
    if arr.shape[1] < 2:
        raise ValueError("La PCA nécessite au moins deux variables.")
    model = PCA(n_components=2, random_state=42)
    coords = model.fit_transform(arr)
    out = pd.DataFrame({"PC1": coords[:, 0], "PC2": coords[:, 1]}, index=index)
    return out, model.explained_variance_ratio_, {"n_analyse": len(out), "lignes_sans_donnee": excluded}


def clustering(df: pd.DataFrame, columns: list[str], n_clusters: int = 3, exclude_special: bool = False):
    arr, index, excluded = _prepare(df, columns, exclude_special)
    if not 2 <= n_clusters <= min(10, len(arr) - 1):
        raise ValueError("Le nombre de groupes doit être compris entre 2 et min(10, n-1).")
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(arr)
    return pd.DataFrame({"cluster": labels.astype(str)}, index=index), {
        "n_analyse": len(index), "lignes_sans_donnee": excluded, "methode": "KMeans"
    }


def anomaly_detection(df: pd.DataFrame, columns: list[str], contamination: float = 0.03,
                      exclude_special: bool = False):
    arr, index, excluded = _prepare(df, columns, exclude_special)
    if not 0.001 <= contamination <= 0.2:
        raise ValueError("contamination doit être entre 0,001 et 0,2.")
    labels = IsolationForest(contamination=contamination, random_state=42).fit_predict(arr)
    out = pd.DataFrame({"statut": np.where(labels == -1, "atypique", "habituel")}, index=index)
    return out, {"n_analyse": len(index), "lignes_sans_donnee": excluded,
                 "n_atypiques": int((labels == -1).sum()), "methode": "IsolationForest"}
