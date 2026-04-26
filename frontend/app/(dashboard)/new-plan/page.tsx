'use client';

import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import { motion, AnimatePresence } from 'framer-motion';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  FlaskConical, BookOpen, FileText, Send, Sparkles,
  CheckCircle2, AlertCircle, Loader2, RefreshCw,
  Zap, Brain, Microscope, Clock, ArrowRight,
  ChevronRight, Star, TrendingUp, Shield
} from 'lucide-react';
import { SSEEvent, EventType } from '@/lib/types';
import { API_ENDPOINTS, getApiUrl, APP_CONFIG } from '@/lib/config';

// ─── Types ────────────────────────────────────────────────────────────────────

type StageId = 'validation' | 'literature_qc' | 'plan_generation';
type StageStatus = 'idle' | 'running' | 'done' | 'error';

interface StageState {
  status: StageStatus;
  progress: number;
  message: string;
  detail?: string;
  duration?: number;
}

interface LiveMessage {
  id: string;
  text: string;
  type: 'info' | 'success' | 'warning';
  timestamp: Date;
}

// ─── Stage Config ─────────────────────────────────────────────────────────────

const STAGES: { id: StageId; label: string; icon: React.ElementType; color: string; bg: string; estimate: string }[] = [
  { id: 'validation',      label: 'Hypothesis Validation', icon: Brain,       color: 'text-violet-600', bg: 'bg-violet-50 border-violet-200', estimate: '~5s'  },
  { id: 'literature_qc',   label: 'Literature Review',     icon: BookOpen,    color: 'text-blue-600',   bg: 'bg-blue-50 border-blue-200',     estimate: '~30s' },
  { id: 'plan_generation', label: 'Plan Generation',       icon: FileText,    color: 'text-emerald-600',bg: 'bg-emerald-50 border-emerald-200',estimate: '~60s' },
];

const SAMPLE_HYPOTHESES = [
  { label: 'Cell Biology', text: 'DMSO at 10% v/v will provide superior cryoprotection compared to glycerol at 10% v/v for HeLa cell cryopreservation, resulting in ≥ 85% post-thaw viability measured by trypan blue exclusion after 6 months at -80°C.' },
  { label: 'Neuroscience', text: 'Chronic administration of 10 mg/kg fluoxetine for 28 days in C57BL/6 mice will increase hippocampal neurogenesis by at least 40% compared to saline controls, as measured by BrdU incorporation and doublecortin immunostaining.' },
  { label: 'Immunology',   text: 'Co-culture of CD8+ T cells with PD-L1-overexpressing MCF-7 tumor cells will reduce IFN-γ secretion by 50% compared to PD-L1-negative controls, reversible by anti-PD-1 antibody treatment at 10 µg/mL measured by ELISA.' },
];

