# Generated CSV tables by project milestone

The original inputs are in `data/raw/`: 12 monthly BTS flight CSVs and one
OurAirports CSV. The pipeline never edits those files. Run
`python scripts/run_etl.py` to regenerate the tables below from those inputs.

| Folder | Milestone | What its CSVs answer |
|---|---|---|
| `02_ingestion/` | 2 — Ingestion | Which source files arrived, and how many rows/dates/columns does each contain? |
| `03_cleaning/` | 3 — Cleaning | What is missing, invalid, converted, or flagged? |
| `04_transformation/` | 4 — Transformation | Did airport joins and row preservation work? |
| `06_eda/` | 6 — EDA | What patterns appear across flights, airlines, routes, airports, and time? |
| `07_ml_preparation/` | 7 — ML preparation | Which fields can enter the model, and how many rows are in each split? |

Milestone 5 (warehouse) has no CSV table yet. The numbering follows
`PROJECT_PLAN.md`, so the missing `05_` folder is intentional. Models and Power
BI exports are also future work.

## Start with these four files

1. `02_ingestion/source_manifest.csv` — inventory and row counts of the 12 inputs.
2. `03_cleaning/row_reconciliation.csv` — initial audit and target eligibility.
3. `04_transformation/final_row_reconciliation.csv` — raw, cleaned, enriched,
   and ML row counts for every month.
4. `07_ml_preparation/ml_split_summary.csv` — training, validation, and test
   months and eligible row counts.

The other CSVs are supporting audit or EDA results. Most contain summaries,
not additional flight records. `06_eda/eda_plot_sample.csv` is a 24,000-row
plotting sample; it is not the model training data.

The actual cleaned and ML-ready flight records are saved as 12 monthly
**Parquet** files in each of `data/interim/flights_standardized/`,
`data/processed/flights_wrangled/`, and `data/processed/flights_ml/`.
`data/interim/airports_standardized/airports_standardized.csv` is a generated
airport lookup used during enrichment.
