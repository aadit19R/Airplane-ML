from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


CODE_COLUMNS = ["reporting_airline", "origin", "destination", "cancellation_code"]
NUMERIC_COLUMNS = [
    "year",
    "quarter",
    "month",
    "day_of_month",
    "day_of_week",
    "flight_number",
    "crs_dep_time",
    "dep_time",
    "departure_delay_minutes",
    "crs_arr_time",
    "arr_time",
    "arrival_delay_minutes",
    "cancelled",
    "diverted",
    "scheduled_elapsed_minutes",
    "actual_elapsed_minutes",
    "air_time_minutes",
    "distance_miles",
    "carrier_delay_minutes",
    "weather_delay_minutes",
    "nas_delay_minutes",
    "security_delay_minutes",
    "late_aircraft_delay_minutes",
]


def scheduled_hour(values: pd.Series) -> pd.Series:
    """Convert BTS HHMM values to a nullable hour; treat 2400 as midnight."""
    numeric = pd.to_numeric(values, errors="coerce").round()
    minutes = numeric.mod(100)
    valid = numeric.between(0, 2359) & minutes.between(0, 59)
    hour = (numeric // 100).where(valid)
    hour = hour.mask(numeric.eq(2400), 0)
    return hour.astype("Int8")


def departure_time_band(hours: pd.Series) -> pd.Series:
    conditions = [
        hours.between(0, 5),
        hours.between(6, 10),
        hours.between(11, 15),
        hours.between(16, 20),
        hours.between(21, 23),
    ]
    labels = ["Late Night", "Morning", "Midday", "Evening", "Night"]
    result = np.select(conditions, labels, default=None)
    return pd.Series(result, index=hours.index, dtype="string")


def clean_chunk(
    raw: pd.DataFrame,
    column_map: dict[str, str],
    source_file: Path,
    source_year: int,
    source_month: int,
    severe_delay_minutes: int = 60,
) -> pd.DataFrame:
    """Standardize types and create documented features without dropping rows."""
    frame = raw.rename(columns=column_map).copy()

    for column in CODE_COLUMNS:
        if column in frame:
            frame[column] = frame[column].astype("string").str.strip().str.upper()

    for column in NUMERIC_COLUMNS:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    invalid_scheduled_elapsed = frame["scheduled_elapsed_minutes"].le(0).fillna(False)
    frame["scheduled_elapsed_invalid"] = invalid_scheduled_elapsed.astype("Int8")
    frame.loc[invalid_scheduled_elapsed, "scheduled_elapsed_minutes"] = np.nan

    frame["flight_date"] = pd.to_datetime(
        frame["flight_date"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    )
    frame["source_file"] = source_file.name
    frame["source_year"] = source_year
    frame["source_month"] = source_month

    frame["route"] = frame["origin"].str.cat(frame["destination"], sep="-")
    frame["scheduled_dep_hour"] = scheduled_hour(frame["crs_dep_time"])
    frame["departure_time_band"] = departure_time_band(frame["scheduled_dep_hour"])
    frame["is_weekend"] = frame["day_of_week"].isin([6, 7]).astype("Int8")
    frame["season"] = frame["month"].map(
        {
            12: "Winter",
            1: "Winter",
            2: "Winter",
            3: "Spring",
            4: "Spring",
            5: "Spring",
            6: "Summer",
            7: "Summer",
            8: "Summer",
            9: "Fall",
            10: "Fall",
            11: "Fall",
        }
    ).astype("string")

    eligible = (
        frame["cancelled"].eq(0)
        & frame["diverted"].eq(0)
        & frame["arrival_delay_minutes"].notna()
    )
    frame["ml_target_eligible"] = eligible.astype("Int8")

    severe = pd.Series(pd.NA, index=frame.index, dtype="Int8")
    severe.loc[eligible] = (
        frame.loc[eligible, "arrival_delay_minutes"] > severe_delay_minutes
    ).astype("Int8")
    frame["severe_delay"] = severe

    delay_category = pd.Series(pd.NA, index=frame.index, dtype="string")
    arrival_delay = frame["arrival_delay_minutes"]
    delay_category.loc[eligible & arrival_delay.le(0)] = "On Time / Early"
    delay_category.loc[eligible & arrival_delay.between(1, 15)] = "Minor Delay"
    delay_category.loc[eligible & arrival_delay.between(16, severe_delay_minutes)] = (
        "Moderate Delay"
    )
    delay_category.loc[eligible & arrival_delay.gt(severe_delay_minutes)] = "Severe Delay"
    frame["delay_category"] = delay_category
    return frame


def quality_issue_counts(frame: pd.DataFrame, expected_year: int, expected_month: int) -> dict[str, int]:
    """Count quality issues; counts are diagnostic and do not remove rows."""
    crs_dep = frame["crs_dep_time"]
    crs_dep_minutes = crs_dep.mod(100)
    invalid_crs_dep = ~(
        (crs_dep.between(0, 2359) & crs_dep_minutes.between(0, 59))
        | crs_dep.eq(2400)
    )
    return {
        "unexpected_year": int((frame["year"].ne(expected_year) | frame["year"].isna()).sum()),
        "source_month_mismatch": int((frame["month"].ne(expected_month) | frame["month"].isna()).sum()),
        "missing_flight_date": int(frame["flight_date"].isna().sum()),
        "flight_date_period_mismatch": int(
            (
                frame["flight_date"].notna()
                & (
                    frame["flight_date"].dt.year.ne(expected_year)
                    | frame["flight_date"].dt.month.ne(expected_month)
                )
            ).sum()
        ),
        "invalid_origin_code": int((~frame["origin"].fillna("").str.fullmatch(r"[A-Z]{3}")).sum()),
        "invalid_destination_code": int(
            (~frame["destination"].fillna("").str.fullmatch(r"[A-Z]{3}")).sum()
        ),
        "nonpositive_distance": int(frame["distance_miles"].le(0).fillna(False).sum()),
        "invalid_cancelled_flag": int((~frame["cancelled"].isin([0, 1])).sum()),
        "invalid_diverted_flag": int((~frame["diverted"].isin([0, 1])).sum()),
        "invalid_scheduled_departure_time": int((invalid_crs_dep | crs_dep.isna()).sum()),
        "nonpositive_scheduled_elapsed_time": int(frame["scheduled_elapsed_invalid"].eq(1).sum()),
        "negative_actual_elapsed_time": int(
            frame["actual_elapsed_minutes"].lt(0).fillna(False).sum()
        ),
        "negative_air_time": int(frame["air_time_minutes"].lt(0).fillna(False).sum()),
        "completed_missing_arrival_delay": int(
            (
                frame["cancelled"].eq(0)
                & frame["diverted"].eq(0)
                & frame["arrival_delay_minutes"].isna()
            ).sum()
        ),
        "cancelled_with_arrival_delay": int(
            (frame["cancelled"].eq(1) & frame["arrival_delay_minutes"].notna()).sum()
        ),
    }
