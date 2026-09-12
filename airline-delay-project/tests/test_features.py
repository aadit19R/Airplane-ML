from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.clean import clean_chunk, scheduled_hour, departure_time_band
from src.config import load_column_map, load_settings
from src.etl import validate_month
from src.features import (
    add_features, chronological_split, join_airports, select_ml_rows,
    MODEL_FEATURES, BLOCKED_FEATURES,
)


def example_raw():
    # A small synthetic fixture: includes boundary labels, status exclusions,
    # bad duration, blank code, invalid time, and a numeric parse failure.
    frame = pd.DataFrame({column: [None] * 8 for column in load_column_map()})
    constants = {
        "YEAR": 2025, "QUARTER": 1, "MONTH": 1, "DAY_OF_MONTH": 1,
        "DAY_OF_WEEK": 3, "FL_DATE": "1/1/2025 12:00:00 AM",
        "OP_UNIQUE_CARRIER": " aa ", "ORIGIN": " jfk ", "DEST": "lax",
        "CRS_DEP_TIME": 600, "CRS_ARR_TIME": 900,
        "CANCELLED": 0, "DIVERTED": 0, "DISTANCE": 2475,
        "CRS_ELAPSED_TIME": 180,
    }
    for column, value in constants.items():
        frame[column] = value
    frame["OP_CARRIER_FL_NUM"] = range(1, 9)
    frame["ARR_DELAY"] = [-5, 0, 15, 60, 61, 100, None, 30]
    frame.loc[5, "CANCELLED"] = 1
    frame.loc[7, "DIVERTED"] = 1
    frame.loc[4, "CRS_ELAPSED_TIME"] = -60
    frame.loc[0, "CANCELLATION_CODE"] = " "
    return frame


def example_clean():
    return clean_chunk(example_raw(), load_column_map(), Path("fixture.csv"), 2025, 1)


def test_target_boundaries_and_unknown_outcomes():
    clean = example_clean()
    assert clean["severe_delay"].iloc[:5].tolist() == [0, 0, 0, 0, 1]
    assert clean["severe_delay"].iloc[5:].isna().all()
    assert clean["completed_missing_arrival_delay"].sum() == 1
    assert clean.loc[4, "scheduled_elapsed_invalid"] == 1
    assert pd.isna(clean.loc[4, "scheduled_elapsed_minutes"])
    assert clean["reporting_airline"].eq("AA").all()
    assert clean["route"].eq("JFK-LAX").all()
    assert pd.isna(clean.loc[0, "cancellation_code"])


def test_invalid_and_missing_clock_values_do_not_become_real_hours():
    values = pd.Series([2359, 2400, 2401, 1260, -1, 600.5, "bad", None])
    hours = scheduled_hour(values)
    assert hours.iloc[:2].tolist() == [23, 0]
    assert hours.iloc[2:].isna().all()
    bands = departure_time_band(hours)
    assert bands.iloc[:2].tolist() == ["Night", "Late Night"]
    assert bands.iloc[2:].isna().all()
    assert departure_time_band(pd.Series([7]), [{"name": "Custom", "start_hour": 0, "end_hour": 23}]).iloc[0] == "Custom"


def test_numeric_mismatch_is_visible_and_missing_time_does_not_crash():
    raw = example_raw()
    raw["DISTANCE"] = raw["DISTANCE"].astype(object)
    raw.loc[0, "DISTANCE"] = "not numeric"
    raw.loc[1, "CRS_DEP_TIME"] = np.nan
    clean = clean_chunk(raw, load_column_map(), Path("fixture.csv"), 2025, 1)
    assert pd.isna(clean.loc[0, "distance_miles"])
    assert pd.isna(clean.loc[1, "departure_time_band"])
    with pytest.raises(ValueError):
        validate_month(clean, 2025, 1)


def test_cyclic_midnight_and_distance_boundaries():
    clean = example_clean()
    clean["crs_dep_time"] = [2359, 0, 1200, 2400, 600, 600, 600, 600]
    clean["scheduled_dep_hour"] = scheduled_hour(clean["crs_dep_time"])
    clean["distance_miles"] = [0, 500, 501, 1500, 1501, 100, 100, 100]
    featured = add_features(clean, load_settings())
    assert pd.isna(featured.loc[0, "distance_band"])
    assert featured["distance_band"].iloc[1:5].tolist() == ["Short", "Medium", "Medium", "Long"]
    assert abs(featured.loc[0, "dep_time_sin"] - featured.loc[1, "dep_time_sin"]) < 0.005
    assert featured.loc[3, "dep_time_cos"] == pytest.approx(1)
    assert featured.loc[2, "dep_time_cos"] == pytest.approx(-1)


def airport_fixture():
    return pd.DataFrame({"iata_code": ["JFK", "LAX"], "source_iata_code": ["JFK", "LAX"],
                         "ident": ["KJFK", "KLAX"], "name": ["Example origin", "Example destination"],
                         "iso_region": ["US-NY", "US-CA"], "latitude_deg": [40.6, 33.9],
                         "longitude_deg": [-73.8, -118.4]})


def test_joins_preserve_rows_and_reject_ambiguous_or_missing_lookup():
    clean = example_clean()
    airports = airport_fixture()
    joined = join_airports(clean, airports)
    assert len(joined) == len(clean)
    assert joined["destination_ident"].eq("KLAX").all()
    with pytest.raises(pd.errors.MergeError):
        join_airports(clean, pd.concat([airports, airports.iloc[:1]]))
    with pytest.raises(ValueError, match="Unmatched destination"):
        join_airports(clean, airports.iloc[:1])


def test_split_boundaries_and_reject_outside_dates():
    dates = pd.Series(pd.to_datetime(["2025-08-31", "2025-09-01", "2025-10-31", "2025-11-01"]))
    assert chronological_split(dates, load_settings()).tolist() == ["train", "validation", "validation", "test"]
    for value in [None, "2024-12-31", "2026-01-01"]:
        with pytest.raises(ValueError):
            chronological_split(pd.Series([value]), load_settings())


def test_ml_output_excludes_outcomes_and_keeps_valid_missing_predictor():
    clean = example_clean()
    clean["source_row_number"] = np.arange(1, len(clean) + 1)
    enriched = join_airports(add_features(clean, load_settings()), airport_fixture())
    ml = select_ml_rows(enriched)
    assert len(ml) == 5
    assert not set(MODEL_FEATURES) & set(BLOCKED_FEATURES)
    assert not (set(BLOCKED_FEATURES) - {"severe_delay"}) & set(ml.columns)
    assert ml.loc[4, "severe_delay"] == 1
    assert pd.isna(ml.loc[4, "scheduled_elapsed_minutes"])


def test_calendar_disagreement_stops_validation():
    clean = example_clean().iloc[:5].copy()
    clean.loc[0, "day_of_week"] = 7
    with pytest.raises(ValueError, match="day_of_week"):
        validate_month(clean, 2025, 1)


def test_ml_parquet_round_trip_preserves_code_types_and_values(tmp_path):
    clean = example_clean()
    clean["source_row_number"] = np.arange(1, len(clean) + 1)
    ml = select_ml_rows(join_airports(add_features(clean, load_settings()), airport_fixture()))
    path = tmp_path / "ml.parquet"
    ml.to_parquet(path, index=False)
    pd.testing.assert_frame_equal(pd.read_parquet(path), ml.reset_index(drop=True))
