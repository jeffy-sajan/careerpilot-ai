import { useState } from "react";
import {
  DndContext,
  useDraggable,
  useDroppable,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  pointerWithin,
} from "@dnd-kit/core";
import { format } from "date-fns";
import { Plus, MoreHorizontal } from "lucide-react";
import { Pill } from "../../../components/ui-kit";
import { JobApplication } from "../../../lib/api/applications";

type ColumnConfig = {
  id: string;
  label: string;
  accent: string;
  pillTone: "neutral" | "primary" | "success" | "warning" | "destructive";
};

const COLUMNS: ColumnConfig[] = [
  {
    id: "SAVED",
    label: "Saved",
    accent: "oklch(0.7 0.04 260)",
    pillTone: "neutral",
  },
  {
    id: "APPLIED",
    label: "Applied",
    accent: "oklch(0.55 0.2 269)",
    pillTone: "primary",
  },
  {
    id: "ASSESSMENT",
    label: "Assessment",
    accent: "oklch(0.7 0.14 70)",
    pillTone: "warning",
  },
  {
    id: "INTERVIEW",
    label: "Interview",
    accent: "oklch(0.62 0.19 295)",
    pillTone: "primary",
  },
  {
    id: "OFFER",
    label: "Offer",
    accent: "oklch(0.62 0.16 152)",
    pillTone: "success",
  },
  {
    id: "REJECTED",
    label: "Rejected",
    accent: "oklch(0.6 0.22 27)",
    pillTone: "destructive",
  },
  {
    id: "WITHDRAWN",
    label: "Withdrawn",
    accent: "oklch(0.62 0.01 270)",
    pillTone: "neutral",
  },
];

// ── Card (draggable) ──────────────────────────────────────────────────────────

function KanbanCard({
  app,
  onClick,
  isOverlay = false,
}: {
  app: JobApplication;
  onClick?: () => void;
  isOverlay?: boolean;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: app.id,
    data: { app },
  });

  const initial = app.company_name.slice(0, 1).toUpperCase();

  const inner = (
    <div
      className={`block w-full rounded-lg border border-border bg-card p-3.5 text-left shadow-card transition-all
        ${
          isOverlay
            ? "rotate-2 scale-105 border-primary/50 shadow-elevated cursor-grabbing"
            : "cursor-grab hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-elevated"
        }
        ${isDragging ? "opacity-30" : "opacity-100"}
      `}
    >
      {/* Top row: avatar + company + menu */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-to-br from-primary/10 to-secondary text-[11px] font-bold text-primary">
            {initial}
          </div>
          <div className="text-xs font-medium text-muted-foreground truncate max-w-[110px]">
            {app.company_name}
          </div>
        </div>
        <MoreHorizontal className="h-4 w-4 shrink-0 text-muted-foreground/50" />
      </div>

      {/* Role */}
      <div className="mt-2 text-sm font-semibold leading-snug text-foreground">
        {app.job_title}
      </div>

      {/* Footer: source · date + priority pill */}
      <div className="mt-3 flex items-center justify-between gap-1">
        <span className="text-[11px] text-muted-foreground truncate">
          {app.source ? `${app.source} · ` : ""}
          {format(new Date(app.application_date), "MMM d")}
        </span>
        <Pill
          tone={
            app.priority === "HIGH"
              ? "destructive"
              : app.priority === "MEDIUM"
                ? "warning"
                : "neutral"
          }
        >
          {app.priority}
        </Pill>
      </div>
    </div>
  );

  if (isOverlay) return inner;

  return (
    <button
      ref={setNodeRef}
      onClick={onClick}
      {...listeners}
      {...attributes}
      className="block w-full text-left"
    >
      {inner}
    </button>
  );
}

// ── Column (droppable) ────────────────────────────────────────────────────────

function KanbanColumn({
  col,
  applications,
  onCardClick,
  onAddClick,
}: {
  col: ColumnConfig;
  applications: JobApplication[];
  onCardClick: (app: JobApplication) => void;
  onAddClick: () => void;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: col.id });

  return (
    <div
      className={`flex flex-col rounded-xl border border-border bg-surface-muted transition-colors duration-150 ${
        isOver ? "border-primary/40 bg-primary/5" : ""
      }`}
    >
      {/* Column header */}
      <div className="flex items-center justify-between border-b border-border px-3.5 py-3">
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full shrink-0"
            style={{ background: col.accent }}
          />
          <span className="text-sm font-semibold text-foreground">
            {col.label}
          </span>
          <span className="text-xs font-medium text-muted-foreground">
            {applications.length}
          </span>
        </div>
        <button
          onClick={onAddClick}
          className="rounded p-1 text-muted-foreground hover:bg-background hover:text-foreground transition-colors"
          title={`Add to ${col.label}`}
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      {/* Cards */}
      <div ref={setNodeRef} className="flex-1 space-y-2.5 p-2.5 min-h-[80px]">
        {applications.map((app) => (
          <KanbanCard key={app.id} app={app} onClick={() => onCardClick(app)} />
        ))}
        {applications.length === 0 && (
          <div
            className={`grid place-items-center rounded-lg border border-dashed border-border p-6 text-xs text-muted-foreground transition-colors ${
              isOver ? "border-primary/40 bg-primary/5" : ""
            }`}
          >
            Drop here
          </div>
        )}
      </div>
    </div>
  );
}

// ── Board ─────────────────────────────────────────────────────────────────────

export function ApplicationKanbanBoard({
  applications,
  onStatusChange,
  onCardClick,
  onAddNew,
}: {
  applications: JobApplication[];
  onStatusChange: (appId: string, newStatus: string) => void;
  onCardClick: (app: JobApplication) => void;
  onAddNew: () => void;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const activeApp = activeId
    ? applications.find((a) => a.id === activeId)
    : null;

  const handleDragStart = (e: DragStartEvent) => {
    setActiveId(e.active.id as string);
  };

  const handleDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = e;
    if (!over) return;

    const dragged = applications.find((a) => a.id === active.id);
    const newStatus = over.id as string;

    if (dragged && dragged.status !== newStatus) {
      onStatusChange(dragged.id, newStatus);
    }
  };

  return (
    <DndContext
      collisionDetection={pointerWithin}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
        {COLUMNS.map((col) => (
          <KanbanColumn
            key={col.id}
            col={col}
            applications={applications.filter((a) => a.status === col.id)}
            onCardClick={onCardClick}
            onAddClick={onAddNew}
          />
        ))}
      </div>

      <DragOverlay
        dropAnimation={{
          duration: 180,
          easing: "cubic-bezier(0.18, 0.67, 0.6, 1.22)",
        }}
      >
        {activeApp ? <KanbanCard app={activeApp} isOverlay /> : null}
      </DragOverlay>
    </DndContext>
  );
}
