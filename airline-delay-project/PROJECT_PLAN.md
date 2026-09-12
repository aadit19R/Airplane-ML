# Airline Flight Delay Prediction & Operational Performance Analysis
## Codex CLI Project Brief / Master Plan

> **Purpose of this file:** This is the current source of truth for project status, decisions, completed work, and remaining implementation.
>
> **Project status:** Cleaning, EDA, and transformation complete; warehouse and model training are next
> **Primary domain:** Airline operations, flight delays, cancellations, airports  
> **Primary dataset:** U.S. Bureau of Transportation Statistics (BTS) Reporting Carrier On-Time Performance  
> **Data period:** January–December 2025 (one full calendar year)  
> **Supporting dataset:** OurAirports `airports.csv`  
> **Optional extension:** Weather data — add only after the core warehouse, ML, and dashboard are complete

## Current checkpoint — 13 September 2026

- Cleaning, transformation, airport enrichment, feature engineering, and EDA
  are complete and documented.
- All 7,001,619 operational rows were retained; 6,879,484 eligible rows were
  exported for the severe-arrival-delay model.
- Twelve monthly Parquet files exist in each cleaned, enriched, and ML layer.
- Both airport joins resolve every flight row. Five invalid scheduled durations
  are flagged, and one completed flight with an unknown arrival outcome is
  excluded from the target.
- The frozen chronological split contains 4,592,366 training rows (Jan–Aug),
  1,159,898 validation rows (Sep–Oct), and 1,127,220 test rows (Nov–Dec).
- `01_beginner_eda.ipynb` and `02_feature_engineering.ipynb` execute without
  errors, and all 12 current tests pass.
- No model or learned preprocessing has been fitted. The next stages are the
  SQLite warehouse, baseline and three classifiers, model interpretation, and
  Power BI exports.

Reproduce the completed stage with `python scripts/run_etl.py`, followed by
`python scripts/execute_notebooks.py`. Detailed evidence is in
`reports/cleaning_log.md`, `reports/feature_dictionary.md`, and
`reports/transformation_report.md`.

---

# 1. Project Title

**Airline Flight Delay Prediction and Operational Performance Analysis Using Data Wrangling, ETL, Machine Learning, and Power BI**

---

# 2. Project Objective

The project will use large-scale real-world airline flight data to answer two broad questions:

1. **Operational analysis:**  
   Which airlines, airports, routes, dates, and departure-time periods experience the highest delays and cancellations?

2. **Machine learning:**  
   Can pre-departure information predict whether an eligible flight will
   experience a **severe arrival delay**, and which factors matter most?

The complete project must demonstrate:

- Data extraction
- Data cleaning
- Data transformation
- Joining multiple sources
- Feature engineering
- Data quality validation
- Persistent storage / SQL
- Dimensional modelling
- Exploratory analysis
- Machine learning
- Model comparison
- Power BI dashboard preparation
- Documentation of insights, assumptions, and limitations

The project must remain understandable enough to explain clearly in a college viva.

---

# 3. Core Research Questions

## Primary Question

**Can we predict severe arrival delays of more than 60 minutes for completed,
non-diverted U.S. flights using only pre-flight information—airline, route,
scheduled time, calendar features, distance, scheduled duration, and static
airport location—and which factors matter most?**

## Secondary Questions

1. **Does the machine-learning model identify severe delays better than a simple baseline when evaluated on future flights?**

   Compare Logistic Regression, Decision Tree, and Random Forest against an
   always-predict-non-severe baseline on the validation set. Select the model
   there, then compare only the selected model and baseline on the untouched
   November–December test set. Use recall, precision, F1, PR-AUC, ROC-AUC, and
   balanced accuracy—not accuracy alone.

2. **Which pre-flight features contribute most to the model's predictions of severe flight delays?**

   Examine model coefficients and feature importance for airline, route,
   airports, scheduled departure time, derived calendar features, season,
   distance, and scheduled duration. Compare these model explanations with the
   patterns found during EDA, while avoiding causal claims. The raw flight date
   is split metadata rather than a model predictor.

3. **For which flights does the selected model make the most mistakes?**

   Analyse false negatives and false positives by airline, origin airport,
   destination airport, route, month, season, and departure-time band. Determine
   whether errors are concentrated in particular operational groups or periods.

4. **Which probability threshold provides the most useful balance between detecting severe delays and avoiding false alarms?**

   Use the validation set's precision-recall results to select a threshold under
   a stated rule, such as maximizing F1 or achieving a required recall. Apply
   that threshold once to the final test set and report its practical effect.

## 3.1 Literature-derived problem definition

A review of ten relevant flight-delay prediction papers identified twenty paper-level drawbacks. After repeated drawbacks were consolidated, three research gaps were selected because they are both important and achievable with this project's data:

1. **Prediction-time realism:** prevent target leakage by using only information available before scheduled departure.
2. **Broad and time-aware evaluation:** use the full 2025 U.S. domestic network in the project data and test on chronologically later months rather than a random holdout.
3. **Imbalance-aware evaluation:** preserve the natural severe-delay rate in validation/testing and report minority-sensitive metrics instead of accuracy alone.

