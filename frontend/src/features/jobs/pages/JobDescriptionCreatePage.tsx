// Job Description Create Page
// Route: /jd-matcher/new
// Uses React Hook Form + Zod validation + TanStack Query mutation.
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  Save,
  Briefcase,
  Building2,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { Card, CardHeader, Topbar, Button } from "../../../components/ui-kit";
import {
  jobsApi,
  type CreateJobDescriptionPayload,
} from "../../../lib/api/jobs";

// ── Zod Schema ────────────────────────────────────────────────────────────

const schema = z.object({
  title: z
    .string()
    .min(1, "Job title is required")
    .max(255, "Title must be under 255 characters"),
  company: z
    .string()
    .max(255, "Company name must be under 255 characters")
    .optional()
    .or(z.literal("")),
  description: z
    .string()
    .min(10, "Please paste the full job description (minimum 10 characters)")
    .max(50_000, "Description is too long"),
});

type FormValues = z.infer<typeof schema>;

// ── Character counter helper ───────────────────────────────────────────────

function CharCount({ value, max }: { value: string; max: number }) {
  const len = value.length;
  const pct = (len / max) * 100;
  return (
    <span
      className={`font-mono text-[10px] tabular-nums ${
        pct >= 90
          ? "text-destructive"
          : pct >= 70
            ? "text-warning-foreground"
            : "text-muted-foreground"
      }`}
    >
      {len.toLocaleString()} / {max.toLocaleString()}
    </span>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function JobDescriptionCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: "onChange",
    defaultValues: { title: "", company: "", description: "" },
  });

  const descriptionValue = watch("description");

  const createMutation = useMutation({
    mutationFn: (data: FormValues) => {
      const payload: CreateJobDescriptionPayload = {
        title: data.title,
        company: data.company || null,
        description: data.description,
      };
      return jobsApi.create(payload);
    },
    onSuccess: (created) => {
      // Bust the list cache so the user sees the new entry immediately on /jd-matcher
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      // Navigate to the detail page of the newly created JD
      navigate(`/jd-matcher/${created.id}`, { replace: true });
    },
  });

  const onSubmit = handleSubmit((data) => createMutation.mutate(data));

  return (
    <>
      <Topbar
        title="New Job Description"
        subtitle="Paste a job posting to save it and match it against your resume."
        actions={
          <Button
            variant="outline"
            onClick={() => navigate("/jd-matcher")}
            id="btn-back-to-list"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to list
          </Button>
        }
      />

      <div className="p-6 lg:p-8 max-w-3xl">
        <form onSubmit={onSubmit} id="form-create-jd" noValidate>
          <Card>
            <CardHeader
              eyebrow="Step 1 of 1"
              title="Job Details"
              subtitle="Fill in the role information, then paste the full job posting below."
            />

            <div className="divide-y divide-border">
              {/* Job Title */}
              <div className="px-5 py-4">
                <label
                  htmlFor="input-title"
                  className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  <Briefcase className="h-3.5 w-3.5" />
                  Job Title <span className="text-destructive">*</span>
                </label>
                <input
                  id="input-title"
                  type="text"
                  placeholder="e.g. Senior Backend Engineer"
                  autoFocus
                  {...register("title")}
                  className={`w-full border bg-surface-muted px-4 py-2.5 text-sm text-foreground placeholder-muted-foreground/60 outline-none transition focus:border-ink ${
                    errors.title ? "border-destructive" : "border-ink/20"
                  }`}
                />
                {errors.title && (
                  <p
                    className="mt-1.5 flex items-center gap-1.5 text-xs text-destructive"
                    role="alert"
                  >
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    {errors.title.message}
                  </p>
                )}
              </div>

              {/* Company */}
              <div className="px-5 py-4">
                <label
                  htmlFor="input-company"
                  className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  <Building2 className="h-3.5 w-3.5" />
                  Company
                  <span className="ml-1 font-normal normal-case tracking-normal text-muted-foreground/50">
                    (optional)
                  </span>
                </label>
                <input
                  id="input-company"
                  type="text"
                  placeholder="e.g. Acme Corp"
                  {...register("company")}
                  className={`w-full border bg-surface-muted px-4 py-2.5 text-sm text-foreground placeholder-muted-foreground/60 outline-none transition focus:border-ink ${
                    errors.company ? "border-destructive" : "border-ink/20"
                  }`}
                />
                {errors.company && (
                  <p
                    className="mt-1.5 flex items-center gap-1.5 text-xs text-destructive"
                    role="alert"
                  >
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    {errors.company.message}
                  </p>
                )}
              </div>

              {/* Job Description text area */}
              <div className="px-5 py-4">
                <div className="mb-1.5 flex items-center justify-between">
                  <label
                    htmlFor="input-description"
                    className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    Job Description <span className="text-destructive">*</span>
                  </label>
                  <CharCount value={descriptionValue} max={50_000} />
                </div>

                <textarea
                  id="input-description"
                  rows={18}
                  placeholder={
                    "Paste the full job description here…\n\n" +
                    "Include everything: responsibilities, requirements, nice-to-haves, " +
                    "and tech stack. The more detail you provide, the more accurate the match score."
                  }
                  {...register("description")}
                  className={`w-full resize-y border bg-surface-muted px-4 py-3 font-mono text-xs leading-relaxed text-foreground placeholder-muted-foreground/50 outline-none transition focus:border-ink ${
                    errors.description ? "border-destructive" : "border-ink/20"
                  }`}
                />
                {errors.description && (
                  <p
                    className="mt-1.5 flex items-center gap-1.5 text-xs text-destructive"
                    role="alert"
                  >
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    {errors.description.message}
                  </p>
                )}
              </div>
            </div>

            {/* Footer — action bar */}
            <div className="flex items-center justify-between gap-4 border-t border-ink/15 px-5 py-4">
              {/* Server error */}
              {createMutation.isError && (
                <p
                  className="flex items-center gap-1.5 text-xs text-destructive"
                  role="alert"
                >
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                  {(createMutation.error as Error).message}
                </p>
              )}
              {!createMutation.isError && (
                <p className="text-xs text-muted-foreground">
                  Saved job descriptions can be matched against any of your
                  uploaded resumes.
                </p>
              )}

              <Button
                type="submit"
                variant="primary"
                disabled={!isValid || createMutation.isPending}
                className="shrink-0"
                id="btn-submit-jd"
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving…
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Job Description
                  </>
                )}
              </Button>
            </div>
          </Card>
        </form>
      </div>
    </>
  );
}
