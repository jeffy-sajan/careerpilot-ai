// AppSidebar — ported from apply-accelerate-ai with CareerPilot routing
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

export function AppSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
    <aside className="hidden lg:flex w-72 shrink-0 flex-col bg-sidebar text-sidebar-foreground">
      {/* Brand */}
      <div className="px-6 pt-7 pb-6 border-b border-sidebar-border">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50">
          № 001 — Vol. 26
        </div>
        <NavLink
          to="/dashboard"
          className="mt-3 block font-display text-[28px] leading-[0.9] text-sidebar-primary"
        >
          Career
          <br />
          Pilot<span className="text-warning">.</span>
        </NavLink>
        <div className="mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50">
          An AI Career Companion
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-5">
        <div className="px-3 pb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40">
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
                    `group flex items-center gap-3 px-3 py-2.5 text-sm transition-colors ${
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
        <div className="mt-8 mx-3 border-t border-sidebar-border pt-5">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40">
            This week
          </div>
          <p className="mt-2 font-display text-lg leading-tight text-sidebar-primary">
            "Tailored resumes get 3.2× more callbacks."
          </p>
          <p className="mt-2 text-xs text-sidebar-foreground/50">
            — Internal data, May 2026
          </p>
        </div>
      </nav>

      {/* User footer */}
      <div className="border-t border-sidebar-border p-4">
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
