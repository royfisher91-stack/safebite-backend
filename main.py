from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class SafetyLevel(str, Enum):
    SAFE = "safe"
    WATCH = "watch"
    AVOID = "avoid"
    UNKNOWN = "unknown"


class ResultLabel(str, Enum):
    SAFE = "Safe"
    MOSTLY_SAFE = "Mostly Safe"
    USE_CAUTION = "Use Caution"
    AVOID = "Avoid"


@dataclass(frozen=True)
class IngredientInfo:
    canonical_name: str
    aliases: tuple[str, ...] = ()
    description: str = ""
    default_level: SafetyLevel = SafetyLevel.UNKNOWN
    allergens: tuple[str, ...] = ()


@dataclass
class IngredientFinding:
    input_name: str
    matched_name: str | None
    level: SafetyLevel
    description: str
    matched_allergens: list[str] = field(default_factory=list)
    score_delta: int = 0


@dataclass
class CheckResult:
    score: int
    label: ResultLabel
    findings: list[IngredientFinding]
    matched_allergens: list[str]
    summary: list[str]


@dataclass
class NutritionInfo:
    serving_size: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    sugar_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None


@dataclass
class ProductAnalysis:
    score: int | None = None
    label: str | None = None
    safe_ingredients: list[str] = field(default_factory=list)
    watch_ingredients: list[str] = field(default_factory=list)
    avoid_ingredients: list[str] = field(default_factory=list)
    unknown_ingredients: list[str] = field(default_factory=list)
    matched_allergens: list[str] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)


@dataclass
class RetailOffer:
    retailer: str
    market: str
    price: float
    currency: str
    in_stock: bool
    product_url: str | None = None
    last_updated: str | None = None


@dataclass
class Product:
    product_id: str
    name: str
    brand: str
    category: str
    ingredients: list[str] = field(default_factory=list)
    allergens: list[str] = field(default_factory=list)
    markets: list[str] = field(default_factory=list)
    age_suitability: str | None = None
    description: str | None = None
    nutrition: NutritionInfo = field(default_factory=NutritionInfo)
    analysis: ProductAnalysis = field(default_factory=ProductAnalysis)
    offers: list[RetailOffer] = field(default_factory=list)


INGREDIENTS = [
    IngredientInfo(
        canonical_name="water",
        aliases=("aqua",),
        description="Base solvent used in many products.",
        default_level=SafetyLevel.SAFE,
    ),
    IngredientInfo(
        canonical_name="glycerin",
        aliases=("glycerol",),
        description="Helps hold moisture.",
        default_level=SafetyLevel.SAFE,
    ),
    IngredientInfo(
        canonical_name="fragrance",
        aliases=("parfum",),
        description="May irritate sensitive users.",
        default_level=SafetyLevel.WATCH,
    ),
    IngredientInfo(
        canonical_name="peanut oil",
        aliases=("arachis oil",),
        description="Oil derived from peanuts.",
        default_level=SafetyLevel.AVOID,
        allergens=("peanut",),
    ),
    IngredientInfo(
        canonical_name="milk protein",
        aliases=("casein", "whey protein"),
        description="Protein derived from milk.",
        default_level=SafetyLevel.WATCH,
        allergens=("milk", "dairy"),
    ),
]

