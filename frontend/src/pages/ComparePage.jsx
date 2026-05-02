import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

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
  maxWidth: "1180px",
  margin: "0 auto",
};

const topBarStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
  marginBottom: "18px",
  flexWrap: "wrap",
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

const topLinkStyle = {
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
  margin: "0 0 10px",
  fontSize: "clamp(28px, 5vw, 52px)",
  lineHeight: 1.02,
  letterSpacing: "-0.04em",
  fontWeight: 800,
};

const subTextStyle = {
  margin: 0,
  color: "#5F6F6B",
  fontSize: "15px",
  lineHeight: 1.7,
};

const twoColGridStyle = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "16px",
  marginBottom: "16px",
};

const sectionCardStyle = {
  background: "rgba(255,255,255,0.9)",
  border: "1px solid rgba(95, 175, 157, 0.14)",
  borderRadius: "24px",
  padding: "20px",
  boxShadow: "0 14px 40px rgba(22, 48, 43, 0.06)",
};

const sectionTitleStyle = {
  margin: "0 0 10px",
  fontSize: "18px",
  fontWeight: 800,
  letterSpacing: "-0.02em",
};

const labelStyle = {
  display: "block",
  fontSize: "12px",
  fontWeight: 800,
  color: "#667A74",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
  marginBottom: "8px",
};

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  borderRadius: "16px",
  border: "1px solid rgba(95, 175, 157, 0.16)",
  padding: "14px 16px",
  fontSize: "15px",
  outline: "none",
  background: "#FFFFFF",
  color: "#142A25",
};

const buttonRowStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "10px",
  marginTop: "18px",
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
  cursor: "pointer",
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
  cursor: "pointer",
};

const successBoxStyle = {
  background: "#ECFDF5",
  color: "#065F46",
  border: "1px solid #A7F3D0",
  borderRadius: "18px",
  padding: "14px 16px",
  marginTop: "16px",
};

const errorBoxStyle = {
  background: "#FEF2F2",
  color: "#991B1B",
  border: "1px solid #FECACA",
  borderRadius: "18px",
  padding: "14px 16px",
  marginBottom: "16px",
};

const winnerBannerStyle = {
  background: "linear-gradient(135deg, #5FAF9D 0%, #3E8F7D 100%)",
  color: "#FFFFFF",
  borderRadius: "24px",
  padding: "18px 20px",
  boxShadow: "0 18px 40px rgba(62,143,125,0.25)",
  marginBottom: "16px",
};

const statGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
  gap: "12px",
};

const statCardStyle = {
  background: "#F9FCFB",
  border: "1px solid rgba(95, 175, 157, 0.12)",
  borderRadius: "18px",
  padding: "14px",
};

const statLabelStyle = {
  margin: "0 0 8px",
  color: "#5E726D",
  fontSize: "13px",
  fontWeight: 700,
};

const statValueStyle = {
  margin: 0,
  fontSize: "28px",
  fontWeight: 800,
  letterSpacing: "-0.03em",
};

const infoBlockStyle = {
  marginTop: "18px",
};

const infoParagraphStyle = {
  ...subTextStyle,
  marginTop: "8px",
};

const badgeWrapStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "8px",
  marginTop: "10px",
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

const compareColumnsStyle = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "16px",
};

const emptyBoxStyle = {
  ...sectionCardStyle,
  textAlign: "center",
  padding: "26px",
};

function parseCommaList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toCommaString(items) {
  return Array.isArray(items) ? items.join(", ") : "";
}

function getSavedUserProfile() {
  try {
    const raw = localStorage.getItem("safebite_user_profile");
    if (!raw) {
      return {
        allergens: [],
        conditions: [],
        avoided_ingredients: [],
        preferred_ingredients: [],
      };
    }

    const parsed = JSON.parse(raw);
    return {
      allergens: Array.isArray(parsed?.allergens) ? parsed.allergens : [],
      conditions: Array.isArray(parsed?.conditions) ? parsed.conditions : [],
      avoided_ingredients: Array.isArray(parsed?.avoided_ingredients)
        ? parsed.avoided_ingredients
        : [],
      preferred_ingredients: Array.isArray(parsed?.preferred_ingredients)
        ? parsed.preferred_ingredients
        : [],
    };
  } catch {
    return {
      allergens: [],
      conditions: [],
      avoided_ingredients: [],
      preferred_ingredients: [],
    };
  }
}

function saveUserProfile(profile) {
  try {
    localStorage.setItem("safebite_user_profile", JSON.stringify(profile));
  } catch {
    // ignore storage errors
  }
}

