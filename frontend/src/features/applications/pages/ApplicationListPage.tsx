import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  DndContext,
  useDraggable,
  useDroppable,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  pointerWithin,
  useSensors,
  useSensor,
  PointerSensor,
  KeyboardSensor,
} from "@dnd-kit/core";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  List as ListIcon,
  Kanban as KanbanIcon,
  ExternalLink,
  Edit2,
  Trash2,
} from "lucide-react";
import { format } from "date-fns";
import { Topbar, Pill, Button } from "../../../components/ui-kit";
import { applicationsApi, JobApplication } from "../../../lib/api/applications";
import { ApplicationFormModal } from "../components/ApplicationFormModal";

const COLUMNS: {
  key: string;
  label: string;
  tone:
    | "neutral"
    | "primary"
    | "purple"
    | "success"
    | "destructive"
    | "warning";
  accent: string;
}[] = [
  {
    key: "SAVED",
    label: "Saved",
    tone: "neutral",
    accent: "oklch(0.7 0.04 260)",
  },
  {
    key: "APPLIED",
    label: "Applied",
    tone: "primary",
    accent: "oklch(0.55 0.2 269)",
  },
  {
    key: "ASSESSMENT",
    label: "Assessment",
    tone: "warning",
    accent: "oklch(0.7 0.14 70)",
  },
  {
    key: "INTERVIEW",
    label: "Interview",
    tone: "purple",
    accent: "oklch(0.62 0.19 295)",
  },
  {
    key: "OFFER",
    label: "Offer",
    tone: "success",
    accent: "oklch(0.62 0.16 152)",
  },
  {
    key: "REJECTED",
    label: "Rejected",
    tone: "destructive",
    accent: "oklch(0.6 0.22 27)",
  },
  {
    key: "WITHDRAWN",
    label: "Withdrawn",
    tone: "neutral",
    accent: "oklch(0.62 0.01 270)",
  },
];

function JobCardMenu({
  onEdit,
  onDelete,
}: {
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative" onMouseLeave={() => setIsOpen(false)}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          e.preventDefault();
          setIsOpen(!isOpen);
        }}
        onPointerDown={(e) => e.stopPropagation()} // Prevent drag start
        className="p-1 rounded hover:bg-muted text-muted-foreground/50 hover:text-foreground transition-colors"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-32 rounded-md border border-border bg-popover p-1 shadow-elevated z-50">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setIsOpen(false);
              onEdit();
            }}
            onPointerDown={(e) => e.stopPropagation()} // Prevent drag start
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-foreground hover:bg-muted transition-colors text-left"
          >
            <Edit2 className="h-3.5 w-3.5" /> Edit
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              setIsOpen(false);
              onDelete();
            }}
            onPointerDown={(e) => e.stopPropagation()} // Prevent drag start
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-destructive hover:bg-destructive/10 transition-colors text-left"
          >
            <Trash2 className="h-3.5 w-3.5" /> Delete
          </button>
        </div>
      )}
    </div>
  );
}

function JobCard({
  app,
  onClick,
  onEdit,
  onDelete,
  isOverlay = false,
}: {
  app: JobApplication;
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
  isOverlay?: boolean;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: app.id,
    data: { app },
  });

  const cardClass = `block w-full rounded-lg border border-border bg-card p-3.5 text-left shadow-card transition
    ${
      isOverlay
        ? "rotate-2 scale-105 border-primary/40 shadow-elevated cursor-grabbing"
        : "cursor-grab hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-elevated"
    }
    ${isDragging && !isOverlay ? "opacity-30" : ""}
  `;

  const inner = (
    <div className={cardClass}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-primary-soft to-secondary text-[11px] font-bold text-primary">
            {app.company_name.slice(0, 1).toUpperCase()}
          </div>
          <div className="text-xs font-medium text-muted-foreground truncate max-w-[100px]">
            {app.company_name}
          </div>
        </div>
        {!isOverlay && onEdit && onDelete && (
          <JobCardMenu onEdit={onEdit} onDelete={onDelete} />
        )}
      </div>

      <div className="mt-2 text-sm font-semibold leading-snug text-foreground">
        {app.job_title}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground truncate">
          {[app.source, format(new Date(app.application_date), "MMM d")]
            .filter(Boolean)
            .join(" · ")}
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
    <div
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className="block w-full"
    >
      {inner}
    </div>
  );
}

