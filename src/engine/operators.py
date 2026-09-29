from datetime import datetime, time
from typing import Any


def _is_empty(value: Any) -> bool:
    """Determine whether a value is empty or null."""

    if value is None:
        return True

    try:
        # Handles NaN
        if value != value:
            return True
    except Exception:
        pass

    return str(value).strip() == ""


def equals(actual: Any, expected: Any) -> bool:
    """Check equality with basic type normalization."""

    if isinstance(expected, bool):
        if isinstance(actual, str):
            actual = actual.strip().lower() == "true"

    return actual == expected


def not_equals(actual: Any, expected: Any) -> bool:
    return not equals(actual, expected)


def contains(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return False

    return str(expected).lower() in str(actual).lower()


def starts_with(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return False

    return str(actual).lower().startswith(
        str(expected).lower()
    )


def ends_with(actual: Any, expected: Any) -> bool:
    if actual is None or expected is None:
        return False

    return str(actual).lower().endswith(
        str(expected).lower()
    )


def in_operator(actual: Any, values: Any) -> bool:
    if values is None:
        return False

    if not isinstance(values, (list, tuple, set)):
        values = [values]

    return any(
        equals(actual, expected)
        for expected in values
    )


def not_in(actual: Any, values: Any) -> bool:
    return not in_operator(actual, values)


def greater_than(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) > float(expected)
    except (TypeError, ValueError):
        return False


def greater_than_or_equal(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) >= float(expected)
    except (TypeError, ValueError):
        return False


def less_than(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) < float(expected)
    except (TypeError, ValueError):
        return False


def less_than_or_equal(actual: Any, expected: Any) -> bool:
    try:
        return float(actual) <= float(expected)
    except (TypeError, ValueError):
        return False


def empty(actual: Any, expected: Any = None) -> bool:
    return _is_empty(actual)


def not_empty(actual: Any, expected: Any = None) -> bool:
    return not _is_empty(actual)


def after_hours(
    actual: Any,
    parameters: dict | None = None
) -> bool:
    """
    Return True when timestamp is outside configured
    business hours.
    """

    if actual is None:
        return False

    parameters = parameters or {}

    start_value = parameters.get("start", "06:00")
    end_value = parameters.get("end", "21:59")

    try:

        if isinstance(actual, datetime):
            current_time = actual.time()

        else:
            timestamp = datetime.fromisoformat(str(actual))
            current_time = timestamp.time()

        start_time = time.fromisoformat(start_value)
        end_time = time.fromisoformat(end_value)

        return not (
            start_time <= current_time <= end_time
        )

    except (ValueError, TypeError):

        return False


def role_not_allowed(
    role: Any,
    resource: Any,
    parameters: dict | None = None
) -> bool:
    """
    Check whether a role is not authorized for a resource.
    """

    parameters = parameters or {}

    allowed_resources = parameters.get(
        "allowed_resources",
        {}
    )

    if role is None or resource is None:
        return True

    role = str(role).strip()
    resource = str(resource).strip()

    allowed = allowed_resources.get(role, [])

    return resource not in allowed


# ============================================================
# OPERATOR REGISTRY
# ============================================================

OPERATORS = {
    "equals": equals,
    "not_equals": not_equals,

    "contains": contains,
    "starts_with": starts_with,
    "ends_with": ends_with,

    "in": in_operator,
    "not_in": not_in,

    "greater_than": greater_than,
    "greater_than_or_equal": greater_than_or_equal,
    "less_than": less_than,
    "less_than_or_equal": less_than_or_equal,

    "empty": empty,
    "not_empty": not_empty,

    "after_hours": after_hours,

    "role_not_allowed": role_not_allowed,
}