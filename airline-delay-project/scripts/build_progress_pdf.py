from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/airline_pdf_deps")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
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
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"
OUTPUT = ROOT / "output" / "pdf" / "airline_delay_project_progress_2025.pdf"

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2F6F9F")
TEAL = colors.HexColor("#2B7A78")
PALE_BLUE = colors.HexColor("#EAF3F8")
PALE_TEAL = colors.HexColor("#E7F4F1")
GREY = colors.HexColor("#5B6770")
LIGHT_GREY = colors.HexColor("#E8ECEF")
ORANGE = colors.HexColor("#D97706")


def read_metric_values() -> dict[str, float]:
    with (TABLES / "overall_summary.csv").open(newline="", encoding="utf-8") as handle:
        return {row["metric"]: float(row["value"]) for row in csv.DictReader(handle)}


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LIGHT_GREY)
    canvas.line(doc.leftMargin, 0.54 * inch, letter[0] - doc.rightMargin, 0.54 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(doc.leftMargin, 0.35 * inch, "Airline Delay Project - 2025 progress update")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def metric_card(label: str, value: str, tint=PALE_BLUE) -> Table:
    table = Table([[Paragraph(value, styles["CardValue"])], [Paragraph(label, styles["CardLabel"])]], colWidths=[1.43 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), tint),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8CCD9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def section_title(text: str) -> Paragraph:
    return Paragraph(text, styles["SectionTitle"])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"<bullet>&bull;</bullet>{text}", styles["BulletItem"])


def mini_table(rows, widths):
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D1D8")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=NAVY, spaceAfter=5))
styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontSize=10.5, leading=14, textColor=GREY, spaceAfter=13))
styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], fontSize=9.2, leading=12.5, spaceAfter=4))
styles.add(ParagraphStyle(name="BulletItem", parent=styles["BodyText"], fontSize=8.7, leading=11, leftIndent=13, firstLineIndent=-8, spaceAfter=3))
styles.add(ParagraphStyle(name="CardValue", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=NAVY, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="CardLabel", parent=styles["Normal"], fontSize=7.5, leading=9, textColor=GREY, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=9, leading=12, textColor=NAVY, backColor=PALE_TEAL, borderColor=TEAL, borderWidth=0.5, borderPadding=7, spaceBefore=5, spaceAfter=7))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=7.5, leading=9.5, textColor=GREY))


