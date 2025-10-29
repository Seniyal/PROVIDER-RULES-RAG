import { useEffect, useState } from "react";

type Rule = {
  rule_id: string;
  title?: string | null;
  body: string;
  steps?: string[] | null;
  tags?: string[];
  source?: { doc_id?: string; doc_url?: string | null; page?: number | null; version?: string | null };
  last_updated?: string | null;
};

export default function RulesPanel({ providerId }: { providerId: string | null }) {
  const [rules, setRules] = useState<Rule[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!providerId) { setRules(null); return; }
    setLoading(true);
    setError(null);
    
    console.log('providerId =', providerId);
    const url = `/api/providers/${providerId}/rules`;
    console.log("Fetching", url);

    fetch(url)
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json(); // { provider_id, provider_name, rules: [...] }
        setRules(Array.isArray(data?.rules) ? data.rules : []);
      })
      .catch((e) => setError(e.message || "Failed to fetch"))
      .finally(() => setLoading(false));
  }, [providerId]);

  if (!providerId) return <div className="text-center text-gray-500">Select a provider…</div>;
  if (loading) return <div className="text-center">Loading rules…</div>;
  if (error) return <div className="text-center text-red-600">Error: {error}</div>;
  if (!rules || rules.length === 0) return <div className="text-center">No rules found for this provider.</div>;

  return (
    <div className="max-w-3xl mx-auto mt-6 space-y-4">
      {rules.map((r) => (
        <div key={r.rule_id} className="rounded-xl border px-5 py-4">
          <div className="font-semibold">{r.title || "Rule"}</div>
          {r.steps?.length ? (
            <ol className="list-decimal ml-5 mt-2 space-y-1">
              {r.steps.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          ) : (
            <p className="mt-2 whitespace-pre-wrap">{r.body}</p>
          )}
          {r.source?.doc_url && (
            <a className="text-blue-600 underline mt-2 inline-block" href={r.source.doc_url} target="_blank" rel="noreferrer">
              View source
            </a>
          )}
        </div>
      ))}
    </div>
  );
}
