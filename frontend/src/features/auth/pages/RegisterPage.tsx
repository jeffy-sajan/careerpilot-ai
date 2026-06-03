import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AxiosError } from 'axios';
import { useRegister } from '../hooks/useRegister';

// ── Zod Validation Schema ─────────────────────────────────────────────────────
const registerSchema = z
  .object({
    name: z
      .string()
      .min(2, 'Name must be at least 2 characters')
      .max(100, 'Name must be under 100 characters')
      .trim(),
    email: z.string().email('Please enter a valid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[a-zA-Z]/, 'Password must contain at least one letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

// ── Input field component ─────────────────────────────────────────────────────
const InputField = ({
  id,
  label,
  type = 'text',
  placeholder,
  error,
  registration,
  rightElement,
}: {
  id: string;
  label: string;
  type?: string;
  placeholder: string;
  error?: string;
  registration: object;
  rightElement?: React.ReactNode;
}) => (
  <div>
    <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1.5">
      {label}
    </label>
    <div className="relative">
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        {...registration}
        className={`w-full px-4 py-2.5 rounded-lg border text-slate-900 placeholder:text-slate-400 text-sm
          bg-white transition-colors outline-none
          focus:ring-2 focus:ring-blue-500 focus:border-transparent
          ${rightElement ? 'pr-11' : ''}
          ${error ? 'border-red-400 focus:ring-red-400' : 'border-slate-300'}`}
      />
      {rightElement && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">{rightElement}</div>
      )}
    </div>
    {error && <p className="mt-1.5 text-xs text-red-600">{error}</p>}
  </div>
);

// ── Component ─────────────────────────────────────────────────────────────────
const RegisterPage = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const { mutate: register, isPending, error } = useRegister();

  const {
    register: rhfRegister,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = ({ name, email, password }: RegisterFormData) => {
    register({ name, email, password });
  };

  const apiError = error
    ? ((error as AxiosError<{ detail: string }>).response?.data?.detail ??
      'Registration failed. Please try again.')
    : null;

  const EyeIcon = ({ visible }: { visible: boolean }) => (
    <button
      type="button"
      onClick={() => {}}
      className="text-slate-400 hover:text-slate-600 transition-colors"
      tabIndex={-1}
    >
      {visible ? (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      )}
    </button>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-extrabold text-slate-900">Create Account</h2>
        <p className="mt-1.5 text-slate-500 text-sm">
          Join CareerPilot AI and accelerate your career journey today.
        </p>
      </div>

      {/* API Error Banner */}
      {apiError && (
        <div className="flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {apiError}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {/* Full Name */}
        <InputField
          id="reg-name"
          label="Full Name"
          placeholder="John Doe"
          registration={rhfRegister('name')}
          error={errors.name?.message}
        />

        {/* Email */}
        <InputField
          id="reg-email"
          label="Email Address"
          type="email"
          placeholder="john@example.com"
          registration={rhfRegister('email')}
          error={errors.email?.message}
        />

        {/* Password + Confirm (side-by-side on sm+) */}
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="reg-password" className="block text-sm font-medium text-slate-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <input
                id="reg-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="new-password"
                {...rhfRegister('password')}
                className={`w-full px-4 py-2.5 pr-11 rounded-lg border text-slate-900 placeholder:text-slate-400 text-sm
                  bg-white transition-colors outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  ${errors.password ? 'border-red-400 focus:ring-red-400' : 'border-slate-300'}`}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                <EyeIcon visible={showPassword} />
              </button>
            </div>
            {errors.password && (
              <p className="mt-1.5 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="reg-confirm" className="block text-sm font-medium text-slate-700 mb-1.5">
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="reg-confirm"
                type={showConfirm ? 'text' : 'password'}
                placeholder="••••••••"
                autoComplete="new-password"
                {...rhfRegister('confirmPassword')}
                className={`w-full px-4 py-2.5 pr-11 rounded-lg border text-slate-900 placeholder:text-slate-400 text-sm
                  bg-white transition-colors outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  ${errors.confirmPassword ? 'border-red-400 focus:ring-red-400' : 'border-slate-300'}`}
              />
              <button
                type="button"
                onClick={() => setShowConfirm((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                aria-label={showConfirm ? 'Hide password' : 'Show password'}
              >
                <EyeIcon visible={showConfirm} />
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="mt-1.5 text-xs text-red-600">{errors.confirmPassword.message}</p>
            )}
          </div>
        </div>

        {/* Terms */}
        <div className="flex items-start gap-2.5">
          <input
            id="reg-terms"
            type="checkbox"
            required
            className="mt-0.5 w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="reg-terms" className="text-sm text-slate-600">
            I agree to the{' '}
            <a href="#" className="text-blue-600 hover:underline font-medium">Terms of Service</a>
            {' '}and{' '}
            <a href="#" className="text-blue-600 hover:underline font-medium">Privacy Policy</a>.
          </label>
        </div>

        {/* Submit */}
        <button
          id="register-submit"
          type="submit"
          disabled={isPending}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400
            text-white font-semibold text-sm py-2.5 rounded-lg transition-colors shadow-sm shadow-blue-600/30"
        >
          {isPending ? (
            <>
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Creating Account…
            </>
          ) : (
            <>
              Get Started
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </>
          )}
        </button>
      </form>

      {/* Footer link */}
      <p className="text-center text-slate-500 text-sm">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-semibold transition-colors">
          Login here
        </Link>
      </p>
    </div>
  );
};

export default RegisterPage;
