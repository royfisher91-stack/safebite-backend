import AppShell from '../../components/AppShell';
import MetricCard from '../../components/MetricCard';
import ProductTable from '../../components/ProductTable';
import { getProducts, Product } from '../../lib/api';

type Props = {
  searchParams?: Promise<{
    q?: string;
  }>;
};

export default async function ProductsPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = params?.q || '';
  let products: Product[] = [];
  let error = '';

  try {
    products = await getProducts(query);
  } catch (caught) {
    error = caught instanceof Error ? caught.message : 'Unable to load products';
  }

  const categories = new Set(products.map((product) => product.category).filter(Boolean));
  const retailers = new Set(
    products
      .map((product) => product.pricing?.cheapest_retailer || product.pricing_summary?.cheapest_retailer)
      .filter(Boolean),
  );
  const cautionCount = products.filter((product) => product.safety_result === 'Caution').length;

  return (
    <AppShell>
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Products</h1>
        </div>
        <form className="search-form">
          <input
            className="input"
            defaultValue={query}
            name="q"
            placeholder="Search products or barcode"
            type="search"
          />
          <button className="button" type="submit">
            Search
          </button>
        </form>
      </header>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="metrics-grid">
        <MetricCard label="Products" value={products.length} />
        <MetricCard label="Categories" value={categories.size} />
        <MetricCard label="Retailers" value={retailers.size} />
        <MetricCard label="Caution" value={cautionCount} />
      </div>

      <section className="panel">
        <div className="panel-header">
          <h2>Catalogue</h2>
        </div>
        <ProductTable products={products} />
      </section>
    </AppShell>
  );
}
