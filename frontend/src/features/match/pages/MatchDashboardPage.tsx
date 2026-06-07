// Match Dashboard Page
// Route: /match/:resumeId/:jobId
// Shows a full match breakdown: score ring, matched/missing skills chips, keyword gaps, suggestions.

import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  Zap,
  CheckCircle2,
  XCircle,
  Lightbulb,
  RefreshCw,
  AlertTriangle,
  Tag,
} from "lucide-react";
import {
  Card,
  CardHeader,
  Topbar,
  Button,
  Pill,
} from "../../../components/ui-kit";
import { matchApi, type ResumeMatchResult } from "../../../lib/api/match";
import { jobsApi, type JobDescriptionDetail } from "../../../lib/api/jobs";
import { resumeApi, type ResumeListItem } from "../../../lib/api/resumes";
import { OptimizationSection } from "../components/OptimizationSection";

// ── Score ring ─────────────────────────────────────────────────────────────

const RADIUS = 60;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function ScoreRing({ score }: { score: number }) {
  const offset = CIRCUMFERENCE - (CIRCUMFERENCE * score) / 100;
  const colour =
    score >= 75
      ? "text-success"
      : score >= 50
        ? "text-warning"
        : "text-destructive";
  const label =
    score >= 75
      ? "Strong Match"
      : score >= 50
        ? "Moderate Match"
        : "Weak Match";

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        <svg
          width="160"
          height="160"
          viewBox="0 0 160 160"
          className="-rotate-90"
        >
          {/* Track */}
          <circle
            cx="80"
            cy="80"
            r={RADIUS}
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            className="text-surface-muted"
          />
          {/* Progress */}
          <circle
            cx="80"
            cy="80"
            r={RADIUS}
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            className={`${colour} transition-all duration-700 ease-out`}
          />
        </svg>
        {/* Centre text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-4xl font-bold text-foreground leading-none">
            {score}
          </span>
          <span className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            / 100
          </span>
        </div>
      </div>

      {/* Verdict pill */}
      <Pill
        tone={score >= 75 ? "success" : score >= 50 ? "warning" : "destructive"}
        className="text-[11px]"
      >
        {label}
      </Pill>

      {/* Weight legend */}
      <div className="w-full space-y-1.5 rounded-lg border border-ink/10 bg-surface-muted p-3">
        <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-2">
          Score Breakdown
        </p>
        <WeightBar
          label="Skills (65%)"
          fill={
            score >= 75 ? "success" : score >= 50 ? "warning" : "destructive"
          }
        />
        <WeightBar label="Keywords (35%)" fill="neutral" />
      </div>
    </div>
  );
}

function WeightBar({
  label,
  fill,
}: {
  label: string;
  fill: "success" | "warning" | "destructive" | "neutral";
}) {
  const colours: Record<string, string> = {
    success: "bg-success",
    warning: "bg-warning",
    destructive: "bg-destructive",
    neutral: "bg-ink/25",
  };
  return (
    <div className="flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full shrink-0 ${colours[fill]}`} />
      <span className="text-[11px] text-muted-foreground">{label}</span>
    </div>
  );
}

// ── Skill chips ─────────────────────────────────────────────────────────────

