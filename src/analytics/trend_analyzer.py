from dataclasses import asdict, is_dataclass

import pandas as pd


class TrendAnalyzer:
    """Analyze compliance violation trends over time."""

    FREQUENCIES = {
    "daily": "D",
    "weekly": "W-SUN",
    "monthly": "M",
    }

    DATE_RANGE_FREQUENCIES = {
    "daily": "D",
    "weekly": "W-SUN",
    "monthly": "MS",
    }

    def __init__(self, violations):
        self.df = self._to_dataframe(violations)

    @staticmethod
    def _to_dataframe(violations):
        """Convert Violation objects or dictionaries into a DataFrame."""
        records = []

        for item in violations:
            if isinstance(item, dict):
                records.append(item)
            elif is_dataclass(item):
                records.append(asdict(item))
            else:
                raise TypeError(
                    "Each violation must be a dictionary "
                    "or dataclass object."
                )

        columns = [
            "timestamp",
            "severity",
            "rule_id",
            "user_id",
        ]

        if not records:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(records)

        # Add optional columns if absent
        for column in columns:
            if column not in df.columns:
                df[column] = "Unknown"

        df["timestamp"] = pd.to_datetime(
            df["timestamp"], errors="coerce", utc=True
        )

        df = df.dropna(subset=["timestamp"]).copy()

        # Normalize severity and rule identifiers
        df["severity"] = (
            df["severity"].fillna("Unknown").astype(str).str.title()
        )
        df["rule_id"] = (
            df["rule_id"].fillna("Unknown").astype(str)
        )

        return df

    def _period_data(self, frequency="daily"):
        if frequency not in self.FREQUENCIES:
            raise ValueError(
                "frequency must be daily, weekly, or monthly"
            )

        df = self.df.copy()

        if df.empty:
            return pd.DataFrame(
                columns=["period", "violations"]
            )

        freq = self.FREQUENCIES[frequency]

        df["period"] = (
            df["timestamp"].dt.tz_convert(None)
            .dt.to_period(freq)
            .dt.start_time
        )

        trend = (
            df.groupby("period")
            .size()
            .reset_index(name="violations")
            .sort_values("period")
        )

        return trend

    def get_overall_trend(self, frequency="daily"):
        """Return counts and direction between the last two periods."""
        trend = self._period_data(frequency)

        if trend.empty:
            return {
                "direction": "No data",
                "change": 0,
                "percentage_change": None,
                "data": [],
            }

        # Include zero-violation periods between observed dates
        trend = trend.set_index("period")

        freq = self.FREQUENCIES[frequency]
        full_index = pd.date_range(
            start=trend.index.min(),
            end=trend.index.max(),
            freq = self.DATE_RANGE_FREQUENCIES[frequency],
        )

        trend = trend.reindex(full_index, fill_value=0)
        trend.index.name = "period"
        trend = trend.reset_index()

        if len(trend) < 2:
            direction = "Insufficient data"
            change = 0
            percentage_change = None
        else:
            previous = int(trend.iloc[-2]["violations"])
            current = int(trend.iloc[-1]["violations"])
            change = current - previous

            if change > 0:
                direction = "Increasing"
            elif change < 0:
                direction = "Decreasing"
            else:
                direction = "Stable"

            percentage_change = (
                round((change / previous) * 100, 2)
                if previous != 0
                else None
            )

        trend["period"] = trend["period"].astype(str)

        return {
            "direction": direction,
            "change": change,
            "percentage_change": percentage_change,
            "data": trend.to_dict(orient="records"),
        }

    def get_severity_trend(self, frequency="daily"):
        """Return period-by-period counts grouped by severity."""
        if self.df.empty:
            return pd.DataFrame(
                columns=["period", "severity", "violations"]
            )

        df = self.df.copy()
        freq = self.FREQUENCIES[frequency]

        df["period"] = (
            df["timestamp"].dt.tz_convert(None)
            .dt.to_period(freq)
            .dt.start_time
        )

        return (
            df.groupby(["period", "severity"])
            .size()
            .reset_index(name="violations")
            .sort_values(["period", "severity"])
        )

    def get_rule_trend(self, frequency="daily"):
        """Return period-by-period counts grouped by rule."""
        if self.df.empty:
            return pd.DataFrame(
                columns=["period", "rule_id", "violations"]
            )

        df = self.df.copy()
        freq = self.FREQUENCIES[frequency]

        df["period"] = (
            df["timestamp"].dt.tz_convert(None)
            .dt.to_period(freq)
            .dt.start_time
        )

        return (
            df.groupby(["period", "rule_id"])
            .size()
            .reset_index(name="violations")
            .sort_values(["period", "rule_id"])
        )

    def get_summary(self, frequency="daily"):
        """Return a combined trend-analysis result."""
        return {
            "overall": self.get_overall_trend(frequency),
            "severity": self.get_severity_trend(frequency),
            "rules": self.get_rule_trend(frequency),
        }