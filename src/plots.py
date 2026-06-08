"""Publication-oriented plotting utilities."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose


def set_plot_style() -> None:
    """Apply a clean style for report figures."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": (11, 5.8),
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.frameon": False,
            "savefig.bbox": "tight",
        }
    )


def save_current(path: Path, dpi: int) -> None:
    """Save the current Matplotlib figure and close it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=dpi)
    plt.close()


def plot_eda(df: pd.DataFrame, figures_dir: Path, dpi: int) -> None:
    """Generate exploratory analysis figures."""
    set_plot_style()

    plt.figure()
    plt.plot(df["date"], df["load"], linewidth=1.0)
    plt.title("Daily Energy Load")
    plt.xlabel("Date")
    plt.ylabel("MWmed")
    save_current(figures_dir / "time_series.png", dpi)

    pivot = df.pivot_table(index=df["date"].dt.dayofyear, columns="year", values="load", aggfunc="mean")
    plt.figure()
    plt.plot(pivot.index, pivot.values, linewidth=0.9)
    plt.title("Yearly Comparison")
    plt.xlabel("Day of year")
    plt.ylabel("MWmed")
    plt.legend(pivot.columns, ncol=4, fontsize=8)
    save_current(figures_dir / "yearly_comparison.png", dpi)

    monthly = df.groupby("month")["load"].mean()
    plt.figure()
    monthly.plot(marker="o")
    plt.title("Monthly Seasonality")
    plt.xlabel("Month")
    plt.ylabel("Average MWmed")
    save_current(figures_dir / "monthly_seasonality.png", dpi)

    weekly = df.groupby("day_of_week")["load"].mean()
    plt.figure()
    weekly.plot(marker="o")
    plt.title("Weekly Seasonality")
    plt.xlabel("Day of week")
    plt.ylabel("Average MWmed")
    save_current(figures_dir / "weekly_seasonality.png", dpi)

    for column, title, file_name in [
        ("day_name", "Load by Day of Week", "boxplot_day_of_week.png"),
        ("month", "Load by Month", "boxplot_month.png"),
        ("is_holiday", "Holiday vs Non-Holiday Load", "boxplot_holiday.png"),
    ]:
        plt.figure()
        df.boxplot(column="load", by=column, grid=False, rot=35)
        plt.title(title)
        plt.suptitle("")
        plt.xlabel(column)
        plt.ylabel("MWmed")
        save_current(figures_dir / file_name, dpi)


def plot_decomposition(y: pd.Series, figures_dir: Path, dpi: int, period: int = 7) -> None:
    """Plot additive seasonal decomposition."""
    set_plot_style()
    decomposition = seasonal_decompose(y, model="additive", period=period, extrapolate_trend="freq")
    figure = decomposition.plot()
    figure.set_size_inches(11, 8)
    figure.suptitle("Seasonal Decomposition", y=1.01)
    save_current(figures_dir / "seasonal_decomposition.png", dpi)


def plot_acf_pacf(y: pd.Series, figures_dir: Path, dpi: int, prefix: str) -> None:
    """Plot ACF and PACF for a series."""
    set_plot_style()
    lags = min(60, max(10, len(y) // 4))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    plot_acf(y.dropna(), lags=lags, ax=axes[0])
    plot_pacf(y.dropna(), lags=lags, ax=axes[1], method="ywm")
    axes[0].set_title(f"{prefix} ACF")
    axes[1].set_title(f"{prefix} PACF")
    save_current(figures_dir / f"{prefix.lower().replace(' ', '_')}_acf_pacf.png", dpi)


def plot_forecasts(
    forecast_df: pd.DataFrame,
    figures_dir: Path,
    dpi: int,
    actual_df: pd.DataFrame | None = None,
) -> None:
    """Plot full-context and zoomed actual-vs-forecast figures per model."""
    set_plot_style()
    forecast_df = forecast_df.copy()
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])
    model_columns = [column for column in forecast_df.columns if column not in {"date", "actual"}]
    forecast_df = forecast_df.dropna(subset=["actual"], how="any")
    forecast_df = forecast_df.loc[forecast_df[model_columns].notna().any(axis=1)]
    start_date = forecast_df["date"].min()
    end_date = forecast_df["date"].max()
    if actual_df is None:
        actual_frame = forecast_df[["date", "actual"]].copy()
    else:
        actual_frame = actual_df[["date", "load"]].rename(columns={"load": "actual"}).copy()
        actual_frame["date"] = pd.to_datetime(actual_frame["date"])

    for column in model_columns:
        model_frame = forecast_df.dropna(subset=[column])
        safe_name = column.lower().replace(" ", "_")

        plt.figure(figsize=(12, 5.5))
        plt.plot(actual_frame["date"], actual_frame["actual"], label="Actual", linewidth=1.1)
        plt.plot(model_frame["date"], model_frame[column], label=f"{column} Forecast", linewidth=1.3, alpha=0.95)
        plt.axvspan(start_date, end_date, color="0.90", alpha=0.35, label="Test period")
        plt.title(f"Actual Series and {column} Forecast - Full Context")
        plt.xlabel("Date")
        plt.ylabel("MWmed")
        plt.legend(fontsize=9)
        save_current(figures_dir / f"forecast_comparison_{safe_name}_full.png", dpi)

        plt.figure(figsize=(12, 5.5))
        plt.plot(model_frame["date"], model_frame["actual"], label="Actual", linewidth=1.5)
        plt.plot(model_frame["date"], model_frame[column], label=f"{column} Forecast", linewidth=1.2, alpha=0.95)
        plt.xlim(start_date, end_date)
        plt.title(f"Actual vs {column} Forecast - Test Period Zoom")
        plt.xlabel("Date")
        plt.ylabel("MWmed")
        plt.legend(fontsize=9)
        save_current(figures_dir / f"forecast_comparison_{safe_name}_zoom.png", dpi)

    errors = forecast_df.drop(columns=["date"]).copy()
    for column in errors.columns:
        if column != "actual":
            errors[column] = errors["actual"] - errors[column]
    errors = errors.drop(columns=["actual"])
    plt.figure(figsize=(10, 5))
    errors.abs().mean().sort_values().plot(kind="bar")
    plt.title("Mean Absolute Forecast Error")
    plt.xlabel("Model")
    plt.ylabel("MAE")
    save_current(figures_dir / "error_comparison.png", dpi)
