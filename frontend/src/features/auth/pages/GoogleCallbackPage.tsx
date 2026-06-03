import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiClient } from "../../../lib/axios";
import { useAuth } from "../../../context/AuthContext";
import { TokenResponse } from "../../../types/auth";

/**
 * GoogleCallbackPage
 *
 * The backend redirects the browser here after Google OAuth:
 *   /auth/google/callback?code=<one_time_code>&is_new_user=true|false
 *
 * This page:
 *  1. Extracts the one-time code from the URL
 *  2. Exchanges it with POST /auth/google/exchange for a JWT pair
 *  3. Calls AuthContext.login() to store tokens and fetch the user profile
 *  4. Redirects to /dashboard
 *
 * On any error, it redirects to /login with a readable error message.
 */
const GoogleCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const hasFired = useRef(false); // Prevent double-execution in React StrictMode

  useEffect(() => {
    if (hasFired.current) return;
    hasFired.current = true;

    const code = searchParams.get("code");
    const isNewUser = searchParams.get("is_new_user") === "true";
    const error = searchParams.get("error");

    // Handle errors redirected from the backend OAuth callback
    if (error) {
      if (error === "account_exists_with_different_provider") {
        navigate(
          "/login?message=An+account+with+this+email+already+exists.+Please+sign+in+with+your+email+and+password.",
          { replace: true },
        );
      } else {
        navigate("/login?message=Google+sign-in+failed.+Please+try+again.", {
          replace: true,
        });
      }
      return;
    }

    if (!code) {
      navigate("/login?message=Invalid+authentication+response.", {
        replace: true,
      });
      return;
    }

    // Exchange the one-time code for a JWT pair
    const exchangeCode = async () => {
      try {
        const { data } = await apiClient.post<TokenResponse>(
          "/auth/google/exchange",
          { code },
        );
        login(data);
        // Redirect to dashboard — show a welcome message for new users
        navigate(isNewUser ? "/dashboard?welcome=true" : "/dashboard", {
          replace: true,
        });
      } catch {
        navigate("/login?message=Google+sign-in+failed.+Please+try+again.", {
          replace: true,
        });
      }
    };

    exchangeCode();
  }, [searchParams, login, navigate]);

  // Show a minimal, branded loading screen while the exchange is in progress
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center gap-6">
      <div className="w-14 h-14 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/40">
        <svg
          className="w-8 h-8 text-white"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
      </div>
      <div className="text-center">
        <div className="flex items-center gap-2 mb-2">
          <svg
            className="animate-spin w-5 h-5 text-blue-400"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <p className="text-blue-400 font-medium">
            Signing you in with Google…
          </p>
        </div>
        <p className="text-slate-500 text-sm">
          Hang tight, this will only take a moment.
        </p>
      </div>
    </div>
  );
};

export default GoogleCallbackPage;
