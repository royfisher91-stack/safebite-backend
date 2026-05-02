import AppShell from '../../components/AppShell';
import MetricCard from '../../components/MetricCard';
import { getHealth, getProducts } from '../../lib/api';
import { formatPrice, formatText } from '../../lib/format';

export default async function ImportReviewPage() {
  const [health, products] = await Promise.all([getHealth(), getProducts()]);

  const missingCategory = products.filter((product) => !product.category || !product.subcategory).length;
  const missingSource = products.filter((product) => !product.source || !product.source_retailer).length;
  const missingPrice = products.filter((product) => {
    const pricing = product.pricing ?? product.pricing_summary ?? {};
    return typeof pricing.best_price !== 'number';
  }).length;

  const sourceCounts = products.reduce<Record<string, number>>((counts, product) => {
    const key = product.source_retailer || product.source || 'Unknown';
    counts[key] = (counts[key] || 0) + 1;
    return counts;
  }, {});

  return (
    <AppShell>
      <header className="page-header">
        <div>
          <p className="eyebrow">Quality</p>
          <h1>Import review</h1>
        </div>
      </header>

      <div className="metrics-grid">
        <MetricCard label="API" value={health.status} />
        <MetricCard label="Products" value={products.length} />
        <MetricCard label="Missing category" value={missingCategory} />
        <MetricCard label="Missing price" value={missingPrice} />
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Import sources</h2>
        </div>
        <div className="panel-body">
          <ul className="quiet-list">
            {Object.entries(sourceCounts).map(([source, count]) => (
              <li key={source}>
                <span>{source}</span>
                <strong>{count}</strong>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Review queue</h2>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Source</th>
                <th>Best price</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {products
                .filter((product) => {
                  const pricing = product.pricing ?? product.pricing_summary ?? {};
                  return !product.category || !product.subcategory || !product.source || !product.source_retailer || typeof pricing.best_price !== 'number';
                })
                .map((product) => {
                  const pricing = product.pricing ?? product.pricing_summary ?? {};
                  const issue = !product.category || !product.subcategory
                    ? 'Category'
                    : !product.source || !product.source_retailer
                      ? 'Source'
                      : 'Price';

                  return (
                    <tr key={product.barcode}>
                      <td>
                        {product.name}
                        <span>{product.barcode}</span>
                      </td>
                      <td>
                        {formatText(product.category)} / {formatText(product.subcategory)}
                      </td>
                      <td>{formatText(product.source_retailer || product.source)}</td>
                      <td>{formatPrice(pricing.best_price)}</td>
                      <td>{issue}</td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Summary</h2>
        </div>
        <div className="panel-body">
          <ul className="quiet-list">
            <li>
              <span>Missing source</span>
              <strong>{missingSource}</strong>
            </li>
            <li>
              <span>Missing category</span>
              <strong>{missingCategory}</strong>
            </li>
            <li>
              <span>Missing price</span>
              <strong>{missingPrice}</strong>
            </li>
          </ul>
        </div>
      </section>
    </AppShell>
  );
}
