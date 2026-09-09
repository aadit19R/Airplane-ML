#!/usr/bin/env python3
"""Create a concise viva handout from the project plan and literature review."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "airline_delay_viva_research_brief.pdf"
FIGURES = ROOT / "reports" / "figures"

NAVY = colors.HexColor("#12355B")
BLUE = colors.HexColor("#2E6F95")
TEAL = colors.HexColor("#2A9D8F")
ORANGE = colors.HexColor("#E76F51")
PALE_BLUE = colors.HexColor("#EAF3F8")
PALE_ORANGE = colors.HexColor("#FDECE8")
DARK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#5B6470")
WHITE = colors.white


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=25,
            leading=30, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=12,
            leading=17, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=17,
            leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=9,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12,
            leading=15, textColor=BLUE, spaceBefore=8, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.3,
            leading=13.2, textColor=DARK, spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.6,
            leading=10.1, textColor=DARK, spaceAfter=3,
        ),
        "tiny": ParagraphStyle(
            "tiny", parent=base["BodyText"], fontName="Helvetica", fontSize=6.6,
            leading=8.4, textColor=DARK, spaceAfter=2,
        ),
        "callout": ParagraphStyle(
            "callout", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=11,
            leading=15, textColor=NAVY, alignment=TA_LEFT, spaceAfter=0,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=7.3,
            leading=9.3, textColor=MUTED, alignment=TA_CENTER, spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["BodyText"], fontName="Helvetica", fontSize=7,
            leading=8, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


S = styles()


def p(text, style="body"):
    return Paragraph(text, S[style])


def bullet(text):
    return Paragraph(f"&bull; {text}", S["body"])


def section(title):
    return [Spacer(1, 3), p(title, "h1")]


def shaded_callout(text, color=PALE_BLUE):
    table = Table([[p(text, "callout")]], colWidths=[17.0 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("BOX", (0, 0), (-1, -1), 0.5, BLUE),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def stat_card(label, value, note):
    return [p(value, "callout"), p(f"<b>{label}</b><br/>{note}", "small")]


def table(data, widths, header=True, font_size=7.4, row_colors=True):
    wrapped = []
    for row_index, row in enumerate(data):
        row_style = "small" if row_index else "small"
        wrapped.append([cell if hasattr(cell, "wrap") else p(str(cell), row_style) for cell in row])
    result = Table(wrapped, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D5E2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    if row_colors:
        for idx in range(1 if header else 0, len(data)):
            if idx % 2 == 0:
                style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F7FAFC")))
    result.setStyle(TableStyle(style))
    return result


def chart(path, width, height):
    image = Image(str(path), width=width, height=height)
    return image


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(1.5 * cm, 1.35 * cm, width - 1.5 * cm, 1.35 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1.5 * cm, 0.82 * cm, "Airline Delay Project - Viva Research Brief")
    canvas.drawRightString(width - 1.5 * cm, 0.82 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=1.65 * cm, leftMargin=1.65 * cm,
        topMargin=1.55 * cm, bottomMargin=1.75 * cm,
        title="Airline Delay Project - Viva Research Brief",
        author="Airline Delay Project",
    )
    story = []

    # Cover
    story.extend([
        Spacer(1, 2.4 * cm),
        p("AIRLINE DELAY PROJECT", "title"),
        p("Viva Research Brief", "title"),
        Spacer(1, 0.4 * cm),
        p("Airline Flight Delay Prediction and Operational Performance Analysis", "subtitle"),
        p("Data wrangling, exploratory analysis, literature review, research gaps, and planned machine learning", "subtitle"),
        Spacer(1, 1.1 * cm),
        shaded_callout(
            "<b>Primary question:</b> Can we predict whether a scheduled domestic U.S. flight will experience a severe arrival delay using only information available before departure?",
            PALE_BLUE,
        ),
        Spacer(1, 0.9 * cm),
    ])
    cover_stats = Table([
        stat_card("Flight records", "7,001,619", "BTS 2025 domestic flights"),
        stat_card("Airport codes matched", "352 / 352", "100% origin and destination coverage"),
        stat_card("Severe-delay rate", "8.04%", "Arrival delay greater than 60 minutes"),
    ], colWidths=[5.65 * cm, 5.65 * cm, 5.65 * cm])
    cover_stats.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([
        cover_stats,
        Spacer(1, 1.0 * cm),
        p("Prepared from PROJECT_PLAN.md and the literature review and research-gap analysis. Current checkpoint: 9 September 2026.", "subtitle"),
        PageBreak(),
    ])

    # Project overview
    story += section("1. Project overview")
    story.append(p(
        "This project uses the U.S. Bureau of Transportation Statistics (BTS) Reporting Carrier On-Time Performance data for January-December 2025 and OurAirports metadata. It turns raw, operational flight records into an auditable data-wrangling pipeline, evidence-backed analysis, a leakage-safe machine-learning task, and Power BI-ready outputs."
    ))
    story.append(p("<b>Two project goals</b>", "h2"))
    story.extend([
        bullet("<b>Operational analysis:</b> identify airline, airport, route, calendar, and departure-time patterns associated with delays and cancellations."),
        bullet("<b>Machine learning:</b> classify a flight as severe-delay or not severe-delay before departure."),
    ])
    story.append(p("<b>Current implementation checkpoint</b>", "h2"))
    checkpoint = [
        ["Completed", "Evidence"],
        ["Source audit", "All 12 monthly files; 7,001,619 rows; consistent 28-column schema."],
        ["Cleaning and features", "Types, codes, route, scheduled hour, time band, weekend, season, delay category, and severe-delay target."],
        ["Airport dimension", "OurAirports standardized; all 352 BTS origin/destination codes matched, including one documented historical alias."],
        ["EDA", "Airline, airport, route, time, cancellation, and delay-cause tables; four reproducible figures and five candidate insights."],
        ["Literature review", "Ten papers, twenty drawbacks, eight consolidated gaps, and three selected research gaps."],
    ]
    story.append(table(checkpoint, [5.0 * cm, 12.0 * cm]))
    story.append(Spacer(1, 5))
    story.append(shaded_callout(
        "<b>Viva message:</b> The project is not just a prediction model. It demonstrates the full data journey: raw data -> cleaning -> transformation -> joining -> validation -> EDA -> ML -> dashboard communication."
    ))
    story.append(PageBreak())

    # Data and EDA
    story += section("2. Data, target, and evidence from EDA")
    data_rows = [
        ["Item", "Project decision"],
        ["Main source", "BTS Reporting Carrier On-Time Performance, all months of 2025."],
        ["Supporting source", "OurAirports airport metadata, joined on standardized IATA codes."],
        ["Unit of analysis", "One scheduled flight record."],
        ["Target", "Severe arrival delay: ARR_DELAY greater than 60 minutes."],
        ["Target eligibility", "Completed, non-diverted flights with a known arrival delay. Cancelled/diverted flights are not forced into the target."],
        ["Observed rate", "8.04% severe delay among 6,879,484 eligible flights."],
    ]
    story.append(table(data_rows, [4.4 * cm, 12.6 * cm]))
    story.append(p("<b>First-pass EDA findings</b>", "h2"))
    findings = [
        ["Finding", "Measured evidence"],
        ["Monthly pattern", "July had the highest severe-delay rate: 11.89% across 612,811 eligible flights."],
        ["Departure-time pattern", "Evening departures had the highest severe-delay rate: 12.34%, versus a network rate of 8.04%."],
        ["Airline comparison", "Among airlines with at least 10,000 flights, OH had the highest severe-delay rate: 12.12%."],
        ["Route comparison", "Among routes with at least 1,000 flights, ASE-DFW had the highest severe-delay rate: 19.15%."],
        ["Delay causes", "Late Aircraft represented the largest share of reported cause-delay minutes: 39.19%. These fields are descriptive only, not ML predictors."],
    ]
    story.append(table(findings, [5.0 * cm, 12.0 * cm]))
    story.append(Spacer(1, 6))
    monthly_path = FIGURES / "monthly_volume_and_severe_delay.png"
    band_path = FIGURES / "severe_delay_by_departure_band.png"
    if monthly_path.exists() and band_path.exists():
        charts = Table([[chart(monthly_path, 8.15 * cm, 4.48 * cm), chart(band_path, 8.15 * cm, 4.48 * cm)]], colWidths=[8.4 * cm, 8.4 * cm])
        charts.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        story.extend([charts, p("Figure 1. Flight volume and severe-delay patterns generated from the full 2025 project data.", "caption")])
    story.append(PageBreak())

    # Literature review
    story += section("3. Literature review: from papers to research gaps")
    story.append(p(
        "The literature review deliberately followed a simple chain: review papers, record drawbacks, combine repeated drawbacks into broader gaps, then select only the gaps that this project can credibly address. Each drawback was labelled either author-reported or critical appraisal."
    ))
    story.append(shaded_callout("10 research papers -> 20 paper-level drawbacks -> 8 recurring gaps -> 3 selected gaps", PALE_ORANGE))
    story.append(Spacer(1, 7))
    paper_matrix = [
        ["Paper", "Context", "Two main drawbacks"],
        ["Rebollo & Balakrishnan (2014)", "U.S. network, 2007-08", "Only 100 most-delayed links; older operating period."],
        ["Belcastro et al. (2016)", "U.S. flight + weather", "Balanced shuffled samples change real prevalence; weather-feed dependency."],
        ["McCarthy et al. (2019)", "European low-cost airlines", "Limited feature breadth; narrow carrier scope."],
        ["Guan et al. (2020)", "ADS-B + weather + schedule", "LSTM overfitting on limited data; multi-source deployment burden."],
        ["Lambelho et al. (2020)", "London Heathrow schedules", "Single-airport setting; strategic schedule problem differs from individual-flight risk."],
        ["Zoutendijk & Mitici (2021)", "Rotterdam gate assignment", "Not tested at large-hub scale; narrow downstream application."],
        ["Kilic & Sallan (2023)", "U.S. network, 2017", "Poor minority-class precision; one-year validation."],
        ["Li et al. (2023)", "U.S. network, CNN-LSTM", "Complex multi-stage system; time-sensitive input requirements."],
        ["Hatipoglu & Tosun (2024)", "One Turkish airport", "Small/local data; SMOTE did not consistently improve testing."],
        ["AlBassam & AlShahrani (2025)", "Kaggle flight-status data", "Post-outcome feature leakage risk; random holdout/generalization risk."],
    ]
    story.append(table(paper_matrix, [3.7 * cm, 3.4 * cm, 9.9 * cm], font_size=6.7))
    story.append(Spacer(1, 8))
    story.append(p("<b>Recurring gaps found across studies</b>", "h2"))
    gap_rows = [
        ["Gap", "Repeated in", "Meaning"],
        ["Restricted scope", "7 papers", "One airport, selected routes, or a few airlines may not represent a national network."],
        ["Weak temporal validation", "5 papers", "Old/one-year samples and random splits may not predict future flights honestly."],
        ["Rare-delay evaluation", "4 papers", "Accuracy can hide missed severe delays or excessive false alerts."],
        ["Leakage / availability", "4 papers", "Some inputs may be unavailable when the prediction is supposed to be made."],
        ["Complexity / deployment", "3 papers", "Advanced multi-source models can be difficult to reproduce and explain."],
    ]
    story.append(table(gap_rows, [4.0 * cm, 2.4 * cm, 10.6 * cm]))
    story.append(PageBreak())

    # selected gaps
    story += section("4. The three selected gaps and how this project addresses them")
    selected = [
        ["Selected gap", "How the project addresses it", "Evidence to show in the viva"],
        ["1. Prediction-time realism and leakage control", "Prediction point is before scheduled departure. Use only date/schedule, airline, airport, route, distance, and static airport metadata. Block actual times, delay values, cancellation fields, and reported delay causes.", "Allowed vs forbidden feature list; target governance; explanation of why post-flight fields cannot be used."],
        ["2. Broad-network evaluation with chronological holdout", "Use all 7,001,619 2025 flight records across 352 matched airport codes. Train Jan-Aug, validate Sep-Oct, and test Nov-Dec.", "Temporal split diagram; network-wide and subgroup performance; explicit within-2025 limitation."],
        ["3. Imbalance-aware severe-delay evaluation", "Keep natural 8.04% severe-delay rate in validation/test. Compare a majority baseline, Logistic Regression, Decision Tree, and Random Forest. Use class weights or training-only resampling if justified.", "Precision, recall, F1, PR-AUC, ROC-AUC, balanced accuracy, and confusion matrix - not accuracy alone."],
    ]
    story.append(table(selected, [4.25 * cm, 7.65 * cm, 5.1 * cm]))
    story.append(Spacer(1, 9))
    story.append(p("<b>Final problem definition</b>", "h2"))
    story.append(shaded_callout(
        "Existing flight-delay studies may report strong performance using restricted airport/route samples, random or artificially balanced evaluation, or variables unavailable before the outcome. This project will develop and evaluate an explainable, leakage-controlled, and imbalance-aware model to predict whether a scheduled domestic U.S. flight will arrive more than 60 minutes late, using only pre-departure information and a chronological future-month holdout.",
        PALE_BLUE,
    ))
    story.append(Spacer(1, 8))
    story.append(p("<b>Research objectives</b>", "h2"))
    objectives = [
        "Build a leakage-controlled feature set from BTS schedules and static OurAirports metadata.",
        "Compare a simple, interpretable baseline with conventional ML classifiers.",
        "Evaluate later-month performance using the chronological train/validation/test split.",
        "Measure severe-delay detection with minority-sensitive metrics.",
        "Explain influential pre-departure factors and analyse model errors by time and operational group.",
    ]
    story.extend([bullet(item) for item in objectives])
    story.append(PageBreak())

    # Method and pipeline
    story += section("5. Project method and planned outputs")
    story.append(p("<b>Data pipeline</b>", "h2"))
    pipeline = [
        ["1", "Raw BTS monthly files + OurAirports"],
        ["2", "Audit schema, missingness, data types, duplicates, dates, and numeric ranges"],
        ["3", "Clean and standardize without editing raw files or blindly dropping records"],
        ["4", "Create route, scheduled hour, departure-time band, weekend, season, delay category, and severe-delay target"],
        ["5", "Validate and join airport metadata; preserve row reconciliation and cleaning log"],
        ["6", "Persist data and create warehouse / Power BI-ready tables"],
        ["7", "Perform EDA, train leakage-safe models, interpret results, and communicate findings"],
    ]
    pipeline_table = Table([[p(f"<b>{step}</b>", "body"), p(desc, "body")] for step, desc in pipeline], colWidths=[1.0 * cm, 16.0 * cm])
    pipeline_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D5E2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(pipeline_table)
    story.append(Spacer(1, 9))
    story.append(p("<b>ML comparison plan</b>", "h2"))
    models = [
        ["Model", "Purpose", "Why it is viva-friendly"],
        ["Majority-class baseline", "Reference performance", "Shows why accuracy alone is insufficient."],
        ["Logistic Regression", "Simple ML baseline", "Coefficients are interpretable."],
        ["Decision Tree", "Non-linear comparison", "Easy to visualise and explain."],
        ["Random Forest", "Stronger ensemble", "Feature importance and robust comparison."],
    ]
    story.append(table(models, [4.4 * cm, 6.2 * cm, 6.4 * cm]))
    story.append(Spacer(1, 7))
    story.append(p("<b>Final communication outputs</b>", "h2"))
    story.extend([
        bullet("Viva-ready Jupyter notebooks for audit, cleaning, EDA, ML, and interpretation."),
        bullet("Cleaning log, data-quality report, source manifest, reproducible tables and figures."),
        bullet("SQLite / star-schema-style warehouse and Power BI-ready fact/dimension extracts."),
        bullet("Three-page Power BI dashboard: overall performance, airport/route drill-down, and ML insights."),
    ])
    story.append(PageBreak())

    # Boundaries and viva prompts
    story += section("6. Boundaries, limitations, and viva answers")
    story.append(p("<b>What this project intentionally does not claim to solve</b>", "h2"))
    boundaries = [
        ["Boundary", "Reason it matters"],
        ["No live weather, ADS-B, crew, aircraft-rotation, or ATC feeds", "The current scope prioritizes a reproducible, schedule-based project. These external inputs are future extensions."],
        ["No graph neural network or full network propagation model", "The project chooses simple, explainable models suitable for the course and viva."],
        ["No causal claims", "Feature importance and EDA associations do not prove that a factor causes delay."],
        ["No full uncertainty quantification", "The model is a classification risk tool, not a probabilistic operational dispatch system."],
        ["No year-over-year or international generalization claim", "The chronological holdout is within 2025 and U.S. domestic data only."],
    ]
    story.append(table(boundaries, [6.4 * cm, 10.6 * cm]))
    story.append(p("<b>Short answers for common viva questions</b>", "h2"))
    viva_rows = [
        ["Question", "Concise answer"],
        ["Why 60 minutes?", "It is a documented project-defined severe-delay threshold. It creates an operationally meaningful, minority-class target and is frozen before model comparison."],
        ["Why exclude cancelled flights from the target?", "A cancelled flight has no comparable arrival outcome. Labelling it as an arrival delay would fabricate the target."],
        ["Why not use departure delay or delay causes?", "They happen during or after the flight process and would leak outcome information into a pre-departure prediction model."],
        ["Why a chronological split?", "The model should learn from earlier flights and be tested on later flights. A random split can mix future patterns into evaluation."],
        ["Why more metrics than accuracy?", "Only 8.04% of eligible flights are severe delays. Accuracy can be high even if the model misses most severe cases."],
        ["What is the main contribution?", "A clear, reproducible, leakage-safe and imbalance-aware severe-delay prediction study over the full 2025 project network."],
    ]
    story.append(table(viva_rows, [5.0 * cm, 12.0 * cm]))
    story.append(Spacer(1, 8))
    story.append(shaded_callout(
        "<b>One-minute closing statement:</b> We use 2025 BTS flight data and airport metadata to build a complete data-wrangling project. After auditing, cleaning, joining, and analysing over seven million flights, we identified delay patterns and reviewed ten research papers. The review showed that leakage, narrow evaluation, and class imbalance are recurring weaknesses. Our model is designed around those three gaps: only pre-departure features, a chronological future-month test, and minority-sensitive evaluation for severe delays above 60 minutes.",
        PALE_ORANGE,
    ))
    story.append(PageBreak())

    # References
    story += section("Appendix. Research papers reviewed")
    story.append(p("The full paper-by-paper review, evidence labels, links, and detailed drawback matrix are retained in <i>reports/literature_review_and_research_gaps.md</i>.", "body"))
    refs = [
        "1. Rebollo, J. J., & Balakrishnan, H. (2014). Characterization and prediction of air traffic delays. Transportation Research Part C, 44, 231-241. doi:10.1016/j.trc.2014.04.007",
        "2. Belcastro, L., Marozzo, F., Talia, D., & Trunfio, P. (2016). Using scalable data mining for predicting flight delays. ACM TIST, 8(1), Article 5. doi:10.1145/2888402",
        "3. McCarthy, N., Karzand, M., & Lecue, F. (2019). Amsterdam to Dublin eventually delayed? LSTM and transfer learning for predicting delays of low cost airlines. AAAI, 33(01), 9541-9546. doi:10.1609/aaai.v33i01.33019541",
        "4. Guan, G., Liu, F., Sun, J., Yang, J., Zhou, Z., & Zhao, D. (2020). Flight delay prediction based on aviation big data and machine learning. IEEE TVT, 69(1), 140-150. doi:10.1109/TVT.2019.2954094",
        "5. Lambelho, M., Mitici, M., Pickup, S., & Marsden, A. (2020). Assessing strategic flight schedules at an airport using machine learning-based flight delay and cancellation predictions. Journal of Air Transport Management, 82, 101737. doi:10.1016/j.jairtraman.2019.101737",
        "6. Zoutendijk, M., & Mitici, M. (2021). Probabilistic flight delay predictions using machine learning and applications to the flight-to-gate assignment problem. Aerospace, 8(6), 152. doi:10.3390/aerospace8060152",
        "7. Kilic, K., & Sallan, J. M. (2023). Study of delay prediction in the US airport network. Aerospace, 10(4), 342. doi:10.3390/aerospace10040342",
        "8. Li, Q., Guan, X., & Liu, J. (2023). A CNN-LSTM framework for flight delay prediction. Expert Systems with Applications, 227, 120287. doi:10.1016/j.eswa.2023.120287",
        "9. Hatipoglu, I., & Tosun, O. (2024). Predictive modeling of flight delays at an airport using machine learning methods. Applied Sciences, 14(13), 5472. doi:10.3390/app14135472",
        "10. AlBassam, S. A. A., & AlShahrani, S. D. N. (2025). Flight delay prediction: Evaluating machine learning algorithms for enhanced accuracy. PLOS ONE, 20(12), e0335141. doi:10.1371/journal.pone.0335141",
        "Supporting review: Wandelt, S., Chen, X., & Sun, X. (2025). Flight delay prediction: A dissecting review of recent studies using machine learning. IEEE TITS, 26(4), 4283-4297. doi:10.1109/TITS.2025.3528536",
    ]
    for reference in refs:
        story.append(p(reference, "small"))
    story.append(Spacer(1, 10))
    story.append(p("Source documents used to prepare this brief: PROJECT_PLAN.md; reports/literature_review_and_research_gaps.md; reports/eda_progress_report.md; reports/data_quality_report.md.", "small"))

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
