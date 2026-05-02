from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


KNOWN_BARCODE = "5056000505910"


class SmokeFailure(Exception):
    pass


def _load_routes() -> Any:
    try:
        import mainBE
    except Exception as exc:
        raise SmokeFailure("Could not load backend routes: {0}".format(exc))
    return mainBE


def _route_response(func: Callable[[], Any]) -> Tuple[int, Any]:
    try:
        return 200, func()
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        detail = getattr(exc, "detail", None)
        if status_code is not None:
            return int(status_code), {"detail": detail}
        raise


def _json(payload: Any) -> Any:
    try:
        return payload
    except Exception as exc:
        raise SmokeFailure("Response was not JSON: {0}".format(exc))


def _require_keys(payload: Dict[str, Any], keys: List[str], label: str) -> None:
    for key in keys:
        if key not in payload:
            raise SmokeFailure("{0} missing key {1}".format(label, key))


def _expect_status(status_code: int, payload: Any, expected: List[int], label: str) -> Any:
    if status_code not in expected:
        body = str(payload)[:500]
        raise SmokeFailure(
            "{0} returned HTTP {1}, expected {2}. Body: {3}".format(
                label,
                status_code,
                expected,
                body,
            )
        )
    return _json(payload)


def _check_health(payload: Dict[str, Any]) -> None:
    if payload.get("status") != "ok":
        raise SmokeFailure("/health did not return status=ok")


def _check_product(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["barcode"], "/products/barcode")
    if str(payload.get("barcode")) != KNOWN_BARCODE:
        raise SmokeFailure("Product barcode mismatch")


def _check_offers(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["barcode", "offer_count", "offers"], "/offers")
    if str(payload.get("barcode")) != KNOWN_BARCODE:
        raise SmokeFailure("Offers barcode mismatch")
    if not isinstance(payload.get("offers"), list):
        raise SmokeFailure("Offers response does not contain a list")


def _check_alternatives(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["barcode", "alternatives"], "/alternatives")
    if str(payload.get("barcode")) != KNOWN_BARCODE:
        raise SmokeFailure("Alternatives barcode mismatch")
    if not isinstance(payload.get("alternatives"), (dict, list)):
        raise SmokeFailure("Alternatives response does not contain a dict or list")


def _check_retailers(payload: List[Dict[str, Any]]) -> None:
    if not isinstance(payload, list):
        raise SmokeFailure("/retailers did not return a list")
    retailers = [item.get("retailer") for item in payload if isinstance(item, dict)]
    for retailer in ["Tesco", "Asda", "Sainsbury's", "Waitrose", "Ocado", "Iceland", "Morrisons"]:
        if retailer not in retailers:
            raise SmokeFailure("/retailers missing active retailer {0}".format(retailer))


def _check_stockists(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["barcode", "stockist_count", "stockists"], "/stockists")
    if not isinstance(payload.get("stockists"), list):
        raise SmokeFailure("Stockists response does not contain a list")


def _check_retailer_coverage(payload: Dict[str, Any]) -> None:
    _require_keys(
        payload,
        ["barcode", "retailer_count", "active_retailers", "missing_retailers", "offers"],
        "/retailer-coverage",
    )
    if not isinstance(payload.get("offers"), list):
        raise SmokeFailure("Retailer coverage response does not contain offers list")


def _check_best_stocked_offer(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["barcode", "best_offer"], "/best-stocked-offer")
    if str(payload.get("barcode")) != KNOWN_BARCODE:
        raise SmokeFailure("Best stocked offer barcode mismatch")


def _check_platform_modules(payload: List[Dict[str, Any]]) -> None:
    if not isinstance(payload, list):
        raise SmokeFailure("/platform/modules did not return a list")
    codes = [
        item.get("module_code") or item.get("code")
        for item in payload
        if isinstance(item, dict)
    ]
    if "safebite_food" not in codes:
        raise SmokeFailure("/platform/modules missing safebite_food")
    if "safehome" not in codes:
        raise SmokeFailure("/platform/modules missing safehome")


def _check_billing_products(payload: Dict[str, Any]) -> None:
    _require_keys(payload, ["products"], "/billing/products")
    product_ids = [item.get("product_id") for item in payload.get("products", []) if isinstance(item, dict)]
    if "safebite_core_monthly" not in product_ids:
        raise SmokeFailure("/billing/products missing safebite_core_monthly")
    if "safehome_addon" not in product_ids:
        raise SmokeFailure("/billing/products missing safehome_addon")


