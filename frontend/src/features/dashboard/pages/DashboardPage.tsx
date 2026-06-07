import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Send,
  Trophy,
  ShieldCheck,
  Upload,
  Target,
  PlusCircle,
  ArrowUpRight,
  FileText,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";
import { useAuth } from "../../../context/AuthContext";
import {
  Topbar,
  Card,
  CardHeader,
  Pill,
  Button,
} from "../../../components/ui-kit";
import { applicationsApi } from "../../../lib/api/applications";

const iconMap: Record<
  string,
  React.ComponentType<{ className?: string; strokeWidth?: number }>
> = {
  Send,
  Trophy,
  ShieldCheck,
  Upload,
  Target,
  PlusCircle,
  FileText,
};

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: metrics, isLoading } = useQuery({
    queryKey: ["applications", "metrics"],
    queryFn: () => applicationsApi.getMetrics(),
  });

  const [shouldAutoLoadInsights] = useState(() => {
    const today = new Date().toISOString().split("T")[0];
    const lastLoaded = localStorage.getItem("careerpilot_insights_last_loaded");
    return lastLoaded !== today;
  });

  const {
    data: insights,
    isFetching: isInsightsFetching,
    refetch: refetchInsights,
  } = useQuery({
    queryKey: ["applications", "insights"],
    queryFn: async () => {
      const today = new Date().toISOString().split("T")[0];
      localStorage.setItem("careerpilot_insights_last_loaded", today);
      const res = await applicationsApi.getInsights();
      localStorage.setItem("careerpilot_insights_data", JSON.stringify(res));
      return res;
    },
    initialData: () => {
      const cached = localStorage.getItem("careerpilot_insights_data");
      if (cached) {
        try {
          return JSON.parse(cached);
        } catch (e) {
          /* ignore parse error */
        }
      }
      return undefined;
    },
    staleTime: Infinity,
    gcTime: 24 * 60 * 60 * 1000,
    refetchOnMount: shouldAutoLoadInsights ? "always" : false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const now = new Date();
  const week = Math.ceil(
    Math.floor(
      (now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 86400000,
    ) / 7,
  );
  const yearStr = now.getFullYear().toString().substring(2);

  const funnel = [
    { s: "Applied", v: metrics?.total_applications || 0 },
    { s: "Active", v: metrics?.active_applications || 0 },
    { s: "Interview", v: metrics?.total_interviews || 0 },
    { s: "Offer", v: metrics?.total_offers || 0 },
  ];

  const trend = metrics?.monthly_trend || [];
  const startMonth = trend.length > 0 ? trend[0].m : "Jan";
  const endMonth = trend.length > 0 ? trend[trend.length - 1].m : "Dec";

  const momGrowth = metrics?.mom_growth_rate || 0;
  const isMomPositive = momGrowth > 0;
  const isMomNegative = momGrowth < 0;
  const momTone = isMomPositive
    ? "success"
    : isMomNegative
      ? "destructive"
      : "neutral";
  const momPrefix = isMomPositive ? "+" : "";
  const momText =
    momGrowth === 0 ? "Flat MoM" : `${momPrefix}${momGrowth}% MoM`;

  return (
    <>
      <Topbar
        title="Dashboard"
        subtitle={`Welcome back, ${user?.name || "User"} — keep up the momentum.`}
        actions={
          <Link to="/job-tracker">
            <Button variant="primary">
              <PlusCircle className="h-4 w-4" /> New Application
            </Button>
          </Link>
        }
      />

      <div className="p-4 md:p-8 lg:p-10 space-y-8 max-w-[1400px]">
        {/* Editorial intro */}
        <section className="grid grid-cols-12 gap-6 items-end border-b border-ink/15 pb-8">
          <div className="col-span-12 lg:col-span-8">
            <div className="eyebrow mb-3">
              Vol. {yearStr} · Week {week} · The Briefing
            </div>
            <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-[0.95] tracking-tight text-foreground">
              {metrics?.total_offers || "Zero"} offers,
              <br />
              {metrics?.total_interviews || "zero"} interviews,
              <br />
              <span className="text-muted-foreground">
                one focused week ahead.
              </span>
            </h2>
          </div>
          <div className="col-span-12 lg:col-span-4 border-l border-ink/15 pl-6">
            <div className="eyebrow mb-2">Editor's Note</div>
            <p className="text-sm leading-relaxed text-foreground">
              Your interview rate is currently{" "}
              <b>{metrics?.interview_rate || 0}%</b>.
              {(metrics?.interview_rate || 0) < 15
                ? " Stay consistent with your applications and consider tailoring your resumes to specific job descriptions to boost this metric further."
                : " You are performing above average. Keep refining your strategy and preparing for upcoming loops."}
            </p>
          </div>
        </section>

        {/* Bento: KPIs */}
        <section className="grid grid-cols-12 gap-px bg-ink/15 border border-ink/15">
          <KpiCell
            label="Total Applications"
            value={isLoading ? "—" : String(metrics?.total_applications || 0)}
            delta="+0 this week"
            num="01"
          />
          <KpiCell
            label="Interviews"
            value={isLoading ? "—" : String(metrics?.total_interviews || 0)}
            delta="Active pipeline"
            num="02"
          />
          <KpiCell
            label="Offers"
            value={isLoading ? "—" : String(metrics?.total_offers || 0)}
            delta="Secured"
            num="03"
          />
          <KpiCell
            label="Interview Rate"
            value={isLoading ? "—" : String(metrics?.interview_rate || 0)}
            suffix="%"
            delta="Conversion"
            num="04"
          />
        </section>

        {/* Bento row 2 */}
        <section className="grid grid-cols-12 gap-6">
          {/* Big chart */}
          <Card className="col-span-12 lg:col-span-8">
            <CardHeader
              eyebrow="Analytics · 12-Month Trend"
              title="Monthly Application Activity"
              subtitle={`Submissions volume, ${startMonth} → ${endMonth}`}
              action={
                <Pill tone={momTone as "success" | "destructive" | "neutral"}>
                  {momText}
                </Pill>
              }
            />
            <div className="h-80 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={metrics?.monthly_trend || []}
                  margin={{ top: 12, right: 12, left: -10, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="ink-fill" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="0%"
                        stopColor="oklch(0.18 0.005 270)"
                        stopOpacity={0.85}
                      />
                      <stop
                        offset="100%"
                        stopColor="oklch(0.18 0.005 270)"
                        stopOpacity={0.05}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    stroke="oklch(0.82 0.012 85)"
                    strokeDasharray="2 4"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="m"
                    tick={{
                      fontSize: 10,
                      fill: "oklch(0.45 0.008 270)",
                      fontFamily: "JetBrains Mono",
                    }}
                    axisLine={{ stroke: "oklch(0.18 0.005 270)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{
                      fontSize: 10,
                      fill: "oklch(0.45 0.008 270)",
                      fontFamily: "JetBrains Mono",
                    }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: 0,
                      border: "1px solid oklch(0.18 0.005 270)",
                      fontSize: 11,
                      fontFamily: "JetBrains Mono",
                      background: "oklch(0.98 0.006 85)",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke="oklch(0.18 0.005 270)"
                    strokeWidth={1.5}
                    fill="url(#ink-fill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Pipeline funnel */}
          <Card className="col-span-12 lg:col-span-4">
            <CardHeader
              eyebrow="Index"
              title="Pipeline Funnel"
              subtitle="Applied → Offer"
            />
            <div className="p-5 space-y-3">
              {funnel.map((f, i) => {
                const pct = funnel[0].v > 0 ? (f.v / funnel[0].v) * 100 : 0;
                return (
                  <div key={f.s}>
                    <div className="flex items-baseline justify-between mb-1.5">
                      <div className="flex items-baseline gap-2">
                        <span className="font-mono text-[10px] text-muted-foreground">
                          0{i + 1}
                        </span>
                        <span className="text-sm font-medium">{f.s}</span>
                      </div>
                      <span className="numeral text-xl">
                        {String(f.v).padStart(2, "0")}
                      </span>
                    </div>
                    <div className="h-1.5 bg-paper-2 relative">
                      <div
                        className="absolute inset-y-0 left-0 bg-ink transition-all duration-1000"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
              <div className="pt-3 mt-2 border-t border-ink/15 flex items-center justify-between">
                <span className="eyebrow">Offer Rate</span>
                <span className="font-display text-lg">
                  {metrics?.offer_rate || 0}%
                </span>
              </div>
            </div>
          </Card>
        </section>

        {/* Bento row 3 */}
        <section className="grid grid-cols-12 gap-6">
          {/* Quick actions */}
          <Card className="col-span-12 lg:col-span-4">
            <CardHeader eyebrow="Tools" title="Quick Actions" />
            <div className="divide-y divide-ink/15">
              <ActionRow
                to="/resume-analyzer"
                icon={Upload}
                title="Analyze Resume"
                hint="Score against ATS rules"
                num="A"
              />
              <ActionRow
                to="/jd-matcher"
                icon={Target}
                title="Match a JD"
                hint="Paste a job description"
                num="B"
              />
              <ActionRow
                to="/job-tracker"
                icon={PlusCircle}
                title="Log Application"
                hint="Track a new opportunity"
                num="C"
              />
            </div>
          </Card>

          {/* Activity log */}
          <Card className="col-span-12 lg:col-span-5">
            <CardHeader
              eyebrow="Dispatch"
              title="Recent Activity"
              action={
                <button className="font-mono text-[10px] uppercase tracking-wider text-foreground hover:underline underline-offset-4">
                  View all →
                </button>
              }
            />
            <ol className="divide-y divide-ink/15">
              {(metrics?.recent_activity || []).map((a, i) => {
                const Icon = iconMap[a.icon] || FileText;
                return (
                  <li
                    key={i}
                    className="group flex items-start gap-4 px-5 py-4 hover:bg-paper-2/50 cursor-pointer transition-colors"
                  >
                    <span className="font-mono text-[10px] text-muted-foreground pt-1">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <Icon
                      className="h-4 w-4 mt-0.5 text-foreground"
                      strokeWidth={1.5}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm leading-snug text-foreground">
                        {a.title}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                        <span className="font-mono uppercase tracking-wider">
                          {a.time}
                        </span>
                        <span className="opacity-30">·</span>
                        <span className="font-mono uppercase tracking-wider">
                          {a.tag}
                        </span>
                      </div>
                    </div>
                    <ArrowUpRight
                      className="h-4 w-4 opacity-0 group-hover:opacity-100 transition"
                      strokeWidth={1.5}
                    />
                  </li>
                );
              })}
            </ol>
          </Card>

          {/* AI insight */}
          <div className="col-span-12 lg:col-span-3 bg-ink text-paper p-6 flex flex-col min-h-[300px]">
            <div className="flex items-center justify-between">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-paper/60">
                AI Insight
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => refetchInsights()}
                  disabled={isInsightsFetching}
                  className="text-paper/60 hover:text-white transition-colors disabled:opacity-50"
                  title="Reload AI Insight"
                >
                  <RefreshCw
                    className={`h-3.5 w-3.5 ${isInsightsFetching ? "animate-spin" : ""}`}
                    strokeWidth={1.5}
                  />
                </button>
                <Sparkles
                  className="h-3.5 w-3.5 text-warning"
                  strokeWidth={1.5}
                />
              </div>
            </div>
            {isInsightsFetching ? (
              <div className="flex flex-col h-full justify-center space-y-4 mt-6 animate-pulse">
                <div className="h-4 bg-paper/20 rounded w-full"></div>
                <div className="h-4 bg-paper/20 rounded w-5/6"></div>
                <div className="h-4 bg-paper/20 rounded w-4/6"></div>
              </div>
            ) : insights ? (
              <>
                <p className="mt-6 font-display text-2xl leading-tight tracking-tight">
                  "{insights.insight_text}"
                </p>
                <div className="mt-auto pt-6 border-t border-paper/15">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-paper/50 mb-2">
                    Recommended Actions
                  </div>
                  <div className="space-y-1.5 text-sm">
                    {insights.recommended_actions.map(
                      (act: { action: string; impact: string }, i: number) => (
                        <div key={i} className="flex justify-between gap-4">
                          <span className="truncate" title={act.action}>
                            {act.action}
                          </span>
                          <span
                            className={`font-mono shrink-0 ${act.impact.toLowerCase().includes("high") ? "text-warning" : "text-paper/50"}`}
                          >
                            {act.impact}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              </>
            ) : (
              <p className="mt-6 font-display text-xl leading-tight tracking-tight text-paper/60">
                Log more applications to receive AI insights.
              </p>
            )}
          </div>
        </section>

        {/* Bottom */}
        <section className="grid grid-cols-12 gap-6">
          <Card className="col-span-12 lg:col-span-7">
            <CardHeader
              eyebrow="Performance"
              title="Response Rate by Role Family"
              subtitle="Last 90 days"
            />
            <div className="h-56 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={metrics?.role_response_rates || []}
                  margin={{ top: 12, right: 12, left: -10, bottom: 0 }}
                >
                  <CartesianGrid
                    stroke="oklch(0.82 0.012 85)"
                    strokeDasharray="2 4"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="k"
                    tick={{
                      fontSize: 10,
                      fill: "oklch(0.45 0.008 270)",
                      fontFamily: "JetBrains Mono",
                    }}
                    axisLine={{ stroke: "oklch(0.18 0.005 270)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{
                      fontSize: 10,
                      fill: "oklch(0.45 0.008 270)",
                      fontFamily: "JetBrains Mono",
                    }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    cursor={{ fill: "oklch(0.93 0.01 85)" }}
                    contentStyle={{
                      borderRadius: 0,
                      border: "1px solid oklch(0.18 0.005 270)",
                      fontSize: 11,
                      fontFamily: "JetBrains Mono",
                    }}
                  />
                  <Bar dataKey="v" fill="oklch(0.18 0.005 270)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div className="col-span-12 lg:col-span-5 border border-ink/15 bg-paper-2/40 p-6">
            <div className="eyebrow mb-4">Upcoming Interviews</div>
            {!metrics?.upcoming_interviews ||
            metrics.upcoming_interviews.length === 0 ? (
              <div className="text-sm text-muted-foreground italic">
                No upcoming interviews scheduled. Apply to more roles!
              </div>
            ) : (
              <ul className="space-y-3">
                {metrics.upcoming_interviews.map((e, idx) => (
                  <li
                    key={idx}
                    className="flex items-baseline justify-between border-b border-ink/10 pb-3 last:border-0"
                  >
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                        {e.d}
                      </div>
                      <div className="text-sm font-medium mt-0.5">{e.t}</div>
                    </div>
                    <span className="font-mono text-sm tabular-nums">
                      {e.time}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

function KpiCell({
  label,
  value,
  suffix,
  delta,
  num,
}: {
  label: string;
  value: string;
  suffix?: string;
  delta: string;
  num: string;
}) {
  return (
    <div className="col-span-12 sm:col-span-6 xl:col-span-3 bg-card p-6 min-h-[180px] flex flex-col justify-between">
      <div className="flex items-start justify-between">
        <div className="eyebrow">{label}</div>
        <span className="font-mono text-[10px] text-muted-foreground">
          № {num}
        </span>
      </div>
      <div>
        <div className="flex items-baseline gap-1">
          <span className="numeral text-6xl text-foreground">{value}</span>
          {suffix && (
            <span className="font-mono text-sm text-muted-foreground">
              {suffix}
            </span>
          )}
        </div>
        <div className="mt-3 pt-3 border-t border-ink/15 font-mono text-[10px] uppercase tracking-wider text-foreground">
          {delta}
        </div>
      </div>
    </div>
  );
}

function ActionRow({
  to,
  icon: Icon,
  title,
  hint,
  num,
}: {
  to: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  title: string;
  hint: string;
  num: string;
}) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-4 px-5 py-4 hover:bg-ink hover:text-paper transition"
    >
      <span className="font-mono text-[10px] text-muted-foreground group-hover:text-paper/60">
        {num}
      </span>
      <Icon className="h-4 w-4" strokeWidth={1.5} />
      <div className="flex-1">
        <div className="text-sm font-medium">{title}</div>
        <div className="text-[11px] text-muted-foreground group-hover:text-paper/60">
          {hint}
        </div>
      </div>
      <ArrowUpRight
        className="h-4 w-4 opacity-40 group-hover:opacity-100"
        strokeWidth={1.5}
      />
    </Link>
  );
}