**Problem definition:** Existing studies may report strong flight-delay performance using restricted airport/route samples, random or artificially balanced evaluations, or variables that are unavailable before the outcome. This project will therefore develop and evaluate an explainable, leakage-controlled, and imbalance-aware machine-learning pipeline to predict whether a completed, non-diverted domestic U.S. flight with a known arrival outcome will arrive more than 60 minutes late, using only pre-departure information and a chronological future-month holdout.

The complete paper-by-paper review, gap matrix, evidence labels, selected-gap rationale, and references are documented in `reports/literature_review_and_research_gaps.md`.

---

# 4. Dataset Sources

## 4.1 Main Dataset — BTS Reporting Carrier On-Time Performance

**Provider:** U.S. Bureau of Transportation Statistics (BTS), TranStats  
**Dataset:** Reporting Carrier On-Time Performance (1987–present)  
**Frequency:** Monthly  
**Project period:** January through December 2025

Official dataset profile:

https://www.transtats.bts.gov/TableInfo.asp?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ

Use the **Download** option on the BTS page to obtain individual flight-level data.

### Files to Obtain

Use all monthly flight files for **2025: January–December**.

That is **12 monthly raw files** in total. One full year is sufficient for the
course requirements and still contains millions of individual flight records.

Do **not** depend on the original downloaded filenames. After download, rename them into the following project convention:

```text
bts_ontime_2025_01.csv
...
bts_ontime_2025_12.csv
```

Do not modify the contents of the raw files.

---

## 4.2 Supporting Dataset — OurAirports

**Provider:** OurAirports  
**Dataset:** `airports.csv`

Official download page:

https://ourairports.com/data/

Download:

```text
airports.csv
```

Store it as:

```text
data/raw/airports/airports.csv
```

### Why This Dataset Is Included

The BTS flight data contains airport codes, while OurAirports provides descriptive airport metadata such as:

- airport name
- municipality
- region
- country
- latitude
- longitude
- elevation
- airport type

This gives the project a genuine **multi-source merge/join**.

---

# 5. BTS Columns to Download / Retain

The exact available fields may change slightly in the BTS interface. Use the closest official BTS field name where necessary.

## 5.1 Time / Date

Prefer retaining:

```text
Year
Quarter
Month
DayofMonth
DayOfWeek
FlightDate
```

## 5.2 Airline

```text
Reporting_Airline
DOT_ID_Reporting_Airline
IATA_CODE_Reporting_Airline
Tail_Number
Flight_Number_Reporting_Airline
```

If one of the airline identifier columns is unavailable, retain the available reporting-carrier code plus airline ID.

## 5.3 Origin Airport

```text
OriginAirportID
Origin
OriginCityName
OriginState
OriginStateName
```

## 5.4 Destination Airport

```text
DestAirportID
Dest
DestCityName
DestState
DestStateName
```

## 5.5 Departure Information

```text
CRSDepTime
DepTime
DepDelay
DepDelayMinutes
DepDel15
DepartureDelayGroups
```

## 5.6 Arrival Information

```text
CRSArrTime
ArrTime
ArrDelay
ArrDelayMinutes
ArrDel15
ArrivalDelayGroups
```

## 5.7 Flight Status

```text
Cancelled
CancellationCode
Diverted
```

## 5.8 Duration and Distance

```text
CRSElapsedTime
ActualElapsedTime
AirTime
Flights
Distance
DistanceGroup
```

## 5.9 Reported Delay Causes

```text
CarrierDelay
WeatherDelay
NASDelay
SecurityDelay
LateAircraftDelay
```

### Important

The delay-cause columns are useful for **descriptive analysis**, but they must **NOT** be used as features in the pre-departure severe-delay prediction model because they are only known after the delay has occurred.

---

# 6. Scope Decision

## Core Project Scope

Use:

```text
BTS 2025 (January–December)
       +
OurAirports airports.csv
```

### Outside the Core Scope

Do not add external weather data until the core warehouse, ML comparison, and
dashboard are complete.

Weather can be added later only as a documented extension if:

- the core project is complete,
- join quality is acceptable,
- the team has enough time,
- the additional source clearly improves the model or analysis.

---

# 7. Repository Structure and Planned Additions

Current files and planned additions follow. Planned items are labelled.

