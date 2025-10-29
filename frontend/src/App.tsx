import { useState } from "react";
import ProviderSearch from "./components/ProviderSearch";
import RulesPanel from "./components/RulesPanel";

type Provider = { provider_id: string; name: string };

export default function App() {
  const [provider, setProvider] = useState<Provider | null>(null);

  return (
    <div className="min-h-screen bg-gray-100 text-gray-900">
      <header className="py-8 text-center text-2xl font-bold">Provider Rules RAG</header>

      <main className="px-4">
        <ProviderSearch onSelect={(p) => setProvider(p)} />

        <div className="mt-8">
          <RulesPanel providerId={provider?.provider_id ?? null} />
        </div>
      </main>
    </div>
  );
}
