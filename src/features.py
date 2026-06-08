"""Calendar feature engineering."""

from __future__ import annotations

import holidays
import numpy as np
import pandas as pd


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create calendar features compatible with daily energy load data."""
    result = df.copy()
    dates = pd.to_datetime(result["date"])
    years = range(int(dates.dt.year.min()), int(dates.dt.year.max()) + 1)
    br_holidays = holidays.country_holidays("BR", years=years)
    holiday_dates = set(pd.to_datetime(list(br_holidays.keys())))

    result["day_of_week"] = dates.dt.dayofweek
    result["day_name"] = dates.dt.day_name()
    result["month"] = dates.dt.month
    result["month_name"] = dates.dt.month_name()
    result["year"] = dates.dt.year
    result["quarter"] = dates.dt.quarter
    result["day_of_year"] = dates.dt.dayofyear
    result["is_weekend"] = result["day_of_week"].isin([5, 6]).astype(int)
    result["is_month_start"] = dates.dt.is_month_start.astype(int)
    result["is_month_end"] = dates.dt.is_month_end.astype(int)
    result["is_holiday"] = dates.isin(holiday_dates).astype(int)
    result["holiday_name"] = [br_holidays.get(date.date(), "") for date in dates]
    result["is_holiday_eve"] = (dates + pd.Timedelta(days=1)).isin(holiday_dates).astype(int)
    result["is_post_holiday"] = (dates - pd.Timedelta(days=1)).isin(holiday_dates).astype(int)
    for harmonic in (1, 2, 3):
        angle = 2 * np.pi * harmonic * result["day_of_year"] / 365.25
        result[f"annual_sin_{harmonic}"] = np.sin(angle)
        result[f"annual_cos_{harmonic}"] = np.cos(angle)
    if "load" in result.columns:
        load_by_date = result.set_index("date")["load"]
        rolling_7_by_date = load_by_date.rolling(7, min_periods=1).mean()
        rolling_30_by_date = load_by_date.rolling(30, min_periods=1).mean()
        previous_year_dates = dates - pd.DateOffset(years=1)
        result["previous_year_load"] = previous_year_dates.map(load_by_date)
        result["previous_year_rolling_7"] = previous_year_dates.map(rolling_7_by_date)
        result["previous_year_rolling_30"] = previous_year_dates.map(rolling_30_by_date)
    return result


def build_exogenous_matrix(
    df: pd.DataFrame,
    reference_columns: list[str] | None = None,
    include_annual_memory: bool = False,
) -> pd.DataFrame:
    """Build a numeric exogenous matrix for SARIMAX models."""
    columns = [
        "day_of_week",
        "month",
        "quarter",
        "is_weekend",
        "is_month_start",
        "is_month_end",
        "is_holiday",
        "is_holiday_eve",
        "is_post_holiday",
        "annual_sin_1",
        "annual_cos_1",
        "annual_sin_2",
        "annual_cos_2",
        "annual_sin_3",
        "annual_cos_3",
    ]
    if include_annual_memory:
        columns.extend(
            [
                "previous_year_load",
                "previous_year_rolling_7",
                "previous_year_rolling_30",
            ]
        )
    base = df[columns].copy()
    base["day_of_week"] = base["day_of_week"].astype("category")
    base["month"] = base["month"].astype("category")
    base["quarter"] = base["quarter"].astype("category")
    exog = pd.get_dummies(base, columns=["day_of_week", "month", "quarter"], drop_first=True)
    exog = exog.astype(float)
    if reference_columns is not None:
        exog = exog.reindex(columns=reference_columns, fill_value=0.0)
    return exog
