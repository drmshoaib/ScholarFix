"""Small local benchmark for deterministic ScholarFix helpers."""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feedback.citation_checker import check_citations
from feedback.math_checker import check_math_definitions
from reports.report_generator import generate_markdown_report
from utils.diff_utils import diff_highlight
from utils.text_metrics import readability_metrics


SAMPLE_TEXT = (
    "Let R(t) denote reviewer pressure. Prior work [1] shows that clarity matters. "
    "We define x_i as the notation quality score. "
) * 100


def time_call(label: str, func, *args) -> tuple[str, float]:
    """Time a function call and return label plus elapsed milliseconds."""
    start = time.perf_counter()
    func(*args)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return label, elapsed_ms


def main() -> None:
    """Run a compact benchmark table."""
    timings = [
        time_call("readability_metrics", readability_metrics, SAMPLE_TEXT),
        time_call("math_checker", check_math_definitions, SAMPLE_TEXT),
        time_call("citation_checker", check_citations, SAMPLE_TEXT),
        time_call("html_diff", diff_highlight, SAMPLE_TEXT[:1000], SAMPLE_TEXT[:900] + " revised"),
        time_call(
            "markdown_report",
            generate_markdown_report,
            ["Math issue"],
            ["Citation issue"],
            "Improved text.",
        ),
    ]

    print("ScholarFix local benchmark")
    print("--------------------------")
    for label, elapsed_ms in timings:
        print(f"{label:<22} {elapsed_ms:>9.2f} ms")


if __name__ == "__main__":
    main()