```text
airline-delay-project/
│
├── README.md
├── PROJECT_PLAN.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── config/
│   ├── settings.yaml
│   └── column_map.yaml
│
├── data/
│   ├── raw/
│   │   ├── bts/
│   │   │   └── 2025/
│   │   │
│   │   └── airports/
│   │       └── airports.csv
│   │
│   ├── interim/
│   │   ├── flights_standardized/
│   │   └── airports_standardized/
│   │
│   ├── processed/
│   │   ├── flights_wrangled.parquet
│   │   ├── flights_ml.parquet
│   │   └── powerbi/
│   │
│   └── samples/
│
├── database/
│   ├── airline_dw.sqlite
│   └── schema.sql
│
├── notebooks/
│   ├── 01_beginner_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_machine_learning.ipynb          # planned
│   └── 04_model_interpretation.ipynb      # planned
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── clean.py
│   ├── features.py
│   ├── initial_analysis.py
│   ├── etl.py
│   ├── warehouse.py                       # planned
│   ├── model.py                           # planned
│   └── export_powerbi.py                  # planned
│
├── scripts/
│   ├── run_initial_analysis.py
│   ├── run_etl.py
│   ├── execute_notebooks.py
│   ├── build_database.py                  # planned
│   ├── train_models.py                    # planned
│   └── export_powerbi.py                  # planned
│
├── models/
│   ├── trained/
│   └── metrics/
│
├── reports/
│   ├── figures/
│   ├── tables/
│   ├── cleaning_log.md
│   ├── data_quality_report.md
│   ├── model_results.md
│   └── insights.md
│
└── tests/
    ├── test_cleaning.py
    ├── test_transformations.py
    ├── test_validation.py
    └── test_features.py
```

---

# 8. Technical Stack

Use a simple, explainable stack.

## Core

- Python 3.11+
- Jupyter Notebook
- pandas
- NumPy
- scikit-learn
- matplotlib
- SQL / SQLite
- Power BI

## Recommended for Large Data

Because the 2025 files contain millions of rows, Codex may additionally use:

- PyArrow / Parquet
- Polars or DuckDB for efficient intermediate processing

However:

- Keep the final logic understandable.
- Do not hide the entire ETL process behind one advanced library call.
- Demonstrate core wrangling concepts clearly.
- Maintain a final persistent SQLite/SQL warehouse or another explicitly documented persistent store.

---

# 9. Data-Wrangling Pipeline

The pipeline is:

```text
RAW BTS MONTHLY FILES
        +
OURAIRPORTS
        │
        ▼
1. EXTRACTION / INGESTION
        │
        ▼
2. INITIAL DATA AUDIT
        │
        ▼
3. CLEANING
        │
        ▼
4. TRANSFORMATION
        │
        ▼
5. JOIN / ENRICHMENT
        │
        ▼
6. FEATURE ENGINEERING
        │
        ▼
7. DATA QUALITY VALIDATION
        │
        ▼
8. PERSISTENT SQL / WAREHOUSE LOAD
        │
        ├───────────────┐
        ▼               ▼
9. EDA / INSIGHTS     10. ML
        │               │
        └───────┬───────┘
                ▼
         POWER BI EXPORTS
                │
                ▼
          FINAL DASHBOARD
```

---

# 10. Phase 1 — Extraction / Ingestion

## Goals

- Load all 12 BTS monthly files.
- Preserve provenance.
- Confirm column consistency.
- Combine files without losing the year/month of origin.
- Load OurAirports data separately.

## Required Actions

For each BTS file:

1. Read file.
2. Record:
   - filename
   - row count
   - column count
   - year/month
   - load status
3. Standardize column names if necessary.
4. Add:
   - `source_file`
   - `source_year`
   - `source_month`
5. Validate that `FlightDate` matches the expected source period.
6. Append into the interim dataset.

## Output

Prefer partitioned Parquet:

```text
data/interim/flights_standardized/year=2025/month=01/...
```

Do not immediately create one enormous CSV.

---

# 11. Phase 2 — Initial Data Audit

Before cleaning, calculate and save:

- total rows
- total columns
- data types
- null count by column
- null percentage by column
- unique count by column
- duplicate row count
- date range
- airline count
- origin airport count
- destination airport count
- minimum / maximum numeric values
- obvious invalid values

Output:

```text
reports/data_quality_report.md
```

Also save machine-readable audit results where practical.

---

# 12. Phase 3 — Data Cleaning

Every cleaning decision must be logged in:

```text
reports/cleaning_log.md
```

The log should contain:

| Issue | Column(s) | Rows affected | Action | Reason |
|---|---|---:|---|---|

## 12.1 Missing Values

Do not blindly run `dropna()`.

### Expected Rules

#### Cancelled Flights

For cancelled flights, fields such as:

- actual departure/arrival time
- arrival delay
- air time

may legitimately be missing.

Do not impute fictional operational values.

#### Cancellation Code

If:

```text
Cancelled == 0
```

then a missing cancellation code is expected.

For descriptive outputs, it may be labelled:

```text
Not Cancelled
```

without changing the raw field.

#### Delay-Cause Columns

Missing delay-cause values may mean the flight did not meet the reporting threshold for that cause.

Do not automatically replace them without documenting the interpretation.

## 12.2 Duplicate Records

Create a business-key check using a combination such as:

```text
FlightDate
Reporting_Airline
Flight_Number_Reporting_Airline
Origin
Dest
CRSDepTime
```

Investigate duplicate candidates before removal.

Do not assume identical-looking flights are always accidental duplicates.

## 12.3 Data Types

Convert:

- `FlightDate` → date
- delay variables → numeric
- distance → numeric
- cancellation/diversion flags → integer/bool
- airport/airline codes → string/category
- scheduled times → parsed hour/minute features

## 12.4 Categorical Standardization

Trim whitespace.

Normalize obvious casing issues where safe.

