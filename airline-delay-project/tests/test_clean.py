from pathlib import Path

import pandas as pd

from src.clean import clean_chunk, scheduled_hour


COLUMN_MAP = {
    "YEAR": "year",
    "QUARTER": "quarter",
    "MONTH": "month",
    "DAY_OF_MONTH": "day_of_month",
    "DAY_OF_WEEK": "day_of_week",
    "FL_DATE": "flight_date",
    "OP_UNIQUE_CARRIER": "reporting_airline",
    "OP_CARRIER_FL_NUM": "flight_number",
    "ORIGIN": "origin",
    "DEST": "destination",
    "CRS_DEP_TIME": "crs_dep_time",
    "DEP_TIME": "dep_time",
    "DEP_DELAY": "departure_delay_minutes",
    "CRS_ARR_TIME": "crs_arr_time",
    "ARR_TIME": "arr_time",
    "ARR_DELAY": "arrival_delay_minutes",
    "CANCELLED": "cancelled",
    "CANCELLATION_CODE": "cancellation_code",
    "DIVERTED": "diverted",
    "CRS_ELAPSED_TIME": "scheduled_elapsed_minutes",
    "ACTUAL_ELAPSED_TIME": "actual_elapsed_minutes",
    "AIR_TIME": "air_time_minutes",
    "DISTANCE": "distance_miles",
    "CARRIER_DELAY": "carrier_delay_minutes",
    "WEATHER_DELAY": "weather_delay_minutes",
    "NAS_DELAY": "nas_delay_minutes",
    "SECURITY_DELAY": "security_delay_minutes",
    "LATE_AIRCRAFT_DELAY": "late_aircraft_delay_minutes",
}


def test_scheduled_hour_handles_midnight_and_invalid_minutes():
    values = pd.Series([5, 559, 600, 2359, 2400, 1260, None])
    actual = scheduled_hour(values).tolist()
    assert actual[:5] == [0, 5, 6, 23, 0]
    assert pd.isna(actual[5])
    assert pd.isna(actual[6])


def test_target_is_null_for_cancelled_and_diverted_flights():
    raw = pd.DataFrame(
        {
            "YEAR": [2025, 2025, 2025, 2025],
            "QUARTER": [1] * 4,
            "MONTH": [1] * 4,
            "DAY_OF_MONTH": [1] * 4,
            "DAY_OF_WEEK": [3] * 4,
            "FL_DATE": ["1/1/2025 12:00:00 AM"] * 4,
            "OP_UNIQUE_CARRIER": ["AA"] * 4,
            "OP_CARRIER_FL_NUM": [1, 2, 3, 4],
            "ORIGIN": ["JFK"] * 4,
            "DEST": ["LAX"] * 4,
            "CRS_DEP_TIME": [600] * 4,
            "DEP_TIME": [610, None, 610, 610],
            "DEP_DELAY": [10, None, 10, 10],
            "CRS_ARR_TIME": [900] * 4,
            "ARR_TIME": [1010, None, None, 910],
            "ARR_DELAY": [70, None, None, 10],
            "CANCELLED": [0, 1, 0, 0],
            "CANCELLATION_CODE": [None, "A", None, None],
            "DIVERTED": [0, 0, 1, 0],
            "CRS_ELAPSED_TIME": [180] * 4,
            "ACTUAL_ELAPSED_TIME": [200, None, None, 180],
            "AIR_TIME": [160, None, None, 150],
            "DISTANCE": [2475] * 4,
            "CARRIER_DELAY": [70, None, None, None],
            "WEATHER_DELAY": [0, None, None, None],
            "NAS_DELAY": [0, None, None, None],
            "SECURITY_DELAY": [0, None, None, None],
            "LATE_AIRCRAFT_DELAY": [0, None, None, None],
        }
    )
    cleaned = clean_chunk(raw, COLUMN_MAP, Path("sample.csv"), 2025, 1)
    assert cleaned["severe_delay"].tolist()[0] == 1
    assert pd.isna(cleaned["severe_delay"].tolist()[1])
    assert pd.isna(cleaned["severe_delay"].tolist()[2])
    assert cleaned["severe_delay"].tolist()[3] == 0
    assert cleaned["route"].tolist()[0] == "JFK-LAX"


def test_nonpositive_scheduled_duration_is_flagged_and_nulled():
    raw = pd.DataFrame(
        {
            "YEAR": [2025], "QUARTER": [1], "MONTH": [1], "DAY_OF_MONTH": [1],
            "DAY_OF_WEEK": [3], "FL_DATE": ["1/1/2025 12:00:00 AM"],
            "OP_UNIQUE_CARRIER": ["AA"], "OP_CARRIER_FL_NUM": [1],
            "ORIGIN": ["JFK"], "DEST": ["LAX"], "CRS_DEP_TIME": [600],
            "DEP_TIME": [610], "DEP_DELAY": [10], "CRS_ARR_TIME": [900],
            "ARR_TIME": [910], "ARR_DELAY": [10], "CANCELLED": [0],
            "CANCELLATION_CODE": [None], "DIVERTED": [0], "CRS_ELAPSED_TIME": [-99],
            "ACTUAL_ELAPSED_TIME": [300], "AIR_TIME": [270], "DISTANCE": [2475],
            "CARRIER_DELAY": [None], "WEATHER_DELAY": [None], "NAS_DELAY": [None],
            "SECURITY_DELAY": [None], "LATE_AIRCRAFT_DELAY": [None],
        }
    )
    cleaned = clean_chunk(raw, COLUMN_MAP, Path("sample.csv"), 2025, 1)
    assert cleaned.loc[0, "scheduled_elapsed_invalid"] == 1
    assert pd.isna(cleaned.loc[0, "scheduled_elapsed_minutes"])
