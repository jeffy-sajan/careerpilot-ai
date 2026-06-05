import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Save, Loader2, Trash2 } from "lucide-react";
import { Button } from "../../../components/ui-kit";
import {
  applicationsApi,
  JobApplication,
  JobApplicationCreate,
} from "../../../lib/api/applications";

const schema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  job_title: z.string().min(1, "Job title is required"),
  job_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  source: z.string().optional(),
  status: z.enum([
    "SAVED",
    "APPLIED",
    "ASSESSMENT",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
  ]),
  priority: z.enum(["LOW", "MEDIUM", "HIGH"]),
  application_date: z.string().min(1, "Application date is required"),
  next_interview_date: z.string().optional(),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  isOpen: boolean;
  onClose: () => void;
  application?: JobApplication | null;
  defaultStatus?: string;
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </label>
      {children}
      {error && <p className="mt-1 text-[11px] text-destructive">{error}</p>}
    </div>
  );
}

export function ApplicationFormModal({
  isOpen,
  onClose,
  application,
  defaultStatus = "SAVED",
}: Props) {
  const queryClient = useQueryClient();
  const isEditing = !!application;

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: "onChange",
    defaultValues: {
      company_name: "",
      job_title: "",
      job_url: "",
      source: "",
      status: defaultStatus as FormValues["status"],
      priority: "MEDIUM",
      application_date: new Date().toISOString().split("T")[0],
      next_interview_date: "",
      notes: "",
    },
  });

  const companyName = watch("company_name");
  const initial = companyName?.slice(0, 1).toUpperCase() || "?";

  useEffect(() => {
    if (isOpen) {
      if (application) {
        reset({
          company_name: application.company_name,
          job_title: application.job_title,
          job_url: application.job_url || "",
          source: application.source || "",
          status: application.status as FormValues["status"],
          priority: application.priority as FormValues["priority"],
          application_date: application.application_date.split("T")[0],
          next_interview_date:
            application.next_interview_date?.split("T")[0] || "",
          notes: application.notes || "",
        });
      } else {
        reset({
          company_name: "",
          job_title: "",
          job_url: "",
          source: "",
          status: defaultStatus as FormValues["status"],
          priority: "MEDIUM",
          application_date: new Date().toISOString().split("T")[0],
          next_interview_date: "",
          notes: "",
        });
      }
    }
  }, [isOpen, application, defaultStatus, reset]);

  const saveMutation = useMutation({
    mutationFn: (data: FormValues) => {
      const payload = {
        ...data,
        application_date: new Date(data.application_date).toISOString(),
        next_interview_date: data.next_interview_date
          ? new Date(data.next_interview_date).toISOString()
          : undefined,
      };
      if (isEditing && application) {
        return applicationsApi.update(application.id, payload);
      }
      return applicationsApi.create(payload as JobApplicationCreate);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      onClose();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => applicationsApi.delete(application!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      onClose();
    },
  });

  const onSubmit = handleSubmit((data) => saveMutation.mutate(data));

  const handleDelete = () => {
    if (window.confirm("Delete this application? This cannot be undone.")) {
      deleteMutation.mutate();
    }
  };

  if (!isOpen) return null;

  const inputCls =
    "h-9 w-full rounded-md border border-input bg-surface px-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/40 transition";

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-foreground/30 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card shadow-elevated animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-border p-5">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-primary/10 to-secondary text-base font-bold text-primary">
              {initial}
            </div>
            <div>
              <div className="text-base font-semibold text-foreground">
                {isEditing ? "Edit Application" : "New Application"}
              </div>
              <div className="text-xs text-muted-foreground">
                {isEditing
                  ? `${application.job_title} · ${application.company_name}`
                  : "Track a new job opportunity"}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={onSubmit} noValidate>
          <div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2 max-h-[65vh] overflow-y-auto">
            <Field label="Company" error={errors.company_name?.message}>
              <input
                autoFocus
                type="text"
                placeholder="e.g. Stripe"
                {...register("company_name")}
                className={inputCls}
              />
            </Field>

            <Field label="Position" error={errors.job_title?.message}>
              <input
                type="text"
                placeholder="e.g. Senior PM, Growth"
                {...register("job_title")}
                className={inputCls}
              />
            </Field>

            <Field label="Source" error={errors.source?.message}>
              <input
                type="text"
                placeholder="e.g. LinkedIn, Referral"
                {...register("source")}
                className={inputCls}
              />
            </Field>

            <Field label="Status">
              <select {...register("status")} className={inputCls}>
                <option value="SAVED">Saved</option>
                <option value="APPLIED">Applied</option>
                <option value="ASSESSMENT">Assessment</option>
                <option value="INTERVIEW">Interview</option>
                <option value="OFFER">Offer</option>
                <option value="REJECTED">Rejected</option>
                <option value="WITHDRAWN">Withdrawn</option>
              </select>
            </Field>

            <Field
              label="Application Date"
              error={errors.application_date?.message}
            >
              <input
                type="date"
                {...register("application_date")}
                className={inputCls}
              />
            </Field>

            <Field label="Priority">
              <select {...register("priority")} className={inputCls}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
              </select>
            </Field>

            <Field label="Job URL" error={errors.job_url?.message}>
              <input
                type="url"
                placeholder="https://..."
                {...register("job_url")}
                className={inputCls}
              />
            </Field>

            <Field label="Next Interview Date">
              <input
                type="date"
                {...register("next_interview_date")}
                className={inputCls}
              />
            </Field>
          </div>

          <div className="px-5 pb-5">
            <Field label="Notes">
              <textarea
                rows={3}
                placeholder="Recruiter name, interview stage, feedback…"
                {...register("notes")}
                className="w-full resize-none rounded-md border border-input bg-surface p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/40 transition"
              />
            </Field>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-border bg-surface-muted px-5 py-3.5">
            {isEditing ? (
              <Button
                type="button"
                variant="ghost"
                className="text-destructive hover:text-destructive"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            ) : (
              <span />
            )}

            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={!isValid || saveMutation.isPending}
              >
                {saveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {saveMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
