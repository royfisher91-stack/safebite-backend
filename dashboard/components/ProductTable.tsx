import Link from 'next/link';
import { Product } from '../lib/api';
import { formatPrice, formatText } from '../lib/format';
import StatusBadge from './StatusBadge';

type Props = {
  products: Product[];
};

export default function ProductTable({ products }: Props) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Barcode</th>
            <th>Category</th>
            <th>Safety</th>
            <th>Best price</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => {
            const pricing = product.pricing ?? product.pricing_summary ?? {};

            return (
              <tr key={product.barcode}>
                <td>
                  <Link className="table-link" href={`/products/${product.barcode}`}>
                    {product.name}
                  </Link>
                  <span>{formatText(product.brand, 'Unbranded')}</span>
                </td>
                <td>{product.barcode}</td>
                <td>
                  {formatText(product.category)} / {formatText(product.subcategory)}
                </td>
                <td>
                  <StatusBadge value={product.safety_result} />
                </td>
                <td>
                  {formatPrice(pricing.best_price)}
                  <span>{formatText(pricing.cheapest_retailer, 'No retailer')}</span>
                </td>
                <td>{formatText(product.source_retailer || product.source)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
