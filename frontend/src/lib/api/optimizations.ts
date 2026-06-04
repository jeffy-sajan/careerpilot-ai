// Optimizations API client
import { getToken } from "../tokenStore";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export type OptimizationStatus = "PENDING" | "ACCEPTED" | "REJECTED";
export type OptimizationType =
  | "KEYWORD"
  | "BULLET_REWRITE"
  | "SKILL_ADDITION"
  | "SUMMARY_IMPROVEMENT"
  | "ATS_FIX";

export interface OptimizationResponse {
  id: string;
  run_id: string;
  optimization_type: OptimizationType;
  section: string;
  original_text: string;
  suggested_text: string;
  reasoning: string;
  status: OptimizationStatus;
  created_at: string;
  updated_at: string;
}

export interface OptimizationRunResponse {
  id: string;
  resume_id: string;
  job_description_id: string | null;
  model_name: string;
  prompt_version: string;
  created_at: string;
  updated_at: string;
  suggestions: OptimizationResponse[];
}

export interface OptimizationListResponse {
  optimizations: OptimizationResponse[];
  total_count: number;
}

export interface PromptResponse {
  prompt: string;
  model_name: string;
  response_schema: Record<string, unknown>;
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const optimizationsApi = {
  /** POST /resumes/{resumeId}/optimize — uses platform key */
  async generate(
    resumeId: string,
    jobId?: string,
  ): Promise<OptimizationRunResponse> {
    const url = jobId
      ? `${API_BASE}/resumes/${resumeId}/optimize?job_id=${jobId}`
      : `${API_BASE}/resumes/${resumeId}/optimize`;

    const res = await fetch(url, {
      method: "POST",
      headers: authHeaders(),
    });
    return handleResponse<OptimizationRunResponse>(res);
  },

  /** GET /resumes/{resumeId}/optimize/prompt — fetch prompt for BYOK */
  async getPrompt(resumeId: string, jobId?: string): Promise<PromptResponse> {
    const url = jobId
      ? `${API_BASE}/resumes/${resumeId}/optimize/prompt?job_id=${jobId}`
      : `${API_BASE}/resumes/${resumeId}/optimize/prompt`;

    const res = await fetch(url, {
      headers: authHeaders(),
    });
    return handleResponse<PromptResponse>(res);
  },

  /** POST /resumes/{resumeId}/optimize/save — persist BYOK results */
  async saveByok(
    resumeId: string,
    suggestions: Record<string, unknown>[],
    jobId?: string,
  ): Promise<OptimizationRunResponse> {
    const url = jobId
      ? `${API_BASE}/resumes/${resumeId}/optimize/save?job_id=${jobId}`
      : `${API_BASE}/resumes/${resumeId}/optimize/save`;

    const res = await fetch(url, {
      method: "POST",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model_name: "gemini-2.5-flash",
        prompt_version: "v1.0-byok",
        suggestions,
      }),
    });
    return handleResponse<OptimizationRunResponse>(res);
  },

  /** GET /resumes/{resumeId}/optimizations */
  async listForResume(resumeId: string): Promise<OptimizationListResponse> {
    const res = await fetch(`${API_BASE}/resumes/${resumeId}/optimizations`, {
      headers: authHeaders(),
    });
    return handleResponse<OptimizationListResponse>(res);
  },

  /** PATCH /optimizations/{id}/status */
  async updateStatus(
    optimizationId: string,
    status: OptimizationStatus,
  ): Promise<OptimizationResponse> {
    const res = await fetch(
      `${API_BASE}/optimizations/${optimizationId}/status`,
      {
        method: "PATCH",
        headers: {
          ...authHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status }),
      },
    );
    return handleResponse<OptimizationResponse>(res);
  },
};
