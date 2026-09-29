from src.analytics.risk_scorer import RiskScorer


def test_user_risk_score():
    violations = [
        {
            "user_id": "U001",
            "severity": "High",
            "resource": "CustomerDB",
        },
        {
            "user_id": "U001",
            "severity": "High",
            "resource": "CustomerDB",
        },
        {
            "user_id": "U001",
            "severity": "Critical",
            "resource": "CustomerDB",
        },
    ]

    result = RiskScorer(violations).get_user_risk()

    user = result.iloc[0]

    assert user["user_id"] == "U001"
    assert user["risk_score"] == 24
    assert user["risk_level"] == "High"
    assert user["total_violations"] == 3


def test_resource_risk():
    violations = [
        {
            "user_id": "U001",
            "severity": "Critical",
            "resource": "CustomerDB",
        },
        {
            "user_id": "U002",
            "severity": "High",
            "resource": "CustomerDB",
        },
    ]

    result = RiskScorer(violations).get_resource_risk()

    assert result.iloc[0]["resource"] == "CustomerDB"
    assert result.iloc[0]["risk_score"] == 17


def test_empty_violations():
    result = RiskScorer([]).get_user_risk()

    assert result.empty