function getPrice(product) {
  const pricing = product?.pricing || {};
  return pricing.best_price ?? product?.best_price ?? product?.price ?? null;
}

function getRetailer(product) {
  const pricing = product?.pricing || {};
  return pricing.cheapest_retailer ?? product?.cheapest_retailer ?? "Unknown retailer";
}

function getProductUrl(product) {
  const pricing = product?.pricing || {};
  return pricing.product_url ?? product?.product_url ?? "";
}

function getSafetyScore(product) {
  return (
    product?.safety_score ??
    product?.analysis?.safety_score ??
    product?.analysis?.score ??
    0
  );
}

function getSafetyResult(product) {
  return (
    product?.safety_result ??
    product?.analysis?.safety_result ??
    product?.analysis?.result ??
    "Unknown"
  );
}

function formatPrice(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "N/A";
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
  }).format(num);
}

function scoreProduct(product, profile) {
  const safetyScore = Number(getSafetyScore(product) || 0);
  const price = getPrice(product);

  const ingredientsRaw = Array.isArray(product?.ingredients) ? product.ingredients : [];
  const allergensRaw = Array.isArray(product?.allergens) ? product.allergens : [];

  const ingredientsLower = ingredientsRaw.map((item) => String(item).toLowerCase());
  const allergensLower = allergensRaw.map((item) => String(item).toLowerCase());

  let personalisedSafetyScore = safetyScore;
  const reasons = [];

  profile.allergens.forEach((item) => {
    const value = String(item).toLowerCase();
    if (allergensLower.includes(value) || ingredientsLower.some((ing) => ing.includes(value))) {
      personalisedSafetyScore -= 35;
      reasons.push(`Contains or may contain ${value}, which conflicts with your allergen profile.`);
    }
  });

  profile.conditions.forEach((item) => {
    const value = String(item).toLowerCase();

    if (
      value === "coeliac" &&
      (allergensLower.includes("gluten") ||
        ingredientsLower.some(
          (ing) => ing.includes("wheat") || ing.includes("barley") || ing.includes("rye")
        ))
    ) {
      personalisedSafetyScore -= 30;
      reasons.push("Less suitable for a coeliac profile because gluten-linked ingredients were found.");
    }

    if (
      (value === "dairy-free" || value === "milk-free") &&
      (allergensLower.includes("milk") ||
        ingredientsLower.some((ing) => ing.includes("milk") || ing.includes("whey")))
    ) {
      personalisedSafetyScore -= 25;
      reasons.push("Less suitable for a dairy-free profile because milk-linked ingredients were found.");
    }

    if (
      (value === "low-sugar" || value === "diabetes" || value === "diabetic") &&
      ingredientsLower.some(
        (ing) =>
          ing.includes("sugar") ||
          ing.includes("syrup") ||
          ing.includes("glucose") ||
          ing.includes("fructose")
      )
    ) {
      personalisedSafetyScore -= 15;
      reasons.push("Less suitable for a low-sugar profile because added sugars or syrups were found.");
    }

    if (
      (value === "sensitive-stomach" || value === "stomach issues" || value === "reflux") &&
      ingredientsLower.some((ing) => ing.includes("acid") || ing.includes("citric"))
    ) {
      personalisedSafetyScore -= 8;
      reasons.push("May be less suitable for a sensitive stomach profile due to acidic ingredients.");
    }
  });

  profile.avoided_ingredients.forEach((item) => {
    const value = String(item).toLowerCase();
    if (ingredientsLower.some((ing) => ing.includes(value))) {
      personalisedSafetyScore -= 15;
      reasons.push(`Profile penalty applied because ${value} is in your avoided ingredients list.`);
    }
  });

  profile.preferred_ingredients.forEach((item) => {
    const value = String(item).toLowerCase();
    if (ingredientsLower.some((ing) => ing.includes(value))) {
      personalisedSafetyScore += 8;
      reasons.push(`Profile boost applied because ${value} is in your preferred ingredients list.`);
    }
  });

  personalisedSafetyScore = Math.max(0, Math.min(100, personalisedSafetyScore));

  let valueScore = 50;
  if (price != null) {
    if (price <= 0.5) valueScore = 100;
    else if (price <= 1.0) valueScore = 90;
    else if (price <= 1.5) valueScore = 80;
    else if (price <= 2.0) valueScore = 70;
    else if (price <= 3.0) valueScore = 55;
    else if (price <= 4.0) valueScore = 40;
    else valueScore = 25;
  }

  const finalCompareScore = Math.round(personalisedSafetyScore * 0.75 + valueScore * 0.25);

  return {
    barcode: product?.barcode,
    name: product?.name || "Unknown product",
    brand: product?.brand || "Unknown brand",
    safety_score: safetyScore,
    safety_result: getSafetyResult(product),
    personalised_safety_score: personalisedSafetyScore,
    price,
    value_score: valueScore,
    final_compare_score: finalCompareScore,
    allergens: allergensRaw,
    ingredients: ingredientsRaw,
    profile_reasons:
      reasons.length > 0
        ? reasons
        : ["No direct conflicts were found against your saved allergen or condition profile."],
    raw_product: product,
  };
}