Do not rewrite official airport or airline codes arbitrarily.

## 12.5 Outliers

Investigate:

- extreme departure delays
- extreme arrival delays
- impossible negative durations
- zero / invalid distance
- impossible elapsed times

Do not remove valid extreme delays only because they are statistically unusual.

A severe operational disruption can be a legitimate record.

---

# 13. Phase 4 — Transformation & Feature Engineering

Create clearly documented derived features.

## 13.1 Route

```text
route = Origin + "-" + Dest
```

Example:

```text
JFK-LAX
```

## 13.2 Scheduled Departure Hour

Parse `CRSDepTime`.

Create:

```text
scheduled_dep_hour
```

## 13.3 Departure Time Band

Recommended categories:

```text
00:00–05:59 -> Late Night
06:00–10:59 -> Morning
11:00–15:59 -> Midday
16:00–20:59 -> Evening
21:00–23:59 -> Night
```

Keep boundaries in configuration, not scattered through code.

## 13.4 Weekend Flag

```text
is_weekend
```

Saturday/Sunday:

```text
1
```

Otherwise:

```text
0
```

## 13.5 Season

Example:

```text
Dec/Jan/Feb -> Winter
Mar/Apr/May -> Spring
Jun/Jul/Aug -> Summer
Sep/Oct/Nov -> Fall
```

## 13.6 Severe Delay Target

Default project definition:

```text
severe_delay = 1 if ArrDelayMinutes > 60
severe_delay = 0 otherwise
```

Only create this target for flights where arrival-delay status can validly be determined.

Cancelled flights should **not** automatically be labelled as severe arrival delays.

### Target Governance

The 60-minute threshold is a **project-defined business threshold**.

Before freezing the ML dataset:

- calculate class distribution,
- report the percentage of severe delays,
- confirm there are enough positive examples.

Do not silently change the threshold after viewing model results.

If the team later changes the threshold, document the reason and rerun all relevant analysis.

## 13.7 Delay Category

For descriptive analysis only, create:

```text
On Time / Early
Minor Delay
Moderate Delay
Severe Delay
```

Recommended configurable definition:

```text
ArrDelayMinutes <= 0      -> On Time / Early
1–15                      -> Minor
16–60                     -> Moderate
>60                       -> Severe
```

## 13.8 Optional Historical Aggregate Features

These can improve the ML model but must avoid leakage.

Possible features:

- historical severe-delay rate by airline
- historical severe-delay rate by origin airport
- historical severe-delay rate by destination airport
- historical severe-delay rate by route
- historical average arrival delay by airline
- historical average arrival delay by route

### Critical Rule

Historical features for a given row must be calculated using **only information available before that row's date** or using training data only.

Do not calculate a full-dataset route delay average and feed it into both training and test rows.

---

# 14. Phase 5 — OurAirports Join

The join must be auditable.

## 14.1 Join Problem

BTS primarily uses U.S. airport codes such as:

```text
JFK
LAX
ATL
ORD
```

OurAirports contains multiple identifiers, including ICAO/IATA-style fields depending on the record.

Prefer joining BTS airport codes against the appropriate OurAirports **IATA code field** when available.

Do not assume `ident` is always identical to the BTS airport code.

## 14.2 Build Airport Dimension

Create one standardized airport dimension with fields such as:

```text
airport_key
iata_code
ident
airport_name
airport_type
latitude_deg
longitude_deg
elevation_ft
iso_country
iso_region
municipality
scheduled_service
```

## 14.3 Origin and Destination Enrichment

Flights need two airport relationships:

```text
Origin -> dim_airport
Dest   -> dim_airport
```

Do not duplicate all airport metadata permanently into the raw table.

For Power BI extracts, selected origin/destination labels may be denormalized for convenience.

## 14.4 Join Validation

Report:

- total distinct BTS airport codes
- matched airport codes
- unmatched airport codes
- match percentage
- flights affected by unmatched codes

Save this to the data-quality report.

---

# 15. Phase 6 — Dimensional Model / Data Warehouse

Use a star-schema-inspired design.

## 15.1 Fact Table

### `fact_flight`

Suggested fields:

```text
flight_key
date_key
airline_key
origin_airport_key
destination_airport_key

flight_number
scheduled_departure_time
actual_departure_time
scheduled_arrival_time
actual_arrival_time

departure_delay_minutes
arrival_delay_minutes

cancelled
cancellation_code
diverted

scheduled_elapsed_minutes
actual_elapsed_minutes
air_time_minutes
distance_miles

carrier_delay_minutes
weather_delay_minutes
nas_delay_minutes
security_delay_minutes
late_aircraft_delay_minutes

severe_delay
route
scheduled_dep_hour
departure_time_band
is_weekend
season
```

## 15.2 `dim_date`

Suggested fields:

```text
date_key
full_date
day
day_name
day_of_week
week
month
month_name
quarter
year
is_weekend
season
```

## 15.3 `dim_airline`

Suggested fields:

```text
airline_key
reporting_airline_code
dot_airline_id
iata_airline_code
airline_name
```

Only include airline-name fields if a reliable BTS lookup source has been loaded.

