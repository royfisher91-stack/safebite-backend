from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class IngredientAnalysisItemSchema(BaseModel):
    ingredient: str
    normalized: str
    category: str
    risk_level: str
    reason: str
    flags: List[str] = []


class ConditionTriggerSchema(BaseModel):
    ingredient: Optional[str] = None
    normalized: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    match_type: Optional[str] = None
    matched_value: Optional[str] = None
    impact: Optional[str] = None
    reason: str
    flags: List[str] = []


class ConditionResultSchema(BaseModel):
    condition: str
    display_name: str
    kind: str
    result: str
    summary: str
    explanation: str = ''
    triggers: List[ConditionTriggerSchema] = []
    flags: List[str] = []
    suggestions: List[str] = []


class ProfileWriteSchema(BaseModel):
    name: str
    allergies: List[str] = []
    conditions: List[str] = []
    is_default: bool = False
    notes: Optional[str] = None


class ProfileSchema(ProfileWriteSchema):
    id: int
    user_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FavouriteWriteSchema(BaseModel):
    barcode: str
    product_name: str
    profile_id: Optional[int] = None


class FavouriteSchema(FavouriteWriteSchema):
    id: int
    user_id: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    image_source_type: Optional[str] = None
    image_rights_status: Optional[str] = None
    image_credit: Optional[str] = None
    image_last_verified_at: Optional[str] = None
    created_at: Optional[str] = None


class HistoryWriteSchema(BaseModel):
    barcode: str
    product_name: str
    profile_id: Optional[int] = None
    profile_name: Optional[str] = None
    allergies: List[str] = []
    conditions: List[str] = []
    safety_result: Optional[str] = None
    safety_score: Optional[int] = None
    condition_results: Dict[str, Any] = {}


class HistorySchema(HistoryWriteSchema):
    id: int
    user_id: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    image_url: Optional[str] = None
    image_source_type: Optional[str] = None
    image_rights_status: Optional[str] = None
    image_credit: Optional[str] = None
    image_last_verified_at: Optional[str] = None
    scanned_at: Optional[str] = None


class CommunityFeedbackWriteSchema(BaseModel):
    barcode: str
    product_name: str
    feedback_type: str
    comment: str
    allergy_tags: List[str] = []
    condition_tags: List[str] = []


class CommunityFeedbackFlagSchema(BaseModel):
    reason: Optional[str] = None


class CommunityFeedbackItemSchema(BaseModel):
    id: int
    barcode: str
    product_name: str
    feedback_type: str
    comment: str
    allergy_tags: List[str] = []
    condition_tags: List[str] = []
    is_visible: bool = True
    is_flagged: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CommunityFeedbackSummarySchema(BaseModel):
    barcode: str
    opinion_label: str
    disclaimer: str
    visible_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    allergy_tag_counts: Dict[str, int] = {}
    condition_tag_counts: Dict[str, int] = {}
    latest_feedback_at: Optional[str] = None


class PromoCodeWriteSchema(BaseModel):
    code: str
    code_type: str
    discount_type: str
    discount_value: Optional[float] = None
    is_active: bool = True
    usage_limit: Optional[int] = None
    expires_at: Optional[str] = None
    plan_scope: str = 'all'
    campaign_label: Optional[str] = None
    notes: Optional[str] = None


class PromoCodeUpdateSchema(BaseModel):
    is_active: Optional[bool] = None
    usage_limit: Optional[int] = None
    expires_at: Optional[str] = None
    plan_scope: Optional[str] = None
    campaign_label: Optional[str] = None
    notes: Optional[str] = None


class PromoCodeSchema(PromoCodeWriteSchema):
    id: int
    usage_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromoCodeValidationSchema(BaseModel):
    code: str
    plan: Optional[str] = None


class PromoCodePreviewSchema(BaseModel):
    code: str
    code_type: str
    discount_type: str
    discount_value: Optional[float] = None
    plan: str
    plan_scope: str = 'all'
    campaign_label: str = ''
    base_price: Optional[float] = None
    final_price: Optional[float] = None
    discount_amount: Optional[float] = None
    savings_percent: Optional[float] = None
    trial_extension_days: Optional[int] = None
    access_granted: bool = False
    expires_at: Optional[str] = None
    usage_limit: Optional[int] = None
    usage_count: int = 0
    notes: str = ''
    pricing_separation_notice: str


class PromoCodeValidationResultSchema(BaseModel):
    valid: bool
    reason: Optional[str] = None
    promo_code: Optional[PromoCodeSchema] = None
    preview: Optional[PromoCodePreviewSchema] = None
    pricing_separation_notice: str


class PromoCodeApplyResultSchema(BaseModel):
    applied: bool
    reason: Optional[str] = None
    promo_code: Optional[PromoCodeSchema] = None
    preview: Optional[PromoCodePreviewSchema] = None
    pricing_separation_notice: str


class AuthRegisterSchema(BaseModel):
    email: str
    password: str


class AuthLoginSchema(BaseModel):
    email: str
    password: str


class UserSchema(BaseModel):
    id: int
    email: str
    is_active: bool = True
    subscription_status: str = "inactive"
    subscription_plan: str = "free"
    free_scans_used: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AuthTokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: UserSchema


class SubscriptionActivationSchema(BaseModel):
    plan_code: str = "paid_monthly"
    provider: Optional[str] = None
    platform: Optional[str] = None
    product_id: Optional[str] = None
    purchase_token: Optional[str] = None
    transaction_id: Optional[str] = None


