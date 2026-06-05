import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Edit2,
  Calendar,
  Link as LinkIcon,
  Building2,
  AlignLeft,
  Clock,
} from "lucide-react";
import { format } from "date-fns";

import {
  Topbar,
  Button,
  Card,
  CardHeader,
  Pill,
} from "../../../components/ui-kit";
import { applicationsApi } from "../../../lib/api/applications";
import { ApplicationFormModal } from "../components/ApplicationFormModal";

const STATUS_COLORS: Record<
  string,
  "neutral" | "primary" | "success" | "warning" | "destructive"
> = {
  SAVED: "neutral",
  APPLIED: "primary",
  ASSESSMENT: "warning",
  INTERVIEW: "primary",
  OFFER: "success",
  REJECTED: "destructive",
  WITHDRAWN: "neutral",
};

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: application, isLoading } = useQuery({
    queryKey: ["applications", id],
    queryFn: () => applicationsApi.get(id as string),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading details...
      </div>
    );
  }

  if (!application) {
    return (
      <div className="p-8 text-center text-destructive">
        Application not found.
      </div>
    );
  }

  return (
    <>
      <Topbar
        title={application.job_title}
        subtitle={application.company_name}
        actions={
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate("/applications")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Button variant="primary" onClick={() => setIsModalOpen(true)}>
              <Edit2 className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>
        }
      />

      <div className="p-6 lg:p-8 max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader title="Application Details" eyebrow="Overview" />
            <div className="p-5 grid grid-cols-2 gap-y-6 gap-x-4">
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Building2 className="h-3 w-3" /> Company
                </div>
                <div className="text-sm font-medium">
                  {application.company_name}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Calendar className="h-3 w-3" /> Applied On
                </div>
                <div className="text-sm font-medium">
                  {format(
                    new Date(application.application_date),
                    "MMMM d, yyyy",
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                  Status
                </div>
                <Pill tone={STATUS_COLORS[application.status] || "neutral"}>
                  {application.status}
                </Pill>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                  Priority
                </div>
                <div
                  className={`text-sm font-bold ${
                    application.priority === "HIGH"
                      ? "text-destructive"
                      : application.priority === "MEDIUM"
                        ? "text-warning-foreground"
                        : "text-muted-foreground"
                  }`}
                >
                  {application.priority}
                </div>
              </div>
              {application.job_url && (
                <div className="col-span-2">
                  <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
                    <LinkIcon className="h-3 w-3" /> Job URL
                  </div>
                  <a
                    href={application.job_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-primary hover:underline break-all"
                  >
                    {application.job_url}
                  </a>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Notes" eyebrow="Information" />
            <div className="p-5">
              {application.notes ? (
                <div className="whitespace-pre-wrap text-sm text-foreground/80 leading-relaxed">
                  {application.notes}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground italic flex items-center gap-2">
                  <AlignLeft className="h-4 w-4" /> No notes added yet.
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Timeline" eyebrow="Status History" />
            <div className="p-5">
              {application.status_history.length === 0 ? (
                <div className="text-sm text-muted-foreground">
                  No history available.
                </div>
              ) : (
                <div className="space-y-4">
                  {application.status_history.map((history) => (
                    <div
                      key={history.id}
                      className="relative pl-6 pb-4 border-l-2 border-ink/15 last:border-0 last:pb-0"
                    >
                      <div className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-primary ring-4 ring-background" />
                      <div className="text-xs text-muted-foreground flex items-center gap-1 mb-1">
                        <Clock className="h-3 w-3" />
                        {format(new Date(history.changed_at), "MMM d, h:mm a")}
                      </div>
                      <div className="text-sm">
                        {history.old_status ? (
                          <>
                            Changed from{" "}
                            <span className="line-through text-muted-foreground">
                              {history.old_status}
                            </span>{" "}
                            to{" "}
                            <span className="font-semibold">
                              {history.new_status}
                            </span>
                          </>
                        ) : (
                          <>
                            Created as{" "}
                            <span className="font-semibold">
                              {history.new_status}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      <ApplicationFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        application={application}
      />
    </>
  );
}
