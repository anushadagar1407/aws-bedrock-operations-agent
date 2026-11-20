export function AuditTimeline({ trace }: { trace: string[] }) {
  if (!trace.length) return null;
  return (
    <section className="panel">
      <h2>Tool trace</h2>
      <ol>
        {trace.map((step, index) => <li key={`${step}-${index}`}>{step}</li>)}
      </ol>
    </section>
  );
}
