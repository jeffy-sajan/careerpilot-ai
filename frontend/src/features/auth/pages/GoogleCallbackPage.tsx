import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
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
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6 sm:p-10">
      <div className="w-full max-w-md text-center">
        <div className="mb-8 flex items-center gap-2 justify-center">
          <div className="h-7 w-7 grid place-items-center bg-ink text-paper font-display text-sm">
            C
          </div>
          <span className="font-display text-base tracking-tight">
            CareerPilot
          </span>
        </div>

        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 border border-ink/20 rounded-full flex items-center justify-center mx-auto bg-muted/50">
            <Loader2 className="w-5 h-5 text-ink animate-spin" />
          </div>
        </div>

        <h2 className="font-display text-2xl tracking-tight mb-2">
          Signing you in...
        </h2>
        <p className="text-sm text-muted-foreground">
          Hang tight, this will only take a moment.
        </p>
      </div>
    </div>
  );
};

export default GoogleCallbackPage;
