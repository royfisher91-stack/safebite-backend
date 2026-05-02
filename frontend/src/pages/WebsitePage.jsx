import { Link } from "react-router-dom";
import "../styles/website.css";

const reviewTodo =
  "TODO: solicitor/legal review required before public launch. This page is a production-ready placeholder, not final legal advice.";

const legalPages = {
  privacy: {
    title: "Privacy Policy",
    eyebrow: "SafeBite legal placeholder",
    intro:
      "This page explains, in plain English, the main types of information SafeBite expects to handle while providing product checks, saved items, account access, and supermarket comparison features.",
    sections: [
      {
        title: "Account data",
        body:
          "SafeBite may use your email address, password credentials handled by the authentication system, user ID, subscription status, promo access, and basic account timestamps to run your account. We should not ask for information we do not need.",
      },
      {
        title: "Saved products, favourites, and scan history",
        body:
          "If you are signed in, SafeBite may store products you save, favourites you add, and barcode scan history so these can appear again in the app. Scan history may include the barcode, product name when known, and time of the check.",
      },
      {
        title: "Subscription and payment handling",
        body:
          "SafeBite may store subscription state, plan code, entitlement, promo access, and payment status. Payment card details should be handled by the chosen payment provider, not stored directly by SafeBite.",
      },
      {
        title: "Product safety data limitations",
        body:
          "Product safety checks depend on available product data such as ingredients, allergens, category, and verified product records. Data can be incomplete, delayed, or wrong, so users must still check the product label and seek medical, allergy, nutrition, or professional advice where needed.",
      },
      {
        title: "Supermarket price and stock limitations",
        body:
          "Retailer prices, promotions, stock status, and product availability can change quickly. SafeBite uses controlled or approved data where available, but supermarket information should be treated as a guide and checked with the retailer before purchase.",
      },
      {
        title: "SafeHome add-on",
        body:
          "SafeHome, if enabled, is intended to support household product checks. It does not replace safety labels, professional advice, manufacturer instructions, or emergency guidance.",
      },
      {
        title: "Deletion requests and contact",
        body:
          "To ask for account deletion or a data request, email privacy@safebite.example from the email linked to your account. For support, email support@safebite.example.",
      },
    ],
  },
  terms: {
    title: "Terms of Use",
    eyebrow: "SafeBite legal placeholder",
    intro:
      "These placeholder terms describe expected use of SafeBite. They must be reviewed and replaced or approved before public launch.",
    sections: [
      {
        title: "Using SafeBite",
        body:
          "SafeBite is designed to support product checking, saved products, scan history, favourites, and supermarket comparison. You should use it as a decision-support tool, not as the only source of truth.",
      },
      {
        title: "Accounts",
        body:
          "You are responsible for using accurate account details, keeping login details secure, and contacting support@safebite.example if you believe your account has been misused.",
      },
      {
        title: "Saved products, scan history, and favourites",
        body:
          "Saved products, scan history, and favourites are provided for convenience. They may be removed, corrected, limited, or unavailable if the underlying product data changes or if the service is unavailable.",
      },
      {
        title: "Product safety limitations",
        body:
          "SafeBite does not provide medical, allergy, nutrition, emergency, or professional advice. Product labels, allergen warnings, manufacturer guidance, and professional advice should be checked before relying on a product.",
      },
      {
        title: "Supermarket price and stock limitations",
        body:
          "Prices, promotions, stock status, and retailer availability are not guaranteed. SafeBite may show unknown or missing values when data has not been verified.",
      },
      {
        title: "SafeHome add-on",
        body:
          "SafeHome is a separate household product add-on. It should not be used as a replacement for manufacturer instructions, hazard labels, or professional safety guidance.",
      },
      {
        title: "Contact and support",
        body:
          "For account, product data, subscription, or support questions, contact support@safebite.example. For legal terms questions, contact legal@safebite.example.",
      },
    ],
  },
  subscriptionTerms: {
    title: "Subscription Terms",
    eyebrow: "SafeBite legal placeholder",
    intro:
      "These placeholder subscription terms explain the planned paid access model and must be reviewed before live payment launch.",
    sections: [
      {
        title: "Plans and access",
        body:
          "SafeBite may offer free access, paid monthly access, promo access, and separate add-ons such as SafeHome. The app should show the current plan, entitlement, and scan allowance before purchase where possible.",
      },
      {
        title: "Payment handling",
        body:
          "Payment details should be processed by the selected payment provider or app store platform. SafeBite should store only the subscription/payment status needed to provide access.",
      },
      {
        title: "Renewals and cancellation",
        body:
          "Subscription renewal and cancellation wording must match the final payment provider or app store rules. TODO: solicitor/payment-provider review required for cancellation, refund, renewal, and billing-cycle wording.",
      },
      {
        title: "Promos and influencer access",
        body:
          "Promo access may be time-limited, revoked if misused, or replaced with another offer. Promo codes do not change product safety limitations or retailer data limitations.",
      },
      {
        title: "SafeHome add-on",
        body:
          "SafeHome may be sold or enabled separately from SafeBite Plus. SafeHome access, limits, and pricing must be confirmed before launch.",
      },
      {
        title: "Support",
        body:
          "For subscription support, email support@safebite.example from the email linked to your SafeBite account.",
      },
    ],
  },
  deleteAccount: {
    title: "Data Deletion Request",
    eyebrow: "Account and data rights placeholder",
    intro:
      "Use this page to request deletion of your SafeBite account data or ask about saved product, scan history, favourites, and subscription records.",
    sections: [
      {
        title: "How to request deletion",
        body:
          "Email privacy@safebite.example from the email linked to your SafeBite account with the subject line Delete my SafeBite account. Include only the information needed to identify your account.",
      },
      {
        title: "What deletion may include",
        body:
          "A deletion request may cover account data, saved products, scan history, favourites, health preference settings stored against the account, promo access, and subscription entitlement records where they are no longer needed.",
      },
      {
        title: "Subscription and payment records",
        body:
          "Some subscription or payment records may need to remain with the payment provider or platform for billing, dispute, refund, tax, or audit reasons. TODO: solicitor/payment-provider review required.",
      },
      {
        title: "Identity checks",
        body:
          "SafeBite may need to confirm you control the account email before acting on deletion, export, or correction requests.",
      },
      {
        title: "Support route",
        body:
          "For help with a deletion request, email support@safebite.example. For privacy-specific questions, email privacy@safebite.example.",
      },
    ],
  },
  contact: {
    title: "Contact / Support",
    eyebrow: "SafeBite support placeholder",
    intro:
      "Use these placeholder contact routes for SafeBite account help, product data questions, data requests, and launch support.",
    sections: [
      {
        title: "General support",
        body:
          "For account access, app issues, saved products, scan history, favourites, or subscription questions, email support@safebite.example.",
      },
      {
        title: "Product data corrections",
        body:
          "If product safety information, allergens, ingredients, barcode data, supermarket price, stock, or retailer availability looks wrong, email support@safebite.example with the barcode, retailer, and screenshot if available.",
      },
      {
        title: "Privacy and deletion",
        body:
          "For deletion requests, data access, or privacy questions, email privacy@safebite.example from the email linked to your account.",
      },
      {
        title: "Partnerships and retailer data",
        body:
          "For approved APIs, licensed feeds, supplier feeds, affiliate feeds, or retailer data partnerships, email partners@safebite.example.",
      },
      {
        title: "Limitations reminder",
        body:
          "SafeBite support cannot provide medical, allergy, nutrition, emergency, or professional advice. For urgent or health-specific concerns, use the appropriate professional route.",
      },
    ],
  },
  support: {
    title: "Contact / Support",
    eyebrow: "SafeBite support placeholder",
    intro:
      "Use these placeholder contact routes for SafeBite account help, product data questions, data requests, and launch support.",
    sections: [],
  },
  pricing: {
    title: "Subscription / Pricing",
    eyebrow: "Simple access for launch",
    intro:
      "SafeBite starts with free product checks and a planned paid subscription for deeper access as the product data network grows.",
    sections: [
      {
        title: "Free access",
        body:
          "Core product lookup, limited free scans, saved products, scan history, favourites, and basic supermarket comparison may be available depending on account state and data availability.",
      },
      {
        title: "SafeBite Plus",
        body:
          "Planned paid access is GBP 5 per month for expanded access and paid entitlement support. TODO: final pricing, billing, cancellation, and refund wording must be reviewed before launch.",
      },
      {
        title: "Subscription terms",
        body:
          "Read the placeholder Subscription Terms for current assumptions about payment handling, renewals, promos, and SafeHome add-on access.",
      },
    ],
  },
  about: {
    title: "About SafeBite",
    eyebrow: "Built for everyday product decisions",
    intro:
      "SafeBite is a product safety and supermarket comparison app for people who want clearer food checks at the point of decision.",
    sections: [
      {
        title: "What SafeBite does",
        body:
          "The app combines product lookup, ingredient and allergen visibility, retailer offer comparison, saved products, scan history, favourites, and safer alternative suggestions where verified data is available.",
      },
      {
        title: "Current retailer focus",
        body:
          "Early supermarket coverage focuses on Tesco, Asda, Sainsbury's, Waitrose, Ocado, and Iceland. Other retailers remain future-compatible until approved data access is available.",
      },
      {
        title: "SafeHome",
        body:
          "SafeHome is planned as a simple add-on for household product checks. It will remain separate from SafeBite food product safety logic.",
      },
    ],
  },
};

