from datetime import datetime
from pathlib import Path

REPORT_PATH = Path(__file__).parent / "test_results" / "test_results.md"


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Writes a markdown summary of the test run to test_results.md,
    alongside pytest's normal console output."""
    rows = []

    for outcome, reports in terminalreporter.stats.items():
        if outcome not in ("passed", "failed", "skipped"):
            continue
        for report in reports:
            is_result = report.when == "call" or (
                outcome == "failed" and report.when in ("setup", "teardown")
            )
            if is_result:
                rows.append((report.nodeid, outcome, getattr(report, "duration", 0.0)))

    rows.sort(key=lambda row: row[0])

    lines = [
        "# datastore.py Test Results",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| Test | Outcome | Duration (s) |",
        "|---|---|---|",
    ]
    lines += [
        f"| `{nodeid}` | {outcome.upper()} | {duration:.4f} |"
        for nodeid, outcome, duration in rows
    ]

    passed = sum(1 for _, outcome, _ in rows if outcome == "passed")
    failed = sum(1 for _, outcome, _ in rows if outcome == "failed")
    skipped = sum(1 for _, outcome, _ in rows if outcome == "skipped")
    total = len(rows)

    summary = f"**Summary:** {passed}/{total} passed"
    if failed:
        summary += f", {failed} failed"
    if skipped:
        summary += f", {skipped} skipped"

    lines += ["", summary]

    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
