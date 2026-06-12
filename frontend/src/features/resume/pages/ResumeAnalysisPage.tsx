import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Wand2,
  RefreshCw,
  Lightbulb,
  Star,
  BookOpen,
  Code2,
  Briefcase,
  GraduationCap,
} from "lucide-react";
import {
  Card,
  CardHeader,
  Topbar,
  Button,
  Pill,
} from "../../../components/ui-kit";
import {
  resumeApi,
  type ATSAnalysis,
  type ResumeListItem,
  type SectionQuality,
} from "../../../lib/api/resumes";
import { useState } from "react";

// ── Helpers ──────────────────────────────────────────────────────────────────

function scoreColor(score: number, max: number): string {
  const pct = (score / max) * 100;
  if (pct >= 75) return "text-success";
  if (pct >= 45) return "text-warning";
  return "text-destructive";
}

function scoreBarColor(score: number, max: number): string {
  const pct = (score / max) * 100;
  if (pct >= 75) return "bg-success";
  if (pct >= 45) return "bg-warning";
  return "bg-destructive";
}

function atsBand(score: number): { label: string; color: string } {
  if (score >= 80) return { label: "Excellent", color: "text-success" };
  if (score >= 60) return { label: "Good", color: "text-success" };
  if (score >= 40) return { label: "Fair", color: "text-warning" };
  return { label: "Needs Work", color: "text-destructive" };
}

// ── Animated score ring ──────────────────────────────────────────────────────
function ScoreRing({ score }: { score: number }) {
  const r = 56;
  const circ = 2 * Math.PI * r;
  const offset = circ - (circ * score) / 100;
  const band = atsBand(score);

  const strokeClass =
    score >= 80
      ? "text-success"
      : score >= 50
        ? "text-warning"
        : "text-destructive";

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <svg
          width="140"
          height="140"
          viewBox="0 0 140 140"
          className="-rotate-90"
        >
          {/* Track */}
          <circle
            cx="70"
            cy="70"
            r={r}
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            className="text-surface-muted"
          />
          {/* Progress */}
          <circle
            cx="70"
            cy="70"
            r={r}
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={`${strokeClass} transition-all duration-700 ease-out`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-display text-4xl font-bold leading-none text-foreground">
            {Math.round(score)}
          </span>
          <span className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            /100
          </span>
        </div>
      </div>
      <div className={`mt-2 font-mono text-sm font-semibold ${band.color}`}>
        {band.label}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">ATS Match Score</div>
    </div>
  );
}

