from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogRecord:
    timestamp: datetime
    user_id: str
    action: str
    status: str
    data_type: str
    resource: str
    consent: bool
    ip_address: str