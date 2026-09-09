# Cleaning and Transformation Log

## Action 001 — Raw file organization

**Issue:** Monthly files used inconsistent download names.  
**Rows affected:** 7,001,619  
**Action:** Files were moved without content changes and renamed `bts_ontime_2025_01.csv` through `bts_ontime_2025_12.csv`.  
**Reason:** Stable names make monthly ingestion reproducible while preserving raw data.

## Action 002 — Column standardization

**Issue:** BTS source columns use uppercase names that differ from analysis naming conventions.  
**Rows affected:** 7,001,619  
**Action:** Column names are mapped to documented snake_case names in memory.  
**Reason:** Consistent names simplify reusable cleaning and analysis code. Raw files remain unchanged.

## Action 003 — Data types and categorical text

**Issue:** CSV inference can mix numeric and text representations, and code fields can contain whitespace.  
**Rows affected:** 7,001,619  
**Action:** Dates are parsed, numeric measures are coerced to numeric, and airline/airport/cancellation codes are trimmed and uppercased in the derived data. Five nonpositive scheduled-duration sentinel values are flagged and converted to null in the derived layer.  
**Reason:** This makes comparisons and validation reliable without inventing values; an impossible duration must not be used by the later model.

## Action 004 — Missing operational values

**Issue:** Actual times, arrival delay, elapsed time, and air time can be missing for cancelled or diverted flights.  
**Rows affected:** See `reports/tables/column_profile.csv`.  
**Action:** Missing operational values were retained. No blanket imputation or `dropna()` was applied.  
**Reason:** These nulls can describe a flight outcome and should not be converted to fictional values.

## Action 005 — Duplicate candidates

**Issue:** 0 exact duplicate rows and 0 business-key duplicate rows after first occurrences were detected.  
**Rows affected:** 0 candidate rows.  
**Action:** Candidates were measured but not automatically deleted.  
**Reason:** Repeated-looking scheduled flights require investigation before removal.

## Action 006 — Feature engineering

**Issue:** Analysis and ML need consistent route, time, calendar, and target features.  
**Rows affected:** 7,001,619  
**Action:** Created route, scheduled departure hour, departure time band, weekend flag, season, delay category, target eligibility, and severe-delay target in the derived analysis layer. BTS `2400` is treated as midnight.  
**Reason:** These features directly support the research questions and are explainable in the viva.

## Action 007 — Severe-delay target governance

**Issue:** Cancelled/diverted flights do not have a comparable scheduled-destination arrival outcome.  
**Rows affected:** 122,135 excluded from target construction.  
**Action:** Severe delay is set only for completed, non-diverted flights with a known arrival delay; the threshold is `ARR_DELAY > 60`.  
**Reason:** This avoids labelling cancellations as arrival delays and prevents fabricated targets.

## Action 008 — Airport reference standardization

**Issue:** OurAirports contains missing and duplicate IATA codes.  
**Rows affected:** 86,053 airport-source rows.  
**Action:** Retained valid three-letter IATA codes and selected one deterministic record per code, prioritizing U.S., scheduled-service, then larger airport types. Added a documented `PBI -> DJT` alias because the supplied current airport file stores `DJT` as the IATA code while its keywords retain the historical 2025 BTS code `PBI`.  
**Reason:** The airport join must use IATA codes, preserve historical flight codes, and remain auditable.

## Items intentionally left for the next cleaning pass

- Continue duplicate checks on every refresh; the current 2025 files contain no duplicate candidates.
- Persist the standardized flight partitions after the final retained-column schema is approved.
- Add airport surrogate keys and enforce fact-to-dimension foreign-key checks during warehouse construction.
- Review extreme delay values with route/date context; do not remove them solely by statistical cutoff.
