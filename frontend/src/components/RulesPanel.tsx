import { useState } from 'react'

interface Rule {
  id: string
  title: string
  content: string
  provider?: string
  category?: string
}

export default function RulesPanel() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Rule[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/v1/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error('Failed to search rules')
      }

      const data = await response.json()
      setResults(data.results || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          Search Provider Rules
        </h2>
        <div className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter your search query..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-lg">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
            Results ({results.length})
          </h3>
          <div className="space-y-4">
            {results.map((rule) => (
              <div
                key={rule.id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-lg font-medium text-gray-900 dark:text-white">
                    {rule.title}
                  </h4>
                  <div className="flex gap-2">
                    {rule.provider && (
                      <span className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                        {rule.provider}
                      </span>
                    )}
                    {rule.category && (
                      <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
                        {rule.category}
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-gray-700 dark:text-gray-300">{rule.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && query && !error && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No results found. Try a different search query.
        </div>
      )}
    </div>
  )
}

