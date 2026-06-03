// Resume Analyzer page — ported from apply-accelerate-ai with real API integration
import { useCallback, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UploadCloud, FileText, CheckCircle2, AlertTriangle,
  Trash2, RefreshCw, Loader2, Clock, XCircle, Wand2
} from "lucide-react";
import { Card, CardHeader, Topbar, Button, Pill } from "../../../components/ui-kit";
import { resumeApi, type ResumeListItem } from "../../../lib/api/resumes";

const MAX_SIZE_MB = 5;
const ALLOWED_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string) {
  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(
    Math.round((new Date(iso).getTime() - Date.now()) / (1000 * 60)),
    "minute"
  );
}

function StatusPill({ status }: { status: ResumeListItem["status"] }) {
  switch (status) {
    case "COMPLETED":
      return (
        <Pill tone="success">
          <CheckCircle2 className="mr-1 h-3 w-3" /> Parsed
        </Pill>
      );
    case "PROCESSING":
      return (
        <Pill tone="warning">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Processing…
        </Pill>
      );
    case "FAILED":
      return (
        <Pill tone="destructive">
          <XCircle className="mr-1 h-3 w-3" /> Failed
        </Pill>
      );
    case "UPLOADED":
    default:
      return (
        <Pill tone="neutral">
          <Clock className="mr-1 h-3 w-3" /> Uploaded
        </Pill>
      );
  }
}

