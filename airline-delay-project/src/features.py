"""Small, readable transformations shared by the notebook and full-data ETL."""

import numpy as np
import pandas as pd

from src.clean import scheduled_hour


# Only these columns may enter X in the later ML notebook.
NUMERIC_FEATURES = [
    "month", "quarter", "day_of_week", "day_of_month", "is_weekend",
    "scheduled_dep_hour", "scheduled_arr_hour", "distance_miles",
    "scheduled_elapsed_minutes", "scheduled_elapsed_invalid",
    "dep_time_sin", "dep_time_cos", "origin_latitude_deg",
    "origin_longitude_deg", "destination_latitude_deg", "destination_longitude_deg",
]
CATEGORICAL_FEATURES = [
    "reporting_airline", "origin", "destination", "route",
    "departure_time_band", "season", "distance_band",
]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
ML_METADATA = ["flight_date", "source_file", "source_row_number", "dataset_split"]
BLOCKED_FEATURES = [
    "dep_time", "departure_delay_minutes", "arr_time", "arrival_delay_minutes",
    "actual_elapsed_minutes", "air_time_minutes", "cancelled", "diverted",
    "cancellation_code", "carrier_delay_minutes", "weather_delay_minutes",
    "nas_delay_minutes", "security_delay_minutes", "late_aircraft_delay_minutes",
    "delay_category", "ml_target_eligible", "completed_missing_arrival_delay",
    "severe_delay",
]


def add_features(clean, settings):
    flights = clean.copy()
    flights["scheduled_arr_hour"] = scheduled_hour(flights["crs_arr_time"])
    # Midnight is 0 minutes. No subtraction of local origin/destination clocks:
    # their time zones differ, so duration comes from CRS_ELAPSED_TIME instead.
    minutes = flights["scheduled_dep_hour"] * 60.0 + flights["crs_dep_time"].mod(100)
    angle = 2 * np.pi * minutes.astype(float) / (24 * 60)
    flights["dep_time_sin"] = np.sin(angle)
    flights["dep_time_cos"] = np.cos(angle)
    flights["distance_band"] = pd.cut(
        flights["distance_miles"], bins=[0, 500, 1500, np.inf],
        labels=["Short", "Medium", "Long"],
    ).astype("string")
    flights["dataset_split"] = chronological_split(flights["flight_date"], settings)
    return flights


def chronological_split(dates, settings):
    dates = pd.to_datetime(dates)
    model = settings["model"]
    start = pd.Timestamp(int(settings["project"]["start_year"]), 1, 1)
    train_end = pd.Timestamp(model["train_end_date"])
    validation_end = pd.Timestamp(model["validation_end_date"])
    test_end = pd.Timestamp(model["test_end_date"])
    if not start <= train_end < validation_end < test_end:
        raise ValueError("Chronological split boundaries must be increasing.")
    if not dates.between(start, test_end).all():
        raise ValueError("Missing or out-of-period flight date.")
    split = pd.Series("test", index=dates.index, dtype="string")
    split.loc[dates.le(validation_end)] = "validation"
    split.loc[dates.le(train_end)] = "train"
    return split


def join_airports(flights, airports):
    """Two left joins preserve flights; validate prevents row multiplication."""
    keep = ["iata_code", "source_iata_code", "ident", "name", "iso_region",
            "latitude_deg", "longitude_deg"]
    result = flights.copy()
    for role in ["origin", "destination"]:
        lookup = airports[keep].rename(columns={
            column: role if column == "iata_code" else role + "_" + column
            for column in keep
        })
        result = result.merge(lookup, on=role, how="left", validate="many_to_one", indicator=True)
        if result["_merge"].ne("both").any():
            missing = result.loc[result["_merge"].ne("both"), role].unique()
            raise ValueError(f"Unmatched {role} airport codes: {missing}")
        result = result.drop(columns="_merge")
        # Keep code types stable across pandas merges and Parquet round trips.
        result[role] = result[role].astype("string")
    assert len(result) == len(flights)
    return result


def select_ml_rows(flights):
    assert not set(MODEL_FEATURES) & set(BLOCKED_FEATURES)
    eligible = flights["ml_target_eligible"].eq(1)
    ml = flights.loc[eligible, ML_METADATA + MODEL_FEATURES + ["severe_delay"]].copy()
    assert ml["severe_delay"].isin([0, 1]).all()
    return ml
