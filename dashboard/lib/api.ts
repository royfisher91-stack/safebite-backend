export type PricingSummary = {
  best_price?: number | null;
  cheapest_retailer?: string | null;
  stock_status?: string | null;
  product_url?: string | null;
  offer_count?: number | null;
  valid_offer_count?: number | null;
};

export type Offer = {
  id?: number | null;
  barcode?: string | null;
  retailer?: string | null;
  price?: number | null;
  promo_price?: number | null;
  original_price?: number | null;
  promo_text?: string | null;
  stock_status?: string | null;
  in_stock?: boolean | null;
  product_url?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
  source?: string | null;
  source_retailer?: string | null;
};

export type Product = {
  id?: number | null;
  barcode: string;
  name: string;
  brand?: string | null;
  description?: string | null;
  ingredients?: string[] | string | null;
  allergens?: string[] | string | null;
  category?: string | null;
  subcategory?: string | null;
  image_url?: string | null;
  image_source_type?: string | null;
  image_rights_status?: string | null;
  image_credit?: string | null;
  image_last_verified_at?: string | null;
  image_source_label?: string | null;
  image_blocked_reason?: string | null;
  source?: string | null;
  source_retailer?: string | null;
  safety_score?: number | null;
  safety_result?: string | null;
  ingredient_reasoning?: string | null;
  allergen_warnings?: string[] | string | null;
  pricing?: PricingSummary | null;
  pricing_summary?: PricingSummary | null;
  offers?: Offer[];
  alternatives?: {
    safer_option?: Product | null;
    cheaper_option?: Product | null;
    same_category_option?: Product | null;
  } | null;
};

export type OffersResponse = {
  barcode: string;
  offer_count: number;
  offers: Offer[];
  summary?: Record<string, unknown>;
};

const apiBaseUrl =
  process.env.SAFEBITE_API_URL ||
  process.env.NEXT_PUBLIC_SAFEBITE_API_URL ||
  'http://127.0.0.1:8000';

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`SafeBite API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getProducts(query?: string): Promise<Product[]> {
  const path = query && query.trim()
    ? `/products?q=${encodeURIComponent(query.trim())}`
    : '/products';

  return readJson<Product[]>(path);
}

export async function getProduct(barcode: string): Promise<Product> {
  return readJson<Product>(`/products/barcode/${encodeURIComponent(barcode)}`);
}

export async function getOffers(barcode: string): Promise<OffersResponse> {
  return readJson<OffersResponse>(`/offers/${encodeURIComponent(barcode)}`);
}

export async function getHealth(): Promise<{ status: string }> {
  return readJson<{ status: string }>('/health');
}

export function getApiBaseUrl(): string {
  return apiBaseUrl;
}
