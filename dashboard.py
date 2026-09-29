from io import BytesIO
from datetime import datetime
from time import perf_counter
import hashlib, json
import pandas as pd
import streamlit as st
import yaml

from src.analytics.trend_analyzer import TrendAnalyzer
from src.analytics.risk_scorer import RiskScorer
from src.analytics.rule_explainer import RuleExplainer
from src.validation.validator import LogValidator
from src.engine.registry import RuleRegistry
from src.engine.parallel_processor import (ParallelComplianceProcessor)
from src.reporting.excel_report import ExcelReport
from src.reporting.html_report import HTMLReport
from src.audit.integrity import AuditIntegrity
from pathlib import Path


@st.cache_data
def get_rule_explanations(rules):
    return RuleExplainer(rules).explain_all()

@st.cache_data(show_spinner=False)
def get_trend_results(violations, frequency):
    analyzer = TrendAnalyzer(violations)

    return {
        "overall": analyzer.get_overall_trend(frequency),
        "severity": analyzer.get_severity_trend(frequency),
        "rule": analyzer.get_rule_trend(frequency),
    }


@st.cache_data(show_spinner=False)
def get_risk_results(violations):
    scorer = RiskScorer(violations)

    return {
        "user": scorer.get_user_risk(),
        "resource": scorer.get_resource_risk(),
    }


@st.cache_data(show_spinner=False)
def get_download_bytes(path, modified_ns, size):
    """Cache report payloads across Streamlit reruns."""
    return Path(path).read_bytes()

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Compliance Auditor", page_icon="🛡️", layout="wide")

# ---------------------------------------------------------
# Center Screen Loading Spinner
# ---------------------------------------------------------
st.markdown("""
<style>
.center-loader-overlay {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(255, 255, 255, 0.72);
    z-index: 999999;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

.center-loader-spinner {
    width: 70px;
    height: 70px;
    border: 7px solid #e6e6e6;
    border-top: 7px solid #1f77b4;
    border-radius: 50%;
    animation: center-loader-spin 0.9s linear infinite;
}

.center-loader-text {
    margin-top: 18px;
    font-size: 20px;
    font-weight: 600;
    color: #333333;
}

@keyframes center-loader-spin {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}
</style>
""", unsafe_allow_html=True)
st.title("🛡️ Compliance Audit Dashboard")
st.caption("Upload log data and configurable rules, run an auditable compliance review, and export findings.")

with st.sidebar:
    st.header("Audit inputs")
    st.caption("Rules are evaluated locally using the configured operator registry.")

csv_file = st.file_uploader("1. Upload audit log data (CSV)", type=["csv"], key="csv_upload")
rules_file = st.file_uploader("2. Upload compliance rules (YAML or JSON)", type=["yaml", "yml", "json"], key="rules_upload")

if not csv_file:
    st.info("Upload a CSV file to begin.")
    st.stop()
try:
    df = pd.read_csv(BytesIO(csv_file.getvalue()))
except Exception as exc:
    st.error(f"Could not parse CSV: {exc}")
    st.stop()
if df.empty:
    st.error("The uploaded CSV contains no records.")
    st.stop()

if rules_file:
    try:
        raw = rules_file.getvalue().decode("utf-8-sig")
        if rules_file.name.lower().endswith(".json"):
            config = json.loads(raw)
        else:
            config = yaml.safe_load(raw)
        registry = RuleRegistry(config)
        rules = registry.rules
        rules_source_name = rules_file.name
        st.success(f"Loaded and validated {len(rules)} rules from {rules_source_name}.")
        with st.expander("Preview uploaded rules"):
            st.code(yaml.safe_dump(rules, sort_keys=False), language="yaml")
    except Exception as exc:
        st.error(f"Rules file is invalid: {exc}")
        st.stop()
else:
    default_path = ROOT / "config" / "rules.yaml"
    if not default_path.is_file():
        st.warning("Upload a YAML/JSON rules file, or add config/rules.yaml as the default ruleset.")
        st.stop()
    try:
        registry = RuleRegistry(default_path)
        rules = registry.rules
        rules_source_name = "config/rules.yaml (default)"
        st.info(f"Using default rules: {len(rules)} loaded. Upload a rules file to override.")
    except Exception as exc:
        st.error(f"Default rules are invalid: {exc}")
        st.stop()

st.subheader("📄 Uploaded data")
a, b, c = st.columns(3)
a.metric("Records", f"{len(df):,}")
b.metric("Columns", len(df.columns))
c.metric("File size", f"{csv_file.size / 1024:.1f} KB")
with st.expander("Preview CSV", expanded=True):
    st.dataframe(df.head(100), use_container_width=True)
