#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
IMPORTS_BULK_DIR = BACKEND_DIR / "imports" / "bulk"

BATCH_TIERS = [
    (100, 250, "100-250"),
    (250, 500, "250-500"),
    (500, 1000, "500-1,000"),
]

CATEGORY_FILES = {
    "baby_formula",
    "baby_meals",
    "baby_porridge",
    "fruit_puree",
    "baby_snacks",
    "toddler_yoghurt",
    "household_cleaning",
    "laundry",
    "dishwasher",
    "surface_cleaners",
}

RETAILER_NAMES = {
    "tesco": "Tesco",
    "asda": "Asda",
    "sainsburys": "Sainsbury's",
    "waitrose": "Waitrose",
    "ocado": "Ocado",
    "morrisons": "Morrisons",
    "marks_spencer": "M&S",
    "iceland": "Iceland",
    "aldi": "Aldi",
    "lidl": "Lidl",
    "farmfoods": "Farmfoods",
    "home_bargains": "Home Bargains",
    "bm": "B&M",
    "heron": "Heron",
}


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for row in csv.DictReader(handle) if any((value or "").strip() for value in row.values()))


def discover_category_files(retailer: Optional[str] = None) -> List[Tuple[Path, str, str, int]]:
    files: List[Tuple[Path, str, str, int]] = []
    for path in sorted(IMPORTS_BULK_DIR.glob("*/*.csv")):
        if path.name == "raw.csv" or path.parent.name == "baby_toddler":
            continue
        category = path.stem
        if category not in CATEGORY_FILES:
            continue
        retailer_key = path.parent.name
        retailer_name = RETAILER_NAMES.get(retailer_key, retailer_key)
        if retailer and retailer_name.lower() != retailer.lower() and retailer_key.lower() != retailer.lower():
            continue
        row_count = count_csv_rows(path)
        if row_count <= 0:
            continue
        files.append((path, retailer_name, category, row_count))
    return files


