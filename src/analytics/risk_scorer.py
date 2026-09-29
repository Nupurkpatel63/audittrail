
from dataclasses import asdict, is_dataclass

import pandas as pd


class RiskScorer:
    """Aggregate compliance risk scores by user or entity."""

    DEFAULT_WEIGHTS = {
        "Critical": 10,
        "High": 7,
        "Medium": 4,
        "Low": 1,
        "Unknown": 1,
    }

    def __init__(self, violations, severity_weights=None):
        self.weights = severity_weights or self.DEFAULT_WEIGHTS.copy()
        self.df = self._to_dataframe(violations)

    @staticmethod
    def _to_dataframe(violations):
        records = []

        for item in violations:
            if isinstance(item, dict):
                records.append(item)
            elif is_dataclass(item):
                records.append(asdict(item))
            else:
                raise TypeError(
                    "Violation must be a dictionary or dataclass."
                )

        columns = ["user_id", "severity", "rule_id", "resource"]

        if not records:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(records)

        for column in columns:
            if column not in df.columns:
                df[column] = "Unknown"

        for column in columns:
            df[column] = (
                df[column]
                .fillna("Unknown")
                .astype(str)
                .replace("", "Unknown")
            )

        df["severity"] = df["severity"].str.title()

        return df

    def score_entities(self, group_by="user_id"):
        """
        Aggregate risk by user_id or resource.

        Returns one row per entity, sorted by risk score.
        """
        if group_by not in ("user_id", "resource"):
            raise ValueError(
                "group_by must be 'user_id' or 'resource'."
            )

        if self.df.empty:
            return pd.DataFrame(
                columns=[
                    group_by,
                    "total_violations",
                    "critical_count",
                    "high_count",
                    "medium_count",
                    "low_count",
                    "risk_score",
                    "risk_level",
                ]
            )

        df = self.df.copy()

        # Missing identifiers should not be grouped together
        # as if they represented a known user or resource.
        df[group_by] = df[group_by].replace(
            "Unknown", "Unidentified"
        )

        df["risk_points"] = (
            df["severity"].map(self.weights).fillna(
                self.weights.get("Unknown", 1)
            )
        )

        df["critical_count"] = (
            df["severity"] == "Critical"
        ).astype(int)

        df["high_count"] = (
            df["severity"] == "High"
        ).astype(int)

        df["medium_count"] = (
            df["severity"] == "Medium"
        ).astype(int)

        df["low_count"] = (
            df["severity"] == "Low"
        ).astype(int)

        result = (
            df.groupby(group_by)
            .agg(
                total_violations=("severity", "size"),
                critical_count=("critical_count", "sum"),
                high_count=("high_count", "sum"),
                medium_count=("medium_count", "sum"),
                low_count=("low_count", "sum"),
                risk_score=("risk_points", "sum"),
            )
            .reset_index()
        )

        result["risk_score"] = result["risk_score"].astype(int)

        result["risk_level"] = result["risk_score"].apply(
            self._risk_level
        )

        return result.sort_values(
            ["risk_score", "total_violations"],
            ascending=False,
        ).reset_index(drop=True)

    @staticmethod
    def _risk_level(score):
        if score >= 30:
            return "Critical"
        elif score >= 20:
            return "High"
        elif score >= 10:
            return "Medium"
        return "Low"

    def get_user_risk(self):
        """Return risk scores grouped by user."""
        return self.score_entities("user_id")

    def get_resource_risk(self):
        """Return risk scores grouped by resource/entity."""
        return self.score_entities("resource")