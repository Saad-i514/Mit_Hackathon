'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createBrowserClient } from '@supabase/ssr';
import {
  FlaskConical, Eye, EyeOff, ArrowRight, CheckCircle2,
  Zap, Shield, BookOpen, BarChart3, Microscope, Dna,
} from 'lucide-react';

// ─── Advanced Particle System ─────────────────────────────────────────────────
function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    let raf: number;
    let mouse = { x: -9999, y: -9999 };

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const onMouse = (e: MouseEvent) => { mouse = { x: e.clientX, y: e.clientY }; };
    window.addEventListener('mousemove', onMouse);

    const nodes: { x: number; y: number; vx: number; vy: number; r: number; hue: number; pulse: number }[] = [];
    for (let i = 0; i < 130; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.5,
        hue: Math.random() > 0.6 ? 220 : 260,
        pulse: Math.random() * Math.PI * 2,
      });
    }

    let t = 0;
    const draw = () => {
      t += 0.008;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 110) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(99,179,237,${(1 - d / 110) * 0.15})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // DNA helix (full screen)
      const cx = canvas.width * 0.5;
      for (let i = 0; i < 24; i++) {
        const angle = (i / 24) * Math.PI * 4 + t;
        const y = (i / 24) * canvas.height;
        const x1 = cx + Math.cos(angle) * (canvas.width * 0.42);
        const x2 = cx - Math.cos(angle) * (canvas.width * 0.42);
        const alpha = 0.03 + Math.abs(Math.cos(angle)) * 0.04;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(139,92,246,${alpha})`;
        ctx.lineWidth = 1;
        ctx.moveTo(x1, y); ctx.lineTo(x2, y);
        ctx.stroke();
        if (i % 4 === 0) {
          [x1, x2].forEach(x => {
            ctx.beginPath();
            ctx.arc(x, y, 2.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(99,179,237,${alpha * 2.5})`;
            ctx.fill();
          });
        }
      }

      // Particles with mouse repulsion
      nodes.forEach((p) => {
        const mdx = p.x - mouse.x, mdy = p.y - mouse.y;
        const md = Math.hypot(mdx, mdy);
        if (md < 90) { p.vx += (mdx / md) * 0.1; p.vy += (mdy / md) * 0.1; }
        p.vx *= 0.99; p.vy *= 0.99;
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        p.pulse += 0.02;
        const alpha = 0.25 + Math.sin(p.pulse) * 0.12;
        const grd = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3.5);
        grd.addColorStop(0, `hsla(${p.hue},80%,70%,${alpha})`);
        grd.addColorStop(1, `hsla(${p.hue},80%,70%,0)`);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 3.5, 0, Math.PI * 2);
        ctx.fillStyle = grd;
        ctx.fill();
      });

      raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouse);
    };
  }, []);

  return <canvas ref={canvasRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />;
}

// ─── Typing Effect ────────────────────────────────────────────────────────────
const PHRASES = [
  'a complete protocol in 90 seconds.',
  'real catalog numbers, not placeholders.',
  'a Gantt chart with actual dates.',
  'safety assessments built in.',
  'something you can run on Monday.',
];

function TypingText() {
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [displayed, setDisplayed] = useState('');
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const target = PHRASES[phraseIdx];
    let timeout: ReturnType<typeof setTimeout>;
    if (!deleting && displayed.length < target.length) {
      timeout = setTimeout(() => setDisplayed(target.slice(0, displayed.length + 1)), 45);
    } else if (!deleting && displayed.length === target.length) {
      timeout = setTimeout(() => setDeleting(true), 2200);
    } else if (deleting && displayed.length > 0) {
      timeout = setTimeout(() => setDisplayed(displayed.slice(0, -1)), 22);
    } else {
      setDeleting(false);
      setPhraseIdx((i) => (i + 1) % PHRASES.length);
    }
    return () => clearTimeout(timeout);
  }, [displayed, deleting, phraseIdx]);

  return (
    <span style={{ color: '#60a5fa' }}>
      {displayed}
      <span style={{ animation: 'blink 1s step-end infinite', color: '#818cf8' }}>|</span>
    </span>
  );
}