PRODUCTS = [
    Product(
        product_id="prd_001",
        name="Organic Peanut Butter Bites",
        brand="NutriJoy",
        category="snacks",
        ingredients=["Arachis Oil", "Oats", "Honey", "Casein"],
        allergens=["peanut", "milk"],
        markets=["uk", "us"],
        age_suitability="3+",
        description="Soft snack bites made with oats and peanut ingredients.",
        nutrition=NutritionInfo(
            serving_size="40g",
            calories=180,
            protein_g=6,
            carbs_g=14,
            fat_g=11,
            sugar_g=7,
            fiber_g=2,
            sodium_mg=85,
        ),
        offers=[
            RetailOffer(
                retailer="Tesco",
                market="uk",
                price=3.99,
                currency="GBP",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
            RetailOffer(
                retailer="Walmart",
                market="us",
                price=4.49,
                currency="USD",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
        ],
    ),
    Product(
        product_id="prd_002",
        name="Gentle Daily Lotion UK",
        brand="PureSkin",
        category="skincare",
        ingredients=["Water", "Glycerin", "Parfum"],
        allergens=[],
        markets=["uk"],
        age_suitability="12+",
        description="UK version of the daily lotion.",
        offers=[
            RetailOffer(
                retailer="Boots",
                market="uk",
                price=5.99,
                currency="GBP",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
            RetailOffer(
                retailer="Superdrug",
                market="uk",
                price=5.49,
                currency="GBP",
                in_stock=False,
                last_updated="2026-04-08T10:00:00Z",
            ),
        ],
    ),
    Product(
        product_id="prd_003",
        name="Simple Hydration Cream UK",
        brand="PureSkin",
        category="skincare",
        ingredients=["Water", "Glycerin"],
        allergens=[],
        markets=["uk"],
        age_suitability="12+",
        description="Simple cream with fewer ingredients for the UK market.",
        offers=[
            RetailOffer(
                retailer="Boots",
                market="uk",
                price=4.99,
                currency="GBP",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
            RetailOffer(
                retailer="Amazon UK",
                market="uk",
                price=5.19,
                currency="GBP",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
        ],
    ),
    Product(
        product_id="prd_004",
        name="Gentle Daily Lotion US",
        brand="PureSkin",
        category="skincare",
        ingredients=["Water", "Glycerin", "Fragrance"],
        allergens=[],
        markets=["us"],
        age_suitability="12+",
        description="US version of the daily lotion.",
        offers=[
            RetailOffer(
                retailer="Target",
                market="us",
                price=6.49,
                currency="USD",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
            RetailOffer(
                retailer="Walmart",
                market="us",
                price=6.29,
                currency="USD",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
        ],
    ),
    Product(
        product_id="prd_005",
        name="Simple Hydration Cream US",
        brand="PureSkin",
        category="skincare",
        ingredients=["Water", "Glycerin"],
        allergens=[],
        markets=["us"],
        age_suitability="12+",
        description="Simple cream for the US market.",
        offers=[
            RetailOffer(
                retailer="Target",
                market="us",
                price=5.29,
                currency="USD",
                in_stock=True,
                last_updated="2026-04-08T10:00:00Z",
            ),
            RetailOffer(
                retailer="Walmart",
                market="us",
                price=4.99,
                currency="USD",
                in_stock=False,
                last_updated="2026-04-08T10:00:00Z",
            ),
        ],
    ),
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def normalize_market(market: str) -> str:
    return normalize_text(market)


def find_ingredient(name: str) -> IngredientInfo | None:
    normalized_name = normalize_text(name)

    for ingredient in INGREDIENTS:
        if normalize_text(ingredient.canonical_name) == normalized_name:
            return ingredient

        for alias in ingredient.aliases:
            if normalize_text(alias) == normalized_name:
                return ingredient

    return None


def score_for_level(level: SafetyLevel) -> int:
    if level == SafetyLevel.SAFE:
        return 0
    if level == SafetyLevel.WATCH:
        return -15
    if level == SafetyLevel.AVOID:
        return -40
    return -8


def label_from_score(
    score: int,
    findings: list[IngredientFinding],
    matched_allergens: list[str],
) -> ResultLabel:
    if matched_allergens:
        return ResultLabel.AVOID
    if any(f.level == SafetyLevel.AVOID for f in findings):
        return ResultLabel.AVOID
    if score >= 85:
        return ResultLabel.SAFE
    if score >= 70:
        return ResultLabel.MOSTLY_SAFE
    if score >= 50:
        return ResultLabel.USE_CAUTION
    return ResultLabel.AVOID


def build_summary(
    score: int,
    label: ResultLabel,
    findings: list[IngredientFinding],
    matched_allergens: list[str],
) -> list[str]:
    summary = [
        f"Final label: {label.value}",
        f"Score: {score}/100",
    ]

    avoid_count = sum(1 for f in findings if f.level == SafetyLevel.AVOID)
    watch_count = sum(1 for f in findings if f.level == SafetyLevel.WATCH)
    unknown_count = sum(1 for f in findings if f.level == SafetyLevel.UNKNOWN)

    if avoid_count:
        summary.append(f"{avoid_count} avoid ingredient(s) detected")
    if watch_count:
        summary.append(f"{watch_count} watch ingredient(s) detected")
    if unknown_count:
        summary.append(f"{unknown_count} unknown ingredient(s) detected")
    if matched_allergens:
        summary.append("Allergen match: " + ", ".join(matched_allergens))

    return summary


def check_ingredients(
    input_ingredients: list[str],
    user_allergens: list[str] | None = None,
) -> CheckResult:
    score = 100
    findings = []
    matched_allergens = set()

    normalized_user_allergens = {
        normalize_text(allergen) for allergen in (user_allergens or [])
    }

    for item in input_ingredients:
        match = find_ingredient(item)

        if match is None:
            level = SafetyLevel.UNKNOWN
            delta = score_for_level(level)

            findings.append(
                IngredientFinding(
                    input_name=item,
                    matched_name=None,
                    level=level,
                    description="Ingredient not found in database.",
                    score_delta=delta,
                )
            )
            score += delta
            continue

        delta = score_for_level(match.default_level)
        found_allergens = []

        for allergen in match.allergens:
            if normalize_text(allergen) in normalized_user_allergens:
                found_allergens.append(allergen)
                matched_allergens.add(allergen)
                delta -= 50

        findings.append(
            IngredientFinding(
                input_name=item,
                matched_name=match.canonical_name,
                level=match.default_level,
                description=match.description,
                matched_allergens=found_allergens,
                score_delta=delta,
            )
        )

        score += delta

    score = max(0, min(100, score))
    final_matched_allergens = sorted(matched_allergens)
    label = label_from_score(score, findings, final_matched_allergens)
    summary = build_summary(score, label, findings, final_matched_allergens)

    return CheckResult(
        score=score,
        label=label,
        findings=findings,
        matched_allergens=final_matched_allergens,
        summary=summary,
    )


def apply_analysis_to_product(product: Product, result: CheckResult) -> Product:
    product.analysis.score = result.score
    product.analysis.label = result.label.value
    product.analysis.matched_allergens = result.matched_allergens
    product.analysis.summary = result.summary

    product.analysis.safe_ingredients = []
    product.analysis.watch_ingredients = []
    product.analysis.avoid_ingredients = []
    product.analysis.unknown_ingredients = []

    for finding in result.findings:
        ingredient_name = finding.matched_name or finding.input_name

        if finding.level == SafetyLevel.SAFE:
            product.analysis.safe_ingredients.append(ingredient_name)
        elif finding.level == SafetyLevel.WATCH:
            product.analysis.watch_ingredients.append(ingredient_name)
        elif finding.level == SafetyLevel.AVOID:
            product.analysis.avoid_ingredients.append(ingredient_name)
        else:
            product.analysis.unknown_ingredients.append(ingredient_name)

    return product


def check_product(product: Product, user_allergens: list[str] | None = None) -> Product:
    result = check_ingredients(product.ingredients, user_allergens=user_allergens)
    return apply_analysis_to_product(product, result)


class ProductRepository:
    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.product_id] = product

    def list_all(self, market: str | None = None) -> list[Product]:
        products = list(self._products.values())

        if market is None:
            return products

        wanted_market = normalize_market(market)

        return [
            product
            for product in products
            if wanted_market in {normalize_market(m) for m in product.markets}
        ]

    def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def get_by_name(self, name: str, market: str | None = None) -> Product | None:
        wanted_name = normalize_text(name)
        allowed_products = self.list_all(market=market)

        for product in allowed_products:
            if normalize_text(product.name) == wanted_name:
                return product

        return None


def get_market_offers(product: Product, market: str | None = None) -> list[RetailOffer]:
    if market is None:
        return sorted(product.offers, key=lambda o: o.price)

    wanted_market = normalize_market(market)
    return sorted(
        [
            offer
            for offer in product.offers
            if normalize_market(offer.market) == wanted_market
        ],
        key=lambda o: o.price,
    )


def get_best_offer(product: Product, market: str | None = None) -> RetailOffer | None:
    offers = [offer for offer in get_market_offers(product, market=market) if offer.in_stock]
    return offers[0] if offers else None


def compare_products(product_a: Product, product_b: Product) -> dict:
    set_a = {normalize_text(i) for i in product_a.ingredients}
    set_b = {normalize_text(i) for i in product_b.ingredients}

    return {
        "product_a": product_a.name,
        "product_b": product_b.name,
        "score_a": product_a.analysis.score,
        "score_b": product_b.analysis.score,
        "label_a": product_a.analysis.label,
        "label_b": product_b.analysis.label,
        "common_ingredients": sorted(set_a & set_b),
        "only_in_a": sorted(set_a - set_b),
        "only_in_b": sorted(set_b - set_a),
        "allergens_a": product_a.allergens,
        "allergens_b": product_b.allergens,
    }


def get_safer_alternatives(
    current_product: Product,
    all_products: list[Product],
    user_allergens: list[str],
    market: str | None = None,
    limit: int = 5,
) -> list[Product]:
    user_allergen_set = {normalize_text(a) for a in user_allergens}
    current_score = current_product.analysis.score or 0
    wanted_market = normalize_market(market) if market else None

    candidates = []

    for product in all_products:
        if product.product_id == current_product.product_id:
            continue

        if normalize_text(product.category) != normalize_text(current_product.category):
            continue

        if wanted_market is not None:
            product_markets = {normalize_market(m) for m in product.markets}
            if wanted_market not in product_markets:
                continue

        product_allergens = {normalize_text(a) for a in product.allergens}
        if product_allergens & user_allergen_set:
            continue

        candidate_score = product.analysis.score or 0
        if candidate_score <= current_score:
            continue

        candidates.append(product)

    candidates.sort(
        key=lambda p: (
            -(p.analysis.score or 0),
            len(p.analysis.avoid_ingredients),
            len(p.analysis.watch_ingredients),
            p.name,
        )
    )

    return candidates[:limit]


repo = ProductRepository()
for product in PRODUCTS:
    repo.add(product)

for product in repo.list_all():
    check_product(product, user_allergens=["milk"])


class CheckIngredientsRequest(BaseModel):
    ingredients: list[str]
    user_allergens: list[str] = []


class IngredientFindingResponse(BaseModel):
    input_name: str
    matched_name: Optional[str]
    level: str
    description: str
    matched_allergens: list[str]
    score_delta: int


class CheckIngredientsResponse(BaseModel):
    score: int
    label: str
    findings: list[IngredientFindingResponse]
    matched_allergens: list[str]
    summary: list[str]


class RetailOfferResponse(BaseModel):
    retailer: str
    market: str
    price: float
    currency: str
    in_stock: bool
    product_url: Optional[str] = None
    last_updated: Optional[str] = None


class ProductAnalysisResponse(BaseModel):
    score: Optional[int] = None
    label: Optional[str] = None
    safe_ingredients: list[str] = []
    watch_ingredients: list[str] = []
    avoid_ingredients: list[str] = []
    unknown_ingredients: list[str] = []
    matched_allergens: list[str] = []
    summary: list[str] = []


class ProductResponse(BaseModel):
    product_id: str
    name: str
    brand: str
    category: str
    ingredients: list[str]
    allergens: list[str]
    markets: list[str]
    age_suitability: Optional[str] = None
    description: Optional[str] = None
    analysis: ProductAnalysisResponse
    offers: list[RetailOfferResponse]
    best_offer: Optional[RetailOfferResponse] = None


class ProductCompareResponse(BaseModel):
    product_a: str
    product_b: str
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    label_a: Optional[str] = None
    label_b: Optional[str] = None
    common_ingredients: list[str]
    only_in_a: list[str]
    only_in_b: list[str]
    allergens_a: list[str]
    allergens_b: list[str]


def map_offer(offer: RetailOffer) -> RetailOfferResponse:
    return RetailOfferResponse(
        retailer=offer.retailer,
        market=offer.market,
        price=offer.price,
        currency=offer.currency,
        in_stock=offer.in_stock,
        product_url=offer.product_url,
        last_updated=offer.last_updated,
    )


def map_product(product: Product, market: str | None = None) -> ProductResponse:
    offers = get_market_offers(product, market=market)
    best_offer = get_best_offer(product, market=market)

    return ProductResponse(
        product_id=product.product_id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        ingredients=product.ingredients,
        allergens=product.allergens,
        markets=product.markets,
        age_suitability=product.age_suitability,
        description=product.description,
        analysis=ProductAnalysisResponse(
            score=product.analysis.score,
            label=product.analysis.label,
            safe_ingredients=product.analysis.safe_ingredients,
            watch_ingredients=product.analysis.watch_ingredients,
            avoid_ingredients=product.analysis.avoid_ingredients,
            unknown_ingredients=product.analysis.unknown_ingredients,
            matched_allergens=product.analysis.matched_allergens,
            summary=product.analysis.summary,
        ),
        offers=[map_offer(offer) for offer in offers],
        best_offer=map_offer(best_offer) if best_offer else None,
    )


app = FastAPI(title="Product Safety API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Product Safety API is running"}


@app.post("/check-ingredients", response_model=CheckIngredientsResponse)
def api_check_ingredients(payload: CheckIngredientsRequest):
    result = check_ingredients(payload.ingredients, payload.user_allergens)

    return CheckIngredientsResponse(
        score=result.score,
        label=result.label.value,
        findings=[
            IngredientFindingResponse(
                input_name=f.input_name,
                matched_name=f.matched_name,
                level=f.level.value,
                description=f.description,
                matched_allergens=f.matched_allergens,
                score_delta=f.score_delta,
            )
            for f in result.findings
        ],
        matched_allergens=result.matched_allergens,
        summary=result.summary,
    )


@app.get("/products", response_model=list[ProductResponse])
def api_list_products(
    market: str | None = Query(default=None),
):
    return [map_product(product, market=market) for product in repo.list_all(market=market)]


@app.get("/products/{name}", response_model=ProductResponse)
def api_get_product(
    name: str,
    market: str | None = Query(default=None),
):
    product = repo.get_by_name(name, market=market)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return map_product(product, market=market)


@app.get("/compare", response_model=ProductCompareResponse)
def api_compare_products(
    product_a: str,
    product_b: str,
    market: str | None = Query(default=None),
):
    a = repo.get_by_name(product_a, market=market)
    b = repo.get_by_name(product_b, market=market)

    if not a:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_a}")
    if not b:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_b}")

    return ProductCompareResponse(**compare_products(a, b))


@app.get("/alternatives/{name}", response_model=list[ProductResponse])
def api_alternatives(
    name: str,
    market: str | None = Query(default=None),
    user_allergens: list[str] = Query(default=[]),
):
    product = repo.get_by_name(name, market=market)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    alternatives = get_safer_alternatives(
        current_product=product,
        all_products=repo.list_all(market=market),
        user_allergens=user_allergens,
        market=market,
        limit=5,
    )

    return [map_product(item, market=market) for item in alternatives]