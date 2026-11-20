'use client';

import { FormEvent, useState } from 'react';
import React from 'react';
import { AgentResponse, queryAgent } from '../lib/api';

export function AgentQuery() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      setResponse(await queryAgent(query.trim()));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'The agent request failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="query-card">
      <form onSubmit={submit}>
        <label htmlFor="container-question">Container question</label>
        <textarea
          id="container-question"
          aria-label="Container question"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="What is the status of ABC123?"
          rows={3}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Checking...' : 'Check status'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      {response && (
        <div className="result" aria-live="polite">
          <div className="result-heading">
            <span className={`status status-${response.status}`}>{response.status}</span>
            <span>{Math.round(response.confidence * 100)}% confidence</span>
          </div>
          <p>{response.answer}</p>
          {response.requires_review && <p className="review">Manual review is required.</p>}
          <p className="audit">Audit ID: {response.audit_id}</p>
        </div>
      )}
    </section>
  );
}
