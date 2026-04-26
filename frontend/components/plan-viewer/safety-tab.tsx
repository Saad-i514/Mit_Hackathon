"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Shield, Flame, Skull, Droplet, AlertCircle, CheckCircle2, Beaker } from "lucide-react";
import { SafetyAssessment } from "@/lib/types";

interface SafetyTabProps {
  safetyAssessment: SafetyAssessment;
}

export function SafetyTab({ safetyAssessment }: SafetyTabProps) {
  if (!safetyAssessment) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          No safety assessment available for this plan.
        </CardContent>
      </Card>
    );
  }

  const getBSLColor = (level: number) => {
    switch (level) {
      case 1: return { bg: "bg-emerald-500", ring: "ring-emerald-400", label: "Low Risk" };
      case 2: return { bg: "bg-yellow-500", ring: "ring-yellow-400", label: "Moderate Risk" };
      case 3: return { bg: "bg-orange-500", ring: "ring-orange-400", label: "High Risk" };
      case 4: return { bg: "bg-red-600", ring: "ring-red-500", label: "Maximum Risk" };
      default: return { bg: "bg-slate-500", ring: "ring-slate-400", label: "Unknown" };
    }
  };

  const getGHSIcon = (code: string) => {
    if (code.includes("02") || code.includes("03")) return <Flame className="h-3.5 w-3.5" />;
    if (code.includes("06") || code.includes("08")) return <Skull className="h-3.5 w-3.5" />;
    if (code.includes("05")) return <Droplet className="h-3.5 w-3.5" />;
    return <AlertCircle className="h-3.5 w-3.5" />;
  };

  const bsl = getBSLColor(safetyAssessment.bsl_level ?? 1);
  const hazardous_reagents = safetyAssessment.hazardous_reagents ?? [];
  const ppe_required = safetyAssessment.ppe_required ?? [];
  const waste_disposal = safetyAssessment.waste_disposal ?? {};
  const emergency_contacts = safetyAssessment.emergency_contacts ?? [];

  return (
    <div className="space-y-5">

      {/* BSL Level */}
      <Card className="border-0 bg-card/60 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-5 w-5 text-blue-400" />
                Biosafety Level
              </CardTitle>
              <CardDescription>Required containment level for this experiment</CardDescription>
            </div>
            <div className={`${bsl.bg} ring-2 ${bsl.ring} text-white px-5 py-3 rounded-xl text-center shadow-lg`}>
              <div className="text-3xl font-black">BSL-{safetyAssessment.bsl_level ?? "?"}</div>
              <div className="text-xs font-medium opacity-90">{bsl.label}</div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">{safetyAssessment.bsl_rationale}</p>
        </CardContent>
      </Card>

      {/* Regulatory Approvals */}
      {(safetyAssessment.requires_iacuc || safetyAssessment.requires_irb || safetyAssessment.requires_biosafety_committee) && (
        <div className="space-y-2">
          {safetyAssessment.requires_iacuc && (
            <Alert className="border-orange-500/50 bg-orange-500/10">
              <AlertTriangle className="h-4 w-4 text-orange-400" />
              <AlertTitle className="text-orange-300">IACUC Approval Required</AlertTitle>
              <AlertDescription className="text-orange-200/80">
                This experiment involves vertebrate animals and requires Institutional Animal Care and Use Committee approval.
              </AlertDescription>
            </Alert>
          )}
          {safetyAssessment.requires_irb && (
            <Alert className="border-red-500/50 bg-red-500/10">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              <AlertTitle className="text-red-300">IRB Approval Required</AlertTitle>
              <AlertDescription className="text-red-200/80">
                This experiment involves human subjects and requires Institutional Review Board approval.
              </AlertDescription>
            </Alert>
          )}
          {safetyAssessment.requires_biosafety_committee && (
            <Alert className="border-yellow-500/50 bg-yellow-500/10">
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
              <AlertTitle className="text-yellow-300">Biosafety Committee Approval Required</AlertTitle>
              <AlertDescription className="text-yellow-200/80">
                This experiment requires Institutional Biosafety Committee approval due to BSL-2+ containment requirements.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Hazardous Reagents */}
      {hazardous_reagents.length > 0 && (
        <Card className="border-0 bg-card/60 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Beaker className="h-5 w-5 text-red-400" />
              Hazardous Reagents
              <Badge variant="destructive" className="ml-1">{hazardous_reagents.length}</Badge>
            </CardTitle>
            <CardDescription>Materials requiring special handling and PPE</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {hazardous_reagents.map((reagent, index) => (
                <div key={index} className="p-4 rounded-xl border border-red-500/20 bg-red-500/5 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-semibold text-sm text-foreground">{reagent.name}</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {(reagent.ghs_codes ?? []).map((code) => (
                        <Badge key={code} className="bg-red-600/80 text-white border-0 flex items-center gap-1 text-xs">
                          {getGHSIcon(code)}
                          {code}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div className="bg-background/40 rounded-lg p-2.5">
                      <span className="font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Hazard</span>
                      <p className="text-foreground mt-1">{reagent.hazard}</p>
                    </div>
                    <div className="bg-background/40 rounded-lg p-2.5">
                      <span className="font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Additional PPE</span>
                      <p className="text-foreground mt-1">{reagent.ppe_addition}</p>
                    </div>
                    <div className="bg-background/40 rounded-lg p-2.5">
                      <span className="font-semibold text-muted-foreground uppercase tracking-wide text-[10px]">Disposal</span>
                      <p className="text-foreground mt-1">{reagent.disposal}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* PPE Requirements */}
      {ppe_required.length > 0 && (
        <Card className="border-0 bg-card/60 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-5 w-5 text-blue-400" />
              Personal Protective Equipment
            </CardTitle>
            <CardDescription>Required safety equipment for this experiment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {ppe_required.map((ppe, index) => (
                <div key={index} className="flex items-center gap-2 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <CheckCircle2 className="h-4 w-4 text-blue-400 flex-shrink-0" />
                  <span className="text-sm font-medium text-foreground capitalize">{ppe}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Waste Disposal */}
      {Object.keys(waste_disposal).length > 0 && (
        <Card className="border-0 bg-card/60 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Droplet className="h-5 w-5 text-cyan-400" />
              Waste Disposal
            </CardTitle>
            <CardDescription>Proper disposal methods for experiment waste</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(waste_disposal).map(([category, method]) => (
                <div key={category} className="flex items-start gap-3 p-3 rounded-lg border border-cyan-500/20 bg-cyan-500/5">
                  <Droplet className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs font-semibold text-cyan-300 uppercase tracking-wide">{category}</span>
                    <p className="text-sm text-foreground mt-0.5">{String(method)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Emergency Contacts */}
      {emergency_contacts.length > 0 && (
        <Card className="border-0 bg-card/60 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              Emergency Contacts
            </CardTitle>
            <CardDescription>Important contacts in case of emergency</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {emergency_contacts.map((contact, index) => (
                <div key={index} className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <AlertTriangle className="h-4 w-4 text-red-400 flex-shrink-0" />
                  <span className="text-sm font-medium text-foreground">{contact}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No safety data fallback */}
      {hazardous_reagents.length === 0 && ppe_required.length === 0 && Object.keys(waste_disposal).length === 0 && (
        <Card className="border-0 bg-card/60">
          <CardContent className="py-8 text-center text-muted-foreground">
            <Shield className="h-10 w-10 mx-auto mb-3 opacity-40" />
            <p className="text-sm">No specific safety hazards identified for this experiment.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
