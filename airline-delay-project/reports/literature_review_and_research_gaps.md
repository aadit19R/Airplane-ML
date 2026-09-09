# Literature Review, Research Gaps, and Problem Definition

## Project context

This review supports the project **Airline Flight Delay Prediction and Operational Performance Analysis**. The proposed machine-learning task is to predict whether a scheduled domestic U.S. flight will arrive more than 60 minutes late using information available before departure.

The review uses ten relevant research papers. Two limitations are recorded for each paper, producing twenty paper-level drawbacks. Repeated drawbacks are then consolidated into broader research gaps. Only three gaps are selected for this project.

### Evidence convention

- **Author-reported** means the issue is stated by the paper itself.
- **Critical appraisal** means the issue follows from the paper's published dataset, features, experimental design, or scope. It should not be presented as a quotation from the authors.

This distinction is important because a research limitation can be valid even when the original authors did not explicitly label it as a limitation.

## Review of ten papers

### Paper 1 — Rebollo and Balakrishnan (2014)

**Paper:** [Characterization and prediction of air traffic delays](https://doi.org/10.1016/j.trc.2014.04.007), *Transportation Research Part C*, 44, 231–241.

**What it did:** Used Random Forest models and spatial/network delay-state variables to predict departure delays 2–24 hours ahead. Models were trained and validated using U.S. operational data from 2007 and 2008.

**Drawbacks:**

1. **Critical appraisal — restricted evaluation population:** Evaluation focused on the 100 most-delayed origin–destination links. Performance on ordinary and low-volume routes was therefore not established.
2. **Critical appraisal — temporal relevance:** The evidence came from 2007–2008. Airline networks, traffic volumes, and operational practices can change, so the measured performance may not transfer to current operations.

### Paper 2 — Belcastro et al. (2016)

**Paper:** [Using Scalable Data Mining for Predicting Flight Delays](https://doi.org/10.1145/2888402), *ACM Transactions on Intelligent Systems and Technology*, 8(1), Article 5.

**What it did:** Combined U.S. flight and weather observations in a cloud-based Random Forest pipeline. It tested several thresholds, including a 60-minute delay threshold.

**Drawbacks:**

1. **Critical appraisal — altered class prevalence:** The evaluation created balanced train/test data by shuffling and sampling delayed and on-time records. This is useful experimentally, but it does not preserve the real frequency of severe delays faced in operation.
2. **Critical appraisal — external-data dependency:** The strongest models depended on multiple weather observations at both airports. Such observations or equivalent forecasts may not always be consistently available at the required prediction time.

### Paper 3 — McCarthy, Karzand, and Lecue (2019)

**Paper:** [Amsterdam to Dublin Eventually Delayed? LSTM and Transfer Learning for Predicting Delays of Low Cost Airlines](https://doi.org/10.1609/aaai.v33i01.33019541), *Proceedings of AAAI*, 33(01), 9541–9546.

**What it did:** Used LSTM sequence models and transfer learning to predict delays for European low-cost airlines, including carriers with relatively little training data.

**Drawbacks:**

1. **Author-reported — limited feature breadth:** The authors identify the quantity and breadth of data as a bottleneck and state that large departure delays may be caused by factors absent from their feature set.
2. **Critical appraisal — carrier-specific scope:** The empirical results concern a small set of European low-cost airlines. Generalization to a nationwide U.S. network and different airline business models was not demonstrated.

### Paper 4 — Guan et al. (2020)

**Paper:** [Flight Delay Prediction Based on Aviation Big Data and Machine Learning](https://doi.org/10.1109/TVT.2019.2954094), *IEEE Transactions on Vehicular Technology*, 69(1), 140–150.

**What it did:** Integrated ADS-B messages, weather, schedules, and airport information, then compared classification and regression models.

**Drawbacks:**

1. **Author-reported — limited data and overfitting:** The paper reports that its LSTM overfit the limited dataset.
2. **Critical appraisal — difficult deployment inputs:** The approach requires several synchronized sources, including ADS-B and weather data. This increases missing-data, timing, integration, and real-time deployment requirements.

### Paper 5 — Lambelho et al. (2020)

**Paper:** [Assessing strategic flight schedules at an airport using machine learning-based flight delay and cancellation predictions](https://doi.org/10.1016/j.jairtraman.2019.101737), *Journal of Air Transport Management*, 82, 101737.

**What it did:** Predicted delays and cancellations to assess ten strategic schedules from 2013–2018 at London Heathrow Airport, up to six months before operations.

**Drawbacks:**

1. **Critical appraisal — single-airport setting:** The study demonstrates the method only at Heathrow, a highly constrained slot-coordinated European hub. Transfer to other airports and regulatory settings was not tested.
2. **Critical appraisal — different decision problem:** Its goal is strategic schedule assessment rather than individual-flight severe arrival-delay classification shortly before departure. Its results are not directly comparable with passenger-facing severe-delay prediction.

### Paper 6 — Zoutendijk and Mitici (2021)

**Paper:** [Probabilistic Flight Delay Predictions Using Machine Learning and Applications to the Flight-to-Gate Assignment Problem](https://doi.org/10.3390/aerospace8060152), *Aerospace*, 8(6), 152.

**What it did:** Used Mixture Density Networks and Random Forest regression to produce probabilistic delay estimates and applied them to gate assignment at Rotterdam The Hague Airport.

**Drawbacks:**

1. **Author-reported — airport scale:** Future work explicitly proposes testing the gate-assignment approach at a larger airport, meaning the original operational application was not validated at large-hub scale.
2. **Author-reported — narrow downstream application:** The paper identifies other airport operations, such as sequencing and scheduling, as future work. The demonstrated benefit is therefore specific to flight-to-gate assignment.

### Paper 7 — Kiliç and Sallan (2023)

**Paper:** [Study of Delay Prediction in the US Airport Network](https://doi.org/10.3390/aerospace10040342), *Aerospace*, 10(4), 342.

**What it did:** Compared four machine-learning models using 2017 U.S. BTS flight data joined with NOAA weather data.

**Drawbacks:**

1. **Author-reported — weak minority-class precision:** The models performed poorly in precision, which the authors connect to the large, imbalanced dataset. A model can therefore create many false delay alerts even when its overall accuracy appears acceptable.
2. **Critical appraisal — one-year validation:** The study uses 2017 data only. It does not establish whether performance remains stable across later operating conditions or structural changes.

### Paper 8 — Li, Guan, and Liu (2023)

**Paper:** [A CNN-LSTM framework for flight delay prediction](https://doi.org/10.1016/j.eswa.2023.120287), *Expert Systems with Applications*, 227, 120287.

**What it did:** Combined CNN, LSTM, feature fusion, and Random Forest components to model spatial and temporal correlations using U.S. domestic flights from 2019.

**Drawbacks:**

1. **Critical appraisal — high system complexity:** The multi-stage CNN–LSTM–Random Forest design is more difficult to train, reproduce, explain, and deploy than a conventional baseline or tree ensemble.
2. **Critical appraisal — demanding time-sensitive inputs:** The model uses recent/current weather, recent delays, and congestion. Operational use requires a precise prediction cut-off and reliable live inputs; otherwise feature availability or leakage can become unclear.

### Paper 9 — Hatıpoğlu and Tosun (2024)

**Paper:** [Predictive Modeling of Flight Delays at an Airport Using Machine Learning Methods](https://doi.org/10.3390/app14135472), *Applied Sciences*, 14(13), 5472.

**What it did:** Compared seven algorithms, weather features, SMOTE, Bayesian tuning, and SHAP using 40,077 flights from one Turkish airport during 2016–2018.

**Drawbacks:**

1. **Critical appraisal — small, local dataset:** Evidence from one airport and approximately 40,000 flights may not generalize to a national network containing different airports, routes, and airline practices.
2. **Author-reported result — balancing is not automatically beneficial:** SMOTE improved some training results but did not consistently improve testing performance; recall sometimes decreased. Synthetic balancing therefore requires careful validation.

### Paper 10 — AlBassam and AlShahrani (2025)

**Paper:** [Flight delay prediction: Evaluating machine learning algorithms for enhanced accuracy](https://doi.org/10.1371/journal.pone.0335141), *PLOS ONE*, 20(12), e0335141.

**What it did:** Compared six classifiers and three resampling methods using a Kaggle flight-status dataset covering 2018–2022.

**Drawbacks:**

1. **Critical appraisal — direct target leakage risk:** The selected predictors listed in the paper include actual arrival time, arrival delay, operational delay-cause fields, and `DelayCategory`. These are known after the outcome, and `DelayCategory` is derived from the delay itself. They cannot support a genuine pre-departure prediction claim.
2. **Critical appraisal plus author-reported limitation — optimistic validation/generalization risk:** The paper uses a random 80/20 split despite temporal dependence in flight data. The authors separately acknowledge that transfer to other countries, regulations, and airline operating patterns remains unresolved.

## From twenty drawbacks to consolidated research gaps

The same issue appears in several papers under slightly different forms. Counting every repetition as a new gap would inflate the literature review, so the twenty drawbacks above are consolidated below.

| Consolidated gap | Repeated evidence in the reviewed papers | Why it matters |
|---|---|---|
| G1. Restricted geographic or operational scope | P1, P3, P4, P5, P6, P9, P10 | A result from selected routes, one airport, or a few airlines may not transfer to a national network. |
| G2. Limited temporal validity or unrealistic validation | P1, P7, P8, P9, P10 | Old/one-year data and random splits can overstate performance on future flights. |
| G3. Inadequate treatment of rare delayed flights | P2, P7, P9, P10 | Accuracy can look high while the model misses severe delays or produces too many false alerts. |
| G4. Feature leakage or uncertain prediction-time availability | P2, P4, P8, P10 | A model is unusable if it needs information that is unavailable at the promised prediction time. |
| G5. High model/data/deployment complexity | P3, P4, P8 | Complex pipelines are harder to reproduce, explain, and operate reliably. |
| G6. Inconsistent target and decision definitions | P1, P2, P5, P6 | Studies predict different thresholds, continuous delays, departure delays, schedule risk, or gate conflicts, so reported scores are not directly comparable. |
| G7. Limited interpretability or actionability | P5, P6, P8 | A high score alone does not tell airlines, airports, or passengers why risk is high or how the result can be used. |
| G8. Weak treatment of extreme-event uncertainty | P3, P6, P7 | Rare, high-impact delays are difficult to learn and are often the outcomes stakeholders care about most. |

The 2025 review by Wandelt, Chen, and Sun independently reports heterogeneity in data processing, evaluation, technology integration, and reproducibility across recent flight-delay studies: [Flight Delay Prediction: A Dissecting Review of Recent Studies Using Machine Learning](https://doi.org/10.1109/TITS.2025.3528536). This supports treating the repeated drawbacks as field-level gaps rather than isolated mistakes.

## Three gaps selected for this project

### Selected Gap 1 — Prediction-time realism and leakage control

**Problem in prior work:** Some published models depend on actual flight outcomes, reported delay causes, recent operational states without a clear cut-off, or multiple external feeds that may not be available when a prediction is promised.

**How this project addresses it:**

- Define the prediction point as **before scheduled departure**.
- Use only schedule/date, airline, origin, destination, route, distance, and static airport metadata that are available before departure.
- Exclude actual departure/arrival times, departure delay, arrival delay, actual duration, air time, cancellation reason, and reported delay-cause minutes from predictors.
- Derive the label `severe_delay = 1` only when `ARR_DELAY > 60` for completed, non-diverted flights with known arrival outcomes.
- Maintain an explicit allowed-feature list and blocked-feature list in the ML notebook.

### Selected Gap 2 — Broad-network evaluation with a chronological holdout

**Problem in prior work:** Many studies use one airport, a few airlines, selected high-delay routes, old observations, or random train/test splits. This limits spatial generalization and can allow future operating patterns to influence model selection.

**How this project addresses it:**

- Use all 7,001,619 scheduled domestic U.S. flight records from January–December 2025 rather than selecting only the most delayed routes or airports.
- Include 352 matched origin and destination airport codes and multiple reporting airlines.
- Split in time: January–August for training, September–October for validation, and November–December for final testing.
- Report performance by month and, where sample sizes allow, by airline, airport, and route—not only one network-wide average.

**Boundary:** This is still a within-2025 future holdout. It improves temporal honesty but does not prove year-over-year or international generalization.

### Selected Gap 3 — Imbalance-aware severe-delay evaluation

**Problem in prior work:** Severe delays are uncommon, so overall accuracy can be dominated by on-time flights. Artificial balancing can also distort the real test distribution or fail to improve minority-class performance.

**How this project addresses it:**

- Preserve the natural severe-delay frequency in validation and test data; the observed 2025 severe-delay rate is 8.04%.
- Start with a majority-class baseline so the ML models must beat a transparent reference.
- Compare a simple Logistic Regression model with tree-based models using class weights where supported.
- Apply any resampling only to training data, never before the chronological split and never to validation/test data.
- Report severe-delay precision, recall, F1-score, PR-AUC, ROC-AUC, balanced accuracy, and a confusion matrix instead of relying on accuracy alone.
- Interpret false negatives and false positives in operational terms.

## Problem definition

Existing flight-delay studies often report strong performance in restricted settings or under evaluations that do not fully represent future operations. Results may be based on a single airport, selected routes, limited time periods, artificially balanced samples, random data splits, or features that are known only after a flight has departed or completed. These choices reduce generalizability and can hide poor detection of rare but operationally important severe delays.

**Therefore, this research will develop and evaluate an explainable, leakage-controlled, and imbalance-aware machine-learning pipeline for predicting whether a scheduled domestic U.S. flight will arrive more than 60 minutes late. The study will use only information available before departure, cover the full 2025 BTS domestic network represented in the project data, and evaluate models on later months using the natural class distribution and minority-sensitive metrics.**

## Research question and objectives

### Primary research question

How accurately can severe arrival delays of more than 60 minutes be predicted for scheduled domestic U.S. flights using only information available before departure?

### Objectives

1. Build a leakage-controlled feature set from BTS schedules and static OurAirports metadata.
2. Compare an interpretable baseline with conventional machine-learning classifiers.
3. Evaluate genuine future-month performance using a chronological train/validation/test split.
4. Measure severe-delay detection with precision, recall, F1, PR-AUC, ROC-AUC, balanced accuracy, and confusion matrices.
5. Explain the most influential pre-departure factors and compare errors across time and operational groups.

## Gaps intentionally not claimed as solved

This project does **not** claim to solve every gap found in the literature:

- It does not incorporate live weather, ADS-B, crew, aircraft-rotation, or air-traffic-control feeds.
- It does not model network delay propagation with graph neural networks.
- It does not provide causal conclusions or prescribe delay-mitigation actions.
- It does not quantify full predictive uncertainty.
- It does not prove performance outside the United States or beyond 2025.

These remain project limitations or possible future work. Keeping them outside the three selected gaps makes the contribution achievable and honest.

## References

1. Rebollo, J. J., & Balakrishnan, H. (2014). Characterization and prediction of air traffic delays. *Transportation Research Part C: Emerging Technologies, 44*, 231–241. https://doi.org/10.1016/j.trc.2014.04.007
2. Belcastro, L., Marozzo, F., Talia, D., & Trunfio, P. (2016). Using scalable data mining for predicting flight delays. *ACM Transactions on Intelligent Systems and Technology, 8*(1), Article 5. https://doi.org/10.1145/2888402
3. McCarthy, N., Karzand, M., & Lecue, F. (2019). Amsterdam to Dublin eventually delayed? LSTM and transfer learning for predicting delays of low cost airlines. *Proceedings of the AAAI Conference on Artificial Intelligence, 33*(01), 9541–9546. https://doi.org/10.1609/aaai.v33i01.33019541
4. Guan, G., Liu, F., Sun, J., Yang, J., Zhou, Z., & Zhao, D. (2020). Flight delay prediction based on aviation big data and machine learning. *IEEE Transactions on Vehicular Technology, 69*(1), 140–150. https://doi.org/10.1109/TVT.2019.2954094
5. Lambelho, M., Mitici, M., Pickup, S., & Marsden, A. (2020). Assessing strategic flight schedules at an airport using machine learning-based flight delay and cancellation predictions. *Journal of Air Transport Management, 82*, 101737. https://doi.org/10.1016/j.jairtraman.2019.101737
6. Zoutendijk, M., & Mitici, M. (2021). Probabilistic flight delay predictions using machine learning and applications to the flight-to-gate assignment problem. *Aerospace, 8*(6), 152. https://doi.org/10.3390/aerospace8060152
7. Kiliç, K., & Sallan, J. M. (2023). Study of delay prediction in the US airport network. *Aerospace, 10*(4), 342. https://doi.org/10.3390/aerospace10040342
8. Li, Q., Guan, X., & Liu, J. (2023). A CNN-LSTM framework for flight delay prediction. *Expert Systems with Applications, 227*, 120287. https://doi.org/10.1016/j.eswa.2023.120287
9. Hatıpoğlu, I., & Tosun, Ö. (2024). Predictive modeling of flight delays at an airport using machine learning methods. *Applied Sciences, 14*(13), 5472. https://doi.org/10.3390/app14135472
10. AlBassam, S. A. A., & AlShahrani, S. D. N. (2025). Flight delay prediction: Evaluating machine learning algorithms for enhanced accuracy. *PLOS ONE, 20*(12), e0335141. https://doi.org/10.1371/journal.pone.0335141

**Supporting review:** Wandelt, S., Chen, X., & Sun, X. (2025). Flight delay prediction: A dissecting review of recent studies using machine learning. *IEEE Transactions on Intelligent Transportation Systems, 26*(4), 4283–4297. https://doi.org/10.1109/TITS.2025.3528536

## Short viva-ready explanation

> I reviewed ten flight-delay papers and recorded two drawbacks from each. Several drawbacks repeated, so I grouped them into broader gaps instead of treating all twenty as unique. I selected three gaps that match my data and course scope: preventing post-outcome feature leakage, evaluating a broad U.S. network with a chronological split, and measuring rare severe delays with imbalance-aware metrics. These gaps lead directly to my problem definition: predicting arrival delays above 60 minutes using only pre-departure information and testing the model on later months.
