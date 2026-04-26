/**
 * API Client with JWT Authentication
 * Handles all API requests with automatic token management
 */

import { createSupabaseClient } from './supabase';
import { 
  config, 
  getApiUrl, 
  APP_CONFIG, 
  ERROR_MESSAGES,
  API_ENDPOINTS 
} from './config';
import { 
  APIError, 
  ExperimentPlan, 
  PaginatedResponse, 
  PlanSummary, 
  ReviewSubmission, 
  ReviewResult,
  GeneratePlanRequest 
} from './types';

class APIClient {
  private supabase = createSupabaseClient();

  /**
   * Get the current JWT token from Supabase
   */
  private async getAuthToken(): Promise<string | null> {
    try {
      const { data: { session } } = await this.supabase.auth.getSession();
      return session?.access_token || null;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    // Add authorization header if token is available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(getApiUrl(endpoint), {
      ...options,
      headers,
      signal: AbortSignal.timeout(APP_CONFIG.apiTimeout),
    });

    // Handle different response types
    if (!response.ok) {
      await this.handleErrorResponse(response);
    }

    // Handle empty responses
    if (response.status === 204) {
      return {} as T;
    }

    // Parse JSON response
    try {
      return await response.json();
    } catch (error) {
      throw new Error('Invalid JSON response from server');
    }
  }

  /**
   * Handle error responses and throw appropriate errors
   */
  private async handleErrorResponse(response: Response): Promise<never> {
    let errorData: APIError;

    try {
      errorData = await response.json();
    } catch {
      // Fallback for non-JSON error responses
      errorData = {
        error_code: 'UNKNOWN_ERROR',
        message: response.statusText || ERROR_MESSAGES.UNKNOWN_ERROR,
        timestamp: new Date().toISOString(),
      };
    }

    // Handle specific HTTP status codes
    switch (response.status) {
      case 401:
        // Redirect to login on authentication failure
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error(ERROR_MESSAGES.UNAUTHORIZED);
      
      case 403:
        throw new Error(ERROR_MESSAGES.FORBIDDEN);
      
      case 404:
        throw new Error(errorData.message || 'Resource not found');
      
      case 429:
        throw new Error('Rate limit exceeded. Please try again later.');
      
      case 500:
      case 502:
      case 503:
      case 504:
        throw new Error(ERROR_MESSAGES.SERVER_ERROR);
      
      default:
        throw new Error(errorData.message || ERROR_MESSAGES.UNKNOWN_ERROR);
    }
  }

  /**
   * Health check
   */
  async checkHealth(): Promise<{ status: string; dependencies: Record<string, any> }> {
    return this.request(API_ENDPOINTS.health);
  }

  /**
   * Generate experiment plan (returns SSE URL for streaming)
   */
  async generatePlan(request: GeneratePlanRequest): Promise<{ sseUrl: string }> {
    // For plan generation, we return the SSE URL instead of making the request here
    // The actual request is made by the SSE connection
    const token = await this.getAuthToken();
    const sseUrl = getApiUrl(API_ENDPOINTS.generatePlan);
    
    return { sseUrl };
  }

  /**
   * Start plan generation (for SSE streaming)
   */
  async startPlanGeneration(request: GeneratePlanRequest): Promise<Response> {
    const token = await this.getAuthToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(getApiUrl(API_ENDPOINTS.generatePlan), {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });
  }

  /**
   * Get experiment plan by ID
   */
  async getPlan(planId: string): Promise<ExperimentPlan> {
    return this.request<ExperimentPlan>(API_ENDPOINTS.getPlan(planId));
  }

  /**
   * List user's experiment plans
   */
  async listPlans(
    status?: string,
    limit: number = APP_CONFIG.defaultPageSize,
    offset: number = 0
  ): Promise<PaginatedResponse<PlanSummary>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (status) {
      params.append('status', status);
    }

    const endpoint = `${API_ENDPOINTS.listPlans}?${params.toString()}`;
    return this.request<PaginatedResponse<PlanSummary>>(endpoint);
  }

  /**
   * Submit plan review
   */
  async submitReview(planId: string, review: ReviewSubmission): Promise<ReviewResult> {
    return this.request<ReviewResult>(API_ENDPOINTS.submitReview(planId), {
      method: 'POST',
      body: JSON.stringify(review),
    });
  }

  /**
   * Get current user session
   */
  async getCurrentUser() {
    const { data: { user }, error } = await this.supabase.auth.getUser();
    
    if (error) {
      throw new Error(error.message);
    }
    
    return user;
  }

  /**
   * Sign in with email and password
   */
  async signIn(email: string, password: string) {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw new Error(error.message);
    }

    return data;
  }

  /**
   * Sign up with email and password
   */
  async signUp(email: string, password: string, name?: string) {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          name: name || '',
        },
      },
    });

    if (error) {
      throw new Error(error.message);
    }

    return data;
  }

  /**
   * Sign out
   */
  async signOut() {
    const { error } = await this.supabase.auth.signOut();
    
    if (error) {
      throw new Error(error.message);
    }
  }

  /**
   * Sign in with OAuth provider
   */
  async signInWithOAuth(provider: 'google' | 'github') {
    const { data, error } = await this.supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (error) {
      throw new Error(error.message);
    }

    return data;
  }

  /**
   * Reset password
   */
  async resetPassword(email: string) {
    const { error } = await this.supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/reset-password`,
    });

    if (error) {
      throw new Error(error.message);
    }
  }

  /**
   * Update password
   */
  async updatePassword(password: string) {
    const { error } = await this.supabase.auth.updateUser({
      password,
    });

    if (error) {
      throw new Error(error.message);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: { name?: string; avatar_url?: string }) {
    const { error } = await this.supabase.auth.updateUser({
      data: updates,
    });

    if (error) {
      throw new Error(error.message);
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };