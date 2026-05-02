import { useState } from "react";
import { Link } from "react-router-dom";
import {
  activateSubscription,
  applySubscriptionPromo,
  getEntitlement,
  getSubscription,
  loginAccount,
  logoutAccount,
  registerAccount,
  setAccessToken,
} from "../api/client";

const pageStyle = {
  minHeight: "100vh",
  background: "#F4F7F6",
  padding: "24px",
  fontFamily:
    '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif',
};

const shellStyle = {
  maxWidth: "720px",
  margin: "0 auto",
};

const cardStyle = {
  background: "#fff",
  border: "1px solid #DCE7E3",
  borderRadius: "18px",
  boxShadow: "0 14px 40px rgba(22,48,43,0.07)",
  marginTop: "16px",
  padding: "22px",
};

const titleStyle = {
  color: "#0E1715",
  fontSize: "34px",
  fontWeight: 900,
  letterSpacing: 0,
  margin: "0 0 8px",
};

const mutedStyle = {
  color: "#687873",
  lineHeight: 1.6,
  margin: 0,
};

const inputStyle = {
  border: "1px solid #D7E1DD",
  borderRadius: "12px",
  color: "#0E1715",
  fontSize: "16px",
  marginTop: "10px",
  minHeight: "48px",
  padding: "0 14px",
  width: "100%",
};

const buttonStyle = {
  background: "#24786A",
  border: "none",
  borderRadius: "12px",
  color: "#fff",
  cursor: "pointer",
  fontSize: "15px",
  fontWeight: 800,
  minHeight: "48px",
  padding: "0 16px",
  width: "100%",
};

const secondaryButtonStyle = {
  ...buttonStyle,
  background: "#EEF4F2",
  color: "#24786A",
};

const rowStyle = {
  display: "grid",
  gap: "12px",
  gridTemplateColumns: "1fr 1fr",
};

const legalLinks = [
  ["Privacy Policy", "/privacy"],
  ["Terms of Use", "/terms"],
  ["Subscription Terms", "/subscription-terms"],
  ["Data Deletion Request", "/delete-account"],
  ["Contact / Support", "/support"],
];

function statusLabel(value) {
  return String(value || "inactive").replaceAll("_", " ");
}

export default function AccountPage() {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [session, setSession] = useState(null);
  const [entitlement, setEntitlement] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function refreshAccess() {
    const [nextEntitlement, nextSubscription] = await Promise.all([
      getEntitlement(),
      getSubscription(),
    ]);
    setEntitlement(nextEntitlement);
    setSubscription(nextSubscription);
  }

  async function submitAuth(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const result =
        mode === "login"
          ? await loginAccount(email.trim().toLowerCase(), password)
          : await registerAccount(email.trim().toLowerCase(), password);
      setSession(result);
      setAccessToken(result.access_token);
      setPassword("");
      await refreshAccess();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Account request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleActivate() {
    setBusy(true);
    setMessage("");
    try {
      await activateSubscription();
      await refreshAccess();
      setMessage("Monthly access is active.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Subscription request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handlePromo(event) {
    event.preventDefault();
    const code = promoCode.trim().toUpperCase();
    if (!code) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await applySubscriptionPromo(code);
      if (!result.applied) {
        setMessage(result.reason || "Promo code could not be applied.");
        return;
      }
      setPromoCode("");
      await refreshAccess();
      setMessage("Promo access has been applied.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Promo request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutAccount();
    } finally {
      setAccessToken(null);
      setSession(null);
      setEntitlement(null);
      setSubscription(null);
    }
  }

  return (
    <main style={pageStyle}>
      <div style={shellStyle}>
        <Link to="/" style={{ color: "#24786A", fontWeight: 800 }}>
          Back to SafeBite
        </Link>
        <section style={cardStyle}>
          <h1 style={titleStyle}>Account</h1>
          <p style={mutedStyle}>
            {session?.user?.email ||
              "Login or register to track scan usage, saved data, and subscription access."}
          </p>
        </section>

        {!session ? (
          <form onSubmit={submitAuth} style={cardStyle}>
            <div style={rowStyle}>
              <button
                type="button"
                onClick={() => setMode("login")}
                style={mode === "login" ? buttonStyle : secondaryButtonStyle}
              >
                Login
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                style={mode === "register" ? buttonStyle : secondaryButtonStyle}
              >
                Register
              </button>
            </div>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              style={inputStyle}
              type="email"
              value={email}
            />
            <input
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              style={inputStyle}
              type="password"
              value={password}
            />
            <button disabled={busy} style={{ ...buttonStyle, marginTop: "14px" }} type="submit">
              {mode === "login" ? "Login" : "Create account"}
            </button>
          </form>
        ) : (
          <>
            <section style={cardStyle}>
              <h2 style={{ marginTop: 0 }}>Access</h2>
              <div style={rowStyle}>
                <div>
                  <strong>{subscription?.active_access ? "Active" : "Free"}</strong>
                  <p style={mutedStyle}>{statusLabel(subscription?.plan_code || entitlement?.plan)}</p>
                </div>
                <div>
                  <strong>
                    {entitlement?.access_active
                      ? "Unlimited"
                      : entitlement?.free_scans_remaining ?? 0}
                  </strong>
                  <p style={mutedStyle}>Scans left</p>
                </div>
              </div>
              <button disabled={busy} onClick={handleActivate} style={{ ...buttonStyle, marginTop: "16px" }}>
                Activate GBP 5/month
              </button>
            </section>

            <form onSubmit={handlePromo} style={cardStyle}>
              <h2 style={{ marginTop: 0 }}>Promo access</h2>
              <input
                autoCapitalize="characters"
                onChange={(event) => setPromoCode(event.target.value.toUpperCase())}
                placeholder="Promo code"
                style={inputStyle}
                value={promoCode}
              />
              <button disabled={busy} style={{ ...secondaryButtonStyle, marginTop: "14px" }} type="submit">
                Apply code
              </button>
            </form>

            <button disabled={busy} onClick={handleLogout} style={{ ...secondaryButtonStyle, marginTop: "16px" }}>
              Logout
            </button>
          </>
        )}

        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Legal and support</h2>
          <p style={mutedStyle}>
            These pages are launch placeholders and include solicitor-review TODO markers.
          </p>
          <div style={{ display: "grid", gap: "10px", marginTop: "14px" }}>
            {legalLinks.map(([label, href]) => (
              <Link
                key={href}
                to={href}
                style={{
                  background: "#EEF4F2",
                  borderRadius: "12px",
                  color: "#24786A",
                  fontWeight: 800,
                  padding: "13px 14px",
                  textDecoration: "none",
                }}
              >
                {label}
              </Link>
            ))}
          </div>
        </section>

        {message ? <p style={{ ...mutedStyle, marginTop: "16px" }}>{message}</p> : null}
      </div>
    </main>
  );
}
