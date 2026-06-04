// Job Description Detail Page
// Route: /jd-matcher/:id
// Shows the full job description text and allows deletion.
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  Calendar,
  Loader2,
  Trash2,
  AlertTriangle,
  Zap,
} from "lucide-react";
import {
  Card,
  CardHeader,
  Topbar,
  Button,
  Pill,
} from "../../../components/ui-kit";
import { jobsApi, type JobDescriptionDetail } from "../../../lib/api/jobs";
import { resumeApi, type ResumeListItem } from "../../../lib/api/resumes";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export default function JobDescriptionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedResumeId, setSelectedResumeId] = useState<string>("");

  const {
    data: jd,
    isLoading,
    isError,
  } = useQuery<JobDescriptionDetail>({
    queryKey: ["jobs", id],
    queryFn: () => jobsApi.get(id!),
    enabled: !!id,
  });

  const { data: resumes } = useQuery<ResumeListItem[]>({
    queryKey: ["resumes"],
    queryFn: resumeApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: () => jobsApi.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      navigate("/jd-matcher", { replace: true });
    },
  });

  return (
    <>
      <Topbar
        title={isLoading ? "Loading…" : (jd?.title ?? "Job Description")}
        subtitle={
          jd?.company
            ? `${jd.company} · Saved ${formatDate(jd.created_at)}`
            : jd
              ? `Saved ${formatDate(jd.created_at)}`
              : undefined
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => navigate("/jd-matcher")}
              id="btn-back"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            {jd && (
              <Button
                variant="outline"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
                className="border-destructive/40 text-destructive hover:bg-destructive hover:text-white"
                id="btn-delete-jd"
              >
                {deleteMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete
              </Button>
            )}
          </div>
        }
      />

      <div className="space-y-6 p-6 lg:p-8 max-w-3xl">
        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-24 text-muted-foreground">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading job description…
          </div>
        )}

        {/* Error */}
        {isError && (
          <Card>
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <AlertTriangle
                className="h-8 w-8 text-destructive/60"
                strokeWidth={1}
              />
              <p className="text-sm font-medium text-foreground">
                Job description not found
              </p>
              <p className="text-xs text-muted-foreground">
                This job description may have been deleted or doesn't belong to
                your account.
              </p>
              <Button
                variant="outline"
                onClick={() => navigate("/jd-matcher")}
                id="btn-error-back"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to list
              </Button>
            </div>
          </Card>
        )}

        {/* Content */}
        {jd && (
          <>
            {/* Meta pills */}
            <div className="flex flex-wrap items-center gap-2">
              {jd.company && (
                <Pill tone="neutral">
                  <Building2 className="mr-1.5 h-3 w-3" />
                  {jd.company}
                </Pill>
              )}
              <Pill tone="neutral">
                <Calendar className="mr-1.5 h-3 w-3" />
                Saved {formatDate(jd.created_at)}
              </Pill>
              <Pill tone="neutral">
                {jd.description.split(/\s+/).length} words
              </Pill>
            </div>

            {/* Full description */}
            <Card>
              <CardHeader
                title="Job Description"
                subtitle="Full text as pasted. Used for skill extraction and matching."
              />
              <div className="px-5 py-4">
                <pre
                  className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground"
                  id="jd-description-text"
                >
                  {jd.description}
                </pre>
              </div>
            </Card>

            {/* Match panel */}
            <Card>
              <CardHeader
                title="Run Match Analysis"
                subtitle="Select a resume to compare against this job description."
              />
              <div className="flex flex-col sm:flex-row items-center gap-4 px-5 py-5 bg-surface-muted/30">
                <div className="w-full max-w-sm">
                  <select
                    className="w-full appearance-none rounded-md border border-ink/20 bg-surface px-4 py-2.5 text-sm text-foreground outline-none transition focus:border-ink"
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    id="select-resume"
                  >
                    <option value="" disabled>
                      -- Select a resume --
                    </option>
                    {resumes?.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.original_file_name}
                      </option>
                    ))}
                  </select>
                </div>
                <Button
                  variant="primary"
                  disabled={!selectedResumeId}
                  onClick={() =>
                    navigate(`/match/${selectedResumeId}/${jd.id}`)
                  }
                  id="btn-run-match"
                >
                  <Zap className="h-4 w-4" />
                  Run Match
                </Button>
              </div>
            </Card>
          </>
        )}
      </div>
    </>
  );
}
