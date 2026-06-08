"""Stationarity tests and transformation diagnostics."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss


def transformed_series(y: pd.Series, seasonal_period: int = 7) -> dict[str, pd.Series]:
    """Create candidate transformed series for stationarity assessment."""
    positive = y[y > 0]
    log_y = np.log(positive).reindex(y.index)
    return {
        "original": y.dropna(),
        "log": log_y.dropna(),
        "first_difference": y.diff().dropna(),
        "seasonal_difference": y.diff(seasonal_period).dropna(),
        "log_first_difference": log_y.diff().dropna(),
        "log_seasonal_difference": log_y.diff(seasonal_period).dropna(),
    }


def run_stationarity_tests(y: pd.Series, seasonal_period: int = 7) -> pd.DataFrame:
    """Run ADF and KPSS tests on original and transformed series."""
    rows = []
    for name, series in transformed_series(y, seasonal_period).items():
        series = series.replace([np.inf, -np.inf], np.nan).dropna()
        if len(series) < 20:
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                adf_stat, adf_pvalue, *_ = adfuller(series, autolag="AIC")
            except Exception:
                adf_stat, adf_pvalue = np.nan, np.nan
            try:
                kpss_stat, kpss_pvalue, *_ = kpss(series, regression="c", nlags="auto")
            except Exception:
                kpss_stat, kpss_pvalue = np.nan, np.nan
        rows.append(
            {
                "transformation": name,
                "n_observations": len(series),
                "adf_statistic": adf_stat,
                "adf_pvalue": adf_pvalue,
                "kpss_statistic": kpss_stat,
                "kpss_pvalue": kpss_pvalue,
                "adf_stationary_at_5pct": bool(adf_pvalue < 0.05) if pd.notna(adf_pvalue) else False,
                "kpss_stationary_at_5pct": bool(kpss_pvalue > 0.05) if pd.notna(kpss_pvalue) else False,
            }
        )
    return pd.DataFrame(rows)
