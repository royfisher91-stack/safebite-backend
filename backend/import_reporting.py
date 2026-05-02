from dataclasses import dataclass


@dataclass
class ImportReport:
    retailer: str
    rows_read: int = 0
    products_created: int = 0
    offers_upserted: int = 0
    rows_skipped: int = 0
    errors_found: int = 0

    def print_summary(self) -> None:
        print(f"\n--- {self.retailer} import summary ---")
        print(f"rows read: {self.rows_read}")
        print(f"products created: {self.products_created}")
        print(f"offers upserted: {self.offers_upserted}")
        print(f"rows skipped: {self.rows_skipped}")
        print(f"errors found: {self.errors_found}")