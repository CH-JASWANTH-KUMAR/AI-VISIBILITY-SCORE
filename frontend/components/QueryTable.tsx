'use client';

import { useState } from 'react';

interface QueryTableProps {
  results: any[];
}

export default function QueryTable({ results }: QueryTableProps) {
  const [filter, setFilter] = useState('all');
  const [modelFilter, setModelFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  // Get unique models
  const models = ['all', ...Array.from(new Set(results.map((r) => r.model)))];

  // Filter results
  const filteredResults = results.filter((result) => {
    const matchesFilter =
      filter === 'all' ||
      (filter === 'mentioned' && result.brand_mentioned) ||
      (filter === 'not-mentioned' && !result.brand_mentioned);

    const matchesModel = modelFilter === 'all' || result.model === modelFilter;

    const matchesSearch =
      !searchTerm ||
      result.query_text.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesFilter && matchesModel && matchesSearch;
  });

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Full Query Transparency</h2>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mention Status
          </label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Queries</option>
            <option value="mentioned">Mentioned Only</option>
            <option value="not-mentioned">Not Mentioned</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
          <select
            value={modelFilter}
            onChange={(e) => setModelFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {models.map((model) => (
              <option key={model} value={model}>
                {model === 'all' ? 'All Models' : model}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search queries..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Showing {filteredResults.length} of {results.length} results
      </p>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Query
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Model
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mentioned
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rank
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Competitors
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Details
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredResults.map((result, idx) => (
              <>
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm text-gray-900">
                    {result.query_text}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {result.model}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    {result.brand_mentioned ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                        Yes
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
                        No
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-900">
                    {result.brand_rank || '-'}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {result.competitor_count || 0}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <button
                      onClick={() =>
                        setExpandedRow(expandedRow === idx ? null : idx)
                      }
                      className="text-blue-600 hover:text-blue-800"
                    >
                      {expandedRow === idx ? 'Hide' : 'View'}
                    </button>
                  </td>
                </tr>
                {expandedRow === idx && (
                  <tr>
                    <td colSpan={6} className="px-4 py-4 bg-gray-50">
                      <div className="text-sm">
                        <div className="mb-2">
                          <span className="font-semibold">Full Response:</span>
                          <p className="mt-1 text-gray-700 whitespace-pre-wrap">
                            {result.full_response}
                          </p>
                        </div>
                        {result.competitors && result.competitors.length > 0 && (
                          <div className="mt-3">
                            <span className="font-semibold">Competitors Found:</span>
                            <p className="mt-1 text-gray-700">
                              {result.competitors.join(', ')}
                            </p>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
