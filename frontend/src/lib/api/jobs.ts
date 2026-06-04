// Job Description API client — mirrors the resumes.ts pattern exactly
import { getToken } from "../tokenStore";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

// ── Types ─────────────────────────────────────────────────────────────────

/** Lightweight item used in list responses (no description text). */
export interface JobDescriptionListItem {
  id: string;
  user_id: string;
  title: string;
  company: string | null;
  created_at: string;
  updated_at: string;
}

/** Full record returned on create / detail fetch. */
export interface JobDescriptionDetail extends JobDescriptionListItem {
  description: string;
}

export interface CreateJobDescriptionPayload {
  title: string;
  company: string | null;
  description: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────

function authHeaders(): HeadersInit {
  const token = getToken();
  return token
    ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── API object ────────────────────────────────────────────────────────────

export const jobsApi = {
  /** POST /api/v1/jobs — create a new Job Description */
  async create(
    payload: CreateJobDescriptionPayload,
  ): Promise<JobDescriptionDetail> {
    const res = await fetch(`${API_BASE}/jobs/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    return handleResponse<JobDescriptionDetail>(res);
  },

  /** GET /api/v1/jobs — list all Job Descriptions for the current user */
  async list(): Promise<JobDescriptionListItem[]> {
    const res = await fetch(`${API_BASE}/jobs/`, {
      headers: authHeaders(),
    });
    return handleResponse<JobDescriptionListItem[]>(res);
  },

  /** GET /api/v1/jobs/{id} — fetch a single Job Description with full text */
  async get(id: string): Promise<JobDescriptionDetail> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      headers: authHeaders(),
    });
    return handleResponse<JobDescriptionDetail>(res);
  },

  /** DELETE /api/v1/jobs/{id} — delete a Job Description */
  async delete(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? "Failed to delete job description");
    }
  },
};
