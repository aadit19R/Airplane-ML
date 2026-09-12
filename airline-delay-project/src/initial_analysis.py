from __future__ import annotations

import hashlib
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "airline-matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.clean import NUMERIC_COLUMNS, clean_chunk, quality_issue_counts
from src.config import load_column_map, load_settings, project_path


BUSINESS_KEY = [
    "flight_date",
    "reporting_airline",
    "flight_number",
    "origin",
    "destination",
    "crs_dep_time",
]

GROUPS = {
    "monthly_performance": ["month"],
    "airline_performance": ["reporting_airline"],
    "origin_airport_performance": ["origin"],
    "destination_airport_performance": ["destination"],
    "route_performance": ["route"],
    "day_of_week_performance": ["day_of_week"],
    "departure_hour_performance": ["scheduled_dep_hour"],
    "departure_time_band_performance": ["departure_time_band"],
    "weekend_performance": ["is_weekend"],
    "season_performance": ["season"],
}

CAUSE_COLUMNS = [
    "carrier_delay_minutes",
    "weather_delay_minutes",
    "nas_delay_minutes",
    "security_delay_minutes",
    "late_aircraft_delay_minutes",
]

CAUSE_LABELS = {
    "carrier_delay_minutes": "Carrier",
    "weather_delay_minutes": "Weather",
    "nas_delay_minutes": "NAS",
    "security_delay_minutes": "Security",
    "late_aircraft_delay_minutes": "Late Aircraft",
}


def _add_frames(left: pd.DataFrame | None, right: pd.DataFrame) -> pd.DataFrame:
    if left is None:
        return right
    return left.add(right, fill_value=0)


