import { AgentQuery } from '../components/AgentQuery';

export default function Home() {
  return (
    <main className="shell">
      <header>
        <p className="eyebrow">AWS BEDROCK OPERATIONS AGENT</p>
        <h1>Container status with evidence attached.</h1>
        <p className="lede">Ask a question and the agent checks structured records, source reports, and validation rules before answering.</p>
      </header>
      <AgentQuery />
      <section className="info-grid">
        <article><strong>Grounded answers</strong><span>Every answer carries source evidence and an audit ID.</span></article>
        <article><strong>Human review</strong><span>Conflicting records produce an exception instead of a guess.</span></article>
        <article><strong>Event driven</strong><span>Reports are processed asynchronously with retries and alerts.</span></article>
      </section>
    </main>
  );
}