Do not invent airline names from codes.

## 15.4 `dim_airport`

Suggested fields:

```text
airport_key
iata_code
ident
airport_name
airport_type
municipality
iso_region
iso_country
latitude
longitude
elevation_ft
```

## 15.5 Optional `dim_delay_category`

May be included for dashboard convenience.

---

# 16. Slowly Changing Dimensions

The syllabus includes slowly changing dimensions, but the project does **not** need to artificially manufacture historical changes.

Document the concept in the report and explain where it could apply, for example:

- airline name changes,
- airport name/metadata changes,
- airport operational status changes.

If implementing SCD Type 2, do so only if the source data genuinely supports historical versions.

Do not create fake historical rows just to say SCD was implemented.

---

# 17. Persistent Storage

Create:

```text
database/airline_dw.sqlite
```

At minimum, load:

```text
fact_flight
dim_date
dim_airline
dim_airport
```

Add primary keys and appropriate indexes only where needed for usability.

The project is about data wrangling, not database-performance benchmarking, so keep indexing simple.

Also retain processed Parquet data for reproducibility and efficient analysis.

---

# 18. Phase 7 — Exploratory Data Analysis

EDA must produce at least three useful, evidence-backed insights.

Do not write the insight first and force the data to fit it.

## Required Analysis Areas

### Overall

- total flights
- completed flights
- cancelled flights
- diverted flights
- average arrival delay
- median arrival delay
- severe-delay rate
- on-time / early rate

### Airline

- flight count by airline
- average delay by airline
- severe-delay percentage by airline
- cancellation percentage by airline

Use minimum-flight thresholds when ranking airlines if necessary.

### Airport

- busiest origin airports
- average departure delay by origin
- average arrival delay by destination
- severe-delay rate by airport
- cancellation rate by airport

### Route

- busiest routes
- average delay by route
- severe-delay rate by route
- cancellation rate by route

Use a minimum-flight threshold to avoid declaring a tiny route with two flights the "worst route."

### Time

Analyze by:

- year
- quarter
- month
- day of week
- scheduled departure hour
- departure-time band
- weekend / weekday
- season

### Delay Causes

For delayed flights:

- carrier delay
- weather delay
- NAS delay
- security delay
- late-aircraft delay

These are descriptive fields only.

---

# 19. Candidate Insight Rules

Final insights must be based on actual computed results.

Examples of the *type* of insight to seek:

1. Certain departure-time bands may have materially different severe-delay rates.
2. A small number of high-volume airport-route combinations may account for a disproportionate share of severe delays.
3. Some carriers may perform better or worse than the network average after applying a reasonable minimum-flight threshold.
4. Cancellation patterns may differ strongly across months or airports.
5. Late-aircraft delay may account for a significant share of reported delay minutes.

These are **hypotheses**, not final findings.

Never put them into the final report as facts until verified.

---

# 20. Machine-Learning Task

## Problem Type

Binary classification for completed, non-diverted flights with a known arrival
delay. Cancelled, diverted, and unknown-outcome rows remain in operational data
but are excluded from model fitting and evaluation.

## Target

```text
severe_delay
```

Definition:

```text
1 -> arrival_delay_minutes > 60
0 -> arrival_delay_minutes <= 60
```

Exactly 60 minutes is non-severe. The threshold is frozen before model fitting.

---

# 21. ML Prediction Point

The model should represent:

> **A prediction made before the flight departs.**

Therefore, only information plausibly known before departure may be used as predictors.

This is one of the most important rules in the project.

---

# 22. Frozen Candidate ML Features

The authoritative allowlist is `MODEL_FEATURES` in `src/features.py` and is
documented in `reports/feature_dictionary.md`. It currently contains:

```text
quarter
month
day_of_month
day_of_week
is_weekend
scheduled_dep_hour
scheduled_arr_hour
departure_time_band
season
dep_time_sin
dep_time_cos
reporting_airline
origin
destination
route
distance_miles
distance_band
scheduled_elapsed_minutes
scheduled_elapsed_invalid
origin_latitude_deg
origin_longitude_deg
destination_latitude_deg
destination_longitude_deg
```

Year is constant in this one-year dataset. Raw `flight_date`, `source_file`,
`source_row_number`, and `dataset_split` are metadata and are excluded from X.
Target-derived historical rate features are deferred; do not add them to the
initial models.

---

# 23. ML Leakage — Forbidden Predictors

Do **not** use the following as inputs to a pre-departure severe-delay model:

```text
DepTime
DepDelay
DepDelayMinutes
DepDel15

ArrTime
ArrDelay
ArrDelayMinutes
ArrDel15
ArrivalDelayGroups

ActualElapsedTime
AirTime

Cancelled
CancellationCode
Diverted
ml_target_eligible
completed_missing_arrival_delay
delay_category
severe_delay

CarrierDelay
WeatherDelay
NASDelay
SecurityDelay
LateAircraftDelay
```

These variables reveal information that occurs after or during the flight, or directly reveals the outcome.

They may still be used in descriptive analysis.

---

# 24. Train/Test Strategy

The chronological split is frozen as:

