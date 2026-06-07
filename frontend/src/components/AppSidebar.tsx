// AppSidebar — ported from apply-accelerate-ai with CareerPilot routing
import { useMemo, useState, useEffect } from "react";
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
  ChevronLeft,
  ChevronRight,
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

interface AppSidebarProps {
  isMobile?: boolean;
  onClose?: () => void;
}

export function AppSidebar({ isMobile, onClose }: AppSidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem("sidebarCollapsed");
    return saved === "true";
  });

  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", String(isCollapsed));
  }, [isCollapsed]);

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
    <aside
      className={`${
        isMobile
          ? "flex w-72"
          : "hidden lg:flex " + (isCollapsed ? "w-20" : "w-72")
      } shrink-0 flex-col bg-sidebar text-sidebar-foreground h-screen sticky top-0 transition-all duration-300 ease-in-out border-r border-sidebar-border`}
    >
      {/* Brand */}
      <div
        className={`sidebar-brand pt-7 pb-6 border-b border-sidebar-border transition-all duration-300 overflow-hidden relative group ${isCollapsed ? "px-4 flex flex-col items-center cursor-pointer" : "px-6"}`}
        onClick={isCollapsed ? () => setIsCollapsed(false) : undefined}
      >
        {!isCollapsed && (
          <button
            onClick={isMobile ? onClose : () => setIsCollapsed(true)}
            className="flex items-center justify-center text-sidebar-foreground/20 hover:text-sidebar-primary transition-colors absolute right-5 top-7"
            aria-label={isMobile ? "Close Sidebar" : "Collapse Sidebar"}
            title={isMobile ? "Close Sidebar" : "Collapse Sidebar"}
          >
            <ChevronLeft className="h-[18px] w-[18px]" strokeWidth={2} />
          </button>
        )}

        {!isCollapsed && (
          <div className="sidebar-brand-vol font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50 whitespace-nowrap">
            № 001 — Vol. 26
          </div>
        )}

        {isCollapsed ? (
          <div
            className="sidebar-brand-title block font-display leading-[0.9] text-sidebar-primary text-2xl mt-0 relative h-8 w-8 flex items-center justify-center"
            title="Expand Sidebar"
          >
            <span className="absolute transition-opacity duration-300 group-hover:opacity-0">
              C<span className="text-warning">.</span>
            </span>
            <ChevronRight
              className="absolute opacity-0 transition-opacity duration-300 group-hover:opacity-100 h-[24px] w-[24px] text-sidebar-primary"
              strokeWidth={2}
            />
          </div>
        ) : (
          <NavLink
            to="/dashboard"
            className="sidebar-brand-title block font-display leading-[0.9] text-sidebar-primary text-[28px] mt-3"
            title="CareerPilot"
          >
            <>
              Career
              <br />
              Pilot<span className="text-warning">.</span>
            </>
          </NavLink>
        )}

        {!isCollapsed && (
          <div className="sidebar-brand-sub mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/50 whitespace-nowrap">
            An AI Career Companion
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav
        className={`sidebar-nav flex-1 py-5 overflow-y-auto premium-scrollbar ${isCollapsed ? "px-3" : "px-3"}`}
      >
        {!isCollapsed && (
          <div className="sidebar-nav-title px-3 pb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40 whitespace-nowrap">
            Sections
          </div>
        )}
        <ul className="space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  title={isCollapsed && !isMobile ? item.label : undefined}
                  onClick={() => {
                    if (isMobile && onClose) onClose();
                  }}
                  className={({ isActive }) =>
                    `sidebar-link group flex items-center transition-colors rounded-md ${isCollapsed && !isMobile ? "justify-center p-3" : "gap-3 px-3 py-2.5 text-sm"} ${
                      isActive
                        ? "bg-sidebar-accent text-sidebar-primary"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-primary"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {!isCollapsed && (
                        <span
                          className={`font-mono text-[10px] tabular-nums ${isActive ? "text-warning" : "text-sidebar-foreground/40"}`}
                        >
                          {item.num}
                        </span>
                      )}
                      <Icon
                        className={`opacity-80 shrink-0 ${isCollapsed ? "h-5 w-5" : "h-4 w-4"}`}
                        strokeWidth={1.5}
                      />

                      {!isCollapsed || isMobile ? (
                        <>
                          <span className="flex-1 font-medium tracking-tight whitespace-nowrap overflow-hidden text-ellipsis">
                            {item.label}
                          </span>
                          {isActive && (
                            <span className="h-1.5 w-1.5 rounded-full bg-warning shrink-0" />
                          )}
                        </>
                      ) : null}
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>

        {/* Editorial callout */}
        {!isCollapsed && (
          <div className="sidebar-editorial mt-8 mx-3 border-t border-sidebar-border pt-5 transition-opacity duration-300">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-sidebar-foreground/40 whitespace-nowrap">
              Career Wisdom
            </div>
            <p className="mt-2 font-display text-base leading-snug text-sidebar-primary">
              "{selectedQuote.quote}"
            </p>
            <p className="mt-2 text-xs text-sidebar-foreground/50">
              — {selectedQuote.author}
            </p>
          </div>
        )}
      </nav>

      {/* User footer */}
      <div
        className={`sidebar-footer border-t border-sidebar-border transition-all duration-300 ${isCollapsed ? "p-3 flex flex-col items-center gap-4" : "p-4"}`}
      >
        <div
          className={`flex items-center w-full ${isCollapsed ? "flex-col gap-3 justify-center" : "gap-3"}`}
        >
          <div
            className={`grid shrink-0 place-items-center bg-sidebar-primary text-sidebar-primary-foreground font-display text-sm rounded-sm ${isCollapsed ? "h-10 w-10" : "h-10 w-10"}`}
          >
            {initials}
          </div>

          {!isCollapsed && (
            <div className="min-w-0 flex-1 leading-tight overflow-hidden">
              <div className="truncate text-sm font-semibold text-sidebar-primary">
                {user?.name ?? "User"}
              </div>
              <div className="truncate text-[11px] text-sidebar-foreground/50 font-mono uppercase tracking-wider">
                {user?.email ?? ""}
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            title={isCollapsed ? "Logout" : undefined}
            className={`text-sidebar-foreground/60 hover:text-sidebar-primary transition-colors shrink-0 ${isCollapsed ? "p-2 border border-sidebar-border rounded-full hover:bg-sidebar-accent" : "p-2"}`}
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </aside>
  );
}
