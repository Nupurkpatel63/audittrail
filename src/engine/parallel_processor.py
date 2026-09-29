
import pandas as pd
import os
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor


CHUNK_SIZE = 500


def chunk_dataframe(
    df: pd.DataFrame,
    chunk_size: int = CHUNK_SIZE
):
    """
    Split a DataFrame into chunks of fixed size.

    Preserves the original DataFrame columns
    and row indexes.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    for start in range(0, len(df), chunk_size):

        yield df.iloc[
            start:start + chunk_size
        ]


def _evaluate_chunk(payload):
    """
    Evaluate one DataFrame chunk using the existing
    configuration-driven RuleEngine.

    Args:
        payload: (chunk_id, chunk_df, rules)

    Returns:
        (chunk_id, list[Violation])
    """

    chunk_id, chunk_df, rules = payload

    # Import inside the worker to keep the worker
    # self-contained for multiprocessing.
    from src.engine.rule_engine import RuleEngine

    engine = RuleEngine(rules)

    violations = engine.evaluate(chunk_df)

    return chunk_id, violations


class ParallelComplianceProcessor:
    """
    Concurrent chunk-based compliance processor.
    Designed to avoid Windows multiprocessing spawn issues
    when called from a Streamlit dashboard.
    """

    def __init__(self, rules, chunk_size=2000, max_workers=None):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        self.rules = rules
        self.chunk_size = chunk_size

        cpu_count = os.cpu_count() or 2

        # Avoid creating excessive threads.
        self.max_workers = max_workers or min(8, cpu_count)

    def process(self, df):
        start_time = perf_counter()
        total_records = len(df)

        if total_records == 0:
            return [], {
                "records_processed": 0,
                "chunks_processed": 0,
                "chunk_size": self.chunk_size,
                "workers": self.max_workers,
                "elapsed_seconds": 0,
                "records_per_second": 0,
                "violations_found": 0,
            }

        total_chunks = (
            total_records + self.chunk_size - 1
        ) // self.chunk_size

        # Generate chunks lazily instead of storing all payloads.
        payloads = (
            (chunk_id, chunk, self.rules)
            for chunk_id, chunk in enumerate(
                chunk_dataframe(df, self.chunk_size)
            )
        )

        all_violations = []

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            # executor.map preserves chunk order.
            results = executor.map(
                _evaluate_chunk,
                payloads
            )

            for chunk_id, violations in results:
                all_violations.extend(violations)

        elapsed = perf_counter() - start_time

        metrics = {
            "records_processed": total_records,
            "chunks_processed": total_chunks,
            "chunk_size": self.chunk_size,
            "workers": self.max_workers,
            "elapsed_seconds": round(elapsed, 3),
            "records_per_second": round(
                total_records / elapsed, 2
            ) if elapsed else 0,
            "violations_found": len(all_violations),
        }

        return all_violations, metrics




    