import { API_BASE_URL } from './config';
import {
  Alternatives,
  AuthResponse,
  BillingProductsResponse,
  BillingVerificationInput,
  BillingVerificationResult,
  CommunityFeedbackItem,
  CommunityFeedbackListResponse,
  CommunityFeedbackSummary,
  CommunityFeedbackWriteInput,
  Entitlement,
  Favourite,
  FavouriteWriteInput,
  HistoryEntry,
  HistoryWriteInput,
  PromoCode,
  PromoCodeApplyResult,
  PromoCodeValidationInput,
  PromoCodeValidationResult,
  PromoCodeWriteInput,
  ProductResponse,
  ProductSummary,
  Profile,
  ProfileWriteInput,
  SubscriptionPromoApplyResult,
  SubscriptionStatus,
  User,
} from '../types/api';

export type ProductQueryOptions = {
  allergens?: string[];
  conditions?: string[];
  profileId?: number | null;
};

type AlternativesResponse = {
  barcode?: string;
  alternatives?: Alternatives | null;
};

const emptyAlternatives: Alternatives = {
  safer_option: null,
  cheaper_option: null,
  same_category_option: null,
};

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

function withAuthHeaders(extraHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    ...(extraHeaders ?? {}),
  };

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  return headers;
}

function appendParams(params: string[], key: string, values: string[] = []) {
  values
    .map((value) => value.trim())
    .filter(Boolean)
    .forEach((value) => {
      params.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    });
}

function queryString(options?: ProductQueryOptions, query?: string): string {
  const params: string[] = [];

  if (query?.trim()) {
    params.push(`q=${encodeURIComponent(query.trim())}`);
  }

  appendParams(params, 'allergies', options?.allergens);
  appendParams(params, 'conditions', options?.conditions);
  if (options?.profileId != null) {
    params.push(`profile_id=${encodeURIComponent(String(options.profileId))}`);
  }

  return params.length ? `?${params.join('&')}` : '';
}

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...(init ?? {}),
      headers: withAuthHeaders(init?.headers as Record<string, string> | undefined),
    });
  } catch {
    throw new Error('SafeBite cannot reach the backend right now. Check your connection and try again.');
  }

  if (!response.ok) {
    let detail = '';
    try {
      const payload = await response.json();
      detail =
        typeof payload?.detail === 'string'
          ? payload.detail
          : payload?.detail?.message || '';
    } catch {
      detail = '';
    }
    const message =
      detail ||
      (response.status === 404
        ? 'Product not found'
        : response.status === 402
          ? 'Free scan limit reached'
          : `API request failed: ${response.status}`);
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

async function sendJson<T>(path: string, method: string, body?: unknown): Promise<T> {
  return readJson<T>(path, {
    method,
    headers: withAuthHeaders({
      'Content-Type': 'application/json',
    }),
    body: body == null ? undefined : JSON.stringify(body),
  });
}

async function sendDelete(path: string): Promise<void> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
      headers: withAuthHeaders(),
    });
  } catch {
    throw new Error('SafeBite cannot reach the backend right now. Check your connection and try again.');
  }

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
}

export function registerAccount(email: string, password: string): Promise<AuthResponse> {
  return sendJson<AuthResponse>('/auth/register', 'POST', { email, password });
}

export function loginAccount(email: string, password: string): Promise<AuthResponse> {
  return sendJson<AuthResponse>('/auth/login', 'POST', { email, password });
}

export function logoutAccount(): Promise<void> {
  return sendJson('/auth/logout', 'POST').then(() => undefined);
}

export function getCurrentUser(): Promise<User> {
  return readJson<User>('/auth/me');
}

export function getEntitlement(): Promise<Entitlement> {
  return readJson<Entitlement>('/entitlement');
}

export function getSubscription(): Promise<SubscriptionStatus> {
  return readJson<SubscriptionStatus>('/subscription');
}

export function getBillingProducts(): Promise<BillingProductsResponse> {
  return readJson<BillingProductsResponse>('/billing/products');
}

export function verifyBillingPurchase(input: BillingVerificationInput): Promise<BillingVerificationResult> {
  return sendJson<BillingVerificationResult>('/billing/verify', 'POST', input);
}

export function activateSubscription(): Promise<{
  subscription: Record<string, unknown>;
  subscription_status: SubscriptionStatus;
}> {
  return sendJson('/subscription/activate', 'POST', { plan_code: 'paid_monthly' });
}