function buildCompareResult(leftProduct, rightProduct, profile) {
  const left = scoreProduct(leftProduct, profile);
  const right = scoreProduct(rightProduct, profile);

  let winner = "left";

  if (right.final_compare_score > left.final_compare_score) {
    winner = "right";
  } else if (
    right.final_compare_score === left.final_compare_score &&
    left.price != null &&
    right.price != null
  ) {
    winner = left.price <= right.price ? "left" : "right";
  }

  const winnerData = winner === "left" ? left : right;
  const loserData = winner === "left" ? right : left;

  let explanation = `${winnerData.name} is the better match overall because its personalised compare score is ${winnerData.final_compare_score} versus ${loserData.final_compare_score} for ${loserData.name}.`;

  if (winnerData.personalised_safety_score !== loserData.personalised_safety_score) {
    explanation += ` The biggest difference comes from profile-aware safety, where ${winnerData.name} scored ${winnerData.personalised_safety_score} compared with ${loserData.personalised_safety_score}.`;
  }

  if (winnerData.price != null && loserData.price != null) {
    if (winnerData.price < loserData.price) {
      explanation += ` It is also cheaper at ${formatPrice(winnerData.price)} compared with ${formatPrice(loserData.price)}.`;
    } else if (winnerData.price > loserData.price) {
      explanation += " It still wins even though it costs more, because it is a stronger fit for your saved profile.";
    }
  }

  return {
    winner,
    winner_name: winnerData.name,
    explanation,
    products: { left, right },
    summary: {
      left_score: left.final_compare_score,
      right_score: right.final_compare_score,
    },
  };
}

