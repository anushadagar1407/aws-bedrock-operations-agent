import { Evidence } from '../lib/api';

export function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  if (!evidence.length) return null;
  return (
    <section className="panel">
      <h2>Evidence</h2>
      <ul>
        {evidence.map((item, index) => (
          <li key={`${item.source_id}-${item.field}-${index}`}>
            <strong>{item.field}</strong>: {item.value} <span>({item.source_id})</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