// ── Section quality bar ───────────────────────────────────────────────────────
function SectionBar({
  label,
  score,
  max,
  icon,
}: {
  label: string;
  score: number;
  max: number;
  icon: React.ReactNode;
}) {
  const pct = Math.round((score / max) * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-foreground font-medium">
          <span className="text-muted-foreground">{icon}</span>
          {label}
        </div>
        <div className={`font-mono text-xs ${scoreColor(score, max)}`}>
          {score}/{max}
        </div>
      </div>
      <div className="h-2 w-full rounded-full bg-surface-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${scoreBarColor(score, max)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
type Tab = "strengths" | "weaknesses" | "recommendations";

function FeedbackTabs({
  analysis,
}: {
  analysis: ATSAnalysis;
}) {
  const [tab, setTab] = useState<Tab>("strengths");

  const tabs: { id: Tab; label: string; count: number; icon: React.ReactNode }[] = [
    {
      id: "strengths",
      label: "Strengths",
      count: analysis.strengths?.length ?? 0,
      icon: <CheckCircle2 className="h-4 w-4" />,
    },
    {
      id: "weaknesses",
      label: "Issues",
      count: analysis.weaknesses?.length ?? 0,
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      id: "recommendations",
      label: "Action Plan",
      count: analysis.recommendations?.length ?? 0,
      icon: <Lightbulb className="h-4 w-4" />,
    },
  ];

  const tabContent: Record<
    Tab,
    { items: string[]; icon: React.ReactNode; color: string }
  > = {
    strengths: {
      items: analysis.strengths ?? [],
      icon: <CheckCircle2 className="h-4 w-4 shrink-0" />,
      color: "text-success",
    },
    weaknesses: {
      items: analysis.weaknesses ?? [],
      icon: <AlertTriangle className="h-4 w-4 shrink-0" />,
      color: "text-warning",
    },
    recommendations: {
      items: analysis.recommendations ?? [],
      icon: <AlertCircle className="h-4 w-4 shrink-0" />,
      color: "text-primary",
    },
  };

  const current = tabContent[tab];

  return (
    <Card>
      {/* Tab headers */}
      <div className="flex border-b border-border overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-3 text-xs font-mono uppercase tracking-wider whitespace-nowrap transition-colors border-b-2 -mb-[2px] ${
              tab === t.id
                ? "border-ink text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <span
              className={
                tab === t.id
                  ? t.id === "strengths"
                    ? "text-success"
                    : t.id === "weaknesses"
                      ? "text-warning"
                      : "text-primary"
                  : ""
              }
            >
              {t.icon}
            </span>
            {t.label}
            <span
              className={`ml-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                tab === t.id
                  ? "bg-ink text-paper"
                  : "bg-surface-muted text-muted-foreground"
              }`}
            >
              {t.count}
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 sm:p-5 space-y-2.5 min-h-[200px]">
        {current.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Star className="h-8 w-8 mb-2 opacity-30" />
            <p className="text-sm">Nothing to show here.</p>
          </div>
        ) : (
          current.items.map((item, i) => (
            <div
              key={i}
              className="flex gap-3 text-sm p-3 rounded-lg bg-surface-muted/40 hover:bg-surface-muted transition-colors"
            >
              <span className={`${current.color} mt-0.5`}>{current.icon}</span>
              <span className="text-foreground leading-relaxed">{item}</span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

// ── Keyword cloud ─────────────────────────────────────────────────────────────
function KeywordCloud({ analysis }: { analysis: ATSAnalysis }) {
  if (!analysis.keyword_analysis) return null;

  // Group string-value keywords by category prefix
  const entries = Object.entries(analysis.keyword_analysis).filter(
    ([, v]) => typeof v === "string"
  ) as [string, string][];

  if (entries.length === 0) return null;

  // Group by category family
  const groups: Record<string, [string, string][]> = {};
  for (const [kw, cat] of entries) {
    const family = cat.includes("languages")
      ? "Languages"
      : cat.includes("frameworks")
        ? "Frameworks"
        : cat.includes("databases")
          ? "Databases"
          : cat.includes("devops")
            ? "DevOps & Cloud"
            : cat.includes("tools")
              ? "Tools"
              : cat.includes("concepts")
                ? "Concepts"
                : cat.toLowerCase().includes("soft")
                  ? "Soft Skills"
                  : "Other";
    if (!groups[family]) groups[family] = [];
    groups[family].push([kw, cat]);
  }

  const familyTone: Record<
    string,
    "success" | "primary" | "warning" | "neutral" | "purple"
  > = {
    Languages: "success",
    Frameworks: "primary",
    Databases: "warning",
    "DevOps & Cloud": "purple",
    Tools: "neutral",
    Concepts: "neutral",
    "Soft Skills": "warning",
    Other: "neutral",
  };

  return (
    <Card>
      <CardHeader
        title="Detected Skills"
        subtitle="Skills and keywords identified in your resume"
        eyebrow="KEYWORD ANALYSIS"
      />
      <div className="p-4 sm:p-5 space-y-4">
        {Object.entries(groups).map(([family, kws]) => (
          <div key={family}>
            <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {family}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {kws.map(([kw], i) => (
                <Pill key={i} tone={familyTone[family] ?? "neutral"}>
                  {kw}
                </Pill>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ── Validation Card ───────────────────────────────────────────────────────────
function ValidationCard({ analysis }: { analysis: ATSAnalysis }) {
  const validation = analysis.keyword_analysis?.resume_validation as
    | {
        confidence: number;
        detected_sections: string[];
        missing_sections: string[];
        warning?: string;
      }
    | undefined;

  if (!validation) return null;

  const conf = validation.confidence ?? 0;
  const confidenceTone =
    conf >= 70 ? "success" : conf >= 40 ? "warning" : "destructive";

  return (
    <Card>
      <CardHeader
        title="Document Validation"
        subtitle="Pre-analysis resume classification"
        eyebrow="RESUME CLASSIFIER"
        action={
          <Pill tone={confidenceTone}>{conf}% confidence</Pill>
        }
      />
      <div className="p-4 sm:p-5 space-y-4">
        {validation.warning && (
          <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning-soft px-4 py-3 text-sm text-warning-foreground">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>{validation.warning}</span>
          </div>
        )}

        {/* Confidence bar */}
        <div>
          <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
            <span>Resume Confidence</span>
            <span className="font-mono">{conf}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-surface-muted overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${conf >= 70 ? "bg-success" : conf >= 40 ? "bg-warning" : "bg-destructive"}`}
              style={{ width: `${conf}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Detected sections */}
          {(validation.detected_sections ?? []).length > 0 && (
            <div>
              <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-success">
                Detected
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(validation.detected_sections ?? []).map((s) => (
                  <Pill key={s} tone="success">
                    <CheckCircle2 className="mr-1 h-2.5 w-2.5" />
                    {s}
                  </Pill>
                ))}
              </div>
            </div>
          )}

          {/* Missing sections */}
          {(validation.missing_sections ?? []).length > 0 && (
            <div>
              <div className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Missing
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(validation.missing_sections ?? []).map((s) => (
                  <Pill key={s} tone="neutral">
                    {s}
                  </Pill>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

// ── Section Quality Breakdown ─────────────────────────────────────────────────
function SectionQualityCard({ sq }: { sq: SectionQuality }) {
  return (
    <Card>
      <CardHeader
        title="Section Quality"
        subtitle="How well each section scores based on content quality"
        eyebrow="CONTENT ANALYSIS"
        action={
          <Pill tone={sq.total_section_quality_score / sq.max_section_quality_score >= 0.75 ? "success" : sq.total_section_quality_score / sq.max_section_quality_score >= 0.45 ? "warning" : "destructive"}>
            {sq.total_section_quality_score}/{sq.max_section_quality_score}
          </Pill>
        }
      />
      <div className="p-4 sm:p-5 space-y-4">
        <SectionBar
          label="Experience"
          score={sq.experience_score}
          max={sq.breakdown?.experience?.max_score ?? 25}
          icon={<Briefcase className="h-4 w-4" />}
        />
        <SectionBar
          label="Skills"
          score={sq.skills_score}
          max={sq.breakdown?.skills?.max_score ?? 15}
          icon={<Code2 className="h-4 w-4" />}
        />
        <SectionBar
          label="Projects"
          score={sq.projects_score}
          max={sq.breakdown?.projects?.max_score ?? 12}
          icon={<BookOpen className="h-4 w-4" />}
        />
        <SectionBar
          label="Education"
          score={sq.education_score}
          max={sq.breakdown?.education?.max_score ?? 8}
          icon={<GraduationCap className="h-4 w-4" />}
        />
      </div>
    </Card>
  );
}

// ── Score Overview Card ───────────────────────────────────────────────────────
function ScoreOverview({
  analysis,
  onReAnalyze,
  isGenerating,
}: {
  analysis: ATSAnalysis;
  onReAnalyze: () => void;
  isGenerating: boolean;
}) {
  const formattingScore = analysis.keyword_analysis?.formatting_score as
    | number
    | undefined;
  const sq = analysis.keyword_analysis?.section_quality as
    | SectionQuality
    | undefined;

  return (
    <Card className="flex flex-col gap-6 p-5 sm:p-6">
      {/* Ring */}
      <ScoreRing score={analysis.ats_score} />

      {/* Sub-scores */}
      {(formattingScore !== undefined || sq) && (
        <div className="grid grid-cols-2 gap-3 border-t border-border pt-4">
          {formattingScore !== undefined && (
            <div className="text-center">
              <div
                className={`font-display text-2xl font-bold ${scoreColor(formattingScore, 40)}`}
              >
                {formattingScore}
              </div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-0.5">
                Formatting
              </div>
              <div className="font-mono text-[10px] text-muted-foreground/60">
                /40
              </div>
            </div>
          )}
          {sq && (
            <div className="text-center">
              <div
                className={`font-display text-2xl font-bold ${scoreColor(sq.total_section_quality_score, sq.max_section_quality_score)}`}
              >
                {sq.total_section_quality_score}
              </div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mt-0.5">
                Content
              </div>
              <div className="font-mono text-[10px] text-muted-foreground/60">
                /{sq.max_section_quality_score}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Timestamp */}
      <div className="text-center border-t border-border pt-4">
        <p className="text-xs text-muted-foreground">
          Last analyzed{" "}
          {new Intl.DateTimeFormat("en-US", {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
          }).format(new Date(analysis.created_at))}
        </p>
        <button
          onClick={onReAnalyze}
          disabled={isGenerating}
          className="mt-3 flex items-center justify-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40 mx-auto"
        >
          <RefreshCw
            className={`h-3 w-3 ${isGenerating ? "animate-spin" : ""}`}
          />
          Re-analyze
        </button>
      </div>
    </Card>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ResumeAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    data: analysis,
    isLoading: isAnalysisLoading,
    error: analysisError,
  } = useQuery<ATSAnalysis>({
    queryKey: ["resume-analysis", id],
    queryFn: () => resumeApi.getAnalysis(id!),
    enabled: !!id,
    retry: false,
  });

  const { data: resumes } = useQuery<ResumeListItem[]>({
    queryKey: ["resumes"],
    queryFn: resumeApi.list,
  });
  const resume = resumes?.find((r) => r.id === id);

  const analyzeMutation = useMutation({
    mutationFn: () => resumeApi.analyze(id!),
    onMutate: () => {
      setIsGenerating(true);
      setErrorMsg(null);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["resume-analysis", id], data);
    },
    onError: (err: Error) => {
      setErrorMsg(err.message || "Failed to generate analysis");
    },
    onSettled: () => {
      setIsGenerating(false);
    },
  });

  if (!id) return <div>Invalid Resume ID</div>;

  const sq = analysis?.keyword_analysis?.section_quality as
    | SectionQuality
    | undefined;

  return (
    <>
      <Topbar
        title="ATS Analysis"
        subtitle={resume ? `Analyzing: ${resume.original_file_name}` : "Loading..."}
        actions={
          <Link to="/resume-analyzer">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back
            </Button>
          </Link>
        }
      />

      <div className="space-y-5 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
        {/* Error banner */}
        {errorMsg && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive-soft px-4 py-3 text-sm text-destructive">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <div>
              <strong>Analysis Failed:</strong> {errorMsg}
            </div>
          </div>
        )}

        {/* Loading spinner */}
        {isAnalysisLoading && !isGenerating && !analysisError && (
          <div className="flex justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Empty / Generate state */}
        {(analysisError || (!analysis && !isAnalysisLoading)) &&
          !isGenerating && (
            <Card className="text-center py-16 sm:py-20 px-6">
              <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-primary-soft">
                <Wand2 className="h-8 w-8 text-ink" />
              </div>
              <h2 className="font-display text-2xl mb-2">
                Generate ATS Insights
              </h2>
              <p className="text-muted-foreground max-w-sm mx-auto mb-8 text-sm leading-relaxed">
                Our deterministic engine will analyze your resume format,
                validate sections, extract skills, and score your content
                quality — no AI guesswork.
              </p>
              <Button
                variant="primary"
                size="lg"
                onClick={() => analyzeMutation.mutate()}
              >
                <Wand2 className="mr-2 h-4 w-4" /> Analyze Resume
              </Button>
            </Card>
          )}

        {/* Generating state */}
        {isGenerating && (
          <Card className="text-center py-20 px-6">
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-5" />
            <h2 className="font-display text-xl text-foreground mb-2">
              Analyzing your resume…
            </h2>
            <p className="text-sm text-muted-foreground">
              Running through 40+ quality checks. Usually takes 5-10 seconds.
            </p>
          </Card>
        )}

        {/* Results */}
        {analysis && !isGenerating && (
          <div className="space-y-5">
            {/* Top row: score + feedback tabs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Score overview */}
              <div className="md:col-span-1">
                <ScoreOverview
                  analysis={analysis}
                  onReAnalyze={() => analyzeMutation.mutate()}
                  isGenerating={isGenerating}
                />
              </div>

              {/* Feedback tabs */}
              <div className="md:col-span-2">
                <FeedbackTabs analysis={analysis} />
              </div>
            </div>

            {/* Section quality bars */}
            {sq && <SectionQualityCard sq={sq} />}

            {/* Validation card */}
            <ValidationCard analysis={analysis} />

            {/* Keyword cloud */}
            <KeywordCloud analysis={analysis} />
          </div>
        )}
      </div>
    </>
  );
}
