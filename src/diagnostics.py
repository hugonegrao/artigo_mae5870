"""Residual diagnostics for fitted models."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.gofplots import qqplot
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.stats.diagnostic import acorr_ljungbox

from .plots import save_current, set_plot_style


def residual_diagnostics(result, model_name: str, figures_dir: Path, tables_dir: Path, dpi: int) -> pd.DataFrame:
    """Generate visual and statistical residual diagnostics."""
    set_plot_style()
    if hasattr(result, "resid"):
        residuals = pd.Series(result.resid).dropna()
    elif hasattr(result, "resid_pearson"):
        residuals = pd.Series(result.resid_pearson).dropna()
    elif hasattr(result, "resid_deviance"):
        residuals = pd.Series(result.resid_deviance).dropna()
    else:
        raise AttributeError(f"Model result for {model_name} does not expose residuals.")
    safe_name = model_name.lower().replace(" ", "_")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].plot(residuals.index, residuals.values, linewidth=0.8)
    axes[0, 0].set_title(f"{model_name} Residuals")
    axes[0, 1].hist(residuals.values, bins=30)
    axes[0, 1].set_title("Residual Histogram")
    qqplot(residuals, line="s", ax=axes[1, 0])
    axes[1, 0].set_title("Residual Q-Q Plot")
    plot_acf(residuals, lags=min(60, max(10, len(residuals) // 4)), ax=axes[1, 1])
    axes[1, 1].set_title("Residual ACF")
    save_current(figures_dir / f"{safe_name}_residual_diagnostics.png", dpi)

    lags = [7, 14, 21, 28]
    table = acorr_ljungbox(residuals, lags=lags, return_df=True).reset_index()
    table = table.rename(columns={"index": "lag", "lb_stat": "ljung_box_statistic", "lb_pvalue": "pvalue"})
    table.insert(0, "model", model_name)
    table.to_csv(tables_dir / f"{safe_name}_ljung_box.csv", index=False)
    return table
