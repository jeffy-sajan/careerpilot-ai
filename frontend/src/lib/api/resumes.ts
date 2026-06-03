// Resume API client — talks to the CareerPilot backend
import { getToken } from "../../lib/tokenStore";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export interface ResumeListItem {
  id: string;
  user_id: string;
  original_file_name: string;
  content_type: string;
  file_size_bytes: number;
  status: "UPLOADED" | "PROCESSING" | "COMPLETED" | "FAILED";
  error_message: string | null;
  file_url: string;
  created_at: string;
  updated_at: string;
}

export interface ATSAnalysis {
  id: string;
  resume_id: string;
  ats_score: number;
  strengths: string[] | null;
  weaknesses: string[] | null;
  recommendations: string[] | null;
  keyword_analysis: Record<string, string> | null;
  created_at: string;
  updated_at: string;
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const resumeApi = {
  async upload(file: File): Promise<ResumeListItem> {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/resumes/`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? "Upload failed");
    }
    return res.json();
  },

  async list(): Promise<ResumeListItem[]> {
    const res = await fetch(`${API_BASE}/resumes/`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch resumes");
    return res.json();
  },

  async delete(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/resumes/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete resume");
  },

  async analyze(id: string): Promise<ATSAnalysis> {
    const res = await fetch(`${API_BASE}/resumes/${id}/analyze`, {
      method: "POST",
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Failed to start analysis");
    return res.json();
  },

  async getAnalysis(id: string): Promise<ATSAnalysis> {
    const res = await fetch(`${API_BASE}/resumes/${id}/analysis`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Failed to fetch analysis");
    return res.json();
  },
};
