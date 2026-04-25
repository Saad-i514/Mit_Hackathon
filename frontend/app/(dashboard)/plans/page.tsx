'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FlaskConical, Plus, Clock, DollarSign, ChevronRight,
  Loader2, AlertCircle, RefreshCw, FileText, Sparkles
} from 'lucide-react';
import { getApiUrl, API_ENDPOINTS } from '@/lib/config';

interface PlanSummary {
  id: string;
  status: string;
  domain?: string;
  total_budget?: number;
  created_at: string;
}

export default function PlansPage() {
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  const router = useRouter();
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const fetchPlans = useCallback(async (off = 0) => {
    setLoading(true);
    setError(null);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { router.push('/login'); return; }

      const url = `${getApiUrl(API_ENDPOINTS.listPlans)}?limit=${limit}&offset=${off}`;
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPlans(data.items ?? []);
      setTotal(data.total ?? 0);
      setOffset(off);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load plans');
    } finally {
      setLoading(false);
    }
  }, [supabase, router]);

  useEffect(() => { fetchPlans(0); }, [fetchPlans]);

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return iso; }
  };

  const statusColor = (s: string) => {
    if (s === 'generated' || s === 'completed') return 'bg-green-100 text-green-700 border-green-200';
    if (s === 'draft') return 'bg-gray-100 text-gray-600 border-gray-200';
    return 'bg-blue-100 text-blue-700 border-blue-200';
  };

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-4 py-10 max-w-4xl">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Plans</h1>
            <p className="text-muted-foreground mt-1">
              {total > 0 ? `${total} experiment plan${total !== 1 ? 's' : ''}` : 'No plans yet'}
            </p>
          </div>
          <Button
            onClick={() => router.push('/new-plan')}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" /> New Plan
          </Button>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3 text-red-700">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <Button variant="ghost" size="sm" onClick={() => fetchPlans(offset)}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && plans.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20"
          >
            <div className="h-20 w-20 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
              <FlaskConical className="h-10 w-10 text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No plans yet</h2>
            <p className="text-muted-foreground mb-6">Generate your first experiment plan to get started.</p>
            <Button onClick={() => router.push('/new-plan')} className="bg-blue-600 hover:bg-blue-700">
              <Sparkles className="h-4 w-4 mr-2" /> Generate First Plan
            </Button>
          </motion.div>
        )}

        {/* Plans list */}
        {!loading && !error && plans.length > 0 && (
          <AnimatePresence>
            <div className="space-y-3">
              {plans.map((plan, i) => (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => router.push(`/plans/${plan.id}`)}
                  className="bg-white rounded-xl border border-gray-100 p-5 flex items-center gap-4 cursor-pointer hover:border-blue-200 hover:shadow-md transition-all card-hover"
                >
                  <div className="h-11 w-11 rounded-xl bg-blue-50 flex items-center justify-center flex-shrink-0">
                    <FileText className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900 truncate">
                        {plan.domain || 'Experiment Plan'}
                      </span>
                      <Badge className={`text-xs border ${statusColor(plan.status)}`}>
                        {plan.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(plan.created_at)}
                      </span>
                      {plan.total_budget && (
                        <span className="flex items-center gap-1">
                          <DollarSign className="h-3 w-3" />
                          ${plan.total_budget.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}

        {/* Pagination */}
        {total > limit && (
          <div className="flex items-center justify-center gap-3 mt-8">
            <Button
              variant="outline" size="sm"
              disabled={offset === 0 || loading}
              onClick={() => fetchPlans(Math.max(0, offset - limit))}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              {offset + 1}–{Math.min(offset + limit, total)} of {total}
            </span>
            <Button
              variant="outline" size="sm"
              disabled={offset + limit >= total || loading}
              onClick={() => fetchPlans(offset + limit)}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
