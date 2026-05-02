import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

const pageStyle = {
  minHeight: "100vh",
  background:
    "linear-gradient(180deg, #F8FCFB 0%, #EEF8F5 45%, #F7FAF9 100%)",
  padding: "20px",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif',
};

const shellStyle = {
  width: "100%",
  maxWidth: "700px",
  margin: "0 auto",
};

const cardStyle = {
  background: "#FFFFFF",
  borderRadius: "24px",
  padding: "20px",
  boxShadow: "0 14px 40px rgba(22, 48, 43, 0.06)",
  marginBottom: "16px",
};

const titleStyle = {
  fontSize: "32px",
  fontWeight: "800",
  marginBottom: "10px",
};

const subTextStyle = {
  color: "#5F6F6B",
  fontSize: "15px",
};

const inputStyle = {
  width: "100%",
  padding: "14px",
  borderRadius: "14px",
  border: "1px solid #ddd",
  marginTop: "10px",
  fontSize: "16px",
};

const buttonStyle = {
  marginTop: "14px",
  padding: "14px",
  borderRadius: "14px",
  border: "none",
  background: "#5FAF9D",
  color: "#fff",
  fontWeight: "700",
  cursor: "pointer",
  width: "100%",
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#fff",
  color: "#245C50",
  border: "1px solid rgba(95,175,157,0.2)",
};

const infoBoxStyle = {
  background: "#EEF8F5",
  borderRadius: "16px",
  padding: "12px",
  marginTop: "10px",
  fontSize: "14px",
};

export default function ScannerPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const mode = searchParams.get("mode"); // compare or null
  const side = searchParams.get("side"); // left or right
  const leftParam = searchParams.get("left") || "";
  const rightParam = searchParams.get("right") || "";

  const [barcode, setBarcode] = useState("");
  const [status, setStatus] = useState("");

  function handleSubmit() {
    const clean = barcode.trim();

    if (!clean) {
      setStatus("Please enter a barcode.");
      return;
    }

    if (mode === "compare") {
      if (side === "left") {
        navigate(
          `/compare?left=${encodeURIComponent(clean)}&right=${encodeURIComponent(
            rightParam
          )}`
        );
      } else {
        navigate(
          `/compare?left=${encodeURIComponent(
            leftParam
          )}&right=${encodeURIComponent(clean)}`
        );
      }
    } else {
      navigate(`/product/${encodeURIComponent(clean)}`);
    }
  }

  return (
    <div style={pageStyle}>
      <div style={shellStyle}>
        <div style={cardStyle}>
          <h1 style={titleStyle}>Scan or enter barcode</h1>

          <p style={subTextStyle}>
            {mode === "compare"
              ? `Scanning for ${side === "left" ? "LEFT" : "RIGHT"} product`
              : "Scan a product to check safety and pricing"}
          </p>

          <input
            style={inputStyle}
            placeholder="Enter barcode manually"
            value={barcode}
            onChange={(e) => setBarcode(e.target.value)}
          />

          <button style={buttonStyle} onClick={handleSubmit}>
            Continue
          </button>

          {mode === "compare" && (
            <>
              <button
                style={secondaryButtonStyle}
                onClick={() =>
                  navigate(
                    `/compare?left=${encodeURIComponent(
                      leftParam
                    )}&right=${encodeURIComponent(rightParam)}`
                  )
                }
              >
                Back to compare
              </button>

              <div style={infoBoxStyle}>
                <strong>Current:</strong>
                <br />
                Left: {leftParam || "Not set"}
                <br />
                Right: {rightParam || "Not set"}
              </div>
            </>
          )}

          {status && <div style={infoBoxStyle}>{status}</div>}
        </div>

        <div style={cardStyle}>
          <h2 style={{ fontSize: "20px", fontWeight: "700" }}>
            Quick actions
          </h2>

          <Link to="/" style={{ textDecoration: "none" }}>
            <button style={secondaryButtonStyle}>Back to Home</button>
          </Link>

          <Link to="/compare" style={{ textDecoration: "none" }}>
            <button style={secondaryButtonStyle}>Go to Compare</button>
          </Link>
        </div>
      </div>
    </div>
  );
}
