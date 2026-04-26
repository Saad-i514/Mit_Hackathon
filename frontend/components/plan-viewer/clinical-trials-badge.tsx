"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { AlertCircle, CheckCircle, AlertTriangle, ExternalLink } from "lucide-react";
import { ClinicalTrialResult } from "@/lib/types";

interface ClinicalTrialsBadgeProps {
  clinicalTrials: ClinicalTrialResult;
}

export function ClinicalTrialsBadge({ clinicalTrials }: ClinicalTrialsBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);

  const getStatus = () => {
    if (clinicalTrials.total_found === 0) {
      return {
        variant: "default" as const,
        icon: <CheckCircle className="h-4 w-4" />,
        text: "No overlapping trials",
        color: "bg-green-500",
      };
    } else if (clinicalTrials.total_found <= 5) {
      return {
        variant: "secondary" as const,
        icon: <AlertCircle className="h-4 w-4" />,
        text: `${clinicalTrials.total_found} related trials`,
        color: "bg-yellow-500",
      };
    } else {
      return {
        variant: "destructive" as const,
        icon: <AlertTriangle className="h-4 w-4" />,
        text: `${clinicalTrials.total_found} overlapping trials`,
        color: "bg-red-500",
      };
    }
  };

  const status = getStatus();

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Badge
          variant={status.variant}
          className="cursor-pointer hover:opacity-80 transition-opacity flex items-center gap-2"
        >
          {status.icon}
          {status.text}
        </Badge>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {status.icon}
            Clinical Trials Radar
          </DialogTitle>
          <DialogDescription>
            Related clinical trials found on ClinicalTrials.gov
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className={`${status.color} text-white px-4 py-2 rounded-lg`}>
                  <div className="text-3xl font-bold">{clinicalTrials.total_found}</div>
                  <div className="text-xs">trials found</div>
                </div>
                <div className="flex-1">
                  {clinicalTrials.total_found === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No overlapping clinical trials were found for this hypothesis. This suggests your
                      research direction is novel or underexplored.
                    </p>
                  )}
                  {clinicalTrials.total_found > 0 && clinicalTrials.total_found <= 5 && (
                    <p className="text-sm text-muted-foreground">
                      A small number of related trials were found. Review them to understand the current
                      research landscape and identify potential collaborations or gaps.
                    </p>
                  )}
                  {clinicalTrials.total_found > 5 && (
                    <p className="text-sm text-muted-foreground">
                      Multiple overlapping trials detected. Consider reviewing these studies to ensure your
                      research adds unique value and doesn't duplicate ongoing work.
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trial List */}
          {clinicalTrials.studies.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-sm">Related Trials:</h4>
              {clinicalTrials.studies.map((study) => (
                <Card key={study.nct_id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-base">{study.title}</CardTitle>
                        <div className="flex gap-2 mt-2">
                          <Badge variant="outline">{study.nct_id}</Badge>
                          <Badge variant="secondary">{study.status}</Badge>
                          {study.phase && <Badge>{study.phase}</Badge>}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        asChild
                      >
                        <a
                          href={study.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1"
                        >
                          <ExternalLink className="h-4 w-4" />
                          View
                        </a>
                      </Button>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          )}

          {/* Error Message */}
          {clinicalTrials.error && (
            <Card className="border-yellow-500">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  API Error
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{clinicalTrials.error}</p>
              </CardContent>
            </Card>
          )}

          {/* Footer */}
          <div className="pt-4 border-t text-xs text-muted-foreground">
            <p>
              Data sourced from{" "}
              <a
                href="https://clinicaltrials.gov"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-primary"
              >
                ClinicalTrials.gov
              </a>
              . Last checked: {new Date().toLocaleDateString()}
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
