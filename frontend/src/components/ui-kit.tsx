// CareerPilot shared UI primitives — ported from the apply-accelerate-ai design system
import React from "react";

// ── Card ──────────────────────────────────────────────
export function Card({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={`border border-ink/15 bg-card ${className}`}>{children}</div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
  eyebrow,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-ink/15 px-5 py-4">
      <div className="min-w-0">
        {eyebrow && <div className="eyebrow mb-1.5">{eyebrow}</div>}
        <h3 className="font-display text-base text-foreground tracking-tight">{title}</h3>
        {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// ── StatCard ──────────────────────────────────────────
export function StatCard({
  label, value, delta, trend = "up", num,
}: {
  label: string; value: string; delta?: string; trend?: "up" | "down" | "flat"; num?: string;
}) {
  const trendColor =
    trend === "up" ? "text-success" : trend === "down" ? "text-destructive" : "text-muted-foreground";
  return (
    <div className="relative flex flex-col justify-between border border-ink/15 bg-card p-5 min-h-[160px]">
      <div className="flex items-start justify-between">
        <div className="eyebrow">{label}</div>
        {num && <span className="font-mono text-[10px] text-muted-foreground">{num}</span>}
      </div>
      <div className="mt-4">
        <div className="numeral text-5xl text-foreground">{value}</div>
        {delta && (
          <div className={`mt-2 font-mono text-[11px] uppercase tracking-wider ${trendColor}`}>
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "■"} {delta}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Pill ──────────────────────────────────────────────
export function Pill({
  tone = "neutral", className = "", children,
}: {
  tone?: "neutral" | "primary" | "success" | "warning" | "destructive";
  className?: string;
  children: React.ReactNode;
}) {
  const tones: Record<string, string> = {
    neutral:     "border-ink/20 text-foreground",
    primary:     "border-ink text-foreground bg-ink/[0.04]",
    success:     "border-success/40 text-success",
    warning:     "border-warning/50 text-warning-foreground bg-warning-soft",
    destructive: "border-destructive/40 text-destructive",
  };
  return (
    <span className={`inline-flex items-center border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] ${tones[tone]} ${className}`}>
      {children}
    </span>
  );
}

// ── Button ────────────────────────────────────────────
export function Button({
  children, variant = "primary", className = "", ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline" | "ghost" | "subtle";
}) {
  const v: Record<string, string> = {
    primary: "bg-ink text-paper hover:bg-ink-2",
    outline: "border border-ink bg-transparent text-foreground hover:bg-ink hover:text-paper",
    ghost:   "text-foreground hover:bg-muted",
    subtle:  "border border-ink/20 bg-surface text-foreground hover:border-ink",
  };
  return (
    <button
      className={`inline-flex h-10 items-center justify-center gap-2 px-4 text-[13px] font-medium uppercase tracking-wider transition disabled:opacity-50 disabled:cursor-not-allowed ${v[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

// ── Topbar ────────────────────────────────────────────
export function Topbar({
  title, subtitle, actions,
}: {
  title: string; subtitle?: string; actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-ink/15 bg-card px-6 py-5">
      <div>
        <h1 className="font-display text-xl text-foreground">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