def build() -> None:
    metrics = read_metric_values()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.62 * inch,
        rightMargin=0.62 * inch,
        topMargin=0.57 * inch,
        bottomMargin=0.72 * inch,
        title="Airline Delay Project - 2025 Progress Update",
        author="Airline Delay Project Team",
    )
    story = []

    # Page 1
    story += [
        Paragraph("Airline Delay Project", styles["TitleCustom"]),
        Paragraph("2025 implementation progress update | Data wrangling, initial cleaning, and first-pass EDA", styles["Subtitle"]),
        Paragraph("Scope", styles["SectionTitle"]),
        Paragraph(
            "The project uses all 12 monthly 2025 BTS Reporting Carrier On-Time Performance files and the supplied OurAirports metadata. The goal is to analyze operational delay patterns and later build a leakage-safe model that predicts severe arrival delays before departure.",
            styles["Body"],
        ),
        Paragraph("What has been completed", styles["SectionTitle"]),
    ]
    completion_rows = [
        [metric_card("BTS flight rows audited", f"{metrics['total_flights']:,.0f}"), metric_card("Monthly files validated", "12 / 12", PALE_TEAL), metric_card("Consistent source columns", "28"), metric_card("Airport-code match", "100%", PALE_TEAL)],
    ]
    completion = Table(completion_rows, colWidths=[1.43 * inch] * 4, hAlign="LEFT")
    completion.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))
    story += [completion, Spacer(1, 8)]
    for item in [
        "Raw BTS and airport data reorganized into a reproducible 2025-only project structure without modifying source contents.",
        "Master plan updated from 2023-2025 to one full 2025 calendar year, including a chronological within-year ML split.",
        "Chunked Python pipeline created for source manifesting, cleaning, validation, feature engineering, airport-reference standardization, and EDA.",
        "Reports, summary tables, figures, settings, column mapping, README instructions, and cleaning tests added.",
    ]:
        story.append(bullet(item))
    story += [
        Paragraph("Current project structure", styles["SectionTitle"]),
        Paragraph(
            "<font face='Courier'>airline-delay-project/<br/>"
            "  data/raw/bts/2025/ - 12 renamed monthly BTS files<br/>"
            "  data/raw/airports/ - airports.csv<br/>"
            "  config/ - settings and column mapping<br/>"
            "  src/ and scripts/ - reusable pipeline code<br/>"
            "  reports/ - quality report, cleaning log, EDA tables, figures</font>",
            styles["Body"],
        ),
        Paragraph("Current phase: first-pass cleaning and EDA are complete. The project has passed the requested 50% cleaning/EDA checkpoint.", styles["Callout"]),
    ]
    story.append(PageBreak())

    # Page 2
    story += [
        Paragraph("Cleaning, validation, and data quality", styles["TitleCustom"]),
        Paragraph("The pipeline reads the full year in chunks, protecting the raw data while keeping the analysis reproducible.", styles["Subtitle"]),
        Paragraph("Cleaning and transformation work completed", styles["SectionTitle"]),
    ]
    for item in [
        "Mapped BTS uppercase source columns to documented snake_case analysis names; parsed flight dates and numeric measures.",
        "Trimmed and standardized airline, airport, and cancellation codes. Created route, scheduled departure hour, departure-time band, weekend, season, delay category, and severe-delay features.",
        "Defined severe delay as ARR_DELAY greater than 60 minutes only for completed, non-diverted flights with a known arrival outcome.",
        "Flagged five impossible nonpositive scheduled-duration values and set them to null only in derived data; raw records remain untouched.",
        "Standardized the airport reference and documented a historical PBI to DJT alias found in the supplied airport metadata, producing full origin and destination code coverage.",
    ]:
        story.append(bullet(item))
    story += [Paragraph("Measured validation outcomes", styles["SectionTitle"])]
    story.append(
        mini_table(
            [
                ["Check", "Outcome"],
                ["Monthly source coverage", "12 of 12 files present; each file dates only to its expected 2025 month"],
                ["Schema and duplicate audit", "One consistent 28-column schema; 0 exact and 0 business-key duplicates"],
                ["Code and flag validation", "0 invalid origin/destination codes; 0 invalid cancellation or diversion flags"],
                ["Airport join", "352 distinct BTS codes matched for origins and destinations (100% flight-row match)"],
                ["Target eligibility", f"{metrics['target_eligible_flights']:,.0f} completed, non-diverted flights with known arrival delay"],
            ],
            [2.0 * inch, 4.75 * inch],
        )
    )
    story += [
        Paragraph("Important handling decisions", styles["SectionTitle"]),
        Paragraph(
            "Cancelled and diverted flights keep their operational records but do not receive a severe-arrival-delay target. Missing post-flight fields and extreme delays are retained for analysis rather than imputed or removed automatically. Reported delay-cause fields are descriptive only and are excluded from the future pre-departure ML feature set.",
            styles["Body"],
        ),
        Paragraph(
            "Six records are flagged for contextual follow-up: five contain impossible scheduled elapsed durations and one completed flight has no arrival-delay value. They do not block the current EDA; their details are preserved in the flagged-row table.",
            styles["Callout"],
        ),
        Paragraph("Still pending in cleaning: contextual review of extreme delay events, finalized retained-column schema, and persisted cleaned flight partitions.", styles["Small"]),
    ]
    story.append(PageBreak())

    # Page 3
    story += [
        Paragraph("Initial EDA outcomes and next steps", styles["TitleCustom"]),
        Paragraph("All values below were calculated from the 2025 files, not assumed in advance.", styles["Subtitle"]),
    ]
    eda_cards = Table(
        [[
            metric_card("Average arrival delay", f"{metrics['average_arrival_delay_minutes']:.1f} min"),
            metric_card("Median arrival delay", f"{metrics['median_arrival_delay_minutes']:.0f} min", PALE_TEAL),
            metric_card("Severe-delay rate", f"{metrics['severe_delay_rate'] * 100:.2f}%"),
            metric_card("Cancellation rate", f"{metrics['cancellation_rate'] * 100:.2f}%", PALE_TEAL),
        ]],
        colWidths=[1.43 * inch] * 4,
        hAlign="LEFT",
    )
    eda_cards.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))
    story += [eda_cards, Spacer(1, 8), Paragraph("Evidence-backed findings", styles["SectionTitle"])]
    for item in [
        "July had the highest monthly severe-delay rate: 11.89% across 612,811 eligible flights.",
        "Evening departures had the highest severe-delay rate: 12.34%, compared with the full-year rate of 8.04%.",
        "Among airlines with at least 10,000 flights, OH had the highest severe-delay rate at 12.12%.",
        "Among routes with at least 1,000 flights, ASE-DFW had the highest severe-delay rate at 19.15%.",
        "Late-aircraft delay accounted for 39.19% of reported delay-cause minutes, the largest category. This is descriptive only, not an ML predictor.",
    ]:
        story.append(bullet(item))
        story.append(Spacer(1, 1.5))
    image_row = Table(
        [[
            Image(str(FIGURES / "monthly_volume_and_severe_delay.png"), width=3.25 * inch, height=1.78 * inch),
            Image(str(FIGURES / "severe_delay_by_departure_band.png"), width=3.25 * inch, height=1.78 * inch),
        ]],
        colWidths=[3.35 * inch, 3.35 * inch],
    )
    image_row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [image_row, Paragraph("Next implementation sequence", styles["SectionTitle"])]
    story.append(
        Paragraph(
            "1. Review the flagged rows and extreme-delay context.  2. Persist standardized flight partitions and complete the airport enrichment.  3. Create viva-friendly audit, cleaning, and EDA notebooks.  4. Load the cleaned data into SQLite.  5. Freeze the chronological 2025 train/validation/test split, then compare a baseline with Logistic Regression and a Decision Tree.",
            styles["Body"],
        )
    )
    story.append(Paragraph("Limitation: one full year supports within-2025 analysis but cannot establish year-over-year trends or long-term generalization.", styles["Small"]))

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
