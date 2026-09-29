from pathlib import Path
import yaml
from src.engine.operators import OPERATORS


class RuleRegistry:
    """Load and validate config-driven rules from a path or in-memory data."""
    def __init__(self, rule_source):
        self.rule_source = rule_source
        self.rules = self._load_rules(rule_source)
        self._validate_rules()

    @staticmethod
    def _load_rules(source):
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(f"Rule file not found: {path}")
            with path.open("r", encoding="utf-8-sig") as stream:
                config = yaml.safe_load(stream)
        else:
            config = source
        if isinstance(config, dict):
            rules = config.get("rules")
        elif isinstance(config, list):
            rules = config
        else:
            rules = None
        if not isinstance(rules, list) or not rules:
            raise ValueError("Rules must be a non-empty list or an object containing 'rules'.")
        return rules

    def _validate_rules(self):
        ids = set()
        allowed_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        for rule in self.rules:
            if not isinstance(rule, dict):
                raise ValueError("Each rule must be a YAML/JSON object.")
            rid = rule.get("id")
            if not rid or rid in ids:
                raise ValueError(f"Missing or duplicate rule id: {rid!r}")
            ids.add(rid)
            if not rule.get("name"):
                raise ValueError(f"Rule {rid} must have a name")
            if str(rule.get("severity", "")).upper() not in allowed_severities:
                raise ValueError(f"Rule {rid} has invalid severity")
            kind = rule.get("type", "comparison" if rule.get("field") and rule.get("operator") else "condition")
            if kind in {"comparison", "threshold"}:
                if not rule.get("field") or not rule.get("operator"):
                    raise ValueError(f"Rule {rid} needs field and operator")
                if "value" not in rule and "compare_with" not in rule:
                    raise ValueError(f"Rule {rid} needs value or compare_with")
                self._check_operator(rule["operator"], rid)
            elif kind == "condition":
                conditions = rule.get("conditions")
                if not isinstance(conditions, list) or not conditions:
                    raise ValueError(f"Rule {rid} needs a non-empty conditions list")
                for condition in conditions:
                    if not isinstance(condition, dict) or not condition.get("field") or not condition.get("operator"):
                        raise ValueError(f"Rule {rid} contains an invalid condition")
                    self._check_operator(condition["operator"], rid)
            else:
                raise ValueError(f"Rule {rid} has unsupported type: {kind}")

    @staticmethod
    def _check_operator(operator, rid):
        if operator not in OPERATORS:
            raise ValueError(f"Rule {rid} uses unsupported operator: {operator}")
