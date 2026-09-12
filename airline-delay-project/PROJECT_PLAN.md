# Airline Flight Delay Prediction & Operational Performance Analysis
## Codex CLI Project Brief / Master Plan

> **Purpose of this file:** This is the single source of truth for implementing the project in Codex CLI.  
> Codex should use this document to scaffold the repository, ingest the data, perform wrangling, build the SQL/warehouse layer, train and evaluate ML models, and prepare Power BI-ready outputs.
>
> **Project status:** Cleaning, EDA, and transformation complete; warehouse and model training are next
> **Primary domain:** Airline operations, flight delays, cancellations, airports  
> **Primary dataset:** U.S. Bureau of Transportation Statistics (BTS) Reporting Carrier On-Time Performance  
> **Data period:** January–December 2025 (one full calendar year)  
> **Supporting dataset:** OurAirports `airports.csv`  
> **Optional extension:** Weather data — **do not add in the initial implementation**

## Active implementation plan — 13 September 2026

This checkpoint completes cleaning, EDA, and transformation. It supersedes the
older first-pass status and suggested notebook filenames below; warehouse,
model training, and Power BI remain subsequent milestones.

1. Finish `notebooks/01_beginner_eda.ipynb`: explain raw schema, measured
   missingness, duplicates, conversions, category normalization, before/after
   cleaning, the six flagged records, extreme-delay context, and full-year EDA.
   Preserve its existing findings and add distributions, airport comparisons,
   and an airport-by-month cancellation heatmap with explicit denominators.
2. Keep reusable logic in small pandas/NumPy functions. Retain operational
   missingness and all source rows; flag invalid scheduled durations and the
   completed flight with unknown arrival delay. Do not impute outcomes or
   delete unusual but possible delays. Measure conversion failures and actual
   category corrections instead of assuming that every row required repair.
3. Add `scripts/run_etl.py` to refresh the source audit and persist one cleaned
   and one enriched Parquet file per month. Validate schema, monthly dates,
   calendar fields, duplicate candidates, row counts, targets, and both airport
   joins. Retain source filename and original one-based data-row number.
4. Create `notebooks/02_feature_engineering.ipynb` with visible examples of
   route, calendar, scheduled-time, distance-band, and cyclic-time features;
   two many-to-one airport merges; a group-by and pivot; and full-data exports.
   Explain why each feature supports the operational or prediction question.
5. Persist eligible ML rows using an explicit pre-departure feature allowlist,
   plus the target, provenance, and chronological split labels. Freeze Jan–Aug
   training, Sep–Oct validation, Nov–Dec testing. Leave imputation, scaling,
   encoding, balancing, and model fitting to the ML stage; they must be fitted
   on training data only. Do not use full-year delay summaries as predictors.
   Current OurAirports labels are descriptive snapshot metadata; only physical
   coordinates are candidate predictors, with the historical-snapshot limitation
   documented. Preserve the existing source-supported PBI alias.
6. Generate a concise final cleaning log, transformation/data dictionary,
   reconciliation and split tables, and measured completion report. Test target
   boundaries, invalid times, missing values, join cardinality, and split
   boundaries. Execute both notebooks from fresh kernels and inspect charts.

**Execution status — completed and verified:** The full ETL retained all
7,001,619 operational rows and exported 6,879,484 eligible ML rows. Each of the
three flight layers contains twelve monthly Parquet files; both endpoint joins
resolve every row. Five impossible durations and one unknown completed outcome
were handled with the documented flags/exclusions. Twenty extreme records were
reviewed; all satisfied the delay/duration identity and were retained. Actual
numeric/date parse failures and category corrections were both zero.

`01_beginner_eda.ipynb` executed all 22 code cells, and
`02_feature_engineering.ipynb` executed all 11 code cells in fresh kernels.
All 12 tests passed, including Parquet type/value round trips. Saved charts were
visually checked. Validation used pandas 2.3.3 and PyArrow 20.0.0 in the local
project environment. Run `python scripts/run_etl.py`, then
`python scripts/execute_notebooks.py` to reproduce the stage.

The frozen split has 4,592,366 training, 1,159,898 validation, and 1,127,220 test
rows. One missing scheduled duration remains among eligible predictors, in
November; any later imputer must be fitted on training rows only. The target
threshold and feature allowlist are fixed for the next stage. No models or
learned preprocessing were fitted. See `reports/cleaning_log.md`,
`reports/feature_dictionary.md`, and `reports/transformation_report.md`.

---

# 1. Project Title

**Airline Flight Delay Prediction and Operational Performance Analysis Using Data Wrangling, ETL, Machine Learning, and Power BI**

---

# 2. Project Objective

