# Cleaning and Transformation Completion

- Raw, cleaned, and enriched operational rows: **7,001,619** each.
- Eligible rows exported for future ML: **6,879,484**.
- Removed operational rows: **0**; excluded only from ML: **122,135**.
- Twelve Parquet files per layer: `flights_standardized`, `flights_wrangled`, `flights_ml`.
- Both airport merges validated as many-to-one; zero unmatched flight rows.
- Exact full-year and group delay quantiles, contextual extreme review, monthly
  airport cancellations, and route-month aggregates generated from every month.
- Predictor allowlist: `src/features.py`; column types/roles: `tables/07_ml_preparation/data_dictionary.csv`.

## Chronological ML handoff

| Split | Eligible rows | Severe delays | Severe rate | Dates |
|---|---:|---:|---:|---|
| train | 4,592,366 | 387,319 | 8.43% | 2025-01-01 to 2025-08-31 |
| validation | 1,159,898 | 67,042 | 5.78% | 2025-09-01 to 2025-10-31 |
| test | 1,127,220 | 98,647 | 8.75% | 2025-11-01 to 2025-12-31 |

Use `MODEL_FEATURES` for X and `severe_delay` for y. Date, provenance, and split
columns are metadata. No encoders, imputers, scalers, resampling, or models have
been fitted. Learn these only from training rows in the future ML notebook.
Outcome aggregates are descriptive tables, never predictors. The model task is
conditional on a completed, non-diverted flight with a known outcome; cancellation
and diversion are separate operational analyses. Full-year EDA includes holdout
months, so it is descriptive and not evidence of an untouched model evaluation.

Warehouse construction, model comparison, and Power BI remain later milestones.
