
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class AuditIntegrity:
    """SHA-256 hash chain for audit records and generated report files."""

    def __init__(self):
        self.chain = []

    @staticmethod
    def _calculate_hash(data):
        """Create a deterministic SHA-256 hash for JSON-compatible data."""
        payload = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _file_hash(file_path):
        """Hash a file in chunks to avoid loading large files into memory."""
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def add_record(self, data):
        """Append a record to the hash chain."""
        previous_hash = (
            self.chain[-1]["hash"] if self.chain else "GENESIS"
        )

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_hash": previous_hash,
            "data": data
        }

        record["hash"] = self._calculate_hash(record)
        self.chain.append(record)

    def add_file_record(self, file_path):
        """
        Add a generated report's SHA-256 hash to the chain.
        Store only the filename so the report directory can be moved.
        """
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"Report file not found: {path}")

        self.add_record({
            "type": "report_file",
            "file_name": path.name,
            "sha256": self._file_hash(path),
            "size_bytes": path.stat().st_size
        })

    def save(self, file_path):
        """Persist the chain as JSON."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.chain, file, indent=4, default=str)

    def verify(self):
        """Verify record hashes and previous-hash links in memory."""
        previous_hash = "GENESIS"

        for record in self.chain:
            if record.get("previous_hash") != previous_hash:
                return False

            stored_hash = record.get("hash")

            data = {
                "timestamp": record["timestamp"],
                "previous_hash": record["previous_hash"],
                "data": record["data"]
            }

            calculated_hash = self._calculate_hash(data)

            if calculated_hash != stored_hash:
                return False

            previous_hash = stored_hash

        return True

    def verify_report_files(self, report_dir):
        """
        Verify every report_file record against the current file contents.
        Returns (is_valid, messages).
        """
        report_dir = Path(report_dir)
        messages = []

        if not self.verify():
            return False, ["Audit hash chain verification FAILED."]

        for record in self.chain:
            data = record.get("data", {})

            if data.get("type") != "report_file":
                continue

            file_name = data.get("file_name")

            # Prevent paths in the manifest from escaping report_dir.
            if not file_name or Path(file_name).name != file_name:
                messages.append("Invalid report filename in audit chain.")
                continue

            file_path = report_dir / file_name

            if not file_path.is_file():
                messages.append(f"Report missing: {file_name}")
                continue

            current_hash = self._file_hash(file_path)

            if current_hash != data.get("sha256"):
                messages.append(f"Report modified: {file_name}")
            else:
                messages.append(f"Report verified: {file_name}")

        failed = any(
            message.startswith(("Report missing:", "Report modified:",
                               "Invalid report"))
            for message in messages
        )

        return not failed, messages