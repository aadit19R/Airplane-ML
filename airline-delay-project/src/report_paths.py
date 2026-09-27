"""Locations of generated CSV tables, grouped by project milestone."""

from pathlib import Path


TABLE_GROUPS = {
    "02_ingestion": ("source_manifest",),
    "03_cleaning": (
        "column_profile", "numeric_ranges", "data_quality_issues",
        "flagged_row_samples", "conversion_audit", "missingness_by_status",
        "extreme_delay_review", "row_reconciliation",
    ),
    "04_transformation": (
        "airport_join_coverage", "unmatched_airport_codes",
        "final_row_reconciliation",
    ),
    "06_eda": (
        "overall_summary", "monthly_performance", "airline_performance",
        "origin_airport_performance", "destination_airport_performance",
        "route_performance", "day_of_week_performance",
        "departure_hour_performance", "departure_time_band_performance",
        "weekend_performance", "season_performance",
        "cancellation_code_counts", "delay_cause_summary",
        "airport_month_cancellations", "route_month_performance",
        "delay_distribution", "monthly_delay_distribution",
        "airline_delay_distribution", "busy_route_delay_distribution",
        "busy_origin_delay_distribution", "eda_plot_sample",
    ),
    "07_ml_preparation": (
        "data_dictionary", "ml_feature_missingness", "ml_split_summary",
    ),
}

TABLE_FOLDERS = {
    name: folder
    for folder, names in TABLE_GROUPS.items()
    for name in names
}


def table_path(tables_root: Path, name: str) -> Path:
    """Return the milestone path for a generated table name or CSV filename."""
    stem = Path(name).stem
    try:
        folder = TABLE_FOLDERS[stem]
    except KeyError as exc:
        raise ValueError(f"Unknown report table: {name}") from exc
    return tables_root / folder / f"{stem}.csv"