function SkillChip({
  label,
  variant,
}: {
  label: string;
  variant: "matched" | "missing";
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
        variant === "matched"
          ? "border-success/40 bg-success/8 text-success"
          : "border-destructive/40 bg-destructive-soft text-destructive"
      }`}
    >
      {variant === "matched" ? (
        <CheckCircle2 className="h-3 w-3 shrink-0" />
      ) : (
        <XCircle className="h-3 w-3 shrink-0" />
      )}
      {label}
    </span>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function MatchDashboardPage() {
  const { resumeId, jobId } = useParams<{ resumeId: string; jobId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Load JD metadata for breadcrumb
  const { data: jd } = useQuery<JobDescriptionDetail>({
    queryKey: ["jobs", jobId],
    queryFn: () => jobsApi.get(jobId!),
    enabled: !!jobId,
  });

  // Load resume name for breadcrumb
  const { data: resumes } = useQuery<ResumeListItem[]>({
    queryKey: ["resumes"],
    queryFn: resumeApi.list,
  });
  const resume = resumes?.find((r) => r.id === resumeId);

  // Try to fetch existing match result first
  const {
    data: match,
    isLoading,
    error: fetchError,
  } = useQuery<ResumeMatchResult>({
    queryKey: ["match", resumeId, jobId],
    queryFn: () => matchApi.get(resumeId!, jobId!),
    enabled: !!resumeId && !!jobId,
    retry: false, // 404 means not generated yet
  });

  // Mutation to trigger/re-run the match
  const generateMutation = useMutation({
    mutationFn: () => matchApi.generate(resumeId!, jobId!),
    onSuccess: (data) => {
      queryClient.setQueryData(["match", resumeId, jobId], data);
    },
  });

  const isNotFound = !match && !isLoading && fetchError;

  return (
    <>
      <Topbar
        title="Match Analysis"
        subtitle={
          jd && resume
            ? `${resume.original_file_name} vs ${jd.title}${jd.company ? ` @ ${jd.company}` : ""}`
            : "Resume vs Job Description"
        }
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/jd-matcher/${jobId}`)}
              id="btn-back-to-jd"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            {match && (
              <Button
                variant="outline"
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending}
                id="btn-re-run-match"
              >
                {generateMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Re-run
              </Button>
            )}
          </div>
        }
      />

      <div className="p-4 md:p-6 lg:p-8 max-w-6xl">
        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-28 text-muted-foreground">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading match analysis…
          </div>
        )}

        {/* Generate state (match not yet run or 404) */}
        {isNotFound &&
          !generateMutation.isPending &&
          !generateMutation.data && (
            <Card>
              <div className="flex flex-col items-center gap-5 py-20 text-center px-6">
                <div className="grid h-16 w-16 place-items-center rounded-2xl bg-primary-soft">
                  <Zap className="h-7 w-7 text-ink" strokeWidth={1.5} />
                </div>
                <div>
                  <h2 className="font-display text-xl text-foreground">
                    Run Match Analysis
                  </h2>
                  <p className="mt-2 max-w-sm text-sm text-muted-foreground">
                    Compare this resume against the job description to get a
                    match score, identify your skill gaps, and get targeted
                    suggestions.
                  </p>
                </div>
                {generateMutation.isError && (
                  <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive-soft px-4 py-2.5 text-sm text-destructive">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    {(generateMutation.error as Error).message}
                  </div>
                )}
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => generateMutation.mutate()}
                  id="btn-generate-match"
                >
                  <Zap className="h-4 w-4" />
                  Generate Match Score
                </Button>
              </div>
            </Card>
          )}

        {/* Running state */}
        {generateMutation.isPending && (
          <Card>
            <div className="flex flex-col items-center gap-4 py-24 text-center">
              <Loader2 className="h-10 w-10 animate-spin text-ink/40" />
              <p className="text-sm font-medium text-foreground">
                Analysing your resume against the job description…
              </p>
              <p className="text-xs text-muted-foreground">
                Extracting skills · Computing overlap · Scoring
              </p>
            </div>
          </Card>
        )}

        {/* Results */}
        {(match || generateMutation.data) && !generateMutation.isPending && (
          <div className="space-y-6">
            <MatchResults result={(generateMutation.data ?? match)!} />
            <OptimizationSection resumeId={resumeId!} jobId={jobId!} />
          </div>
        )}
      </div>
    </>
  );
}

// ── Results layout ─────────────────────────────────────────────────────────

