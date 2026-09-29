import pandas as pd

REQUIRED_COLUMNS = ["timestamp", "user_id", "action", "status", "data_type", "resource", "consent", "ip_address"]

class LogValidator:
    def validate(self, df: pd.DataFrame, required_columns=None) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input logs must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Input dataset is empty")
        required = REQUIRED_COLUMNS if required_columns is None else list(dict.fromkeys(required_columns))
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns for selected rules: {missing}")
        if "timestamp" in required and df["timestamp"].isna().any():
            raise ValueError("timestamp cannot contain null values")
        if "user_id" in required and df["user_id"].isna().any():
            raise ValueError("user_id cannot contain null values")
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            if "timestamp" in required and df["timestamp"].isna().any():
                raise ValueError("timestamp contains invalid date/time values")
