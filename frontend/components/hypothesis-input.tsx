/**
 * Hypothesis Input Component
 * Allows users to input and submit scientific hypotheses
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Send, AlertCircle } from 'lucide-react';
import { HypothesisInputProps } from '@/lib/types';
import { APP_CONFIG, VALIDATION_RULES, ERROR_MESSAGES } from '@/lib/config';

export function HypothesisInput({ onSubmit, isLoading, disabled = false }: HypothesisInputProps) {
  const [hypothesis, setHypothesis] = useState('');
  const [error, setError] = useState<string | null>(null);

  const characterCount = hypothesis.length;
  const isOverLimit = characterCount > APP_CONFIG.maxHypothesisLength;
  const isUnderLimit = characterCount < VALIDATION_RULES.hypothesis.minLength;
  const canSubmit = !isLoading && !disabled && !isOverLimit && !isUnderLimit && hypothesis.trim().length > 0;

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous errors
    setError(null);
    
    // Validate hypothesis
    const trimmedHypothesis = hypothesis.trim();
    
    if (!trimmedHypothesis) {
      setError(ERROR_MESSAGES.INVALID_HYPOTHESIS);
      return;
    }
    
    if (trimmedHypothesis.length < VALIDATION_RULES.hypothesis.minLength) {
      setError(ERROR_MESSAGES.HYPOTHESIS_TOO_SHORT);
      return;
    }
    
    if (trimmedHypothesis.length > APP_CONFIG.maxHypothesisLength) {
      setError(ERROR_MESSAGES.HYPOTHESIS_TOO_LONG);
      return;
    }
    
    // Submit hypothesis
    onSubmit(trimmedHypothesis);
  }, [hypothesis, onSubmit]);

  const handleTextareaChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setHypothesis(value);
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  }, [error]);

  const getCharacterCountColor = () => {
    if (isOverLimit) return 'text-red-500';
    if (characterCount > APP_CONFIG.maxHypothesisLength * 0.9) return 'text-yellow-500';
    return 'text-gray-500';
  };

  const getCharacterCountText = () => {
    return `${characterCount} / ${APP_CONFIG.maxHypothesisLength}`;
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Scientific Hypothesis
        </CardTitle>
        <CardDescription>
          Enter your scientific hypothesis to generate a complete experiment plan. 
          Be specific about what you want to test and the expected outcomes.
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="hypothesis" className="text-sm font-medium">
              Hypothesis Statement
            </Label>
            
            <Textarea
              id="hypothesis"
              placeholder="Example: I hypothesize that adding 10mM glucose to the cell culture medium will increase cell proliferation by 25% compared to the control group, as measured by MTT assay after 48 hours of incubation."
              value={hypothesis}
              onChange={handleTextareaChange}
              disabled={isLoading || disabled}
              className={`min-h-[120px] resize-none ${
                isOverLimit ? 'border-red-500 focus:border-red-500' : ''
              } ${
                isUnderLimit && hypothesis.length > 0 ? 'border-yellow-500 focus:border-yellow-500' : ''
              }`}
              rows={6}
            />
            
            <div className="flex justify-between items-center text-sm">
              <div className="text-gray-600">
                Minimum {VALIDATION_RULES.hypothesis.minLength} characters required
              </div>
              <div className={getCharacterCountColor()}>
                {getCharacterCountText()}
              </div>
            </div>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              type="submit"
              disabled={!canSubmit}
              className="flex-1 sm:flex-none"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating Plan...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Generate Experiment Plan
                </>
              )}
            </Button>
            
            {hypothesis.trim() && !isLoading && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setHypothesis('');
                  setError(null);
                }}
                disabled={disabled}
              >
                Clear
              </Button>
            )}
          </div>

          <div className="text-xs text-gray-500 space-y-1">
            <p>
              <strong>Tips for better results:</strong>
            </p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>Be specific about what you want to measure</li>
              <li>Include expected outcomes or ranges</li>
              <li>Mention the experimental approach if known</li>
              <li>Specify the biological system or materials involved</li>
            </ul>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}