legalPages.support.sections = legalPages.contact.sections;

const legalLinks = [
  ["Privacy Policy", "/privacy"],
  ["Terms of Use", "/terms"],
  ["Subscription Terms", "/subscription-terms"],
  ["Data Deletion Request", "/delete-account"],
  ["Contact / Support", "/support"],
];

export default function WebsitePage({ page }) {
  const content = legalPages[page] || legalPages.about;

  return (
    <main className="site-page site-page-simple">
      <nav className="site-nav" aria-label="Main navigation">
        <Link className="site-brand" to="/">
          <span className="site-brand-mark">S</span>
          <span>SafeBite</span>
        </Link>
        <div className="site-nav-links">
          <Link to="/about">About</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/support">Support</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/account">Account</Link>
        </div>
      </nav>

      <section className="simple-hero">
        <p className="site-kicker">{content.eyebrow}</p>
        <h1>{content.title}</h1>
        <p>{content.intro}</p>
        <p className="legal-review-note">{reviewTodo}</p>
      </section>

      <section className="content-list legal-content-list">
        {content.sections.map((section) => (
          <article key={section.title}>
            <h2>{section.title}</h2>
            <p>{section.body}</p>
          </article>
        ))}
      </section>

      <section className="site-disclaimer">
        <strong>Important:</strong> SafeBite supports product checking and comparison, but does not
        replace medical, allergy, nutrition, or professional advice. Product data, supermarket prices,
        stock status, and SafeHome information may be incomplete, delayed, or unavailable.
      </section>

      <footer className="site-footer">
        <div>
          <strong>SafeBite legal placeholders</strong>
          <p>No company registration number or postal address has been provided yet.</p>
        </div>
        <div className="site-footer-links">
          {legalLinks.map(([label, href]) => (
            <Link key={href} to={href}>
              {label}
            </Link>
          ))}
        </div>
      </footer>
    </main>
  );
}
