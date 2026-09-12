# Feature and Transformation Dictionary

The prediction point is before scheduled departure. A candidate feature being
available does not demonstrate that it improves accuracy; that requires later
training/validation. The authoritative allowlist is `src/features.py`.

| Columns | Definition | Purpose / availability |
|---|---|---|
| `reporting_airline`, `origin`, `destination` | Standardized source codes | Scheduled carrier and endpoint differences; categorical predictors. |
| `route` | Origin + hyphen + destination, preserving direction | Route-level operational comparisons and candidate network predictor. |
| `month`, `quarter`, `day_of_month`, `day_of_week` | Calendar fields checked against flight date; Monday=1 | Recurring date and schedule patterns. Year is constant in 2025 and excluded from X. |
| `is_weekend` | 1 on Saturday/Sunday, otherwise 0 | Weekday/weekend schedule differences. |
| `season` | DJF Winter, MAM Spring, JJA Summer, SON Fall | Calendar grouping, not measured weather. |
| `scheduled_dep_hour`, `scheduled_arr_hour` | Whole hour parsed from HHMM; 2400→0 | Pre-departure schedule timing. Invalid minutes/fractions produce missing. No flight-date shift for 2400 in hour features. |
| `departure_time_band` | Late Night 0–5; Morning 6–10; Midday 11–15; Evening 16–20; Night 21–23 | Readable scheduled departure comparisons; bands supplied by settings. |
| `dep_time_sin`, `dep_time_cos` | sin/cos of 2π × scheduled departure minutes after midnight / 1440 | Encodes clock proximity around midnight, using both coordinates. |
| `distance_miles` | Source route distance | Continuous flight-length predictor. |
| `distance_band` | Short (0,500], Medium (500,1500], Long (1500,∞) | Simple project-defined distance grouping. |
| `scheduled_elapsed_minutes` | Positive source scheduled duration; invalid nonpositive values become null | Use planned elapsed duration, never subtract local airport clocks. |
| `scheduled_elapsed_invalid` | 1 when original scheduled elapsed duration was nonpositive | Flag available from the schedule; retain alongside missing duration. |
| `origin_latitude_deg`, `origin_longitude_deg`, `destination_latitude_deg`, `destination_longitude_deg` | Physical coordinates from two IATA joins | Candidate geography predictors; supplied airport metadata is a current snapshot, not a dated 2025 reference. |
| Origin/destination `name`, `ident`, `iso_region`, `source_iata_code` | Joined airport labels and identifiers | Descriptive/audit only. Both historical BTS code and source snapshot code retained. |
| `severe_delay` | 1 when ARR_DELAY >60, 0 otherwise, only on eligible rows | Target y, never part of X. Exactly 60 minutes is not severe. |
| `ml_target_eligible` | Not cancelled, not diverted, known arrival delay | Operational filter only; exclude from predictors. |
| `completed_missing_arrival_delay` | Completed/non-diverted with missing arrival delay | Audit only; target undefined. |
| `delay_category` | ≤0 early/on-time; (0,15] minor; (15,60] moderate; >60 severe | Descriptive outcome only, missing for ineligible rows. |
| `dataset_split` | Train Jan–Aug; validation Sep–Oct; test Nov–Dec | Metadata only; dates frozen before training. |
| `flight_date`, `source_file`, `source_row_number` | Date and original filename/one-based data-row number | Traceability and chronological selection; excluded from X. |

All actual times, operational delays, actual duration, air time, cancellation and
diversion fields, cancellation reasons, and cause minutes are descriptive only.
The explicit X allowlist excludes them even when they exist in the enriched table.
Numeric/categorical redundancy is intentional at this candidate-feature stage;
later validation can select a simpler subset without looking at test performance.

## Aggregations and joins

- Two left, many-to-one IATA merges add origin and destination metadata without
  multiplying or dropping flights. Missing or ambiguous lookup codes stop ETL.
- `route_month_performance.csv` groups by month and directional route. Severe
  rate is severe count / eligible count; a zero eligible denominator yields null.
- `airport_month_cancellations.csv` groups by month and origin. Cancellation rate
  is cancellation count / all scheduled records in that airport-month.
- Notebooks pivot these grouped tables into airport/route-by-month heatmaps.
  No full-year outcome averages enter predictors; historical features are deferred.
- Distribution tables report exact eligible-flight quantiles. Plot samples use
  2,000 eligible flights per month with random seed 42 and are labeled as samples.

## Storage and next-stage contract

Each layer contains twelve `2025_MM.parquet` files: cleaned operational data in
`data/interim/flights_standardized`, enriched data in
`data/processed/flights_wrangled`, and eligible feature/label rows in
`data/processed/flights_ml`. `reports/tables/data_dictionary.csv` records stored
types and column roles. `source_file` + `source_row_number` links the layers.

Read the future ML partitions with pandas, select X using `MODEL_FEATURES`, y
using `severe_delay`, and split by `dataset_split`. Fit preprocessing on training
rows only. The data intentionally retain missing predictors; they are not yet a
fully encoded/imputed matrix. Do not fill missing targets, balance holdouts, or
train a model as part of the wrangling stage.