function MatchResults({ result }: { result: ResumeMatchResult }) {
  const matched = result.matched_skills ?? [];
  const missing = result.missing_skills ?? [];

  const hasMatchedList = matched.length > 0;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* ── Left column: Score ring + metadata ── */}
      <div className="lg:col-span-1 space-y-6">
        <Card>
          <div className="p-6">
            <p className="eyebrow mb-5 text-center">Job Match Score</p>
            <ScoreRing score={result.match_score} />
          </div>
        </Card>

        {/* Quick stats */}
        <Card>
          <CardHeader
            title="Summary"
            subtitle="Extracted from job description"
          />
          <dl className="divide-y divide-border">
            <StatRow
              label="Missing Skills"
              value={missing.length}
              tone={missing.length === 0 ? "success" : "destructive"}
            />
            <StatRow
              label="Keyword Gaps"
              value={(result.missing_keywords ?? []).length}
              tone={
                (result.missing_keywords ?? []).length === 0
                  ? "success"
                  : "warning"
              }
            />
            <StatRow
              label="Suggestions"
              value={(result.suggestions ?? []).length}
              tone="neutral"
            />
          </dl>
        </Card>
      </div>

      {/* ── Right column: Detail cards ── */}
      <div className="lg:col-span-2 space-y-6">
        {/* Matched Skills */}
        {hasMatchedList && (
          <Card>
            <CardHeader
              title="Matched Skills"
              subtitle="Skills from the job description found in your resume"
              action={<Pill tone="success">{matched.length} found</Pill>}
            />
            <div className="flex flex-wrap gap-2 p-5">
              {matched.map((skill) => (
                <SkillChip key={skill} label={skill} variant="matched" />
              ))}
            </div>
          </Card>
        )}

        {/* Missing Skills */}
        <Card>
          <CardHeader
            title="Missing Skills"
            subtitle="Required skills from the job description not detected in your resume"
            action={
              <Pill tone={missing.length === 0 ? "success" : "destructive"}>
                {missing.length === 0
                  ? "None"
                  : `${missing.length} gap${missing.length > 1 ? "s" : ""}`}
              </Pill>
            }
          />
          {missing.length === 0 ? (
            <div className="flex items-center gap-3 p-5 text-sm text-success">
              <CheckCircle2 className="h-5 w-5 shrink-0" />
              Your resume covers all detected skills from this job description.
            </div>
          ) : (
            <div className="flex flex-wrap gap-2 p-5">
              {missing.map((skill) => (
                <SkillChip key={skill} label={skill} variant="missing" />
              ))}
            </div>
          )}
        </Card>

        {/* Missing Keywords */}
        {(result.missing_keywords ?? []).length > 0 && (
          <Card>
            <CardHeader
              title="Keyword Gaps"
              subtitle="High-frequency terms in the JD not found in your resume"
              action={
                <Pill tone="warning">
                  {result.missing_keywords!.length} term
                  {result.missing_keywords!.length > 1 ? "s" : ""}
                </Pill>
              }
            />
            <div className="flex flex-wrap gap-2 p-5">
              {result.missing_keywords!.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-1.5 rounded-full border border-warning/40 bg-warning-soft px-3 py-1 text-xs font-medium text-warning-foreground"
                >
                  <Tag className="h-3 w-3 shrink-0" />
                  {kw}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Suggestions */}
        {(result.suggestions ?? []).length > 0 && (
          <Card>
            <CardHeader
              title="Suggestions"
              subtitle="Actionable steps to improve your match score"
            />
            <div className="divide-y divide-border">
              {result.suggestions!.map((s, i) => (
                <div
                  key={i}
                  className="flex gap-3 px-5 py-4 text-sm"
                  id={`suggestion-${i}`}
                >
                  <div className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary-soft">
                    <Lightbulb className="h-3 w-3 text-ink" />
                  </div>
                  <p className="text-foreground leading-relaxed">{s}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

// ── Stat row helper ────────────────────────────────────────────────────────

function StatRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "destructive" | "warning" | "neutral";
}) {
  const colours: Record<string, string> = {
    success: "text-success",
    destructive: "text-destructive",
    warning: "text-warning-foreground",
    neutral: "text-foreground",
  };
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className={`font-mono text-sm font-semibold ${colours[tone]}`}>
        {value}
      </dd>
    </div>
  );
}