```text
TRAIN:
January 1–August 31, 2025

VALIDATION:
September 1–October 31, 2025

TEST:
November 1–December 31, 2025
```

This makes the experiment closer to:

> train on historical flights, evaluate on future flights.

Do not change these boundaries after viewing model results. Fit encoders,
scalers, imputers, class weights, and any resampling using training data only.
Use validation data for model and threshold selection, then evaluate the chosen
model and threshold once on test data. With only one calendar year, the model
cannot claim year-over-year generalization.

---

# 25. Models to Compare

Compare all four approaches below on the same frozen splits and feature policy.

## Model 0 — Baseline

- Use `DummyClassifier(strategy="most_frequent")`.
- It always predicts the non-severe majority class and ignores the features.
- Its high accuracy is not evidence of severe-delay detection; its severe-class
  recall and F1 will be zero.

## Model 1 — Logistic Regression

Purpose:

- simple
- interpretable
- useful baseline ML model

## Model 2 — Decision Tree

Purpose:

- directly connected to the syllabus
- easy to explain in viva
- handles nonlinear relationships

## Model 3 — Random Forest

Purpose:

- stronger ensemble comparison
- provides feature importance
- usually performs better than one simple tree

Keep model count manageable.

Do not add advanced models merely to make the project look complicated.

---

# 26. ML Evaluation Metrics

Because severe delays are imbalanced, use the same metrics for every model and
do not select a model using accuracy alone.

Report:

- Accuracy
- Precision
- Recall
- F1-score
- Balanced accuracy
- Confusion matrix
- ROC-AUC
- PR-AUC / Average Precision
- class distribution

Interpret the metrics in plain language.

Example:

> Recall tells us what percentage of actual severe-delay flights the model successfully identifies.

---

# 27. Model Interpretation

For the selected model, produce:

- feature importance or coefficient analysis
- validation precision-recall curve and documented threshold rule
- final test confusion matrix at the selected threshold
- false-negative and false-positive analysis by month, airline, origin,
  destination, route, season, and departure-time band where sample sizes allow
- performance comparison with the EDA patterns

Do not imply that feature importance proves causation. Apply minimum-volume
rules to subgroup conclusions and report counts with rates.

---

# 28. Power BI Data Outputs

Codex should prepare clean files for Power BI.

Power BI itself can be built manually after the data pipeline is complete.

Create:

```text
data/processed/powerbi/
```

Recommended outputs:

```text
fact_flight_powerbi.parquet
dim_date.csv
dim_airline.csv
dim_airport.csv
model_predictions.csv
model_metrics.csv
feature_importance.csv
```

If Power BI ingestion becomes easier with CSV, create a dashboard-sized export rather than forcing an excessively large raw fact CSV.

Do not delete the full processed dataset.

---

# 29. Power BI Dashboard Plan

Minimum: **3 report pages**

---

## Page 1 — Executive / Flight Performance Overview

### KPI Cards

- Total Flights
- Completed Flights
- Average Arrival Delay
- Severe Delay %
- Cancellation %
- On-Time / Early %

### Visuals

- flight volume trend
- delay trend by month
- airline performance comparison
- cancellation trend
- airport map

### Slicers

- Year
- Month
- Airline
- Origin Airport
- Destination Airport

### Stakeholder Question

> How is the overall network performing?

---

## Page 2 — Airport & Route Drill-Down

### Visuals

- busiest airports
- worst high-volume origins by delay
- worst high-volume destinations by delay
- route performance
- delay by departure hour
- delay by day of week
- cancellation reasons
- origin/destination map

### Drill-Down / Filters

Potential hierarchy:

```text
State
  -> Airport
      -> Route
```

### Stakeholder Question

> Where and when are operational problems concentrated?

---

## Page 3 — Machine Learning Insights

### Show

- model comparison table
- Accuracy
- Precision
- Recall
- F1
- Balanced Accuracy
- ROC-AUC
- PR-AUC / Average Precision
- confusion matrix
- feature importance
- selected probability threshold and precision-recall trade-off
- false-negative and false-positive subgroup analysis
- actual vs predicted severe-delay counts
- prediction results sliced by airline, airport, route, month, season, and time band where sample sizes allow

### Stakeholder Question

> How well can severe delays be predicted before departure, and which features are most informative?

---

# 30. Cleaning & Transformation Log

The completed log is `reports/cleaning_log.md`. It records each issue, measured
row count, action, justification, and intentionally retained condition. Refresh
it whenever cleaning logic or source data changes.

---

# 31. Data-Quality Checks

Automate checks where possible.

## Required Checks

- no unexpected years outside 2025
- no missing `FlightDate`
- origin/destination codes have expected format
- `Distance >= 0`
- cancellation flag values are valid
- diversion flag values are valid
- no impossible month/day values
- target only contains `0/1`
- target is null where outcome is intentionally undefined
- dimension keys remain unique
- fact foreign keys resolve where expected
- airport join coverage is reported
- source row counts are tracked before and after cleaning

## Row Reconciliation

The completed monthly reconciliation is
`reports/tables/final_row_reconciliation.csv`. It distinguishes rows retained in
the operational data from rows excluded only because the ML target is undefined.

