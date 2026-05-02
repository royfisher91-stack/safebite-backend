import { safetyClass } from '../lib/format';

type Props = {
  value?: string | null;
};

export default function StatusBadge({ value }: Props) {
  const tone = safetyClass(value);

  return <span className={`status-badge status-badge-${tone}`}>{value || 'Unknown'}</span>;
}
