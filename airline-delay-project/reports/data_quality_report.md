# Data Quality Report — BTS 2025

Generated from all 12 monthly raw files using chunked processing. Raw files were read only.

## Source coverage

| Month | Status | Rows | Minimum flight date | Maximum flight date |
|---:|---|---:|---|---|
| 01 | present | 539,747 | 2025-01-01 | 2025-01-31 |
| 02 | present | 504,884 | 2025-02-01 | 2025-02-28 |
| 03 | present | 600,872 | 2025-03-01 | 2025-03-31 |
| 04 | present | 583,950 | 2025-04-01 | 2025-04-30 |
| 05 | present | 605,648 | 2025-05-01 | 2025-05-31 |
| 06 | present | 611,575 | 2025-06-01 | 2025-06-30 |
| 07 | present | 631,428 | 2025-07-01 | 2025-07-31 |
| 08 | present | 602,378 | 2025-08-01 | 2025-08-31 |
| 09 | present | 562,439 | 2025-09-01 | 2025-09-30 |
| 10 | present | 605,844 | 2025-10-01 | 2025-10-31 |
| 11 | present | 570,550 | 2025-11-01 | 2025-11-30 |
| 12 | present | 582,304 | 2025-12-01 | 2025-12-31 |

- Total flight rows: **7,001,619**
- Exact duplicate rows after the first occurrence: **0**
- Business-key duplicate rows after the first occurrence: **0**
- Schema consistency: **consistent**

## Highest raw-column missingness

| Column | Null rows | Null percentage |
|---|---:|---:|
| CANCELLATION_CODE | 6,898,743 | 98.53% |
| LATE_AIRCRAFT_DELAY | 5,466,981 | 78.08% |
| SECURITY_DELAY | 5,466,981 | 78.08% |
| NAS_DELAY | 5,466,981 | 78.08% |
| WEATHER_DELAY | 5,466,981 | 78.08% |
| CARRIER_DELAY | 5,466,981 | 78.08% |
| ARR_DELAY | 122,135 | 1.74% |
| AIR_TIME | 122,135 | 1.74% |
| ACTUAL_ELAPSED_TIME | 122,135 | 1.74% |
| ARR_TIME | 104,608 | 1.49% |

Missing operational fields on cancelled or diverted flights are not automatically treated as errors.

## Quality checks

| Check | Rows affected |
|---|---:|
| Unexpected Year | 0 |
| Source Month Mismatch | 0 |
| Missing Flight Date | 0 |
| Flight Date Period Mismatch | 0 |
| Invalid Origin Code | 0 |
| Invalid Destination Code | 0 |
| Nonpositive Distance | 0 |
| Invalid Cancelled Flag | 0 |
| Invalid Diverted Flag | 0 |
| Invalid Scheduled Departure Time | 0 |
| Invalid Scheduled Arrival Time | 0 |
| Nonpositive Scheduled Elapsed Time | 5 |
| Negative Actual Elapsed Time | 0 |
| Negative Air Time | 0 |
| Completed Missing Arrival Delay | 1 |
| Cancelled With Arrival Delay | 0 |

Final cleaning retained every operational record. The five invalid durations and one unknown completed arrival outcome were reviewed; see cleaning_log.md for decisions.

## Airport source and join coverage

- Raw OurAirports rows: **86,053**
- Standardized airport dimension rows with a valid unique IATA code: **9,057**
- Duplicate-IATA candidate rows investigated by deterministic ranking: **0**
- Historical IATA alias rows added from documented configuration: **1**

| Flight role | Distinct BTS codes | Matched codes | Code match rate | Flight rows with unmatched code |
|---|---:|---:|---:|---:|
| Origin | 352 | 352 | 100.00% | 0 |
| Destination | 352 | 352 | 100.00% | 0 |

## Target eligibility

- Eligible completed, non-diverted flights with known arrival delay: **6,879,484**
- Rows excluded from the arrival-delay target: **122,135**
- Severe-delay threshold: **arrival delay greater than 60 minutes**

## Interpretation notes

- `ARR_DELAY` is the available BTS field and is used to derive the non-negative threshold test; no separate `ARR_DELAY_NEW` field was downloaded.
- Cancelled and diverted flights retain their operational records but receive a null severe-delay target.
- Outlying delay values are retained because large disruption events can be legitimate.
- The one-year scope supports within-2025 analysis but not year-over-year trend claims.

## Final persistence and validation

- 7,001,619 cleaned and enriched operational rows read back from monthly Parquet.
- 6,879,484 eligible ML rows persisted with the explicit feature allowlist.
- All saved ML values/types checked against the pre-save DataFrames.
- Calendar fields agree with flight dates; both endpoint joins preserve rows.
- Conversion/category audit: 0 parse failures and 0 actual field corrections.
- Full reconciliation: `tables/04_transformation/final_row_reconciliation.csv`.
- Remaining missing predictors: `tables/07_ml_preparation/ml_feature_missingness.csv`; imputation belongs to training only.
