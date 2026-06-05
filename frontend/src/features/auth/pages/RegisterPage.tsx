import { useState, forwardRef } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AxiosError } from "axios";
import { ArrowRight, Check, Eye, EyeOff } from "lucide-react";
import { useRegister } from "../hooks/useRegister";

// ── Zod Validation Schema ─────────────────────────────────────────────────────
const registerSchema = z
  .object({
    name: z
      .string()
      .min(2, "Name must be at least 2 characters")
      .max(100, "Name must be under 100 characters")
      .trim(),
    email: z.string().email("Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[a-zA-Z]/, "Password must contain at least one letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

const benefits = [
  "Unlimited resume scans + ATS scoring",
  "AI keyword and skill-gap analysis",
  "Kanban tracker with interview reminders",
];

// ── Shared UI Components ──────────────────────────────────────────────────────
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

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden>
      <path
        fill="currentColor"
        d="M12 10.2v3.96h5.52c-.24 1.32-1.68 3.84-5.52 3.84-3.36 0-6.12-2.76-6.12-6.12S8.64 5.76 12 5.76c1.92 0 3.24.84 3.96 1.56l2.7-2.64C16.92 3.12 14.64 2.16 12 2.16 6.6 2.16 2.16 6.6 2.16 12s4.44 9.84 9.84 9.84c5.64 0 9.36-3.96 9.36-9.6 0-.6-.06-1.08-.18-1.56H12z"
      />
    </svg>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { mutate: registerUser, isPending, error } = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = ({ name, email, password }: RegisterFormData) => {
    registerUser({ name, email, password });
  };

  const apiError = error
    ? ((error as AxiosError<{ detail: string }>).response?.data?.detail ??
      "Registration failed. Please try again.")
    : null;

  return (
    <div className="h-screen overflow-hidden bg-background text-foreground grid lg:grid-cols-[1fr_1.05fr]">
      {/* Form left */}
      <main className="flex items-center justify-center p-6 sm:p-10 overflow-auto order-2 lg:order-1">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-6 flex items-center gap-2">
            <div className="h-7 w-7 grid place-items-center bg-ink text-paper font-display text-sm">
              C
            </div>
            <span className="font-display text-base tracking-tight">
              CareerPilot
            </span>
          </div>

          <div className="eyebrow mb-2">Section 02 — Enrollment</div>
          <h2 className="font-display text-4xl leading-[0.95] tracking-tight">
            Begin your next chapter.
          </h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Free for 14 days. No card required.{" "}
            <Link
              to="/login"
              className="text-foreground underline underline-offset-4 decoration-ink/40 hover:decoration-ink"
            >
              Already a member?
            </Link>
          </p>

          {/* API Error Banner */}
          {apiError && (
            <div className="mt-6 flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
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
              {apiError}
            </div>
          )}

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="mt-6 space-y-4"
            noValidate
          >
            <Field
              num="01"
              label="Full name"
              placeholder="Ananya Mehta"
              error={errors.name?.message}
              {...register("name")}
            />

            <Field
              num="02"
              label="Work email"
              type="email"
              placeholder="you@company.com"
              error={errors.email?.message}
              {...register("email")}
            />

            <div className="grid sm:grid-cols-2 gap-5">
              <div className="relative">
                <Field
                  num="03"
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  placeholder="8+ characters"
                  error={errors.password?.message}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-0 top-7 text-muted-foreground hover:text-foreground transition-colors"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              <div className="relative">
                <Field
                  num="04"
                  label="Confirm"
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

            <p className="text-xs text-muted-foreground leading-relaxed pt-2">
              By creating an account you agree to our{" "}
              <span className="underline underline-offset-2 hover:text-foreground cursor-pointer">
                Terms
              </span>{" "}
              and{" "}
              <span className="underline underline-offset-2 hover:text-foreground cursor-pointer">
                Privacy Policy
              </span>
              .
            </p>

            <button
              type="submit"
              disabled={isPending}
              className="mt-6 group flex h-11 w-full items-center justify-between bg-ink px-5 text-paper font-display text-sm tracking-wide uppercase hover:bg-ink/90 transition disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isPending ? "Creating account..." : "Create account"}
              {!isPending && (
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              )}
            </button>

            <div className="flex items-center gap-4 py-2">
              <div className="h-px flex-1 bg-ink/15" />
              <span className="eyebrow">or</span>
              <div className="h-px flex-1 bg-ink/15" />
            </div>

            <a
              href={`${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/auth/google/authorize`}
              className="flex h-11 w-full items-center justify-center gap-3 border border-ink/20 bg-paper px-5 text-sm font-medium hover:border-ink hover:bg-paper-2 transition"
            >
              <GoogleIcon /> Sign up with Google
            </a>
          </form>
        </div>
      </main>

      {/* Editorial right */}
      <aside className="relative hidden lg:flex flex-col justify-between border-l border-ink/15 p-8 xl:p-10 order-1 lg:order-2">
        <header className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="h-7 w-7 grid place-items-center bg-ink text-paper font-display text-sm">
              C
            </div>
            <span className="font-display text-base tracking-tight">
              CareerPilot
            </span>
          </Link>
          <span className="eyebrow">Issue №26 / Join</span>
        </header>

        <div className="min-h-0">
          <div className="eyebrow mb-3">Featured Volume — Spring '26</div>
          <h1 className="font-display text-5xl xl:text-6xl leading-[0.92] tracking-tight">
            The search,
            <br />
            <span className="text-muted-foreground">refined.</span>
          </h1>

          <ul className="mt-8 divide-y divide-ink/15 border-y border-ink/15">
            {benefits.map((b, i) => (
              <li key={b} className="flex items-center gap-5 py-3">
                <span className="font-mono text-[10px] tracking-widest text-muted-foreground w-8">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="font-display text-base tracking-tight flex-1">
                  {b}
                </span>
                <Check className="h-4 w-4 text-foreground" />
              </li>
            ))}
          </ul>
        </div>

        <footer className="flex items-center justify-between text-xs font-mono uppercase tracking-widest text-muted-foreground">
          <span>© 2026 CareerPilot Labs</span>
          <span>SOC 2 · Type II</span>
        </footer>
      </aside>
    </div>
  );
}

export default RegisterPage;
