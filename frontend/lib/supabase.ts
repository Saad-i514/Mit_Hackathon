/**
 * Supabase client configuration for frontend authentication
 */

import { createClientComponentClient, createServerComponentClient } from '@supabase/auth-helpers-nextjs';
import { createClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';
import { config } from './config';

// Client-side Supabase client for use in components
export const createSupabaseClient = () => {
  return createClientComponentClient({
    supabaseUrl: config.supabaseUrl,
    supabaseKey: config.supabaseAnonKey,
  });
};

// Server-side Supabase client for use in server components and API routes
export const createSupabaseServerClient = () => {
  const cookieStore = cookies();
  return createServerComponentClient({
    cookies: () => cookieStore,
    supabaseUrl: config.supabaseUrl,
    supabaseKey: config.supabaseAnonKey,
  });
};

// Direct client for use when auth helpers are not needed
export const supabase = createClient(
  config.supabaseUrl,
  config.supabaseAnonKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  }
);

// Database types (to be extended as needed)
export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          email: string;
          name?: string;
          avatar_url?: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          email: string;
          name?: string;
          avatar_url?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          name?: string;
          avatar_url?: string;
          updated_at?: string;
        };
      };
      hypotheses: {
        Row: {
          id: string;
          user_id: string;
          hypothesis_text: string;
          domain: string;
          status: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          hypothesis_text: string;
          domain: string;
          status?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          hypothesis_text?: string;
          domain?: string;
          status?: string;
          updated_at?: string;
        };
      };
      experiment_plans: {
        Row: {
          id: string;
          hypothesis_id: string;
          user_id: string;
          plan_data: any; // JSONB
          status: string;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          hypothesis_id: string;
          user_id: string;
          plan_data: any;
          status?: string;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          hypothesis_id?: string;
          user_id?: string;
          plan_data?: any;
          status?: string;
          updated_at?: string;
        };
      };
      reviews: {
        Row: {
          id: string;
          plan_id: string;
          user_id: string;
          protocol_rating: number;
          materials_rating: number;
          timeline_rating: number;
          validation_rating: number;
          overall_rating: number;
          protocol_corrections?: string;
          materials_corrections?: string;
          timeline_corrections?: string;
          validation_corrections?: string;
          created_at: string;
        };
        Insert: {
          id?: string;
          plan_id: string;
          user_id: string;
          protocol_rating: number;
          materials_rating: number;
          timeline_rating: number;
          validation_rating: number;
          overall_rating?: number;
          protocol_corrections?: string;
          materials_corrections?: string;
          timeline_corrections?: string;
          validation_corrections?: string;
          created_at?: string;
        };
        Update: {
          id?: string;
          plan_id?: string;
          user_id?: string;
          protocol_rating?: number;
          materials_rating?: number;
          timeline_rating?: number;
          validation_rating?: number;
          overall_rating?: number;
          protocol_corrections?: string;
          materials_corrections?: string;
          timeline_corrections?: string;
          validation_corrections?: string;
        };
      };
      feedback_embeddings: {
        Row: {
          id: string;
          review_id: string;
          section: string;
          original_content: string;
          corrected_content: string;
          embedding: number[]; // vector(1536)
          domain: string;
          rating: number;
          created_at: string;
        };
        Insert: {
          id?: string;
          review_id: string;
          section: string;
          original_content: string;
          corrected_content: string;
          embedding: number[];
          domain: string;
          rating: number;
          created_at?: string;
        };
        Update: {
          id?: string;
          review_id?: string;
          section?: string;
          original_content?: string;
          corrected_content?: string;
          embedding?: number[];
          domain?: string;
          rating?: number;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      match_feedback_embeddings: {
        Args: {
          query_embedding: number[];
          domain_filter?: string;
          similarity_threshold?: number;
          match_count?: number;
        };
        Returns: {
          id: string;
          section: string;
          original_content: string;
          corrected_content: string;
          domain: string;
          rating: number;
          similarity: number;
        }[];
      };
      get_average_plan_rating: {
        Args: {
          plan_id_param: string;
        };
        Returns: number;
      };
    };
    Enums: {
      [_ in never]: never;
    };
  };
}