def _check_unauthorized(payload: Dict[str, Any], label: str) -> None:
    if "detail" not in payload:
        raise SmokeFailure("{0} unauthorized response missing detail".format(label))


def _run_case(
    route_call: Callable[[], Any],
    method: str,
    path: str,
    expected_status: List[int],
    label: str,
    checker: Optional[Callable[[Any], None]] = None,
) -> Dict[str, Any]:
    status_code, response_payload = _route_response(route_call)
    payload = _expect_status(status_code, response_payload, expected_status, label)
    if checker is not None:
        checker(payload)
    return {
        "label": label,
        "method": method,
        "path": path,
        "status_code": status_code,
        "result": "PASS",
    }


def main() -> int:
    routes = _load_routes()
    auth_login_payload = routes.AuthLoginSchema(
        email="pre-release-smoke@example.invalid",
        password="not-a-real-password",
    )

    checks = [
        (lambda: routes.health(), "GET", "/health", [200], "/health", _check_health),
        (lambda: routes.get_product_from_barcode(KNOWN_BARCODE), "GET", "/products/barcode/{0}".format(KNOWN_BARCODE), [200], "/products/barcode/{known_barcode}", _check_product),
        (lambda: routes.get_offers_route(KNOWN_BARCODE), "GET", "/offers/{0}".format(KNOWN_BARCODE), [200], "/offers/{known_barcode}", _check_offers),
        (lambda: routes.get_alternatives_route(KNOWN_BARCODE), "GET", "/alternatives/{0}".format(KNOWN_BARCODE), [200], "/alternatives/{known_barcode}", _check_alternatives),
        (lambda: routes.list_retailers_route(), "GET", "/retailers", [200], "/retailers", _check_retailers),
        (lambda: routes.get_stockists_route(KNOWN_BARCODE), "GET", "/products/barcode/{0}/stockists".format(KNOWN_BARCODE), [200], "/products/barcode/{known_barcode}/stockists", _check_stockists),
        (lambda: routes.get_retailer_coverage_route(KNOWN_BARCODE), "GET", "/products/barcode/{0}/retailer-coverage".format(KNOWN_BARCODE), [200], "/products/barcode/{known_barcode}/retailer-coverage", _check_retailer_coverage),
        (lambda: routes.get_best_stocked_offer_route(KNOWN_BARCODE), "GET", "/products/barcode/{0}/best-stocked-offer".format(KNOWN_BARCODE), [200], "/products/barcode/{known_barcode}/best-stocked-offer", _check_best_stocked_offer),
        (lambda: routes.platform_modules_route(), "GET", "/platform/modules", [200], "/platform/modules", _check_platform_modules),
        (lambda: routes.billing_products_route(), "GET", "/billing/products", [200], "/billing/products", _check_billing_products),
        (lambda: routes.subscription_status_route(), "GET", "/subscription/status", [401], "/subscription/status without token", lambda payload: _check_unauthorized(payload, "/subscription/status")),
        (lambda: routes.subscription_entitlement_route(), "GET", "/subscription/entitlement", [401], "/subscription/entitlement without token", lambda payload: _check_unauthorized(payload, "/subscription/entitlement")),
        (lambda: routes.login_route(auth_login_payload), "POST", "/auth/login", [401], "/auth/login with invalid credentials", lambda payload: _check_unauthorized(payload, "/auth/login")),
    ]

    results: List[Dict[str, Any]] = []
    failures: List[str] = []

    for route_call, method, path, expected, label, checker in checks:
        try:
            results.append(_run_case(route_call, method, path, expected, label, checker))
        except Exception as exc:
            failures.append("{0}: {1}".format(label, exc))
            results.append(
                {
                    "label": label,
                    "method": method,
                    "path": path,
                    "status_code": None,
                    "result": "FAIL",
                    "error": str(exc),
                }
            )

    print("SafeBite pre-release smoke test")
    print("- known_barcode: {0}".format(KNOWN_BARCODE))
    print("- checks_total: {0}".format(len(results)))
    print("- checks_failed: {0}".format(len(failures)))

    for result in results:
        status = result["status_code"] if result["status_code"] is not None else "n/a"
        print("- {0} {1}: {2} ({3})".format(result["method"], result["path"], result["result"], status))

    if failures:
        print("\nFailures")
        for failure in failures:
            print("- {0}".format(failure))
        return 1

    print("SafeBite pre-release smoke test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
