// Job Description List Page
// Route: /jd-matcher
// Shows all saved Job Descriptions and allows inline deletion.
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Briefcase,
  Plus,
  Trash2,
  Loader2,
  Building2,
  Calendar,
  FileText,
} from "lucide-react";
import {
  Card,
  CardHeader,
  Topbar,
  Button,
  Pill,
} from "../../../components/ui-kit";
import { jobsApi, type JobDescriptionListItem } from "../../../lib/api/jobs";

function formatDate(iso: string) {
  const date = new Date(iso);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function JobDescriptionListPage() {
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    data: jobs = [],
    isLoading,
    isError,
  } = useQuery<JobDescriptionListItem[]>({
    queryKey: ["jobs"],
    queryFn: jobsApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => {
      setDeletingId(id);
      return jobsApi.delete(id);
    },
    onSuccess: () => {
      setDeletingId(null);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: () => setDeletingId(null),
  });

  return (
    <>
      <Topbar
        title="JD Matcher"
        subtitle="Save job descriptions and match them against your resumes."
        actions={
          <Link to="/jd-matcher/new">
            <Button variant="primary" id="btn-new-jd">
              <Plus className="h-4 w-4" />
              New Job Description
            </Button>
          </Link>
        }
      />

      <div className="space-y-6 p-6 lg:p-8">
        {/* Stats bar */}
        {jobs.length > 0 && (
          <div className="flex items-center gap-3">
            <Pill tone="primary">
              <Briefcase className="mr-1.5 h-3 w-3" />
              {jobs.length} saved
            </Pill>
          </div>
        )}

        <Card>
          <CardHeader
            title="Saved Job Descriptions"
            subtitle="Click a job to view and match against your resume."
            action={
              <Link to="/jd-matcher/new">
                <Button variant="outline" size="sm" id="btn-new-jd-header">
                  <Plus className="h-3.5 w-3.5" />
                  Add new
                </Button>
              </Link>
            }
          />

          {/* Loading */}
          {isLoading && (
            <div className="flex items-center justify-center py-20 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading job descriptions…
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="flex items-center justify-center py-20 text-destructive text-sm">
              Failed to load job descriptions. Please try again.
            </div>
          )}

          {/* Empty state */}
          {!isLoading && !isError && jobs.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
              <div className="grid h-14 w-14 place-items-center rounded-2xl border-2 border-dashed border-ink/20">
                <FileText
                  className="h-6 w-6 text-muted-foreground/50"
                  strokeWidth={1}
                />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  No job descriptions yet
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Paste a job posting and save it to start matching.
                </p>
              </div>
              <Link to="/jd-matcher/new">
                <Button variant="outline" id="btn-empty-state-new">
                  <Plus className="h-4 w-4" />
                  Paste your first job
                </Button>
              </Link>
            </div>
          )}

          {/* Job list */}
          {!isLoading && !isError && jobs.length > 0 && (
            <ul className="divide-y divide-border">
              {jobs.map((job) => (
                <JobRow
                  key={job.id}
                  job={job}
                  isDeleting={deletingId === job.id}
                  onDelete={() => deleteMutation.mutate(job.id)}
                />
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}

// ── Job Row sub-component ──────────────────────────────────────────────────

function JobRow({
  job,
  isDeleting,
  onDelete,
}: {
  job: JobDescriptionListItem;
  isDeleting: boolean;
  onDelete: () => void;
}) {
  return (
    <li
      className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-surface-muted/50"
      id={`jd-row-${job.id}`}
    >
      {/* Left: icon + text */}
      <div className="flex min-w-0 items-center gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary-soft text-ink">
          <Briefcase className="h-4 w-4" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-foreground">
            {job.title}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
            {job.company && (
              <>
                <Building2 className="h-3 w-3 shrink-0" />
                <span className="truncate">{job.company}</span>
                <span className="text-ink/20">·</span>
              </>
            )}
            <Calendar className="h-3 w-3 shrink-0" />
            <span>{formatDate(job.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Right: actions */}
      <div className="flex shrink-0 items-center gap-2">
        <Link to={`/jd-matcher/${job.id}`}>
          <Button
            variant="outline"
            size="sm"
            className="h-8 px-3 text-xs"
            id={`btn-view-jd-${job.id}`}
          >
            View
          </Button>
        </Link>
        <button
          onClick={onDelete}
          disabled={isDeleting}
          className="p-1.5 text-muted-foreground transition-colors hover:text-destructive disabled:opacity-40"
          aria-label={`Delete ${job.title}`}
          id={`btn-delete-jd-${job.id}`}
        >
          {isDeleting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
        </button>
      </div>
    </li>
  );
}
