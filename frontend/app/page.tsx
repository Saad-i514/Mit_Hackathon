import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FlaskConical, BookOpen, FileText, Zap, ArrowRight,
  CheckCircle, Clock, DollarSign, Shield, Sparkles,
  Brain, Microscope, TrendingUp, Star, ChevronRight
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen text-white">

      {/* ── Nav ── */}
      <header className="sticky top-0 z-50 bg-[#020617]/80 backdrop-blur border-b border-white/10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between max-w-6xl">
          <Link href="/" className="flex items-center gap-2 font-bold text-white">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <FlaskConical className="h-4 w-4 text-white" />
            </div>
            AI Scientist Platform
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-sm text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#domains" className="hover:text-white transition-colors">Domains</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white">Sign In</Button>
            </Link>
            <Link href="/new-plan">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                Get Started <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">

        {/* ── Hero ── */}
        <section className="relative overflow-hidden gradient-bg py-20 md:py-32">
          <div className="container mx-auto px-4 max-w-5xl text-center relative z-10">
            <Badge className="mb-6 bg-blue-950/60 text-blue-300 border-blue-700/50 hover:bg-blue-950/60">
              <Sparkles className="h-3 w-3 mr-1" />
              Powered by GPT-4o · LangGraph · Supabase
            </Badge>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6 leading-tight">
              From Hypothesis to
              <br />
              <span className="gradient-text">Lab-Ready Plan</span>
              <br />
              <span className="text-slate-300">in 90 Seconds</span>
            </h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              AI-powered experiment planning that generates complete protocols, real materials with catalog numbers,
              budgets, timelines, and validation criteria — instantly.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/new-plan">
                <Button size="lg" className="h-14 px-8 text-base bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-900/50">
                  <Zap className="h-5 w-5 mr-2" />
                  Generate Your First Plan — Free
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </div>
            <div className="flex items-center justify-center gap-6 mt-8 text-sm text-slate-400">
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-400" /> No credit card</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-400" /> Ready in seconds</span>
              <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-green-400" /> 20 domains</span>
            </div>
          </div>
        </section>

        {/* ── Stats ── */}
        <section className="border-y border-white/10 bg-white/5 py-10">
          <div className="container mx-auto px-4 max-w-5xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {[
                { value: '200M+', label: 'Papers Analyzed' },
                { value: '< 90s',  label: 'P95 Generation Time' },
                { value: '20',     label: 'Scientific Domains' },
                { value: '100%',   label: 'Real Catalog Numbers' },
              ].map(s => (
                <div key={s.label}>
                  <div className="text-3xl font-bold text-white mb-1">{s.value}</div>
                  <div className="text-sm text-slate-400">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Features ── */}
        <section id="features" className="py-20 md:py-28">
          <div className="container mx-auto px-4 max-w-5xl">
            <div className="text-center mb-14">
              <h2 className="text-4xl font-bold text-white mb-4">Everything in One Plan</h2>
              <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                Each generated plan includes everything a PI needs to start experiments immediately.
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  icon: Brain, color: 'bg-violet-900/50 text-violet-400',
                  title: 'Hypothesis Validation',
                  desc: 'GPT-4o validates testability, extracts domain, and generates clarification questions for ambiguous hypotheses.',
                },
                {
                  icon: BookOpen, color: 'bg-blue-900/50 text-blue-400',
                  title: 'Literature QC',
                  desc: 'Concurrent search across Semantic Scholar (200M+ papers) and web sources. Novelty classified as not_found, similar_exists, or exact_match.',
                },
                {
                  icon: FileText, color: 'bg-emerald-900/50 text-emerald-400',
                  title: 'Complete Protocol',
                  desc: 'Step-by-step protocol grounded in protocols.io and peer-reviewed publications with DOI references and critical parameters.',
                },
                {
                  icon: DollarSign, color: 'bg-amber-900/50 text-amber-400',
                  title: 'Real Materials & Budget',
                  desc: 'Actual catalog numbers from Thermo Fisher and Sigma-Aldrich with 2024–2025 pricing and supplier links.',
                },
                {
                  icon: Clock, color: 'bg-pink-900/50 text-pink-400',
                  title: 'Phased Timeline',
                  desc: 'Gantt-style timeline with explicit phase dependencies, realistic durations, and material delivery windows.',
                },
                {
                  icon: Shield, color: 'bg-indigo-900/50 text-indigo-400',
                  title: 'Validation Criteria',
                  desc: 'Quantitative success and failure thresholds with statistical methods, expected ranges, and controls.',
                },
              ].map(f => (
                <div key={f.title} className="bg-white/5 rounded-2xl border border-white/10 p-6 card-hover">
                  <div className={`h-11 w-11 rounded-xl ${f.color} flex items-center justify-center mb-4`}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section id="how-it-works" className="py-20 bg-white/5">
          <div className="container mx-auto px-4 max-w-4xl">
            <div className="text-center mb-14">
              <h2 className="text-4xl font-bold text-white mb-4">Three Stages, One Plan</h2>
              <p className="text-lg text-slate-400">Watch your plan come together in real time.</p>
            </div>
            <div className="space-y-4">
              {[
                { n: '01', icon: Brain,    color: 'bg-violet-600', title: 'Hypothesis Validation (~5s)',    desc: 'GPT-4o extracts the scientific domain, testable claim, and flags any ambiguities.' },
                { n: '02', icon: BookOpen, color: 'bg-blue-600',   title: 'Literature Review (~30s)',       desc: 'Concurrent search of Semantic Scholar + Serper. Novelty classified and similar papers surfaced.' },
                { n: '03', icon: FileText, color: 'bg-emerald-600',title: 'Plan Generation (~60s)',         desc: 'GPT-4o generates the full plan using RAG few-shot examples from expert-reviewed plans.' },
              ].map((step) => (
                <div key={step.n} className="flex gap-5 bg-white/5 rounded-2xl border border-white/10 p-5">
                  <div className={`h-12 w-12 rounded-xl ${step.color} flex items-center justify-center flex-shrink-0`}>
                    <step.icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Step {step.n}</span>
                    </div>
                    <h3 className="font-semibold text-white mb-1">{step.title}</h3>
                    <p className="text-sm text-slate-400">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Domains ── */}
        <section id="domains" className="py-20">
          <div className="container mx-auto px-4 max-w-5xl">
            <div className="text-center mb-10">
              <h2 className="text-4xl font-bold text-white mb-4">20 Scientific Domains</h2>
              <p className="text-slate-400">From molecular biology to synthetic biology — we cover it all.</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                'Molecular Biology','Cell Biology','Biochemistry','Genetics','Neuroscience',
                'Immunology','Microbiology','Pharmacology','Biophysics','Structural Biology',
                'Genomics','Proteomics','Metabolomics','Ecology','Evolutionary Biology',
                'Developmental Biology','Physiology','Pathology','Bioinformatics','Synthetic Biology',
              ].map(d => (
                <span key={d} className="px-3 py-1.5 rounded-full bg-blue-950/60 text-blue-300 text-sm font-medium border border-blue-700/40">
                  {d}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="py-20 bg-gradient-to-br from-blue-700 to-indigo-800">
          <div className="container mx-auto px-4 max-w-3xl text-center">
            <h2 className="text-4xl font-bold text-white mb-4">Ready to Accelerate Your Research?</h2>
            <p className="text-blue-200 text-lg mb-8">
              Generate your first experiment plan in under 90 seconds. No setup required.
            </p>
            <Link href="/new-plan">
              <Button size="lg" variant="secondary" className="h-14 px-10 text-base font-semibold shadow-xl bg-white text-blue-700 hover:bg-blue-50">
                <Sparkles className="h-5 w-5 mr-2" />
                Start Planning Now
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 py-8">
        <div className="container mx-auto px-4 max-w-5xl flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <FlaskConical className="h-4 w-4" />
            <span>© 2025 AI Scientist Platform</span>
          </div>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
