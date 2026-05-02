type Props = {
  label: string;
  value: string | number;
  detail?: string;
};

export default function MetricCard({ label, value, detail }: Props) {
  return (
    <section className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
      {detail ? <span>{detail}</span> : null}
    </section>
  );
}
