const API_BASE = "http://127.0.0.1:8000";
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token || null;
}

function authHeaders(extra = {}) {
  return accessToken
    ? { ...extra, Authorization: `Bearer ${accessToken}` }
    : extra;
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== "") {
          query.append(key, item);
        }
      });
    } else if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

async function fetchJson(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: authHeaders(options.headers || {}),
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;

      try {
        const data = await response.json();
        if (typeof data?.detail === "string") {
          message = data.detail;
        } else if (data?.detail?.message) {
          message = data.detail.message;
        }
      } catch {
        // ignore JSON parse errors
      }

      throw new Error(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        "Cannot reach backend at http://127.0.0.1:8000. Make sure uvicorn mainBE:app is running."
      );
    }

    throw error;
  }
}

async function sendJson(path, method, body) {
  return fetchJson(`${API_BASE}${path}`, {
    method,
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: body == null ? undefined : JSON.stringify(body),
  });
}

export async function registerAccount(email, password) {
  return sendJson("/auth/register", "POST", { email, password });
}

export async function loginAccount(email, password) {
  return sendJson("/auth/login", "POST", { email, password });
}

export async function logoutAccount() {
  return sendJson("/auth/logout", "POST");
}

export async function getCurrentUser() {
  return fetchJson(`${API_BASE}/auth/me`);
}

export async function getEntitlement() {
  return fetchJson(`${API_BASE}/entitlement`);
}

export async function getSubscription() {
  return fetchJson(`${API_BASE}/subscription`);
}

export async function activateSubscription() {
  return sendJson("/subscription/activate", "POST", { plan_code: "paid_monthly" });
}

export async function applySubscriptionPromo(code) {
  return sendJson("/subscription/apply-promo", "POST", { code });
}

export async function getProducts(market = "uk", allergens = []) {
  const query = buildQuery({
    market,
    allergen: allergens,
  });

  return fetchJson(`${API_BASE}/products${query}`);
}

export async function searchProducts(queryText, market = "uk", allergens = []) {
  const query = buildQuery({
    q: queryText,
    market,
    allergen: allergens,
  });

  return fetchJson(`${API_BASE}/products/search${query}`);
}

export async function getProduct(name, market = "uk", allergens = []) {
  const query = buildQuery({
    market,
    allergen: allergens,
  });

  return fetchJson(
    `${API_BASE}/products/${encodeURIComponent(name)}${query}`
  );
}

export async function getProductByBarcode(barcode, market = "uk", allergens = []) {
  const query = buildQuery({
    market,
    allergen: allergens,
  });

  return fetchJson(
    `${API_BASE}/products/barcode/${encodeURIComponent(barcode)}${query}`
  );
}

export async function getAlternatives(barcode, market = "uk", allergens = []) {
  const query = buildQuery({
    market,
    allergen: allergens,
  });

  return fetchJson(
    `${API_BASE}/alternatives/${encodeURIComponent(barcode)}${query}`
  );
}
