# Airline Delay Project

This project uses all 12 monthly 2025 BTS Reporting Carrier On-Time Performance files and the supplied OurAirports metadata. Data cleaning, descriptive EDA, airport enrichment, and feature engineering are complete. The code uses pandas, NumPy, Matplotlib, and Seaborn, with PyArrow for Parquet storage. Model training, the SQL warehouse, and Power BI are later stages.

## Current status

- 12/12 monthly BTS files present
- 7,001,619 flight rows audited
- 28 source columns with a consistent schema
- no exact or business-key duplicates detected
- 7,001,619 cleaned and airport-enriched operational rows saved in monthly Parquet files
- 6,879,484 eligible ML rows saved with a pre-departure feature allowlist and chronological split
- five invalid durations flagged/nulled; one unknown completed outcome excluded from the target
- 100% of 352 BTS origin and destination codes resolved against the airport dimension using a documented historical `PBI -> DJT` alias
- expanded, executed cleaning/EDA and feature-engineering notebooks with tables and charts

See `reports/cleaning_log.md`, `reports/transformation_report.md`, and `reports/feature_dictionary.md` for decisions, measured results, and feature definitions. The research basis remains in `reports/literature_review_and_research_gaps.md`.

## Repository structure

```text
airline-delay-project/
├── PROJECT_PLAN.md
├── README.md
├── config/
├── data/
│   ├── raw/
│   │   ├── bts/2025/bts_ontime_2025_01.csv ... bts_ontime_2025_12.csv
│   │   └── airports/airports.csv
│   ├── interim/
│   └── processed/
├── Professors guideline doc/
├── reports/
│   ├── figures/
│   └── tables/
│       ├── 02_ingestion/
│       ├── 03_cleaning/
│       ├── 04_transformation/
│       ├── 06_eda/
│       ├── 07_ml_preparation/
│       └── README.md
├── scripts/
├── src/
└── tests/
```


Raw files are never edited by the pipeline.

## Setup

Python 3.11 or newer is recommended.

```bash
cd airline-delay-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use the project virtual environment for both scripts and Jupyter so library versions match `requirements.txt`. PyYAML reads existing configuration; PyArrow supports pandas Parquet I/O. The source audit reads 100,000-row chunks; final ETL processes one month at a time. Several GB of available memory are recommended for the monthly pass and notebook walkthrough.

## Reproduce cleaning and transformation from raw files

```bash
python scripts/run_etl.py
python scripts/execute_notebooks.py
```

The ETL script runs the source audit, final cleaning, airport joins, feature engineering, and validation. It regenerates:

- `reports/tables/02_ingestion/source_manifest.csv`
- `reports/data_quality_report.md`
- `reports/cleaning_log.md`
- `reports/eda_progress_report.md`
- detailed CSV tables in milestone folders under `reports/tables/` (see `reports/tables/README.md`)
- baseline PNG figures in `reports/figures/`; notebook execution adds the remaining charts
- `data/interim/airports_standardized/airports_standardized.csv`
- `data/interim/flights_standardized/2025_MM.parquet` (all cleaned operational rows)
- `data/processed/flights_wrangled/2025_MM.parquet` (enriched operational rows)
- `data/processed/flights_ml/2025_MM.parquet` (eligible rows with features, target, and split)
- final reconciliation, conversion audit, missingness-by-status, distribution, and split tables
- `reports/transformation_report.md` and `reports/tables/07_ml_preparation/data_dictionary.csv`

Each flight layer contains 12 monthly files. Large data and generated PNG/CSV outputs are ignored by Git; both executed notebooks and Markdown reports can be committed. Rerunning ETL refreshes generated outputs and never edits raw sources. The older `scripts/run_initial_analysis.py` remains an audit-only entrypoint; use the full ETL command for current final reports.

## Open the beginner-friendly notebooks

After ETL, start Jupyter from the activated virtual environment:

```bash
python -m jupyterlab
```

1. `notebooks/01_beginner_eda.ipynb`: raw audit, visible cleaning operations, missing-value justifications, six flagged records, extreme review, full-year EDA, and reconciliation.
2. `notebooks/02_feature_engineering.ipynb`: route/calendar/time/distance features, two airport merges, group-by/pivots, target governance, feature allowlist, and saved-data verification.

Choose **Run All Cells** in order within each notebook. Notebook 01 uses a 10,000-row teaching preview and full-year report tables; its distribution charts use a clearly labeled monthly sample. Notebook 02 walks through a full January partition and checks all 12 monthly outputs. `scripts/execute_notebooks.py` runs both from fresh kernels and saves outputs; a single notebook filename may also be supplied as an argument.

## Run tests

After installing the requirements:

```bash
python -m pytest -q
```

Tests cover target boundaries and exclusions, invalid/missing times, category normalization, bad numeric input, calendar validation, distance/cyclic features, join cardinality/coverage, chronological boundaries, leakage exclusions, and Parquet round-trip types/values.

## Cleaning rules already implemented

- standardize source column names using `config/column_map.yaml`
- parse BTS flight dates and numeric measures
- trim and uppercase airline, airport, and cancellation codes
- keep legitimate missing operational values for cancelled/diverted flights
- flag and null impossible nonpositive scheduled durations in derived data
- detect exact and business-key duplicates without deleting candidates blindly
- derive route, scheduled hours, cyclic departure-time coordinates, distance band, time band, weekend, season, delay category, and severe-delay target
- set the severe-delay target only for noncancelled, nondiverted flights with a known arrival delay
- preserve extreme delays for contextual investigation instead of deleting statistical outliers

## Next implementation sequence

1. Build the SQLite star schema with airport/date/airline keys and row-reconciliation checks.
2. Create the ML notebook using `MODEL_FEATURES` from `src/features.py`; fit imputation/encoding/scaling on training rows only.
3. Train the baseline and planned classifiers, evaluate severe-delay detection, then prepare Power BI outputs.

The saved ML split is January-August for training, September-October for validation, and November-December for testing. Candidate predictors still contain legitimate missing values; this stage does not fit an imputer or encoder. Full-year EDA includes holdout outcomes; keep later model tuning separate from test evaluation. This is a within-year future holdout, not evidence of year-over-year generalization.

## Course requirement alignment

The completed stage includes justified missing-value/type/category/duplicate decisions, a short cleaning log, two source joins, group-by/pivot transformations, derived features, persistent Parquet data, and evidence-backed EDA findings. The SQLite warehouse, ML comparison, and Power BI dashboard remain later milestones.
