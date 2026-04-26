"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, DollarSign, Clock } from "lucide-react";
import { ProtocolVariants } from "@/lib/types";

interface VariantSelectorProps {
  variants: ProtocolVariants;
  selectedVariant: "budget" | "standard" | "premium";
  onSelect: (variant: "budget" | "standard" | "premium") => void;
}

export function VariantSelector({ variants, selectedVariant, onSelect }: VariantSelectorProps) {
  const variantData = [
    {
      key: "budget" as const,
      name: "Budget",
      description: "Cost-optimized approach with essential materials",
      color: "border-green-500",
      bgColor: "bg-green-50 dark:bg-green-950",
    },
    {
      key: "standard" as const,
      name: "Standard",
      description: "Balanced approach with recommended materials",
      color: "border-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950",
    },
    {
      key: "premium" as const,
      name: "Premium",
      description: "High-quality materials for optimal results",
      color: "border-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950",
    },
  ];

  // Guard: if variants object is missing required keys, show a fallback
  if (!variants || (!variants.budget && !variants.standard && !variants.premium)) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Protocol variants are not available for this plan.
        </CardContent>
      </Card>
    );
  }

  const fmt = (val: number | undefined) =>
    val != null ? val.toLocaleString() : "N/A";

  // Normalize a variant to handle both old (total_cost_usd/timeline_weeks)
  // and new (total_budget/timeline_days) field names from the AI
  const normalize = (v: any) => {
    if (!v) return null;
    const total_budget = v.total_budget ?? v.total_cost_usd ?? v.total_cost ?? v.cost_usd;
    const timeline_days = v.timeline_days ?? (v.timeline_weeks != null ? v.timeline_weeks * 7 : undefined);
    // Always produce an array — AI sometimes returns a string or object
    const rawMods = v.protocol_modifications ?? v.key_tradeoffs ?? v.key_advantages ?? v.modifications;
    const protocol_modifications: string[] = Array.isArray(rawMods)
      ? rawMods
      : typeof rawMods === "string"
      ? rawMods.split(/[;\n]/).map((s: string) => s.trim()).filter(Boolean)
      : [];
    const materials = Array.isArray(v.materials)
      ? { items: v.materials, total_budget, currency: "USD" }
      : v.materials;
    return { ...v, total_budget, timeline_days, protocol_modifications, materials };
  };

  return (
    <div className="space-y-6">
      {/* Variant Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {variantData.map((variant) => {
          const data = normalize(variants[variant.key]);
          const isSelected = selectedVariant === variant.key;

          if (!data) return null;

          return (
            <Card
              key={variant.key}
              className={`cursor-pointer transition-all ${
                isSelected ? `${variant.color} border-2 ${variant.bgColor}` : "hover:shadow-lg"
              }`}
              onClick={() => onSelect(variant.key)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {variant.name}
                      {isSelected && <Check className="h-5 w-5 text-primary" />}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {data.protocol_modifications.length > 0
                        ? data.protocol_modifications[0]
                        : variant.description}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                    <span className="text-2xl font-bold">${fmt(data.total_budget)}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span>{data.timeline_days ?? "N/A"} days</span>
                  </div>
                </div>

                <div className="pt-3 border-t">
                  {data.protocol_modifications.length > 1 ? (
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {data.protocol_modifications.slice(0, 3).map((mod: string, i: number) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="mt-0.5 text-primary">•</span>
                          <span>{mod}</span>
                        </li>
                      ))}
                    </ul>
                  ) : data.protocol_modifications.length === 1 ? (
                    <p className="text-xs text-muted-foreground">{data.protocol_modifications[0]}</p>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Standard protocol — no modifications</p>
                  )}
                </div>

                {isSelected ? (
                  <Button className="w-full" variant="default">
                    Selected
                  </Button>
                ) : (
                  <Button className="w-full" variant="outline" onClick={() => onSelect(variant.key)}>
                    Select {variant.name}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Variant Comparison</CardTitle>
          <CardDescription>Detailed comparison of protocol variants</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold">Feature</th>
                  <th className="text-center p-3 font-semibold">Budget</th>
                  <th className="text-center p-3 font-semibold">Standard</th>
                  <th className="text-center p-3 font-semibold">Premium</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="p-3 font-medium">Total Cost</td>
                  <td className="text-center p-3">${fmt(normalize(variants.budget)?.total_budget)}</td>
                  <td className="text-center p-3">${fmt(normalize(variants.standard)?.total_budget)}</td>
                  <td className="text-center p-3">${fmt(normalize(variants.premium)?.total_budget)}</td>
                </tr>
                <tr className="border-b">
                  <td className="p-3 font-medium">Timeline</td>
                  <td className="text-center p-3">{normalize(variants.budget)?.timeline_days ?? "N/A"} days</td>
                  <td className="text-center p-3">{normalize(variants.standard)?.timeline_days ?? "N/A"} days</td>
                  <td className="text-center p-3">{normalize(variants.premium)?.timeline_days ?? "N/A"} days</td>
                </tr>
                <tr className="border-b">
                  <td className="p-3 font-medium">vs Standard</td>
                  {(() => {
                    const stdCost = normalize(variants.standard)?.total_budget ?? 0;
                    return (["budget", "standard", "premium"] as const).map((key) => {
                      const cost = normalize(variants[key])?.total_budget ?? 0;
                      const diff = cost - stdCost;
                      if (key === "standard") return <td key={key} className="text-center p-3 text-muted-foreground">—</td>;
                      return (
                        <td key={key} className="text-center p-3">
                          <span className={diff < 0 ? "text-emerald-500 font-medium" : "text-red-400 font-medium"}>
                            {diff < 0 ? `−$${fmt(Math.abs(diff))}` : `+$${fmt(diff)}`}
                          </span>
                        </td>
                      );
                    });
                  })()}
                </tr>
                <tr className="border-b">
                  <td className="p-3 font-medium">Modifications</td>
                  <td className="p-3">
                    <ul className="text-xs space-y-1">
                      {(normalize(variants.budget)?.protocol_modifications ?? []).slice(0, 2).map((mod: string, i: number) => (
                        <li key={i}>• {mod}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="p-3">
                    <ul className="text-xs space-y-1">
                      {(normalize(variants.standard)?.protocol_modifications ?? []).slice(0, 2).map((mod: string, i: number) => (
                        <li key={i}>• {mod}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="p-3">
                    <ul className="text-xs space-y-1">
                      {(normalize(variants.premium)?.protocol_modifications ?? []).slice(0, 2).map((mod: string, i: number) => (
                        <li key={i}>• {mod}</li>
                      ))}
                    </ul>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