The project will use large-scale real-world airline flight data to answer two broad questions:

1. **Operational analysis:**  
   Which airlines, airports, routes, dates, and departure-time periods experience the highest delays and cancellations?

2. **Machine learning:**  
   Can historical and pre-departure flight information be used to predict whether a flight will experience a **severe arrival delay**?

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

**Can we predict whether a scheduled domestic U.S. flight will experience a severe arrival delay using information available before departure?**

## Secondary Questions

1. Which airlines have the highest and lowest delay rates?
2. Which origin airports experience the highest average departure delays?
3. Which destination airports experience the highest average arrival delays?
4. Which routes have the highest severe-delay rates?
5. How do delays change by:
   - month,
   - day of week,
   - hour of departure,
   - weekend vs weekday,
   - season?
6. Which airlines and airports have the highest cancellation rates?
7. What are the most common reported delay causes?
8. Are some routes consistently more delay-prone than others?
9. How well can a simple baseline model predict severe delays compared with machine-learning models?

## 3.1 Literature-derived problem definition

A review of ten relevant flight-delay prediction papers identified twenty paper-level drawbacks. After repeated drawbacks were consolidated, three research gaps were selected because they are both important and achievable with this project's data:

1. **Prediction-time realism:** prevent target leakage by using only information available before scheduled departure.
2. **Broad and time-aware evaluation:** use the full 2025 U.S. domestic network in the project data and test on chronologically later months rather than a random holdout.
3. **Imbalance-aware evaluation:** preserve the natural severe-delay rate in validation/testing and report minority-sensitive metrics instead of accuracy alone.

**Problem definition:** Existing studies may report strong flight-delay performance using restricted airport/route samples, random or artificially balanced evaluations, or variables that are unavailable before the outcome. This project will therefore develop and evaluate an explainable, leakage-controlled, and imbalance-aware machine-learning pipeline to predict whether a scheduled domestic U.S. flight will arrive more than 60 minutes late, using only pre-departure information and a chronological future-month holdout.

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

## Initial Project Scope

Use:

```text
BTS 2025 (January–December)
       +
OurAirports airports.csv
```

### Not Included Initially

Do not add external weather data during the first implementation.

Weather can be added later only as a documented extension if:

- the core project is complete,
- join quality is acceptable,
- the team has enough time,
- the additional source clearly improves the model or analysis.

## Historical Implementation Checkpoint — 9 September 2026

Completed against the full 2025 dataset:

- all 12 BTS files organized and validated (7,001,619 rows),
- consistent 28-column schema and correct monthly date coverage confirmed,
- missingness, data types, unique counts, numeric ranges, invalid values, and duplicates audited,
- explainable route/time/calendar/target features implemented,
- OurAirports dimension standardized and 100% of BTS airport codes matched using one documented historical alias,
- first-pass airline, airport, route, time, cancellation, and delay-cause EDA completed,
- four reproducible figures and five evidence-backed candidate insights generated.

This exceeds the current goal of completing at least half of the cleaning/EDA work.
The immediate next step is to persist cleaned flight partitions, investigate the
small flagged-row set and extreme-delay context, then convert the audit and EDA
outputs into viva-friendly notebooks. Warehouse construction and ML follow only
after the cleaned schema is frozen.

---

# 7. Recommended Repository Structure

Codex should scaffold approximately this structure:

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
│   ├── 01_data_audit.ipynb
│   ├── 02_cleaning_and_transformation.ipynb
│   ├── 03_eda_and_insights.ipynb
│   ├── 04_machine_learning.ipynb
│   └── 05_model_interpretation.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingest.py
│   ├── clean.py
│   ├── transform.py
│   ├── validate.py
│   ├── warehouse.py
│   ├── features.py
│   ├── model.py
│   ├── evaluate.py
│   └── export_powerbi.py
│
├── scripts/
│   ├── run_ingestion.py
│   ├── run_etl.py
│   ├── build_database.py
│   ├── train_models.py
│   └── export_powerbi.py
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

Binary classification.

## Target

```text
severe_delay
```

Definition:

```text
1 -> ArrDelayMinutes > 60
0 -> ArrDelayMinutes <= 60
```

Cancelled flights should normally be excluded from this arrival-delay classification model.

Document the exact filtering rule.

---

# 21. ML Prediction Point

The model should represent:

> **A prediction made before the flight departs.**

Therefore, only information plausibly known before departure may be used as predictors.

This is one of the most important rules in the project.

---

# 22. Allowed Candidate ML Features

Examples:

```text
Year
Quarter
Month
DayOfWeek
scheduled_dep_hour
departure_time_band
is_weekend
season

Reporting_Airline
Origin
Dest
route

Distance
CRSElapsedTime
```

