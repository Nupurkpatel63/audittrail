from typing import Any
from datetime import datetime

from src.engine.operators import OPERATORS
from src.models.violation import Violation


class RuleEngine:
    """
    Generic configuration-driven compliance rule engine.
    """

    def __init__(self, rules):
        self.rules = rules or []

    def evaluate(self, df):
        violations = []

        # Avoid constructing a pandas Series for every row. Plain dictionaries
        # retain the field access behavior while reducing large-log overhead.
        for record in df.to_dict(orient="records"):

            for rule in self.rules:

                try:

                    if self._evaluate_rule(
                        record,
                        rule
                    ):

                        violation = self._create_violation(
                            record,
                            rule
                        )

                        violations.append(
                            violation
                        )

                except Exception as exc:

                    print(
                        f"Rule evaluation failed "
                        f"for {rule.get('id')}: {exc}"
                    )

        return violations

    def _evaluate_rule(
        self,
        record,
        rule: dict
    ) -> bool:

        rule_type = rule.get("type")

        if rule_type == "condition":
            return self._evaluate_conditions(
                record,
                rule
            )

        if rule_type in (
            "comparison",
            "threshold"
        ):
            return self._evaluate_comparison(
                record,
                rule
            )

        # Support rules that directly contain
        # field/operator/value.
        if (
            rule.get("field")
            and rule.get("operator")
        ):
            return self._evaluate_comparison(
                record,
                rule
            )

        return self._evaluate_conditions(
            record,
            rule
        )

    def _evaluate_conditions(
        self,
        record,
        rule: dict
    ) -> bool:

        conditions = rule.get(
            "conditions",
            []
        )

        if not conditions:
            return False

        for condition in conditions:

            if not self._evaluate_condition(
                record,
                condition,
                rule
            ):
                return False

        return True

    def _evaluate_condition(
        self,
        record,
        condition: dict,
        rule: dict
    ) -> bool:

        field = condition.get("field")
        operator_name = condition.get("operator")

        if not field or not operator_name:
            return False

        operator = OPERATORS.get(
            operator_name
        )

        if operator is None:
            raise ValueError(
                f"Unsupported operator: "
                f"{operator_name}"
            )

        actual_value = self._get_field_value(
            record,
            field
        )

        expected_value = self._get_expected_value(
            record,
            condition
        )

        parameters = {}

        parameters.update(
            rule.get("parameters", {})
        )

        parameters.update(
            condition.get("parameters", {})
        )

        return self._execute_operator(
            operator_name,
            operator,
            actual_value,
            expected_value,
            parameters,
            record,
            condition
        )

    def _evaluate_comparison(
        self,
        record,
        rule: dict
    ) -> bool:

        conditions = rule.get(
            "conditions",
            []
        )

        if conditions:

            if not self._evaluate_conditions(
                record,
                rule
            ):
                return False

        field = rule.get("field")
        operator_name = rule.get("operator")

        if not field or not operator_name:
            return False

        operator = OPERATORS.get(
            operator_name
        )

        if operator is None:
            raise ValueError(
                f"Unsupported operator: "
                f"{operator_name}"
            )

        actual_value = self._get_field_value(
            record,
            field
        )

        compare_with = rule.get(
            "compare_with"
        )

        if compare_with:

            expected_value = self._get_field_value(
                record,
                compare_with
            )

        else:

            expected_value = rule.get(
                "value"
            )

        parameters = rule.get(
            "parameters",
            {}
        )

        return self._execute_operator(
            operator_name,
            operator,
            actual_value,
            expected_value,
            parameters,
            record,
            rule
        )

    def _execute_operator(
        self,
        operator_name: str,
        operator,
        actual_value: Any,
        expected_value: Any,
        parameters: dict,
        record,
        configuration: dict
    ) -> bool:

        if operator_name == "after_hours":

            return operator(
                actual_value,
                parameters
            )

        if operator_name == "role_not_allowed":

            resource = self._get_field_value(
                record,
                configuration.get(
                    "compare_with",
                    "resource"
                )
            )

            return operator(
                actual_value,
                resource,
                parameters
            )

        return operator(
            actual_value,
            expected_value
        )

    def _get_expected_value(
        self,
        record,
        condition: dict
    ):

        if "compare_with" in condition:

            return self._get_field_value(
                record,
                condition["compare_with"]
            )

        if "values" in condition:

            return condition["values"]

        return condition.get("value")

    @staticmethod
    def _get_field_value(
        record,
        field: str
    ):

        return record.get(field)

    @staticmethod
    def _create_violation(
        record,
        rule: dict
    ) -> Violation:

        conditions = rule.get(
            "conditions",
            []
        )

        field = rule.get(
            "field",
            ""
        )

        operator = rule.get(
            "operator",
            ""
        )

        expected_value = rule.get(
            "value"
        )

        # -----------------------------------------------------
        # Get evaluation information from first condition
        # -----------------------------------------------------

        if conditions and not field:

            first_condition = conditions[0]

            field = first_condition.get(
                "field",
                ""
            )

            operator = first_condition.get(
                "operator",
                ""
            )

            if "compare_with" in first_condition:

                compare_field = first_condition.get(
                    "compare_with"
                )

                expected_value = record.get(
                    compare_field
                )

            elif "values" in first_condition:

                expected_value = first_condition.get(
                    "values"
                )

            else:

                expected_value = first_condition.get(
                    "value"
                )

        # -----------------------------------------------------
        # Actual value
        # -----------------------------------------------------

        actual_value = None

        if field:

            actual_value = record.get(
                field
            )

        # -----------------------------------------------------
        # Create violation
        # -----------------------------------------------------

        return Violation(

            rule_id=rule.get(
                "id",
                "UNKNOWN"
            ),

            rule_name=rule.get(
                "name",
                "Unnamed Rule"
            ),

            severity=str(
                rule.get(
                    "severity",
                    "MEDIUM"
                )
            ).upper(),

            description=rule.get(
                "description",
                ""
            ),

            record_id=str(
                record.get("record_id")
                or record.get("event_id")
                or ""
            ),

            timestamp=record.get(
                "timestamp"
            ),

            source_row=record.get(
                "source_row",
                ""
            ),

            user_id=str(
                record.get(
                    "user_id",
                    ""
                )
            ),

            department=str(
                record.get(
                    "department",
                    ""
                )
            ),

            role=str(
                record.get(
                    "role",
                    ""
                )
            ),

            action=str(
                record.get(
                    "action",
                    ""
                )
            ),

            status=str(
                record.get(
                    "status",
                    ""
                )
            ),

            data_type=str(
                record.get(
                    "data_type",
                    ""
                )
            ),

            resource=str(
                record.get(
                    "resource",
                    ""
                )
            ),

            transaction_amount=record.get(
                "transaction_amount"
            ),

            approved_amount=record.get(
                "approved_amount"
            ),

            approval_limit=record.get(
                "approval_limit"
            ),

            approver_id=str(
                record.get(
                    "approver_id",
                    ""
                )
            ),

            sod_conflict=record.get("sod_conflict", ""),

            consent=record.get("consent", ""),

            justification=str(
                record.get(
                    "justification",
                    ""
                )
            ),

            data_access_count_24h=record.get(
                "data_access_count_24h"
            ),

            ip_address=str(
                record.get(
                    "ip_address",
                    ""
                )
            ),

            field=str(
                field
            ),

            operator=str(
                operator
            ),

            actual_value=actual_value,

            expected_value=expected_value,

            detected_at=datetime.now()
        )