export default function ResumeAnalyzerPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Auto-poll every 3s when any resume is in PROCESSING state
  const { data: resumes = [], isLoading } = useQuery<ResumeListItem[]>({
    queryKey: ["resumes"],
    queryFn: resumeApi.list,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.some((r) => r.status === "PROCESSING" || r.status === "UPLOADED")) {
        return 3000;
      }
      return false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: resumeApi.upload,
    onSuccess: () => {
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
    onError: (e: Error) => setUploadError(e.message),
  });

  const deleteMutation = useMutation({
    mutationFn: resumeApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resumes"] }),
  });

  const handleFile = useCallback((file: File) => {
    setUploadError(null);
    if (!ALLOWED_TYPES.includes(file.type)) {
      setUploadError("Only PDF and DOCX files are allowed.");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setUploadError(`File exceeds ${MAX_SIZE_MB}MB limit.`);
      return;
    }
    uploadMutation.mutate(file);
  }, [uploadMutation]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  };

  // Status summary counts
  const counts = {
    uploaded: resumes.filter((r) => r.status === "UPLOADED").length,
    processing: resumes.filter((r) => r.status === "PROCESSING").length,
    completed: resumes.filter((r) => r.status === "COMPLETED").length,
    failed: resumes.filter((r) => r.status === "FAILED").length,
  };

  return (
    <>
      <Topbar
        title="Resume Analyzer"
        subtitle="Upload, manage, and track your resumes."
        actions={
          <Button
            variant="outline"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["resumes"] })}
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        }
      />

      <div className="space-y-6 p-6 lg:p-8">

        {/* Status Summary Bar */}
        {resumes.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <StatusSummaryCard icon={<Clock className="h-4 w-4" />} label="Uploaded" count={counts.uploaded} tone="neutral" />
            <StatusSummaryCard icon={<Loader2 className={`h-4 w-4 ${counts.processing > 0 ? 'animate-spin' : ''}`} />} label="Processing" count={counts.processing} tone="warning" />
            <StatusSummaryCard icon={<CheckCircle2 className="h-4 w-4" />} label="Completed" count={counts.completed} tone="success" />
            <StatusSummaryCard icon={<XCircle className="h-4 w-4" />} label="Failed" count={counts.failed} tone="destructive" />
          </div>
        )}

        {/* Drop Zone */}
        <Card>
          <div className="p-5">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 text-center cursor-pointer transition-colors ${
                dragOver
                  ? "border-ink bg-surface-muted"
                  : "border-border bg-surface-muted hover:border-ink/40"
              }`}
            >
              <div className={`grid h-12 w-12 place-items-center rounded-xl transition-colors ${
                dragOver ? "bg-ink text-paper" : "bg-primary-soft text-ink"
              }`}>
                {uploadMutation.isPending
                  ? <Loader2 className="h-6 w-6 animate-spin" />
                  : <UploadCloud className="h-6 w-6" />
                }
              </div>
              <div>
                <h3 className="text-base font-semibold text-foreground">
                  {uploadMutation.isPending ? "Uploading…" : "Drop your resume here, or browse"}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  PDF and DOCX only · max {MAX_SIZE_MB}MB · we never share your data
                </p>
              </div>
              {!uploadMutation.isPending && (
                <Button variant="primary" type="button">Browse files</Button>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={onFileChange}
            />

            {uploadError && (
              <div className="mt-3 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive-soft px-4 py-2.5 text-sm text-destructive">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                {uploadError}
              </div>
            )}
          </div>
        </Card>

        {/* Resume List */}
        <Card>
          <CardHeader
            title="Your Resumes"
            subtitle={`${resumes.length} file${resumes.length !== 1 ? "s" : ""} uploaded`}
          />

          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Loading resumes…
            </div>
          ) : resumes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <FileText className="h-10 w-10 text-muted-foreground/40" strokeWidth={1} />
              <p className="mt-3 text-sm font-medium text-foreground">No resumes yet</p>
              <p className="text-xs text-muted-foreground">Upload your first resume above to get started.</p>
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {resumes.map((resume) => (
                <ResumeRow
                  key={resume.id}
                  resume={resume}
                  onDelete={() => deleteMutation.mutate(resume.id)}
                  isDeleting={deleteMutation.isPending && deleteMutation.variables === resume.id}
                />
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}

/* ── Status Summary Cards ─────────────────────────────── */
function StatusSummaryCard({
  icon, label, count, tone,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
  tone: "neutral" | "warning" | "success" | "destructive";
}) {
  const toneStyles: Record<string, string> = {
    neutral:     "border-ink/15 text-muted-foreground",
    warning:     "border-warning/30 text-warning-foreground",
    success:     "border-success/30 text-success",
    destructive: "border-destructive/30 text-destructive",
  };
  const bgStyles: Record<string, string> = {
    neutral:     "bg-surface-muted",
    warning:     "bg-warning-soft",
    success:     "bg-success/5",
    destructive: "bg-destructive-soft",
  };

  return (
    <div className={`flex items-center gap-3 border rounded-lg px-4 py-3 ${toneStyles[tone]} ${bgStyles[tone]}`}>
      <div className="shrink-0">{icon}</div>
      <div className="min-w-0">
        <div className="font-mono text-lg font-semibold leading-none">{count}</div>
        <div className="mt-0.5 text-[11px] uppercase tracking-wider opacity-70">{label}</div>
      </div>
    </div>
  );
}

/* ── Resume Row ───────────────────────────────────────── */
function ResumeRow({
  resume, onDelete, isDeleting,
}: {
  resume: ResumeListItem;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  const isProcessing = resume.status === "PROCESSING";
  const isFailed = resume.status === "FAILED";

  return (
    <li className={`group px-5 py-3.5 transition-colors hover:bg-surface-muted/50 ${isProcessing ? "animate-pulse" : ""}`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-md ${
            isFailed
              ? "bg-destructive-soft text-destructive"
              : resume.status === "COMPLETED"
                ? "bg-success/10 text-success"
                : "bg-primary-soft text-ink"
          }`}>
            {isProcessing
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <FileText className="h-4 w-4" />
            }
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-foreground">{resume.original_file_name}</div>
            <div className="text-xs text-muted-foreground">
              {formatBytes(resume.file_size_bytes)} · {formatDate(resume.created_at)}
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <StatusPill status={resume.status} />
          {resume.status === "COMPLETED" && (
            <Link to={`/resume-analyzer/${resume.id}/analysis`}>
              <Button variant="outline" size="sm" className="h-8 text-xs px-2.5">
                <Wand2 className="mr-1.5 h-3 w-3" /> Analyze ATS
              </Button>
            </Link>
          )}
          <button
            onClick={onDelete}
            disabled={isDeleting || isProcessing}
            className="p-1.5 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-40"
            aria-label={`Delete ${resume.original_file_name}`}
          >
            {isDeleting
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <Trash2 className="h-4 w-4" />
            }
          </button>
        </div>
      </div>

      {/* Error message for FAILED resumes */}
      {isFailed && resume.error_message && (
        <div className="mt-2 ml-12 flex items-start gap-2 rounded-md border border-destructive/20 bg-destructive-soft px-3 py-2 text-xs text-destructive">
          <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0" />
          <span>{resume.error_message}</span>
        </div>
      )}
    </li>
  );
}
