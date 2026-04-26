"use client";

import React, { useState } from "react";
import { jsPDF } from "jspdf";
import { createBrowserClient } from "@supabase/ssr";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, Download, Loader2, FileText } from "lucide-react";
import { NotebookTemplate } from "@/lib/types";
import { toast } from "sonner";
import { getApiUrl, API_ENDPOINTS } from "@/lib/config";

interface NotebookExportProps {
  planId: string;
  onGenerate?: () => void;
  onExport?: (format: "pdf") => void;
}

export function NotebookExport({ planId, onGenerate, onExport }: NotebookExportProps) {
  const [notebook, setNotebook] = useState<NotebookTemplate | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { toast.error("Please log in to continue"); return; }

      const response = await fetch(getApiUrl(API_ENDPOINTS.generateNotebook(planId)), {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err?.message || "Failed to generate notebook");
      }

      const data = await response.json();
      // Backend returns { notebook: NotebookTemplate }
      setNotebook(data.notebook || data);
      toast.success("Lab notebook generated");
      if (onGenerate) onGenerate();
    } catch (error) {
      console.error("Error generating notebook:", error);
      toast.error(error instanceof Error ? error.message : "Failed to generate notebook");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportPDF = () => {
    if (!notebook) return;

    setIsExporting(true);
    try {
      const doc = new jsPDF();
      let yPos = 20;

      // Title
      doc.setFontSize(18);
      doc.text("Laboratory Notebook", 20, yPos);
      yPos += 10;

      // Metadata
      doc.setFontSize(10);
      doc.text(`Title: ${notebook.title}`, 20, yPos);
      yPos += 6;
      doc.text(`Date: ${notebook.date}`, 20, yPos);
      yPos += 6;
      doc.text(`Hypothesis: ${notebook.hypothesis}`, 20, yPos);
      yPos += 12;

      // Sections
      notebook.sections.forEach((section) => {
        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }

        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.text(section.title, 20, yPos);
        yPos += 8;

        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        const contentLines = doc.splitTextToSize(section.content, 170);
        doc.text(contentLines, 20, yPos);
        yPos += contentLines.length * 5 + 10;

        // Fields
        if (section.fields) {
          Object.entries(section.fields).forEach(([key, value]) => {
            if (yPos > 270) {
              doc.addPage();
              yPos = 20;
            }
            doc.text(`${key}: ${value}`, 25, yPos);
            yPos += 6;
          });
          yPos += 5;
        }
      });

      // Materials Log
      if (notebook.materials_log.length > 0) {
        if (yPos > 250) {
          doc.addPage();
          yPos = 20;
        }

        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.text("Materials Receipt Log", 20, yPos);
        yPos += 8;

        doc.setFontSize(9);
        doc.setFont("helvetica", "normal");
        notebook.materials_log.forEach((material) => {
          if (yPos > 270) {
            doc.addPage();
            yPos = 20;
          }
          doc.text(`Material: ${material.material}`, 20, yPos);
          yPos += 5;
          doc.text(`Lot #: __________ | Received: __________ | Expiry: __________`, 25, yPos);
          yPos += 8;
        });
      }

      // Protocol Checklist
      if (notebook.protocol_checklist.length > 0) {
        if (yPos > 250) {
          doc.addPage();
          yPos = 20;
        }

        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.text("Protocol Checklist", 20, yPos);
        yPos += 8;

        doc.setFontSize(9);
        doc.setFont("helvetica", "normal");
        notebook.protocol_checklist.forEach((step) => {
          if (yPos > 270) {
            doc.addPage();
            yPos = 20;
          }
          doc.text(`☐ ${step.step}`, 20, yPos);
          yPos += 5;
          doc.text(`Observations: _________________________________`, 25, yPos);
          yPos += 8;
        });
      }

      // Save PDF
      doc.save(`lab-notebook-${Date.now()}.pdf`);
      toast.success("Notebook exported as PDF");
    } catch (error) {
      console.error("PDF export error:", error);
      toast.error("Failed to export notebook");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Lab Notebook
        </CardTitle>
        <CardDescription>
          Generate a structured lab notebook template for your experiment
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!notebook && (
          <Button onClick={handleGenerate} disabled={isGenerating} className="w-full">
            {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Generate Lab Notebook
          </Button>
        )}

        {notebook && (
          <div className="space-y-4">
            {/* Preview */}
            <div className="p-4 bg-muted rounded-lg max-h-96 overflow-y-auto">
              <h3 className="font-bold text-lg mb-2">{notebook.title}</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Date: {notebook.date} | Hypothesis: {notebook.hypothesis}
              </p>

              {notebook.sections.map((section, index) => (
                <div key={index} className="mb-4">
                  <h4 className="font-semibold text-sm mb-1">{section.title}</h4>
                  <p className="text-xs text-muted-foreground">{section.content}</p>
                  {section.fields && (
                    <div className="mt-2 space-y-1">
                      {Object.entries(section.fields).map(([key, value]) => (
                        <p key={key} className="text-xs">
                          <span className="font-medium">{key}:</span> {value}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              <div className="mt-4 pt-4 border-t">
                <h4 className="font-semibold text-sm mb-2">Materials Log</h4>
                <p className="text-xs text-muted-foreground">
                  {notebook.materials_log.length} materials to track
                </p>
              </div>

              <div className="mt-4 pt-4 border-t">
                <h4 className="font-semibold text-sm mb-2">Protocol Checklist</h4>
                <p className="text-xs text-muted-foreground">
                  {notebook.protocol_checklist.length} steps to complete
                </p>
              </div>

              <div className="mt-4 pt-4 border-t">
                <h4 className="font-semibold text-sm mb-2">Data Tables</h4>
                <p className="text-xs text-muted-foreground">
                  {notebook.data_tables.length} data collection tables
                </p>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="flex gap-2">
              <Button onClick={handleExportPDF} disabled={isExporting} className="flex-1">
                {isExporting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                Export as PDF
              </Button>
              <Button variant="outline" onClick={handleGenerate} disabled={isGenerating}>
                <FileText className="mr-2 h-4 w-4" />
                Regenerate
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