---

# 32. Reproducibility

The completed stages are reproducible from raw files with:

```bash
python scripts/run_etl.py
python scripts/execute_notebooks.py
```

The remaining planned stage commands are:

```bash
python scripts/build_database.py
python scripts/train_models.py
python scripts/export_powerbi.py
```

Add those commands only with their corresponding implementation. Keep each
stage independently understandable and testable.

---

# 33. Configuration

`config/settings.yaml` is authoritative for source/output paths, chunk size,
the 60-minute target, group-ranking thresholds, departure-time bands, the PBI
airport alias, chronological split dates, and random seed. Do not duplicate
these values in production code. `src/features.py` is authoritative for the
model feature allowlist and blocked outcome fields.

---

# 34. Notebook Structure

The notebooks are for explanation, visual evidence, and viva readability.

Core production logic should live in `src/`.

## `01_beginner_eda.ipynb` — complete

Contains:

- source overview
- shapes, columns, data types, missingness, and duplicates
- cleaning decisions and before/after examples
- flagged-record and extreme-delay review
- operational EDA and evidence-backed findings
- final row reconciliation

## `02_feature_engineering.ipynb` — complete

Contains:

- before/after examples
- route, calendar, scheduled-time, distance, and cyclic-time features
- origin and destination airport joins
- group-by and pivot transformations
- feature allowlist, leakage exclusions, and chronological split
- persisted-output validation

## `03_machine_learning.ipynb` — planned

Show:

- target definition
- frozen feature selection and chronological split
- training-only preprocessing
- majority baseline, Logistic Regression, Decision Tree, and Random Forest
- validation model comparison and threshold selection
- one final November–December test evaluation

## `04_model_interpretation.ipynb` — planned

Show:

- coefficients and feature importance
- false-negative and false-positive subgroup analysis
- comparison between model explanations and EDA
- operational interpretation of the chosen threshold
- limitations
- export of prediction results

---

# 35. Required Final Deliverables

The project should eventually produce:

1. **Jupyter notebook(s)**
   - wrangling
   - analysis
   - ML
   - markdown explanation

2. **Cleaning & transformation log**

3. **Power BI `.pbix`**
   - minimum 3 report pages
   - interactive filtering/drill-down
   - model page

4. **Power BI PDF export**
   - fallback copy

5. **Written report**
   - 5–7 pages
   - objective
   - dataset
   - extraction
   - cleaning
   - transformation
   - loading
   - ML
   - dashboard
   - insights
   - limitations

6. **Presentation**
   - 8–10 slides
   - include dashboard demo/screens

7. **Raw and cleaned data**
   - or regeneration script if raw data is too large

8. **Individual contribution statement**
   - one line per group member

---

# 36. Mapping to Course Syllabus

| Syllabus Area | Project Implementation |
|---|---|
| Introduction to Data Science | Airline operational problem definition |
| Data Scientist's Toolbox | Python, Jupyter, SQL, Power BI, ML |
| Data Collection | BTS + OurAirports |
| Data Formats | CSV + Parquet + SQL |
| Tidy Data | standardized flight/airport tables |
| Data Cleaning | nulls, types, duplicates, outliers, categories |
| Data Warehousing | SQLite warehouse |
| Metadata | source/column documentation |
| Granularity | one flight record per fact row |
| Dimensional Modelling | fact flight + date/airline/airport dimensions |
| Fact Tables | `fact_flight` |
| Dimension Tables | `dim_date`, `dim_airline`, `dim_airport` |
| SCD | concept discussed; implement only if source supports it |
| ETL | extract, clean, transform, validate, load |
| Data Quality | automated validation + cleaning log |
| Testing | data-quality tests + pipeline tests |
| Decision Trees | Decision Tree classifier |
| Bayes Model | optional extension, not required for core ML |
| Frequent Itemsets | optional extension, not required for core project |
| Operational Data Store / Trends | warehouse discussion + processed operational tables |

---

# 37. Project Milestones

## Milestone 1 — Repository & Data

- [x] Scaffold repository
- [x] Add configuration
- [x] Download BTS files
- [x] Download OurAirports
- [x] Verify all 12 BTS periods are present
- [x] Add `.gitignore` so raw large files are not committed

## Milestone 2 — Ingestion

- [x] Load all source files
- [x] Produce source manifest
- [x] Validate schema
- [x] Create standardized interim Parquet (12 monthly files)

## Milestone 3 — Cleaning

- [x] Missing-value audit
- [x] Duplicate audit
- [x] Type conversion
- [x] Outlier investigation (all six flags and 20 delay extremes reviewed)
- [x] Cleaning log

## Milestone 4 — Transformation

- [x] Route
- [x] scheduled departure hour
- [x] departure band
- [x] weekend
- [x] season
- [x] delay category
- [x] severe-delay target
- [x] airport enrichment (both endpoint joins persisted with row reconciliation)
- [x] distance band and cyclic scheduled-time features
- [x] route-month aggregation and route/airport-month pivots
- [x] explicit feature allowlist and persisted eligible ML partitions

