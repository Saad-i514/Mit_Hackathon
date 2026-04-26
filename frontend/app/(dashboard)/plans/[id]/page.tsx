'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft, Loader2, AlertCircle, FlaskConical,
  BookOpen, DollarSign, Clock, CheckCircle2, Shield,
  ExternalLink, Copy, Check, ChevronDown, ChevronUp,
  Star, AlertTriangle, Microscope
} from 'lucide-react';
import { getApiUrl, API_ENDPOINTS } from '@/lib/config';
import { ExperimentPlan, NoveltyClassification } from '@/lib/types';
import { useToast } from '@/components/ui/use-toast';

type Tab = 'protocol' | 'materials' | 'timeline' | 'validation';

export default function PlanDetailPage() {
  const supabase = useMemo(() => createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  ), []);
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const planId = params?.id as string;

  const [plan, setPlan] = useState<ExperimentPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('protocol');
  const [copiedStep, setCopiedStep] = useState<number | null>(null);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  useEffect(() => {
    if (!planId) return;
    (async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) { router.push('/login'); return; }

        const res = await fetch(getApiUrl(API_ENDPOINTS.getPlan(planId)), {
          headers: { Authorization: `Bearer ${session.access_token}` }
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        setPlan(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load plan');
      } finally {
        setLoading(false);
      }
    })();
  }, [planId, supabase, router]);

  const copyStep = async (text: string, stepNum: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedStep(stepNum);
    toast({ title: 'Copied!', description: 'Step copied to clipboard' });
    setTimeout(() => setCopiedStep(null), 2000);
  };

  const noveltyBadge = (c: NoveltyClassification) => {
    if (c === NoveltyClassification.NOT_FOUND)    return { label: 'Novel', color: 'bg-green-100 text-green-700 border-green-200' };
    if (c === NoveltyClassification.SIMILAR_EXISTS) return { label: 'Similar Exists', color: 'bg-amber-100 text-amber-700 border-amber-200' };
    return { label: 'Exact Match', color: 'bg-red-100 text-red-700 border-red-200' };
  };

  const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'protocol',   label: 'Protocol',   icon: FlaskConical },
    { id: 'materials',  label: 'Materials',  icon: DollarSign },
    { id: 'timeline',   label: 'Timeline',   icon: Clock },
    { id: 'validation', label: 'Validation', icon: CheckCircle2 },
  ];

  if (loading) return (
    <div className="min-h-screen gradient-bg flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-10 w-10 text-blue-600 animate-spin mx-auto mb-3" />
        <p className="text-muted-foreground">Loading experiment plan...</p>
      </div>
    </div>
  );

  if (error || !plan) return (
    <div className="min-h-screen gradient-bg flex items-center justify-center p-4">
      <div className="bg-background/60 backdrop-blur-md rounded-2xl border border-red-200 p-8 max-w-md w-full text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">Plan Not Found</h2>
        <p className="text-muted-foreground mb-6">{error || 'This plan does not exist or you do not have access.'}</p>
        <Button onClick={() => router.push('/plans')} variant="outline">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Plans
        </Button>
      </div>
    </div>
  );

  const nb = noveltyBadge(plan.novelty_classification);

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-8 max-w-5xl">

        {/* Back button */}
        <Button variant="ghost" size="sm" onClick={() => router.push('/plans')} className="mb-6 text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Plans
        </Button>

        {/* Plan header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-background/60 backdrop-blur-md rounded-2xl border border-white/10 shadow-sm p-6 mb-6"
        >
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-blue-600 flex items-center justify-center flex-shrink-0">
                <Microscope className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">{plan.domain}</h1>
                <p className="text-sm text-muted-foreground">Experiment Plan</p>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">
              <Badge className={`border ${nb.color}`}>{nb.label}</Badge>
              {plan.metadata.few_shot_examples_used > 0 && (
                <Badge className="bg-purple-100 text-purple-700 border-purple-200 border">
                  <Star className="h-3 w-3 mr-1" />
                  {plan.metadata.few_shot_examples_used} examples used
                </Badge>
              )}
            </div>
          </div>

          <div className="bg-card/50 rounded-xl p-4 mb-4">
            <p className="text-sm text-foreground/80 leading-relaxed italic">"{plan.hypothesis}"</p>
          </div>

          {/* Expert review flags */}
          {plan.metadata.requires_expert_review.length > 0 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
              <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <div>
                <span className="font-medium">Expert review recommended: </span>
                {plan.metadata.requires_expert_review.join(' · ')}
              </div>
            </div>
          )}

          {/* Quick stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
            {[
              { icon: FlaskConical, label: 'Protocol Steps', value: plan.protocol.steps.length },
              { icon: DollarSign,   label: 'Total Budget',   value: `$${plan.materials.total_budget.toLocaleString()}` },
              { icon: Clock,        label: 'Duration',       value: `${plan.timeline.total_duration_days}d` },
              { icon: CheckCircle2, label: 'Success Criteria', value: plan.validation_criteria.success_criteria.length },
            ].map(s => (
              <div key={s.label} className="bg-card/50 rounded-xl p-3 text-center">
                <s.icon className="h-4 w-4 text-blue-600 mx-auto mb-1" />
                <div className="text-lg font-bold text-foreground">{s.value}</div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-1 bg-background/60 backdrop-blur-md rounded-xl border border-white/10 p-1 mb-4 shadow-sm overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-shrink-0 ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-muted-foreground hover:text-foreground hover:bg-card/50'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >

          {/* ── Protocol Tab ── */}
          {activeTab === 'protocol' && (
            <div className="space-y-3">
              {plan.protocol.safety_considerations.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2 font-medium text-amber-800">
                    <Shield className="h-4 w-4" /> Safety Considerations
                  </div>
                  <ul className="space-y-1">
                    {plan.protocol.safety_considerations.map((s, i) => (
                      <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                        <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {plan.protocol.steps.map((step, i) => (
                <div key={i} className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm overflow-hidden">
                  <div
                    className="flex items-center gap-3 p-4 cursor-pointer hover:bg-card/50 transition-colors"
                    onClick={() => setExpandedStep(expandedStep === i ? null : i)}
                  >
                    <div className="h-8 w-8 rounded-lg bg-blue-600 text-white text-sm font-bold flex items-center justify-center flex-shrink-0">
                      {step.step_number}
                    </div>
                    <p className="flex-1 text-sm font-medium text-foreground line-clamp-2">{step.description}</p>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge variant="outline" className="text-xs">{step.duration}</Badge>
                      <button
                        onClick={e => { e.stopPropagation(); copyStep(step.description, i); }}
                        className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground/80 hover:text-muted-foreground transition-colors"
                      >
                        {copiedStep === i ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                      {expandedStep === i ? <ChevronUp className="h-4 w-4 text-muted-foreground/80" /> : <ChevronDown className="h-4 w-4 text-muted-foreground/80" />}
                    </div>
                  </div>

                  {expandedStep === i && (
                    <div className="border-t border-white/10 p-4 bg-card/50 space-y-3">
                      {Object.keys(step.critical_parameters).length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Critical Parameters</p>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(step.critical_parameters).map(([k, v]) => (
                              <span key={k} className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium border border-blue-100">
                                {k}: {v}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {step.source && (
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Source</p>
                          <div className="flex items-center gap-2 text-xs text-blue-600">
                            <BookOpen className="h-3.5 w-3.5" />
                            <span>{step.source.title}</span>
                            {step.source.url && (
                              <a href={step.source.url} target="_blank" rel="noopener noreferrer" className="hover:underline flex items-center gap-1">
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {plan.protocol.troubleshooting.length > 0 && (
                <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-4">
                  <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-orange-500" /> Troubleshooting
                  </h3>
                  <div className="space-y-3">
                    {plan.protocol.troubleshooting.map((t, i) => (
                      <div key={i} className="grid grid-cols-2 gap-3 text-sm">
                        <div className="bg-red-50 rounded-lg p-3 border border-red-100">
                          <p className="text-xs font-semibold text-red-600 mb-1">Issue</p>
                          <p className="text-red-800">{t.issue}</p>
                        </div>
                        <div className="bg-green-50 rounded-lg p-3 border border-green-100">
                          <p className="text-xs font-semibold text-green-600 mb-1">Solution</p>
                          <p className="text-green-800">{t.solution}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Materials Tab ── */}
          {activeTab === 'materials' && (
            <div className="space-y-4">
              <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-card/50 border-b border-white/10">
                        <th className="text-left p-3 font-semibold text-foreground/80">Material</th>
                        <th className="text-left p-3 font-semibold text-foreground/80">Catalog #</th>
                        <th className="text-left p-3 font-semibold text-foreground/80">Supplier</th>
                        <th className="text-right p-3 font-semibold text-foreground/80">Qty</th>
                        <th className="text-right p-3 font-semibold text-foreground/80">Unit Price</th>
                        <th className="text-right p-3 font-semibold text-foreground/80">Total</th>
                        <th className="text-center p-3 font-semibold text-foreground/80">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {plan.materials.items.map((item, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-card/50 transition-colors">
                          <td className="p-3 font-medium text-foreground">{item.name}</td>
                          <td className="p-3 font-mono text-xs text-muted-foreground">{item.catalog_number}</td>
                          <td className="p-3 text-muted-foreground">
                            {item.product_url ? (
                              <a href={item.product_url} target="_blank" rel="noopener noreferrer"
                                className="text-blue-600 hover:underline flex items-center gap-1">
                                {item.supplier} <ExternalLink className="h-3 w-3" />
                              </a>
                            ) : item.supplier}
                          </td>
                          <td className="p-3 text-right text-foreground/80">{item.quantity} {item.unit}</td>
                          <td className="p-3 text-right text-foreground/80">${item.unit_price.toFixed(2)}</td>
                          <td className="p-3 text-right font-medium text-foreground">${item.total_price.toFixed(2)}</td>
                          <td className="p-3 text-center">
                            <Badge className={`text-xs border ${
                              item.verification_status === 'verified'
                                ? 'bg-green-100 text-green-700 border-green-200'
                                : 'bg-amber-100 text-amber-700 border-amber-200'
                            }`}>
                              {item.verification_status === 'verified' ? '✓ Verified' : '⚠ Pending'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-blue-50 border-t-2 border-blue-200">
                        <td colSpan={5} className="p-3 font-bold text-foreground text-right">Total Budget</td>
                        <td className="p-3 text-right font-bold text-blue-700 text-lg">
                          ${plan.materials.total_budget.toLocaleString()} {plan.materials.currency}
                        </td>
                        <td />
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── Timeline Tab ── */}
          {activeTab === 'timeline' && (
            <div className="space-y-3">
              <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-4 mb-4">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-foreground">Total Duration</span>
                  <Badge className="bg-blue-100 text-blue-700 border-blue-200 border text-sm px-3 py-1">
                    {plan.timeline.total_duration_days} days
                  </Badge>
                </div>
              </div>

              <div className="relative">
                {plan.timeline.phases.map((phase, i) => (
                  <div key={i} className="flex gap-4 mb-4">
                    <div className="flex flex-col items-center">
                      <div className="h-10 w-10 rounded-full bg-blue-600 text-white text-sm font-bold flex items-center justify-center flex-shrink-0 z-10">
                        {phase.phase_number}
                      </div>
                      {i < plan.timeline.phases.length - 1 && (
                        <div className="w-0.5 flex-1 bg-gradient-to-b from-blue-400 to-blue-200 mt-1 min-h-[24px]" />
                      )}
                    </div>
                    <div className="flex-1 bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-4 mb-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold text-foreground">{phase.name}</h3>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />{phase.duration_days}d
                          </Badge>
                          {phase.start_date && (
                            <span className="text-xs text-muted-foreground">{phase.start_date}</span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground">{phase.description}</p>
                      {phase.dependencies.length > 0 && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                          <span>Depends on:</span>
                          {phase.dependencies.map(d => (
                            <Badge key={d} variant="outline" className="text-xs">Phase {d}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Validation Tab ── */}
          {activeTab === 'validation' && (
            <div className="space-y-4">
              <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-5">
                <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" /> Success Criteria
                </h3>
                <div className="space-y-3">
                  {plan.validation_criteria.success_criteria.map((c, i) => (
                    <div key={i} className="bg-green-50 border border-green-100 rounded-xl p-4">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm text-foreground/90 font-medium">{c.description}</p>
                        <Badge className="bg-green-100 text-green-700 border-green-200 border text-xs flex-shrink-0">
                          {c.threshold}
                        </Badge>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                        <span>Method: {c.measurement_technique}</span>
                        {c.expected_range && <span>Expected: {c.expected_range}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-5">
                <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-500" /> Failure Criteria
                </h3>
                <div className="space-y-3">
                  {plan.validation_criteria.failure_criteria.map((c, i) => (
                    <div key={i} className="bg-red-50 border border-red-100 rounded-xl p-4">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm text-foreground/90 font-medium">{c.description}</p>
                        <Badge className="bg-red-100 text-red-700 border-red-200 border text-xs flex-shrink-0">
                          {c.threshold}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Method: {c.measurement_technique}</p>
                    </div>
                  ))}
                </div>
              </div>

              {plan.validation_criteria.validation_methods.length > 0 && (
                <div className="bg-background/60 backdrop-blur-md rounded-xl border border-white/10 shadow-sm p-5">
                  <h3 className="font-semibold text-foreground mb-3">Statistical Methods</h3>
                  <div className="flex flex-wrap gap-2">
                    {plan.validation_criteria.validation_methods.map((m, i) => (
                      <Badge key={i} variant="outline" className="text-sm">{m}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
