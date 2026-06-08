"""SARIMA and SARIMAX model fitting."""

from __future__ import annotations

import itertools
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.families import Gamma
from statsmodels.genmod.families.links import Log
from statsmodels.tsa.statespace.sarimax import SARIMAX


def sarima_grid(seasonality: int = 7) -> list[tuple[tuple[int, int, int], tuple[int, int, int, int]]]:
    """Build the requested SARIMA search grid."""
    orders = list(itertools.product([0, 1, 2], [0, 1], [0, 1, 2]))
    seasonal_orders = list(itertools.product([0, 1], [0, 1], [0, 1]))
    return [(order, seasonal + (seasonality,)) for order in orders for seasonal in seasonal_orders]


def arima_grid() -> list[tuple[int, int, int]]:
    """Build the requested non-seasonal ARIMA search grid."""
    return list(itertools.product([0, 1, 2], [0, 1], [0, 1, 2]))


def fit_sarimax(
    y: pd.Series,
    order: tuple[int, int, int],
    seasonal_order: tuple[int, int, int, int],
    exog: pd.DataFrame | None = None,
):
    """Fit a SARIMAX model with robust defaults."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = SARIMAX(
            y,
            exog=exog,
            order=order,
            seasonal_order=seasonal_order,
            trend="c",
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        return model.fit(disp=False, maxiter=200)


def search_sarima(
    y_train: pd.Series,
    seasonality: int,
    tables_dir: Path,
    max_models: int | None = None,
) -> pd.DataFrame:
    """Fit SARIMA candidates and export a ranking table."""
    rows = []
    grid = sarima_grid(seasonality)
    if max_models is not None:
        grid = grid[:max_models]

    for order, seasonal_order in grid:
        row = {
            "order": str(order),
            "seasonal_order": str(seasonal_order),
            "log_likelihood": np.nan,
            "AIC": np.nan,
            "BIC": np.nan,
            "converged": False,
            "error": "",
        }
        try:
            result = fit_sarimax(y_train, order, seasonal_order)
            row.update(
                {
                    "log_likelihood": float(result.llf),
                    "AIC": float(result.aic),
                    "BIC": float(result.bic),
                    "converged": bool(result.mle_retvals.get("converged", False)),
                }
            )
        except Exception as exc:
            row["error"] = str(exc)[:250]
        rows.append(row)

    ranking = pd.DataFrame(rows).sort_values(["AIC", "BIC"], na_position="last")
    ranking.to_csv(tables_dir / "sarima_search_results.csv", index=False)
    ranking.sort_values(["BIC", "AIC"], na_position="last").to_csv(
        tables_dir / "sarima_search_results_by_bic.csv", index=False
    )
    return ranking


def search_arima(y_train: pd.Series, tables_dir: Path) -> pd.DataFrame:
    """Fit non-seasonal ARIMA candidates and export a ranking table."""
    rows = []
    for order in arima_grid():
        row = {
            "order": str(order),
            "seasonal_order": "(0, 0, 0, 0)",
            "log_likelihood": np.nan,
            "AIC": np.nan,
            "BIC": np.nan,
            "converged": False,
            "error": "",
        }
        try:
            result = fit_sarimax(y_train, order, (0, 0, 0, 0))
            row.update(
                {
                    "log_likelihood": float(result.llf),
                    "AIC": float(result.aic),
                    "BIC": float(result.bic),
                    "converged": bool(result.mle_retvals.get("converged", False)),
                }
            )
        except Exception as exc:
            row["error"] = str(exc)[:250]
        rows.append(row)

    ranking = pd.DataFrame(rows).sort_values(["AIC", "BIC"], na_position="last")
    ranking.to_csv(tables_dir / "arima_search_results.csv", index=False)
    ranking.sort_values(["BIC", "AIC"], na_position="last").to_csv(
        tables_dir / "arima_search_results_by_bic.csv",
        index=False,
    )
    return ranking


def parse_order(value: str) -> tuple[int, ...]:
    """Parse tuple strings produced in the search table."""
    cleaned = value.strip().strip("()")
    return tuple(int(part.strip()) for part in cleaned.split(",") if part.strip())


def fit_best_sarima(y_train: pd.Series, ranking: pd.DataFrame, models_dir: Path):
    """Fit the best SARIMA candidate according to AIC."""
    best = ranking.dropna(subset=["AIC"]).iloc[0]
    result = fit_sarimax(y_train, parse_order(best["order"]), parse_order(best["seasonal_order"]))
    with open(models_dir / "best_sarima.pkl", "wb") as file:
        pickle.dump(result, file)
    return result, best


def fit_best_arima(y_train: pd.Series, ranking: pd.DataFrame, models_dir: Path):
    """Fit the best non-seasonal ARIMA candidate according to AIC."""
    best = ranking.dropna(subset=["AIC"]).iloc[0]
    result = fit_sarimax(y_train, parse_order(best["order"]), (0, 0, 0, 0))
    with open(models_dir / "best_arima.pkl", "wb") as file:
        pickle.dump(result, file)
    return result, best


def fit_sarimax_candidates(
    y_train: pd.Series,
    exog_train: pd.DataFrame,
    ranking: pd.DataFrame,
    tables_dir: Path,
    models_dir: Path,
    top_n: int = 5,
    output_prefix: str = "sarimax",
    model_label: str = "SARIMAX",
):
    """Fit SARIMAX-family models using the strongest structures."""
    rows = []
    fitted = []
    candidates = ranking.dropna(subset=["AIC"]).head(top_n)
    for _, candidate in candidates.iterrows():
        order = parse_order(candidate["order"])
        seasonal_order = parse_order(candidate["seasonal_order"])
        row = {
            "order": str(order),
            "seasonal_order": str(seasonal_order),
            "log_likelihood": np.nan,
            "AIC": np.nan,
            "BIC": np.nan,
            "converged": False,
            "error": "",
        }
        try:
            result = fit_sarimax(y_train, order, seasonal_order, exog_train)
            row.update(
                {
                    "log_likelihood": float(result.llf),
                    "AIC": float(result.aic),
                    "BIC": float(result.bic),
                    "converged": bool(result.mle_retvals.get("converged", False)),
                }
            )
            fitted.append((result, row))
        except Exception as exc:
            row["error"] = str(exc)[:250]
        rows.append(row)

    table = pd.DataFrame(rows).sort_values(["AIC", "BIC"], na_position="last")
    table.to_csv(tables_dir / f"{output_prefix}_candidate_results.csv", index=False)
    if not fitted:
        raise RuntimeError(f"No {model_label} candidate converged successfully.")
    best_row = table.dropna(subset=["AIC"]).iloc[0]
    best_result = next(result for result, row in fitted if row["order"] == best_row["order"] and row["seasonal_order"] == best_row["seasonal_order"])
    with open(models_dir / f"best_{output_prefix}.pkl", "wb") as file:
        pickle.dump(best_result, file)
    coefficients = pd.DataFrame(
        {
            "term": best_result.params.index,
            "estimate": best_result.params.values,
            "pvalue": best_result.pvalues.values,
        }
    ).sort_values("pvalue")
    coefficients.to_csv(tables_dir / f"{output_prefix}_coefficients.csv", index=False)
    return best_result, best_row, table


def make_garma_training_data(
    y_train: pd.Series,
    exog_train: pd.DataFrame,
    ar_lags: tuple[int, ...] = (1, 7),
) -> tuple[pd.Series, pd.DataFrame]:
    """Create a Gamma autoregressive design matrix for GARMA estimation."""
    frame = pd.DataFrame({"load": y_train})
    for lag in ar_lags:
        frame[f"log_load_lag_{lag}"] = np.log(y_train.shift(lag).clip(lower=1e-6))
    frame = frame.join(exog_train)
    frame = frame.dropna()
    y = frame["load"].clip(lower=1e-6)
    x = sm.add_constant(frame.drop(columns=["load"]), has_constant="add")
    return y, x


def fit_garma(
    y_train: pd.Series,
    exog_train: pd.DataFrame,
    tables_dir: Path,
    models_dir: Path,
    ar_lags: tuple[int, ...] = (1, 7),
    output_prefix: str = "garma",
    model_label: str = "GARMA",
):
    """Fit a GARMA-style Gamma model with log link and autoregressive terms."""
    y, x = make_garma_training_data(y_train, exog_train, ar_lags)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = sm.GLM(y, x, family=Gamma(link=Log())).fit(maxiter=200)

    with open(models_dir / f"best_{output_prefix}.pkl", "wb") as file:
        pickle.dump(result, file)

    coefficients = pd.DataFrame(
        {
            "term": result.params.index,
            "estimate": result.params.values,
            "pvalue": result.pvalues.values,
        }
    ).sort_values("pvalue")
    coefficients.to_csv(tables_dir / f"{output_prefix}_coefficients.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "model": model_label,
                "family": "Gamma",
                "link": "log",
                "ar_lags": str(ar_lags),
                "uses_calendar_exog": bool(len(exog_train.columns) > 0),
                "log_likelihood": float(result.llf),
                "AIC": float(result.aic),
                "BIC": float(result.bic_llf),
            }
        ]
    )
    summary.to_csv(tables_dir / f"{output_prefix}_model_summary.csv", index=False)
    return result, summary.iloc[0], list(x.columns), ar_lags


def forecast_garma(
    result,
    y_train: pd.Series,
    exog_test: pd.DataFrame,
    feature_columns: list[str],
    ar_lags: tuple[int, ...] = (1, 7),
) -> pd.Series:
    """Generate recursive GARMA forecasts without using future actual values."""
    history = [float(value) for value in y_train.dropna().values]
    forecasts = []

    for date, exog_row in exog_test.iterrows():
        row = {}
        for lag in ar_lags:
            row[f"log_load_lag_{lag}"] = np.log(max(history[-lag], 1e-6))
        row.update(exog_row.to_dict())
        x_next = pd.DataFrame([row], index=[date])
        x_next = sm.add_constant(x_next, has_constant="add")
        x_next = x_next.reindex(columns=feature_columns, fill_value=0.0)
        prediction = float(result.predict(x_next).iloc[0])
        forecasts.append(prediction)
        history.append(max(prediction, 1e-6))

    return pd.Series(forecasts, index=exog_test.index, name="Best GARMA")


def monthly_bias_adjusted_forecast(
    base_forecast: pd.Series,
    y_train: pd.Series,
    exog_train: pd.DataFrame,
    exog_test: pd.DataFrame,
    order: tuple[int, int, int],
    seasonal_order: tuple[int, int, int, int],
    validation_year: int,
    tables_dir: Path,
    output_name: str,
) -> pd.Series:
    """Adjust forecasts using monthly residual bias estimated on a validation year."""
    validation_mask = y_train.index.year == validation_year
    calibration_mask = y_train.index.year < validation_year
    y_calibration = y_train.loc[calibration_mask]
    y_validation = y_train.loc[validation_mask]
    exog_calibration = exog_train.loc[y_calibration.index]
    exog_validation = exog_train.loc[y_validation.index]

    validation_result = fit_sarimax(y_calibration, order, seasonal_order, exog_calibration)
    validation_forecast = validation_result.get_forecast(
        steps=len(y_validation),
        exog=exog_validation,
    ).predicted_mean
    residuals = y_validation - validation_forecast
    corrections = residuals.groupby(residuals.index.month).mean()
    correction_table = pd.DataFrame(
        {
            "month": corrections.index,
            "monthly_bias_correction": corrections.values,
        }
    )
    correction_table.to_csv(tables_dir / f"{output_name}_monthly_bias_corrections.csv", index=False)

    test_corrections = pd.Series(
        exog_test.index.month,
        index=exog_test.index,
    ).map(corrections).fillna(0.0)
    adjusted = base_forecast.reindex(exog_test.index) + test_corrections
    return adjusted.rename(f"{output_name} Calibrated")