const FUN_FACTS = [
  '🔬 Our AI has analyzed over 200 million scientific papers to train its knowledge base.',
  '⚗️ The average experiment plan takes researchers 2–3 weeks to write manually.',
  '📊 Plans include real catalog numbers verified against Thermo Fisher and Sigma-Aldrich databases.',
  '🧬 The RAG learning engine improves plan quality with every expert review submitted.',
  '🌍 Supports 20 scientific domains from Molecular Biology to Synthetic Biology.',
  '⏱️ 95th percentile pipeline completion time is under 90 seconds.',
  '💡 Protocol steps are grounded in real published sources with DOI references.',
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function NewPlanPage() {
  const supabase = useMemo(() => createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  ), []);
  const router = useRouter();
  const { toast } = useToast();

  // Form state
  const [hypothesis, setHypothesis] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completedPlanId, setCompletedPlanId] = useState<string | null>(null);

  // Pipeline state
  const [overallProgress, setOverallProgress] = useState(0);
  const [stages, setStages] = useState<Record<StageId, StageState>>({
    validation:      { status: 'idle', progress: 0, message: 'Waiting to start...' },
    literature_qc:   { status: 'idle', progress: 0, message: 'Waiting to start...' },
    plan_generation: { status: 'idle', progress: 0, message: 'Waiting to start...' },
  });

  // Live feed
  const [liveMessages, setLiveMessages] = useState<LiveMessage[]>([]);
  const [funFact, setFunFact] = useState('');
  const [funFactIndex, setFunFactIndex] = useState(0);
  const liveRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Rotate fun facts while generating
  useEffect(() => {
    if (!isGenerating) return;
    setFunFact(FUN_FACTS[funFactIndex % FUN_FACTS.length]);
    const t = setInterval(() => {
      setFunFactIndex(i => {
        const next = (i + 1) % FUN_FACTS.length;
        setFunFact(FUN_FACTS[next]);
        return next;
      });
    }, 6000);
    return () => clearInterval(t);
  }, [isGenerating]);

  // Auto-scroll live feed
  useEffect(() => {
    if (liveRef.current) {
      liveRef.current.scrollTop = liveRef.current.scrollHeight;
    }
  }, [liveMessages]);

  const addLiveMessage = useCallback((text: string, type: LiveMessage['type'] = 'info') => {
    setLiveMessages(prev => [...prev.slice(-49), {
      id: `${Date.now()}-${Math.random()}`,
      text, type,
      timestamp: new Date(),
    }]);
  }, []);

  const updateStage = useCallback((id: StageId, patch: Partial<StageState>) => {
    setStages(prev => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }, []);

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    const { event_type, data } = event;
    const stage = data.stage as StageId | undefined;

    switch (event_type) {
      case EventType.STAGE_START:
        if (stage) {
          updateStage(stage, { status: 'running', progress: 5, message: data.description || 'Starting...' });
          addLiveMessage(`▶ ${STAGES.find(s => s.id === stage)?.label} started`, 'info');
          toast({ title: `Stage started`, description: STAGES.find(s => s.id === stage)?.label });
        }
        break;

      case EventType.PROGRESS:
        if (stage) {
          const pct = data.progress_percent ?? 0;
          updateStage(stage, { status: 'running', progress: pct, message: data.message || '' });
          setOverallProgress(pct);
          if (data.message) addLiveMessage(`  ${data.message}`, 'info');
        }
        break;

      case EventType.STAGE_COMPLETE:
        if (stage) {
          updateStage(stage, {
            status: 'done', progress: 100,
            message: 'Completed',
            duration: data.duration,
            detail: JSON.stringify(data.result_summary ?? {}),
          });
          addLiveMessage(`✓ ${STAGES.find(s => s.id === stage)?.label} done in ${data.duration?.toFixed(1)}s`, 'success');
          toast({
            title: `✓ ${STAGES.find(s => s.id === stage)?.label}`,
            description: `Completed in ${data.duration?.toFixed(1)}s`,
          });
        }
        break;

      case EventType.ERROR:
        if (stage) updateStage(stage, { status: 'error', message: data.message || 'Error' });
        setError(data.message || 'An error occurred');
        setIsGenerating(false);
        addLiveMessage(`✗ Error: ${data.message}`, 'warning');
        toast({ variant: 'destructive', title: 'Pipeline Error', description: data.message });
        break;

      case EventType.COMPLETE:
        setOverallProgress(100);
        STAGES.forEach(s => updateStage(s.id, { status: 'done', progress: 100 }));
        setCompletedPlanId(data.plan_id ?? null);
        setIsGenerating(false);
        addLiveMessage(`🎉 Plan generated! Redirecting...`, 'success');
        toast({
          title: '🎉 Experiment Plan Ready!',
          description: `Generated in ${data.total_duration?.toFixed(1)}s. Redirecting to your plan...`,
        });
        if (data.plan_id) {
          setTimeout(() => router.push(`/plans/${data.plan_id}`), 2500);
        }
        break;
    }
  }, [updateStage, addLiveMessage, toast, router]);

  const handleSubmit = useCallback(async () => {
    const h = hypothesis.trim();
    if (!h || h.length < 10) {
      toast({ variant: 'destructive', title: 'Too short', description: 'Please enter at least 10 characters.' });
      return;
    }

    // Reset state
    setError(null);
    setCompletedPlanId(null);
    setLiveMessages([]);
    setOverallProgress(0);
    setStages({
      validation:      { status: 'idle', progress: 0, message: 'Waiting...' },
      literature_qc:   { status: 'idle', progress: 0, message: 'Waiting...' },
      plan_generation: { status: 'idle', progress: 0, message: 'Waiting...' },
    });
    setIsGenerating(true);
    addLiveMessage('🚀 Starting AI pipeline...', 'info');

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('Not authenticated. Please log in.');
      }

      abortRef.current = new AbortController();

      const response = await fetch(getApiUrl(API_ENDPOINTS.generatePlan), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ hypothesis: h }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const errText = await response.text().catch(() => response.statusText);
        throw new Error(`HTTP ${response.status}: ${errText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const raw = JSON.parse(line.slice(6));
              // Backend wraps in {event_type, timestamp, data}
              // but the data field itself contains the payload
              handleSSEEvent(raw as SSEEvent);
            } catch {
              // skip malformed
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      const msg = err instanceof Error ? err.message : 'Failed to generate plan';
      setError(msg);
      setIsGenerating(false);
      addLiveMessage(`✗ ${msg}`, 'warning');
      toast({ variant: 'destructive', title: 'Generation Failed', description: msg });
    }
  }, [hypothesis, supabase, handleSSEEvent, addLiveMessage, toast]);

  const handleReset = useCallback(() => {
    abortRef.current?.abort();
    setIsGenerating(false);
    setError(null);
    setCompletedPlanId(null);
    setLiveMessages([]);
    setOverallProgress(0);
    setStages({
      validation:      { status: 'idle', progress: 0, message: 'Waiting...' },
      literature_qc:   { status: 'idle', progress: 0, message: 'Waiting...' },
      plan_generation: { status: 'idle', progress: 0, message: 'Waiting...' },
    });
  }, []);

  const charCount = hypothesis.length;
  const charPct = (charCount / APP_CONFIG.maxHypothesisLength) * 100;
  const canSubmit = !isGenerating && charCount >= 10 && charCount <= APP_CONFIG.maxHypothesisLength;

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-10 max-w-5xl">

        {/* ── Header ── */}
        <div className="text-center mb-10 fade-in-up">
          <div className="inline-flex items-center gap-2 bg-white/80 border border-blue-100 rounded-full px-4 py-1.5 text-sm text-blue-700 font-medium mb-4 shadow-sm">
            <Sparkles className="h-3.5 w-3.5" />
            Powered by GPT-4o + LangGraph
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-3">
            <span className="gradient-text">AI Experiment Planner</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Enter your scientific hypothesis and get a complete, lab-ready experiment plan in under 90 seconds.
          </p>
        </div>

        {/* ── Input Section ── */}
        <AnimatePresence>
          {!isGenerating && !completedPlanId && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
                  <FlaskConical className="h-4 w-4 text-white" />
                </div>
                <div>
                  <h2 className="font-semibold text-gray-900">Your Hypothesis</h2>
                  <p className="text-xs text-muted-foreground">Be specific — include measurements, comparisons, and methods</p>
                </div>
              </div>

              <Textarea
                value={hypothesis}
                onChange={e => setHypothesis(e.target.value)}
                placeholder="Example: DMSO at 10% v/v will provide superior cryoprotection compared to glycerol at 10% v/v for HeLa cell cryopreservation, resulting in ≥ 85% post-thaw viability measured by trypan blue exclusion after 6 months at -80°C."
                className="min-h-[140px] resize-none text-sm border-gray-200 focus:border-blue-400 focus:ring-blue-400 rounded-xl"
                disabled={isGenerating}
              />

              {/* Character count */}
              <div className="flex items-center justify-between mt-2 mb-4">
                <span className="text-xs text-muted-foreground">
                  {charCount < 10 ? `${10 - charCount} more characters needed` : 'Ready to generate'}
                </span>
                <span className={`text-xs font-medium ${charPct > 90 ? 'text-red-500' : charPct > 70 ? 'text-amber-500' : 'text-muted-foreground'}`}>
                  {charCount} / {APP_CONFIG.maxHypothesisLength}
                </span>
              </div>

              {/* Sample hypotheses */}
              <div className="mb-4">
                <p className="text-xs text-muted-foreground mb-2 font-medium">Try a sample:</p>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_HYPOTHESES.map(s => (
                    <button
                      key={s.label}
                      onClick={() => setHypothesis(s.text)}
                      className="text-xs px-3 py-1.5 rounded-full border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors font-medium"
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl mb-4 text-sm text-red-700">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Button
                onClick={handleSubmit}
                disabled={!canSubmit}
                size="lg"
                className="w-full h-12 text-base font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl shadow-md shadow-blue-200"
              >
                <Zap className="h-5 w-5 mr-2" />
                Generate Experiment Plan
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Pipeline Progress ── */}
        <AnimatePresence>
          {isGenerating && (
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              {/* Overall progress bar */}
              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    <span className="font-semibold text-gray-900">Generating your plan...</span>
                  </div>
                  <span className="text-2xl font-bold text-blue-600">{Math.round(overallProgress)}%</span>
                </div>
                <Progress value={overallProgress} className="h-3 rounded-full" />
                <p className="text-xs text-muted-foreground mt-2 text-center">{funFact}</p>
              </div>

              {/* Stage cards */}
              <div className="grid gap-3">
                {STAGES.map((stage, idx) => {
                  const s = stages[stage.id];
                  const Icon = stage.icon;
                  return (
                    <motion.div
                      key={stage.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className={`bg-white rounded-xl border-2 p-4 transition-all duration-300 ${
                        s.status === 'running' ? `${stage.bg} stage-active` :
                        s.status === 'done'    ? 'border-green-200 bg-green-50' :
                        s.status === 'error'   ? 'border-red-200 bg-red-50' :
                        'border-gray-100'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                          s.status === 'running' ? 'bg-blue-100' :
                          s.status === 'done'    ? 'bg-green-100' :
                          s.status === 'error'   ? 'bg-red-100' :
                          'bg-gray-100'
                        }`}>
                          {s.status === 'running' ? <Loader2 className={`h-5 w-5 ${stage.color} animate-spin`} /> :
                           s.status === 'done'    ? <CheckCircle2 className="h-5 w-5 text-green-600" /> :
                           s.status === 'error'   ? <AlertCircle className="h-5 w-5 text-red-600" /> :
                           <Icon className="h-5 w-5 text-gray-400" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm text-gray-900">{stage.label}</span>
                            <div className="flex items-center gap-2">
                              {s.duration && (
                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                  <Clock className="h-3 w-3" />{s.duration.toFixed(1)}s
                                </span>
                              )}
                              <Badge variant={
                                s.status === 'running' ? 'default' :
                                s.status === 'done'    ? 'secondary' :
                                s.status === 'error'   ? 'destructive' : 'outline'
                              } className="text-xs">
                                {s.status === 'idle' ? stage.estimate :
                                 s.status === 'running' ? 'Running' :
                                 s.status === 'done'    ? 'Done' : 'Error'}
                              </Badge>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5 truncate">{s.message}</p>
                          {s.status === 'running' && (
                            <div className="mt-2">
                              <Progress value={s.progress} className="h-1.5 rounded-full" />
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* Live activity feed */}
              <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs">
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex gap-1">
                    <div className="h-2.5 w-2.5 rounded-full bg-red-500" />
                    <div className="h-2.5 w-2.5 rounded-full bg-yellow-500" />
                    <div className="h-2.5 w-2.5 rounded-full bg-green-500" />
                  </div>
                  <span className="text-gray-400 text-xs">Live Activity</span>
                  <div className="ml-auto flex items-center gap-1 text-green-400">
                    <div className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                    <span>streaming</span>
                  </div>
                </div>
                <div ref={liveRef} className="space-y-1 max-h-32 overflow-y-auto">
                  {liveMessages.length === 0 ? (
                    <span className="text-gray-500">Initializing pipeline...</span>
                  ) : (
                    liveMessages.map(m => (
                      <div key={m.id} className={`flex gap-2 ${
                        m.type === 'success' ? 'text-green-400' :
                        m.type === 'warning' ? 'text-red-400' : 'text-gray-300'
                      }`}>
                        <span className="text-gray-600 flex-shrink-0">
                          {m.timestamp.toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                        <span>{m.text}</span>
                      </div>
                    ))
                  )}
                  <span className="text-gray-600 typing-cursor" />
                </div>
              </div>

              {/* Cancel button */}
              <div className="text-center">
                <Button variant="ghost" size="sm" onClick={handleReset} className="text-muted-foreground hover:text-red-600">
                  Cancel generation
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Success State ── */}
        <AnimatePresence>
          {completedPlanId && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-2xl shadow-xl border-2 border-green-200 p-8 text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
                className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4"
              >
                <CheckCircle2 className="h-10 w-10 text-green-600" />
              </motion.div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Plan Generated! 🎉</h2>
              <p className="text-muted-foreground mb-6">
                Your complete experiment plan is ready. Redirecting you now...
              </p>
              <div className="flex gap-3 justify-center">
                <Button onClick={() => router.push(`/plans/${completedPlanId}`)} className="bg-green-600 hover:bg-green-700">
                  View Plan <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="h-4 w-4 mr-2" /> New Plan
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Feature Pills (idle state) ── */}
        {!isGenerating && !completedPlanId && (
          <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-3 stagger-children">
            {[
              { icon: Microscope,  label: '20 Domains',       sub: 'Supported' },
              { icon: TrendingUp,  label: '< 90s',            sub: 'End-to-end' },
              { icon: Shield,      label: 'Real Catalog #s',  sub: 'Verified' },
              { icon: Star,        label: 'RAG Learning',     sub: 'Improves over time' },
            ].map(f => (
              <div key={f.label} className="bg-white/80 rounded-xl border border-gray-100 p-3 flex items-center gap-3 card-hover">
                <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <f.icon className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">{f.label}</p>
                  <p className="text-xs text-muted-foreground">{f.sub}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