## Milestone 5 — Warehouse

- [ ] Build dimensions
- [ ] Build fact table
- [ ] Load SQLite
- [ ] Test keys
- [ ] Validate row counts

## Milestone 6 — EDA

- [x] airline analysis
- [x] airport analysis
- [x] route analysis
- [x] time analysis
- [x] cancellation analysis
- [x] delay-cause analysis
- [x] 3+ evidence-backed insights

## Milestone 7 — ML

- [x] finalize target (ARR_DELAY > 60 on completed, non-diverted flights with known outcomes)
- [x] leakage-safe candidate feature allowlist (no fitted preprocessing yet)
- [x] chronological split (Jan–Aug / Sep–Oct / Nov–Dec)
- [ ] baseline
- [ ] Logistic Regression
- [ ] Decision Tree
- [ ] Random Forest
- [ ] evaluate metrics
- [ ] interpret selected model

## Milestone 8 — Power BI Exports

- [ ] dashboard fact extract
- [ ] dimensions
- [ ] prediction output
- [ ] model metrics
- [ ] feature importance

## Milestone 9 — Final Presentation Assets

- [ ] final plots
- [ ] insights summary
- [ ] limitations
- [ ] report-ready tables
- [ ] viva explanations

---

# 38. Definition of Done

The coding portion is considered complete when:

- all 12 BTS monthly files can be ingested reproducibly,
- data-quality issues are measured and documented,
- cleaning decisions are logged,
- BTS flight data is successfully enriched with airport metadata,
- processed data is stored persistently,
- a valid dimensional model exists,
- at least three non-obvious findings are supported by statistics/visuals,
- a severe-delay ML task is implemented without obvious target leakage,
- the majority baseline, Logistic Regression, Decision Tree, and Random Forest are evaluated,
- model metrics are exported,
- Power BI-ready files are generated,
- all major scripts run end-to-end without manual code edits,
- README contains reproducible setup/run instructions.

---

# 39. Important Codex Guardrails

Codex must follow these rules.

## Data

1. **Never modify raw source files.**
2. Never fabricate missing values solely to make the dataset complete.
3. Do not drop records without logging the reason and count.
4. Treat legitimate cancelled-flight missingness differently from accidental missingness.
5. Keep a source manifest and row reconciliation.

## Machine Learning

6. Follow the frozen target, population, feature, split, and evaluation contract
   in Sections 20–27.
7. Fit all learned preprocessing and resampling on training rows only.
8. Select the model and probability threshold on validation data, then evaluate
   once on the untouched test set.
9. Do not fabricate results, optimize accuracy alone, add post-flight features,
   or change the target threshold after viewing model performance.

## Analysis

10. Do not state an insight until it is calculated from the data.
11. Distinguish correlation/association from causation.
12. Apply sensible minimum-flight thresholds to "best/worst" airline, airport, and route rankings.
13. Preserve both average and median delay where outliers make the mean misleading.

## Engineering

14. Avoid loading the entire full-year raw dataset into memory when a chunked/partitioned approach is safer.
15. Keep production code in `src/`; notebooks should call reusable functions.
16. Add tests for critical cleaning, feature, split, and model logic.
17. Prefer simple, explainable implementation over unnecessary complexity.

---

# 40. Future Optional Extensions

Only after the core project is stable:

## Weather Enrichment

Join historical airport weather by:

```text
airport + date/time
```

Possible predictors:

- temperature
- precipitation
- wind
- visibility
- weather condition

This must be joined carefully and without future information.

## Cancellation Prediction

Separate binary-classification problem:

```text
cancelled vs not cancelled
```

Do not mix this target with severe-arrival-delay classification.

## Naive Bayes

Could be included to connect directly to the syllabus.

## Frequent Itemset Mining

Possible question:

> Which combinations of airline, airport, departure-time band, season, and delay category frequently occur together?

This is optional and should not distract from the main project.

---

# 41. Key Viva Explanation

A concise explanation of the project:

> We are using all January–December 2025 U.S. BTS flight records with OurAirports metadata. Cleaning, transformation, airport joining, feature engineering, validation, and EDA are complete. We retained every operational row and prepared a leakage-controlled ML dataset for completed, non-diverted flights with known arrival outcomes. Next, we will build the SQLite warehouse and compare a majority baseline, Logistic Regression, Decision Tree, and Random Forest using a chronological future-month holdout. We will select the model and probability threshold on validation data, evaluate once on November–December test data, explain its errors and important features, and prepare a three-page Power BI dashboard.

---

# 42. Final Project Philosophy

The objective is **not** to create the most complicated airline model possible.

The objective is to create a project that clearly demonstrates:

```text
REAL DATA
   ->
MESSY DATA
   ->
WRANGLING
   ->
TRANSFORMATION
   ->
SQL / WAREHOUSING
   ->
ANALYSIS
   ->
MACHINE LEARNING
   ->
COMMUNICATION
```

Every major decision should be:

- reproducible,
- documented,
- technically defensible,
- easy to explain in a viva.

**Prefer a clean, correct, leakage-safe project over a more advanced but poorly justified one.**
