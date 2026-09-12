"""Finish the 2025 wrangling stage using one month at a time."""

from collections import Counter

import numpy as np
import pandas as pd

from src.clean import CODE_COLUMNS, NUMERIC_COLUMNS, clean_chunk, quality_issue_counts
from src.config import PROJECT_ROOT, load_column_map, load_settings
from src.features import MODEL_FEATURES, ML_METADATA, add_features, join_airports, select_ml_rows
from src.initial_analysis import BUSINESS_KEY


def validate_month(flights, year, month):
    issues = quality_issue_counts(flights, year, month)
    # These two issues are documented and retained with flags.
    allowed = {"nonpositive_scheduled_elapsed_time", "completed_missing_arrival_delay"}
    failures = {name: count for name, count in issues.items() if count and name not in allowed}
    if failures:
        raise ValueError(f"Unexpected quality failures: {failures}")
    date = flights["flight_date"]
    for column, expected in [("year", date.dt.year), ("quarter", date.dt.quarter),
                             ("month", date.dt.month), ("day_of_month", date.dt.day),
                             ("day_of_week", date.dt.dayofweek + 1)]:
        if not flights[column].eq(expected).all():
            raise ValueError(f"{column} disagrees with flight_date")
    required = ["reporting_airline", "flight_number", "origin", "destination", "distance_miles"]
    if flights[required].isna().any().any():
        raise ValueError("Missing required flight identifier or distance")
    eligible = flights["ml_target_eligible"].eq(1)
    assert flights.loc[~eligible, "severe_delay"].isna().all()
    assert flights.loc[eligible, "severe_delay"].isin([0, 1]).all()
    assert flights.loc[eligible, "delay_category"].notna().all()
    return issues


def distribution_row(label, values):
    values = np.asarray(values, dtype=float)
    return {"group": label, "eligible_flights": len(values), "mean": values.mean(),
            "median": np.median(values), "p90": np.quantile(values, 0.90),
            "p95": np.quantile(values, 0.95), "p99": np.quantile(values, 0.99),
            "minimum": values.min(), "maximum": values.max()}


