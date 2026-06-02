import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { PublicRoute } from './routes/PublicRoute';
import AuthLayout from './layouts/AuthLayout';

// Auth pages (Phase 4)
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';
import GoogleCallbackPage from './features/auth/pages/GoogleCallbackPage';
import ForgotPasswordPage from './features/auth/pages/ForgotPasswordPage';
import ResetPasswordPage from './features/auth/pages/ResetPasswordPage';

// Temporary dashboard placeholder (Phase 4 test — will be replaced in later phases)
const DashboardPage = () => (
  <div className="min-h-screen bg-slate-50 flex items-center justify-center">
    <div className="text-center space-y-4">
      <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center mx-auto shadow-lg shadow-blue-600/30">
        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
      <p className="text-slate-500 text-sm max-w-xs">
        You are authenticated ✅ — this placeholder will be replaced with the real dashboard in an upcoming phase.
      </p>
    </div>
  </div>
);

function App() {
  return (
    // Note: QueryClientProvider wraps App in main.tsx
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* ── Public Routes (redirect to /dashboard if already logged in) ── */}
          <Route element={<PublicRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
            </Route>
          </Route>

          {/* ── Google OAuth Callback (outside PublicRoute guard — must be accessible always) ── */}
          <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />

          {/* ── Protected Routes (redirect to /login if not authenticated) ─── */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            {/* More protected routes added per feature phase */}
          </Route>

          {/* ── Catch-all: send everyone to /dashboard (ProtectedRoute handles the guard) ── */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
