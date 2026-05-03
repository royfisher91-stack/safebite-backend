#!/usr/bin/env python3
"""Validate that catalogue volume is reproducible from committed files."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
EXPECTED_PRODUCTS = 97
EXPECTED_OFFERS = 104
EXPECTED_OFF_CATALOGUE_PRODUCTS = 33
EXPECTED_OFF_CATALOGUE_WITHOUT_OFFERS = 33
DRIFT_MESSAGE = "Catalogue volume drift detected: expected 97 products / 104 offers from committed import files."


class GateError(RuntimeError):
    pass


def run_command(label: str, command: Sequence[str], cwd: Path) -> str:
    print("\nRunning {0}".format(label))
    print("$ {0}".format(" ".join(command)))
    completed = subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = completed.stdout or ""
    if completed.returncode != 0:
        if output.strip():
            print(output.rstrip())
        raise GateError("{0} failed with exit code {1}".format(label, completed.returncode))
    print("{0}: PASS".format(label))
    return output


def count_state(backend_dir: Path) -> Dict[str, int]:
    db_path = backend_dir / "safebite.db"
    if not db_path.exists():
        return {
            "products": 0,
            "offers": 0,
            "off_catalogue_products": 0,
            "off_catalogue_without_offers": 0,
        }

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        products = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM offers")
        offers = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM products WHERE source = 'open_food_facts_catalogue'")
        off_catalogue_products = int(cur.fetchone()[0] or 0)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM products p
            WHERE p.source = 'open_food_facts_catalogue'
              AND NOT EXISTS (
                SELECT 1
                FROM offers o
                WHERE o.barcode = p.barcode
              )
            """
        )
        off_catalogue_without_offers = int(cur.fetchone()[0] or 0)
        return {
            "products": products,
            "offers": offers,
            "off_catalogue_products": off_catalogue_products,
            "off_catalogue_without_offers": off_catalogue_without_offers,
        }
    finally:
        conn.close()


def assert_counts(stage: str, state: Dict[str, int]) -> None:
    expected = {
        "products": EXPECTED_PRODUCTS,
        "offers": EXPECTED_OFFERS,
        "off_catalogue_products": EXPECTED_OFF_CATALOGUE_PRODUCTS,
        "off_catalogue_without_offers": EXPECTED_OFF_CATALOGUE_WITHOUT_OFFERS,
    }
    failures: List[str] = []
    for key, expected_value in expected.items():
        actual = state.get(key)
        if actual != expected_value:
            failures.append("{0}: expected {1}, got {2}".format(key, expected_value, actual))
    if failures:
        raise GateError("{0} {1} {2}".format(DRIFT_MESSAGE, stage, "; ".join(failures)))


def print_state(label: str, state: Dict[str, int]) -> None:
    print("\n{0}".format(label))
    print("- products: {0}".format(state["products"]))
    print("- offers: {0}".format(state["offers"]))
    print("- OFF catalogue products: {0}".format(state["off_catalogue_products"]))
    print("- OFF catalogue products without retailer offers: {0}".format(state["off_catalogue_without_offers"]))


def archive_head(destination: Path) -> None:
    archive_path = destination / "head.tar"
    with archive_path.open("wb") as handle:
        completed = subprocess.run(
            ["git", "archive", "HEAD"],
            cwd=str(PROJECT_ROOT),
            stdout=handle,
            stderr=subprocess.PIPE,
        )
    if completed.returncode != 0:
        error = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else "unknown error"
        raise GateError("git archive HEAD failed: {0}".format(error.strip()))

    extract_dir = destination / "checkout"
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(str(archive_path), "r") as archive:
        archive.extractall(str(extract_dir))


def main() -> int:
    print("CATALOGUE VOLUME REPRODUCIBILITY GATE")
    print("=" * 80)
    with tempfile.TemporaryDirectory(prefix="safebite_catalogue_repro_") as tmpdir:
        tmp_path = Path(tmpdir)
        archive_head(tmp_path)
        backend_dir = tmp_path / "checkout" / "backend"
        if not backend_dir.exists():
            raise GateError("Archived checkout does not contain backend directory")

        before = count_state(backend_dir)
        print_state("Fresh database state before import", before)
        if before["products"] != 0 or before["offers"] != 0:
            raise GateError("Fresh rebuild must start with 0 products and 0 offers")

        run_command("run_imports.py", [sys.executable, "run_imports.py"], backend_dir)
        after_import = count_state(backend_dir)
        print_state("State after run_imports.py", after_import)
        assert_counts("after run_imports.py", after_import)

        run_command("validate_backend.py", [sys.executable, "validate_backend.py"], backend_dir)
        after_validation = count_state(backend_dir)
        print_state("State after validate_backend.py", after_validation)
        assert_counts("after validate_backend.py", after_validation)

    print("\nCatalogue reproducibility validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
