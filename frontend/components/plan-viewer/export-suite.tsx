"use client";

import React, { useState } from "react";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { saveAs } from "file-saver";
import { createEvents, EventAttributes } from "ics";
import { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell } from "docx";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileDown, FileText, Calendar, FileSpreadsheet } from "lucide-react";
import { ExperimentPlan } from "@/lib/types";
import { toast } from "sonner";

interface ExportSuiteProps {
  plan: ExperimentPlan;
  onExport?: (format: "pdf" | "csv" | "ical" | "docx") => void;
}

export function ExportSuite({ plan, onExport }: ExportSuiteProps) {
  const [isExporting, setIsExporting] = useState(false);

  const exportToPDF = async () => {
    setIsExporting(true);
    try {
      const doc = new jsPDF();
      let yPos = 20;

      // Title
      doc.setFontSize(20);
      doc.text("Experiment Plan", 20, yPos);
      yPos += 15;

      // Hypothesis
      doc.setFontSize(12);
      doc.text("Hypothesis:", 20, yPos);
      yPos += 7;
      doc.setFontSize(10);
      const hypothesisLines = doc.splitTextToSize(plan.hypothesis, 170);
      doc.text(hypothesisLines, 20, yPos);
      yPos += hypothesisLines.length * 5 + 10;

      // Domain
      doc.setFontSize(12);
      doc.text(`Domain: ${plan.domain}`, 20, yPos);
      yPos += 10;

      // Materials Table
      doc.setFontSize(14);
      doc.text("Materials", 20, yPos);
      yPos += 7;

      autoTable(doc, {
        startY: yPos,
        head: [["Item", "Catalog #", "Supplier", "Quantity", "Price"]],
        body: plan.materials.items.map((item) => [
          item.name,
          item.catalog_number,
          item.supplier,
          `${item.quantity} ${item.unit}`,
          `$${item.total_price.toFixed(2)}`,
        ]),
        theme: "grid",
        headStyles: { fillColor: [59, 130, 246] },
      });

      yPos = (doc as any).lastAutoTable.finalY + 10;

      // Protocol Steps
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      doc.setFontSize(14);
      doc.text("Protocol Steps", 20, yPos);
      yPos += 7;

      plan.protocol.steps.forEach((step, index) => {
        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }

        doc.setFontSize(11);
        doc.setFont("helvetica", "bold");
        doc.text(`Step ${step.step_number}: ${step.duration}`, 20, yPos);
        yPos += 6;

        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        const stepLines = doc.splitTextToSize(step.description, 170);
        doc.text(stepLines, 20, yPos);
        yPos += stepLines.length * 5 + 8;
      });

      // Timeline
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }

      doc.setFontSize(14);
      doc.text("Timeline", 20, yPos);
      yPos += 7;

      autoTable(doc, {
        startY: yPos,
        head: [["Phase", "Duration", "Start Date", "End Date"]],
        body: plan.timeline.phases.map((phase) => [
          phase.name,
          `${phase.duration_days} days`,
          phase.start_date,
          phase.end_date,
        ]),
        theme: "grid",
        headStyles: { fillColor: [59, 130, 246] },
      });

      // Save PDF
      doc.save(`experiment-plan-${Date.now()}.pdf`);
      onExport?.("pdf");
      toast.success("PDF exported successfully");
    } catch (error) {
      console.error("PDF export error:", error);
      toast.error("Failed to export PDF");
    } finally {
      setIsExporting(false);
    }
  };

  const exportToCSV = () => {
    setIsExporting(true);
    try {
      // Create CSV content
      let csv = "Experiment Plan Export\n\n";
      csv += `Hypothesis,${plan.hypothesis.replace(/,/g, ";")}\n`;
      csv += `Domain,${plan.domain}\n`;
      csv += `Total Budget,$${plan.materials.total_budget}\n\n`;

      // Materials
      csv += "Materials\n";
      csv += "Name,Catalog Number,Supplier,Quantity,Unit,Unit Price,Total Price\n";
      plan.materials.items.forEach((item) => {
        csv += `"${item.name}",${item.catalog_number},${item.supplier},${item.quantity},${item.unit},$${item.unit_price},$${item.total_price}\n`;
      });

      csv += "\nProtocol Steps\n";
      csv += "Step,Duration,Description\n";
      plan.protocol.steps.forEach((step) => {
        csv += `${step.step_number},${step.duration},"${step.description.replace(/"/g, '""')}"\n`;
      });

      csv += "\nTimeline\n";
      csv += "Phase,Duration (days),Start Date,End Date,Description\n";
      plan.timeline.phases.forEach((phase) => {
        csv += `"${phase.name}",${phase.duration_days},${phase.start_date},${phase.end_date},"${phase.description.replace(/"/g, '""')}"\n`;
      });

      // Save CSV
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      saveAs(blob, `experiment-plan-${Date.now()}.csv`);
      onExport?.("csv");
      toast.success("CSV exported successfully");
    } catch (error) {
      console.error("CSV export error:", error);
      toast.error("Failed to export CSV");
    } finally {
      setIsExporting(false);
    }
  };

  const exportToICal = () => {
    setIsExporting(true);
    try {
      const events: EventAttributes[] = plan.timeline.phases.map((phase) => ({
        start: phase.start_date.split("-").map(Number) as [number, number, number],
        end: phase.end_date.split("-").map(Number) as [number, number, number],
        title: phase.name,
        description: phase.description,
        status: "CONFIRMED",
        busyStatus: "BUSY",
        organizer: { name: "AI Scientist Platform", email: "noreply@aiscientist.com" },
      }));

      createEvents(events, (error, value) => {
        if (error) {
          console.error("iCal export error:", error);
          toast.error("Failed to export iCal");
          return;
        }

        const blob = new Blob([value], { type: "text/calendar;charset=utf-8" });
        saveAs(blob, `experiment-timeline-${Date.now()}.ics`);
        onExport?.("ical");
        toast.success("iCal exported successfully");
      });
    } catch (error) {
      console.error("iCal export error:", error);
      toast.error("Failed to export iCal");
    } finally {
      setIsExporting(false);
    }
  };

  const exportToDOCX = async () => {
    setIsExporting(true);
    try {
      const doc = new Document({
        sections: [
          {
            properties: {},
            children: [
              new Paragraph({
                text: "Experiment Plan",
                heading: HeadingLevel.HEADING_1,
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: "Hypothesis: ", bold: true }),
                  new TextRun(plan.hypothesis),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: "Domain: ", bold: true }),
                  new TextRun(plan.domain),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({ text: "Total Budget: ", bold: true }),
                  new TextRun(`$${plan.materials.total_budget}`),
                ],
              }),
              new Paragraph({ text: "" }),
              new Paragraph({
                text: "Materials",
                heading: HeadingLevel.HEADING_2,
              }),
              new Table({
                rows: [
                  new TableRow({
                    children: [
                      new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Name", bold: true })] })] }),
                      new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Catalog #", bold: true })] })] }),
                      new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Supplier", bold: true })] })] }),
                      new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Quantity", bold: true })] })] }),
                      new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: "Price", bold: true })] })] }),
                    ],
                  }),
                  ...plan.materials.items.map(
                    (item) =>
                      new TableRow({
                        children: [
                          new TableCell({ children: [new Paragraph(item.name)] }),
                          new TableCell({ children: [new Paragraph(item.catalog_number)] }),
                          new TableCell({ children: [new Paragraph(item.supplier)] }),
                          new TableCell({ children: [new Paragraph(`${item.quantity} ${item.unit}`)] }),
                          new TableCell({ children: [new Paragraph(`$${item.total_price.toFixed(2)}`)] }),
                        ],
                      })
                  ),
                ],
              }),
              new Paragraph({ text: "" }),
              new Paragraph({
                text: "Protocol Steps",
                heading: HeadingLevel.HEADING_2,
              }),
              ...plan.protocol.steps.flatMap((step) => [
                new Paragraph({
                  children: [
                    new TextRun({ text: `Step ${step.step_number}: `, bold: true }),
                    new TextRun(step.duration),
                  ],
                }),
                new Paragraph(step.description),
                new Paragraph({ text: "" }),
              ]),
            ],
          },
        ],
      });

      const blob = await Packer.toBlob(doc);
      saveAs(blob, `experiment-plan-${Date.now()}.docx`);
      onExport?.("docx");
      toast.success("DOCX exported successfully");
    } catch (error) {
      console.error("DOCX export error:", error);
      toast.error("Failed to export DOCX");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Export Plan</CardTitle>
        <CardDescription>Download your experiment plan in various formats</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button
            variant="outline"
            className="h-24 flex-col gap-2"
            onClick={exportToPDF}
            disabled={isExporting}
          >
            <FileText className="h-8 w-8" />
            <span>PDF</span>
          </Button>

          <Button
            variant="outline"
            className="h-24 flex-col gap-2"
            onClick={exportToCSV}
            disabled={isExporting}
          >
            <FileSpreadsheet className="h-8 w-8" />
            <span>CSV</span>
          </Button>

          <Button
            variant="outline"
            className="h-24 flex-col gap-2"
            onClick={exportToICal}
            disabled={isExporting}
          >
            <Calendar className="h-8 w-8" />
            <span>iCal</span>
          </Button>

          <Button
            variant="outline"
            className="h-24 flex-col gap-2"
            onClick={exportToDOCX}
            disabled={isExporting}
          >
            <FileDown className="h-8 w-8" />
            <span>DOCX</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
