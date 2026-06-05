import { apiClient as api } from "../axios";

export interface ApplicationStatusHistory {
  id: string;
  application_id: string;
  old_status: string | null;
  new_status: string;
  changed_at: string;
  changed_by: string | null;
}

export interface JobApplication {
  id: string;
  user_id: string;
  resume_id: string | null;
  job_id: string | null;
  company_name: string;
  job_title: string;
  job_url: string | null;
  source: string | null;
  status: string;
  priority: string;
  application_date: string;
  next_interview_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  status_history: ApplicationStatusHistory[];
}

export interface JobApplicationCreate {
  company_name: string;
  job_title: string;
  job_url?: string;
  source?: string;
  status?: string;
  priority?: string;
  application_date: string;
  next_interview_date?: string;
  notes?: string;
  resume_id?: string;
  job_id?: string;
}

export interface JobApplicationUpdate {
  company_name?: string;
  job_title?: string;
  job_url?: string;
  source?: string;
  status?: string;
  priority?: string;
  application_date?: string;
  next_interview_date?: string;
  notes?: string;
  resume_id?: string;
  job_id?: string;
}

export interface MonthlyTrend {
  m: string;
  v: number;
}

export interface RecentActivity {
  icon: string;
  title: string;
  time: string;
  tag: string;
}

export interface RoleResponseRate {
  k: string;
  v: number;
}

export interface UpcomingInterview {
  d: string;
  t: string;
  time: string;
}

export interface ApplicationMetrics {
  total_applications: number;
  active_applications: number;
  total_interviews: number;
  total_offers: number;
  interview_rate: number;
  offer_rate: number;
  mom_growth_rate: number;
  monthly_trend: MonthlyTrend[];
  recent_activity: RecentActivity[];
  role_response_rates: RoleResponseRate[];
  upcoming_interviews: UpcomingInterview[];
}

export interface RecommendedAction {
  action: string;
  impact: string;
}

export interface DashboardInsight {
  insight_text: string;
  recommended_actions: RecommendedAction[];
}

export const applicationsApi = {
  list: async (): Promise<{ applications: JobApplication[] }> => {
    const response = await api.get("/applications");
    return response.data;
  },

  get: async (id: string): Promise<JobApplication> => {
    const response = await api.get(`/applications/${id}`);
    return response.data;
  },

  create: async (data: JobApplicationCreate): Promise<JobApplication> => {
    const response = await api.post("/applications", data);
    return response.data;
  },

  update: async (
    id: string,
    data: JobApplicationUpdate,
  ): Promise<JobApplication> => {
    const response = await api.patch(`/applications/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/applications/${id}`);
  },

  getMetrics: async (): Promise<ApplicationMetrics> => {
    const response = await api.get("/applications/metrics");
    return response.data;
  },

  getInsights: async (): Promise<DashboardInsight> => {
    const response = await api.get("/applications/insights");
    return response.data;
  },
};
