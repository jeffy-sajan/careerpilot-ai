import { useState, forwardRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "../../../lib/api/auth";
import { AxiosError } from "axios";
import { ArrowRight, Check, Eye, EyeOff } from "lucide-react";

const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

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

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [isSuccess, setIsSuccess] = useState(false);
  const [globalError, setGlobalError] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
  });

  if (!token) {
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

          <div className="mb-6 flex flex-col items-center">
            <div className="w-12 h-12 border border-red-500/20 rounded-full flex items-center justify-center mb-6">
              <span className="text-red-500 text-xl">!</span>
            </div>
            <h2 className="font-display text-3xl leading-[0.95] tracking-tight">
              Invalid Request
            </h2>
            <p className="mt-3 text-sm text-muted-foreground max-w-sm">
              No reset token provided. Please use the exact link from your
              email.
            </p>
          </div>

          <Link
            to="/forgot-password"
            className="group inline-flex h-11 items-center justify-center gap-2 bg-ink px-5 text-paper font-display text-sm tracking-wide uppercase hover:bg-ink/90 transition"
          >
            Request new link
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    );
  }

  const onSubmit = async (data: ResetPasswordFormValues) => {
    try {
      setGlobalError("");
      await authApi.resetPassword({ token, new_password: data.newPassword });
      setIsSuccess(true);
      setTimeout(() => {
        navigate("/login?message=Password+successfully+reset.+Please+log+in.", {
          replace: true,
        });
      }, 3000);
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
            Create new password.
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Must be different from previous passwords.
          </p>
        </div>

        {isSuccess ? (
          <div className="mt-8 text-center space-y-6">
            <div className="w-12 h-12 border border-ink/20 rounded-full flex items-center justify-center mx-auto">
              <Check className="h-5 w-5 text-ink" />
            </div>
            <div>
              <h3 className="font-display text-lg tracking-tight">
                Password Reset Successful
              </h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto">
                Redirecting to login...
              </p>
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

            <div className="space-y-4">
              <div className="relative">
                <Field
                  num="01"
                  label="New Password"
                  type={showNew ? "text" : "password"}
                  placeholder="8+ characters"
                  error={errors.newPassword?.message}
                  {...register("newPassword")}
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-0 top-7 text-muted-foreground hover:text-foreground transition-colors"
                  title={showNew ? "Hide password" : "Show password"}
                >
                  {showNew ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              <div className="relative">
                <Field
                  num="02"
                  label="Confirm Password"
                  type={showConfirm ? "text" : "password"}
                  placeholder="Repeat"
                  error={errors.confirmPassword?.message}
                  {...register("confirmPassword")}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-0 top-7 text-muted-foreground hover:text-foreground transition-colors"
                  title={showConfirm ? "Hide password" : "Show password"}
                >
                  {showConfirm ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="group flex h-11 w-full items-center justify-between bg-ink px-5 text-paper font-display text-sm tracking-wide uppercase hover:bg-ink/90 transition disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Resetting..." : "Save new password"}
              {!isSubmitting && (
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ResetPasswordPage;
