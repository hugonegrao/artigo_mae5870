"""End-to-end ONS daily energy load forecasting pipeline."""

from __future__ import annotations

import argparse

import pandas as pd

from .config import ProjectConfig
from .data import prepare_daily_series, read_csv_files, split_train_test
from .diagnostics import residual_diagnostics
from .evaluation import build_forecast_frame, forecast_metrics, naive_forecast, seasonal_naive_forecast
from .features import add_calendar_features, build_exogenous_matrix
from .modeling import (
    fit_best_arima,
    fit_best_sarima,
    fit_garma,
    fit_sarimax_candidates,
    forecast_garma,
    search_arima,
    search_sarima,
)
from .plots import plot_acf_pacf, plot_decomposition, plot_eda, plot_forecasts
from .stationarity import run_stationarity_tests, transformed_series


def descriptive_tables(df: pd.DataFrame, tables_dir) -> None:
    """Export descriptive tables for the article."""
    df[["load"]].describe().T.to_csv(tables_dir / "descriptive_statistics.csv")
    calendar_summary = (
        df.groupby(["is_holiday", "is_weekend"])["load"]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    calendar_summary.to_csv(tables_dir / "calendar_descriptive_statistics.csv", index=False)


def run_pipeline(config: ProjectConfig, max_models: int | None = None, sarimax_top_n: int = 20) -> None:
    """Run data processing, model selection, diagnostics and forecast evaluation."""
    config.ensure_directories()

    raw = read_csv_files(config.input_dir)
    daily, missing_summary = prepare_daily_series(raw, config.target_subsystem)
    daily = add_calendar_features(daily)
    daily.to_csv(config.processed_dir / "daily_energy_load.csv", index=False)
    missing_summary.to_csv(config.tables_dir / "missing_values_summary.csv", index=False)
    descriptive_tables(daily, config.tables_dir)

    train, test = split_train_test(
        daily,
        config.train_start,
        config.train_end,
        config.test_start,
        config.test_end,
    )
    y_train = train.set_index("date")["load"].asfreq("D")
    y_test = test.set_index("date")["load"].asfreq("D")

    plot_eda(daily, config.figures_dir, config.figure_dpi)
    plot_decomposition(y_train, config.figures_dir, config.figure_dpi, config.seasonal_period)
    plot_acf_pacf(y_train, config.figures_dir, config.figure_dpi, "Original Series")
    transformed = transformed_series(y_train, config.seasonal_period)
    plot_acf_pacf(transformed["first_difference"], config.figures_dir, config.figure_dpi, "First Difference")

    stationarity = run_stationarity_tests(y_train, config.seasonal_period)
    stationarity.to_csv(config.tables_dir / "stationarity_test_results.csv", index=False)

    arima_ranking = search_arima(y_train, config.tables_dir)
    arima_result, arima_best_row = fit_best_arima(y_train, arima_ranking, config.models_dir)

    sarima_ranking = search_sarima(
        y_train,
        seasonality=config.seasonal_period,
        tables_dir=config.tables_dir,
        max_models=max_models,
    )
    sarima_result, sarima_best_row = fit_best_sarima(y_train, sarima_ranking, config.models_dir)

    calendar_exog_train = build_exogenous_matrix(train, include_annual_memory=False).set_index(y_train.index)
    calendar_exog_test = build_exogenous_matrix(
        test,
        list(calendar_exog_train.columns),
        include_annual_memory=False,
    ).set_index(y_test.index)
    annual_exog_train = build_exogenous_matrix(train, include_annual_memory=True).set_index(y_train.index)
    annual_exog_test = build_exogenous_matrix(
        test,
        list(annual_exog_train.columns),
        include_annual_memory=True,
    ).set_index(y_test.index)
    if annual_exog_test.isna().any().any():
        missing_columns = annual_exog_test.columns[annual_exog_test.isna().any()].tolist()
        raise ValueError(f"Exogenous test data contains missing values: {missing_columns}")
    annual_exog_train = annual_exog_train.dropna()
    y_train_annual_exog = y_train.reindex(annual_exog_train.index)
    empty_exog_train = pd.DataFrame(index=y_train.index)
    empty_exog_test = pd.DataFrame(index=y_test.index)
    arimax_result, arimax_best_row, _ = fit_sarimax_candidates(
        y_train,
        calendar_exog_train,
        arima_ranking,
        config.tables_dir,
        config.models_dir,
        top_n=len(arima_ranking),
        output_prefix="arimax",
        model_label="ARIMAX",
    )
    garma_result, garma_best_row, garma_columns, garma_lags = fit_garma(
        y_train,
        empty_exog_train,
        config.tables_dir,
        config.models_dir,
        output_prefix="garma",
        model_label="GARMA",
    )
    garmax_result, garmax_best_row, garmax_columns, garmax_lags = fit_garma(
        y_train_annual_exog,
        annual_exog_train,
        config.tables_dir,
        config.models_dir,
        output_prefix="garmax",
        model_label="GARMAX",
    )
    sarimax_result, sarimax_best_row, _ = fit_sarimax_candidates(
        y_train,
        calendar_exog_train,
        sarima_ranking,
        config.tables_dir,
        config.models_dir,
        top_n=sarimax_top_n,
        output_prefix="sarimax",
        model_label="SARIMAX",
    )

    arimax_forecast = arimax_result.get_forecast(steps=len(y_test), exog=calendar_exog_test).predicted_mean.rename("Best ARIMAX")

    forecasts = {
        "Naive": naive_forecast(y_train, y_test),
        "Seasonal Naive": seasonal_naive_forecast(y_train, y_test, config.seasonal_period),
        "Best ARIMA": arima_result.get_forecast(steps=len(y_test)).predicted_mean.rename("Best ARIMA"),
        "Best ARIMAX": arimax_forecast,
        "Best SARIMA": sarima_result.get_forecast(steps=len(y_test)).predicted_mean.rename("Best SARIMA"),
        "Best GARMA": forecast_garma(garma_result, y_train, empty_exog_test, garma_columns, garma_lags).rename("Best GARMA"),
        "Best GARMAX": forecast_garma(garmax_result, y_train, annual_exog_test, garmax_columns, garmax_lags).rename("Best GARMAX"),
        "Best SARIMAX": sarimax_result.get_forecast(steps=len(y_test), exog=calendar_exog_test).predicted_mean.rename("Best SARIMAX"),
    }

    accuracy = pd.DataFrame(
        [forecast_metrics(y_test, prediction, name) for name, prediction in forecasts.items()]
    ).sort_values("RMSE")
    accuracy.to_csv(config.tables_dir / "forecast_accuracy_table.csv", index=False)

    model_comparison = accuracy.merge(
        pd.DataFrame(
            [
                {
                    "model": "Best ARIMA",
                    "order": arima_best_row["order"],
                    "seasonal_order": arima_best_row["seasonal_order"],
                    "AIC": arima_best_row["AIC"],
                    "BIC": arima_best_row["BIC"],
                },
                {
                    "model": "Best ARIMAX",
                    "order": arimax_best_row["order"],
                    "seasonal_order": arimax_best_row["seasonal_order"],
                    "AIC": arimax_best_row["AIC"],
                    "BIC": arimax_best_row["BIC"],
                },
                {
                    "model": "Best SARIMA",
                    "order": sarima_best_row["order"],
                    "seasonal_order": sarima_best_row["seasonal_order"],
                    "AIC": sarima_best_row["AIC"],
                    "BIC": sarima_best_row["BIC"],
                },
                {
                    "model": "Best SARIMAX",
                    "order": sarimax_best_row["order"],
                    "seasonal_order": sarimax_best_row["seasonal_order"],
                    "AIC": sarimax_best_row["AIC"],
                    "BIC": sarimax_best_row["BIC"],
                },
                {
                    "model": "Best GARMA",
                    "order": f"AR lags {garma_best_row['ar_lags']}",
                    "seasonal_order": "",
                    "AIC": garma_best_row["AIC"],
                    "BIC": garma_best_row["BIC"],
                },
                {
                    "model": "Best GARMAX",
                    "order": f"AR lags {garmax_best_row['ar_lags']}",
                    "seasonal_order": "",
                    "AIC": garmax_best_row["AIC"],
                    "BIC": garmax_best_row["BIC"],
                },
            ]
        ),
        on="model",
        how="left",
    )
    model_comparison.to_csv(config.tables_dir / "model_comparison_table.csv", index=False)

    forecast_frame = build_forecast_frame(test["date"], y_test, forecasts)
    forecast_frame["date"] = pd.to_datetime(forecast_frame["date"])
    if forecast_frame["date"].min() < pd.Timestamp(config.test_start) or forecast_frame["date"].max() > pd.Timestamp(config.test_end):
        raise ValueError("Forecast output contains dates outside the configured test period.")
    forecast_frame.to_csv(config.tables_dir / "forecast_values.csv", index=False)
    plot_forecasts(forecast_frame, config.figures_dir, config.figure_dpi, actual_df=daily)

    lb_arima = residual_diagnostics(arima_result, "Best ARIMA", config.figures_dir, config.tables_dir, config.figure_dpi)
    lb_arimax = residual_diagnostics(arimax_result, "Best ARIMAX", config.figures_dir, config.tables_dir, config.figure_dpi)
    lb_sarima = residual_diagnostics(sarima_result, "Best SARIMA", config.figures_dir, config.tables_dir, config.figure_dpi)
    lb_sarimax = residual_diagnostics(sarimax_result, "Best SARIMAX", config.figures_dir, config.tables_dir, config.figure_dpi)
    lb_garma = residual_diagnostics(garma_result, "Best GARMA", config.figures_dir, config.tables_dir, config.figure_dpi)
    lb_garmax = residual_diagnostics(garmax_result, "Best GARMAX", config.figures_dir, config.tables_dir, config.figure_dpi)
    pd.concat([lb_arima, lb_arimax, lb_sarima, lb_garma, lb_garmax, lb_sarimax], ignore_index=True).to_csv(
        config.tables_dir / "ljung_box_results.csv",
        index=False,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="ONS daily energy load forecasting pipeline.")
    parser.add_argument("--subsystem", default="SIN Total", help="Subsystem name or 'SIN Total' to aggregate all subsystems.")
    parser.add_argument("--max-models", type=int, default=None, help="Optional cap for SARIMA candidates, useful for smoke tests.")
    parser.add_argument("--sarimax-top-n", type=int, default=20, help="Number of top SARIMA structures to evaluate with exogenous variables.")
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    config = ProjectConfig(target_subsystem=args.subsystem)
    run_pipeline(config, max_models=args.max_models, sarimax_top_n=args.sarimax_top_n)


if __name__ == "__main__":
    main()
