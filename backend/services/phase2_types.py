from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProductImportRow:
    barcode: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    nutrition_json: Optional[Dict[str, Any]] = None
    processing_notes: Optional[str] = None
    price: Optional[float] = None
    promo_price: Optional[float] = None
    retailer: Optional[str] = None
    stock_status: Optional[str] = None
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    source_retailer: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationIssue:
    code: str
    severity: str
    message: str
    field_name: Optional[str] = None


@dataclass
class ValidationResult:
    accepted: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_flags: List[str] = field(default_factory=list)

    def add_issue(self, code: str, severity: str, message: str, field_name: Optional[str] = None) -> None:
        self.issues.append(
            ValidationIssue(
                code=code,
                severity=severity,
                message=message,
                field_name=field_name,
            )
        )

    def add_flag(self, flag_name: str) -> None:
        if flag_name not in self.quality_flags:
            self.quality_flags.append(flag_name)
