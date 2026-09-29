from pathlib import Path
import pandas as pd


# Project root:
# compliance_auditor/
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_csv(file_path):
    """
    Load a CSV log file using a project-root-relative
    path or an absolute path.
    """

    path = Path(file_path)

    # Resolve relative paths from project root
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    # Verify file exists
    if not path.is_file():
        raise FileNotFoundError(
            f"Log file not found: {path}\n"
            f"Project root: {PROJECT_ROOT}\n"
            f"Please verify the CSV file location."
        )

    # Load CSV
    df = pd.read_csv(path)

    print(f"Loaded {len(df)} records from {path}")

    return df