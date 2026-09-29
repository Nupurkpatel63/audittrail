from pathlib import Path
import html


class HTMLReport:
    """
    HTML compliance report generator.

    Input:
        list[Violation]

    The report consumes Violation objects directly.
    """

    def generate(self, violations, output_file):

        output_path = Path(output_file)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        total = len(violations)

        # ---------------------------------------------------------
        # Severity summary
        # ---------------------------------------------------------

        critical = sum(
            1
            for v in violations
            if str(v.severity).upper() == "CRITICAL"
        )

        high = sum(
            1
            for v in violations
            if str(v.severity).upper() == "HIGH"
        )

        medium = sum(
            1
            for v in violations
            if str(v.severity).upper() == "MEDIUM"
        )

        low = sum(
            1
            for v in violations
            if str(v.severity).upper() == "LOW"
        )

        # ---------------------------------------------------------
        # Build table rows
        # ---------------------------------------------------------

        rows = []

        for violation in violations:

            severity = str(
                violation.severity or ""
            ).upper()

            rows.append(
                f"""
                <tr>
                    <td>{self._safe(violation.record_id)}</td>

                    <td>
                        {self._safe(violation.timestamp)}
                    </td>

                    <td>
                        {self._safe(violation.user_id)}
                    </td>

                    <td>
                        {self._safe(violation.department)}
                    </td>

                    <td>
                        {self._safe(violation.role)}
                    </td>

                    <td>
                        {self._safe(violation.action)}
                    </td>

                    <td>
                        {self._safe(violation.resource)}
                    </td>

                    <td>
                        {self._safe(violation.rule_id)}
                    </td>

                    <td>
                        {self._safe(violation.rule_name)}
                    </td>

                    <td>
                        <span class="severity {severity.lower()}">
                            {self._safe(severity)}
                        </span>
                    </td>

                    <td>
                        {self._safe(violation.field)}
                    </td>

                    <td>
                        {self._safe(violation.actual_value)}
                    </td>

                    <td>
                        {self._safe(violation.expected_value)}
                    </td>

                    <td>
                        {self._safe(violation.approver_id)}
                    </td>

                    <td>
                        {self._safe(violation.sod_conflict)}
                    </td>

                    <td>
                        {self._safe(violation.consent)}
                    </td>

                    <td>
                        {self._safe(violation.ip_address)}
                    </td>

                    <td>
                        {self._safe(violation.source_row)}
                    </td>

                    <td>
                        {self._safe(violation.detected_at)}
                    </td>
                </tr>
                """
            )

        # ---------------------------------------------------------
        # Empty result
        # ---------------------------------------------------------

        if not rows:

            rows.append(
                """
                <tr>
                    <td colspan="19" class="no-data">
                        No compliance violations detected.
                    </td>
                </tr>
                """
            )

        table_rows = "\n".join(rows)

        # ---------------------------------------------------------
        # HTML document
        # ---------------------------------------------------------

        html_content = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Compliance Audit Report</title>

<style>

body {{
    font-family: Arial, Helvetica, sans-serif;
    margin: 0;
    background: #f4f6f8;
    color: #222;
}}

.header {{
    background: #1f2937;
    color: white;
    padding: 30px;
}}

.header h1 {{
    margin: 0;
}}

.header p {{
    margin-top: 8px;
    color: #d1d5db;
}}

.container {{
    padding: 25px;
}}

.dashboard {{
    display: grid;
    grid-template-columns:
        repeat(5, minmax(160px, 1fr));

    gap: 15px;
    margin-bottom: 25px;
}}

.card {{
    background: white;
    border-radius: 8px;
    padding: 20px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.08);
}}

.card-title {{
    font-size: 13px;
    color: #6b7280;
}}

.card-value {{
    font-size: 30px;
    font-weight: bold;
    margin-top: 8px;
}}

.table-container {{
    background: white;
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 1800px;
}}

th {{
    background: #374151;
    color: white;
    padding: 10px;
    text-align: left;
    position: sticky;
    top: 0;
}}

td {{
    border-bottom: 1px solid #e5e7eb;
    padding: 9px;
    white-space: nowrap;
}}

tr:hover {{
    background: #f9fafb;
}}

.severity {{
    font-weight: bold;
    padding: 5px 9px;
    border-radius: 4px;
}}

.critical {{
    background: #fecaca;
    color: #991b1b;
}}

.high {{
    background: #fed7aa;
    color: #9a3412;
}}

.medium {{
    background: #fef3c7;
    color: #92400e;
}}

.low {{
    background: #dcfce7;
    color: #166534;
}}

.no-data {{
    text-align: center;
    padding: 30px;
}}

.footer {{
    margin-top: 25px;
    color: #6b7280;
    font-size: 13px;
}}

@media(max-width: 900px) {{

    .dashboard {{
        grid-template-columns:
            repeat(2, 1fr);
    }}

}}

</style>

</head>

<body>

<div class="header">

    <h1>
        Compliance Audit Report
    </h1>

    <p>
        Automated Compliance &amp; Audit Trail
    </p>

</div>

<div class="container">

    <div class="dashboard">

        <div class="card">

            <div class="card-title">
                Total Violations
            </div>

            <div class="card-value">
                {total}
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Critical
            </div>

            <div class="card-value">
                {critical}
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                High
            </div>

            <div class="card-value">
                {high}
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Medium
            </div>

            <div class="card-value">
                {medium}
            </div>

        </div>


        <div class="card">

            <div class="card-title">
                Low
            </div>

            <div class="card-value">
                {low}
            </div>

        </div>

    </div>


    <div class="table-container">

        <h2>
            Detected Compliance Violations
        </h2>

        <table>

            <thead>

                <tr>

                    <th>Record ID</th>
                    <th>Event Timestamp</th>
                    <th>User ID</th>
                    <th>Department</th>
                    <th>Role</th>
                    <th>Action</th>
                    <th>Resource</th>

                    <th>Rule ID</th>
                    <th>Rule Name</th>
                    <th>Severity</th>

                    <th>Field</th>
                    <th>Actual Value</th>
                    <th>Expected Value</th>

                    <th>Approver ID</th>
                    <th>SoD Conflict</th>
                    <th>Consent</th>

                    <th>IP Address</th>
                    <th>Source Row</th>
                    <th>Detected At</th>

                </tr>

            </thead>

            <tbody>

                {table_rows}

            </tbody>

        </table>

    </div>


    <div class="footer">

        Generated by Automated Compliance &amp;
        Audit Trail system.

    </div>

</div>

</body>

</html>
"""

        # ---------------------------------------------------------
        # Write file
        # ---------------------------------------------------------

        try:

            output_path.write_text(
                html_content,
                encoding="utf-8"
            )

            print(
                "HTML compliance report generated successfully:"
            )

            print(
                output_path.resolve()
            )

        except PermissionError:

            raise PermissionError(
                f"Unable to write HTML report: "
                f"{output_path.resolve()}. "
                f"Close the HTML file if it is open."
            )

    @staticmethod
    def _safe(value):

        if value is None:
            return ""

        return html.escape(
            str(value)
        )