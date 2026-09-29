from pathlib import Path
from src.ingestion.loader import load_csv   
from src.validation.validator import LogValidator
from src.engine.registry import RuleRegistry
from src.engine.rule_engine import RuleEngine
from src.reporting.excel_report import ExcelReport
from src.reporting.html_report import HTMLReport
from src.audit.integrity import AuditIntegrity
from src.utils.logger import get_logger
from src.engine.parallel_processor import (
    ParallelComplianceProcessor
)


PROJECT_ROOT = Path(__file__).resolve().parent

logger = get_logger()


def run_parallel_audit(df, rules):
    processor = ParallelComplianceProcessor(
        rules=rules,
        chunk_size=500,
        max_workers=None
    )

    violations, metrics = processor.process(df)

    logger.info("Parallel processing metrics: %s", metrics)

    print("\n--- Parallel Audit Performance ---")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    return violations, metrics



def main():

    logger.info(
        "Starting Compliance Auditor"
    )

    # =========================================================
    # PATHS
    # =========================================================

    input_file = PROJECT_ROOT / "data" / "sample_logs_1000.csv"

    rules_file = PROJECT_ROOT / "config" / "rules.yaml"

    excel_output = PROJECT_ROOT / "reports" / "compliance_report.xlsx"

    html_output = PROJECT_ROOT / "reports" / "compliance_report.html"

    audit_output = PROJECT_ROOT / "reports" / "audit_chain.json"

    Path(excel_output).parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # =========================================================
    # LOAD DATA
    # =========================================================
    df = load_csv(input_file)

    logger.info(
        "Loaded %s log records",
        len(df)
    )

    # =========================================================
    # VALIDATE DATA
    # =========================================================

    validator = LogValidator()

    validator.validate(df)

    logger.info(
        "Log validation completed"
    )

    # =========================================================
    # LOAD RULES
    # =========================================================

    registry = RuleRegistry(
        rules_file
    )

    logger.info(
        "Loaded %s compliance rules",
        len(registry.rules)
    )

    # =========================================================
    # EXECUTE RULE ENGINE
    # =========================================================
        #engine = RuleEngine(
               # registry.rules
           # )
        
           # violations = engine.evaluate(
                #df
           # )
        
            #logger.info(
               # "Detected %s violations",
               # len(violations)
            #)

    violations, metrics = run_parallel_audit(
        df,
        registry.rules
    )

    logger.info(
        "Detected %s violations",
        len(violations)
    )

    logger.info(
     "Parallel processing completed in %s seconds",
     metrics["elapsed_seconds"]
    )
    
    

    # =========================================================
    # REPORTING
    # =========================================================

    ExcelReport().generate(
        violations,
        excel_output
    )

    HTMLReport().generate(
        violations,
        html_output
    )

    logger.info(
        "Reports generated successfully"
    )

    # =========================================================
    # TAMPER-EVIDENT AUDIT TRAIL
    # =========================================================

    audit = AuditIntegrity()

    for violation in violations:

        audit.add_record({

            "rule_id": violation.rule_id,

            "rule_name": violation.rule_name,

            "category": getattr(
                violation,
                "category",
                ""
            ),

            "severity": violation.severity,

            "timestamp": str(
                violation.timestamp
            ),

            "user_id": violation.user_id,

            "action": violation.action,

            "resource": violation.resource,

            "description": violation.description
        })

    audit.save(
        audit_output
    )

    integrity_status = audit.verify()

    logger.info(
        "Audit chain integrity: %s",
        integrity_status
    )

    logger.info(
        "Compliance audit completed successfully"
    )


if __name__ == "__main__":
    main()