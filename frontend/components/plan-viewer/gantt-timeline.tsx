"use client";

import React, { useEffect, useRef, useState } from "react";
import Gantt from "frappe-gantt";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Timeline, Phase } from "@/lib/types";

interface GanttTimelineProps {
  timeline: Timeline;
  onTaskClick?: (phaseNumber: number) => void;
  onReschedule?: (phaseNumber: number, newStartDate: string) => void;
}

export function GanttTimeline({ timeline, onTaskClick, onReschedule }: GanttTimelineProps) {
  const ganttRef = useRef<SVGSVGElement>(null);
  const ganttInstance = useRef<any>(null);
  const [viewMode, setViewMode] = useState<"Day" | "Week" | "Month">("Week");

  // Compute real ISO dates from duration_days since AI often returns "Week 1" etc.
  const phasesWithDates = React.useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    let cursor = new Date(today);

    return timeline.phases.map((phase) => {
      const durationDays = phase.duration_days && phase.duration_days > 0 ? phase.duration_days : 7;
      const startDate = new Date(cursor);
      const endDate = new Date(cursor);
      endDate.setDate(endDate.getDate() + durationDays - 1);

      // Advance cursor for next phase
      cursor = new Date(endDate);
      cursor.setDate(cursor.getDate() + 1);

      const fmt = (d: Date) => d.toISOString().split("T")[0];

      // Normalize dependencies to numeric phase numbers
      const deps: number[] = (phase.dependencies || [])
        .map((d: any) => {
          if (typeof d === "number") return d;
          const m = String(d).match(/\d+/);
          return m ? parseInt(m[0]) : null;
        })
        .filter((d: any) => d !== null && d !== phase.phase_number);

      return { ...phase, start_date: fmt(startDate), end_date: fmt(endDate), duration_days: durationDays, _deps: deps };
    });
  }, [timeline.phases]);

  useEffect(() => {
    if (!ganttRef.current || phasesWithDates.length === 0) return;

    // Convert timeline phases to Frappe Gantt format
    const tasks = phasesWithDates.map((phase) => ({
      id: `phase-${phase.phase_number}`,
      name: phase.name,
      start: phase.start_date,
      end: phase.end_date,
      progress: 0,
      dependencies: phase._deps.map((dep: number) => `phase-${dep}`).join(", "),
    }));

    try {
      ganttInstance.current = new Gantt(ganttRef.current, tasks, {
        view_mode: viewMode,
        date_format: "YYYY-MM-DD",
        custom_popup_html: (task: any) => {
          const phase = phasesWithDates.find((p) => `phase-${p.phase_number}` === task.id);
          if (!phase) return "";
          return `
            <div style="padding:12px;min-width:200px">
              <strong>${phase.name}</strong>
              <p style="margin:4px 0;font-size:13px">Duration: ${phase.duration_days} days</p>
              <p style="margin:4px 0;font-size:13px">${phase.start_date} → ${phase.end_date}</p>
              <p style="margin:6px 0 0;font-size:12px;color:#64748b">${phase.description}</p>
            </div>
          `;
        },
        on_click: (task: any) => {
          const phaseNumber = parseInt(task.id.replace("phase-", ""));
          if (onTaskClick) onTaskClick(phaseNumber);
        },
        on_date_change: (task: any, start: Date) => {
          const phaseNumber = parseInt(task.id.replace("phase-", ""));
          if (onReschedule) onReschedule(phaseNumber, start.toISOString().split("T")[0]);
        },
      });
    } catch (e) {
      console.error("Gantt init error:", e);
    }

    return () => { ganttInstance.current = null; };
  }, [phasesWithDates, viewMode, onTaskClick, onReschedule]);

  const handleViewModeChange = (mode: "Day" | "Week" | "Month") => {
    setViewMode(mode);
    if (ganttInstance.current) {
      ganttInstance.current.change_view_mode(mode);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Project Timeline</CardTitle>
            <CardDescription>
              Gantt chart showing experiment phases and dependencies
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant={viewMode === "Day" ? "default" : "outline"}
              size="sm"
              onClick={() => handleViewModeChange("Day")}
            >
              Day
            </Button>
            <Button
              variant={viewMode === "Week" ? "default" : "outline"}
              size="sm"
              onClick={() => handleViewModeChange("Week")}
            >
              Week
            </Button>
            <Button
              variant={viewMode === "Month" ? "default" : "outline"}
              size="sm"
              onClick={() => handleViewModeChange("Month")}
            >
              Month
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="gantt-container">
          <svg ref={ganttRef} className="w-full" style={{ minHeight: "400px" }}></svg>
        </div>

        {/* Phase Details */}
        <div className="mt-6 space-y-3">
          <h4 className="font-semibold text-sm">Phase Details:</h4>
          {phasesWithDates.map((phase) => (
            <div
              key={phase.phase_number}
              className="flex items-start gap-3 p-3 bg-muted rounded-lg hover:bg-muted/80 cursor-pointer transition-colors"
              onClick={() => onTaskClick && onTaskClick(phase.phase_number)}
            >
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                {phase.phase_number}
              </div>
              <div className="flex-1 min-w-0">
                <h5 className="font-medium text-sm">{phase.name}</h5>
                <p className="text-xs text-muted-foreground mt-1">{phase.description}</p>
                <div className="flex flex-wrap gap-4 mt-2 text-xs text-muted-foreground">
                  <span>Duration: {phase.duration_days} days</span>
                  <span>{phase.start_date} → {phase.end_date}</span>
                  {phase._deps.length > 0 && (
                    <span>Depends on: Phase {phase._deps.join(", ")}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 p-4 bg-primary/10 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="font-medium">Total Project Duration:</span>
            <span className="text-2xl font-bold text-primary">
              {timeline.total_duration_days} days
            </span>
          </div>
        </div>

        <style jsx global>{`
          .gantt-container {
            overflow-x: auto;
          }
          .gantt .bar {
            fill: hsl(var(--primary));
          }
          .gantt .bar-progress {
            fill: hsl(var(--primary) / 0.6);
          }
          .gantt .bar-label {
            fill: hsl(var(--primary-foreground));
            font-size: 12px;
          }
          .gantt-popup {
            padding: 12px;
            background: hsl(var(--popover));
            border: 1px solid hsl(var(--border));
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          }
          .gantt-popup h3 {
            font-weight: 600;
            margin-bottom: 8px;
          }
          .gantt-popup p {
            margin: 4px 0;
            font-size: 14px;
          }
        `}</style>
      </CardContent>
    </Card>
  );
}
