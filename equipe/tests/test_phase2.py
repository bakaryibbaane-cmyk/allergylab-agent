import pandas as pd
import pytest
from equipe.analyse.phase2 import descriptive_statistics, compare_groups, correlation_matrix, data_quality


def sample():
    return pd.DataFrame({
        "Chip_Type": ["ALEX", "ALEX", "ISAC_V1", "ISAC_V1"],
        "dose": [1.0, -1.0, 3.0, None],
        "autre": [2.0, 4.0, 6.0, 8.0],
    })


def test_stats_keep_and_flag_special_values():
    result = descriptive_statistics(sample(), "dose")
    assert result["n_renseignes"] == 3
    assert result["codes_speciaux"]["-1"] == 1
    assert result["codes_speciaux"]["9"] == 0
    assert result["moyenne"] == pytest.approx(1.0)


def test_compare_groups():
    result = compare_groups(sample(), "dose")
    assert set(result["groupe"]) == {"ALEX", "ISAC_V1"}
    assert list(result["n"]) == [2, 1]


def test_correlation():
    result = correlation_matrix(sample(), ["dose", "autre"])
    assert result.shape == (2, 2)


def test_quality():
    result = data_quality(sample())
    assert "completude_pct" in result.columns
