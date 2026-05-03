export type SafetyResult = 'Safe' | 'Caution' | 'Avoid' | string;

export type User = {
  id: number;
  email: string;
  is_active: boolean;
  subscription_status: string;
  subscription_plan: string;
  free_scans_used: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer' | string;
  expires_at: string;
  user: User;
};

export type Entitlement = {
  user_id: number;
  plan: string;
  subscription_status: string;
  access_active: boolean;
  add_on_entitlements?: string[];
  safehome_addon_active?: boolean;
  free_scan_limit: number;
  free_scans_used: number;
  free_scans_remaining?: number | null;
  can_scan: boolean;
  scan_count_rule: string;
  access_notice: string;
};

export type SubscriptionStatus = {
  user_id: number;
  plan_code: string;
  status: string;
  active_access: boolean;
  monthly_price: number;
  currency: string;
  core_product_id?: string;
  safehome_addon_product_id?: string;
  add_on_entitlements?: string[];
  subscription?: Record<string, unknown> | null;
  access_notice: string;
  billing_notice?: string;
};

export type BillingProduct = {
  product_id: string;
  name: string;
  plan_code: string;
  price?: number | null;
  currency: string;
  billing_period: string;
  entitlement: string;
};

export type BillingProductsResponse = {
  products: BillingProduct[];
  providers: string[];
  billing_dev_mode: boolean;
  notice: string;
};

export type BillingVerificationInput = {
  provider: 'apple_iap' | 'google_play_billing' | 'stripe_web';
  product_id: string;
  platform?: string;
  purchase_token?: string;
  transaction_id?: string;
};

export type BillingVerificationResult = {
  verified: boolean;
  subscription?: Record<string, unknown> | null;
  subscription_status: SubscriptionStatus;
  verification?: Record<string, unknown>;
  billing_products?: BillingProductsResponse;
};

export type SubscriptionPromoApplyResult = {
  applied: boolean;
  reason?: string | null;
  subscription?: Record<string, unknown> | null;
  promo?: PromoCodeApplyResult | null;
  access_notice: string;
};

export type ConditionTrigger = {
  ingredient?: string | null;
  normalized?: string | null;
  category?: string | null;
  source?: string | null;
  match_type?: string | null;
  matched_value?: string | null;
  impact?: string | null;
  reason: string;
  flags?: string[] | null;
};

export type ConditionResult = {
  condition: string;
  display_name: string;
  kind: string;
  result: SafetyResult | null;
  summary?: string | null;
  explanation?: string | null;
  triggers?: ConditionTrigger[] | null;
  flags?: string[] | null;
  suggestions?: string[] | null;
};

