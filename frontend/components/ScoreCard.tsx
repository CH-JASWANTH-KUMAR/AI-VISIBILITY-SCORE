'use client';

interface ScoreCardProps {
  score: number;
  visibilityBreakdown: {
    overall_score: number;
    mention_rate: number;
    rank_score: number;
    competitor_dominance: number;
    model_consistency: number;
    mentions: number;
    total_queries: number;
  };
}

export default function ScoreCard({ score, visibilityBreakdown }: ScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    if (score >= 30) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreInterpretation = (score: number) => {
    if (score >= 90) return 'Dominant Presence';
    if (score >= 70) return 'Strong Visibility';
    if (score >= 50) return 'Moderate Visibility';
    if (score >= 30) return 'Low Visibility';
    return 'Minimal Visibility';
  };

  const getProgressWidth = (score: number) => {
    return `${score}%`;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      {/* Overall Score */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Overall Visibility Score</h2>
        <div className={`text-7xl font-bold ${getScoreColor(score)} mb-2`}>
          {score.toFixed(1)}
        </div>
        <div className="text-xl text-gray-600 mb-4">{getScoreInterpretation(score)}</div>

        {/* Progress Bar */}
        <div className="w-full max-w-2xl mx-auto bg-gray-200 rounded-full h-4 mb-6">
          <div
            className={`h-4 rounded-full transition-all duration-1000 ${
              score >= 90
                ? 'bg-green-600'
                : score >= 70
                ? 'bg-blue-600'
                : score >= 50
                ? 'bg-yellow-600'
                : score >= 30
                ? 'bg-orange-600'
                : 'bg-red-600'
            }`}
            style={{ width: getProgressWidth(score) }}
          ></div>
        </div>

        <p className="text-gray-600">
          Mentioned in <span className="font-semibold">{visibilityBreakdown.mentions}</span> out of{' '}
          <span className="font-semibold">{visibilityBreakdown.total_queries}</span> queries
        </p>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {visibilityBreakdown.mention_rate.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Mention Rate</div>
          <div className="text-xs text-gray-500">out of 40</div>
        </div>

        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {visibilityBreakdown.rank_score.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Rank Score</div>
          <div className="text-xs text-gray-500">out of 30</div>
        </div>

        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {visibilityBreakdown.competitor_dominance.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Competitor Edge</div>
          <div className="text-xs text-gray-500">out of 20</div>
        </div>

        <div className="text-center">
          <div className="text-3xl font-bold text-gray-900 mb-1">
            {visibilityBreakdown.model_consistency.toFixed(1)}
          </div>
          <div className="text-sm text-gray-600">Consistency</div>
          <div className="text-xs text-gray-500">out of 10</div>
        </div>
      </div>
    </div>
  );
}