// ─── Feature Pills ────────────────────────────────────────────────────────────
const FEATURES = [
  { icon: Zap,        label: '< 90s generation',     color: '#fbbf24' },
  { icon: BookOpen,   label: 'Literature QC',         color: '#34d399' },
  { icon: BarChart3,  label: 'Power analysis',        color: '#60a5fa' },
  { icon: Shield,     label: 'Safety assessment',     color: '#f87171' },
  { icon: Microscope, label: '20 scientific domains', color: '#a78bfa' },
  { icon: Dna,        label: 'RAG learning engine',   color: '#fb923c' },
];

// ─── Custom Input ─────────────────────────────────────────────────────────────
function Field({ label, type, value, onChange, placeholder }: {
  label: string; type: string; value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; placeholder: string;
}) {
  const [focused, setFocused] = useState(false);
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{
        display: 'block', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
        textTransform: 'uppercase', color: '#64748b', marginBottom: 6,
      }}>{label}</label>
      <div style={{
        display: 'flex', alignItems: 'center',
        background: focused ? 'rgba(59,130,246,0.07)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${focused ? 'rgba(99,179,237,0.45)' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: 11, transition: 'all 0.2s',
        boxShadow: focused ? '0 0 0 3px rgba(59,130,246,0.1)' : 'none',
      }}>
        <input
          type={isPassword && !show ? 'password' : 'text'}
          value={value} onChange={onChange} placeholder={placeholder} required
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{
            flex: 1, padding: '12px 14px', background: 'transparent',
            border: 'none', outline: 'none', color: '#e2e8f0', fontSize: 14,
          }}
        />
        {isPassword && (
          <button type="button" onClick={() => setShow(!show)}
            style={{ padding: '0 14px', background: 'none', border: 'none', cursor: 'pointer', color: '#475569' }}>
            {show ? <EyeOff size={15} /> : <Eye size={15} />}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function LoginPage() {
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      if (session) { router.push('/new-plan'); router.refresh(); }
    });
    return () => subscription.unsubscribe();
  }, [supabase, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(''); setSuccess('');
    try {
      if (mode === 'signin') {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setSuccess('Account created! Check your email to confirm.');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #020817 0%, #0a0f1e 50%, #050b14 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      padding: '24px 16px', position: 'relative',
    }}>
      <ParticleField />

      {/* Ambient glows */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 1 }}>
        <div style={{
          position: 'absolute', top: '15%', left: '20%', width: 500, height: 500,
          borderRadius: '50%', filter: 'blur(80px)',
          background: 'radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%)',
        }} />
        <div style={{
          position: 'absolute', bottom: '15%', right: '20%', width: 400, height: 400,
          borderRadius: '50%', filter: 'blur(80px)',
          background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
        }} />
      </div>

      {/* Centered container */}
      <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: 900 }}>

        {/* Top: headline + hook */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          {/* Badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '5px 14px', borderRadius: 100, marginBottom: 20,
            background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)',
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#22d3ee', boxShadow: '0 0 8px #22d3ee' }} />
            <span style={{ fontSize: 11, color: '#93c5fd', fontWeight: 600, letterSpacing: '0.06em' }}>
              PRODUCTION-GRADE AI RESEARCH TOOL
            </span>
          </div>

          <h1 style={{
            fontSize: 'clamp(32px, 5vw, 52px)', fontWeight: 900, lineHeight: 1.1,
            letterSpacing: '-1.5px', marginBottom: 16,
          }}>
            <span style={{
              background: 'linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>From hypothesis to </span>
            <span style={{
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>protocol</span>
            <span style={{
              background: 'linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}> in 90 seconds.</span>
          </h1>

          {/* Hook */}
          <div style={{
            display: 'inline-block', padding: '10px 20px', borderRadius: 12, marginBottom: 8,
            background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(99,179,237,0.12)',
            backdropFilter: 'blur(10px)',
          }}>
            <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.7, margin: 0 }}>
              <span style={{ color: '#f87171', fontWeight: 600 }}>Most AI science tools</span> give you a wall of text and call it a protocol.{' '}
              <span style={{ color: '#34d399', fontWeight: 600 }}>We give you</span> <TypingText />
            </p>
          </div>
        </div>

        {/* Middle: features + form side by side */}
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>

          {/* Feature grid — left */}
          <div style={{ flex: '1 1 300px', minWidth: 280 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
              {FEATURES.map(({ icon: Icon, label, color }) => (
                <div key={label} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '11px 14px', borderRadius: 11,
                  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: 8, flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: `${color}18`,
                  }}>
                    <Icon size={14} color={color} />
                  </div>
                  <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>{label}</span>
                </div>
              ))}
            </div>

            {/* What you get checklist */}
            <div style={{
              padding: '16px 18px', borderRadius: 12,
              background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)',
            }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: '#475569', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 12 }}>
                What you get
              </p>
              {[
                'Complete protocol with real catalog numbers',
                'Literature novelty assessment via 6 databases',
                'Safety assessment + BSL classification',
                'Gantt timeline + power analysis',
              ].map((item) => (
                <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 8 }}>
                  <CheckCircle2 size={13} color="#22d3ee" style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: '#475569' }}>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Auth form — right */}
          <div style={{
            flex: '1 1 340px', minWidth: 320,
            background: 'rgba(8,14,28,0.92)',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(99,179,237,0.12)',
            borderRadius: 20, padding: '32px 32px',
            boxShadow: '0 30px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.04)',
          }}>
            {/* Logo */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
              <div style={{
                width: 42, height: 42, borderRadius: 11,
                background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 0 20px rgba(59,130,246,0.35)',
              }}>
                <FlaskConical size={20} color="white" />
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.3px' }}>AI Scientist</div>
                <div style={{ fontSize: 11, color: '#475569' }}>Platform</div>
              </div>
            </div>

            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', marginBottom: 4, letterSpacing: '-0.4px' }}>
              {mode === 'signin' ? 'Welcome back' : 'Create account'}
            </h2>
            <p style={{ fontSize: 13, color: '#475569', marginBottom: 24 }}>
              {mode === 'signin' ? 'Sign in to access your experiment plans' : 'Start generating lab-ready protocols today'}
            </p>

            {/* Toggle */}
            <div style={{
              display: 'flex', background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.07)', borderRadius: 11, padding: 4, marginBottom: 24,
            }}>
              {(['signin', 'signup'] as const).map((m) => (
                <button key={m} onClick={() => { setMode(m); setError(''); setSuccess(''); }}
                  style={{
                    flex: 1, padding: '9px 0', borderRadius: 8, border: 'none',
                    cursor: 'pointer', fontSize: 13, fontWeight: 700, transition: 'all 0.25s',
                    background: mode === m ? 'linear-gradient(135deg, #3b82f6, #6366f1)' : 'transparent',
                    color: mode === m ? 'white' : '#475569',
                    boxShadow: mode === m ? '0 4px 14px rgba(59,130,246,0.35)' : 'none',
                  }}>
                  {m === 'signin' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit}>
              <Field label="Email Address" type="email" value={email}
                onChange={(e) => setEmail(e.target.value)} placeholder="you@institution.edu" />
              <Field label="Password" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 characters" />

              {(error || success) && (
                <div style={{
                  display: 'flex', alignItems: 'flex-start', gap: 9,
                  padding: '11px 13px', borderRadius: 10, marginBottom: 16,
                  background: success ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
                  border: `1px solid ${success ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'}`,
                }}>
                  <CheckCircle2 size={14} color={success ? '#34d399' : '#f87171'} style={{ marginTop: 1, flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: success ? '#6ee7b7' : '#fca5a5', lineHeight: 1.5 }}>
                    {success || error}
                  </span>
                </div>
              )}

              <button type="submit" disabled={loading} style={{
                width: '100%', padding: '13px', borderRadius: 11, border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 700,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                background: loading ? 'rgba(59,130,246,0.3)' : 'linear-gradient(135deg, #3b82f6, #6366f1)',
                color: 'white',
                boxShadow: loading ? 'none' : '0 4px 20px rgba(59,130,246,0.4)',
                transition: 'all 0.2s', marginBottom: 14,
              }}>
                {loading ? (
                  <>
                    <div style={{
                      width: 15, height: 15, borderRadius: '50%',
                      border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white',
                      animation: 'spin 0.7s linear infinite',
                    }} />
                    Processing...
                  </>
                ) : (
                  <>{mode === 'signin' ? 'Sign In' : 'Create Account'} <ArrowRight size={15} /></>
                )}
              </button>

              {mode === 'signin' && (
                <p style={{ textAlign: 'center', fontSize: 12 }}>
                  <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', fontSize: 12 }}>
                    Forgot your password?
                  </button>
                </p>
              )}
            </form>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes spin  { to{transform:rotate(360deg)} }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        input::placeholder { color: #334155; }
      `}</style>
    </div>
  );
}
