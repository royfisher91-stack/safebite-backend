import Link from 'next/link';
import AppShell from '../../../components/AppShell';
import StatusBadge from '../../../components/StatusBadge';
import { getProduct } from '../../../lib/api';
import { formatPrice, formatText, listText } from '../../../lib/format';

type Props = {
  params: Promise<{
    barcode: string;
  }>;
};

export default async function ProductDetailPage({ params }: Props) {
  const { barcode } = await params;
  const product = await getProduct(barcode);
  const pricing = product.pricing ?? product.pricing_summary ?? {};

  return (
    <AppShell>
      <header className="page-header">
        <div>
          <p className="eyebrow">{formatText(product.brand, 'SafeBite')}</p>
          <h1>{product.name}</h1>
        </div>
        <div className="toolbar">
          <Link className="button button-secondary" href="/products">
            Products
          </Link>
          <Link className="button button-secondary" href={`/offers?barcode=${product.barcode}`}>
            Offers
          </Link>
        </div>
      </header>

      <div className="detail-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>Product editor</h2>
            <StatusBadge value={product.safety_result} />
          </div>
          <div className="panel-body">
            <form className="form-grid">
              <div className="form-field">
                <label htmlFor="barcode">Barcode</label>
                <input className="input" id="barcode" readOnly value={product.barcode} />
              </div>
              <div className="form-field">
                <label htmlFor="brand">Brand</label>
                <input className="input" id="brand" readOnly value={formatText(product.brand, '')} />
              </div>
              <div className="form-field form-field-full">
                <label htmlFor="name">Name</label>
                <input className="input" id="name" readOnly value={product.name} />
              </div>
              <div className="form-field">
                <label htmlFor="category">Category</label>
                <input className="input" id="category" readOnly value={formatText(product.category, '')} />
              </div>
              <div className="form-field">
                <label htmlFor="subcategory">Subcategory</label>
                <input className="input" id="subcategory" readOnly value={formatText(product.subcategory, '')} />
              </div>
              <div className="form-field">
                <label htmlFor="score">Safety score</label>
                <input className="input" id="score" readOnly value={formatText(product.safety_score, '')} />
              </div>
              <div className="form-field">
                <label htmlFor="result">Safety result</label>
                <input className="input" id="result" readOnly value={formatText(product.safety_result, '')} />
              </div>
              <div className="form-field form-field-full">
                <label htmlFor="ingredients">Ingredients</label>
                <textarea className="textarea" id="ingredients" readOnly value={listText(product.ingredients)} />
              </div>
              <div className="form-field form-field-full">
                <label htmlFor="allergens">Allergens</label>
                <textarea className="textarea" id="allergens" readOnly value={listText(product.allergens)} />
              </div>
              <button className="button" disabled type="button">
                Save draft
              </button>
            </form>
          </div>
        </section>

        <aside>
          <section className="panel">
            <div className="panel-header">
              <h2>Pricing</h2>
            </div>
            <div className="panel-body">
              <ul className="quiet-list">
                <li>
                  <span>Best price</span>
                  <strong>{formatPrice(pricing.best_price)}</strong>
                </li>
                <li>
                  <span>Retailer</span>
                  <strong>{formatText(pricing.cheapest_retailer)}</strong>
                </li>
                <li>
                  <span>Stock</span>
                  <strong>{formatText(pricing.stock_status)}</strong>
                </li>
                <li>
                  <span>Offers</span>
                  <strong>{formatText(pricing.offer_count, '0')}</strong>
                </li>
              </ul>
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Source</h2>
            </div>
            <div className="panel-body">
              <ul className="quiet-list">
                <li>
                  <span>Source</span>
                  <strong>{formatText(product.source)}</strong>
                </li>
                <li>
                  <span>Retailer</span>
                  <strong>{formatText(product.source_retailer)}</strong>
                </li>
              </ul>
            </div>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