with st.expander("Column profile"):
    st.dataframe(pd.DataFrame({"Column": df.columns, "Type": df.dtypes.astype(str).values, "Missing": df.isna().sum().values}), use_container_width=True)

loader_placeholder = None

if st.button("🚀 Run Compliance Audit", type="primary"):
    audit_started = perf_counter()
    loader_placeholder = st.empty()
    loader_placeholder.markdown(
        '<div class="center-loader-overlay"><div class="center-loader-spinner"></div>'
        '<div class="center-loader-text">Starting compliance audit…</div></div>',
        unsafe_allow_html=True,
    )

    try:
        # loader_placeholder.markdown("""
        #         <div class="center-loader-overlay">
        #             <div class="center-loader-spinner"></div>
        #             <div class="center-loader-text">
        #                 Running Compliance Audit...<br>
        #                 <span style="font-size:14px;font-weight:400;">
        #                     Please wait while the audit is being processed.
        #                 </span>
        #             </div>
        #         </div>
        #     """, unsafe_allow_html=True)
        
        # Require fields referenced by rules; this allows different CSV schemas per ruleset.
        required = []
        for rule in rules:
            if rule.get("field"): required.append(rule["field"])
            if rule.get("compare_with"): required.append(rule["compare_with"])
            for cond in rule.get("conditions", []):
                if cond.get("field"): required.append(cond["field"])
                if cond.get("compare_with"): required.append(cond["compare_with"])
        LogValidator().validate(df, required_columns=required)
        loader_placeholder.markdown(
            '<div class="center-loader-overlay"><div class="center-loader-spinner"></div>'
            '<div class="center-loader-text">Checking records against rules…</div></div>',
            unsafe_allow_html=True,
        )
        # The custom centered loader remains visible during the full
        # audit/report/integrity processing block below.
        # ---------------------------------------------------------
        # PARALLEL COMPLIANCE PROCESSING
        # ---------------------------------------------------------

        processor = ParallelComplianceProcessor(
            rules=rules,
            chunk_size=2000,
            max_workers=None
        )

        violations, metrics = processor.process(df)
        loader_placeholder.markdown(
            '<div class="center-loader-overlay"><div class="center-loader-spinner"></div>'
            '<div class="center-loader-text">Generating Excel and HTML reports…</div></div>',
            unsafe_allow_html=True,
        )

    # Display processing performance in the dashboard
        st.subheader("⚡ Parallel Processing Performance")

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
        "Records Processed",
        f"{metrics['records_processed']:,}"
        )

        m2.metric(
        "Chunks Processed",
        f"{metrics['chunks_processed']:,}"
        )

        m3.metric(
        "Processing Time",
        f"{metrics['elapsed_seconds']:.3f} sec"
        )

        m4.metric(
            "Records / Second",
            f"{metrics['records_per_second']:,.0f}"
        )

        st.caption(
            f"Parallel workers: {metrics['workers']} | "
            f"Chunk size: {metrics['chunk_size']}"
        )
        vdf = pd.DataFrame([v.to_dict() if hasattr(v, "to_dict") else vars(v) for v in violations])
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = REPORTS / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        excel_path = run_dir / "compliance_report.xlsx"
        html_path = run_dir / "compliance_report.html"
        audit_path = run_dir / "audit_chain.json"
        ExcelReport().generate(violations, str(excel_path))
        HTMLReport().generate(violations, str(html_path))


            
            # -------------------------------------------------
            # Create audit chain with source and rule metadata
            # -------------------------------------------------
        audit = AuditIntegrity()

        audit.add_record({
                "event": "audit_run_started",
                "run_id": run_id,
                "source_file": csv_file.name,
                "source_sha256": hashlib.sha256(
                    csv_file.getvalue()
                ).hexdigest(),
                "rules_file": rules_source_name,
                "rules_sha256": hashlib.sha256(
                    yaml.safe_dump(
                        rules, sort_keys=True
                    ).encode()
                ).hexdigest(),
                "records_processed": len(df),
                "violations_detected": len(violations)
            })

            # Add individual violation records
        for item in violations:
                audit.add_record(
                    item.to_dict()
                    if hasattr(item, "to_dict")
                    else vars(item)
                )

            # -------------------------------------------------
            # Add hashes of generated report files to the chain
            # -------------------------------------------------
        audit.add_file_record(excel_path)
        audit.add_file_record(html_path)

            # Save chain after all records have been added
        audit.save(str(audit_path))

        loader_placeholder.markdown(
            '<div class="center-loader-overlay"><div class="center-loader-spinner"></div>'
            '<div class="center-loader-text">Verifying audit chain and reports…</div></div>',
            unsafe_allow_html=True,
        )

            # Verify both the chain and report file contents
        reports_integrity, integrity_messages = (
                audit.verify_report_files(run_dir)
            )

        # verify_report_files also validates the hash chain, so this single
        # call verifies both the chain and report file hashes.
        integrity = reports_integrity
        total_elapsed = perf_counter() - audit_started
        st.session_state["audit_result"] = {
            "vdf": vdf,

        # FIX: Save violations for trend analysis after Streamlit reruns
            "violations": [
                item.to_dict() if hasattr(item, "to_dict") else vars(item)
            for item in violations
             ],

            "records": len(df),
            "rule_count": len(rules),
            "run_id": run_id,
            "integrity": integrity,
            "integrity_messages": integrity_messages,
            "excel": str(excel_path),
            "html": str(html_path),
            "audit": str(audit_path),
            "rules": rules,
            "parallel_metrics": metrics,
            "total_elapsed_seconds": total_elapsed,
        }
        
        st.success(f"Audit completed in {total_elapsed:.2f} seconds.")
        if total_elapsed > 60:
            st.warning("This run exceeded the 60-second target. Total time includes processing, report generation, and integrity verification.")

    except Exception as exc:
        st.error(f"Audit failed: {exc}")
        st.exception(exc)

    finally:
        # Remove the centered loader after success or failure.
        if loader_placeholder is not None:
            loader_placeholder.empty()


