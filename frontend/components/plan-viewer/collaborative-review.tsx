"use client";

import React, { useEffect, useState } from "react";
import { createSupabaseClient } from "@/lib/supabase";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Users } from "lucide-react";
import { PlanAnnotation } from "@/lib/types";
import { toast } from "sonner";

interface CollaborativeReviewProps {
  planId: string;
  onAnnotate?: (annotation: Omit<PlanAnnotation, "id" | "created_at">) => void;
}

interface Presence {
  user_id: string;
  user_name: string;
  viewing_section: string;
}

export function CollaborativeReview({ planId, onAnnotate }: CollaborativeReviewProps) {
  const [annotations, setAnnotations] = useState<PlanAnnotation[]>([]);
  const [presence, setPresence] = useState<Presence[]>([]);
  const [newAnnotation, setNewAnnotation] = useState("");
  const [selectedSection, setSelectedSection] = useState("protocol");
  const supabase = createSupabaseClient();

  useEffect(() => {
    // Subscribe to annotations
    const annotationsChannel = supabase
      .channel(`plan-annotations-${planId}`)
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "plan_annotations",
          filter: `plan_id=eq.${planId}`,
        },
        (payload) => {
          if (payload.eventType === "INSERT") {
            setAnnotations((prev) => [...prev, payload.new as PlanAnnotation]);
          }
        }
      )
      .subscribe();

    // Subscribe to presence
    const presenceChannel = supabase.channel(`plan-presence-${planId}`, {
      config: { presence: { key: planId } },
    });

    presenceChannel
      .on("presence", { event: "sync" }, () => {
        const state = presenceChannel.presenceState();
        const users = Object.values(state)
          .flat()
          .map((entry) => entry as unknown as Partial<Presence>)
          .filter(
            (entry): entry is Presence =>
              Boolean(entry.user_id && entry.user_name && entry.viewing_section)
          );
        setPresence(users);
      })
      .subscribe(async (status) => {
        if (status === "SUBSCRIBED") {
          await presenceChannel.track({
            user_id: "current-user",
            user_name: "You",
            viewing_section: selectedSection,
          });
        }
      });

    // Load existing annotations
    loadAnnotations();

    return () => {
      supabase.removeChannel(annotationsChannel);
      supabase.removeChannel(presenceChannel);
    };
  }, [planId, supabase]);

  const loadAnnotations = async () => {
    try {
      const { data, error } = await supabase
        .from("plan_annotations")
        .select("*")
        .eq("plan_id", planId)
        .order("created_at", { ascending: false });

      if (error) throw error;
      setAnnotations(data || []);
    } catch (error) {
      console.error("Error loading annotations:", error);
    }
  };

  const handleAddAnnotation = async () => {
    if (!newAnnotation.trim()) return;

    try {
      const annotation: Omit<PlanAnnotation, "id" | "created_at"> = {
        plan_id: planId,
        section: selectedSection,
        content: newAnnotation,
        author_id: "current-user",
        author_role: "Scientist",
      };

      const { error } = await supabase.from("plan_annotations").insert([annotation]);

      if (error) throw error;

      setNewAnnotation("");
      toast.success("Annotation added");

      if (onAnnotate) {
        onAnnotate(annotation);
      }
    } catch (error) {
      console.error("Error adding annotation:", error);
      toast.error("Failed to add annotation");
    }
  };

  return (
    <div className="space-y-4">
      {/* Active Reviewers */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Active Reviewers
              </CardTitle>
              <CardDescription>Currently viewing this plan</CardDescription>
            </div>
            <Badge variant="secondary">{presence.length} online</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {presence.map((user, index) => (
              <div key={index} className="flex items-center gap-2 p-2 bg-muted rounded-lg">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{user.user_name.charAt(0)}</AvatarFallback>
                </Avatar>
                <div className="text-sm">
                  <div className="font-medium">{user.user_name}</div>
                  <div className="text-xs text-muted-foreground">{user.viewing_section}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Add Annotation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Add Annotation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <label className="text-sm font-medium">Section:</label>
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="w-full mt-1 p-2 border rounded-md"
            >
              <option value="protocol">Protocol</option>
              <option value="materials">Materials</option>
              <option value="timeline">Timeline</option>
              <option value="validation">Validation</option>
              <option value="safety">Safety</option>
            </select>
          </div>
          <Textarea
            placeholder="Add your comment or suggestion..."
            value={newAnnotation}
            onChange={(e) => setNewAnnotation(e.target.value)}
            rows={3}
          />
          <Button onClick={handleAddAnnotation} disabled={!newAnnotation.trim()}>
            Add Annotation
          </Button>
        </CardContent>
      </Card>

      {/* Annotations Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Review Feed</CardTitle>
          <CardDescription>{annotations.length} annotations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {annotations.map((annotation) => (
              <div key={annotation.id} className="p-3 border rounded-lg space-y-2">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="text-xs">
                        {annotation.author_role?.charAt(0) || "U"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="text-sm">
                      <span className="font-medium">{annotation.author_role || "User"}</span>
                      <span className="text-muted-foreground"> • </span>
                      <Badge variant="outline" className="text-xs">
                        {annotation.section}
                      </Badge>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(annotation.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm">{annotation.content}</p>
              </div>
            ))}

            {annotations.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No annotations yet. Be the first to add one!</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
