
class RuleExplainer:
    """Generate readable explanations from configured compliance rules."""

    OPERATOR_TEXT = {
        "equals": "is equal to",
        "equal": "is equal to",
        "==": "is equal to",
        "not_equals": "is not equal to",
        "!=": "is not equal to",
        "greater_than": "is greater than",
        ">": "is greater than",
        "greater_than_or_equal": "is greater than or equal to",
        ">=": "is greater than or equal to",
        "less_than": "is less than",
        "<": "is less than",
        "less_than_or_equal": "is less than or equal to",
        "<=": "is less than or equal to",
        "in": "is one of",
        "not_in": "is not one of",
        "contains": "contains",
        "not_empty": "is not empty",
        "is_empty": "is empty",
        "after_hours": "falls outside the permitted time window",
        "role_not_allowed": "is not authorized for this resource",
    }

    def __init__(self, rules):
        self.rules = rules or []

    @staticmethod
    def _format_value(value):
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "not configured"
        return str(value)

    def _condition_text(self, condition):
        field = condition.get("field", "the configured field")
        operator = str(condition.get("operator", "")).lower()
        value = condition.get("value")

        operator_text = self.OPERATOR_TEXT.get(
            operator, f"matches operator '{operator or 'unspecified'}'"
        )

        if operator in ("after_hours",):
            start = condition.get("start", condition.get("start_time"))
            end = condition.get("end", condition.get("end_time"))

            if start is not None and end is not None:
                return (
                    f"{field} {operator_text} "
                    f"({start}–{end})"
                )

        if operator in ("not_empty", "is_empty"):
            return f"{field} {operator_text}"

        if value is not None:
            return (
                f"{field} {operator_text} "
                f"'{self._format_value(value)}'"
            )

        compare_with = condition.get("compare_with")
        if compare_with:
            return f"{field} {operator_text} field '{compare_with}'"

        return f"{field} {operator_text}"

    def explain_rule(self, rule):
        """Create a plain-language explanation for one rule."""
        rule_id = rule.get("id", rule.get("rule_id", "Unknown rule"))
        name = rule.get("name", rule.get("rule_name", rule_id))
        severity = rule.get("severity", "Unspecified")
        category = rule.get("category", "General compliance")

        conditions = rule.get("conditions", [])

        # Also support rules that use a single field/operator/value.
        if not conditions and rule.get("field"):
            conditions = [{
                "field": rule.get("field"),
                "operator": rule.get("operator", ""),
                "value": rule.get("value"),
                "compare_with": rule.get("compare_with"),
            }]

        condition_texts = [
            self._condition_text(condition)
            for condition in conditions
        ]

        if condition_texts:
            condition_summary = " AND ".join(condition_texts)
        else:
            condition_summary = (
                "the configured rule conditions are met"
            )

        description = rule.get("description")

        explanation = (
            f"{name} ({rule_id}) is a {severity}-severity "
            f"rule in the {category} category. "
        )

        if description:
            explanation += f"{description.strip()} "

        explanation += (
            f"It flags a record when {condition_summary}."
        )

        return explanation

    def explain_all(self):
        """Return explanations for all configured rules."""
        return [
            {
                "rule_id": rule.get(
                    "id", rule.get("rule_id", "Unknown")
                ),
                "rule_name": rule.get(
                    "name", rule.get("rule_name", "Unnamed rule")
                ),
                "severity": rule.get("severity", "Unspecified"),
                "explanation": self.explain_rule(rule),
            }
            for rule in self.rules
        ]

    def explain_violation(self, violation):
        """Explain a detected violation using its matching rule."""
        if hasattr(violation, "to_dict"):
            violation = violation.to_dict()

        rule_id = str(
            violation.get("rule_id", "Unknown")
        )

        matching_rule = next(
            (
                rule for rule in self.rules
                if str(rule.get(
                    "id", rule.get("rule_id", "")
                )) == rule_id
            ),
            None,
        )

        if matching_rule is None:
            return (
                f"Violation triggered by rule {rule_id}. "
                "The matching rule configuration was not found."
            )

        rule_explanation = self.explain_rule(matching_rule)

        user = violation.get("user_id", "Unknown user")
        resource = violation.get("resource", "Unknown resource")
        timestamp = violation.get("timestamp", "Unknown time")
        description = violation.get("description")

        message = (
            f"{rule_explanation} "
            f"Flagged event: user '{user}', resource "
            f"'{resource}', timestamp '{timestamp}'."
        )

        if description:
            message += f" Finding details: {description}"

        return message