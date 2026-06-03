import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Wand2,
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
} from "../../../lib/api/resumes";
import { useState } from "react";

export default function ResumeAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch the analysis
  const {
    data: analysis,
    isLoading: isAnalysisLoading,
    error: analysisError,
  } = useQuery<ATSAnalysis>({
    queryKey: ["resume-analysis", id],
    queryFn: () => resumeApi.getAnalysis(id!),
    enabled: !!id,
    retry: false, // Don't retry if it's 404
  });

  // Fetch the resume to show its name
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

  return (
    <>
      <Topbar
        title="ATS Analysis"
        subtitle={
          resume ? `Analyzing: ${resume.original_file_name}` : "Loading..."
        }
        actions={
          <Link to="/resume-analyzer">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to Resumes
            </Button>
          </Link>
        }
      />

      <div className="space-y-6 p-6 lg:p-8 max-w-5xl mx-auto">
        {/* Error handling */}
        {errorMsg && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive-soft px-4 py-3 text-sm text-destructive">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <div>
              <strong>Analysis Failed:</strong> {errorMsg}
            </div>
          </div>
        )}

        {isAnalysisLoading && !isGenerating && !analysisError && (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {/* Generate State / Empty State */}
        {(analysisError || (!analysis && !isAnalysisLoading)) &&
          !isGenerating && (
            <Card className="text-center py-16">
              <Wand2 className="h-12 w-12 mx-auto text-primary opacity-80 mb-4" />
              <h2 className="text-xl font-semibold mb-2">
                Generate ATS Insights
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto mb-6">
                Our AI engine will analyze your resume format, identify missing
                keywords, and suggest improvements to boost your ATS score.
              </p>
              <Button
                variant="primary"
                size="lg"
                onClick={() => analyzeMutation.mutate()}
              >
                <Wand2 className="mr-2 h-4 w-4" /> Generate Analysis
              </Button>
            </Card>
          )}

        {isGenerating && (
          <Card className="text-center py-20">
            <Loader2 className="h-10 w-10 animate-spin mx-auto text-primary mb-4" />
            <h2 className="text-lg font-medium text-foreground">
              AI is reading your resume...
            </h2>
            <p className="text-sm text-muted-foreground">
              This usually takes about 5-10 seconds.
            </p>
          </Card>
        )}

        {/* Results Dashboard */}
        {analysis && !isGenerating && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Score Overview */}
            <div className="md:col-span-1 space-y-6">
              <Card className="flex flex-col items-center justify-center p-8 text-center h-full">
                <div className="relative mb-4">
                  <svg className="w-32 h-32 transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      className="text-surface-muted"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="60"
                      stroke="currentColor"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray="377"
                      strokeDashoffset={377 - (377 * analysis.ats_score) / 100}
                      className={
                        analysis.ats_score >= 80
                          ? "text-success"
                          : analysis.ats_score >= 50
                            ? "text-warning"
                            : "text-destructive"
                      }
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold">
                      {analysis.ats_score.toFixed(0)}
                    </span>
                  </div>
                </div>
                <h3 className="text-lg font-semibold">ATS Match Score</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Based on industry standards
                </p>
              </Card>
            </div>

            {/* Detailed Insights */}
            <div className="md:col-span-2 space-y-6">
              {/* Strengths */}
              {analysis.strengths && analysis.strengths.length > 0 && (
                <Card>
                  <CardHeader
                    title="Strengths"
                    className="border-b border-border/50 pb-3"
                  />
                  <div className="p-5 space-y-3">
                    {analysis.strengths.map((str, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
                        <span className="text-foreground">{str}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Weaknesses */}
              {analysis.weaknesses && analysis.weaknesses.length > 0 && (
                <Card>
                  <CardHeader
                    title="Areas for Improvement"
                    className="border-b border-border/50 pb-3"
                  />
                  <div className="p-5 space-y-3">
                    {analysis.weaknesses.map((weak, i) => (
                      <div key={i} className="flex gap-3 text-sm">
                        <AlertTriangle className="h-5 w-5 text-warning shrink-0" />
                        <span className="text-foreground">{weak}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Recommendations */}
              {analysis.recommendations &&
                analysis.recommendations.length > 0 && (
                  <Card>
                    <CardHeader
                      title="Action Plan"
                      className="border-b border-border/50 pb-3"
                    />
                    <div className="p-5 space-y-3">
                      {analysis.recommendations.map((rec, i) => (
                        <div key={i} className="flex gap-3 text-sm">
                          <AlertCircle className="h-5 w-5 text-primary shrink-0" />
                          <span className="text-foreground">{rec}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
            </div>

            {/* Keyword Cloud */}
            {analysis.keyword_analysis &&
              Object.keys(analysis.keyword_analysis).length > 0 && (
                <div className="md:col-span-3">
                  <Card>
                    <CardHeader
                      title="Detected Keywords"
                      subtitle="Skills and keywords identified by the ATS"
                    />
                    <div className="p-5 flex flex-wrap gap-2">
                      {Object.entries(analysis.keyword_analysis).map(
                        ([keyword, category], i) => (
                          <Pill
                            key={i}
                            tone={
                              category.toLowerCase().includes("soft")
                                ? "warning"
                                : category.toLowerCase().includes("hard")
                                  ? "success"
                                  : "neutral"
                            }
                          >
                            {keyword}{" "}
                            <span className="opacity-60 text-[10px] ml-1">
                              {category}
                            </span>
                          </Pill>
                        ),
                      )}
                    </div>
                  </Card>
                </div>
              )}
          </div>
        )}
      </div>
    </>
  );
}
