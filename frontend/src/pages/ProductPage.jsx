import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

const pageStyle = {
  minHeight: "100vh",
  background:
    "linear-gradient(180deg, #F8FCFB 0%, #EEF8F5 45%, #F7FAF9 100%)",
  padding: "20px",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif',
  color: "#10231E",
};

const shellStyle = {
  width: "100%",
  maxWidth: "760px",
  margin: "0 auto",
};

const topBarStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
  marginBottom: "18px",
};

const backButtonStyle = {
  appearance: "none",
  border: "1px solid rgba(62, 143, 125, 0.16)",
  background: "rgba(255,255,255,0.82)",
  color: "#245C50",
  borderRadius: "14px",
  padding: "10px 14px",
  fontSize: "14px",
  fontWeight: 700,
  cursor: "pointer",
  backdropFilter: "blur(10px)",
  WebkitBackdropFilter: "blur(10px)",
  boxShadow: "0 10px 24px rgba(24, 44, 39, 0.06)",
};

const actionLinkStyle = {
  textDecoration: "none",
  border: "1px solid rgba(95, 175, 157, 0.18)",
  background: "#FFFFFF",
  color: "#245C50",
  borderRadius: "14px",
  padding: "10px 14px",
  fontSize: "14px",
  fontWeight: 700,
  boxShadow: "0 10px 24px rgba(24, 44, 39, 0.06)",
};

const heroCardStyle = {
  background: "rgba(255,255,255,0.88)",
  border: "1px solid rgba(95, 175, 157, 0.14)",
  borderRadius: "28px",
  padding: "24px",
  boxShadow: "0 18px 50px rgba(22, 48, 43, 0.08)",
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  marginBottom: "18px",
};

const eyebrowStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  padding: "8px 12px",
  borderRadius: "999px",
  background: "#EEF8F5",
  color: "#3E8F7D",
  fontSize: "12px",
  fontWeight: 800,
  letterSpacing: "0.04em",
  textTransform: "uppercase",
  marginBottom: "14px",
};

const titleStyle = {
  margin: "0 0 8px",
  fontSize: "clamp(28px, 5vw, 40px)",
  lineHeight: 1.05,
  letterSpacing: "-0.03em",
  fontWeight: 800,
};

const subTextStyle = {
  margin: 0,
  color: "#5F6F6B",
  fontSize: "15px",
  lineHeight: 1.6,
};

const scoreRowStyle = {
  display: "grid",
  gridTemplateColumns: "1.2fr 0.8fr",
  gap: "14px",
  marginTop: "18px",
};

const statCardStyle = {
  background: "#FCFFFE",
  border: "1px solid rgba(95, 175, 157, 0.12)",
  borderRadius: "22px",
  padding: "18px",
};

const statLabelStyle = {
  margin: "0 0 8px",
  color: "#5E726D",
  fontSize: "13px",
  fontWeight: 700,
  letterSpacing: "0.02em",
};

const statValueStyle = {
  margin: 0,
  fontSize: "32px",
  fontWeight: 800,
  letterSpacing: "-0.03em",
};

const resultBadgeBase = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "42px",
  padding: "10px 16px",
  borderRadius: "999px",
  fontSize: "15px",
  fontWeight: 800,
  letterSpacing: "-0.01em",
};

const sectionCardStyle = {
  background: "rgba(255,255,255,0.9)",
  border: "1px solid rgba(95, 175, 157, 0.14)",
  borderRadius: "24px",
  padding: "20px",
  boxShadow: "0 14px 40px rgba(22, 48, 43, 0.06)",
  marginBottom: "16px",
};

const sectionTitleStyle = {
  margin: "0 0 14px",
  fontSize: "18px",
  fontWeight: 800,
  letterSpacing: "-0.02em",
};

const infoGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: "12px",
};

const infoItemStyle = {
  background: "#F9FCFB",
  border: "1px solid rgba(95, 175, 157, 0.10)",
  borderRadius: "18px",
  padding: "14px",
};

const infoLabelStyle = {
  margin: "0 0 6px",
  fontSize: "12px",
  fontWeight: 800,
  color: "#667A74",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
};

const infoValueStyle = {
  margin: 0,
  fontSize: "15px",
  fontWeight: 700,
  color: "#142A25",
  lineHeight: 1.45,
  wordBreak: "break-word",
};

