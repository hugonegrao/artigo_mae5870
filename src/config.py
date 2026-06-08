"""Project configuration."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    """Central configuration for the forecasting pipeline."""

    root_dir: Path = Path(__file__).resolve().parents[1]
    input_dir: Path = root_dir / "data" / "input"
    processed_dir: Path = root_dir / "data" / "processed"
    figures_dir: Path = root_dir / "reports" / "figures"
    tables_dir: Path = root_dir / "reports" / "tables"
    models_dir: Path = root_dir / "models"
    target_subsystem: str = "SIN Total"
    train_start: str = "2018-01-01"
    train_end: str = "2024-12-31"
    test_start: str = "2025-01-01"
    test_end: str = "2025-12-31"
    seasonal_period: int = 7
    figure_dpi: int = 160

    def ensure_directories(self) -> None:
        """Create output directories if needed."""
        for path in [
            self.processed_dir,
            self.figures_dir,
            self.tables_dir,
            self.models_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
