"""Data ingestion and preparation utilities."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def standardize_column_name(name: str) -> str:
    """Convert a source column name to a predictable snake_case name."""
    normalized = unicodedata.normalize("NFKD", str(name))
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^0-9a-zA-Z]+", "_", ascii_name.strip().lower())
    return re.sub(r"_+", "_", ascii_name).strip("_")


def read_csv_files(input_dir: Path) -> pd.DataFrame:
    """Read and concatenate all CSV files found in the input directory."""
    files = sorted(input_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    frames = []
    for file_path in files:
        frame = pd.read_csv(file_path, sep=None, engine="python", decimal=".")
        frame.columns = [standardize_column_name(col) for col in frame.columns]
        frame["source_file"] = file_path.name
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def identify_date_column(df: pd.DataFrame) -> str:
    """Identify the most likely date column."""
    preferred_terms = ("date", "data", "instante", "din")
    candidates = [col for col in df.columns if any(term in col for term in preferred_terms)]
    candidates = candidates or list(df.columns)

    best_column = None
    best_score = -1
    for column in candidates:
        parsed = pd.to_datetime(df[column], errors="coerce", dayfirst=False)
        score = parsed.notna().sum()
        if score > best_score:
            best_column = column
            best_score = score

    if best_column is None or best_score == 0:
        raise ValueError("Could not identify a valid date column.")
    return best_column


def identify_load_column(df: pd.DataFrame, date_column: str) -> str:
    """Identify the most likely energy load column."""
    terms = ("carga", "load", "energia", "energy", "mwmed", "mwh")
    numeric_scores = {}
    for column in df.columns:
        if column == date_column or column == "source_file":
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        if values.notna().sum() == 0:
            continue
        name_bonus = 10 if any(term in column for term in terms) else 0
        numeric_scores[column] = values.notna().sum() + name_bonus

    if not numeric_scores:
        raise ValueError("Could not identify a numeric energy load column.")
    return max(numeric_scores, key=numeric_scores.get)


def detect_subsystem_column(df: pd.DataFrame) -> str | None:
    """Return a likely subsystem column, if present."""
    priority = ["nom_subsistema", "subsystem", "subsistema", "id_subsistema"]
    for column in priority:
        if column in df.columns:
            return column
    for column in df.columns:
        if "sub" in column and df[column].nunique(dropna=True) < 50:
            return column
    return None


def prepare_daily_series(raw: pd.DataFrame, target_subsystem: str = "SIN Total") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare a continuous daily energy load series.

    If `target_subsystem` is `SIN Total`, all subsystem values are summed by date.
    Otherwise, the function filters the detected subsystem column.
    """
    date_column = identify_date_column(raw)
    load_column = identify_load_column(raw, date_column)
    subsystem_column = detect_subsystem_column(raw)

    df = raw.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df[load_column] = pd.to_numeric(df[load_column], errors="coerce")
    df = df.dropna(subset=[date_column, load_column])

    metadata = {
        "date_column": date_column,
        "load_column": load_column,
        "subsystem_column": subsystem_column or "",
        "target_subsystem": target_subsystem,
        "raw_rows": len(raw),
        "valid_rows": len(df),
    }

    subsystem_key = target_subsystem.strip().lower()
    total_aliases = {"sin total", "total", "sin", "sistema interligado nacional"}
    if subsystem_column and subsystem_key not in total_aliases:
        available = sorted(df[subsystem_column].dropna().astype(str).unique())
        mask = df[subsystem_column].astype(str).str.casefold() == target_subsystem.casefold()
        if not mask.any():
            raise ValueError(
                f"Subsystem '{target_subsystem}' not found. Available values: {available}"
            )
        df = df.loc[mask].copy()
        aggregation = "mean"
    else:
        aggregation = "sum"

    daily = (
        df.groupby(date_column, as_index=False)[load_column]
        .agg(aggregation)
        .rename(columns={date_column: "date", load_column: "load"})
        .sort_values("date")
    )

    full_index = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = daily.set_index("date").reindex(full_index)
    daily.index.name = "date"
    daily["missing_original"] = daily["load"].isna()
    daily["load"] = daily["load"].interpolate(method="time").ffill().bfill()
    daily = daily.reset_index()
    daily["subsystem"] = target_subsystem

    missing_summary = pd.DataFrame(
        {
            "metric": [
                "raw_rows",
                "valid_rows",
                "start_date",
                "end_date",
                "missing_days_before_imputation",
                "aggregation",
            ],
            "value": [
                metadata["raw_rows"],
                metadata["valid_rows"],
                daily["date"].min().date(),
                daily["date"].max().date(),
                int(daily["missing_original"].sum()),
                aggregation,
            ],
        }
    )
    return daily, missing_summary


def split_train_test(df: pd.DataFrame, train_start: str, train_end: str, test_start: str, test_end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a daily series using fixed temporal boundaries."""
    train = df[(df["date"] >= train_start) & (df["date"] <= train_end)].copy()
    test = df[(df["date"] >= test_start) & (df["date"] <= test_end)].copy()
    if train.empty or test.empty:
        raise ValueError("Train or test split is empty. Check date boundaries and input data.")
    return train, test