class BillingVerificationSchema(BaseModel):
    provider: str
    product_id: str
    platform: Optional[str] = None
    purchase_token: Optional[str] = None
    transaction_id: Optional[str] = None


class SubscriptionPromoApplySchema(BaseModel):
    code: str


class AnalysisSchema(BaseModel):
    safety_result: str
    safety_score: Optional[int] = None
    ingredient_reasoning: Any = ''
    allergen_warnings: List[str] = []
    personal_warnings: List[str] = []
    unknown_flags: List[str] = []
    ingredient_analysis: Dict[str, Any] = {}
    processing_analysis: Dict[str, Any] = {}
    sugar_analysis: Dict[str, Any] = {}
    component_scores: Dict[str, Any] = {}
    confidence: Dict[str, Any] = {}
    requested_allergies: List[str] = []
    requested_conditions: List[str] = []
    condition_results: Dict[str, ConditionResultSchema] = {}


class PricingSchema(BaseModel):
    best_price: Optional[float] = None
    lowest_price: Optional[float] = None
    lowest_in_stock_price: Optional[float] = None
    best_value_price: Optional[float] = None
    lowest_standard_price: Optional[float] = None
    lowest_promo_price: Optional[float] = None
    cheapest_retailer: Optional[str] = None
    cheapest_overall_retailer: Optional[str] = None
    cheapest_in_stock_retailer: Optional[str] = None
    best_value_retailer: Optional[str] = None
    stock_status: str = 'unknown'
    product_url: Optional[str] = None
    offer_count: int = 0
    valid_offer_count: int = 0
    in_stock_offer_count: int = 0
    out_of_stock_offer_count: int = 0
    promo_offer_count: int = 0
    multi_buy_offer_count: int = 0
    best_offer: Optional[Dict[str, Any]] = None
    best_in_stock_offer: Optional[Dict[str, Any]] = None
    best_value_offer: Optional[Dict[str, Any]] = None
    pricing_summary: Optional[str] = None
    unknown_flags: List[str] = []


class OfferSchema(BaseModel):
    id: Optional[int] = None
    barcode: str
    retailer: str
    offer_title: Optional[str] = None
    price: Optional[float] = None
    promo_price: Optional[float] = None
    effective_price: Optional[float] = None
    standard_unit_price: Optional[float] = None
    promo_unit_price: Optional[float] = None
    multi_buy_effective_price: Optional[float] = None
    best_unit_price: Optional[float] = None
    promotion_type: Optional[str] = None
    promotion_label: Optional[str] = None
    buy_quantity: Optional[int] = None
    pay_quantity: Optional[int] = None
    bundle_price: Optional[float] = None
    better_value_when_buying: bool = False
    promotion_summary: Optional[str] = None
    currency: str = '£'
    in_stock: bool = False
    stock_status: str = 'unknown'
    product_url: Optional[str] = None
    image_url: Optional[str] = None
    image_source_type: Optional[str] = None
    image_rights_status: Optional[str] = None
    image_credit: Optional[str] = None
    image_last_verified_at: Optional[str] = None
    unit_price: Optional[float] = None
    unit_name: Optional[str] = None
    size_text: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    source_product_id: Optional[str] = None
    is_promo: bool = False
    available_for_delivery: bool = False
    available_for_collection: bool = False
    last_updated: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AlternativeProductSchema(BaseModel):
    product_id: Optional[str] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    safety_score: Optional[int] = None
    safety_result: Optional[str] = None
    ingredient_reasoning: Optional[str] = None
    allergen_warnings: List[str] = []
    best_price: Optional[float] = None
    lowest_in_stock_price: Optional[float] = None
    cheapest_retailer: Optional[str] = None
    stock_status: Optional[str] = None
    product_url: Optional[str] = None
    reason: Optional[str] = None
    confidence: Dict[str, Any] = {}


class AlternativesSchema(BaseModel):
    safer_option: Optional[AlternativeProductSchema] = None
    cheaper_option: Optional[AlternativeProductSchema] = None
    same_category_option: Optional[AlternativeProductSchema] = None


class ProductBaseSchema(BaseModel):
    product_id: Optional[str] = None
    barcode: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    ingredients: List[Any] = []
    allergens: List[Any] = []
    markets: List[Any] = []
    age_suitability: Optional[str] = None
    description: Optional[str] = None
    nutrition: Dict[str, Any] = {}
    image_url: Optional[str] = None
    image_source_type: Optional[str] = None
    image_rights_status: Optional[str] = None
    image_credit: Optional[str] = None
    image_last_verified_at: Optional[str] = None
    image_source_label: Optional[str] = None
    image_blocked_reason: Optional[str] = None
    tags: List[Any] = []
    safety_score: Optional[int] = None
    safety_result: str = 'Unknown'
    ingredient_reasoning: Any = ''
    allergen_warnings: List[str] = []
    personal_warnings: List[str] = []
    requested_allergies: List[str] = []
    requested_conditions: List[str] = []
    matched_allergens: List[str] = []
    allergen_safe_for_request: Optional[bool] = None
    condition_results: Dict[str, ConditionResultSchema] = {}
    analysis: Optional[AnalysisSchema] = None
    pricing: Optional[PricingSchema] = None


class ProductListItemSchema(ProductBaseSchema):
    pass


class ProductDetailSchema(ProductBaseSchema):
    offers: List[OfferSchema] = []
    alternatives: Optional[AlternativesSchema] = None
