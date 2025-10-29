import { useState } from 'react'
import RulesPanel from './components/RulesPanel'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Provider Rules RAG
          </h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-8">
        <RulesPanel />
      </main>
    </div>
  )
}

export default App

