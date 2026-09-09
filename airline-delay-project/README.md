# Airline Delay Project

This project uses all 12 monthly 2025 BTS Reporting Carrier On-Time Performance files and the supplied OurAirports metadata. The current implementation covers repository setup, full-source auditing, a first cleaning/transformation pass, airport-code validation, and first-pass EDA. Machine learning has intentionally not started yet.

## Current status

- 12/12 monthly BTS files present
- 7,001,619 flight rows audited
- 28 source columns with a consistent schema
- no exact or business-key duplicates detected
- cleaning and feature logic implemented with chunked processing
- 100% of 352 BTS origin and destination codes resolved against the airport dimension using a documented historical `PBI -> DJT` alias
- first-pass EDA tables and four figures generated

See `reports/data_quality_report.md`, `reports/cleaning_log.md`, `reports/eda_progress_report.md`, and `reports/literature_review_and_research_gaps.md` for the measured results, research basis, and decisions.

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
├── docs/Data_Wrangling_Project_Guidelines.pdf
├── reports/
│   ├── figures/
│   └── tables/
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

The initial-analysis script runs with pandas, NumPy, matplotlib, and PyYAML. The beginner EDA notebook uses pandas, NumPy, Matplotlib, and Seaborn. PyArrow is listed because a later stage will persist partitioned Parquet files.

## Run the initial cleaning and EDA pass

```bash
python scripts/run_initial_analysis.py
```

The script processes the files in 100,000-row chunks and regenerates:

- `reports/source_manifest.csv`
- `reports/data_quality_report.md`
- `reports/cleaning_log.md`
- `reports/eda_progress_report.md`
- detailed CSV tables in `reports/tables/`
- four PNG figures in `reports/figures/`
- `data/interim/airports_standardized/airports_standardized.csv`

## Open the beginner-friendly EDA notebook

After the initial-analysis script has created the summary tables, start Jupyter:

```bash
jupyter lab
```

Then open `notebooks/01_beginner_eda.ipynb` and choose **Run All Cells**. The notebook uses short pandas, NumPy, Matplotlib, and Seaborn cells to reproduce the four EDA figures and the same five headline findings. It reads the prepared summary tables instead of loading all 884 MB of raw CSV data, which keeps it fast and suitable for a classroom explanation.

## Run tests

After installing the requirements:

```bash
python -m pytest -q
```

The current tests cover scheduled-time parsing, target eligibility, and invalid scheduled-duration handling.

## Cleaning rules already implemented

- standardize source column names using `config/column_map.yaml`
- parse BTS flight dates and numeric measures
- trim and uppercase airline, airport, and cancellation codes
- keep legitimate missing operational values for cancelled/diverted flights
- flag and null impossible nonpositive scheduled durations in derived data
- detect exact and business-key duplicates without deleting candidates blindly
- derive route, scheduled departure hour, time band, weekend, season, delay category, and severe-delay target
- set the severe-delay target only for noncancelled, nondiverted flights with a known arrival delay
- preserve extreme delays for contextual investigation instead of deleting statistical outliers

## Next implementation sequence

1. Review the six flagged records and extreme-delay cases in context; finalize the retained-column schema.
2. Persist monthly cleaned flight partitions as Parquet, including provenance and quality flags.
3. Join origin/destination airport keys and validate all foreign keys.
4. Create the first three explanatory notebooks from the reproducible report tables.
5. Build the SQLite star schema and row-reconciliation checks.
6. Freeze the chronological 2025 train/validation/test split, then begin the baseline and ML models.

The proposed ML split is January-August for training, September-October for validation, and November-December for testing. This is a within-year future holdout; conclusions must not claim year-over-year generalization.

## Course requirement alignment

The supplied project guidelines require a real messy dataset, a justified cleaning log, at least one non-trivial transformation/join, persistent storage, three evidence-backed insights, an ML comparison, and a three-page Power BI dashboard. The 2025 BTS data comfortably satisfies the size and complexity requirements. Persistent storage, ML, and Power BI remain later milestones.