function CompareColumn({ title, data, isWinner, onViewProduct }) {
  if (!data) return null;

  const retailer = getRetailer(data.raw_product);
  const productUrl = getProductUrl(data.raw_product);

  return (
    <div
      style={{
        ...sectionCardStyle,
        border: isWinner ? "2px solid #5FAF9D" : sectionCardStyle.border,
        boxShadow: isWinner
          ? "0 18px 40px rgba(95,175,157,0.18)"
          : sectionCardStyle.boxShadow,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={subTextStyle}>{title}</div>
          <h2 style={{ margin: "6px 0 0", fontSize: "28px", lineHeight: 1.12 }}>
            {data.name}
          </h2>
          <div style={{ ...subTextStyle, marginTop: 6 }}>{data.brand}</div>
        </div>

        <div
          style={{
            ...pillStyle,
            background: isWinner ? "#EEF8F5" : "#F8FAFC",
            color: isWinner ? "#2E7D6B" : "#334155",
            fontWeight: 800,
          }}
        >
          {isWinner ? "Winner" : "Option"}
        </div>
      </div>

      <div style={{ marginTop: 18, ...statGridStyle }}>
        <div style={statCardStyle}>
          <p style={statLabelStyle}>Compare score</p>
          <p style={statValueStyle}>{data.final_compare_score}</p>
        </div>

        <div style={statCardStyle}>
          <p style={statLabelStyle}>Personalised safety</p>
          <p style={statValueStyle}>{data.personalised_safety_score}</p>
        </div>

        <div style={statCardStyle}>
          <p style={statLabelStyle}>Best price</p>
          <p style={{ ...statValueStyle, fontSize: "24px" }}>{formatPrice(data.price)}</p>
          <p style={{ ...subTextStyle, marginTop: 4 }}>{retailer}</p>
        </div>
      </div>

      <div style={infoBlockStyle}>
        <h3 style={sectionTitleStyle}>Safety result</h3>
        <p style={infoParagraphStyle}>
          {data.safety_score} · {data.safety_result}
        </p>
      </div>

      <div style={infoBlockStyle}>
        <h3 style={sectionTitleStyle}>Why this scored this way</h3>
        <div style={badgeWrapStyle}>
          {(data.profile_reasons || []).map((reason, index) => (
            <div key={index} style={pillStyle}>
              {reason}
            </div>
          ))}
        </div>
      </div>

      <div style={infoBlockStyle}>
        <h3 style={sectionTitleStyle}>Ingredients</h3>
        <p style={infoParagraphStyle}>
          {data.ingredients?.length
            ? data.ingredients.join(", ")
            : "No ingredient information available."}
        </p>
      </div>

      <div style={infoBlockStyle}>
        <h3 style={sectionTitleStyle}>Allergens</h3>
        <p style={infoParagraphStyle}>
          {data.allergens?.length
            ? data.allergens.join(", ")
            : "No known allergen information available."}
        </p>
      </div>

      <div className="sb-button-row" style={buttonRowStyle}>
        <button style={primaryButtonStyle} onClick={() => onViewProduct(data.barcode)}>
          View product
        </button>

        {productUrl ? (
          <a
            href={productUrl}
            target="_blank"
            rel="noreferrer"
            style={secondaryButtonStyle}
          >
            Open retailer
          </a>
        ) : null}
      </div>
    </div>
  );
}

export default function ComparePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const savedProfile = useMemo(() => getSavedUserProfile(), []);

  const [leftBarcode, setLeftBarcode] = useState(
    searchParams.get("left") || searchParams.get("barcode") || ""
  );
  const [rightBarcode, setRightBarcode] = useState(searchParams.get("right") || "");
  const [allergensInput, setAllergensInput] = useState(toCommaString(savedProfile.allergens));
  const [conditionsInput, setConditionsInput] = useState(toCommaString(savedProfile.conditions));
  const [avoidedInput, setAvoidedInput] = useState(toCommaString(savedProfile.avoided_ingredients));
  const [preferredInput, setPreferredInput] = useState(toCommaString(savedProfile.preferred_ingredients));

  const [compareResult, setCompareResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savingMessage, setSavingMessage] = useState("");
  const [error, setError] = useState("");

  const profile = useMemo(() => {
    return {
      allergens: parseCommaList(allergensInput),
      conditions: parseCommaList(conditionsInput),
      avoided_ingredients: parseCommaList(avoidedInput),
      preferred_ingredients: parseCommaList(preferredInput),
    };
  }, [allergensInput, conditionsInput, avoidedInput, preferredInput]);

  async function fetchProduct(barcode) {
    const cleaned = String(barcode || "").trim();
    if (!cleaned) {
      throw new Error("Missing barcode.");
    }

    const response = await fetch(
      `${API_BASE}/products/barcode/${encodeURIComponent(cleaned)}`
    );
    if (!response.ok) {
      throw new Error(`Product ${cleaned} could not be loaded.`);
    }

    return response.json();
  }

  async function runCompare() {
    setLoading(true);
    setError("");
    setCompareResult(null);

    try {
      if (!leftBarcode.trim() || !rightBarcode.trim()) {
        throw new Error("Enter both barcodes before comparing.");
      }

      const [leftProduct, rightProduct] = await Promise.all([
        fetchProduct(leftBarcode),
        fetchProduct(rightBarcode),
      ]);

      const result = buildCompareResult(leftProduct, rightProduct, profile);
      setCompareResult(result);
    } catch (err) {
      setError(err?.message || "Compare failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleSaveProfile() {
    saveUserProfile(profile);
    setSavingMessage("Profile saved for future compare runs.");
    window.setTimeout(() => setSavingMessage(""), 2200);
  }

  function handleViewProduct(barcode) {
    if (!barcode) return;
    navigate(`/product/${encodeURIComponent(barcode)}`);
  }

  useEffect(() => {
    const left = searchParams.get("left") || "";
    const right = searchParams.get("right") || "";
    const singleBarcode = searchParams.get("barcode") || "";

    if (left) setLeftBarcode(left);
    else if (singleBarcode) setLeftBarcode(singleBarcode);

    if (right) setRightBarcode(right);
  }, [searchParams]);

  return (
    <>
      <style>
        {`
          @media (max-width: 900px) {
            .sb-two-col,
            .sb-compare-cols {
              grid-template-columns: 1fr !important;
            }
          }

          @media (max-width: 640px) {
            .sb-stat-grid {
              grid-template-columns: 1fr !important;
            }

            .sb-button-row {
              flex-direction: column;
            }

            .sb-button-row a,
            .sb-button-row button {
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

            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              <Link to="/" style={topLinkStyle}>
                Home
              </Link>
              <Link to="/scanner" style={topLinkStyle}>
                Scanner
              </Link>
            </div>
          </div>

          <div style={heroCardStyle}>
            <div style={eyebrowStyle}>SafeBite compare</div>
            <h1 style={titleStyle}>Compare products with safety and value together</h1>
            <p style={subTextStyle}>
              Put two products side by side, apply your own profile, and let SafeBite
              rank the stronger overall fit.
            </p>
          </div>

          <div className="sb-two-col" style={twoColGridStyle}>
            <div style={sectionCardStyle}>
              <h2 style={sectionTitleStyle}>Choose two products</h2>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Left product barcode</label>
                <input
                  style={inputStyle}
                  value={leftBarcode}
                  onChange={(e) => setLeftBarcode(e.target.value)}
                  placeholder="Enter first barcode"
                />
              </div>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Right product barcode</label>
                <input
                  style={inputStyle}
                  value={rightBarcode}
                  onChange={(e) => setRightBarcode(e.target.value)}
                  placeholder="Enter second barcode"
                />
              </div>

              <div className="sb-button-row" style={buttonRowStyle}>
                <button style={primaryButtonStyle} onClick={runCompare} disabled={loading}>
                  {loading ? "Comparing..." : "Compare now"}
                </button>

                <button
                  style={secondaryButtonStyle}
                  onClick={() =>
                    navigate(
                      `/scanner?mode=compare&left=${encodeURIComponent(
                        leftBarcode
                      )}&right=${encodeURIComponent(rightBarcode)}&side=left`
                    )
                  }
                >
                  Scan left product
                </button>

                <button
                  style={secondaryButtonStyle}
                  onClick={() =>
                    navigate(
                      `/scanner?mode=compare&left=${encodeURIComponent(
                        leftBarcode
                      )}&right=${encodeURIComponent(rightBarcode)}&side=right`
                    )
                  }
                >
                  Scan right product
                </button>
              </div>
            </div>

            <div style={sectionCardStyle}>
              <h2 style={sectionTitleStyle}>Your profile</h2>
              <p style={subTextStyle}>
                Personalise compare results using allergens, conditions, avoided
                ingredients, and preferred ingredients.
              </p>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Allergens</label>
                <input
                  style={inputStyle}
                  value={allergensInput}
                  onChange={(e) => setAllergensInput(e.target.value)}
                  placeholder="milk, peanut, soy"
                />
              </div>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Conditions</label>
                <input
                  style={inputStyle}
                  value={conditionsInput}
                  onChange={(e) => setConditionsInput(e.target.value)}
                  placeholder="coeliac, dairy-free, low-sugar"
                />
              </div>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Avoided ingredients</label>
                <input
                  style={inputStyle}
                  value={avoidedInput}
                  onChange={(e) => setAvoidedInput(e.target.value)}
                  placeholder="palm oil, syrup"
                />
              </div>

              <div style={{ marginTop: "16px" }}>
                <label style={labelStyle}>Preferred ingredients</label>
                <input
                  style={inputStyle}
                  value={preferredInput}
                  onChange={(e) => setPreferredInput(e.target.value)}
                  placeholder="oats, banana"
                />
              </div>

              <div className="sb-button-row" style={buttonRowStyle}>
                <button style={primaryButtonStyle} onClick={handleSaveProfile}>
                  Save profile
                </button>
              </div>

              {savingMessage ? <div style={successBoxStyle}>{savingMessage}</div> : null}
            </div>
          </div>

          {error ? <div style={errorBoxStyle}>{error}</div> : null}

          {compareResult ? (
            <>
              <div style={winnerBannerStyle}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 800,
                    opacity: 0.9,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                  }}
                >
                  Winner
                </div>
                <div style={{ fontSize: 26, fontWeight: 900, marginTop: 4 }}>
                  {compareResult.winner_name}
                </div>
                <div style={{ marginTop: 8, lineHeight: 1.7, fontSize: 15 }}>
                  {compareResult.explanation}
                </div>
              </div>

              <div className="sb-compare-cols" style={compareColumnsStyle}>
                <CompareColumn
                  title="Left product"
                  data={compareResult.products.left}
                  isWinner={compareResult.winner === "left"}
                  onViewProduct={handleViewProduct}
                />

                <CompareColumn
                  title="Right product"
                  data={compareResult.products.right}
                  isWinner={compareResult.winner === "right"}
                  onViewProduct={handleViewProduct}
                />
              </div>
            </>
          ) : (
            <div style={emptyBoxStyle}>
              <h3 style={{ marginTop: 0, fontSize: 20 }}>Ready to compare</h3>
              <p style={{ ...subTextStyle, marginBottom: 0 }}>
                Enter two barcodes or scan them from the scanner page. When both
                products are loaded, SafeBite will compare safety, value, and profile
                fit.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
