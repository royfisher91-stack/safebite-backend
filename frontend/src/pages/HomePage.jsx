import { Link } from "react-router-dom";
import heroImage from "../assets/hero.png";
import "../styles/website.css";

const activeRetailers = ["Tesco", "Asda", "Sainsbury's", "Waitrose", "Ocado", "Iceland"];

export default function HomePage() {
  return (
    <main className="site-page">
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

      <section className="site-hero">
        <div className="site-hero-copy">
          <p className="site-kicker">Product safety and supermarket comparison</p>
          <h1>Check food products with calm, clear confidence.</h1>
          <p className="site-hero-text">
            SafeBite helps shoppers check ingredients, allergens, and supermarket availability in one
            simple app, with safer alternatives and price comparison built around verified product data.
          </p>
          <div className="site-action-row">
            <Link className="site-button site-button-primary" to="/scanner">
              Scan a barcode
            </Link>
            <Link className="site-button site-button-secondary" to="/compare">
              Compare products
            </Link>
          </div>
          <div className="download-row" aria-label="App download placeholders">
            <span className="download-button">App Store - coming soon</span>
            <span className="download-button">Google Play - coming soon</span>
          </div>
        </div>
        <div className="site-hero-visual" aria-label="SafeBite app preview">
          <img src={heroImage} alt="SafeBite app preview" />
        </div>
      </section>

      <section className="site-band">
        <div>
          <p className="site-kicker">Current supermarket focus</p>
          <h2>Built around the first six active retailers.</h2>
        </div>
        <div className="retailer-strip">
          {activeRetailers.map((retailer) => (
            <span key={retailer}>{retailer}</span>
          ))}
        </div>
      </section>

      <section className="feature-grid">
        <article>
          <span className="feature-number">01</span>
          <h2>Safety checks</h2>
          <p>
            Ingredient, allergen, and processing signals are shown separately from retailer availability
            so users can understand what is known and what still needs verification.
          </p>
        </article>
        <article>
          <span className="feature-number">02</span>
          <h2>Supermarket comparison</h2>
          <p>
            See where products are stocked, compare current offers, and find the best stocked price
            where approved retailer data is available.
          </p>
        </article>
        <article>
          <span className="feature-number">03</span>
          <h2>SafeHome add-on</h2>
          <p>
            SafeHome is planned as a lightweight paid add-on for household product checks, kept separate
            from SafeBite food safety scoring.
          </p>
        </article>
      </section>

      <section className="site-disclaimer">
        <strong>Important:</strong> SafeBite supports product checking and comparison, but does not
        replace medical, allergy, nutrition, or professional advice.
      </section>

      <footer className="site-footer">
        <div>
          <strong>SafeBite</strong>
          <p>Contact: hello@safebite.example</p>
          <p>Support: support@safebite.example</p>
        </div>
        <div className="site-footer-links">
          <Link to="/privacy">Privacy</Link>
          <Link to="/terms">Terms of Use</Link>
          <Link to="/subscription-terms">Subscription Terms</Link>
          <Link to="/delete-account">Delete account</Link>
          <Link to="/contact">Contact</Link>
        </div>
      </footer>
    </main>
  );
}
