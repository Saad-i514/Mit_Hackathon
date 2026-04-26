"use client";

import React, { useState } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Copy, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { getApiUrl, API_ENDPOINTS } from "@/lib/config";

interface GrantMethodsProps {
  planId: string;
  onGenerate?: (grantBody: "NIH" | "NSF" | "ERC") => void;
}

export function GrantMethods({ planId, onGenerate }: GrantMethodsProps) {
  const [grantBody, setGrantBody] = useState<"NIH" | "NSF" | "ERC">("NIH");
  const [methodsText, setMethodsText] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { toast.error("Please log in to continue"); return; }

      // grant_body is a query param, not a request body
      const url = `${getApiUrl(API_ENDPOINTS.generateGrantMethods(planId))}?grant_body=${grantBody}`;
      const response = await fetch(url, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err?.message || "Failed to generate grant methods");
      }

      const data = await response.json();
      // Backend returns { grant_body, methods_section, generated_at }
      setMethodsText(data.methods_section || data.methods_text || "");
      toast.success("Grant Methods section generated");
      if (onGenerate) onGenerate(grantBody);
    } catch (error) {
      console.error("Error generating grant methods:", error);
      toast.error(error instanceof Error ? error.message : "Failed to generate grant methods");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(methodsText);
    toast.success("Copied to clipboard");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Grant Methods Section</CardTitle>
        <CardDescription>
          Generate a Methods section formatted for grant applications
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <Select value={grantBody} onValueChange={(v) => setGrantBody(v as "NIH" | "NSF" | "ERC")}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NIH">NIH (National Institutes of Health)</SelectItem>
                <SelectItem value="NSF">NSF (National Science Foundation)</SelectItem>
                <SelectItem value="ERC">ERC (European Research Council)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Generate
          </Button>
        </div>

        {methodsText && (
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-sm">Generated Methods Section:</h4>
              <Button variant="ghost" size="sm" onClick={handleCopy}>
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
            </div>
            <div className="p-4 bg-muted rounded-lg max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm font-mono">{methodsText}</pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
