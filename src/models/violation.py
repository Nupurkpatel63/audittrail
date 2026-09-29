from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Violation:

    # Rule information
    rule_id: str
    rule_name: str
    severity: str

    description: str = ""

    # Record information
    record_id: str = ""
    timestamp: Optional[datetime] = None
    source_row: Any = ""

    # User information
    user_id: str = ""
    department: str = ""
    role: str = ""

    # Activity information
    action: str = ""
    status: str = ""
    data_type: str = ""
    resource: str = ""

    # Transaction / approval
    transaction_amount: Any = None
    approved_amount: Any = None
    approval_limit: Any = None

    approver_id: str = ""
    sod_conflict: str = ""

    # Compliance
    consent: str = ""
    justification: str = ""

    data_access_count_24h: Any = None

    # Network
    ip_address: str = ""

    # Rule evaluation evidence
    field: str = ""
    operator: str = ""
    actual_value: Any = None
    expected_value: Any = None

    # Audit
    detected_at: Optional[datetime] = None

    def __getitem__(self, key):
        """Allow dict-style access for downstream consumers/tests."""
        return getattr(self, key)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity,
            "description": self.description,

            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "source_row": self.source_row,

            "user_id": self.user_id,
            "department": self.department,
            "role": self.role,

            "action": self.action,
            "status": self.status,
            "data_type": self.data_type,
            "resource": self.resource,

            "transaction_amount": self.transaction_amount,
            "approved_amount": self.approved_amount,
            "approval_limit": self.approval_limit,

            "approver_id": self.approver_id,
            "sod_conflict": self.sod_conflict,

            "consent": self.consent,
            "justification": self.justification,

            "data_access_count_24h":
                self.data_access_count_24h,

            "ip_address": self.ip_address,

            "field": self.field,
            "operator": self.operator,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,

            "detected_at": self.detected_at
        }