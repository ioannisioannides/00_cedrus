"use client"

import { CheckCircle2, Circle } from "lucide-react"

enum AuditStatus {
  DRAFT = "DRAFT",
  SCHEDULED = "SCHEDULED",
  IN_PROGRESS = "IN_PROGRESS",
  REPORT_DRAFT = "REPORT_DRAFT",
  CLIENT_REVIEW = "CLIENT_REVIEW",
  SUBMITTED = "SUBMITTED",
  TECHNICAL_REVIEW = "TECHNICAL_REVIEW",
  DECISION_PENDING = "DECISION_PENDING",
  DECIDED = "DECIDED",
  CLOSED = "CLOSED",
}

const TIMELINE_STEPS = [
  { status: AuditStatus.DRAFT, label: "Planning/Draft", description: "Audit is prepared" },
  { status: AuditStatus.SCHEDULED, label: "Scheduled", description: "Auditors assigned" },
  { status: AuditStatus.IN_PROGRESS, label: "Conducting", description: "On-site assessment" },
  { status: AuditStatus.REPORT_DRAFT, label: "Report Draft", description: "Compiling results" },
  { status: AuditStatus.CLIENT_REVIEW, label: "Client Review", description: "NC responses & signoff" },
  { status: AuditStatus.SUBMITTED, label: "Submitted", description: "Ready for QA" },
  { status: AuditStatus.TECHNICAL_REVIEW, label: "Technical Review", description: "Verification (ISO 17021)" },
  { status: AuditStatus.DECISION_PENDING, label: "Decision", description: "Panel evaluation" },
  { status: AuditStatus.DECIDED, label: "Decided", description: "Outcome completed" },
  { status: AuditStatus.CLOSED, label: "Closed", description: "Audit records sealed" },
]

interface AuditProgressionMapProps {
  currentStatus: keyof typeof AuditStatus | string
}

export function AuditProgressionMap({ currentStatus }: AuditProgressionMapProps) {
  const currentIdx = TIMELINE_STEPS.findIndex((step) => step.status === currentStatus)

  return (
    <div className="w-full bg-card border rounded-lg p-5">
      <div className="mb-4">
        <h3 className="font-semibold text-sm">Audit Lifecycle (ISO 17021 Compliance)</h3>
        <p className="text-xs text-muted-foreground">Trace real-time operational progression from planning to certification closure.</p>
      </div>

      {/* Horizontal workflow bar in medium / large viewports */}
      <div className="hidden lg:grid grid-cols-10 gap-2 relative">
        <div className="absolute top-[18px] left-[5%] right-[5%] h-0.5 bg-muted z-0">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${currentIdx >= 0 ? (currentIdx / 9) * 100 : 0}%` }}
          />
        </div>

        {TIMELINE_STEPS.map((step, idx) => {
          const isCompleted = idx < currentIdx
          const isActive = idx === currentIdx

          return (
            <div key={step.status} className="flex flex-col items-center text-center z-10">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-colors ${
                  isCompleted
                    ? "bg-primary border-primary text-primary-foreground"
                    : isActive
                    ? "bg-card border-primary text-primary shadow"
                    : "bg-muted/50 border-muted text-muted-foreground"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : isActive ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
                ) : (
                  <Circle className="w-4 h-4 text-muted-foreground" />
                )}
              </div>
              <span className={`text-[11px] font-medium mt-2 line-clamp-1 ${isActive ? "text-primary font-bold" : "text-muted-foreground"}`}>
                {step.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Vertical timeline for smaller viewports */}
      <div className="lg:hidden space-y-4">
        {TIMELINE_STEPS.map((step, idx) => {
          const isCompleted = idx < currentIdx
          const isActive = idx === currentIdx
          const isFuture = idx > currentIdx

          if (isFuture && idx !== currentIdx + 1) return null // Only show completed, current, and the next immediate step for brevity

          return (
            <div key={step.status} className="flex items-start gap-3">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center border-2 mt-0.5 transition-colors ${
                  isCompleted
                    ? "bg-primary border-primary text-primary-foreground"
                    : isActive
                    ? "bg-card border-primary text-primary"
                    : "bg-muted/50 border-muted text-muted-foreground"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : isActive ? (
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                ) : (
                  <Circle className="w-3 h-3" />
                )}
              </div>
              <div>
                <p className={`text-xs font-semibold ${isActive ? "text-primary" : "text-foreground"}`}>
                  {step.label} {isActive && <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.2 rounded ml-1">Current</span>}
                </p>
                <p className="text-[11px] text-muted-foreground">{step.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