# ---------------------------------------------------------
# Results navigation and section views
# ---------------------------------------------------------

def _trend_results(result, frequency):
    cache = result.setdefault("_trend_cache", {})
    if frequency not in cache:
        cache[frequency] = get_trend_results(result.get("violations", []), frequency)
    return cache[frequency]


def _risk_results(result):
    if "_risk_results" not in result:
        result["_risk_results"] = get_risk_results(result.get("violations", []))
    return result["_risk_results"]


def _show_section_loader(section_name):
    placeholder = st.empty()
    placeholder.markdown(
        '<div class="center-loader-overlay"><div class="center-loader-spinner"></div>'
        f'<div class="center-loader-text">Loading {section_name}…</div></div>',
        unsafe_allow_html=True,
    )
    return placeholder


with st.sidebar:
    st.divider()
    section = st.radio(
        "Audit sections",
        ["Dashboard", "Trend Analysis", "Rule Explanations", "Risk Scoring", "Charts", "Violations", "Downloads"],
        key="dashboard_section",
    )

result = st.session_state.get("audit_result")
if result is None:
    st.info("Run an audit to view its dashboard, trends, explanations, risk scores, findings, and downloads.")
else:
    vdf = result["vdf"]
    saved_violations = result.get("violations", [])
    saved_rules = result.get("rules", [])
    section_loader = _show_section_loader(section)

    if section == "Dashboard":
        st.header("Audit Dashboard")
        unique_affected = vdf["record_id"].nunique() if not vdf.empty and "record_id" in vdf else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Records audited", f"{result['records']:,}")
        c2.metric("Violations", f"{len(vdf):,}")
        c3.metric("Affected records", f"{unique_affected:,}")
        c4.metric("Rules loaded", result["rule_count"])
        st.caption(f"Full audit, report generation, and integrity verification: {result.get('total_elapsed_seconds', 0):.2f} sec")
        metrics = result.get("parallel_metrics", {})
        if metrics:
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Processing time", f"{metrics.get('elapsed_seconds', 0):.3f} sec")
            p2.metric("Records / second", f"{metrics.get('records_per_second', 0):,.0f}")
            p3.metric("Chunks processed", f"{metrics.get('chunks_processed', 0):,}")
            p4.metric("Workers", metrics.get("workers", 0))
        if result["integrity"]:
            st.success("Audit chain and report integrity: VERIFIED")
        else:
            st.error("Audit chain or report integrity: FAILED")
        with st.expander("Integrity verification details"):
            for message in result["integrity_messages"]:
                st.write(message)

    elif section == "Trend Analysis":
        st.header("Compliance Trend Analysis")
        frequency = st.selectbox("Trend period", ["daily", "weekly", "monthly"], key="trend_frequency")
        if saved_violations:
            overall = _trend_results(result, frequency)["overall"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Trend direction", overall["direction"])
            c2.metric("Change vs previous period", overall["change"])
            pct = overall["percentage_change"]
            c3.metric("Percentage change", f"{pct:.2f}%" if pct is not None else "N/A")
            st.caption("Open Charts in the sidebar to view the trend charts.")
        else:
            st.info("No violations are available for trend analysis.")

    elif section == "Rule Explanations":
        st.header("Compliance Rule Explanations")
        if "_rule_explanations" not in result:
            result["_rule_explanations"] = get_rule_explanations(saved_rules)
        with st.container(height=500, border=False):
            if result["_rule_explanations"]:
                for item in result["_rule_explanations"]:
                    st.markdown(f"**{item['rule_id']} ? {item['rule_name']}** ({item['severity']})")
                    st.write(item["explanation"])
                    st.divider()
            else:
                st.info("No rule configuration available.")
        if saved_violations:
            max_options = min(len(saved_violations), 100)
            selected_index = st.selectbox(
                "Explain a finding",
                options=list(range(max_options)),
                format_func=lambda i: f"Finding {i + 1} ? Rule {saved_violations[i].get('rule_id', 'Unknown')}",
                key=f"selected_violation_{result['run_id']}",
            )
            st.write(RuleExplainer(saved_rules).explain_violation(saved_violations[selected_index]))
            if len(saved_violations) > max_options:
                st.caption(f"Showing the first {max_options} findings for explanation; all findings remain in the reports.")
        else:
            st.success("No violations detected, so there are no finding explanations.")

    elif section == "Risk Scoring":
        st.header("Compliance Risk Scoring")
        if saved_violations:
            risks = _risk_results(result)
            for key, label in (("user", "User"), ("resource", "Resource")):
                data = risks[key]
                st.subheader(f"Risk by {label}")
                if data.empty:
                    st.info(f"No {label.lower()} risk scores are available.")
                else:
                    st.caption(f"Showing up to 500 of {len(data):,} {label.lower()}s.")
                    st.dataframe(data.head(500), use_container_width=True, hide_index=True)
        else:
            st.info("No violations were detected, so risk scores are not available.")

    elif section == "Charts":
        st.header("Audit Charts")
        if saved_violations:
            frequency = st.selectbox("Trend period", ["daily", "weekly", "monthly"], key="chart_frequency")
            trends = _trend_results(result, frequency)
            overall_df = pd.DataFrame(trends["overall"]["data"])
            if not overall_df.empty:
                st.subheader("Overall violations over time")
                overall_df["period"] = pd.to_datetime(overall_df["period"])
                st.line_chart(overall_df.set_index("period")["violations"])
            severity_df = trends["severity"]
            if not severity_df.empty:
                st.subheader("Severity trends")
                st.line_chart(severity_df.pivot(index="period", columns="severity", values="violations").fillna(0))
            rule_df = trends["rule"]
            if not rule_df.empty:
                st.subheader("Rule-wise violation trends")
                top_rules = rule_df.groupby("rule_id")["violations"].sum().nlargest(20).index
                chart_data = rule_df[rule_df["rule_id"].isin(top_rules)]
                st.line_chart(chart_data.pivot(index="period", columns="rule_id", values="violations").fillna(0))
                if rule_df["rule_id"].nunique() > len(top_rules):
                    st.caption("Showing the 20 rules with the most violations.")
            st.subheader("Violation counts by severity")
            if "severity" in vdf:
                st.bar_chart(vdf["severity"].fillna("Unspecified").astype(str).value_counts())
            risks = _risk_results(result)
            for key, label, id_column in (("user", "Top users by risk", "user_id"), ("resource", "Top resources by risk", "resource")):
                data = risks[key].head(100)
                if not data.empty:
                    st.subheader(label)
                    st.bar_chart(data.set_index(id_column)["risk_score"])
        else:
            st.info("No violations are available to chart.")

    elif section == "Violations":
        st.header("Violations")
        if vdf.empty:
            st.success("No violations were detected.")
        else:
            if "severity" in vdf.columns:
                severity_values = vdf["severity"].fillna("Unspecified").astype(str)
                severities = sorted(severity_values.unique())
                selected = st.multiselect("Filter severity", severities, default=severities, key=f"severity_filter_{result['run_id']}")
                shown = vdf.loc[severity_values.isin(selected)]
            else:
                shown = vdf
            display_limit = 500
            st.caption(f"Displaying up to {display_limit:,} findings. Total matching findings: {len(shown):,}. Download Excel for the complete results.")
            st.dataframe(shown.head(display_limit), use_container_width=True, hide_index=True)

    elif section == "Downloads":
        st.header("Download Audit Reports")
        def cached_report(path):
            report = Path(path)
            stat = report.stat()
            return get_download_bytes(str(report), stat.st_mtime_ns, stat.st_size)
        x, h, a = st.columns(3)
        x.download_button("Download Excel", cached_report(result["excel"]), file_name="compliance_report.xlsx")
        h.download_button("Download HTML", cached_report(result["html"]), file_name="compliance_report.html", mime="text/html")
        a.download_button("Download audit chain", cached_report(result["audit"]), file_name="audit_chain.json", mime="application/json")

    # Keep the custom overlay up through the selected view's calculations,
    # table/chart construction, and download payload preparation.
    section_loader.empty()
