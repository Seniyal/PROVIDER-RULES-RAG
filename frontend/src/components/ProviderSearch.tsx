import { useEffect, useMemo, useState } from "react";

type Provider = {
  provider_id: string;
  name: string;
  specialty?: string | null;
  npi?: string | null;
};

export default function ProviderSearch({
  onSelect,
}: {
  onSelect: (p: Provider) => void;
}) {
  const [q, setQ] = useState("");
  const [opts, setOpts] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedQ = useMemo(() => q.trim(), [q]);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setError(null);

      // if the box is empty, load full list
      if (!debouncedQ) {
        setLoading(true);
        try {
          const r = await fetch("/api/ehr/providers");
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const data = await r.json(); // { providers: [...] }
          if (!cancelled) setOpts(data.providers ?? []);
        } catch (e: any) {
          if (!cancelled) setError(e.message || "Failed to load providers");
        } finally {
          if (!cancelled) setLoading(false);
        }
        return;
      }

      // if user typed something, search
      setLoading(true);
      try {
        const r = await fetch(`/api/ehr/providers/search?q=${encodeURIComponent(debouncedQ)}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) setOpts(data.providers ?? []);
      } catch (e: any) {
        if (!cancelled) setError(e.message || "Failed to search providers");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    run();
    return () => { cancelled = true; };
  }, [debouncedQ]);

  return (
    <div className="max-w-2xl mx-auto">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search providers (name, specialty, NPI)…"
        className="w-full border rounded-xl px-4 py-3 outline-none"
      />

      {error && <div className="text-red-600 mt-2">Error: {error}</div>}

      <div className="mt-3 grid gap-2">
        {loading && <div className="text-gray-500">Loading…</div>}
        {!loading && opts.length === 0 && (
          <div className="text-gray-500">No providers.</div>
        )}

        {opts.map((p) => (
          <button
            key={p.provider_id}
            onClick={() => onSelect(p)}
            className="text-left border rounded-xl px-4 py-3 hover:bg-gray-50"
          >
            <div className="font-medium">{p.name}</div>
            <div className="text-sm text-gray-600">
              {p.specialty || "—"} • {p.npi || "NPI —"} • {p.provider_id}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
