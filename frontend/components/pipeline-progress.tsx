/**
 * Pipeline Progress Component
 * Displays real-time progress of the AI experiment planning pipeline
 */

'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Loader2, 
  FlaskConical,
  BookOpen,
  FileText,
  Timer
} from 'lucide-react';
import { PipelineProgressProps, SSEEvent, EventType, StageType } from '@/lib/types';

interface StageInfo {
  id: StageType;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  estimatedDuration: string;
}

const PIPELINE_STAGES: StageInfo[] = [
  {
    id: 'validation',
    name: 'Hypothesis Validation',
    description: 'Validating hypothesis and extracting scientific domain',
    icon: FlaskConical,
    estimatedDuration: '~5 seconds'
  },
  {
    id: 'literature_qc',
    name: 'Literature Review',
    description: 'Searching scientific literature and assessing novelty',
    icon: BookOpen,
    estimatedDuration: '~30 seconds'
  },
  {
    id: 'plan_generation',
    name: 'Plan Generation',
    description: 'Generating detailed experiment plan with AI',
    icon: FileText,
    estimatedDuration: '~60 seconds'
  }
];

type StageStatus = 'pending' | 'in_progress' | 'completed' | 'error';

interface StageState {
  status: StageStatus;
  progress: number;
  message?: string;
  duration?: number;
  error?: string;
  details?: Record<string, any>;
}

export function PipelineProgress({ events, currentStage }: PipelineProgressProps) {
  // Process events to determine stage states
  const stageStates = useMemo(() => {
    const states: Record<StageType, StageState> = {
      validation: { status: 'pending', progress: 0 },
      literature_qc: { status: 'pending', progress: 0 },
      plan_generation: { status: 'pending', progress: 0 }
    };

    let overallProgress = 0;
    let hasError = false;

    events.forEach(event => {
      const stage = event.data.stage as StageType;
      
      switch (event.event_type) {
        case EventType.STAGE_START:
          if (stage && states[stage]) {
            states[stage].status = 'in_progress';
            states[stage].message = event.data.description;
          }
          break;

        case EventType.PROGRESS:
          if (stage && states[stage]) {
            states[stage].progress = event.data.progress_percent || 0;
            states[stage].message = event.data.message;
            states[stage].details = event.data.details;
            overallProgress = Math.max(overallProgress, event.data.progress_percent || 0);
          }
          break;

        case EventType.STAGE_COMPLETE:
          if (stage && states[stage]) {
            states[stage].status = 'completed';
            states[stage].progress = 100;
            states[stage].duration = event.data.duration;
            states[stage].details = event.data.result_summary;
          }
          break;

        case EventType.ERROR:
          hasError = true;
          if (stage && states[stage]) {
            states[stage].status = 'error';
            states[stage].error = event.data.message;
          }
          break;

        case EventType.COMPLETE:
          // Mark all stages as completed
          Object.keys(states).forEach(stageKey => {
            const stageState = states[stageKey as StageType];
            if (stageState.status !== 'error') {
              stageState.status = 'completed';
              stageState.progress = 100;
            }
          });
          overallProgress = 100;
          break;
      }
    });

    return { states, overallProgress, hasError };
  }, [events]);

  const getStageIcon = (stage: StageInfo, state: StageState) => {
    const IconComponent = stage.icon;
    
    switch (state.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <IconComponent className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStageStatusBadge = (state: StageState) => {
    switch (state.status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-100 text-green-800">Completed</Badge>;
      case 'in_progress':
        return <Badge variant="default" className="bg-blue-100 text-blue-800">In Progress</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="secondary">Pending</Badge>;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    return seconds < 60 ? `${seconds.toFixed(1)}s` : `${(seconds / 60).toFixed(1)}m`;
  };

  const latestErrorEvent = events
    .filter(e => e.event_type === EventType.ERROR)
    .pop();

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timer className="h-5 w-5" />
          Experiment Plan Generation Progress
        </CardTitle>
        <CardDescription>
          AI is analyzing your hypothesis and generating a complete experiment plan
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="font-medium">Overall Progress</span>
            <span>{Math.round(stageStates.overallProgress)}%</span>
          </div>
          <Progress value={stageStates.overallProgress} className="h-2" />
        </div>

        {/* Stage Progress */}
        <div className="space-y-4">
          {PIPELINE_STAGES.map((stage, index) => {
            const state = stageStates.states[stage.id];
            
            return (
              <div key={stage.id} className="flex items-start gap-4 p-4 rounded-lg border bg-card">
                <div className="flex-shrink-0 mt-1">
                  {getStageIcon(stage, state)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-sm">{stage.name}</h4>
                      {getStageStatusBadge(state)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {state.duration ? formatDuration(state.duration) : stage.estimatedDuration}
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">{stage.description}</p>
                  
                  {state.status === 'in_progress' && (
                    <div className="space-y-2">
                      <Progress value={state.progress} className="h-1" />
                      {state.message && (
                        <p className="text-xs text-blue-600">{state.message}</p>
                      )}
                    </div>
                  )}
                  
                  {state.status === 'completed' && state.details && (
                    <div className="text-xs text-green-600 space-y-1">
                      {stage.id === 'validation' && state.details.domain && (
                        <p>✓ Domain identified: {state.details.domain}</p>
                      )}
                      {stage.id === 'literature_qc' && (
                        <p>✓ Classification: {state.details.classification} 
                           {state.details.similar_papers_count > 0 && 
                             ` (${state.details.similar_papers_count} similar papers found)`}
                        </p>
                      )}
                      {stage.id === 'plan_generation' && (
                        <div>
                          <p>✓ Plan generated with {state.details.protocol_steps} protocol steps</p>
                          <p>✓ Budget: ${state.details.total_budget} ({state.details.materials_count} materials)</p>
                          {state.details.few_shot_examples_used > 0 && (
                            <p>✓ Enhanced with {state.details.few_shot_examples_used} learning examples</p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {state.status === 'error' && state.error && (
                    <Alert variant="destructive" className="mt-2">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        {state.error}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Global Error */}
        {latestErrorEvent && !latestErrorEvent.data.stage && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {latestErrorEvent.data.message || 'An unexpected error occurred'}
            </AlertDescription>
          </Alert>
        )}

        {/* Completion Message */}
        {stageStates.overallProgress === 100 && !stageStates.hasError && (
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              Experiment plan generated successfully! You can now review and refine the plan.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}