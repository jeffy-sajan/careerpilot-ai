// AppSidebar — ported from apply-accelerate-ai with CareerPilot routing
import { useMemo } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  LayoutDashboard,
  FileText,
  ShieldCheck,
  Target,
  Kanban,
  BarChart3,
  Settings,
  LogOut,
} from "lucide-react";

const nav = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard, num: "01" },
  {
    label: "Resume Analyzer",
    to: "/resume-analyzer",
    icon: FileText,
    num: "02",
  },
  { label: "ATS Analysis", to: "/ats-analysis", icon: ShieldCheck, num: "03" },
  { label: "JD Matcher", to: "/jd-matcher", icon: Target, num: "04" },
  { label: "Job Tracker", to: "/job-tracker", icon: Kanban, num: "05" },
  { label: "Analytics", to: "/analytics", icon: BarChart3, num: "06" },
  { label: "Settings", to: "/settings", icon: Settings, num: "07" },
] as const;

const MOTIVATIONAL_QUOTES = [
  {
    quote: "The only way to do great work is to love what you do.",
    author: "Steve Jobs",
  },
  {
    quote: "Opportunities don't happen, you create them.",
    author: "Chris Grosser",
  },
  {
    quote: "The best way to predict the future is to create it.",
    author: "Peter Drucker",
  },
  {
    quote:
      "Choose a job you love, and you will never have to work a day in your life.",
    author: "Confucius",
  },
  {
    quote:
      "I am not a product of my circumstances. I am a product of my decisions.",
    author: "Stephen Covey",
  },
  {
    quote: "Believe you can and you're halfway there.",
    author: "Theodore Roosevelt",
  },
  {
    quote:
      "Find out what you like doing best, and get someone to pay you for it.",
    author: "Katharine Whitehorn",
  },
  {
    quote:
      "Your talent determines what you can do. Your motivation determines how much you are willing to do.",
    author: "Lou Holtz",
  },
  {
    quote:
      "Success is not final, failure is not fatal: it is the courage to continue that counts.",
    author: "Winston Churchill",
  },
] as const;

export function AppSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const selectedQuote = useMemo(() => {
    const index = Math.floor(Math.random() * MOTIVATIONAL_QUOTES.length);
    return MOTIVATIONAL_QUOTES[index];
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <aside className="hidden lg:flex w-72 shrink-0 flex-col bg-sidebar text-sidebar-foreground h-screen sticky top-0">
      {/* Brand */}
      <div className="sidebar-brand px-6 pt-7 pb-6 border-b border-sidebar-border">
        <div className="sidebar-brand-vol font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50">
          № 001 — Vol. 26
        </div>
        <NavLink
          to="/dashboard"
          className="sidebar-brand-title mt-3 block font-display text-[28px] leading-[0.9] text-sidebar-primary"
        >
          Career
          <br />
          Pilot<span className="text-warning">.</span>
        </NavLink>
        <div className="sidebar-brand-sub mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50">
          An AI Career Companion
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav flex-1 px-3 py-5 overflow-y-auto premium-scrollbar">
        <div className="sidebar-nav-title px-3 pb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40">
          Sections
        </div>
        <ul className="space-y-px">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `sidebar-link group flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
                      isActive
                        ? "bg-sidebar-accent text-sidebar-primary"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-primary"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <span
                        className={`font-mono text-[10px] tabular-nums ${isActive ? "text-warning" : "text-sidebar-foreground/40"}`}
                      >
                        {item.num}
                      </span>
                      <Icon className="h-4 w-4 opacity-80" strokeWidth={1.5} />
                      <span className="flex-1 font-medium tracking-tight">
                        {item.label}
                      </span>
                      {isActive && (
                        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                      )}
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>

        {/* Editorial callout */}
        <div className="sidebar-editorial mt-8 mx-3 border-t border-sidebar-border pt-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40">
            Career Wisdom
          </div>
          <p className="mt-2 font-display text-base leading-snug text-sidebar-primary">
            "{selectedQuote.quote}"
          </p>
          <p className="mt-2 text-xs text-sidebar-foreground/50">
            — {selectedQuote.author}
          </p>
        </div>
      </nav>

      {/* User footer */}
      <div className="sidebar-footer border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center bg-sidebar-primary text-sidebar-primary-foreground font-display text-sm shrink-0">
            {initials}
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-sm font-semibold text-sidebar-primary">
              {user?.name ?? "User"}
            </div>
            <div className="truncate text-[11px] text-sidebar-foreground/50 font-mono uppercase tracking-wider">
              {user?.email ?? ""}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 text-sidebar-foreground/60 hover:text-sidebar-primary transition-colors"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </aside>
  );
}
