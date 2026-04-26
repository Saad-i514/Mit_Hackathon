'use client';

/**
 * Dashboard Layout
 */

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { FlaskConical, Plus, LogOut } from 'lucide-react';
import { createBrowserClient } from '@supabase/ssr';
import { useEffect, useState, useMemo } from 'react';
import { ThemeToggle } from '@/components/theme-toggle';
import { WelcomePopup } from '@/components/welcome-popup';
import { AnimatePresence, motion } from 'framer-motion';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = useMemo(() => createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  ), []);
  const router = useRouter();
  const pathname = usePathname();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        router.push('/login');
      } else {
        setUserEmail(session.user.email ?? null);
      }
    });
  }, [supabase, router]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  return (
    <div className="flex min-h-screen flex-col relative z-0">
      <WelcomePopup />
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-background/40 backdrop-blur-xl supports-[backdrop-filter]:bg-background/40 shadow-sm">
        <div className="container flex h-14 items-center">
          <Link className="flex items-center space-x-2" href="/">
            <FlaskConical className="h-6 w-6 text-primary" />
            <span className="font-bold hidden sm:inline-block">AI Scientist Platform</span>
          </Link>

          <nav className="flex items-center space-x-4 sm:space-x-6 text-sm font-medium ml-4 sm:ml-6">
            <Link
              href="/new-plan"
              className="transition-colors hover:text-foreground/80 text-foreground"
            >
              New Plan
            </Link>
            <Link
              href="/plans"
              className="transition-colors hover:text-foreground/80 text-foreground/60"
            >
              My Plans
            </Link>
          </nav>

          <div className="ml-auto flex items-center space-x-2 sm:space-x-4">
            {userEmail && (
              <span className="text-sm text-muted-foreground hidden md:block">
                {userEmail}
              </span>
            )}
            <ThemeToggle />
            <Link href="/new-plan">
              <Button size="sm" className="hidden sm:flex">
                <Plus className="h-4 w-4 mr-2" />
                New Plan
              </Button>
            </Link>
            <Button variant="ghost" size="sm" onClick={handleSignOut} title="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content with Page Transitions */}
      <main className="flex-1 relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
