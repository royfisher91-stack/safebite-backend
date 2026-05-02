import Link from 'next/link';
import AppShell from '../../components/AppShell';
import MetricCard from '../../components/MetricCard';
import { getOffers, getProduct, getProducts, Offer } from '../../lib/api';
import { formatPrice, formatText } from '../../lib/format';

type Props = {
  searchParams?: Promise<{
    barcode?: string;
  }>;
};

export default async function OffersPage({ searchParams }: Props) {
  const params = await searchParams;
  const products = await getProducts();
  const selectedBarcode = params?.barcode || products[0]?.barcode || '';
  const selectedProduct = selectedBarcode ? await getProduct(selectedBarcode) : null;
  const offersResponse = selectedBarcode ? await getOffers(selectedBarcode) : null;
  const offers: Offer[] = offersResponse?.offers || [];

  return (
    <AppShell>
      <header className="page-header">
        <div>
          <p className="eyebrow">Commercial</p>
          <h1>Offers</h1>
        </div>
        <form className="toolbar">
          <select className="select" defaultValue={selectedBarcode} name="barcode">
            {products.map((product) => (
              <option key={product.barcode} value={product.barcode}>
                {product.name}
              </option>
            ))}
          </select>
          <button className="button" type="submit">
            Load
          </button>
        </form>
      </header>

      <div className="metrics-grid">
        <MetricCard label="Selected product" value={selectedProduct?.brand || 'SafeBite'} detail={selectedBarcode} />
        <MetricCard label="Offers" value={offers.length} />
        <MetricCard
          label="Best price"
          value={formatPrice(selectedProduct?.pricing?.best_price || selectedProduct?.pricing_summary?.best_price)}
        />
        <MetricCard
          label="Retailer"
          value={formatText(selectedProduct?.pricing?.cheapest_retailer || selectedProduct?.pricing_summary?.cheapest_retailer)}
        />
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>{selectedProduct?.name || 'Offers editor'}</h2>
          {selectedProduct ? (
            <Link className="button button-secondary" href={`/products/${selectedProduct.barcode}`}>
              Product
            </Link>
          ) : null}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Retailer</th>
                <th>Price</th>
                <th>Promo</th>
                <th>Stock</th>
                <th>Source</th>
                <th>URL</th>
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <tr key={`${offer.retailer}-${offer.product_url}`}>
                  <td>{formatText(offer.retailer)}</td>
                  <td>{formatPrice(offer.price)}</td>
                  <td>{formatPrice(offer.promo_price)}</td>
                  <td>{formatText(offer.stock_status)}</td>
                  <td>{formatText(offer.source_retailer || offer.source)}</td>
                  <td>
                    {offer.product_url ? (
                      <a className="table-link" href={offer.product_url}>
                        Open
                      </a>
                    ) : (
                      'Not set'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Offer editor</h2>
        </div>
        <div className="panel-body">
          <form className="form-grid">
            <div className="form-field">
              <label htmlFor="retailer">Retailer</label>
              <input className="input" id="retailer" readOnly value={formatText(offers[0]?.retailer, '')} />
            </div>
            <div className="form-field">
              <label htmlFor="price">Price</label>
              <input className="input" id="price" readOnly value={formatText(offers[0]?.price, '')} />
            </div>
            <div className="form-field">
              <label htmlFor="stock">Stock status</label>
              <input className="input" id="stock" readOnly value={formatText(offers[0]?.stock_status, '')} />
            </div>
            <div className="form-field">
              <label htmlFor="url">Product URL</label>
              <input className="input" id="url" readOnly value={formatText(offers[0]?.product_url, '')} />
            </div>
            <button className="button" disabled type="button">
              Save offer
            </button>
          </form>
        </div>
      </section>
    </AppShell>
  );
}
