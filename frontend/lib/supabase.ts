/**
 * Supabase client configuration for frontend
 * Uses @supabase/ssr for proper session management
 */

import { createBrowserClient } from '@supabase/ssr';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

/**
 * Create a Supabase browser client.
 * Call this inside components — do not use as a module-level singleton
 * because it needs to read cookies on each render.
 */
export function createSupabaseClient() {
  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}

// Convenience re-export for components that import from this file
export { createBrowserClient };
