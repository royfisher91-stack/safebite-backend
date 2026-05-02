from typing import Any, Dict


def normalise_home_source_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": row.get("source"),
        "source_retailer": row.get("source_retailer"),
        "barcode": row.get("barcode"),
        "name": row.get("name"),
        "brand": row.get("brand"),
        "hazard_data": row.get("hazard_data") or row.get("chemical_hazards"),
        "unknown_flags": ["safehome_source_not_verified_flag"],
    }
