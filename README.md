# ONS Daily Energy Load Forecasting

Academic time series forecasting pipeline for Brazilian ONS daily energy load data.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Default run aggregates all subsystems as `SIN Total` and uses the full SARIMA grid.

```bash
python -m src.pipeline
```

Run a faster smoke test with fewer SARIMA candidates:

```bash
python -m src.pipeline --max-models 12
```

Run for the Southeast/Central-West subsystem:

```bash
python -m src.pipeline --subsystem "Sudeste/Centro-Oeste"
```

Outputs are saved to:

- `data/processed`
- `reports/figures`
- `reports/tables`
- `models`
