from database import DB_PATH, init_db, seed_products_from_json
from import_tesco import import_tesco
from import_asda import import_asda
from import_sainsburys import import_sainsburys
from import_quality_report import print_quality_report
from coverage_summary_report import print_coverage_summary_report
from services.phase2_data_quality import ensure_phase2_tables, refresh_existing_quality_records
from services.phase2_reporting import build_phase2_summary, render_phase2_text_report


def run_imports(include_reports=False):
    init_db()
    ensure_phase2_tables(str(DB_PATH))
    seeded_products = seed_products_from_json()

    results = [
        import_tesco(),
        import_asda(),
        import_sainsburys(),
    ]

    refresh_existing_quality_records(str(DB_PATH))

    if include_reports:
        print(f"Seed products checked: {seeded_products}\n")

        for result in results:
            print_result(result)
            print()

        print_quality_report(limit=20)
        print()
        print_coverage_summary_report()
        print()

        print("Phase 2 data quality")
        print(render_phase2_text_report(build_phase2_summary(str(DB_PATH))))

    return {
        "seeded_products": seeded_products,
        "results": results,
    }


def print_result(result):
    retailer = result.get("retailer", "Unknown")
    errors = result.get("errors", [])

    print(f"✅ {retailer} import complete")
    print(f"   File used:         {result.get('file_used', 'unknown')}")
    print(f"   Products upserted: {result.get('products_upserted', 0)}")
    print(f"   Offers upserted:   {result.get('offers_upserted', 0)}")
    print(f"   Rows skipped:      {result.get('rows_skipped', 0)}")

    if errors:
        print(f"   Errors:            {len(errors)}")
        for err in errors[:5]:
            print(f"   - {err}")


def main():
    print("🚀 Running supermarket imports...\n")

    run_imports(include_reports=True)

    print("✅ Import run finished")


if __name__ == "__main__":
    main()
