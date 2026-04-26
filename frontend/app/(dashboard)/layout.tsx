'use client';

/**
 * Dashboard Layout
 */

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { FlaskConical, Plus, LogOut } from 'lucide-react';
import { createBrowserClient } from '@supabase/ssr';
import { useEffect, useState, useMemo } from 'react';

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
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <Link className="flex items-center space-x-2" href="/">
            <FlaskConical className="h-6 w-6" />
            <span className="font-bold">AI Scientist Platform</span>
          </Link>

          <nav className="flex items-center space-x-6 text-sm font-medium ml-6">
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

          <div className="ml-auto flex items-center space-x-4">
            {userEmail && (
              <span className="text-sm text-muted-foreground hidden sm:block">
                {userEmail}
              </span>
            )}
            <Link href="/new-plan">
              <Button size="sm">
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

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}
