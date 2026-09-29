from src.analytics.rule_explainer import RuleExplainer


def test_explain_rule():
    rules = [
        {
            "id": "R003",
            "name": "Transaction Approval Limit",
            "severity": "High",
            "category": "Financial Controls",
            "field": "transaction_amount",
            "operator": "greater_than",
            "value": 5000,
        }
    ]

    explainer = RuleExplainer(rules)
    explanation = explainer.explain_rule(rules[0])

    assert "Transaction Approval Limit" in explanation
    assert "transaction_amount" in explanation
    assert "greater than" in explanation


def test_explain_violation():
    rules = [
        {
            "id": "R003",
            "name": "Transaction Approval Limit",
            "severity": "High",
            "field": "transaction_amount",
            "operator": "greater_than",
            "value": 5000,
        }
    ]

    violation = {
        "rule_id": "R003",
        "user_id": "U001",
        "resource": "FinanceDB",
        "timestamp": "2026-09-21T10:00:00",
        "description": "Transaction exceeded approval limit",
    }

    explanation = RuleExplainer(rules).explain_violation(
        violation
    )

    assert "U001" in explanation
    assert "R003" in explanation
    assert "Transaction exceeded approval limit" in explanation


def test_unknown_rule():
    explanation = RuleExplainer([]).explain_violation(
        {"rule_id": "R999"}
    )

    assert "configuration was not found" in explanation