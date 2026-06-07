import { useState } from "react";
import { Outlet } from "react-router-dom";
import { AppSidebar } from "../components/AppSidebar";
import { Menu } from "lucide-react";

export default function AppLayout() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen w-full bg-background">
      {/* Desktop Sidebar */}
      <AppSidebar />

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 transition-opacity"
            onClick={() => setIsMobileOpen(false)}
          />
          {/* Sidebar Drawer */}
          <div className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[calc(100%-3rem)] bg-sidebar">
            <AppSidebar isMobile onClose={() => setIsMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col h-screen">
        {/* Mobile Header */}
        <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-background px-4 lg:hidden">
          <button
            onClick={() => setIsMobileOpen(true)}
            className="inline-flex items-center justify-center rounded-md p-2 text-foreground/60 hover:bg-muted hover:text-foreground"
            aria-label="Open Sidebar"
          >
            <Menu className="h-6 w-6" strokeWidth={1.5} />
          </button>
          <div className="font-display text-lg tracking-tight font-semibold">
            CareerPilot<span className="text-warning">.</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