export type Profile = {
  id: number;
  user_id?: number | null;
  name: string;
  allergies: string[];
  conditions: string[];
  notes?: string | null;
  is_default: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type ProfileWriteInput = {
  name: string;
  allergies: string[];
  conditions: string[];
  notes?: string | null;
  is_default?: boolean;
};

export type Favourite = {
  id: number;
  user_id?: number | null;
  barcode: string;
  product_name: string;
  profile_id?: number | null;
  brand?: string | null;
  category?: string | null;
  subcategory?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
  created_at?: string | null;
};

export type FavouriteWriteInput = {
  barcode: string;
  product_name: string;
  profile_id?: number | null;
};

export type HistoryEntry = {
  id: number;
  user_id?: number | null;
  barcode: string;
  product_name: string;
  profile_id?: number | null;
  profile_name?: string | null;
  brand?: string | null;
  category?: string | null;
  subcategory?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
  allergies: string[];
  conditions: string[];
  safety_result?: SafetyResult | null;
  safety_score?: number | null;
  condition_results?: Record<string, ConditionResult> | null;
  scanned_at?: string | null;
};

export type HistoryWriteInput = {
  barcode: string;
  product_name: string;
  profile_id?: number | null;
  profile_name?: string | null;
  allergies: string[];
  conditions: string[];
  safety_result?: SafetyResult | null;
  safety_score?: number | null;
  condition_results?: Record<string, ConditionResult> | null;
};

export type CommunityFeedbackType = 'positive' | 'negative';

export type CommunityFeedbackItem = {
  id: number;
  barcode: string;
  product_name: string;
  feedback_type: CommunityFeedbackType;
  comment: string;
  allergy_tags: string[];
  condition_tags: string[];
  is_visible?: boolean;
  is_flagged?: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export type CommunityFeedbackSummary = {
  barcode: string;
  opinion_label: string;
  disclaimer: string;
  visible_count: number;
  positive_count: number;
  negative_count: number;
  allergy_tag_counts: Record<string, number>;
  condition_tag_counts: Record<string, number>;
  latest_feedback_at?: string | null;
};

export type CommunityFeedbackListResponse = {
  barcode: string;
  summary: CommunityFeedbackSummary;
  items: CommunityFeedbackItem[];
};

export type CommunityFeedbackWriteInput = {
  barcode: string;
  product_name: string;
  feedback_type: CommunityFeedbackType;
  comment: string;
  allergy_tags?: string[];
  condition_tags?: string[];
};

export type PromoCode = {
  id: number;
  code: string;
  code_type: string;
  discount_type: string;
  discount_value?: number | null;
  is_active: boolean;
  usage_limit?: number | null;
  usage_count: number;
  expires_at?: string | null;
  plan_scope?: string | null;
  campaign_label?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type PromoCodeWriteInput = {
  code: string;
  code_type: string;
  discount_type: string;
  discount_value?: number | null;
  is_active?: boolean;
  usage_limit?: number | null;
  expires_at?: string | null;
  plan_scope?: string | null;
  campaign_label?: string | null;
  notes?: string | null;
};

export type PromoCodeValidationInput = {
  code: string;
  plan?: string | null;
};

export type PromoCodePreview = {
  code: string;
  code_type: string;
  discount_type: string;
  discount_value?: number | null;
  plan: string;
  plan_scope?: string | null;
  campaign_label?: string | null;
  base_price?: number | null;
  final_price?: number | null;
  discount_amount?: number | null;
  savings_percent?: number | null;
  trial_extension_days?: number | null;
  access_granted: boolean;
  expires_at?: string | null;
  usage_limit?: number | null;
  usage_count?: number | null;
  notes?: string | null;
  pricing_separation_notice: string;
};

export type PromoCodeValidationResult = {
  valid: boolean;
  reason?: string | null;
  promo_code?: PromoCode | null;
  preview?: PromoCodePreview | null;
  pricing_separation_notice: string;
};

export type PromoCodeApplyResult = {
  applied: boolean;
  reason?: string | null;
  promo_code?: PromoCode | null;
  preview?: PromoCodePreview | null;
  pricing_separation_notice: string;
};

export type Offer = {
  id?: number | null;
  barcode?: string | null;
  retailer?: string | null;
  price?: number | null;
  promo_price?: number | null;
  original_price?: number | null;
  promo_text?: string | null;
  promotion_type?: string | null;
  promotion_label?: string | null;
  buy_quantity?: number | null;
  pay_quantity?: number | null;
  bundle_price?: number | null;
  standard_unit_price?: number | null;
  promo_unit_price?: number | null;
  multi_buy_effective_price?: number | null;
  best_unit_price?: number | null;
  better_value_when_buying?: boolean | null;
  promotion_summary?: string | null;
  stock_status?: string | null;
  in_stock?: boolean | null;
  product_url?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
};

export type PricingSummary = {
  best_price?: number | null;
  lowest_price?: number | null;
  lowest_in_stock_price?: number | null;
  best_value_price?: number | null;
  lowest_standard_price?: number | null;
  lowest_promo_price?: number | null;
  cheapest_retailer?: string | null;
  cheapest_in_stock_retailer?: string | null;
  best_value_retailer?: string | null;
  stock_status?: string | null;
  product_url?: string | null;
  offer_count?: number | null;
  valid_offer_count?: number | null;
  in_stock_offer_count?: number | null;
  out_of_stock_offer_count?: number | null;
  promo_offer_count?: number | null;
  multi_buy_offer_count?: number | null;
  pricing_summary?: string | null;
  unknown_flags?: string[] | null;
  best_offer?: Offer | null;
  best_in_stock_offer?: Offer | null;
  best_value_offer?: Offer | null;
};

export type Analysis = {
  score?: number | null;
  safety_score?: number | null;
  result?: SafetyResult | null;
  safety_result?: SafetyResult | null;
  ingredient_reasoning?: string[] | string | null;
  allergen_warnings?: string[] | string | null;
  personal_warnings?: string[] | string | null;
  unknown_flags?: string[] | null;
  requested_allergies?: string[] | null;
  requested_conditions?: string[] | null;
  condition_results?: Record<string, ConditionResult> | null;
};

export type ProductSummary = {
  id?: number | null;
  barcode: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  subcategory?: string | null;
  safety_score?: number | null;
  safety_result?: SafetyResult | null;
  best_price?: number | null;
  cheapest_retailer?: string | null;
  product_url?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
  image_source_label?: string | null;
  image_blocked_reason?: string | null;
  requested_allergies?: string[] | null;
  requested_conditions?: string[] | null;
  matched_allergens?: string[] | null;
  allergen_safe_for_request?: boolean | null;
  personal_warnings?: string[] | string | null;
  condition_results?: Record<string, ConditionResult> | null;
};

export type Alternatives = {
  safer_option?: ProductSummary | null;
  cheaper_option?: ProductSummary | null;
  same_category_option?: ProductSummary | null;
};

export type ProductResponse = ProductSummary & {
  description?: string | null;
  ingredients?: string[] | string | null;
  allergens?: string[] | string | null;
  allergen_warnings?: string[] | string | null;
  personal_warnings?: string[] | string | null;
  ingredient_reasoning?: string[] | string | null;
  unknown_flags?: string[] | null;
  requested_allergies?: string[] | null;
  requested_conditions?: string[] | null;
  matched_allergens?: string[] | null;
  allergen_safe_for_request?: boolean | null;
  condition_results?: Record<string, ConditionResult> | null;
  pricing?: PricingSummary | null;
  pricing_summary?: PricingSummary | null;
  offers?: Offer[];
  alternatives?: Alternatives | null;
  same_category_products?: ProductSummary[];
  analysis?: Analysis | null;
  entitlement?: Entitlement | null;
};
