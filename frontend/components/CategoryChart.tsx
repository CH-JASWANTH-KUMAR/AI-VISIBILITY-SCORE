'use client';

interface CategoryChartProps {
  categoryBreakdown: Record<string, any>;
}

export default function CategoryChart({ categoryBreakdown }: CategoryChartProps) {
  const categories = Object.entries(categoryBreakdown || {});

  if (categories.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Score by Query Category</h2>
      <div className="space-y-4">
        {categories.map(([category, data]: [string, any]) => {
          const score = data.overall_score || 0;
          const maxScore = 100;

          return (
            <div key={category}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">{category}</span>
                <span className="text-sm font-semibold text-gray-900">
                  {score.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${
                    score >= 80
                      ? 'bg-green-600'
                      : score >= 60
                      ? 'bg-blue-600'
                      : score >= 40
                      ? 'bg-yellow-600'
                      : 'bg-red-600'
                  }`}
                  style={{ width: `${(score / maxScore) * 100}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {data.mentions || 0} mentions out of {data.total_queries || 0} queries
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
