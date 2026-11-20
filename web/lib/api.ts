export type Evidence = {
  source_type: string;
  source_id: string;
  field: string;
  value: string;
  observed_at: string;
};

export type AgentResponse = {
  answer: string;
  status: string;
  confidence: number;
  evidence: Evidence[];
  requires_review: boolean;
  audit_id: string;
  tool_trace: string[];
};

export async function queryAgent(query: string): Promise<AgentResponse> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  const response = await fetch(`${base.replace(/\/$/, '')}/agent`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!response.ok) throw new Error(`Agent request failed with ${response.status}`);
  return response.json() as Promise<AgentResponse>;
}
