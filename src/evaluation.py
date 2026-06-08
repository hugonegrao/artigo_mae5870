"""Forecast evaluation metrics and baseline models."""

from __future__ import annotations

import numpy as np
import pandas as pd


def naive_forecast(train: pd.Series, test: pd.Series) -> pd.Series:
    """Generate a recursive naive forecast without using test observations."""
    last_value = float(train.dropna().iloc[-1])
    return pd.Series([last_value] * len(test), index=test.index, name="naive")


def seasonal_naive_forecast(train: pd.Series, test: pd.Series, seasonality: int = 7) -> pd.Series:
    """Generate a recursive seasonal naive forecast without using test observations."""
    history = [float(value) for value in train.dropna().values]
    forecasts = []
    for _ in range(len(test)):
        prediction = history[-seasonality]
        forecasts.append(prediction)
        history.append(prediction)
    return pd.Series(forecasts, index=test.index, name="seasonal_naive")


def forecast_metrics(y_true: pd.Series, y_pred: pd.Series, model_name: str) -> dict[str, float | str]:
    """Calculate MAE, RMSE and MAPE for a forecast."""
    aligned = pd.concat([y_true.rename("actual"), y_pred.rename("predicted")], axis=1).dropna()
    error = aligned["actual"] - aligned["predicted"]
    non_zero = aligned["actual"] != 0
    mape = np.nan
    if non_zero.any():
        mape = (np.abs(error[non_zero] / aligned.loc[non_zero, "actual"]).mean()) * 100
    return {
        "model": model_name,
        "MAE": float(np.abs(error).mean()),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "MAPE": float(mape),
    }


def build_forecast_frame(dates: pd.Series, actual: pd.Series, forecasts: dict[str, pd.Series]) -> pd.DataFrame:
    """Combine actual values and forecasts in a single table."""
    frame = pd.DataFrame({"date": dates.values, "actual": actual.values}, index=actual.index)
    for name, values in forecasts.items():
        frame[name] = values.reindex(actual.index).values
    return frame.reset_index(drop=True)
