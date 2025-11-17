'use client';

interface ModelComparisonProps {
  modelBreakdown: Record<string, any>;
}

export default function ModelComparison({ modelBreakdown }: ModelComparisonProps) {
  const models = Object.entries(modelBreakdown || {});

  if (models.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Mention Rate by Model</h2>
      <div className="space-y-4">
        {models.map(([model, data]: [string, any]) => {
          const mentionRate =
            data.total_queries > 0
              ? (data.mentions / data.total_queries) * 100
              : 0;

          return (
            <div key={model}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">{model}</span>
                <span className="text-sm font-semibold text-gray-900">
                  {mentionRate.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${mentionRate}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {data.mentions} mentions out of {data.total_queries} queries
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
