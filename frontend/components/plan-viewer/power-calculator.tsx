"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PowerAnalysis } from "@/lib/types";

interface PowerCalculatorProps {
  initialValues?: PowerAnalysis;
  onCalculate?: (analysis: PowerAnalysis) => void;
}

export function PowerCalculator({ initialValues, onCalculate }: PowerCalculatorProps) {
  const [testType, setTestType] = useState(initialValues?.test_type || "t-test");
  const [effectSize, setEffectSize] = useState(initialValues?.effect_size || 0.5);
  const [alpha, setAlpha] = useState(initialValues?.alpha || 0.05);
  const [power, setPower] = useState(initialValues?.power || 0.8);
  const [sampleSize, setSampleSize] = useState(initialValues?.sample_size || 0);
  const [interpretation, setInterpretation] = useState(initialValues?.interpretation || "");

  // Calculate sample size based on inputs
  useEffect(() => {
    const calculated = calculateSampleSize(testType, effectSize, alpha, power);
    setSampleSize(calculated.sampleSize);
    setInterpretation(calculated.interpretation);

    if (onCalculate) {
      onCalculate({
        test_type: testType,
        effect_size: effectSize,
        alpha,
        power,
        sample_size: calculated.sampleSize,
        interpretation: calculated.interpretation,
      });
    }
  }, [testType, effectSize, alpha, power]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistical Power Calculator</CardTitle>
        <CardDescription>
          Calculate required sample size for your experiment
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Test Type Selection */}
        <div className="space-y-2">
          <Label htmlFor="test-type">Test Type</Label>
          <Select value={testType} onValueChange={setTestType}>
            <SelectTrigger id="test-type">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="t-test">Independent t-test</SelectItem>
              <SelectItem value="paired-t-test">Paired t-test</SelectItem>
              <SelectItem value="anova">One-way ANOVA</SelectItem>
              <SelectItem value="chi-squared">Chi-squared test</SelectItem>
              <SelectItem value="log-rank">Log-rank (survival)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Effect Size Slider */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="effect-size">Effect Size (Cohen's d)</Label>
            <span className="text-sm text-muted-foreground">{effectSize.toFixed(2)}</span>
          </div>
          <input
            id="effect-size"
            type="range"
            min="0.1"
            max="2.0"
            step="0.1"
            value={effectSize}
            onChange={(e) => setEffectSize(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Small (0.2)</span>
            <span>Medium (0.5)</span>
            <span>Large (0.8)</span>
          </div>
        </div>

        {/* Alpha Slider */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="alpha">Significance Level (α)</Label>
            <span className="text-sm text-muted-foreground">{alpha.toFixed(3)}</span>
          </div>
          <input
            id="alpha"
            type="range"
            min="0.001"
            max="0.1"
            step="0.001"
            value={alpha}
            onChange={(e) => setAlpha(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.001</span>
            <span>0.05</span>
            <span>0.1</span>
          </div>
        </div>

        {/* Power Slider */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="power">Statistical Power (1-β)</Label>
            <span className="text-sm text-muted-foreground">{power.toFixed(2)}</span>
          </div>
          <input
            id="power"
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={power}
            onChange={(e) => setPower(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>50%</span>
            <span>80%</span>
            <span>99%</span>
          </div>
        </div>

        {/* Results */}
        <div className="pt-4 border-t">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-primary/10 rounded-lg">
              <span className="font-medium">Required Sample Size:</span>
              <span className="text-2xl font-bold text-primary">
                {sampleSize} {testType.includes("t-test") ? "per group" : "total"}
              </span>
            </div>
            
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Interpretation:</p>
              <p className="text-sm text-muted-foreground">{interpretation}</p>
            </div>

            <div className="text-xs text-muted-foreground space-y-1">
              <p>• Effect size: {getEffectSizeLabel(effectSize)}</p>
              <p>• Type I error rate (α): {(alpha * 100).toFixed(1)}%</p>
              <p>• Type II error rate (β): {((1 - power) * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Helper function to calculate sample size
function calculateSampleSize(
  testType: string,
  effectSize: number,
  alpha: number,
  power: number
): { sampleSize: number; interpretation: string } {
  // Z-scores for alpha and power
  const zAlpha = getZScore(alpha / 2); // Two-tailed
  const zBeta = getZScore(1 - power);

  let n = 0;
  let interpretation = "";

  switch (testType) {
    case "t-test":
    case "paired-t-test":
      // Formula: n = 2 * ((z_alpha + z_beta) / effect_size)^2
      n = Math.ceil(2 * Math.pow((zAlpha + zBeta) / effectSize, 2));
      interpretation = `For a ${testType} with effect size ${effectSize.toFixed(2)}, you need ${n} participants per group (${n * 2} total) to detect a significant difference with ${(power * 100).toFixed(0)}% power at α=${alpha}.`;
      break;

    case "anova":
      // Simplified ANOVA calculation (3 groups assumed)
      const groups = 3;
      n = Math.ceil((groups * Math.pow((zAlpha + zBeta) / effectSize, 2)) / (groups - 1));
      interpretation = `For a one-way ANOVA with ${groups} groups and effect size ${effectSize.toFixed(2)}, you need approximately ${n} participants per group (${n * groups} total) to achieve ${(power * 100).toFixed(0)}% power.`;
      break;

    case "chi-squared":
      // Chi-squared approximation
      n = Math.ceil(Math.pow((zAlpha + zBeta), 2) / Math.pow(effectSize, 2));
      interpretation = `For a chi-squared test with effect size ${effectSize.toFixed(2)}, you need approximately ${n} total observations to detect an association with ${(power * 100).toFixed(0)}% power.`;
      break;

    case "log-rank":
      // Log-rank (survival analysis) approximation
      n = Math.ceil(4 * Math.pow((zAlpha + zBeta) / effectSize, 2));
      interpretation = `For a log-rank test (survival analysis) with hazard ratio corresponding to effect size ${effectSize.toFixed(2)}, you need approximately ${n} events (not participants) to achieve ${(power * 100).toFixed(0)}% power.`;
      break;

    default:
      n = Math.ceil(2 * Math.pow((zAlpha + zBeta) / effectSize, 2));
      interpretation = `Sample size calculation: ${n} participants needed.`;
  }

  return { sampleSize: Math.max(n, 2), interpretation };
}

// Helper function to get Z-score from probability
function getZScore(p: number): number {
  // Approximation of inverse normal CDF
  if (p <= 0 || p >= 1) return 0;
  
  const a1 = -39.6968302866538;
  const a2 = 220.946098424521;
  const a3 = -275.928510446969;
  const a4 = 138.357751867269;
  const a5 = -30.6647980661472;
  const a6 = 2.50662827745924;
  
  const b1 = -54.4760987982241;
  const b2 = 161.585836858041;
  const b3 = -155.698979859887;
  const b4 = 66.8013118877197;
  const b5 = -13.2806815528857;
  
  const c1 = -0.00778489400243029;
  const c2 = -0.322396458041136;
  const c3 = -2.40075827716184;
  const c4 = -2.54973253934373;
  const c5 = 4.37466414146497;
  const c6 = 2.93816398269878;
  
  const d1 = 0.00778469570904146;
  const d2 = 0.32246712907004;
  const d3 = 2.445134137143;
  const d4 = 3.75440866190742;
  
  const pLow = 0.02425;
  const pHigh = 1 - pLow;
  
  let q, r, z;
  
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p));
    z = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
        ((((d1 * q + d2) * q + d3) * q + d4) * q + 1);
  } else if (p <= pHigh) {
    q = p - 0.5;
    r = q * q;
    z = (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q /
        (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1);
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p));
    z = -(((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) /
         ((((d1 * q + d2) * q + d3) * q + d4) * q + 1);
  }
  
  return z;
}

// Helper function to label effect size
function getEffectSizeLabel(effectSize: number): string {
  if (effectSize < 0.3) return "Small";
  if (effectSize < 0.6) return "Medium";
  if (effectSize < 0.9) return "Large";
  return "Very Large";
}