function KanbanColumn({
  col,
  items,
  onCardClick,
  onAddClick,
  onEditClick,
  onDeleteClick,
}: {
  col: (typeof COLUMNS)[number];
  items: JobApplication[];
  onCardClick: (app: JobApplication) => void;
  onAddClick: (status: string) => void;
  onEditClick: (app: JobApplication) => void;
  onDeleteClick: (appId: string) => void;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: col.key });

  return (
    <div
      className={`flex h-full flex-col rounded-xl border border-border bg-surface-muted transition-colors duration-150
        ${isOver ? "border-primary/40 ring-2 ring-primary/10" : ""}
      `}
    >
      <div className="flex items-center justify-between border-b border-border px-3.5 py-3">
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: col.accent }}
          />
          <span className="text-sm font-semibold text-foreground">
            {col.label}
          </span>
          <span className="text-xs font-medium text-muted-foreground">
            {items.length}
          </span>
        </div>
        <button
          onClick={() => onAddClick(col.key)}
          className="rounded p-1 text-muted-foreground hover:bg-background hover:text-foreground transition-colors"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <div ref={setNodeRef} className="flex-1 space-y-2.5 p-2.5 min-h-[80px]">
        {items.map((app) => (
          <JobCard
            key={app.id}
            app={app}
            onClick={() => onCardClick(app)}
            onEdit={() => onEditClick(app)}
            onDelete={() => onDeleteClick(app.id)}
          />
        ))}
        {items.length === 0 && (
          <div
            className={`grid place-items-center rounded-lg border border-dashed border-border p-6 text-xs text-muted-foreground transition-colors
              ${isOver ? "border-primary/40 bg-primary/5" : ""}
            `}
          >
            No items
          </div>
        )}
      </div>
    </div>
  );
}

const EMPTY_APPS: JobApplication[] = [];

