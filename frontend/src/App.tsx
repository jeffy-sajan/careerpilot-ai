import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { PublicRoute } from "./routes/PublicRoute";
import AuthLayout from "./layouts/AuthLayout";
import AppLayout from "./layouts/AppLayout";

// Auth pages
import LoginPage from "./features/auth/pages/LoginPage";
import RegisterPage from "./features/auth/pages/RegisterPage";
import GoogleCallbackPage from "./features/auth/pages/GoogleCallbackPage";
import ForgotPasswordPage from "./features/auth/pages/ForgotPasswordPage";
import ResetPasswordPage from "./features/auth/pages/ResetPasswordPage";

// App pages
import ResumeAnalyzerPage from "./features/resume/pages/ResumeAnalyzerPage";
import ResumeAnalysisPage from "./features/resume/pages/ResumeAnalysisPage";
import JobDescriptionListPage from "./features/jobs/pages/JobDescriptionListPage";
import JobDescriptionCreatePage from "./features/jobs/pages/JobDescriptionCreatePage";
import JobDescriptionDetailPage from "./features/jobs/pages/JobDescriptionDetailPage";
import MatchDashboardPage from "./features/match/pages/MatchDashboardPage";

// Placeholder for not-yet-built pages
const ComingSoon = ({ page }: { page: string }) => (
  <div className="flex flex-1 items-center justify-center min-h-screen">
    <div className="text-center space-y-3">
      <p className="eyebrow">Coming soon</p>
      <h1 className="font-display text-3xl text-foreground">{page}</h1>
      <p className="text-sm text-muted-foreground max-w-xs">
        This section is under construction and will be available in a future
        phase.
      </p>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* ── Public Routes ── */}
          <Route element={<PublicRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
            </Route>
          </Route>

          {/* ── Google OAuth Callback ── */}
          <Route
            path="/auth/google/callback"
            element={<GoogleCallbackPage />}
          />

          {/* ── Protected Routes with App Shell ── */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route
                path="/dashboard"
                element={<ComingSoon page="Dashboard" />}
              />
              <Route path="/resume-analyzer" element={<ResumeAnalyzerPage />} />
              <Route
                path="/resume-analyzer/:id/analysis"
                element={<ResumeAnalysisPage />}
              />
              <Route
                path="/ats-analysis"
                element={<ComingSoon page="ATS Analysis" />}
              />
              <Route path="/jd-matcher" element={<JobDescriptionListPage />} />
              <Route
                path="/jd-matcher/new"
                element={<JobDescriptionCreatePage />}
              />
              <Route
                path="/jd-matcher/:id"
                element={<JobDescriptionDetailPage />}
              />
              <Route
                path="/match/:resumeId/:jobId"
                element={<MatchDashboardPage />}
              />
              <Route
                path="/job-tracker"
                element={<ComingSoon page="Job Tracker" />}
              />
              <Route
                path="/analytics"
                element={<ComingSoon page="Analytics" />}
              />
              <Route
                path="/settings"
                element={<ComingSoon page="Settings" />}
              />
            </Route>
          </Route>

          {/* ── Catch-all ── */}
          <Route
            path="*"
            element={<Navigate to="/resume-analyzer" replace />}
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
