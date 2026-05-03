from typing import Any, Dict, List, Optional

from fastapi import Header, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from core.registry import get_module_config, list_modules
from schemas import (
    AuthLoginSchema,
    AuthRegisterSchema,
    BillingVerificationSchema,
    CommunityFeedbackFlagSchema,
    CommunityFeedbackWriteSchema,
    FavouriteWriteSchema,
    HistoryWriteSchema,
    PromoCodeUpdateSchema,
    PromoCodeValidationSchema,
    PromoCodeWriteSchema,
    ProfileWriteSchema,
    SubscriptionActivationSchema,
    SubscriptionPromoApplySchema,
)
from services.auth_service import (
    get_user_from_authorization,
    login_user,
    logout_token,
    register_user,
)
from services.condition_engine import apply_conditions
from services.community_service import (
    ALLOWED_FEEDBACK_TYPES,
    COMMENT_MAX_LENGTH,
    LOCKED_ALLERGY_TAGS,
    LOCKED_CONDITION_TAGS,
    build_feedback_summary,
    create_feedback,
    flag_feedback,
    list_feedback,
)
from services.favourites_service import add_favourite, delete_favourite, list_favourites
from services.history_service import add_history_entry, delete_history_entry, list_history
from services.entitlement_service import get_entitlement, record_successful_scan
from services.profile_service import (
    create_profile,
    delete_profile,
    list_profiles,
    resolve_profile_preferences,
    update_profile,
)
from services.subscription_service import (
    activate_monthly_subscription,
    apply_promo_to_subscription,
    cancel_subscription,
    get_subscription_status,
    verify_and_apply_billing_subscription,
)
from services.billing_service import CORE_PRODUCT_ID, list_billing_products
from services.promo_service import (
    apply_promo_code,
    create_promo_code,
    delete_promo_code,
    list_promo_codes,
    update_promo_code,
    validate_promo_code,
)

from database import (
    get_all_products,
    get_offers_by_barcode,
    get_product_count,
    get_product_by_barcode,
    get_similar_products,
    init_db,
    search_products,
    seed_products_from_json,
    seed_sample_offers,
)
from run_imports import run_imports
from services.alternatives_service import build_alternatives
from services.analysis_service import analyse_product
from services.pricing_service import build_pricing_summary, normalise_offer
from services.supermarket_coverage_service import (
    get_best_stocked_offer,
    get_retailer_coverage,
    get_stockists,
    list_import_batch_errors,
    list_import_batches,
    list_retailers,
)

app = FastAPI(title='SafeBite Product Safety API')


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


TARGET_RENDER_BARCODE = '5000177025658'


def bootstrap_product_data() -> None:
    init_db()
    product_count = get_product_count()

    if product_count == 0:
        print('SafeBite startup: product table empty, running import pipeline')
        run_imports(include_reports=False)
    else:
        print(f'SafeBite startup: product table already has {product_count} products')

    seeded_products = seed_products_from_json()
    seeded_offers = seed_sample_offers()
    final_product_count = get_product_count()
    target_product = get_product_by_barcode(TARGET_RENDER_BARCODE)

    print(
        'SafeBite startup: product count after bootstrap = {}'.format(
            final_product_count
        )
    )
    print(
        'SafeBite startup: JSON seeds checked = {}, sample offers added = {}'.format(
            seeded_products,
            seeded_offers,
        )
    )
    print(
        'SafeBite startup: barcode {} present = {}'.format(
            TARGET_RENDER_BARCODE,
            bool(target_product),
        )
    )


@app.on_event('startup')
def startup_event() -> None:
    bootstrap_product_data()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_optional_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def merge_query_values(*groups: Optional[List[str]]) -> List[str]:
    merged: List[str] = []
    for group in groups:
        if not group:
            continue
        for value in group:
            for piece in str(value or '').split(','):
                trimmed = piece.strip()
                if trimmed:
                    merged.append(trimmed)
    return merged


def current_user_from_header(authorization: Optional[str]) -> Dict[str, Any]:
    if not isinstance(authorization, str):
        authorization = None
    user = get_user_from_authorization(authorization)
    if not user:
        raise HTTPException(status_code=401, detail='Valid bearer token required')
    return user


