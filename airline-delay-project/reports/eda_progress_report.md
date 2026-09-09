# Initial EDA Progress Report — BTS 2025

This report covers the first full-pass EDA across all monthly files. Rankings use minimum-volume thresholds from `config/settings.yaml`.

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
