"""Run the source audit, final cleaning, feature engineering, and EDA tables."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.initial_analysis import run as run_audit
from src.etl import run

if __name__ == "__main__":
    run_audit()
    run()
