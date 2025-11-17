/**
 * API Client for Backend Communication
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AnalyzeRequest {
  brand_name: string;
  website_url: string;
  query_count?: number;
}

export interface JobStatus {
  job_id: string;
  brand_name: string;
  website_url: string;
  industry: string | null;
  status: string;
  progress: number;
  overall_score: number | null;
  mention_rate: number | null;
  total_queries: number | null;
  total_mentions: number | null;
  created_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface Report {
  job_id: string;
  brand_name: string;
  industry: string;
  overall_score: number;
  visibility_breakdown: any;
  results: any[];
  top_competitors: Array<{ name: string; mentions: number }>;
  model_breakdown: any;
  category_breakdown: any;
}

export const api = {
  /**
   * Start brand visibility analysis
   */
  async startAnalysis(data: AnalyzeRequest): Promise<{ job_id: string; status: string; message: string }> {
    const response = await apiClient.post('/analyze', data);
    return response.data;
  },

  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await apiClient.get(`/status/${jobId}`);
    return response.data;
  },

  /**
   * Get full report
   */
  async getReport(jobId: string): Promise<Report> {
    const response = await apiClient.get(`/report/${jobId}`);
    return response.data;
  },

  /**
   * Get download URL
   */
  getDownloadUrl(jobId: string, format: 'excel' | 'csv'): string {
    return `${API_BASE_URL}/download/${jobId}/${format}`;
  },

  /**
   * List recent jobs
   */
  async listJobs(limit: number = 20): Promise<JobStatus[]> {
    const response = await apiClient.get(`/jobs?limit=${limit}`);
    return response.data;
  },
};

export default api;