export function applySubscriptionPromo(code: string): Promise<SubscriptionPromoApplyResult> {
  return sendJson<SubscriptionPromoApplyResult>('/subscription/apply-promo', 'POST', { code });
}

export function getProductByBarcode(
  barcode: string,
  options?: ProductQueryOptions,
): Promise<ProductResponse> {
  return readJson<ProductResponse>(
    `/products/barcode/${encodeURIComponent(barcode)}${queryString(options)}`,
  );
}

export function searchProducts(
  query: string,
  options?: ProductQueryOptions,
): Promise<ProductSummary[]> {
  return readJson<ProductSummary[]>(`/products${queryString(options, query)}`);
}

export async function getAlternativesForBarcode(barcode: string): Promise<Alternatives> {
  const response = await readJson<AlternativesResponse>(
    `/alternatives/${encodeURIComponent(barcode)}`,
  );

  return response.alternatives ?? emptyAlternatives;
}

export function getProfiles(): Promise<Profile[]> {
  return readJson<Profile[]>('/profiles');
}

export function createProfile(input: ProfileWriteInput): Promise<Profile> {
  return sendJson<Profile>('/profiles', 'POST', input);
}

export function updateProfile(profileId: number, input: ProfileWriteInput): Promise<Profile> {
  return sendJson<Profile>(`/profiles/${profileId}`, 'PUT', input);
}

export function deleteProfile(profileId: number): Promise<void> {
  return sendDelete(`/profiles/${profileId}`);
}

export function getPromoCodes(activeOnly = false): Promise<PromoCode[]> {
  const query = activeOnly ? '?active_only=true' : '';
  return readJson<PromoCode[]>(`/promo-codes${query}`);
}

export function createPromoCode(input: PromoCodeWriteInput): Promise<PromoCode> {
  return sendJson<PromoCode>('/promo-codes', 'POST', input);
}

export function validatePromoCode(input: PromoCodeValidationInput): Promise<PromoCodeValidationResult> {
  return sendJson<PromoCodeValidationResult>('/promo-codes/validate', 'POST', input);
}

export function applyPromoCode(input: PromoCodeValidationInput): Promise<PromoCodeApplyResult> {
  return sendJson<PromoCodeApplyResult>('/promo-codes/apply', 'POST', input);
}

export function getFavourites(barcode?: string): Promise<Favourite[]> {
  const query = barcode ? `?barcode=${encodeURIComponent(barcode)}` : '';
  return readJson<Favourite[]>(`/favourites${query}`);
}

export function addFavourite(input: FavouriteWriteInput): Promise<Favourite> {
  return sendJson<Favourite>('/favourites', 'POST', input);
}

export function deleteFavourite(favouriteId: number): Promise<void> {
  return sendDelete(`/favourites/${favouriteId}`);
}

export function getHistory(limit = 50): Promise<HistoryEntry[]> {
  return readJson<HistoryEntry[]>(`/history?limit=${encodeURIComponent(String(limit))}`);
}

export function addHistoryEntry(input: HistoryWriteInput): Promise<HistoryEntry> {
  return sendJson<HistoryEntry>('/history', 'POST', input);
}

export function deleteHistoryEntry(historyId: number): Promise<void> {
  return sendDelete(`/history/${historyId}`);
}

export function getCommunityFeedback(
  barcode: string,
  limit = 20,
): Promise<CommunityFeedbackListResponse> {
  return readJson<CommunityFeedbackListResponse>(
    `/community-feedback/${encodeURIComponent(barcode)}?limit=${encodeURIComponent(String(limit))}`,
  );
}

export function getCommunityFeedbackSummary(barcode: string): Promise<CommunityFeedbackSummary> {
  return readJson<CommunityFeedbackSummary>(
    `/community-feedback/${encodeURIComponent(barcode)}/summary`,
  );
}

export function addCommunityFeedback(
  input: CommunityFeedbackWriteInput,
): Promise<CommunityFeedbackItem> {
  return sendJson<CommunityFeedbackItem>('/community-feedback', 'POST', input);
}

export function flagCommunityFeedback(
  feedbackId: number,
  reason?: string,
): Promise<void> {
  return sendJson(`/community-feedback/${feedbackId}/flag`, 'POST', {
    reason: reason ?? null,
  }).then(() => undefined);
}
