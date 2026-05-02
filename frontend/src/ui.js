export const colors = {
  brand: "#5FAF9D",
  brandDark: "#3E8F7D",
  brandLight: "#EEF8F5",
  text: "#0F172A",
  textSoft: "#475569",
  border: "rgba(62,143,125,0.14)",
  white: "#FFFFFF",
  dangerBg: "#FFF1F2",
  dangerText: "#9F1239",
  successBg: "#EEF8F5",
  successText: "#2E7D6B",
  shadow: "0 18px 40px rgba(15,23,42,0.08)",
  softShadow: "0 10px 30px rgba(15,23,42,0.06)",
};

export const pageShellStyle = {
  minHeight: "100vh",
  background: `linear-gradient(180deg, ${colors.brandLight} 0%, #F8FAFC 100%)`,
  padding: "32px 20px 56px",
  boxSizing: "border-box",
};

export const containerStyle = {
  maxWidth: "1180px",
  margin: "0 auto",
  width: "100%",
};

export const heroCardStyle = {
  background: "rgba(255,255,255,0.78)",
  backdropFilter: "blur(14px)",
  WebkitBackdropFilter: "blur(14px)",
  border: `1px solid ${colors.border}`,
  borderRadius: "28px",
  padding: "32px",
  boxShadow: colors.shadow,
};

export const cardStyle = {
  background: colors.white,
  border: `1px solid ${colors.border}`,
  borderRadius: "24px",
  padding: "24px",
  boxShadow: colors.softShadow,
};

export const statCardStyle = {
  background: "#F8FAFC",
  border: `1px solid ${colors.border}`,
  borderRadius: "18px",
  padding: "16px",
};

export const buttonStyle = {
  appearance: "none",
  border: "none",
  borderRadius: "999px",
  padding: "14px 20px",
  background: colors.brand,
  color: "#FFFFFF",
  fontSize: "15px",
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 12px 24px rgba(95,175,157,0.24)",
};

export const secondaryButtonStyle = {
  appearance: "none",
  border: `1px solid ${colors.border}`,
  borderRadius: "999px",
  padding: "14px 20px",
  background: "#FFFFFF",
  color: colors.text,
  fontSize: "15px",
  fontWeight: 700,
  cursor: "pointer",
};

export const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  border: `1px solid ${colors.border}`,
  borderRadius: "16px",
  padding: "14px 16px",
  fontSize: "15px",
  color: colors.text,
  background: "#FFFFFF",
  outline: "none",
  marginTop: "8px",
};

export const labelStyle = {
  fontSize: "13px",
  fontWeight: 700,
  color: colors.textSoft,
};

export const badgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: "8px 12px",
  borderRadius: "999px",
  background: "#F8FAFC",
  border: `1px solid ${colors.border}`,
  color: colors.text,
  fontSize: "13px",
  fontWeight: 700,
};

export const sectionTitleStyle = {
  fontSize: "15px",
  fontWeight: 800,
  color: colors.text,
  margin: 0,
};

export const mutedTextStyle = {
  color: colors.textSoft,
  fontSize: "15px",
};

export const gridTwoStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
  gap: "16px",
};

export const gridThreeStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "16px",
};

export const winnerBannerStyle = {
  background: "linear-gradient(135deg, #EEF8F5 0%, #FFFFFF 100%)",
  border: `1px solid ${colors.border}`,
  borderRadius: "24px",
  padding: "24px",
  boxShadow: colors.softShadow,
};

export const errorBoxStyle = {
  marginTop: "16px",
  padding: "14px 16px",
  borderRadius: "16px",
  background: colors.dangerBg,
  color: colors.dangerText,
  fontWeight: 700,
};

export const successBoxStyle = {
  marginTop: "16px",
  padding: "14px 16px",
  borderRadius: "16px",
  background: colors.successBg,
  color: colors.successText,
  fontWeight: 700,
};

export const dividerStyle = {
  height: "1px",
  background: "rgba(62,143,125,0.10)",
  margin: "20px 0",
  border: "none",
};