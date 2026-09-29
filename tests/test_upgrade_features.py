import pandas as pd
import pytest
from src.engine.registry import RuleRegistry
from src.engine.rule_engine import RuleEngine
from src.validation.validator import LogValidator


def test_no_violations():
    rules = [{"id":"N1", "name":"Flag blocked", "field":"status", "operator":"equals", "value":"BLOCKED", "severity":"HIGH"}]
    df = pd.DataFrame([{"status":"OK"}])
    assert RuleEngine(RuleRegistry(rules).rules).evaluate(df) == []


def test_overlapping_rules_both_reported():
    rules = [
        {"id":"A", "name":"Rule A", "field":"status", "operator":"equals", "value":"BAD", "severity":"HIGH"},
        {"id":"B", "name":"Rule B", "field":"status", "operator":"equals", "value":"BAD", "severity":"CRITICAL"},
    ]
    result = RuleEngine(RuleRegistry(rules).rules).evaluate(pd.DataFrame([{"status":"BAD"}]))
    assert {v.rule_id for v in result} == {"A", "B"}


def test_rejects_unsupported_operator():
    rules = [{"id":"X", "name":"Invalid", "field":"x", "operator":"run_code", "value":1, "severity":"LOW"}]
    with pytest.raises(ValueError, match="unsupported operator"):
        RuleRegistry(rules)


def test_validator_reports_missing_rule_fields():
    with pytest.raises(ValueError, match="Missing required columns"):
        LogValidator().validate(pd.DataFrame([{"status":"OK"}]), required_columns=["user_id"])
