"""Fonctions analytiques déterministes pour AllergyLab Phase 2.

Aucun appel IA. Les DataFrames reçus ne sont jamais modifiés.
Les valeurs -1 et 9 sont conservées par défaut et signalées ; leur sens doit
être confirmé colonne par colonne avant toute exclusion/interprétation.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

SPECIAL_CODES = (-1, 9)
GROUP_COLUMN = "Chip_Type"


def _numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise KeyError(f"Colonne absente : {column}")
    values = pd.to_numeric(df[column], errors="coerce")
    if values.notna().sum() == 0:
        raise ValueError(f"La colonne {column!r} ne contient aucune valeur numérique exploitable.")
    return values


def special_code_counts(values: pd.Series) -> dict:
    numeric = pd.to_numeric(values, errors="coerce")
    return {"-1": int((numeric == -1).sum()), "9": int((numeric == 9).sum())}


def descriptive_statistics(df: pd.DataFrame, column: str) -> dict:
    """Statistiques usuelles, sans recodage ni exclusion implicite des sentinelles."""
    s = _numeric_series(df, column)
    clean = s.dropna()
    if not np.isfinite(clean).all():
        clean = clean[np.isfinite(clean)]
    if clean.empty:
        raise ValueError("Aucune valeur finie.")
    q = clean.quantile([0.25, 0.5, 0.75])
    return {
        "variable": column,
        "n_total": int(len(s)),
        "n_renseignes": int(s.notna().sum()),
        "n_absents": int(s.isna().sum()),
        "moyenne": float(clean.mean()),
        "mediane": float(clean.median()),
        "ecart_type": float(clean.std(ddof=1)) if len(clean) > 1 else None,
        "minimum": float(clean.min()),
        "q1": float(q.loc[0.25]),
        "q2": float(q.loc[0.50]),
        "q3": float(q.loc[0.75]),
        "maximum": float(clean.max()),
        "codes_speciaux": special_code_counts(clean),
        "avertissement": "Les codes -1 et 9 restent inclus et ne sont pas interprétés.",
    }


def distribution(df: pd.DataFrame, column: str, bins: int = 30) -> pd.DataFrame:
    s = _numeric_series(df, column).dropna()
    return pd.DataFrame({"valeur": s})


def compare_groups(df: pd.DataFrame, column: str, group_column: str = GROUP_COLUMN) -> pd.DataFrame:
    """Résumé descriptif par puce. Ne conclut pas à une différence significative."""
    if group_column not in df.columns:
        raise KeyError(f"Colonne de groupe absente : {group_column}")
    s = _numeric_series(df, column)
    work = pd.DataFrame({"groupe": df[group_column], "valeur": s})
    result = work.groupby("groupe", dropna=False)["valeur"].agg(
        n="count", moyenne="mean", mediane="median", ecart_type="std", minimum="min", maximum="max"
    ).reset_index()
    result["codes_-1"] = [
        int(((work.loc[work["groupe"] == g, "valeur"]) == -1).sum()) for g in result["groupe"]
    ]
    result["codes_9"] = [
        int(((work.loc[work["groupe"] == g, "valeur"]) == 9).sum()) for g in result["groupe"]
    ]
    return result


def correlation_matrix(df: pd.DataFrame, columns: list[str], method: str = "spearman") -> pd.DataFrame:
    if len(columns) < 2:
        raise ValueError("Sélectionner au moins deux variables.")
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Colonnes absentes : {missing}")
    numeric = df[columns].apply(pd.to_numeric, errors="coerce")
    if method not in {"pearson", "spearman", "kendall"}:
        raise ValueError("Méthode attendue : pearson, spearman ou kendall.")
    return numeric.corr(method=method, min_periods=3)


def data_quality(df: pd.DataFrame, dictionary: pd.DataFrame | None = None) -> pd.DataFrame:
    """Taux de renseignement global ou, si fourni, seulement pour les puces mesurantes."""
    rows = []
    for col in df.columns:
        s = df[col]
        n = len(s)
        numeric = pd.to_numeric(s, errors="coerce")
        row = {
            "colonne": col,
            "n_lignes": n,
            "renseignes": int(s.notna().sum()),
            "vides": int(s.isna().sum()),
            "completude_pct": round(100 * s.notna().mean(), 2) if n else 0.0,
            "code_-1": int((numeric == -1).sum()) if numeric.notna().any() else 0,
            "code_9": int((numeric == 9).sum()) if numeric.notna().any() else 0,
        }
        if dictionary is not None and "colonne" in dictionary.columns:
            match = dictionary[dictionary["colonne"] == col]
            if not match.empty:
                row["bloc"] = match.iloc[0].get("bloc", "")
                row["puces_mesurantes"] = ", ".join(
                    c.removeprefix("puce_") for c in dictionary.columns
                    if c.startswith("puce_") and bool(match.iloc[0][c])
                )
        rows.append(row)
    return pd.DataFrame(rows).sort_values("completude_pct", ascending=True)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) or pd.to_numeric(df[c], errors="coerce").notna().any()
    ]
