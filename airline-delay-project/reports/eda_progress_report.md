# Completed Cleaning and EDA Report — BTS 2025

This report covers the completed descriptive EDA across all monthly files. Rankings use minimum-volume thresholds from `config/settings.yaml`.

## Overall performance

- Scheduled flight rows: **7,001,619**
- Cancelled flights: **102,876** (1.47%)
- Diverted flights: **19,258** (0.28%)
- Average arrival delay among target-eligible flights: **8.50 minutes**
- Median arrival delay among target-eligible flights: **-6.00 minutes**
- Severe-delay rate (`ARR_DELAY > 60`): **8.04%**
- On-time/early rate (`ARR_DELAY <= 0`): **62.43%**

## Evidence-backed findings

1. **Highest monthly severe-delay rate:** Month 7 had a severe-delay rate of **11.89%** across 612,811 eligible flights.
2. **Departure-time pattern:** **Evening** departures had the highest severe-delay rate at **12.34%**, compared with the network rate of 8.04%.
3. **Airline comparison:** Among airlines with at least 10,000 flights, **OH** had the highest severe-delay rate at **12.12%**.
4. **High-volume route comparison:** Among routes with at least 1,000 flights, **ASE-DFW** had the highest severe-delay rate at **19.15%**.
5. **Reported delay causes:** **Late Aircraft** contributed the largest share of reported cause-delay minutes at **39.19%**. These fields are descriptive only and will not be ML predictors.

## Completed EDA areas

- Overall volume, cancellation, diversion, delay, severe-delay, and on-time measures
- Airline, origin, destination, and route performance tables
- Month, day-of-week, scheduled-hour, time-band, weekend, and season tables
- Cancellation-code counts and reported delay-cause composition
- Airport-code join coverage against the standardized OurAirports dimension
- Four reproducible figures in `reports/figures/`

## Final EDA additions

- Expanded notebook with raw audit, explicit cleaning operations, and decisions.
- Reviewed all six flagged records and 20 delay extremes without dropping flights.
- Exact full-year, monthly, airline, and busiest-route/origin mean/median/quantiles.
- Distribution plots using a documented 2,000-flight-per-month sample.
- Highest/lowest origin-rate comparisons with minimum-volume filters.
- Airport-month cancellation and route-month severe-delay heatmaps.
- Full row reconciliation and an explicit ML feature/split handoff.

The new figures are reproduced by `python scripts/execute_notebooks.py` after ETL.

## Limitations at this checkpoint

- Results cover only 2025 and cannot establish year-over-year trends.
- Airline codes are not expanded to names until an authoritative airline lookup is added.
- Reported delay-cause fields describe delays after they occur and cannot be used for pre-departure prediction.
- Associations do not establish causal effects.

- Full-year EDA includes holdout outcomes; future model tuning must still respect the frozen chronological split.
