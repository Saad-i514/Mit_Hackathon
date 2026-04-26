"use client";

import React, { useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { getApiUrl, API_ENDPOINTS } from "@/lib/config";

interface EquipmentChecklistProps {
  planId: string;
  equipment: string[];
  onUpdate?: (equipment: string, hasItem: boolean, notes?: string) => void;
}

export function EquipmentChecklist({ planId, equipment, onUpdate }: EquipmentChecklistProps) {
  const [checklist, setChecklist] = useState<Record<string, { hasItem: boolean; notes: string }>>(
    equipment.reduce((acc, item) => ({ ...acc, [item]: { hasItem: false, notes: "" } }), {})
  );

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const handleToggle = async (item: string, hasItem: boolean) => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { toast.error("Please log in to continue"); return; }

      const notes = checklist[item]?.notes || "";
      // Correct path: PUT /api/v1/plans/equipment/{name}?has_item=true&notes=...
      const url = `${getApiUrl(API_ENDPOINTS.updateEquipment(item))}?has_item=${hasItem}${notes ? `&notes=${encodeURIComponent(notes)}` : ""}`;

      const response = await fetch(url, {
        method: "PUT",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err?.message || "Failed to update equipment");
      }

      setChecklist((prev) => ({ ...prev, [item]: { ...prev[item], hasItem } }));
      toast.success(`${item} updated`);
      if (onUpdate) onUpdate(item, hasItem, notes);
    } catch (error) {
      console.error("Error updating equipment:", error);
      toast.error(error instanceof Error ? error.message : "Failed to update equipment");
    }
  };

  const handleNotesBlur = async (item: string) => {
    // Persist notes on blur
    const current = checklist[item];
    if (!current) return;
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const url = `${getApiUrl(API_ENDPOINTS.updateEquipment(item))}?has_item=${current.hasItem}${current.notes ? `&notes=${encodeURIComponent(current.notes)}` : ""}`;
      await fetch(url, {
        method: "PUT",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
    } catch (e) {
      // Silent fail on notes blur
    }
  };

  const handleNotesChange = (item: string, notes: string) => {
    setChecklist((prev) => ({ ...prev, [item]: { ...prev[item], notes } }));
  };

  if (equipment.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Equipment Checklist</CardTitle>
          <CardDescription>Track equipment availability for your experiment</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            No equipment items detected in this plan.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Equipment Checklist</CardTitle>
        <CardDescription>
          Track equipment availability — {equipment.filter(i => checklist[i]?.hasItem).length}/{equipment.length} available
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {equipment.map((item) => (
          <div key={item} className="flex items-start gap-4 p-3 border rounded-lg">
            <Checkbox
              id={item}
              checked={checklist[item]?.hasItem || false}
              onCheckedChange={(checked) => handleToggle(item, checked as boolean)}
              className="mt-1"
            />
            <div className="flex-1 space-y-2">
              <Label htmlFor={item} className="font-medium cursor-pointer">
                {item}
              </Label>
              <Input
                placeholder="Notes (e.g., location, booking required)"
                value={checklist[item]?.notes || ""}
                onChange={(e) => handleNotesChange(item, e.target.value)}
                onBlur={() => handleNotesBlur(item)}
                className="text-sm"
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