export default function ApplicationListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState<JobApplication | null | "new">(null);
  const [defaultStatus, setDefaultStatus] = useState("SAVED");
  const [search, setSearch] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "kanban">("kanban");

  const { data, isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => applicationsApi.delete(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      applicationsApi.update(id, { status }),
    onMutate: async ({ id, status }) => {
      await queryClient.cancelQueries({ queryKey: ["applications"] });
      const prev = queryClient.getQueryData<{ applications: JobApplication[] }>(
        ["applications"],
      );
      queryClient.setQueryData<{ applications: JobApplication[] }>(
        ["applications"],
        (old) => ({
          applications: (old?.applications || []).map((a) =>
            a.id === id ? { ...a, status } : a,
          ),
        }),
      );
      return { prev };
    },
    onError: (_e, _v, ctx) =>
      queryClient.setQueryData(["applications"], ctx?.prev),
    onSettled: () =>
      queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const allApps = data?.applications || EMPTY_APPS;

  const filtered = useMemo(() => {
    if (!search.trim()) return allApps;
    const q = search.toLowerCase();
    return allApps.filter(
      (a) =>
        a.company_name.toLowerCase().includes(q) ||
        a.job_title.toLowerCase().includes(q) ||
        (a.source || "").toLowerCase().includes(q),
    );
  }, [allApps, search]);

  const stats = useMemo(
    () => ({
      total: allApps.length,
      interviews: allApps.filter((a) =>
        ["INTERVIEW", "OFFER"].includes(a.status),
      ).length,
      offers: allApps.filter((a) => a.status === "OFFER").length,
    }),
    [allApps],
  );

  const activeApp = activeId ? allApps.find((a) => a.id === activeId) : null;

  // Fix click vs drag events by adding an activation constraint
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, // Must move 5 pixels to be considered a drag
      },
    }),
    useSensor(KeyboardSensor),
  );

  const handleDragStart = (e: DragStartEvent) =>
    setActiveId(e.active.id as string);

  const handleDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = e;
    if (!over) return;
    const dragged = allApps.find((a) => a.id === active.id);
    const newStatus = over.id as string;
    if (dragged && dragged.status !== newStatus) {
      updateStatusMutation.mutate({ id: dragged.id, status: newStatus });
    }
  };

  const openNew = (status = "SAVED") => {
    setDefaultStatus(status);
    setOpen("new");
  };

  const handleDelete = (id: string) => {
    if (window.confirm("Are you sure you want to delete this application?")) {
      deleteMutation.mutate(id);
    }
  };

  const subtitle =
    stats.total > 0
      ? `${stats.total} applications · ${stats.interviews} interviews · ${stats.offers} offers`
      : "Track your entire job search pipeline";

  return (
    <>
      <Topbar
        title="Job Tracker"
        subtitle={subtitle}
        actions={
          <div className="flex items-center gap-3">
            {/* View toggle */}
            <div className="flex bg-surface-muted p-1 rounded-md border border-ink/10">
              <button
                onClick={() => setViewMode("list")}
                className={`p-1.5 rounded-sm transition-colors ${viewMode === "list" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                title="List View"
              >
                <ListIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode("kanban")}
                className={`p-1.5 rounded-sm transition-colors ${viewMode === "kanban" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
                title="Kanban View"
              >
                <KanbanIcon className="h-4 w-4" />
              </button>
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4" /> Filter
            </Button>
            <Button variant="primary" onClick={() => openNew()}>
              <Plus className="h-4 w-4" /> Add application
            </Button>
          </div>
        }
      />

      <div className="space-y-4 p-6 lg:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-full max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-surface pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/40"
              placeholder="Search company, role…"
            />
          </div>
          <Pill tone="primary">All sources</Pill>
          <Pill tone="neutral">Last 30 days</Pill>
          <Pill tone="neutral">Remote</Pill>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-5 animate-pulse">
            {COLUMNS.slice(0, 5).map((c) => (
              <div
                key={c.key}
                className="h-48 rounded-xl bg-surface-muted border border-border"
              />
            ))}
          </div>
        ) : allApps.length === 0 ? (
          <div className="grid place-items-center rounded-xl border border-dashed border-border py-20">
            <div className="text-center space-y-3">
              <p className="text-sm font-medium text-foreground">
                No applications yet
              </p>
              <p className="text-xs text-muted-foreground max-w-xs">
                Start tracking your job search by adding your first application.
              </p>
              <Button variant="primary" onClick={() => openNew()}>
                <Plus className="h-4 w-4" /> Add application
              </Button>
            </div>
          </div>
        ) : viewMode === "kanban" ? (
          <DndContext
            sensors={sensors}
            collisionDetection={pointerWithin}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-5 2xl:grid-cols-7">
              {COLUMNS.map((col) => (
                <KanbanColumn
                  key={col.key}
                  col={col}
                  items={filtered.filter((a) => a.status === col.key)}
                  onCardClick={(app) => setOpen(app)}
                  onAddClick={openNew}
                  onEditClick={(app) => setOpen(app)}
                  onDeleteClick={handleDelete}
                />
              ))}
            </div>

            <DragOverlay
              dropAnimation={{
                duration: 180,
                easing: "cubic-bezier(0.18, 0.67, 0.6, 1.22)",
              }}
            >
              {activeApp ? <JobCard app={activeApp} isOverlay /> : null}
            </DragOverlay>
          </DndContext>
        ) : (
          /* ── List View ── */
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-foreground">
                <thead className="border-b border-border bg-surface-muted text-xs uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">
                      Company & Role
                    </th>
                    <th className="px-5 py-3.5 font-semibold">Status</th>
                    <th className="px-5 py-3.5 font-semibold">Priority</th>
                    <th className="px-5 py-3.5 font-semibold">Applied</th>
                    <th className="px-5 py-3.5 font-semibold text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filtered.map((app) => {
                    const colConfig = COLUMNS.find((c) => c.key === app.status);
                    return (
                      <tr
                        key={app.id}
                        className="hover:bg-surface-muted/40 group transition-colors cursor-pointer"
                        onClick={() => setOpen(app)}
                      >
                        <td className="px-5 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-gradient-to-br from-primary/10 to-secondary text-[11px] font-bold text-primary">
                              {app.company_name.slice(0, 1).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-foreground">
                                {app.job_title}
                              </div>
                              <div className="text-xs text-muted-foreground flex items-center gap-1">
                                {app.company_name}
                                {app.job_url && (
                                  <a
                                    href={app.job_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="text-primary hover:underline"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">
                          <Pill tone={colConfig?.tone || "neutral"}>
                            {app.status}
                          </Pill>
                        </td>
                        <td className="px-5 py-3.5">
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
                        </td>
                        <td className="px-5 py-3.5 text-muted-foreground text-xs">
                          {format(
                            new Date(app.application_date),
                            "MMM d, yyyy",
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/job-tracker/${app.id}`);
                              }}
                              className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                              title="View Timeline"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpen(app);
                              }}
                              className="p-1.5 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                              title="Edit"
                            >
                              <Edit2 className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(app.id);
                              }}
                              className="p-1.5 rounded text-muted-foreground hover:text-destructive hover:bg-muted transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {open !== null && (
        <ApplicationFormModal
          isOpen={true}
          application={open === "new" ? null : open}
          defaultStatus={defaultStatus}
          onClose={() => setOpen(null)}
        />
      )}
    </>
  );
}
