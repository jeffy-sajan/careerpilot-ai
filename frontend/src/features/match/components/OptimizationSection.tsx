import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import {
  Loader2,
  Lightbulb,
  CheckCircle2,
  XCircle,
  Wand2,
  Copy,
  Settings,
  Key,
  ExternalLink,
  Shield,
} from "lucide-react";
import { Card, CardHeader, Button, Pill } from "../../../components/ui-kit";
import {
  optimizationsApi,
  type OptimizationResponse,
  type OptimizationStatus,
} from "../../../lib/api/optimizations";
import { callGeminiDirect } from "../../../lib/api/geminiClient";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

type AIProvider = "platform" | "personal";

const STORAGE_KEY_API = "gemini_api_key";
const STORAGE_KEY_PROVIDER = "ai_provider";

function getStoredProvider(): AIProvider {
  return (
    (localStorage.getItem(STORAGE_KEY_PROVIDER) as AIProvider) ?? "platform"
  );
}

function getStoredApiKey(): string {
  return localStorage.getItem(STORAGE_KEY_API) ?? "";
}

// ---------------------------------------------------------------------------
// Main Section
// ---------------------------------------------------------------------------

export function OptimizationSection({
  resumeId,
  jobId,
}: {
  resumeId: string;
  jobId?: string;
}) {
  const queryClient = useQueryClient();

  // AI Provider state
  const [provider, setProvider] = useState<AIProvider>(getStoredProvider);
  const [apiKey, setApiKey] = useState(getStoredApiKey);
  const [showSettings, setShowSettings] = useState(false);
  const [byokError, setByokError] = useState<string | null>(null);

  // Persist provider & key
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_PROVIDER, provider);
  }, [provider]);
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_API, apiKey);
  }, [apiKey]);

  // Fetch existing optimizations
  const { data: listData, isLoading } = useQuery({
    queryKey: ["optimizations", resumeId],
    queryFn: () => optimizationsApi.listForResume(resumeId),
    enabled: !!resumeId,
  });

  // ── Platform key mutation (existing flow) ──
  const platformMutation = useMutation({
    mutationFn: () => optimizationsApi.generate(resumeId, jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["optimizations", resumeId] });
    },
  });

  // ── BYOK mutation (new: prompt → Gemini direct → save) ──
  const byokMutation = useMutation({
    mutationFn: async () => {
      setByokError(null);

      // 1. Fetch assembled prompt from our backend
      const promptData = await optimizationsApi.getPrompt(resumeId, jobId);

      // 2. Call Gemini directly from the browser
      const suggestions = await callGeminiDirect(
        apiKey,
        promptData.model_name,
        promptData.prompt,
        promptData.response_schema,
      );

      // 3. Save results to our backend
      const run = await optimizationsApi.saveByok(
        resumeId,
        suggestions as unknown as Record<string, unknown>[],
        jobId,
      );

      return run;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["optimizations", resumeId] });
    },
    onError: (err: Error) => {
      setByokError(err.message);
    },
  });

  // Update status mutation
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: OptimizationStatus }) =>
      optimizationsApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["optimizations", resumeId] });
    },
  });

  const optimizations = listData?.optimizations ?? [];

  // Determine which mutation to fire
  const handleGenerate = () => {
    if (provider === "personal") {
      if (!apiKey.trim()) {
        setByokError("Please enter your Gemini API key first.");
        setShowSettings(true);
        return;
      }
      byokMutation.mutate();
    } else {
      platformMutation.mutate();
    }
  };

  const isPending = platformMutation.isPending || byokMutation.isPending;

  // Determine the error to display
  const displayError = (() => {
    if (byokError) return byokError;
    if (platformMutation.isError) {
      const msg = platformMutation.error?.message ?? "";
      // Intercept 503 to offer BYOK
      if (
        msg.includes("quota") ||
        msg.includes("503") ||
        msg.includes("exhausted")
      ) {
        return null; // handled by the quota-exhausted banner below
      }
      return msg || "Failed to generate suggestions. Please try again.";
    }
    return null;
  })();

  const isQuotaExhausted =
    platformMutation.isError &&
    (platformMutation.error?.message?.includes("quota") ||
      platformMutation.error?.message?.includes("503") ||
      platformMutation.error?.message?.includes("exhausted"));

  return (
    <Card>
      <CardHeader
        title="AI Resume Optimization"
        subtitle="Review and accept section-by-section improvements to better align your resume."
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
              className="text-muted-foreground"
            >
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={isPending}
            >
              {isPending ? (
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
              ) : (
                <Wand2 className="h-4 w-4 mr-2" />
              )}
              Generate Suggestions
            </Button>
          </div>
        }
      />

      <div className="p-5">
        {/* ── AI Provider Settings Panel ── */}
        {showSettings && (
          <AIProviderSettings
            provider={provider}
            apiKey={apiKey}
            onProviderChange={setProvider}
            onApiKeyChange={setApiKey}
          />
        )}

        {/* ── Quota Exhausted Banner ── */}
        {isQuotaExhausted && (
          <div className="mb-4 rounded-xl border border-warning/30 bg-warning-soft p-4">
            <p className="text-sm font-semibold text-warning-foreground mb-2">
              CareerPilot AI quota is currently exhausted.
            </p>
            <p className="text-xs text-muted-foreground mb-3">You can:</p>
            <div className="flex flex-col gap-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  1.
                </span>
                <span className="text-foreground">Try again later</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  2.
                </span>
                <button
                  className="text-foreground underline underline-offset-4 hover:text-muted-foreground transition-colors"
                  onClick={() => {
                    setProvider("personal");
                    setShowSettings(true);
                  }}
                >
                  Use your own Gemini API key →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Error Banner ── */}
        {displayError && (
          <div className="mb-4 text-sm text-destructive bg-destructive/10 p-3 rounded-lg border border-destructive/20">
            {displayError}
          </div>
        )}

        {/* ── Optimization Cards ── */}
        {isLoading ? (
          <div className="flex items-center justify-center py-10 text-muted-foreground">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading suggestions...
          </div>
        ) : optimizations.length === 0 ? (
          <div className="text-center py-10">
            <Lightbulb className="mx-auto h-10 w-10 text-muted-foreground opacity-50 mb-3" />
            <p className="text-sm text-muted-foreground">
              No optimizations generated yet. Click the button above to get AI
              suggestions.
            </p>
          </div>
        ) : (
          <div className="space-y-6 max-h-[600px] overflow-y-auto pr-3 premium-scrollbar">
            {optimizations.map((opt) => (
              <OptimizationCard
                key={opt.id}
                opt={opt}
                onAccept={() =>
                  statusMutation.mutate({ id: opt.id, status: "ACCEPTED" })
                }
                onReject={() =>
                  statusMutation.mutate({ id: opt.id, status: "REJECTED" })
                }
                isUpdating={
                  statusMutation.isPending &&
                  statusMutation.variables?.id === opt.id
                }
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// AI Provider Settings
// ---------------------------------------------------------------------------

function AIProviderSettings({
  provider,
  apiKey,
  onProviderChange,
  onApiKeyChange,
}: {
  provider: AIProvider;
  apiKey: string;
  onProviderChange: (p: AIProvider) => void;
  onApiKeyChange: (key: string) => void;
}) {
  return (
    <div className="mb-5 rounded-xl border border-border bg-surface-muted p-4 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <Settings className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          AI Provider Settings
        </span>
      </div>

      {/* Radio: Platform vs Personal */}
      <div className="space-y-2">
        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="radio"
            name="ai-provider"
            checked={provider === "platform"}
            onChange={() => onProviderChange("platform")}
            className="accent-current"
          />
          <div>
            <span className="text-sm font-medium text-foreground">
              CareerPilot AI
            </span>
            <span className="text-xs text-muted-foreground ml-2">
              (Default)
            </span>
          </div>
        </label>

        <label className="flex items-center gap-3 cursor-pointer group">
          <input
            type="radio"
            name="ai-provider"
            checked={provider === "personal"}
            onChange={() => onProviderChange("personal")}
            className="accent-current"
          />
          <div>
            <span className="text-sm font-medium text-foreground">
              Personal Gemini API Key
            </span>
          </div>
        </label>
      </div>

      {/* Personal Key Input */}
      {provider === "personal" && (
        <div className="ml-6 space-y-3 animate-in fade-in duration-200">
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="password"
              placeholder="Paste your Gemini API key…"
              value={apiKey}
              onChange={(e) => onApiKeyChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm bg-surface border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-ink focus:ring-1 focus:ring-ink/20 transition-colors"
            />
          </div>

          {/* Get a Key link */}
          <a
            href="https://aistudio.google.com/apikey"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
            Get a free API key from Google AI Studio
          </a>

          {/* Privacy Notice */}
          <div className="flex items-start gap-2 rounded-lg bg-surface border border-border p-3">
            <Shield className="h-4 w-4 text-success mt-0.5 shrink-0" />
            <div className="text-xs text-muted-foreground leading-relaxed">
              <p className="font-medium text-foreground mb-0.5">
                Your key is private.
              </p>
              <p>
                Stored only in your browser's local storage. Never synced. Never
                sent to our servers. Requests go directly from your browser to
                Google.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Optimization Card (unchanged logic, same as before)
// ---------------------------------------------------------------------------

function OptimizationCard({
  opt,
  onAccept,
  onReject,
  isUpdating,
}: {
  opt: OptimizationResponse;
  onAccept: () => void;
  onReject: () => void;
  isUpdating: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(opt.suggested_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`rounded-xl border p-4 transition-colors ${
        opt.status === "ACCEPTED"
          ? "border-success/30 bg-success/5"
          : opt.status === "REJECTED"
            ? "border-destructive/30 bg-destructive/5 opacity-70"
            : "border-border bg-surface-muted"
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Pill tone="neutral">{opt.section}</Pill>
          <Pill tone="warning">{opt.optimization_type.replace("_", " ")}</Pill>
        </div>
        <div className="flex items-center gap-2">
          {opt.status === "PENDING" ? (
            <>
              <Button
                size="sm"
                variant="outline"
                className="h-8 border-destructive text-destructive hover:bg-destructive/10"
                onClick={onReject}
                disabled={isUpdating}
              >
                <XCircle className="h-4 w-4 mr-1" /> Reject
              </Button>
              <Button
                size="sm"
                variant="primary"
                className="h-8 bg-success hover:bg-success/90 border-transparent text-white"
                onClick={onAccept}
                disabled={isUpdating}
              >
                <CheckCircle2 className="h-4 w-4 mr-1" /> Accept
              </Button>
            </>
          ) : (
            <span
              className={`text-xs font-semibold ${opt.status === "ACCEPTED" ? "text-success" : "text-destructive"}`}
            >
              {opt.status}
            </span>
          )}
          <Button
            size="sm"
            variant="outline"
            className="h-8 text-muted-foreground ml-2"
            onClick={handleCopy}
          >
            {copied ? (
              <CheckCircle2 className="h-4 w-4 mr-1 text-success" />
            ) : (
              <Copy className="h-4 w-4 mr-1" />
            )}
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-2">
            Original
          </h4>
          <div className="text-sm p-3 rounded bg-surface border border-border line-through opacity-70 whitespace-pre-wrap">
            {opt.original_text}
          </div>
        </div>
        <div>
          <h4 className="text-xs font-semibold uppercase text-success mb-2">
            Suggested
          </h4>
          <div className="text-sm p-3 rounded bg-success/10 border border-success/30 text-foreground whitespace-pre-wrap">
            {opt.suggested_text}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border flex gap-3 text-sm">
        <div className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary-soft">
          <Lightbulb className="h-3 w-3 text-ink" />
        </div>
        <p className="text-muted-foreground italic leading-relaxed">
          {opt.reasoning}
        </p>
      </div>
    </div>
  );
}
