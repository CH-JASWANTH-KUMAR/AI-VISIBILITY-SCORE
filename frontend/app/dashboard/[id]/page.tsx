'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type JobStatus, type Report } from '../../../lib/api';
import ScoreCard from '../../../components/ScoreCard';
import QueryTable from '../../../components/QueryTable';
import ModelComparison from '../../../components/ModelComparison';
import CategoryChart from '../../../components/CategoryChart';

export default function Dashboard() {
  const params = useParams();
  const jobId = params.id as string;

  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const status = await api.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed') {
          // Fetch full report
          const reportData = await api.getReport(jobId);
          setReport(reportData);
          setLoading(false);
          clearInterval(interval);
        } else if (status.status === 'failed') {
          setError(status.error_message || 'Analysis failed');
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch status');
        setLoading(false);
      }
    };

    fetchStatus();
    interval = setInterval(fetchStatus, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [jobId]);

  const downloadReport = (format: 'excel' | 'csv') => {
    const url = api.getDownloadUrl(jobId, format);
    window.open(url, '_blank');
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => (window.location.href = '/')}
            className="mt-6 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700"
          >
            Start New Analysis
          </button>
        </div>
      </div>
    );
  }

  if (loading || !jobStatus || jobStatus.status !== 'completed' || !report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="bg-white rounded-xl shadow-lg p-12 max-w-2xl w-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {jobStatus?.brand_name ? `Analyzing ${jobStatus.brand_name}` : 'Processing...'}
            </h2>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${jobStatus?.progress || 0}%` }}
              ></div>
            </div>
            <p className="text-gray-600 mb-8">{jobStatus?.progress || 0}% complete</p>

            {/* Status Steps */}
            <div className="text-left space-y-3">
              <div className={`flex items-center ${(jobStatus?.progress ?? 0) >= 15 ? 'text-green-600' : 'text-gray-400'}`}>
                <span className="mr-3">{(jobStatus?.progress ?? 0) >= 15 ? '✓' : '○'}</span>
                <span>Detecting industry...</span>
              </div>
              <div className={`flex items-center ${(jobStatus?.progress ?? 0) >= 25 ? 'text-green-600' : 'text-gray-400'}`}>
                <span className="mr-3">{(jobStatus?.progress ?? 0) >= 25 ? '✓' : '○'}</span>
                <span>Generating queries...</span>
              </div>
              <div className={`flex items-center ${(jobStatus?.progress ?? 0) >= 50 ? 'text-green-600' : 'text-gray-400'}`}>
                <span className="mr-3">{(jobStatus?.progress ?? 0) >= 50 ? '✓' : '○'}</span>
                <span>Testing AI models...</span>
              </div>
              <div className={`flex items-center ${(jobStatus?.progress ?? 0) >= 100 ? 'text-green-600' : 'text-gray-400'}`}>
                <span className="mr-3">{(jobStatus?.progress ?? 0) >= 100 ? '✓' : '○'}</span>
                <span>Calculating scores...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            {report.brand_name} - Visibility Report
          </h1>
          <p className="text-gray-600">Industry: {report.industry}</p>
        </div>

        {/* Score Card */}
        <ScoreCard
          score={report.overall_score}
          visibilityBreakdown={report.visibility_breakdown}
        />

        {/* Model Comparison & Category Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ModelComparison modelBreakdown={report.model_breakdown} />
          <CategoryChart categoryBreakdown={report.category_breakdown} />
        </div>

        {/* Top Competitors */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top Competitors</h2>
          <div className="space-y-3">
            {report.top_competitors.slice(0, 5).map((comp, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="text-gray-700">
                  {idx + 1}. {comp.name}
                </span>
                <span className="text-sm text-gray-500">
                  {comp.mentions} mentions
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Download Buttons */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Download Report</h2>
          <div className="flex gap-4">
            <button
              onClick={() => downloadReport('excel')}
              className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition"
            >
              📊 Download Excel
            </button>
            <button
              onClick={() => downloadReport('csv')}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition"
            >
              📄 Download CSV
            </button>
          </div>
        </div>

        {/* Query Table */}
        <QueryTable results={report.results} />
      </div>
    </div>
  );
}
