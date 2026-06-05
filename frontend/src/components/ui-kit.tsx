// CareerPilot shared UI primitives — ported from the apply-accelerate-ai design system
import React from "react";
import { Bell } from "lucide-react";

// ── Card ──────────────────────────────────────────────
export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`border border-ink/15 bg-card ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
  eyebrow,
  className = "",
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  eyebrow?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-start justify-between gap-4 border-b border-ink/15 px-5 py-4 ${className}`}
    >
      <div className="min-w-0">
        {eyebrow && <div className="eyebrow mb-1.5">{eyebrow}</div>}
        <h3 className="font-display text-base text-foreground tracking-tight">
          {title}
        </h3>
        {subtitle && (
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

// ── StatCard ──────────────────────────────────────────
export function StatCard({
  label,
  value,
  delta,
  trend = "up",
  num,
}: {
  label: string;
  value: string;
  delta?: string;
  trend?: "up" | "down" | "flat";
  num?: string;
}) {
  const trendColor =
    trend === "up"
      ? "text-success"
      : trend === "down"
        ? "text-destructive"
        : "text-muted-foreground";
  return (
    <div className="relative flex flex-col justify-between border border-ink/15 bg-card p-5 min-h-[160px]">
      <div className="flex items-start justify-between">
        <div className="eyebrow">{label}</div>
        {num && (
          <span className="font-mono text-[10px] text-muted-foreground">
            {num}
          </span>
        )}
      </div>
      <div className="mt-4">
        <div className="numeral text-5xl text-foreground">{value}</div>
        {delta && (
          <div
            className={`mt-2 font-mono text-[11px] uppercase tracking-wider ${trendColor}`}
          >
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "■"} {delta}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Pill ──────────────────────────────────────────────
export function Pill({
  tone = "neutral",
  className = "",
  children,
}: {
  tone?:
    | "neutral"
    | "primary"
    | "success"
    | "warning"
    | "destructive"
    | "purple";
  className?: string;
  children: React.ReactNode;
}) {
  const tones: Record<string, string> = {
    neutral: "border-ink/20 text-foreground",
    primary: "border-ink text-foreground bg-ink/[0.04]",
    success: "border-success/40 text-success",
    warning: "border-warning/50 text-warning-foreground bg-warning-soft",
    destructive: "border-destructive/40 text-destructive",
    purple: "border-purple-400/50 text-purple-600 bg-purple-50",
  };
  return (
    <span
      className={`inline-flex items-center border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.14em] ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

// ── Button ────────────────────────────────────────────
export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline" | "ghost" | "subtle";
  size?: "sm" | "md" | "lg";
}) {
  const v: Record<string, string> = {
    primary: "bg-ink text-paper hover:bg-ink-2",
    outline:
      "border border-ink bg-transparent text-foreground hover:bg-ink hover:text-paper",
    ghost: "text-foreground hover:bg-muted",
    subtle: "border border-ink/20 bg-surface text-foreground hover:border-ink",
  };
  const sizes: Record<string, string> = {
    sm: "h-8 px-3 text-xs",
    md: "h-10 px-4 text-[13px]",
    lg: "h-12 px-6 text-sm",
  };
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium uppercase tracking-wider transition disabled:opacity-50 disabled:cursor-not-allowed ${v[variant]} ${sizes[size]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

// ── Topbar ────────────────────────────────────────────
export function Topbar({
  title,
  subtitle,
  actions,
}: {
  title: React.ReactNode;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  const dateString = new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="sticky top-0 z-20 border-b-2 border-ink bg-background">
      <div className="flex items-center justify-between px-8 pt-5 pb-2 border-b border-border">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          {dateString}
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
          Issue · {title}
        </div>
      </div>

      <div className="flex h-16 items-center gap-4 px-8">
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-2xl leading-none text-foreground">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1.5 text-[13px] text-muted-foreground truncate">
              {subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {actions}
          <button
            className="relative grid h-10 w-10 place-items-center border border-input bg-surface text-foreground hover:bg-muted"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" strokeWidth={1.5} />
            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-warning" />
          </button>
        </div>
      </div>
    </header>
  );
}