Potential carefully constructed historical features:

```text
historical_airline_delay_rate
historical_origin_delay_rate
historical_destination_delay_rate
historical_route_delay_rate
```

These historical features must be created without leakage.

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

Because this is time-based operational data, prefer a chronological split rather than a purely random split.

Recommended approach:

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

The exact date boundaries may be adjusted before model training if data-quality
checks reveal incomplete periods, but the final split must remain chronological
and must be frozen before model comparison. With only one calendar year, the
model cannot claim year-over-year generalization; this limitation must be stated
in the report.

Do not fit encoders, scalers, imputers, or target-derived historical features using test data.

---

# 25. Models to Compare

At minimum compare two meaningful approaches.

Recommended:

## Model 0 — Baseline

Possible baseline:

- always predict the majority class, or
- stratified/simple rule baseline

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

Optional but recommended.

Purpose:

- stronger ensemble comparison
- provides feature importance
- usually performs better than one simple tree

Keep model count manageable.

Do not add advanced models merely to make the project look complicated.

---

# 26. ML Evaluation Metrics

Because severe delays may be imbalanced, do not report only accuracy.

Report:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- ROC-AUC where appropriate
- class distribution

If severe-delay prevalence is low, additionally consider:

- PR-AUC / Average Precision

Interpret the metrics in plain language.

Example:

> Recall tells us what percentage of actual severe-delay flights the model successfully identifies.

---

# 27. Model Interpretation

For the best model, produce:

- feature importance or coefficient analysis
- confusion matrix
- performance by year
- performance by airline if useful
- performance by major airport if useful

Do not imply that feature importance proves causation.

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
- ROC-AUC if used
- confusion matrix
- feature importance
- actual vs predicted severe-delay counts
- prediction results sliced by airline/airport if practical

### Stakeholder Question

> How well can severe delays be predicted before departure, and which features are most informative?

---

# 30. Cleaning & Transformation Log

Maintain:

```text
reports/cleaning_log.md
```

Suggested format:

```markdown
## Cleaning Action 001

**Issue:** Missing ArrDelayMinutes  
**Rows affected:** X  
**Investigation:** Most affected rows are cancelled/diverted flights.  
**Action:** Excluded from severe-arrival-delay target construction; retained in operational dataset.  
**Reason:** Arrival delay cannot be validly imputed for a cancelled flight.
```

The log is a formal project deliverable, not an afterthought.

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

## Row-Reconciliation Table

Maintain something similar to:

| Stage | Rows | Rows Removed | Reason |
|---|---:|---:|---|
| Raw ingestion | ... | — | — |
| Schema validation | ... | ... | malformed records |
| Deduplication | ... | ... | confirmed duplicates |
| ML eligibility filter | ... | ... | cancelled/no valid target |
| Final ML dataset | ... | — | — |

---

# 32. Reproducibility

The entire pipeline should be runnable from raw files.

Preferred commands:

```bash
python scripts/run_ingestion.py
python scripts/run_etl.py
python scripts/build_database.py
python scripts/train_models.py
python scripts/export_powerbi.py
```

Optional master command:

```bash
python -m src.pipeline
```

If a master pipeline is implemented, individual stage commands should still remain understandable.

---

# 33. Configuration

Do not hard-code important project decisions throughout the codebase.

Put them in:

```text
config/settings.yaml
```

Example:

```yaml
project:
  start_year: 2025
  end_year: 2025

target:
  severe_delay_minutes: 60

paths:
  raw_bts: data/raw/bts
  raw_airports: data/raw/airports/airports.csv
  processed: data/processed
  database: database/airline_dw.sqlite

features:
  include_historical_features: false

model:
  train_end_date: 2025-08-31
  validation_end_date: 2025-10-31
  test_end_date: 2025-12-31
  random_state: 42
```

---

# 34. Notebook Structure

The notebooks are for explanation, visual evidence, and viva readability.

Core production logic should live in `src/`.

## `01_data_audit.ipynb`

Show:

- source overview
- shapes
- columns
- data types
- missing values
- duplicates
- basic statistics

## `02_cleaning_and_transformation.ipynb`

Show:

- cleaning decisions
- before/after examples
- transformation logic
- airport join
- engineered features
- quality validation

## `03_eda_and_insights.ipynb`

Show:

- operational analysis
- key visualizations
- candidate insights
- final evidence-backed insights

## `04_machine_learning.ipynb`

Show:

- target definition
- feature selection
- leakage explanation
- train/test split
- preprocessing
- baseline
- model comparison
- evaluation

## `05_model_interpretation.ipynb`

Show:

- feature importance
- error analysis
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

# 37. Suggested Project Milestones

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

