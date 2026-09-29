import hashlib
import json
from datetime import datetime


class AuditIntegrity:

    def __init__(self):
        self.chain = []

    def add_record(self, data):

        previous_hash = (
            self.chain[-1]["hash"]
            if self.chain
            else "GENESIS"
        )

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "previous_hash": previous_hash,
            "data": data
        }

        payload = json.dumps(
            record,
            sort_keys=True,
            default=str
        )

        record["hash"] = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

        self.chain.append(record)

    def save(self, file_path):

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                self.chain,
                file,
                indent=4,
                default=str
            )

    def verify(self):

        previous_hash = "GENESIS"

        for record in self.chain:

            if record["previous_hash"] != previous_hash:
                return False

            stored_hash = record["hash"]

            data = {
                "timestamp": record["timestamp"],
                "previous_hash": record["previous_hash"],
                "data": record["data"]
            }

            payload = json.dumps(
                data,
                sort_keys=True,
                default=str
            )

            calculated_hash = hashlib.sha256(
                payload.encode("utf-8")
            ).hexdigest()

            if calculated_hash != stored_hash:
                return False

            previous_hash = stored_hash

        return True