def run_command(label: str, command: Sequence[str]) -> Dict[str, object]:
    print("\nRunning {0}".format(label))
    print("$ {0}".format(" ".join(command)))
    completed = subprocess.run(
        list(command),
        cwd=str(BACKEND_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = completed.stdout or ""
    if output.strip():
        print(output.rstrip())
    print("{0}: {1}".format(label, "PASS" if completed.returncode == 0 else "FAIL"))
    return {
        "label": label,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "output": output,
    }


def parse_metric(output: str, name: str) -> Optional[int]:
    pattern = r"{0}\s*:\s*([0-9]+)".format(re.escape(name))
    match = re.search(pattern, output, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def classify_batch_size(row_count: int) -> Tuple[str, bool]:
    for low, high, label in BATCH_TIERS:
        if low <= row_count <= high:
            return label, True
    if row_count < BATCH_TIERS[0][0]:
        return "below 100", True
    return "above 1,000", False


def validation_issues(result: Dict[str, object], total_rows: int, max_warning_rate: float) -> List[str]:
    issues: List[str] = []
    output = str(result.get("output") or "")
    if int(result.get("returncode") or 0) != 0:
        issues.append("real product batch validation failed")
    for metric in ["errors", "blocked rows", "duplicates", "malformed rows"]:
        value = parse_metric(output, metric)
        if value is not None and value > 0:
            issues.append("{0}: {1}".format(metric, value))
    warnings = parse_metric(output, "warnings")
    if warnings is not None and total_rows > 0:
        rate = (warnings / float(total_rows)) * 100.0
        if rate > max_warning_rate:
            issues.append(
                "warning rate {0:.1f}% exceeds acceptable threshold {1:.1f}%".format(
                    rate,
                    max_warning_rate,
                )
            )
    return issues


def report_issues(result: Dict[str, object]) -> List[str]:
    issues: List[str] = []
    label = str(result.get("label") or "command")
    output = str(result.get("output") or "")
    if int(result.get("returncode") or 0) != 0:
        issues.append("{0} failed".format(label))
    for metric in ["Errors count", "errors_count", "Rows skipped", "rows_skipped"]:
        value = parse_metric(output, metric)
        if value is not None and value > 0:
            issues.append("{0} reported {1}: {2}".format(label, metric, value))
    if re.search(r"Validation warnings:\s*[1-9]", output):
        issues.append("{0} reported backend validation warnings".format(label))
    if re.search(r"Validation errors:\s*[1-9]", output):
        issues.append("{0} reported backend validation errors".format(label))
    return issues


def dry_run_issue(result: Dict[str, object], csv_path: Path) -> List[str]:
    issues: List[str] = []
    output = str(result.get("output") or "")
    if int(result.get("returncode") or 0) != 0:
        issues.append("dry-run failed for {0}".format(csv_path))
    quality_blocks = parse_metric(output, "quality_blocks")
    if quality_blocks is not None and quality_blocks > 0:
        issues.append("dry-run quality blocks for {0}: {1}".format(csv_path, quality_blocks))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SafeBite controlled scaling import gate.")
    parser.add_argument("--retailer", help="Limit dry-runs to one retailer folder/name.")
    parser.add_argument(
        "--max-warning-rate",
        type=float,
        default=50.0,
        help="Maximum acceptable validator warning rate as a percentage of active rows.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: List[str] = []
    category_files = discover_category_files(args.retailer)
    total_rows = sum(item[3] for item in category_files)
    batch_tier, tier_allowed = classify_batch_size(total_rows)

    print("SafeBite controlled scaling gate")
    print("=" * 80)
    print("Active category CSV files: {0}".format(len(category_files)))
    print("Active rows: {0}".format(total_rows))
    print("Batch size tier: {0}".format(batch_tier))
    print("Acceptable warning threshold: {0:.1f}%".format(args.max_warning_rate))

    if not category_files:
        issues.append("no non-empty category CSV files found")
    if not tier_allowed:
        issues.append("batch size is above the 1,000 row controlled scaling limit")

    for path, retailer, category, row_count in category_files:
        print("- {0}: retailer={1}, category={2}, rows={3}".format(
            path.relative_to(BACKEND_DIR),
            retailer,
            category,
            row_count,
        ))

    command_results: List[Dict[str, object]] = []
    validation_result = run_command(
        "validate_real_product_batch.py",
        [sys.executable, "scripts/validate_real_product_batch.py"],
    )
    command_results.append(validation_result)
    issues.extend(validation_issues(validation_result, total_rows, args.max_warning_rate))

    for path, retailer, category, _row_count in category_files:
        result = run_command(
            "import_category_batch.py --dry-run {0}".format(path.relative_to(BACKEND_DIR)),
            [
                sys.executable,
                "scripts/import_category_batch.py",
                "--csv",
                str(path.relative_to(BACKEND_DIR)),
                "--retailer",
                retailer,
                "--category",
                category,
                "--dry-run",
            ],
        )
        command_results.append(result)
        issues.extend(dry_run_issue(result, path))

    for label, command in [
        ("product_volume_tracker.py", [sys.executable, "scripts/product_volume_tracker.py"]),
        ("bulk_import_quality_report.py", [sys.executable, "scripts/bulk_import_quality_report.py"]),
        ("supermarket_coverage_report.py", [sys.executable, "scripts/supermarket_coverage_report.py"]),
        ("validate_backend.py", [sys.executable, "validate_backend.py"]),
    ]:
        result = run_command(label, command)
        command_results.append(result)
        issues.extend(report_issues(result))

    safe_to_import = not issues
    print("\nCONTROLLED SCALING DECISION")
    print("=" * 80)
    print("safe to import: {0}".format("yes" if safe_to_import else "no"))
    print("issues list:")
    if issues:
        for issue in issues:
            print("- {0}".format(issue))
    else:
        print("- none")
    return 0 if safe_to_import else 1


if __name__ == "__main__":
    raise SystemExit(main())
