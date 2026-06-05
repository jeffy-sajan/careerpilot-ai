import { useState, forwardRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link } from "react-router-dom";
import { authApi } from "../../../lib/api/auth";
import { AxiosError } from "axios";
import { ArrowRight, Check } from "lucide-react";

const forgotPasswordSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email address"),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

const Field = forwardRef<
  HTMLInputElement,
  {
    label: string;
    type?: string;
    placeholder?: string;
    num: string;
    error?: string;
    right?: React.ReactNode;
  } & React.InputHTMLAttributes<HTMLInputElement>
>(({ label, type = "text", placeholder, num, error, right, ...props }, ref) => {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <label className="flex items-baseline gap-3">
          <span className="font-mono text-[10px] tracking-widest text-muted-foreground">
            {num}
          </span>
          <span className="font-display text-sm tracking-tight">{label}</span>
        </label>
        {right}
      </div>
      <input
        ref={ref}
        type={type}
        placeholder={placeholder}
        className={`h-10 w-full border-0 border-b bg-transparent px-0 text-base text-foreground placeholder:text-muted-foreground focus:outline-none transition ${
          error
            ? "border-red-500 focus:border-red-500"
            : "border-ink/25 focus:border-ink"
        }`}
        {...props}
      />
      {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
    </div>
  );
});
Field.displayName = "Field";

const ForgotPasswordPage = () => {
  const [isSuccess, setIsSuccess] = useState(false);
  const [globalError, setGlobalError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    try {
      setGlobalError("");
      await authApi.forgotPassword(data);
      setIsSuccess(true);
    } catch (err) {
      if (err instanceof AxiosError && err.response?.data?.detail) {
        setGlobalError(err.response.data.detail);
      } else {
        setGlobalError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6 sm:p-10">
      <div className="w-full max-w-md">
        <div className="mb-8 flex items-center gap-2 justify-center">
          <div className="h-7 w-7 grid place-items-center bg-ink text-paper font-display text-sm">
            C
          </div>
          <span className="font-display text-base tracking-tight">
            CareerPilot
          </span>
        </div>

        <div className="text-center">
          <div className="eyebrow mb-2">Account Recovery</div>
          <h2 className="font-display text-4xl leading-[0.95] tracking-tight">
            Reset password.
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Enter your work email and we'll send you a link.
          </p>
        </div>

        {isSuccess ? (
          <div className="mt-8 text-center space-y-6">
            <div className="w-12 h-12 border border-ink/20 rounded-full flex items-center justify-center mx-auto">
              <Check className="h-5 w-5 text-ink" />
            </div>
            <div>
              <h3 className="font-display text-lg tracking-tight">
                Check your email
              </h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto">
                We have sent instructions to reset your password to your email
                address.
              </p>
            </div>
            <div className="pt-4">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-sm font-medium text-foreground hover:text-muted-foreground transition-colors"
              >
                Return to Login
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-6">
            {globalError && (
              <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
                <svg
                  className="w-4 h-4 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                {globalError}
              </div>
            )}

            <Field
              num="01"
              label="Work email"
              type="email"
              placeholder="you@company.com"
              error={errors.email?.message}
              {...register("email")}
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="group flex h-11 w-full items-center justify-between bg-ink px-5 text-paper font-display text-sm tracking-wide uppercase hover:bg-ink/90 transition disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Sending..." : "Send Reset Link"}
              {!isSubmitting && (
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              )}
            </button>

            <div className="text-center mt-6">
              <Link
                to="/login"
                className="text-xs font-mono tracking-widest text-muted-foreground hover:text-foreground uppercase transition-colors"
              >
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
