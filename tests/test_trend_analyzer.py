
from src.analytics.trend_analyzer import TrendAnalyzer


def test_overall_trend_increasing():
    violations = [
        {
            "timestamp": "2026-09-01T10:00:00Z",
            "severity": "High",
            "rule_id": "R001",
            "user_id": "U001",
        },
        {
            "timestamp": "2026-09-01T11:00:00Z",
            "severity": "High",
            "rule_id": "R001",
            "user_id": "U001",
        },
        {
            "timestamp": "2026-09-02T10:00:00Z",
            "severity": "Critical",
            "rule_id": "R003",
            "user_id": "U002",
        },
        {
            "timestamp": "2026-09-02T11:00:00Z",
            "severity": "Medium",
            "rule_id": "R005",
            "user_id": "U002",
        },
        {
            "timestamp": "2026-09-02T12:00:00Z",
            "severity": "Low",
            "rule_id": "R006",
            "user_id": "U003",
        },
    ]

    analyzer = TrendAnalyzer(violations)
    result = analyzer.get_overall_trend("daily")

    assert result["direction"] == "Increasing"
    assert result["change"] == 1
    assert result["percentage_change"] == 50.0


def test_empty_violations():
    analyzer = TrendAnalyzer([])
    result = analyzer.get_overall_trend()

    assert result["direction"] == "No data"
    assert result["data"] == []


def test_rule_trend():
    violations = [
        {
            "timestamp": "2026-09-01T10:00:00Z",
            "severity": "High",
            "rule_id": "R001",
            "user_id": "U001",
        },
        {
            "timestamp": "2026-09-01T11:00:00Z",
            "severity": "High",
            "rule_id": "R001",
            "user_id": "U002",
        },
    ]

    analyzer = TrendAnalyzer(violations)
    result = analyzer.get_rule_trend("daily")

    assert len(result) == 1
    assert result.iloc[0]["rule_id"] == "R001"
    assert result.iloc[0]["violations"] == 2