def run():
    settings = load_settings()
    column_map = load_column_map()
    tables = PROJECT_ROOT / "reports/tables"
    reports = PROJECT_ROOT / "reports"
    airports = pd.read_csv(PROJECT_ROOT / "data/interim/airports_standardized/airports_standardized.csv")
    assert airports["iata_code"].is_unique
    year = int(settings["project"]["start_year"])
    folders = {
        "cleaned": PROJECT_ROOT / "data/interim/flights_standardized",
        "enriched": PROJECT_ROOT / "data/processed/flights_wrangled",
        "ml": PROJECT_ROOT / "data/processed/flights_ml",
    }
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(reports / "source_manifest.csv")
    expected = set(settings["project"]["expected_months"])
    assert set(manifest["expected_month"]) == expected and manifest["status"].eq("present").all()
    counts, conversions, monthly_distributions = [], [], []
    missingness, extremes, samples, airport_months, route_months = [], [], [], [], []
    feature_missingness = []
    all_delays, airline_delays, route_delays, airport_delays = [], {}, {}, {}
    issues_total = Counter()
    route_table = pd.read_csv(tables / "route_performance.csv")
    busiest_routes = route_table.nlargest(10, "total_flights")["route"].tolist()
    origin_table = pd.read_csv(tables / "origin_airport_performance.csv")
    busiest_airports = origin_table.nlargest(10, "total_flights")["origin"].tolist()

    for month in sorted(expected):
        path = PROJECT_ROOT / settings["paths"]["raw_bts"] / f"bts_ontime_{year}_{month:02d}.csv"
        raw = pd.read_csv(path, low_memory=False)
        if set(raw.columns) != set(column_map):
            raise ValueError(f"Unexpected source schema: {path.name}")
        flights = clean_chunk(raw, column_map, path, year, month,
                              settings["target"]["severe_delay_minutes"],
                              settings["features"]["departure_time_bands"])
        flights["source_row_number"] = np.arange(1, len(flights) + 1)
        for column in ["year", "quarter", "month", "day_of_month", "day_of_week", "flight_number",
                       "crs_dep_time", "crs_arr_time", "cancelled", "diverted"]:
            flights[column] = flights[column].astype("Int64")
        issues = validate_month(flights, year, month)
        issues_total.update(issues)
        exact_duplicates = int(raw.duplicated().sum())
        key_duplicates = int(flights.duplicated(BUSINESS_KEY).sum())
        if exact_duplicates or key_duplicates:
            raise ValueError("Duplicate candidates need review before publishing this refresh")
        expected_rows = int(manifest.loc[manifest["expected_month"].eq(month), "row_count"].iloc[0])
        assert len(flights) == expected_rows

        # Record actual repairs and parse failures, separately from existing nulls.
        renamed = raw.rename(columns=column_map)
        for column in NUMERIC_COLUMNS:
            failures = renamed[column].notna() & pd.to_numeric(renamed[column], errors="coerce").isna()
            conversions.append({"month": month, "column": column, "check": "numeric_parse_failures", "rows": int(failures.sum())})
        conversions.append({"month": month, "column": "flight_date", "check": "date_parse_failures",
                            "rows": int((renamed["flight_date"].notna() & flights["flight_date"].isna()).sum())})
        for column in CODE_COLUMNS:
            before = renamed[column].astype("string")
            changed = before.fillna("<NULL>").ne(flights[column].fillna("<NULL>"))
            conversions.append({"month": month, "column": column, "check": "category_corrections", "rows": int(changed.sum())})
        del raw, renamed

        suffix = f"{year}_{month:02d}.parquet"
        flights.to_parquet(folders["cleaned"] / suffix, index=False)
        enriched = join_airports(add_features(flights, settings), airports)
        ml = select_ml_rows(enriched)
        for column in MODEL_FEATURES:
            feature_missingness.append({"month": month, "feature": column,
                                        "missing_rows": int(ml[column].isna().sum())})
        enriched.to_parquet(folders["enriched"] / suffix, index=False)
        ml.to_parquet(folders["ml"] / suffix, index=False)
        # Check persisted files, not just the DataFrames before saving.
        for stage, expected_frame in [("cleaned", flights), ("enriched", enriched), ("ml", ml)]:
            check_columns = list(expected_frame.columns) if stage == "ml" else ["source_row_number", "severe_delay"]
            check = pd.read_parquet(folders[stage] / suffix, columns=check_columns)
            pd.testing.assert_frame_equal(check.reset_index(drop=True), expected_frame[check.columns].reset_index(drop=True))
        split = enriched["dataset_split"].iloc[0]
        counts.append({"month": month, "raw_rows": expected_rows, "cleaned_rows": len(flights),
                       "enriched_rows": len(enriched), "ml_rows": len(ml),
                       "excluded_from_ml": len(flights) - len(ml), "severe_count": int(ml["severe_delay"].sum()),
                       "dataset_split": split, "min_date": flights["flight_date"].min().date(),
                       "max_date": flights["flight_date"].max().date(), "exact_duplicates": exact_duplicates,
                       "business_key_duplicates": key_duplicates, "unmatched_origin": 0, "unmatched_destination": 0})

        status = pd.Series("Completed: known outcome", index=flights.index)
        status.loc[flights["completed_missing_arrival_delay"].eq(1)] = "Completed: unknown outcome"
        status.loc[flights["diverted"].eq(1)] = "Diverted"
        status.loc[flights["cancelled"].eq(1)] = "Cancelled"
        for label in status.unique():
            group = flights.loc[status.eq(label)]
            row = {"status": label, "flights": len(group)}
            for column in ["dep_time", "arr_time", "arrival_delay_minutes", "air_time_minutes", "cancellation_code", "carrier_delay_minutes"]:
                row[column + "_missing"] = int(group[column].isna().sum())
            missingness.append(row)

        eligible = flights.loc[flights["ml_target_eligible"].eq(1)]
        delays = eligible["arrival_delay_minutes"].to_numpy(dtype=float)
        all_delays.append(delays)
        monthly_distributions.append(distribution_row(str(month), delays))
        for label, group in eligible.groupby("reporting_airline"):
            airline_delays.setdefault(label, []).append(group["arrival_delay_minutes"].to_numpy(dtype=float))
        for label, group in eligible.loc[eligible["route"].isin(busiest_routes)].groupby("route"):
            route_delays.setdefault(label, []).append(group["arrival_delay_minutes"].to_numpy(dtype=float))
        for label, group in eligible.loc[eligible["origin"].isin(busiest_airports)].groupby("origin"):
            airport_delays.setdefault(label, []).append(group["arrival_delay_minutes"].to_numpy(dtype=float))
        # Equal-sized monthly samples are for plots only, never for headline rates.
        sample = eligible.sample(n=min(2000, len(eligible)), random_state=42)
        samples.append(sample[["month", "reporting_airline", "arrival_delay_minutes", "departure_time_band"]])
        extreme_columns = BUSINESS_KEY + ["departure_delay_minutes", "arrival_delay_minutes", "scheduled_elapsed_minutes",
            "actual_elapsed_minutes", "air_time_minutes", "distance_miles", "cancelled", "diverted",
            "carrier_delay_minutes", "weather_delay_minutes", "nas_delay_minutes", "security_delay_minutes",
            "late_aircraft_delay_minutes", "source_file", "source_row_number"]
        extremes.append(flights.nlargest(10, "arrival_delay_minutes")[extreme_columns])
        extremes.append(flights.nsmallest(10, "arrival_delay_minutes")[extreme_columns])
        airport_months.append(flights.groupby(["month", "origin"], as_index=False).agg(
            total_flights=("origin", "size"), cancelled_flights=("cancelled", "sum")))
        route_months.append(flights.groupby(["month", "route"], as_index=False).agg(
            total_flights=("route", "size"), eligible_flights=("severe_delay", "count"),
            severe_count=("severe_delay", "sum"), cancelled_flights=("cancelled", "sum")))
        if month == min(expected):
            dictionary = pd.DataFrame({"column": enriched.columns, "dtype": enriched.dtypes.astype(str).values})
            dictionary["role"] = "descriptive / audit only"
            dictionary.loc[dictionary["column"].isin(MODEL_FEATURES), "role"] = "candidate predictor"
            dictionary.loc[dictionary["column"].isin(ML_METADATA), "role"] = "metadata, excluded from X"
            dictionary.loc[dictionary["column"].eq("severe_delay"), "role"] = "target y"
            dictionary.to_csv(tables / "data_dictionary.csv", index=False)
        print(f"Saved and verified {year}-{month:02d}: {len(flights):,} operational, {len(ml):,} ML rows", flush=True)
        del flights, enriched, ml, eligible

    reconciliation = pd.DataFrame(counts)
    reconciliation.to_csv(tables / "final_row_reconciliation.csv", index=False)
    splits = reconciliation.groupby("dataset_split", as_index=False).agg(
        operational_rows=("raw_rows", "sum"), eligible_rows=("ml_rows", "sum"),
        severe_count=("severe_count", "sum"), min_date=("min_date", "min"), max_date=("max_date", "max"))
    splits["severe_delay_rate"] = splits["severe_count"] / splits["eligible_rows"]
    splits.to_csv(tables / "ml_split_summary.csv", index=False)
    conversion_table = pd.DataFrame(conversions)
    conversion_table.to_csv(tables / "conversion_audit.csv", index=False)
    pd.DataFrame(feature_missingness).to_csv(tables / "ml_feature_missingness.csv", index=False)
    pd.DataFrame(missingness).groupby("status", as_index=False).sum().to_csv(tables / "missingness_by_status.csv", index=False)
    pd.DataFrame(monthly_distributions).to_csv(tables / "monthly_delay_distribution.csv", index=False)
    for name, groups in [("airline", airline_delays), ("busy_route", route_delays), ("busy_origin", airport_delays)]:
        pd.DataFrame([distribution_row(label, np.concatenate(parts)) for label, parts in groups.items()]).to_csv(
            tables / f"{name}_delay_distribution.csv", index=False)
    overall_delays = np.concatenate(all_delays)
    pd.DataFrame([distribution_row("All eligible flights", overall_delays)]).to_csv(tables / "delay_distribution.csv", index=False)
    pd.concat(samples, ignore_index=True).to_csv(tables / "eda_plot_sample.csv", index=False)
    extreme_table = pd.concat(extremes, ignore_index=True).drop_duplicates(["source_file", "source_row_number"])
    extreme_table = pd.concat([extreme_table.nlargest(10, "arrival_delay_minutes"), extreme_table.nsmallest(10, "arrival_delay_minutes")])
    extreme_table["elapsed_delay_identity_error"] = (extreme_table["arrival_delay_minutes"] - extreme_table["departure_delay_minutes"]
        - extreme_table["actual_elapsed_minutes"] + extreme_table["scheduled_elapsed_minutes"])
    extreme_table.to_csv(tables / "extreme_delay_review.csv", index=False)
    airport_month = pd.concat(airport_months, ignore_index=True)
    airport_month["cancellation_rate"] = airport_month["cancelled_flights"] / airport_month["total_flights"]
    airport_month.to_csv(tables / "airport_month_cancellations.csv", index=False)
    route_month = pd.concat(route_months, ignore_index=True)
    route_month["severe_delay_rate"] = route_month["severe_count"] / route_month["eligible_flights"].replace(0, np.nan)
    route_month.to_csv(tables / "route_month_performance.csv", index=False)
    assert airport_month["total_flights"].sum() == reconciliation["raw_rows"].sum()
    assert route_month["eligible_flights"].sum() == reconciliation["ml_rows"].sum()
    write_completion_reports(reconciliation, splits, conversion_table, issues_total, extreme_table)


