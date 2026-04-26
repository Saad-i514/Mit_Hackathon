"use client";

import React, { useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { History, RotateCcw, GitCompare } from "lucide-react";
import { PlanVersion } from "@/lib/types";
import { toast } from "sonner";
import Diff from "fast-diff";
import { getApiUrl, API_ENDPOINTS } from "@/lib/config";

interface VersionHistoryProps {
  planId: string;
  versions: PlanVersion[];
  onRestore?: (versionNumber: number) => void;
  onCompare?: (version1: number, version2: number) => void;
}

export function VersionHistory({ planId, versions, onRestore, onCompare }: VersionHistoryProps) {
  const [selectedVersions, setSelectedVersions] = useState<number[]>([]);
  const [diffView, setDiffView] = useState<any>(null);

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const handleVersionSelect = (versionNumber: number) => {
    if (selectedVersions.includes(versionNumber)) {
      setSelectedVersions(selectedVersions.filter((v) => v !== versionNumber));
    } else if (selectedVersions.length < 2) {
      setSelectedVersions([...selectedVersions, versionNumber]);
    } else {
      setSelectedVersions([selectedVersions[1], versionNumber]);
    }
  };

  const handleCompare = () => {
    if (selectedVersions.length !== 2) {
      toast.error("Please select exactly 2 versions to compare");
      return;
    }

    const [v1, v2] = [...selectedVersions].sort((a, b) => a - b);
    const version1 = versions.find((v) => v.version_number === v1);
    const version2 = versions.find((v) => v.version_number === v2);

    // Backend list endpoint currently does not include snapshots.
    if (!version1 || !version2 || !version1.plan_snapshot || !version2.plan_snapshot) {
      toast.error("Diff data unavailable. Load full snapshots first.");
      return;
    }

    // Generate diff
    const text1 = JSON.stringify(version1.plan_snapshot, null, 2);
    const text2 = JSON.stringify(version2.plan_snapshot, null, 2);
    const diff = Diff(text1, text2);

    setDiffView({ v1, v2, diff });

    if (onCompare) {
      onCompare(v1, v2);
    }
  };

  const handleRestore = async (versionNumber: number) => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { toast.error("Please log in to continue"); return; }

      // Backend expects version_number (integer), not UUID
      const response = await fetch(
        getApiUrl(API_ENDPOINTS.restoreVersion(planId, versionNumber)),
        {
          method: "POST",
          headers: { Authorization: `Bearer ${session.access_token}` },
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err?.message || "Failed to restore version");
      }

      toast.success(`Restored to version ${versionNumber}`);
      if (onRestore) onRestore(versionNumber);
    } catch (error) {
      console.error("Error restoring version:", error);
      toast.error(error instanceof Error ? error.message : "Failed to restore version");
    }
  };

  const getTriggerBadge = (trigger: string) => {
    const colors: Record<string, string> = {
      initial_generation: "bg-blue-500",
      scientist_correction: "bg-green-500",
      hypothesis_edit: "bg-yellow-500",
      manual_regen: "bg-purple-500",
    };

    return (
      <Badge className={colors[trigger] || "bg-gray-500"}>
        {trigger.replace(/_/g, " ")}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {/* Version Rail */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Version History
              </CardTitle>
              <CardDescription>{versions.length} versions available</CardDescription>
            </div>
            {selectedVersions.length === 2 && (
              <Button onClick={handleCompare} variant="outline" size="sm">
                <GitCompare className="h-4 w-4 mr-2" />
                Compare
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {versions.map((version) => (
              <div
                key={version.version_number}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedVersions.includes(version.version_number)
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted"
                }`}
                onClick={() => handleVersionSelect(version.version_number)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">Version {version.version_number}</span>
                      {getTriggerBadge(version.triggered_by)}
                      {version.version_number === versions[0].version_number && (
                        <Badge variant="default">Current</Badge>
                      )}
                    </div>
                    {version.change_summary && (
                      <p className="text-sm text-muted-foreground mb-2">{version.change_summary}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {new Date(version.created_at).toLocaleString()}
                    </p>
                  </div>
                  {version.version_number !== versions[0].version_number && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRestore(version.version_number);
                      }}
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Restore
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Diff View */}
      {diffView && (
        <Card>
          <CardHeader>
            <CardTitle>
              Comparing Version {diffView.v1} → Version {diffView.v2}
            </CardTitle>
            <CardDescription>Changes between selected versions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-4 rounded-lg max-h-96 overflow-y-auto font-mono text-sm">
              {diffView.diff.map((part: any, index: number) => {
                const [type, text] = part;
                let className = "";
                let prefix = "";

                if (type === -1) {
                  className = "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
                  prefix = "- ";
                } else if (type === 1) {
                  className = "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
                  prefix = "+ ";
                }

                return (
                  <span key={index} className={className}>
                    {prefix}
                    {text}
                  </span>
                );
              })}
            </div>
            <div className="mt-4 flex justify-end">
              <Button variant="outline" onClick={() => setDiffView(null)}>
                Close Diff
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
