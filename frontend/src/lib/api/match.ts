// Match API client
import { getToken } from "../tokenStore";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export interface ResumeMatchResult {
  id: string;
  resume_id: string;
  job_description_id: string;
  match_score: number;
  matched_skills: string[] | null;
  missing_skills: string[] | null;
  missing_keywords: string[] | null;
  suggestions: string[] | null;
  created_at: string;
  updated_at: string;
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

export const matchApi = {
  /** POST /resumes/{resumeId}/match/{jobId} — run matching and store results */
  async generate(resumeId: string, jobId: string): Promise<ResumeMatchResult> {
    const res = await fetch(`${API_BASE}/resumes/${resumeId}/match/${jobId}`, {
      method: "POST",
      headers: authHeaders(),
    });
    return handleResponse<ResumeMatchResult>(res);
  },

  /** GET /resumes/{resumeId}/match/{jobId} — fetch existing match result */
  async get(resumeId: string, jobId: string): Promise<ResumeMatchResult> {
    const res = await fetch(`${API_BASE}/resumes/${resumeId}/match/${jobId}`, {
      headers: authHeaders(),
    });
    return handleResponse<ResumeMatchResult>(res);
  },
};