def write_completion_reports(rows, splits, conversions, issues, extremes):
    reports = PROJECT_ROOT / "reports"
    total = int(rows["raw_rows"].sum())
    eligible = int(rows["ml_rows"].sum())
    parse_failures = int(conversions.loc[conversions["check"].str.contains("parse"), "rows"].sum())
    corrections = int(conversions.loc[conversions["check"].eq("category_corrections"), "rows"].sum())
    log = f"""# Final Cleaning Log — BTS 2025

Generated by `python scripts/run_etl.py`. All {total:,} source records are retained.
Source files are read only. Counts are measured on the supplied snapshot.

| Found | Rows affected | Decision and justification |
|---|---:|---|
| CSV types and 28 uppercase column names | {total:,} processed | Parse dates/numbers, use nullable integers for discrete fields, and standardize names so comparisons have consistent types. |
| Non-null values that failed numeric/date conversion | {parse_failures:,} | Count failures separately from existing missing values; do not invent replacements. |
| Category whitespace/case/blank corrections | {corrections:,} field corrections | Trim, uppercase code fields, and map blank strings to missing. Current labels already consistent if count is zero. |
| Exact / business-key duplicate rows | {int(rows['exact_duplicates'].sum())} / {int(rows['business_key_duplicates'].sum())} | No removal needed. Fail a future refresh if candidates appear, so they can be reviewed first. Monthly date checks ensure keys cannot overlap across months. |
| Nonpositive scheduled durations | {issues['nonpositive_scheduled_elapsed_time']} | Set derived duration to missing and retain `scheduled_elapsed_invalid=1`. A negative duration is impossible. Raw values and identifiers remain in flagged-row evidence. |
| Completed, non-diverted flight without arrival delay | {issues['completed_missing_arrival_delay']} | Flag, retain in operational data, and exclude from target/ML. An unknown outcome cannot be inferred from the other flights. |
| Cancelled/diverted/unknown arrival outcomes | {total - eligible:,} | Retain operational records and missing measurements; severe-delay target stays null. No zero or median imputation of outcomes. |
| Missing cancellation codes / delay causes | See missingness tables | Preserve source nulls: not-cancelled is structurally inapplicable; a missing cause is not a measured zero. Cause totals describe only reported minutes. |
| Negative or very large delays | 20 extreme rows reviewed | Retain: negative delay means early arrival, and long disruptions can be real. Check route/date/status, duration and delay identities; internal consistency does not independently prove the source record correct. |
| Historical PBI airport code | One reference alias | Retain BTS PBI and resolve via the existing configured OurAirports DJT record. Keep both codes for audit. |

## Contextual review and remaining limitations

The five invalid durations comprise three diverted flights, one cancelled flight,
and one completed DTW–LEX flight (OO 3574, 19 November) with a 218-minute arrival
delay. Keep that completed flight and its valid target; its missing scheduled
duration will require a training-fitted imputer in the ML stage. The unknown
arrival outcome is YX 5859, JFK–MVY, 6 September; leave its target undefined.

Among the 20 reviewed extremes, {int(extremes['elapsed_delay_identity_error'].ne(0).sum())}
fail the identity `arrival_delay - departure_delay = actual_duration - scheduled_duration`.
The reviewed range is {extremes['arrival_delay_minutes'].min():.0f} to
{extremes['arrival_delay_minutes'].max():.0f} minutes. No statistical trimming,
winsorizing, or full-dataset imputation was performed.

`conversion_audit.csv`, `missingness_by_status.csv`, `flagged_row_samples.csv`,
`extreme_delay_review.csv`, and `final_row_reconciliation.csv` provide evidence.
Airport joins preserve every operational row and resolve every origin/destination.
Current airport names/regions are descriptive snapshot labels, not a historical
2025 dimension. Physical coordinates are candidate features with this limitation.
"""
    (reports / "cleaning_log.md").write_text(log, encoding="utf-8")
    result = f"""# Cleaning and Transformation Completion

- Raw, cleaned, and enriched operational rows: **{total:,}** each.
- Eligible rows exported for future ML: **{eligible:,}**.
- Removed operational rows: **0**; excluded only from ML: **{total - eligible:,}**.
- Twelve Parquet files per layer: `flights_standardized`, `flights_wrangled`, `flights_ml`.
- Both airport merges validated as many-to-one; zero unmatched flight rows.
- Exact full-year and group delay quantiles, contextual extreme review, monthly
  airport cancellations, and route-month aggregates generated from every month.
- Predictor allowlist: `src/features.py`; column types/roles: `tables/data_dictionary.csv`.

## Chronological ML handoff

| Split | Eligible rows | Severe delays | Severe rate | Dates |
|---|---:|---:|---:|---|
"""
    for split in ["train", "validation", "test"]:
        row = splits.loc[splits["dataset_split"].eq(split)].iloc[0]
        result += f"| {split} | {row['eligible_rows']:,} | {row['severe_count']:,} | {row['severe_delay_rate']:.2%} | {row['min_date']} to {row['max_date']} |\n"
    result += """
Use `MODEL_FEATURES` for X and `severe_delay` for y. Date, provenance, and split
columns are metadata. No encoders, imputers, scalers, resampling, or models have
been fitted. Learn these only from training rows in the future ML notebook.
Outcome aggregates are descriptive tables, never predictors. The model task is
conditional on a completed, non-diverted flight with a known outcome; cancellation
and diversion are separate operational analyses. Full-year EDA includes holdout
months, so it is descriptive and not evidence of an untouched model evaluation.

Warehouse construction, model comparison, and Power BI remain later milestones.
"""
    (reports / "transformation_report.md").write_text(result, encoding="utf-8")

    # The audit writes a first-pass report; mark the completed final pass here.
    quality_path = reports / "data_quality_report.md"
    quality = quality_path.read_text(encoding="utf-8")
    quality = quality.replace(
        "No records were removed during this initial phase. Candidate issues remain traceable for the next cleaning decision.",
        "Final cleaning retained every operational record. The five invalid durations and one unknown completed arrival outcome were reviewed; see cleaning_log.md for decisions."
    )
    quality += f"""
## Final persistence and validation

- {total:,} cleaned and enriched operational rows read back from monthly Parquet.
- {eligible:,} eligible ML rows persisted with the explicit feature allowlist.
- All saved ML values/types checked against the pre-save DataFrames.
- Calendar fields agree with flight dates; both endpoint joins preserve rows.
- Conversion/category audit: {parse_failures} parse failures and {corrections} actual field corrections.
- Full reconciliation: `tables/final_row_reconciliation.csv`.
- Remaining missing predictors: `tables/ml_feature_missingness.csv`; imputation belongs to training only.
"""
    quality_path.write_text(quality, encoding="utf-8")
    eda_path = reports / "eda_progress_report.md"
    eda = eda_path.read_text(encoding="utf-8")
    eda = eda.replace("# Initial EDA Progress Report", "# Completed Cleaning and EDA Report")
    eda = eda.replace("This report covers the first full-pass EDA across all monthly files.",
                      "This report covers the completed descriptive EDA across all monthly files.")
    start = eda.index("## Next EDA work")
    end = eda.index("## Limitations at this checkpoint")
    eda = eda[:start] + """## Final EDA additions

- Expanded notebook with raw audit, explicit cleaning operations, and decisions.
- Reviewed all six flagged records and 20 delay extremes without dropping flights.
- Exact full-year, monthly, airline, and busiest-route/origin mean/median/quantiles.
- Distribution plots using a documented 2,000-flight-per-month sample.
- Highest/lowest origin-rate comparisons with minimum-volume filters.
- Airport-month cancellation and route-month severe-delay heatmaps.
- Full row reconciliation and an explicit ML feature/split handoff.

The new figures are reproduced by `python scripts/execute_notebooks.py` after ETL.

""" + eda[end:]
    eda += "\n- Full-year EDA includes holdout outcomes; future model tuning must still respect the frozen chronological split.\n"
    eda_path.write_text(eda, encoding="utf-8")
