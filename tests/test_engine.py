from src.engine.rule_engine import RuleEngine
import pandas as pd


def test_unauthorized_access():

    rules = [
        {
            "id": "R001",
            "name": "Unauthorized Access",
            "field": "status",
            "operator": "equals",
            "value": "UNAUTHORIZED",
            "severity": "HIGH"
        }
    ]

    df = pd.DataFrame([
        {
            "timestamp": "2026-09-18 10:00:00",
            "user_id": "U001",
            "action": "DATA_ACCESS",
            "status": "UNAUTHORIZED",
            "data_type": "NORMAL",
            "resource": "Customer",
            "consent": True,
            "ip_address": "127.0.0.1"
        }
    ])

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    engine = RuleEngine(rules)

    violations = engine.evaluate(df)

    assert len(violations) == 1

    violation = violations[0]

    assert violation.rule_id == "R001"
    assert violation.rule_name == "Unauthorized Access"
    assert violation.severity == "HIGH"

    assert violation.field == "status"
    assert violation.operator == "equals"

    assert violation.actual_value == "UNAUTHORIZED"
    assert violation.expected_value == "UNAUTHORIZED"

    assert violation.user_id == "U001"
    assert violation.action == "DATA_ACCESS"
    assert violation.resource == "Customer"

    assert violation.consent is True
    assert violation.ip_address == "127.0.0.1"

    rules = [
        {
            "id": "R001",
            "name": "Unauthorized Access",
            "field": "status",
            "operator": "equals",
            "value": "UNAUTHORIZED",
            "severity": "HIGH"
        }
    ]

    df = pd.DataFrame([
        {
            "timestamp": "2026-09-18 10:00:00",
            "user_id": "U001",
            "action": "DATA_ACCESS",
            "status": "UNAUTHORIZED",
            "data_type": "NORMAL",
            "resource": "Customer",
            "consent": True,
            "ip_address": "127.0.0.1"
        }
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    engine = RuleEngine(rules)

    violations = engine.evaluate(df)

    assert len(violations) == 1

    violation = violations[0]

    assert violation["rule_id"] == "R001"
    assert violation["rule_name"] == "Unauthorized Access"
    assert violation["severity"] == "HIGH"
    assert violation["field"] == "status"
    assert violation["actual_value"] == "UNAUTHORIZED"