const listStyle = {
  margin: 0,
  paddingLeft: "18px",
  color: "#32433F",
  lineHeight: 1.7,
  fontSize: "15px",
};

const pillWrapStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "10px",
};

const pillStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  borderRadius: "999px",
  padding: "10px 14px",
  background: "#F5FBF9",
  border: "1px solid rgba(95, 175, 157, 0.16)",
  color: "#245C50",
  fontSize: "14px",
  fontWeight: 700,
};

const offerCardStyle = {
  background: "#F9FCFB",
  border: "1px solid rgba(95, 175, 157, 0.12)",
  borderRadius: "20px",
  padding: "16px",
  display: "grid",
  gap: "12px",
};

const offerPriceStyle = {
  margin: 0,
  fontSize: "28px",
  fontWeight: 800,
  letterSpacing: "-0.03em",
};

const primaryButtonStyle = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  textDecoration: "none",
  border: "none",
  borderRadius: "16px",
  background: "linear-gradient(135deg, #5FAF9D 0%, #3E8F7D 100%)",
  color: "#FFFFFF",
  padding: "12px 16px",
  fontSize: "14px",
  fontWeight: 800,
  boxShadow: "0 14px 30px rgba(62, 143, 125, 0.22)",
};

const secondaryButtonStyle = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  textDecoration: "none",
  borderRadius: "16px",
  background: "#FFFFFF",
  color: "#245C50",
  border: "1px solid rgba(95, 175, 157, 0.16)",
  padding: "12px 16px",
  fontSize: "14px",
  fontWeight: 800,
};

const rowButtonsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "10px",
};

const emptyBoxStyle = {
  ...sectionCardStyle,
  textAlign: "center",
  padding: "26px",
};

const errorBoxStyle = {
  ...sectionCardStyle,
  border: "1px solid rgba(220, 38, 38, 0.16)",
  background: "rgba(255,255,255,0.95)",
};

const skeletonCardStyle = {
  ...sectionCardStyle,
  overflow: "hidden",
};

const skeletonBlock = (width = "100%", height = 14, radius = 10) => ({
  width,
  height,
  borderRadius: radius,
  background:
    "linear-gradient(90deg, rgba(95,175,157,0.08) 0%, rgba(95,175,157,0.16) 50%, rgba(95,175,157,0.08) 100%)",
  backgroundSize: "200% 100%",
  animation: "sbShimmer 1.4s infinite linear",
});

function normaliseList(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean).map(String);
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function getResultBadgeStyle(result) {
  const base = { ...resultBadgeBase };

  if (result === "Safe") {
    return {
      ...base,
      background: "rgba(34, 197, 94, 0.12)",
      color: "#15803D",
      border: "1px solid rgba(34, 197, 94, 0.18)",
    };
  }

  if (result === "Caution") {
    return {
      ...base,
      background: "rgba(245, 158, 11, 0.12)",
      color: "#B45309",
      border: "1px solid rgba(245, 158, 11, 0.18)",
    };
  }

  return {
    ...base,
    background: "rgba(239, 68, 68, 0.10)",
    color: "#B91C1C",
    border: "1px solid rgba(239, 68, 68, 0.16)",
  };
}

function formatPrice(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "Price unavailable";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
  }).format(num);
}