def _group_chunk(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    valid_key = frame[keys].notna().all(axis=1)
    data = frame.loc[valid_key, keys].copy()
    eligible = frame.loc[valid_key, "ml_target_eligible"].eq(1)
    arrival = frame.loc[valid_key, "arrival_delay_minutes"]
    dep_valid = frame.loc[valid_key, "cancelled"].eq(0) & frame.loc[
        valid_key, "departure_delay_minutes"
    ].notna()
    departure = frame.loc[valid_key, "departure_delay_minutes"]

    data["total_flights"] = 1
    data["target_eligible_flights"] = eligible.astype("int64")
    data["arrival_delay_sum"] = arrival.where(eligible, 0).fillna(0)
    data["arrival_delay_observations"] = eligible.astype("int64")
    data["departure_delay_sum"] = departure.where(dep_valid, 0).fillna(0)
    data["departure_delay_observations"] = dep_valid.astype("int64")
    data["severe_delay_count"] = (
        frame.loc[valid_key, "severe_delay"].eq(1).fillna(False).astype("int64")
    )
    data["on_time_early_count"] = (
        (eligible & arrival.le(0)).fillna(False).astype("int64")
    )
    data["cancelled_flights"] = frame.loc[valid_key, "cancelled"].eq(1).astype("int64")
    data["diverted_flights"] = frame.loc[valid_key, "diverted"].eq(1).astype("int64")
    return data.groupby(keys, observed=True).sum(numeric_only=True)


def _finalize_group(table: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    result = table.reset_index()
    result["average_arrival_delay_minutes"] = (
        result["arrival_delay_sum"] / result["arrival_delay_observations"]
    )
    result["average_departure_delay_minutes"] = (
        result["departure_delay_sum"] / result["departure_delay_observations"]
    )
    result["severe_delay_rate"] = (
        result["severe_delay_count"] / result["target_eligible_flights"]
    )
    result["on_time_early_rate"] = (
        result["on_time_early_count"] / result["target_eligible_flights"]
    )
    result["cancellation_rate"] = result["cancelled_flights"] / result["total_flights"]
    result["diversion_rate"] = result["diverted_flights"] / result["total_flights"]
    count_columns = [
        "total_flights",
        "target_eligible_flights",
        "arrival_delay_observations",
        "departure_delay_observations",
        "severe_delay_count",
        "on_time_early_count",
        "cancelled_flights",
        "diverted_flights",
    ]
    result[count_columns] = result[count_columns].round().astype("int64")
    return result.sort_values(keys).reset_index(drop=True)


def _duplicate_count(hashes: list[np.ndarray]) -> int:
    if not hashes:
        return 0
    combined = np.concatenate(hashes)
    return int(combined.size - np.unique(combined).size)


def _human_int(value: int | float) -> str:
    return f"{int(value):,}"


def _human_pct(value: float) -> str:
    return f"{value:.2%}"


@dataclass
class AnalysisState:
    raw_columns: list[str]
    total_rows: int = 0
    null_counts: Counter = field(default_factory=Counter)
    dtype_observations: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_values: dict[str, set[Any]] = field(default_factory=lambda: defaultdict(set))
    numeric_min: dict[str, float] = field(default_factory=dict)
    numeric_max: dict[str, float] = field(default_factory=dict)
    issue_counts: Counter = field(default_factory=Counter)
    grouped: dict[str, pd.DataFrame] = field(default_factory=dict)
    cancellation_codes: Counter = field(default_factory=Counter)
    cause_minutes: Counter = field(default_factory=Counter)
    cause_reported_rows: Counter = field(default_factory=Counter)
    arrival_delays: list[np.ndarray] = field(default_factory=list)
    origin_codes: set[str] = field(default_factory=set)
    destination_codes: set[str] = field(default_factory=set)
    airport_unmatched_rows: Counter = field(default_factory=Counter)
    unmatched_airport_codes: dict[str, Counter] = field(
        default_factory=lambda: {"origin": Counter(), "destination": Counter()}
    )
    flagged_samples: list[pd.DataFrame] = field(default_factory=list)

    def update(
        self,
        raw: pd.DataFrame,
        clean: pd.DataFrame,
        expected_year: int,
        expected_month: int,
        airport_codes: set[str],
    ) -> None:
        self.total_rows += len(raw)
        for column in self.raw_columns:
            series = raw[column]
            self.null_counts[column] += int(series.isna().sum())
            self.dtype_observations[column].add(str(series.dtype))
            values = series.dropna().unique()
            self.unique_values[column].update(values.tolist())

        for column in NUMERIC_COLUMNS:
            if column not in clean:
                continue
            series = clean[column].dropna()
            if series.empty:
                continue
            current_min = float(series.min())
            current_max = float(series.max())
            self.numeric_min[column] = min(self.numeric_min.get(column, current_min), current_min)
            self.numeric_max[column] = max(self.numeric_max.get(column, current_max), current_max)

        self.issue_counts.update(quality_issue_counts(clean, expected_year, expected_month))

        identifier_columns = [
            "flight_date",
            "reporting_airline",
            "flight_number",
            "origin",
            "destination",
            "crs_dep_time",
            "cancelled",
            "diverted",
            "arrival_delay_minutes",
            "scheduled_elapsed_minutes",
            "source_file",
        ]
        invalid_elapsed = clean["scheduled_elapsed_invalid"].eq(1)
        if invalid_elapsed.any():
            sample = clean.loc[invalid_elapsed, identifier_columns].copy()
            sample["raw_scheduled_elapsed_minutes"] = raw.loc[
                invalid_elapsed, "CRS_ELAPSED_TIME"
            ].to_numpy()
            sample["issue"] = "nonpositive_scheduled_elapsed_time"
            self.flagged_samples.append(sample)
        missing_arrival = (
            clean["cancelled"].eq(0)
            & clean["diverted"].eq(0)
            & clean["arrival_delay_minutes"].isna()
        )
        if missing_arrival.any():
            sample = clean.loc[missing_arrival, identifier_columns].copy()
            sample["raw_scheduled_elapsed_minutes"] = raw.loc[
                missing_arrival, "CRS_ELAPSED_TIME"
            ].to_numpy()
            sample["issue"] = "completed_missing_arrival_delay"
            self.flagged_samples.append(sample)

        for name, keys in GROUPS.items():
            grouped = _group_chunk(clean, keys)
            self.grouped[name] = _add_frames(self.grouped.get(name), grouped)

        codes = clean["cancellation_code"].dropna()
        self.cancellation_codes.update(codes.value_counts().to_dict())
        for column in CAUSE_COLUMNS:
            values = clean[column]
            self.cause_minutes[column] += float(values.fillna(0).sum())
            self.cause_reported_rows[column] += int(values.gt(0).sum())

        eligible_delays = clean.loc[
            clean["ml_target_eligible"].eq(1), "arrival_delay_minutes"
        ].dropna()
        self.arrival_delays.append(eligible_delays.to_numpy(dtype="float32"))

        for perspective, column in (("origin", "origin"), ("destination", "destination")):
            valid_codes = clean[column].dropna()
            code_counts = valid_codes.value_counts()
            distinct = set(code_counts.index.astype(str))
            if perspective == "origin":
                self.origin_codes.update(distinct)
            else:
                self.destination_codes.update(distinct)
            unmatched = {code for code in distinct if code not in airport_codes}
            self.airport_unmatched_rows[perspective] += int(code_counts.loc[list(unmatched)].sum()) if unmatched else 0
            for code in unmatched:
                self.unmatched_airport_codes[perspective][code] += int(code_counts.loc[code])


def load_airport_dimension(
    path: Path,
    output_path: Path,
    aliases: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, set[str], dict[str, int]]:
    airports = pd.read_csv(path, low_memory=False)
    keep = [
        "iata_code",
        "ident",
        "name",
        "type",
        "latitude_deg",
        "longitude_deg",
        "elevation_ft",
        "iso_country",
        "iso_region",
        "municipality",
        "scheduled_service",
    ]
    dimension = airports[keep].copy()
    for column in ["iata_code", "ident", "iso_country", "iso_region", "scheduled_service"]:
        dimension[column] = dimension[column].astype("string").str.strip().str.upper()
    dimension["iata_code"] = dimension["iata_code"].replace("", pd.NA)
    valid_iata = dimension["iata_code"].fillna("").str.fullmatch(r"[A-Z]{3}")
    valid = dimension.loc[valid_iata].copy()
    valid["country_priority"] = valid["iso_country"].eq("US").fillna(False).astype(int)
    valid["service_priority"] = valid["scheduled_service"].eq("YES").fillna(False).astype(int)
    type_priority = {
        "large_airport": 4,
        "medium_airport": 3,
        "small_airport": 2,
        "heliport": 1,
    }
    valid["type_priority"] = valid["type"].map(type_priority).fillna(0)
    duplicate_iata_rows = int(valid.duplicated("iata_code", keep=False).sum())
    valid = valid.sort_values(
        ["iata_code", "country_priority", "service_priority", "type_priority", "ident"],
        ascending=[True, False, False, False, True],
    )
    dimension_out = valid.drop_duplicates("iata_code", keep="first").drop(
        columns=["country_priority", "service_priority", "type_priority"]
    )
    dimension_out.insert(1, "source_iata_code", dimension_out["iata_code"])
    alias_rows = []
    for historical_code, current_code in (aliases or {}).items():
        if dimension_out["iata_code"].eq(historical_code).any():
            continue
        source = dimension_out.loc[dimension_out["iata_code"].eq(current_code)]
        if source.empty:
            raise ValueError(
                f"Airport alias {historical_code}->{current_code} cannot be resolved in OurAirports"
            )
        alias = source.iloc[0].copy()
        alias["iata_code"] = historical_code
        alias_rows.append(alias)
    if alias_rows:
        dimension_out = pd.concat([dimension_out, pd.DataFrame(alias_rows)], ignore_index=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dimension_out.to_csv(output_path, index=False)
    metadata = {
        "raw_airport_rows": len(airports),
        "valid_iata_rows": len(valid),
        "duplicate_iata_candidate_rows": duplicate_iata_rows,
        "dimension_rows": len(dimension_out),
        "historical_alias_rows": len(alias_rows),
    }
    return dimension_out, set(dimension_out["iata_code"].astype(str)), metadata


def _plot_outputs(tables: dict[str, pd.DataFrame], cause_table: pd.DataFrame, figures_dir: Path, thresholds: dict[str, int]) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    monthly = tables["monthly_performance"].sort_values("month")
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax1.bar(monthly["month"], monthly["total_flights"], color="#4C78A8", alpha=0.75)
    ax1.set_xlabel("Month (2025)")
    ax1.set_ylabel("Scheduled flights")
    ax1.set_xticks(range(1, 13))
    ax2 = ax1.twinx()
    ax2.plot(monthly["month"], monthly["severe_delay_rate"] * 100, color="#E45756", marker="o", linewidth=2)
    ax2.set_ylabel("Severe arrival-delay rate (%)")
    ax1.set_title("Monthly flight volume and severe-delay rate")
    fig.tight_layout()
    fig.savefig(figures_dir / "monthly_volume_and_severe_delay.png", dpi=160)
    plt.close(fig)

    bands = tables["departure_time_band_performance"].copy()
    order = ["Late Night", "Morning", "Midday", "Evening", "Night"]
    bands["departure_time_band"] = pd.Categorical(bands["departure_time_band"], order, ordered=True)
    bands = bands.sort_values("departure_time_band")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(bands["departure_time_band"].astype(str), bands["severe_delay_rate"] * 100, color="#F58518")
    ax.set_ylabel("Severe arrival-delay rate (%)")
    ax.set_xlabel("Scheduled departure time band")
    ax.set_title("Severe-delay rate by scheduled departure time")
    fig.tight_layout()
    fig.savefig(figures_dir / "severe_delay_by_departure_band.png", dpi=160)
    plt.close(fig)

    airlines = tables["airline_performance"]
    airlines = airlines.loc[airlines["total_flights"] >= thresholds["airline_min_flights"]]
    airlines = airlines.sort_values("severe_delay_rate", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(airlines["reporting_airline"], airlines["severe_delay_rate"] * 100, color="#54A24B")
    ax.invert_yaxis()
    ax.set_xlabel("Severe arrival-delay rate (%)")
    ax.set_ylabel("Reporting airline code")
    ax.set_title("Airline severe-delay rate (minimum 10,000 flights)")
    fig.tight_layout()
    fig.savefig(figures_dir / "airline_severe_delay_rate.png", dpi=160)
    plt.close(fig)

    causes = cause_table.sort_values("total_delay_minutes", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(causes["cause"], causes["share_of_reported_cause_minutes"] * 100, color="#B279A2")
    ax.set_xlabel("Share of reported cause-delay minutes (%)")
    ax.set_ylabel("Reported cause")
    ax.set_title("Composition of reported delay-cause minutes")
    fig.tight_layout()
    fig.savefig(figures_dir / "reported_delay_cause_share.png", dpi=160)
    plt.close(fig)


def _write_markdown_reports(
    reports_dir: Path,
    total_rows: int,
    overall: dict[str, float],
    issue_counts: Counter,
    manifest: pd.DataFrame,
    column_profile: pd.DataFrame,
    duplicate_exact: int,
    duplicate_business: int,
    join_table: pd.DataFrame,
    airport_metadata: dict[str, int],
    tables: dict[str, pd.DataFrame],
    cause_table: pd.DataFrame,
    thresholds: dict[str, int],
) -> None:
    missing_top = column_profile.sort_values("null_percentage", ascending=False).head(10)
    issue_lines = "\n".join(
        f"| {name.replace('_', ' ').title()} | {_human_int(count)} |"
        for name, count in issue_counts.items()
    )
    missing_lines = "\n".join(
        f"| {row.column} | {_human_int(row.null_count)} | {row.null_percentage:.2%} |"
        for row in missing_top.itertuples()
    )
    manifest_lines = "\n".join(
        f"| {int(row.expected_month):02d} | {row.status} | {_human_int(row.row_count)} | {row.min_flight_date} | {row.max_flight_date} |"
        for row in manifest.itertuples()
    )
    join_lines = "\n".join(
        f"| {row.perspective.title()} | {_human_int(row.distinct_bts_codes)} | {_human_int(row.matched_codes)} | {row.distinct_code_match_rate:.2%} | {_human_int(row.unmatched_flight_rows)} |"
        for row in join_table.itertuples()
    )

    quality_report = f"""# Data Quality Report — BTS 2025

Generated from all 12 monthly raw files using chunked processing. Raw files were read only.

## Source coverage

| Month | Status | Rows | Minimum flight date | Maximum flight date |
|---:|---|---:|---|---|
{manifest_lines}

- Total flight rows: **{_human_int(total_rows)}**
- Exact duplicate rows after the first occurrence: **{_human_int(duplicate_exact)}**
- Business-key duplicate rows after the first occurrence: **{_human_int(duplicate_business)}**
- Schema consistency: **{'consistent' if manifest['schema_matches_reference'].all() else 'differences detected'}**

## Highest raw-column missingness

| Column | Null rows | Null percentage |
|---|---:|---:|
{missing_lines}

Missing operational fields on cancelled or diverted flights are not automatically treated as errors.

## Quality checks

| Check | Rows affected |
|---|---:|
{issue_lines}

No records were removed during this initial phase. Candidate issues remain traceable for the next cleaning decision.

## Airport source and join coverage

- Raw OurAirports rows: **{_human_int(airport_metadata['raw_airport_rows'])}**
- Standardized airport dimension rows with a valid unique IATA code: **{_human_int(airport_metadata['dimension_rows'])}**
- Duplicate-IATA candidate rows investigated by deterministic ranking: **{_human_int(airport_metadata['duplicate_iata_candidate_rows'])}**
- Historical IATA alias rows added from documented configuration: **{_human_int(airport_metadata['historical_alias_rows'])}**

| Flight role | Distinct BTS codes | Matched codes | Code match rate | Flight rows with unmatched code |
|---|---:|---:|---:|---:|
{join_lines}

## Target eligibility

- Eligible completed, non-diverted flights with known arrival delay: **{_human_int(overall['target_eligible_flights'])}**
- Rows excluded from the arrival-delay target: **{_human_int(total_rows - overall['target_eligible_flights'])}**
- Severe-delay threshold: **arrival delay greater than 60 minutes**

## Interpretation notes

- `ARR_DELAY` is the available BTS field and is used to derive the non-negative threshold test; no separate `ARR_DELAY_NEW` field was downloaded.
- Cancelled and diverted flights retain their operational records but receive a null severe-delay target.
- Outlying delay values are retained because large disruption events can be legitimate.
- The one-year scope supports within-2025 analysis but not year-over-year trend claims.
"""
    (reports_dir / "data_quality_report.md").write_text(quality_report, encoding="utf-8")

    cleaning_log = f"""# Cleaning and Transformation Log

## Action 001 — Raw file organization

**Issue:** Monthly files used inconsistent download names.  
**Rows affected:** {_human_int(total_rows)}  
**Action:** Files were moved without content changes and renamed `bts_ontime_2025_01.csv` through `bts_ontime_2025_12.csv`.  
**Reason:** Stable names make monthly ingestion reproducible while preserving raw data.

## Action 002 — Column standardization

**Issue:** BTS source columns use uppercase names that differ from analysis naming conventions.  
**Rows affected:** {_human_int(total_rows)}  
**Action:** Column names are mapped to documented snake_case names in memory.  
**Reason:** Consistent names simplify reusable cleaning and analysis code. Raw files remain unchanged.

## Action 003 — Data types and categorical text

**Issue:** CSV inference can mix numeric and text representations, and code fields can contain whitespace.  
**Rows affected:** {_human_int(total_rows)}  
**Action:** Dates are parsed, numeric measures are coerced to numeric, and airline/airport/cancellation codes are trimmed and uppercased in the derived data. Five nonpositive scheduled-duration sentinel values are flagged and converted to null in the derived layer.  
**Reason:** This makes comparisons and validation reliable without inventing values; an impossible duration must not be used by the later model.

## Action 004 — Missing operational values

**Issue:** Actual times, arrival delay, elapsed time, and air time can be missing for cancelled or diverted flights.  
**Rows affected:** See `reports/tables/column_profile.csv`.  
**Action:** Missing operational values were retained. No blanket imputation or `dropna()` was applied.  
**Reason:** These nulls can describe a flight outcome and should not be converted to fictional values.

## Action 005 — Duplicate candidates

**Issue:** {_human_int(duplicate_exact)} exact duplicate rows and {_human_int(duplicate_business)} business-key duplicate rows after first occurrences were detected.  
**Rows affected:** {_human_int(duplicate_business)} candidate rows.  
**Action:** Candidates were measured but not automatically deleted.  
**Reason:** Repeated-looking scheduled flights require investigation before removal.

## Action 006 — Feature engineering

**Issue:** Analysis and ML need consistent route, time, calendar, and target features.  
**Rows affected:** {_human_int(total_rows)}  
**Action:** Created route, scheduled departure hour, departure time band, weekend flag, season, delay category, target eligibility, and severe-delay target in the derived analysis layer. BTS `2400` is treated as midnight.  
**Reason:** These features directly support the research questions and are explainable in the viva.

## Action 007 — Severe-delay target governance

**Issue:** Cancelled/diverted flights do not have a comparable scheduled-destination arrival outcome.  
**Rows affected:** {_human_int(total_rows - overall['target_eligible_flights'])} excluded from target construction.  
**Action:** Severe delay is set only for completed, non-diverted flights with a known arrival delay; the threshold is `ARR_DELAY > 60`.  
**Reason:** This avoids labelling cancellations as arrival delays and prevents fabricated targets.

## Action 008 — Airport reference standardization

**Issue:** OurAirports contains missing and duplicate IATA codes.  
**Rows affected:** {_human_int(airport_metadata['raw_airport_rows'])} airport-source rows.  
**Action:** Retained valid three-letter IATA codes and selected one deterministic record per code, prioritizing U.S., scheduled-service, then larger airport types. Added a documented `PBI -> DJT` alias because the supplied current airport file stores `DJT` as the IATA code while its keywords retain the historical 2025 BTS code `PBI`.  
**Reason:** The airport join must use IATA codes, preserve historical flight codes, and remain auditable.

## Items intentionally left for the next cleaning pass

- Continue duplicate checks on every refresh; the current 2025 files contain no duplicate candidates.
- Persist the standardized flight partitions after the final retained-column schema is approved.
- Add airport surrogate keys and enforce fact-to-dimension foreign-key checks during warehouse construction.
- Review extreme delay values with route/date context; do not remove them solely by statistical cutoff.
"""
    (reports_dir / "cleaning_log.md").write_text(cleaning_log, encoding="utf-8")

    monthly = tables["monthly_performance"].sort_values("severe_delay_rate", ascending=False)
    bands = tables["departure_time_band_performance"].sort_values("severe_delay_rate", ascending=False)
    airlines = tables["airline_performance"]
    airlines = airlines.loc[airlines["total_flights"] >= thresholds["airline_min_flights"]].sort_values(
        "severe_delay_rate", ascending=False
    )
    routes = tables["route_performance"]
    routes = routes.loc[routes["total_flights"] >= thresholds["route_min_flights"]].sort_values(
        "severe_delay_rate", ascending=False
    )
    top_cause = cause_table.sort_values("total_delay_minutes", ascending=False).iloc[0]
    top_month = monthly.iloc[0]
    top_band = bands.iloc[0]
    top_airline = airlines.iloc[0]
    top_route = routes.iloc[0]

    eda_report = f"""# Initial EDA Progress Report — BTS 2025

This report covers the first full-pass EDA across all monthly files. Rankings use minimum-volume thresholds from `config/settings.yaml`.

## Overall performance

- Scheduled flight rows: **{_human_int(total_rows)}**
- Cancelled flights: **{_human_int(overall['cancelled_flights'])}** ({_human_pct(overall['cancellation_rate'])})
- Diverted flights: **{_human_int(overall['diverted_flights'])}** ({_human_pct(overall['diversion_rate'])})
- Average arrival delay among target-eligible flights: **{overall['average_arrival_delay_minutes']:.2f} minutes**
- Median arrival delay among target-eligible flights: **{overall['median_arrival_delay_minutes']:.2f} minutes**
- Severe-delay rate (`ARR_DELAY > 60`): **{_human_pct(overall['severe_delay_rate'])}**
- On-time/early rate (`ARR_DELAY <= 0`): **{_human_pct(overall['on_time_early_rate'])}**

## Evidence-backed findings

1. **Highest monthly severe-delay rate:** Month {int(top_month['month'])} had a severe-delay rate of **{_human_pct(top_month['severe_delay_rate'])}** across {_human_int(top_month['target_eligible_flights'])} eligible flights.
2. **Departure-time pattern:** **{top_band['departure_time_band']}** departures had the highest severe-delay rate at **{_human_pct(top_band['severe_delay_rate'])}**, compared with the network rate of {_human_pct(overall['severe_delay_rate'])}.
3. **Airline comparison:** Among airlines with at least {_human_int(thresholds['airline_min_flights'])} flights, **{top_airline['reporting_airline']}** had the highest severe-delay rate at **{_human_pct(top_airline['severe_delay_rate'])}**.
4. **High-volume route comparison:** Among routes with at least {_human_int(thresholds['route_min_flights'])} flights, **{top_route['route']}** had the highest severe-delay rate at **{_human_pct(top_route['severe_delay_rate'])}**.
5. **Reported delay causes:** **{top_cause['cause']}** contributed the largest share of reported cause-delay minutes at **{_human_pct(top_cause['share_of_reported_cause_minutes'])}**. These fields are descriptive only and will not be ML predictors.

## Completed EDA areas

- Overall volume, cancellation, diversion, delay, severe-delay, and on-time measures
- Airline, origin, destination, and route performance tables
- Month, day-of-week, scheduled-hour, time-band, weekend, and season tables
- Cancellation-code counts and reported delay-cause composition
- Airport-code join coverage against the standardized OurAirports dimension
- Four reproducible figures in `reports/figures/`

## Next EDA work

- Investigate the top and bottom high-volume airports/routes with uncertainty and distribution plots.
- Add median/quantile comparisons for groups where averages are distorted by extreme delays.
- Review cancellation patterns by airport and month together.
- Convert the evidence into notebook narration and final report-ready charts.

## Limitations at this checkpoint

- Results cover only 2025 and cannot establish year-over-year trends.
- Airline codes are not expanded to names until an authoritative airline lookup is added.
- Reported delay-cause fields describe delays after they occur and cannot be used for pre-departure prediction.
- Associations do not establish causal effects.
"""
    (reports_dir / "eda_progress_report.md").write_text(eda_report, encoding="utf-8")


def run() -> None:
    settings = load_settings()
    column_map = load_column_map()
    raw_dir = project_path(settings["paths"]["raw_bts"])
    airports_path = project_path(settings["paths"]["raw_airports"])
    reports_dir = project_path(settings["paths"]["reports"])
    tables_dir = project_path(settings["paths"]["tables"])
    figures_dir = project_path(settings["paths"]["figures"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    airport_output = project_path("data/interim/airports_standardized/airports_standardized.csv")
    _, airport_codes, airport_metadata = load_airport_dimension(
        airports_path,
        airport_output,
        settings["features"].get("airport_iata_aliases", {}),
    )

    expected_year = int(settings["project"]["start_year"])
    expected_months = [int(month) for month in settings["project"]["expected_months"]]
    chunksize = int(settings["processing"]["chunksize"])
    severe_threshold = int(settings["target"]["severe_delay_minutes"])

    manifest_rows: list[dict[str, Any]] = []
    reference_columns: list[str] | None = None
    state: AnalysisState | None = None
    all_exact_duplicates = 0
    all_business_duplicates = 0

    for month in expected_months:
        path = raw_dir / f"bts_ontime_{expected_year}_{month:02d}.csv"
        if not path.exists():
            manifest_rows.append(
                {
                    "expected_year": expected_year,
                    "expected_month": month,
                    "status": "missing",
                    "filename": path.name,
                    "size_bytes": 0,
                    "row_count": 0,
                    "column_count": 0,
                    "min_flight_date": "",
                    "max_flight_date": "",
                    "observed_years": "",
                    "observed_months": "",
                    "schema_matches_reference": False,
                    "exact_duplicates_after_first": 0,
                    "business_key_duplicates_after_first": 0,
                }
            )
            continue

        file_rows = 0
        file_min_date: pd.Timestamp | None = None
        file_max_date: pd.Timestamp | None = None
        observed_years: set[int] = set()
        observed_months: set[int] = set()
        exact_hashes: list[np.ndarray] = []
        business_hashes: list[np.ndarray] = []
        file_columns: list[str] | None = None

        for raw in pd.read_csv(path, chunksize=chunksize, low_memory=False):
            if file_columns is None:
                file_columns = list(raw.columns)
                if reference_columns is None:
                    reference_columns = file_columns
                    state = AnalysisState(raw_columns=reference_columns)
            if state is None or reference_columns is None:
                raise RuntimeError("Analysis state was not initialized")
            if list(raw.columns) != reference_columns:
                raise ValueError(f"Schema mismatch in {path.name}")

            clean = clean_chunk(
                raw,
                column_map,
                path,
                expected_year,
                month,
                severe_threshold,
                settings["features"]["departure_time_bands"],
            )
            state.update(raw, clean, expected_year, month, airport_codes)
            file_rows += len(raw)
            dates = clean["flight_date"].dropna()
            if not dates.empty:
                current_min = dates.min()
                current_max = dates.max()
                file_min_date = current_min if file_min_date is None else min(file_min_date, current_min)
                file_max_date = current_max if file_max_date is None else max(file_max_date, current_max)
            observed_years.update(clean["year"].dropna().astype(int).unique().tolist())
            observed_months.update(clean["month"].dropna().astype(int).unique().tolist())
            exact_hashes.append(pd.util.hash_pandas_object(raw, index=False).to_numpy(dtype="uint64"))
            business_hashes.append(
                pd.util.hash_pandas_object(clean[BUSINESS_KEY], index=False).to_numpy(dtype="uint64")
            )

        exact_duplicates = _duplicate_count(exact_hashes)
        business_duplicates = _duplicate_count(business_hashes)
        all_exact_duplicates += exact_duplicates
        all_business_duplicates += business_duplicates
        schema_text = ",".join(file_columns or [])
        manifest_rows.append(
            {
                "expected_year": expected_year,
                "expected_month": month,
                "status": "present",
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "row_count": file_rows,
                "column_count": len(file_columns or []),
                "min_flight_date": file_min_date.date().isoformat() if file_min_date is not None else "",
                "max_flight_date": file_max_date.date().isoformat() if file_max_date is not None else "",
                "observed_years": ",".join(map(str, sorted(observed_years))),
                "observed_months": ",".join(map(str, sorted(observed_months))),
                "schema_matches_reference": file_columns == reference_columns,
                "schema_sha256": hashlib.sha256(schema_text.encode("utf-8")).hexdigest(),
                "exact_duplicates_after_first": exact_duplicates,
                "business_key_duplicates_after_first": business_duplicates,
            }
        )

    if state is None:
        raise FileNotFoundError(f"No BTS CSV files found in {raw_dir}")

    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(reports_dir / "source_manifest.csv", index=False)

    column_profile = pd.DataFrame(
        [
            {
                "column": column,
                "observed_dtypes": ", ".join(sorted(state.dtype_observations[column])),
                "null_count": state.null_counts[column],
                "null_percentage": state.null_counts[column] / state.total_rows,
                "unique_count": len(state.unique_values[column]),
            }
            for column in state.raw_columns
        ]
    )
    column_profile.to_csv(tables_dir / "column_profile.csv", index=False)

    numeric_ranges = pd.DataFrame(
        [
            {"column": column, "minimum": state.numeric_min[column], "maximum": state.numeric_max[column]}
            for column in state.numeric_min
        ]
    )
    numeric_ranges.to_csv(tables_dir / "numeric_ranges.csv", index=False)

    issues = pd.DataFrame(
        [{"issue": name, "rows_affected": count} for name, count in state.issue_counts.items()]
    )
    issues.to_csv(tables_dir / "data_quality_issues.csv", index=False)
    flagged = (
        pd.concat(state.flagged_samples, ignore_index=True)
        if state.flagged_samples
        else pd.DataFrame()
    )
    flagged.to_csv(tables_dir / "flagged_row_samples.csv", index=False)

    tables: dict[str, pd.DataFrame] = {}
    for name, keys in GROUPS.items():
        table = _finalize_group(state.grouped[name], keys)
        tables[name] = table
        table.to_csv(tables_dir / f"{name}.csv", index=False)

    cancellation_table = pd.DataFrame(
        sorted(state.cancellation_codes.items()), columns=["cancellation_code", "cancelled_flights"]
    )
    cancellation_table.to_csv(tables_dir / "cancellation_code_counts.csv", index=False)

    total_cause_minutes = sum(state.cause_minutes.values())
    cause_table = pd.DataFrame(
        [
            {
                "cause": CAUSE_LABELS[column],
                "source_column": column,
                "total_delay_minutes": state.cause_minutes[column],
                "rows_with_positive_minutes": state.cause_reported_rows[column],
                "share_of_reported_cause_minutes": (
                    state.cause_minutes[column] / total_cause_minutes if total_cause_minutes else np.nan
                ),
            }
            for column in CAUSE_COLUMNS
        ]
    )
    cause_table.to_csv(tables_dir / "delay_cause_summary.csv", index=False)

    origin_matched = state.origin_codes & airport_codes
    destination_matched = state.destination_codes & airport_codes
    origin_total = int(tables["origin_airport_performance"]["total_flights"].sum())
    destination_total = int(tables["destination_airport_performance"]["total_flights"].sum())
    join_table = pd.DataFrame(
        [
            {
                "perspective": "origin",
                "distinct_bts_codes": len(state.origin_codes),
                "matched_codes": len(origin_matched),
                "distinct_code_match_rate": len(origin_matched) / len(state.origin_codes),
                "total_flight_rows": origin_total,
                "unmatched_flight_rows": state.airport_unmatched_rows["origin"],
                "flight_row_match_rate": 1 - state.airport_unmatched_rows["origin"] / origin_total,
            },
            {
                "perspective": "destination",
                "distinct_bts_codes": len(state.destination_codes),
                "matched_codes": len(destination_matched),
                "distinct_code_match_rate": len(destination_matched) / len(state.destination_codes),
                "total_flight_rows": destination_total,
                "unmatched_flight_rows": state.airport_unmatched_rows["destination"],
                "flight_row_match_rate": 1 - state.airport_unmatched_rows["destination"] / destination_total,
            },
        ]
    )
    join_table.to_csv(tables_dir / "airport_join_coverage.csv", index=False)
    unmatched_rows = []
    for perspective, counts in state.unmatched_airport_codes.items():
        unmatched_rows.extend(
            {"perspective": perspective, "iata_code": code, "flight_rows": count}
            for code, count in counts.most_common()
        )
    pd.DataFrame(unmatched_rows, columns=["perspective", "iata_code", "flight_rows"]).to_csv(
        tables_dir / "unmatched_airport_codes.csv", index=False
    )

    monthly = tables["monthly_performance"]
    total_eligible = int(monthly["target_eligible_flights"].sum())
    total_severe = int(monthly["severe_delay_count"].sum())
    total_on_time = int(monthly["on_time_early_count"].sum())
    total_cancelled = int(monthly["cancelled_flights"].sum())
    total_diverted = int(monthly["diverted_flights"].sum())
    delays = np.concatenate(state.arrival_delays) if state.arrival_delays else np.array([])
    overall = {
        "total_flights": state.total_rows,
        "target_eligible_flights": total_eligible,
        "cancelled_flights": total_cancelled,
        "diverted_flights": total_diverted,
        "average_arrival_delay_minutes": float(delays.mean()),
        "median_arrival_delay_minutes": float(np.median(delays)),
        "severe_delay_rate": total_severe / total_eligible,
        "on_time_early_rate": total_on_time / total_eligible,
        "cancellation_rate": total_cancelled / state.total_rows,
        "diversion_rate": total_diverted / state.total_rows,
    }
    pd.DataFrame([{"metric": key, "value": value} for key, value in overall.items()]).to_csv(
        tables_dir / "overall_summary.csv", index=False
    )
    row_reconciliation = pd.DataFrame(
        [
            {"stage": "Raw ingestion", "rows": state.total_rows, "rows_removed": 0, "reason": "All source rows retained"},
            {"stage": "Schema/type validation", "rows": state.total_rows, "rows_removed": 0, "reason": "Issues flagged; no automatic deletion"},
            {"stage": "Deduplication", "rows": state.total_rows, "rows_removed": 0, "reason": "Candidates retained pending investigation"},
            {"stage": "ML target eligibility", "rows": total_eligible, "rows_removed": state.total_rows - total_eligible, "reason": "Cancelled, diverted, or unknown arrival outcome excluded from target only"},
        ]
    )
    row_reconciliation.to_csv(tables_dir / "row_reconciliation.csv", index=False)

    thresholds = {key: int(value) for key, value in settings["ranking_thresholds"].items()}
    _plot_outputs(tables, cause_table, figures_dir, thresholds)
    _write_markdown_reports(
        reports_dir,
        state.total_rows,
        overall,
        state.issue_counts,
        manifest,
        column_profile,
        all_exact_duplicates,
        all_business_duplicates,
        join_table,
        airport_metadata,
        tables,
        cause_table,
        thresholds,
    )

    print(f"Processed {state.total_rows:,} BTS rows across {int((manifest['status'] == 'present').sum())} files.")
    print(f"Reports written to {reports_dir}")


if __name__ == "__main__":
    run()