- [x] airline analysis (first pass)
- [x] airport analysis (first pass)
- [x] route analysis (first pass)
- [x] time analysis (first pass)
- [x] cancellation analysis (first pass)
- [x] delay-cause analysis (first pass)
- [x] 3+ evidence-backed candidate insights

## Milestone 7 — ML

- [x] finalize target (ARR_DELAY > 60 on eligible completed flights)
- [x] leakage-safe candidate feature allowlist (no fitted preprocessing yet)
- [x] chronological split (Jan–Aug / Sep–Oct / Nov–Dec)
- [ ] baseline
- [ ] Logistic Regression
- [ ] Decision Tree
- [ ] Random Forest
- [ ] evaluate metrics
- [ ] interpret best model

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
- at least a baseline plus two ML models are evaluated,
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

6. **Never use target-leaking post-flight fields as predictors.**
7. Never use `ArrDelay`, `ArrDelayMinutes`, `ArrDel15`, or delay-cause columns to predict severe arrival delay.
8. Do not use test data to fit preprocessing.
9. Do not calculate full-dataset target averages and use them as historical predictors.
10. Do not optimize only for accuracy if the target is imbalanced.
11. Do not fabricate model results.
12. Do not change the target threshold merely because a different threshold gives better metrics.

## Analysis

13. Do not state an insight until it is calculated from the data.
14. Distinguish correlation/association from causation.
15. Apply sensible minimum-flight thresholds to "best/worst" airline, airport, and route rankings.
16. Preserve both average and median delay where outliers make the mean misleading.

## Engineering

17. Avoid loading the entire full-year raw dataset into memory when a chunked/partitioned approach is safer.
18. Keep production code in `src/`; notebooks should call reusable functions.
19. Add tests for critical cleaning and feature logic.
20. Prefer simple, explainable implementation over unnecessary complexity.

---

# 40. First Tasks for Codex CLI

When this file is first given to Codex, begin with the following sequence.

## Step 1 — Inspect Existing Directory

Do not overwrite existing work.

Identify:

- current files
- available raw datasets
- Python version
- existing virtual environment
- installed dependencies

## Step 2 — Scaffold Missing Project Structure

Create only missing directories/files described above.

## Step 3 — Create Setup Files

Generate:

```text
README.md
requirements.txt
.gitignore
config/settings.yaml
```

The `.gitignore` should exclude large raw/processed datasets, database files if appropriate, environments, caches, and trained model binaries unless deliberately versioned.

## Step 4 — Build a Data Manifest Tool

Before writing ML code, create a script that scans:

```text
data/raw/bts/
```

and reports:

- which months from 2025 are present,
- which are missing,
- filename,
- file size,
- row count where feasible,
- columns,
- schema differences.

Expected output:

```text
reports/source_manifest.csv
```

## Step 5 — Implement Ingestion

Implement robust multi-file ingestion and schema standardization.

## Step 6 — Stop and Report

After ingestion infrastructure exists, report:

- files detected,
- missing months,
- schema inconsistencies,
- approximate total rows,
- next recommended action.

Do not jump immediately to model training before data quality is understood.

---

# 41. Suggested Initial Prompt to Codex CLI

After placing this file in the repository, use something close to:

```text
Read PROJECT_PLAN.md completely and treat it as the project's source of truth.

Start by inspecting the existing repository and raw-data directories. Do not modify any raw data.

Then:
1. scaffold only the missing repository structure,
2. create the Python environment/dependency files,
3. implement a BTS source-manifest/audit script,
4. detect which 2025 monthly files are present or missing,
5. inspect schema consistency across the available files,
6. implement the ingestion layer and interim partitioned output,
7. add basic tests for ingestion/schema validation,
8. update README.md with exact commands to run what you implemented.

Do not build the ML models yet. Do not fabricate data or results. Follow all leakage and cleaning guardrails in PROJECT_PLAN.md.

At the end, summarize exactly what was created, what data was found, any issues, and the next recommended implementation step.
```

---

# 42. Future Optional Extensions

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

# 43. Key Viva Explanation

A concise explanation of the project:

> We are using the U.S. Bureau of Transportation Statistics Reporting Carrier On-Time Performance dataset for all flights reported from January through December 2025, along with airport metadata from OurAirports. We will take the raw data through the complete data-wrangling pipeline: extraction, cleaning, transformation, joining, feature engineering, validation, and SQL loading. We will then analyze airline, airport, route, and time-based delay patterns and build a classification model that predicts whether a completed flight will have an arrival delay of more than 60 minutes using only information available before departure. Finally, we will communicate the operational and model insights through a three-page Power BI dashboard.

---

# 44. Final Project Philosophy

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