def optional_user_from_header(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    if not isinstance(authorization, str):
        return None
    if not authorization:
        return None
    user = get_user_from_authorization(authorization)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid or expired bearer token')
    return user


def ensure_user_can_scan(user: Optional[Dict[str, Any]]) -> None:
    if not user:
        return
    entitlement = get_entitlement(int(user['id']))
    if not entitlement.get('can_scan'):
        raise HTTPException(
            status_code=402,
            detail={
                'message': 'Free scan limit reached',
                'entitlement': entitlement,
            },
        )


def filter_product_for_allergens(
    product: Dict[str, Any],
    allergens: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not allergens:
        return product

    product_allergens = product.get('allergens', []) or []
    lower_product_allergens = {str(item).strip().lower() for item in product_allergens}
    requested = {str(item).strip().lower() for item in allergens if str(item).strip()}

    allergy_hits = sorted(list(lower_product_allergens.intersection(requested)))

    filtered = dict(product)
    filtered['requested_allergies'] = list(requested)
    filtered['matched_allergens'] = allergy_hits
    filtered['allergen_safe_for_request'] = len(allergy_hits) == 0

    return filtered


def build_similar_products_response(product: Dict[str, Any]) -> List[Dict[str, Any]]:
    related = get_similar_products(product=product, limit=6)

    results = []
    for item in related:
        analysis = analyse_product(item)
        results.append(
            {
                'barcode': item.get('barcode'),
                'name': item.get('name'),
                'brand': item.get('brand'),
                'category': item.get('category', ''),
                'subcategory': item.get('subcategory', ''),
                'safety_score': analysis.get('safety_score'),
                'safety_result': analysis.get('safety_result', 'Unknown'),
            }
        )

    return results


def build_offer_summary(offers: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not offers:
        return {
            'best_offer': None,
            'best_in_stock_offer': None,
            'lowest_price': None,
            'lowest_in_stock_price': None,
            'cheapest_retailer': None,
            'cheapest_in_stock_retailer': None,
            'in_stock_count': 0,
            'out_of_stock_count': 0,
        }

    def offer_price(offer: Dict[str, Any]) -> Optional[float]:
        promo = safe_float(offer.get('promo_price'))
        price = safe_float(offer.get('price'))
        if promo is not None and promo > 0:
            return promo
        return price

    priced_offers = []
    in_stock_offers = []

    for offer in offers:
        current_price = offer_price(offer)
        if current_price is None:
            continue

        shaped = dict(offer)
        shaped['active_price'] = current_price
        priced_offers.append(shaped)

        if shaped.get('in_stock'):
            in_stock_offers.append(shaped)

    priced_offers.sort(
        key=lambda item: (item['active_price'], str(item.get('retailer', '')).lower())
    )
    in_stock_offers.sort(
        key=lambda item: (item['active_price'], str(item.get('retailer', '')).lower())
    )

    best_offer = priced_offers[0] if priced_offers else None
    best_in_stock_offer = in_stock_offers[0] if in_stock_offers else None

    return {
        'best_offer': best_offer,
        'best_in_stock_offer': best_in_stock_offer,
        'lowest_price': best_offer['active_price'] if best_offer else None,
        'lowest_in_stock_price': best_in_stock_offer['active_price'] if best_in_stock_offer else None,
        'cheapest_retailer': best_offer.get('retailer') if best_offer else None,
        'cheapest_in_stock_retailer': best_in_stock_offer.get('retailer') if best_in_stock_offer else None,
        'in_stock_count': len(in_stock_offers),
        'out_of_stock_count': max(len(priced_offers) - len(in_stock_offers), 0),
    }


def build_product_response(
    product: Dict[str, Any],
    include_offers: bool = False,
    include_alternatives: bool = False,
    include_similar: bool = False,
    allergens: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    product_copy = filter_product_for_allergens(product, allergens)

    barcode = product_copy.get('barcode')
    offers = [normalise_offer(offer) for offer in get_offers_by_barcode(barcode)] if barcode else []
    pricing = build_pricing_summary(offers)
    offer_summary = build_offer_summary(offers)

    analysis = analyse_product(product_copy)
    analysis = apply_conditions(
        analysis=analysis,
        allergies=allergens or [],
        conditions=conditions or [],
        product=product_copy,
    )

    response = dict(product_copy)

    computed_score = analysis.get('safety_score')
    fallback_score = safe_optional_int(product_copy.get('safety_score'))
    if analysis.get('safety_result') == 'Unknown' and computed_score is None:
        response['safety_score'] = None
    else:
        response['safety_score'] = safe_optional_int(computed_score)
        if response['safety_score'] is None:
            response['safety_score'] = fallback_score

    response['safety_result'] = analysis.get(
        'safety_result',
        product_copy.get('safety_result', 'Unknown'),
    )
    response['ingredient_reasoning'] = analysis.get(
        'ingredient_reasoning',
        product_copy.get('ingredient_reasoning', ''),
    )
    response['allergen_warnings'] = analysis.get(
        'allergen_warnings',
        product_copy.get('allergen_warnings', []),
    )
    response['personal_warnings'] = analysis.get('personal_warnings', [])
    response['unknown_flags'] = analysis.get('unknown_flags', [])
    response['requested_allergies'] = analysis.get('requested_allergies', [])
    response['requested_conditions'] = analysis.get('requested_conditions', [])
    response['condition_results'] = analysis.get('condition_results', {})

    if response['requested_allergies']:
        matched_allergies = sorted(
            [
                key
                for key in response['requested_allergies']
                if response['condition_results'].get(key, {}).get('result') != 'Safe'
            ]
        )
        response['matched_allergens'] = matched_allergies
        response['allergen_safe_for_request'] = len(matched_allergies) == 0
    else:
        response['matched_allergens'] = []
        response['allergen_safe_for_request'] = True

    response['analysis'] = analysis

    response['pricing'] = pricing
    response['pricing_summary'] = pricing
    response['best_price'] = pricing.get('best_price')
    response['cheapest_retailer'] = pricing.get('cheapest_retailer')
    response['stock_status'] = pricing.get('stock_status')
    response['product_url'] = pricing.get('product_url')

    response['offer_summary'] = offer_summary
    response['best_offer'] = offer_summary.get('best_offer')
    response['best_in_stock_offer'] = pricing.get('best_in_stock_offer') or offer_summary.get('best_in_stock_offer')
    response['lowest_price'] = pricing.get('lowest_price')
    response['lowest_in_stock_price'] = pricing.get('lowest_in_stock_price')
    response['cheapest_in_stock_retailer'] = pricing.get('cheapest_in_stock_retailer')
    response['in_stock_offer_count'] = pricing.get('in_stock_offer_count')
    response['out_of_stock_offer_count'] = pricing.get('out_of_stock_offer_count')

    response['offers'] = offers if include_offers else []

    if include_alternatives:
        response['alternatives'] = build_alternatives(product_copy)
    else:
        response['alternatives'] = {
            'safer_option': None,
            'cheaper_option': None,
            'same_category_option': None,
        }

    response['same_category_products'] = (
        build_similar_products_response(product_copy) if include_similar else []
    )

    return response


@app.get('/')
def root() -> Dict[str, str]:
    return {'message': 'SafeBite backend is running'}


@app.get('/health')
def health() -> Dict[str, str]:
    return {'status': 'ok'}


@app.get('/platform/modules')
def platform_modules_route() -> List[Dict[str, Any]]:
    return list_modules()


@app.get('/platform/modules/{module_code}')
def platform_module_route(module_code: str) -> Dict[str, Any]:
    try:
        return get_module_config(module_code)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post('/auth/register')
def register_route(payload: AuthRegisterSchema) -> Dict[str, Any]:
    try:
        register_user(payload.email, payload.password)
        return login_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/auth/login')
def login_route(payload: AuthLoginSchema) -> Dict[str, Any]:
    try:
        return login_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post('/auth/logout')
def logout_route(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    current_user_from_header(authorization)
    logout_token(authorization)
    return {'status': 'logged_out'}


@app.get('/auth/me')
def me_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    return current_user_from_header(authorization)


@app.get('/subscription')
def subscription_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    return get_subscription_status(int(user['id']))


@app.get('/subscription/status')
def subscription_status_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    return subscription_route(authorization=authorization)


@app.get('/billing/products')
def billing_products_route() -> Dict[str, Any]:
    return list_billing_products()


@app.post('/billing/verify')
def verify_billing_route(
    payload: BillingVerificationSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    try:
        return verify_and_apply_billing_subscription(
            int(user['id']),
            provider=payload.provider,
            product_id=payload.product_id,
            purchase_token=payload.purchase_token,
            transaction_id=payload.transaction_id,
            platform=payload.platform,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post('/subscription/activate')
def activate_subscription_route(
    payload: SubscriptionActivationSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if payload.plan_code != 'paid_monthly':
        raise HTTPException(status_code=400, detail='Only paid_monthly is supported for SafeBite core billing')
    if payload.provider:
        try:
            return verify_and_apply_billing_subscription(
                int(user['id']),
                provider=payload.provider,
                product_id=payload.product_id or CORE_PRODUCT_ID,
                purchase_token=payload.purchase_token,
                transaction_id=payload.transaction_id,
                platform=payload.platform,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    subscription = activate_monthly_subscription(int(user['id']))
    return {
        'verified': False,
        'subscription': subscription,
        'subscription_status': get_subscription_status(int(user['id'])),
        'billing_products': list_billing_products(),
        'message': 'Billing provider verification is required before paid access is granted.',
    }


@app.post('/subscription/cancel')
def cancel_subscription_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    return {
        'subscription': cancel_subscription(int(user['id'])),
        'subscription_status': get_subscription_status(int(user['id'])),
    }


@app.post('/subscription/apply-promo')
def apply_subscription_promo_route(
    payload: SubscriptionPromoApplySchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail='Promo code is required')
    return apply_promo_to_subscription(int(user['id']), payload.code)


@app.post('/subscription/promo')
def subscription_promo_route(
    payload: SubscriptionPromoApplySchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    return apply_subscription_promo_route(payload=payload, authorization=authorization)


@app.get('/entitlement')
def entitlement_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    return get_entitlement(int(user['id']))


@app.get('/subscription/entitlement')
def subscription_entitlement_route(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    return entitlement_route(authorization=authorization)


@app.get('/products')
def list_products(
    q: Optional[str] = None,
    allergen: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    profile_id: Optional[int] = None,
    authorization: Optional[str] = Header(None),
) -> List[Dict[str, Any]]:
    user = optional_user_from_header(authorization)
    if user and q and q.strip():
        ensure_user_can_scan(user)

    if q and q.strip():
        products = search_products(q.strip())
    else:
        products = get_all_products()

    merged_allergies = merge_query_values(allergen, allergies)
    merged_conditions = merge_query_values(conditions)
    merged_allergies, merged_conditions, _ = resolve_profile_preferences(
        profile_id=profile_id,
        manual_allergies=merged_allergies,
        manual_conditions=merged_conditions,
        user_id=int(user['id']) if user else None,
    )

    results = []
    for product in products:
        shaped = build_product_response(
            product=product,
            include_offers=False,
            include_alternatives=False,
            include_similar=False,
            allergens=merged_allergies,
            conditions=merged_conditions,
        )
        results.append(shaped)

    if user and q and q.strip() and results:
        record_successful_scan(int(user['id']), source='manual_product_lookup')

    return results


@app.get('/products/barcode/{barcode}')
def get_product_from_barcode(
    barcode: str,
    allergen: Optional[List[str]] = None,
    allergies: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None,
    profile_id: Optional[int] = None,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = optional_user_from_header(authorization)
    product = get_product_by_barcode(barcode)

    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    ensure_user_can_scan(user)

    resolved_allergies, resolved_conditions, _ = resolve_profile_preferences(
        profile_id=profile_id,
        manual_allergies=merge_query_values(allergen, allergies),
        manual_conditions=merge_query_values(conditions),
        user_id=int(user['id']) if user else None,
    )

    response = build_product_response(
        product=product,
        include_offers=True,
        include_alternatives=True,
        include_similar=True,
        allergens=resolved_allergies,
        conditions=resolved_conditions,
    )
    if user:
        response['entitlement'] = record_successful_scan(
            int(user['id']),
            barcode=barcode,
            source='barcode_lookup',
        )
    return response


@app.get('/offers/{barcode}')
def get_offers_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)

    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    offers = [normalise_offer(offer) for offer in get_offers_by_barcode(barcode)]
    pricing = build_pricing_summary(offers)
    offer_summary = build_offer_summary(offers)

    combined_summary = dict(offer_summary)
    combined_summary.update(pricing)

    return {
        'barcode': barcode,
        'offer_count': len(offers),
        'offers': offers,
        'summary': combined_summary,
        'pricing': pricing,
    }


@app.get('/retailers')
def list_retailers_route() -> List[Dict[str, Any]]:
    return list_retailers()


@app.get('/products/barcode/{barcode}/retailer-coverage')
def get_retailer_coverage_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return get_retailer_coverage(barcode)


@app.get('/products/barcode/{barcode}/stockists')
def get_stockists_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return get_stockists(barcode)


@app.get('/products/barcode/{barcode}/best-stocked-offer')
def get_best_stocked_offer_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return get_best_stocked_offer(barcode)


@app.get('/stockists')
def get_stockists_query_route(barcode: str = Query(...)) -> Dict[str, Any]:
    return get_stockists_route(barcode=barcode)


@app.get('/best-stocked-offer')
def get_best_stocked_offer_query_route(barcode: str = Query(...)) -> Dict[str, Any]:
    return get_best_stocked_offer_route(barcode=barcode)


@app.get('/admin/import-batches')
def list_import_batches_route(limit: int = 50) -> List[Dict[str, Any]]:
    return list_import_batches(limit=limit)


@app.get('/admin/import-batches/{batch_id}/errors')
def list_import_batch_errors_route(
    batch_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    return list_import_batch_errors(batch_id=batch_id, limit=limit)


@app.get('/alternatives/{barcode}')
def get_alternatives_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)

    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    alternatives = build_alternatives(product)

    return {
        'barcode': barcode,
        'alternatives': alternatives,
    }


@app.get('/promo-codes')
def list_promo_codes_route(active_only: bool = False) -> List[Dict[str, Any]]:
    return list_promo_codes(active_only=active_only)


@app.post('/promo-codes')
def create_promo_code_route(payload: PromoCodeWriteSchema) -> Dict[str, Any]:
    try:
        return create_promo_code(
            code=payload.code,
            code_type=payload.code_type,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            is_active=payload.is_active,
            usage_limit=payload.usage_limit,
            expires_at=payload.expires_at,
            plan_scope=payload.plan_scope,
            campaign_label=payload.campaign_label,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put('/promo-codes/{promo_id}')
def update_promo_code_route(
    promo_id: int,
    payload: PromoCodeUpdateSchema,
) -> Dict[str, Any]:
    try:
        updated = update_promo_code(
            promo_id=promo_id,
            is_active=payload.is_active,
            usage_limit=payload.usage_limit,
            expires_at=payload.expires_at,
            plan_scope=payload.plan_scope,
            campaign_label=payload.campaign_label,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail='Promo code not found')
    return updated


@app.delete('/promo-codes/{promo_id}')
def delete_promo_code_route(promo_id: int) -> Dict[str, Any]:
    if not delete_promo_code(promo_id):
        raise HTTPException(status_code=404, detail='Promo code not found')
    return {'status': 'deleted', 'id': promo_id}


@app.post('/promo-codes/validate')
def validate_promo_code_route(payload: PromoCodeValidationSchema) -> Dict[str, Any]:
    result = validate_promo_code(payload.code, plan=payload.plan)
    if not result.get('valid'):
        return result
    return result


@app.post('/promo-codes/apply')
def apply_promo_code_route(payload: PromoCodeValidationSchema) -> Dict[str, Any]:
    if not str(payload.plan or '').strip():
        raise HTTPException(status_code=400, detail='Plan is required to apply a promo code')
    result = apply_promo_code(payload.code, plan=str(payload.plan))
    if not result.get('applied'):
        return result
    return result


@app.get('/profiles')
def get_profiles_route(authorization: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    user = optional_user_from_header(authorization)
    return list_profiles(user_id=int(user['id']) if user else None)


@app.post('/profiles')
def create_profile_route(
    payload: ProfileWriteSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = optional_user_from_header(authorization)
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail='Profile name is required')
    return create_profile(
        name=payload.name,
        allergies=payload.allergies,
        conditions=payload.conditions,
        is_default=payload.is_default,
        notes=payload.notes,
        user_id=int(user['id']) if user else None,
    )


@app.put('/profiles/{profile_id}')
def update_profile_route(
    profile_id: int,
    payload: ProfileWriteSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = optional_user_from_header(authorization)
    updated = update_profile(
        profile_id=profile_id,
        name=payload.name,
        allergies=payload.allergies,
        conditions=payload.conditions,
        is_default=payload.is_default,
        notes=payload.notes,
        user_id=int(user['id']) if user else None,
    )
    if not updated:
        raise HTTPException(status_code=404, detail='Profile not found')
    return updated


@app.delete('/profiles/{profile_id}')
def delete_profile_route(
    profile_id: int,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = optional_user_from_header(authorization)
    if not delete_profile(profile_id, user_id=int(user['id']) if user else None):
        raise HTTPException(status_code=404, detail='Profile not found')
    return {'status': 'deleted', 'id': profile_id}


@app.get('/favourites')
def list_favourites_route(
    barcode: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
) -> List[Dict[str, Any]]:
    user = current_user_from_header(authorization)
    return list_favourites(barcode=barcode, user_id=int(user['id']))


@app.post('/favourites')
def add_favourite_route(
    payload: FavouriteWriteSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if not payload.barcode.strip() or not payload.product_name.strip():
        raise HTTPException(status_code=400, detail='Barcode and product name are required')
    return add_favourite(
        barcode=payload.barcode,
        product_name=payload.product_name,
        profile_id=payload.profile_id,
        user_id=int(user['id']),
    )


@app.delete('/favourites/{favourite_id}')
def delete_favourite_route(
    favourite_id: int,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if not delete_favourite(favourite_id, user_id=int(user['id'])):
        raise HTTPException(status_code=404, detail='Favourite not found')
    return {'status': 'deleted', 'id': favourite_id}


@app.get('/history')
def list_history_route(
    limit: int = Query(50, ge=1, le=200),
    authorization: Optional[str] = Header(None),
) -> List[Dict[str, Any]]:
    user = current_user_from_header(authorization)
    return list_history(limit=limit, user_id=int(user['id']))


@app.post('/history')
def add_history_route(
    payload: HistoryWriteSchema,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if not payload.barcode.strip() or not payload.product_name.strip():
        raise HTTPException(status_code=400, detail='Barcode and product name are required')
    return add_history_entry(
        barcode=payload.barcode,
        product_name=payload.product_name,
        profile_id=payload.profile_id,
        profile_name=payload.profile_name,
        allergies=payload.allergies,
        conditions=payload.conditions,
        safety_result=payload.safety_result,
        safety_score=payload.safety_score,
        condition_results=payload.condition_results,
        user_id=int(user['id']),
    )


@app.delete('/history/{history_id}')
def delete_history_route(
    history_id: int,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    user = current_user_from_header(authorization)
    if not delete_history_entry(history_id, user_id=int(user['id'])):
        raise HTTPException(status_code=404, detail='History row not found')
    return {'status': 'deleted', 'id': history_id}


@app.post('/community-feedback')
def add_community_feedback_route(payload: CommunityFeedbackWriteSchema) -> Dict[str, Any]:
    barcode = payload.barcode.strip()
    if not barcode:
        raise HTTPException(status_code=400, detail='Barcode is required')

    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    feedback_type = str(payload.feedback_type or '').strip().lower()
    if feedback_type not in ALLOWED_FEEDBACK_TYPES:
        raise HTTPException(status_code=400, detail='Feedback type must be positive or negative')

    comment = str(payload.comment or '').strip()
    if len(comment) < 4:
        raise HTTPException(status_code=400, detail='Comment must be at least 4 characters')
    if len(comment) > COMMENT_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail='Comment must be 280 characters or fewer',
        )

    invalid_allergy_tags = sorted(
        {
            str(tag).strip()
            for tag in payload.allergy_tags
            if str(tag).strip().lower() not in LOCKED_ALLERGY_TAGS
        }
    )
    if invalid_allergy_tags:
        raise HTTPException(
            status_code=400,
            detail='Unsupported allergy tags: {0}'.format(', '.join(invalid_allergy_tags)),
        )

    invalid_condition_tags = sorted(
        {
            str(tag).strip()
            for tag in payload.condition_tags
            if str(tag).strip().lower() not in LOCKED_CONDITION_TAGS
        }
    )
    if invalid_condition_tags:
        raise HTTPException(
            status_code=400,
            detail='Unsupported condition tags: {0}'.format(', '.join(invalid_condition_tags)),
        )

    return create_feedback(
        barcode=barcode,
        product_name=(product.get('name') or payload.product_name or '').strip(),
        feedback_type=feedback_type,
        comment=comment,
        allergy_tags=payload.allergy_tags,
        condition_tags=payload.condition_tags,
    )


@app.get('/community-feedback/{barcode}/summary')
def get_community_feedback_summary_route(barcode: str) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')
    return build_feedback_summary(barcode)


@app.get('/community-feedback/{barcode}')
def get_community_feedback_route(
    barcode: str,
    limit: int = Query(20, ge=1, le=50),
) -> Dict[str, Any]:
    product = get_product_by_barcode(barcode)
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    return {
        'barcode': barcode,
        'summary': build_feedback_summary(barcode),
        'items': list_feedback(barcode=barcode, limit=limit),
    }


@app.post('/community-feedback/{feedback_id}/flag')
def flag_community_feedback_route(
    feedback_id: int,
    payload: CommunityFeedbackFlagSchema,
) -> Dict[str, Any]:
    flagged = flag_feedback(feedback_id, reason=payload.reason)
    if not flagged:
        raise HTTPException(status_code=404, detail='Community feedback not found')
    return {
        'status': 'flagged',
        'id': feedback_id,
    }