function compactText(value, fallback = "Not available") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function LoadingState() {
  return (
    <>
      <style>
        {`
          @keyframes sbShimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
          }
          @media (max-width: 640px) {
            .sb-score-grid,
            .sb-info-grid {
              grid-template-columns: 1fr !important;
            }
          }
        `}
      </style>

      <div style={pageStyle}>
        <div style={shellStyle}>
          <div style={topBarStyle}>
            <div style={skeletonBlock("96px", 40, 14)} />
            <div style={skeletonBlock("116px", 40, 14)} />
          </div>

          <div style={skeletonCardStyle}>
            <div style={skeletonBlock("120px", 28, 999)} />
            <div style={{ height: 14 }} />
            <div style={skeletonBlock("72%", 38, 14)} />
            <div style={{ height: 10 }} />
            <div style={skeletonBlock("52%", 18, 10)} />
            <div style={{ height: 20 }} />
            <div className="sb-score-grid" style={scoreRowStyle}>
              <div style={statCardStyle}>
                <div style={skeletonBlock("92px", 12, 10)} />
                <div style={{ height: 10 }} />
                <div style={skeletonBlock("84px", 32, 12)} />
              </div>
              <div style={statCardStyle}>
                <div style={skeletonBlock("90px", 12, 10)} />
                <div style={{ height: 10 }} />
                <div style={skeletonBlock("120px", 42, 999)} />
              </div>
            </div>
          </div>

          <div style={skeletonCardStyle}>
            <div style={skeletonBlock("130px", 18, 10)} />
            <div style={{ height: 14 }} />
            <div className="sb-info-grid" style={infoGridStyle}>
              <div style={skeletonBlock("100%", 76, 18)} />
              <div style={skeletonBlock("100%", 76, 18)} />
              <div style={skeletonBlock("100%", 76, 18)} />
              <div style={skeletonBlock("100%", 76, 18)} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function ProductPage() {
  const { barcode } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [alternatives, setAlternatives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [altLoading, setAltLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadProduct() {
      setLoading(true);
      setError("");
      setProduct(null);

      try {
        const response = await fetch(
          `${API_BASE}/products/barcode/${encodeURIComponent(barcode)}`,
          {
            headers: { Accept: "application/json" },
          }
        );

        if (!response.ok) {
          throw new Error(`Product request failed with status ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setProduct(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Failed to load product.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    if (barcode) {
      loadProduct();
    }

    return () => {
      cancelled = true;
    };
  }, [barcode]);

  useEffect(() => {
    let cancelled = false;

    async function loadAlternatives() {
      if (!barcode) return;

      setAltLoading(true);
      try {
        const response = await fetch(
          `${API_BASE}/alternatives/${encodeURIComponent(barcode)}`,
          {
            headers: { Accept: "application/json" },
          }
        );

        if (!response.ok) {
          throw new Error("Alternatives unavailable");
        }

        const data = await response.json();
        const items = Array.isArray(data)
          ? data
          : Array.isArray(data?.alternatives)
          ? data.alternatives
          : [];

        if (!cancelled) {
          setAlternatives(items);
        }
      } catch {
        if (!cancelled) {
          setAlternatives([]);
        }
      } finally {
        if (!cancelled) {
          setAltLoading(false);
        }
      }
    }

    loadAlternatives();

    return () => {
      cancelled = true;
    };
  }, [barcode]);

  const derived = useMemo(() => {
    if (!product) return null;

    const ingredients = normaliseList(product.ingredients);
    const allergens = normaliseList(product.allergens);
    const reasoning = normaliseList(
      product.ingredient_reasoning ||
        product.analysis?.ingredient_reasoning ||
        product.analysis?.reasoning
    );

    const score =
      product.safety_score ??
      product.analysis?.safety_score ??
      product.analysis?.score ??
      null;

    const result =
      product.safety_result ??
      product.analysis?.safety_result ??
      product.analysis?.result ??
      "Unknown";

    const bestPrice =
      product.best_price ??
      product.pricing?.best_price ??
      product.pricing_summary?.best_price ??
      null;

    const cheapestRetailer =
      product.cheapest_retailer ??
      product.pricing?.cheapest_retailer ??
      product.pricing_summary?.cheapest_retailer ??
      null;

    const stockStatus =
      product.stock_status ??
      product.pricing?.stock_status ??
      product.pricing_summary?.stock_status ??
      null;

    const productUrl =
      product.product_url ??
      product.pricing?.product_url ??
      product.pricing_summary?.product_url ??
      null;

    const offerCount =
      product.offer_count ??
      product.pricing?.offer_count ??
      product.pricing_summary?.offer_count ??
      null;

    const validOfferCount =
      product.valid_offer_count ??
      product.pricing?.valid_offer_count ??
      product.pricing_summary?.valid_offer_count ??
      null;

    return {
      ingredients,
      allergens,
      reasoning,
      score,
      result,
      bestPrice,
      cheapestRetailer,
      stockStatus,
      productUrl,
      offerCount,
      validOfferCount,
    };
  }, [product]);

  if (loading) {
    return <LoadingState />;
  }

  return (
    <>
      <style>
        {`
          @media (max-width: 640px) {
            .sb-score-grid,
            .sb-info-grid,
            .sb-alt-grid {
              grid-template-columns: 1fr !important;
            }
            .sb-row-buttons {
              flex-direction: column;
            }
            .sb-row-buttons a,
            .sb-row-buttons button {
              width: 100%;
            }
          }
        `}
      </style>

      <div style={pageStyle}>
        <div style={shellStyle}>
          <div style={topBarStyle}>
            <button type="button" style={backButtonStyle} onClick={() => navigate(-1)}>
              ← Back
            </button>

            <Link to="/scanner" style={actionLinkStyle}>
              Scan another
            </Link>
          </div>

          {error ? (
            <div style={errorBoxStyle}>
              <h2 style={{ ...sectionTitleStyle, marginBottom: "8px" }}>
                Product could not be loaded
              </h2>
              <p style={{ ...subTextStyle, marginBottom: "14px" }}>
                {compactText(error, "Unknown error")}
              </p>
              <div className="sb-row-buttons" style={rowButtonsStyle}>
                <Link to="/scanner" style={primaryButtonStyle}>
                  Go to scanner
                </Link>
                <Link to="/" style={secondaryButtonStyle}>
                  Back home
                </Link>
              </div>
            </div>
          ) : !product || !derived ? (
            <div style={emptyBoxStyle}>
              <h2 style={{ ...sectionTitleStyle, marginBottom: "8px" }}>
                Product not found
              </h2>
              <p style={{ ...subTextStyle, marginBottom: "14px" }}>
                We could not find a product for barcode {barcode}.
              </p>
              <Link to="/scanner" style={primaryButtonStyle}>
                Try another barcode
              </Link>
            </div>
          ) : (
            <>
              <div style={heroCardStyle}>
                <div style={eyebrowStyle}>SafeBite product check</div>

                <h1 style={titleStyle}>{compactText(product.name, "Unknown product")}</h1>
                <p style={subTextStyle}>
                  {compactText(product.brand, "Unknown brand")}
                  {product.category ? ` • ${product.category}` : ""}
                  {product.subcategory ? ` • ${product.subcategory}` : ""}
                </p>

                <div className="sb-score-grid" style={scoreRowStyle}>
                  <div style={statCardStyle}>
                    <p style={statLabelStyle}>Safety score</p>
                    <p style={statValueStyle}>
                      {derived.score !== null && derived.score !== undefined
                        ? `${derived.score}/100`
                        : "N/A"}
                    </p>
                  </div>

                  <div style={statCardStyle}>
                    <p style={statLabelStyle}>Safety result</p>
                    <div style={getResultBadgeStyle(derived.result)}>
                      {compactText(derived.result, "Unknown")}
                    </div>
                  </div>
                </div>
              </div>

              <div style={sectionCardStyle}>
                <h2 style={sectionTitleStyle}>Overview</h2>
                <div className="sb-info-grid" style={infoGridStyle}>
                  <div style={infoItemStyle}>
                    <p style={infoLabelStyle}>Barcode</p>
                    <p style={infoValueStyle}>{compactText(product.barcode)}</p>
                  </div>

                  <div style={infoItemStyle}>
                    <p style={infoLabelStyle}>Category</p>
                    <p style={infoValueStyle}>
                      {product.category
                        ? `${product.category}${
                            product.subcategory ? ` / ${product.subcategory}` : ""
                          }`
                        : "Not available"}
                    </p>
                  </div>

                  <div style={infoItemStyle}>
                    <p style={infoLabelStyle}>Allergens</p>
                    <p style={infoValueStyle}>
                      {derived.allergens.length
                        ? derived.allergens.join(", ")
                        : "None listed"}
                    </p>
                  </div>

                  <div style={infoItemStyle}>
                    <p style={infoLabelStyle}>Ingredient count</p>
                    <p style={infoValueStyle}>{derived.ingredients.length || 0}</p>
                  </div>
                </div>
              </div>

              <div style={sectionCardStyle}>
                <h2 style={sectionTitleStyle}>Best price</h2>
                <div style={offerCardStyle}>
                  <div>
                    <p style={statLabelStyle}>Current best known price</p>
                    <p style={offerPriceStyle}>{formatPrice(derived.bestPrice)}</p>
                  </div>

                  <div className="sb-info-grid" style={infoGridStyle}>
                    <div style={infoItemStyle}>
                      <p style={infoLabelStyle}>Cheapest retailer</p>
                      <p style={infoValueStyle}>
                        {compactText(derived.cheapestRetailer)}
                      </p>
                    </div>

                    <div style={infoItemStyle}>
                      <p style={infoLabelStyle}>Stock status</p>
                      <p style={infoValueStyle}>{compactText(derived.stockStatus)}</p>
                    </div>

                    <div style={infoItemStyle}>
                      <p style={infoLabelStyle}>Offer count</p>
                      <p style={infoValueStyle}>
                        {derived.offerCount !== null && derived.offerCount !== undefined
                          ? derived.offerCount
                          : "Not available"}
                      </p>
                    </div>

                    <div style={infoItemStyle}>
                      <p style={infoLabelStyle}>Valid offers</p>
                      <p style={infoValueStyle}>
                        {derived.validOfferCount !== null &&
                        derived.validOfferCount !== undefined
                          ? derived.validOfferCount
                          : "Not available"}
                      </p>
                    </div>
                  </div>

                  <div className="sb-row-buttons" style={rowButtonsStyle}>
                    {derived.productUrl ? (
                      <a
                        href={derived.productUrl}
                        target="_blank"
                        rel="noreferrer"
                        style={primaryButtonStyle}
                      >
                        View retailer offer
                      </a>
                    ) : null}

                    <Link
                      to={`/compare?barcode=${encodeURIComponent(product.barcode || barcode)}`}
                      style={secondaryButtonStyle}
                    >
                      Compare options
                    </Link>
                  </div>
                </div>
              </div>

              <div style={sectionCardStyle}>
                <h2 style={sectionTitleStyle}>Ingredients</h2>
                {derived.ingredients.length ? (
                  <div style={pillWrapStyle}>
                    {derived.ingredients.map((item, index) => (
                      <span key={`${item}-${index}`} style={pillStyle}>
                        {item}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p style={subTextStyle}>No ingredient list available.</p>
                )}
              </div>

              <div style={sectionCardStyle}>
                <h2 style={sectionTitleStyle}>Reasoning</h2>
                {derived.reasoning.length ? (
                  <ul style={listStyle}>
                    {derived.reasoning.map((item, index) => (
                      <li key={`${item}-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={subTextStyle}>No detailed reasoning available yet.</p>
                )}
              </div>

              <div style={sectionCardStyle}>
                <h2 style={sectionTitleStyle}>Alternatives</h2>

                {altLoading ? (
                  <p style={subTextStyle}>Loading alternatives...</p>
                ) : alternatives.length ? (
                  <div
                    className="sb-alt-grid"
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                      gap: "12px",
                    }}
                  >
                    {alternatives.slice(0, 4).map((item, index) => {
                      const altBarcode = item?.barcode || item?.id || `alt-${index}`;
                      const altScore =
                        item?.safety_score ??
                        item?.analysis?.safety_score ??
                        item?.analysis?.score;

                      const altResult =
                        item?.safety_result ??
                        item?.analysis?.safety_result ??
                        item?.analysis?.result ??
                        "Unknown";

                      const altPrice =
                        item?.best_price ??
                        item?.pricing?.best_price ??
                        item?.pricing_summary?.best_price;

                      return (
                        <div key={altBarcode} style={infoItemStyle}>
                          <p
                            style={{
                              margin: "0 0 8px",
                              fontSize: "16px",
                              fontWeight: 800,
                              lineHeight: 1.3,
                            }}
                          >
                            {compactText(item?.name, "Alternative product")}
                          </p>

                          <p style={{ ...subTextStyle, fontSize: "14px", marginBottom: "10px" }}>
                            {compactText(item?.brand, "Unknown brand")}
                          </p>

                          <div style={pillWrapStyle}>
                            <span style={pillStyle}>
                              {altScore !== null && altScore !== undefined
                                ? `Score ${altScore}`
                                : "Score N/A"}
                            </span>
                            <span style={pillStyle}>{altResult}</span>
                            <span style={pillStyle}>{formatPrice(altPrice)}</span>
                          </div>

                          {item?.barcode ? (
                            <div style={{ marginTop: "12px" }}>
                              <Link
                                to={`/product/${encodeURIComponent(item.barcode)}`}
                                style={secondaryButtonStyle}
                              >
                                View product
                              </Link>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p style={subTextStyle}>No alternatives available yet.</p>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}