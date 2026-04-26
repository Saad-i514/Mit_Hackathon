/**
 * Environment configuration for the AI Scientist Platform frontend
 */

import { Config } from './types';

// Validate required environment variables
const requiredEnvVars = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
};

// Check for missing environment variables
const missingVars = Object.entries(requiredEnvVars)
  .filter(([_, value]) => !value)
  .map(([key, _]) => key);

if (missingVars.length > 0) {
  throw new Error(
    `Missing required environment variables: ${missingVars.join(', ')}\n` +
    'Please check your .env.local file and ensure all required variables are set.'
  );
}

// Export configuration object
export const config: Config = {
  apiUrl: requiredEnvVars.NEXT_PUBLIC_API_URL!,
  supabaseUrl: requiredEnvVars.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseAnonKey: requiredEnvVars.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
};

// API endpoints
export const API_ENDPOINTS = {
  // Health
  health: '/health',
  
  // Plans
  generatePlan: '/api/v1/plans/generate',
  getPlan: (id: string) => `/api/v1/plans/${id}`,
  listPlans: '/api/v1/plans',
  submitReview: (id: string) => `/api/v1/plans/${id}/reviews`,
  
  // Advanced features
  getVersions: (id: string) => `/api/v1/plans/${id}/versions`,
  restoreVersion: (id: string, versionNumber: number) => `/api/v1/plans/${id}/restore/${versionNumber}`,
  generateGrantMethods: (id: string) => `/api/v1/plans/${id}/grant-methods`,
  generateNotebook: (id: string) => `/api/v1/plans/${id}/notebook`,
  updateEquipment: (name: string) => `/api/v1/plans/equipment/${encodeURIComponent(name)}`,
} as const;

// SSE endpoints
export const SSE_ENDPOINTS = {
  planGeneration: '/api/v1/plans/generate',
} as const;

// Application constants
export const APP_CONFIG = {
  // Hypothesis input
  maxHypothesisLength: 5000,
  
  // Pagination
  defaultPageSize: 20,
  maxPageSize: 100,
  
  // SSE
  sseReconnectAttempts: 5,
  sseReconnectDelay: 1000, // ms
  
  // Timeouts
  apiTimeout: 30000, // 30 seconds
  sseTimeout: 300000, // 5 minutes
  
  // Rating
  minRating: 1,
  maxRating: 5,
  
  // File uploads (future use)
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedFileTypes: ['pdf', 'doc', 'docx', 'txt'],
} as const;

// Feature flags
export const FEATURES = {
  enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
  enableDebugMode: process.env.NODE_ENV === 'development',
  enableExperimentalFeatures: process.env.NEXT_PUBLIC_ENABLE_EXPERIMENTAL === 'true',
} as const;

// Theme configuration
export const THEME_CONFIG = {
  defaultTheme: 'light',
  storageKey: 'ai-scientist-theme',
} as const;

// Validation rules
export const VALIDATION_RULES = {
  hypothesis: {
    minLength: 10,
    maxLength: APP_CONFIG.maxHypothesisLength,
    required: true,
  },
  email: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    required: true,
  },
  password: {
    minLength: 8,
    required: true,
  },
  rating: {
    min: APP_CONFIG.minRating,
    max: APP_CONFIG.maxRating,
    required: true,
  },
} as const;

// Error messages
export const ERROR_MESSAGES = {
  // Network errors
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  TIMEOUT_ERROR: 'Request timed out. Please try again.',
  
  // Authentication errors
  UNAUTHORIZED: 'Please log in to continue.',
  FORBIDDEN: 'You do not have permission to access this resource.',
  
  // Validation errors
  INVALID_HYPOTHESIS: 'Please enter a valid hypothesis.',
  HYPOTHESIS_TOO_LONG: `Hypothesis must be less than ${APP_CONFIG.maxHypothesisLength} characters.`,
  HYPOTHESIS_TOO_SHORT: `Hypothesis must be at least ${VALIDATION_RULES.hypothesis.minLength} characters.`,
  
  // Plan generation errors
  GENERATION_FAILED: 'Plan generation failed. Please try again.',
  PLAN_NOT_FOUND: 'Experiment plan not found.',
  
  // Review errors
  REVIEW_SUBMISSION_FAILED: 'Failed to submit review. Please try again.',
  INVALID_RATING: `Rating must be between ${APP_CONFIG.minRating} and ${APP_CONFIG.maxRating}.`,
  
  // Generic errors
  UNKNOWN_ERROR: 'An unexpected error occurred. Please try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  PLAN_GENERATED: 'Experiment plan generated successfully!',
  REVIEW_SUBMITTED: 'Review submitted successfully!',
  LOGIN_SUCCESS: 'Logged in successfully!',
  LOGOUT_SUCCESS: 'Logged out successfully!',
  SIGNUP_SUCCESS: 'Account created successfully!',
} as const;

// Development helpers
export const isDevelopment = process.env.NODE_ENV === 'development';
export const isProduction = process.env.NODE_ENV === 'production';
export const isTest = process.env.NODE_ENV === 'test';

// Logging configuration
export const LOG_CONFIG = {
  level: isDevelopment ? 'debug' : 'info',
  enableConsole: isDevelopment,
  enableRemote: isProduction,
} as const;

// Export utility functions
export function getApiUrl(endpoint: string): string {
  return `${config.apiUrl}${endpoint}`;
}

export function getSSEUrl(endpoint: string): string {
  return `${config.apiUrl}${endpoint}`;
}

export function validateConfig(): boolean {
  try {
    // Check if all required config values are present
    const configValues = Object.values(config);
    return configValues.every(value => value && value.length > 0);
  } catch (error) {
    console.error('Configuration validation failed:', error);
    return false;
  }
}

// Initialize configuration validation
if (typeof window !== 'undefined' && !validateConfig()) {
  console.error('Invalid configuration detected. Please check your environment variables.');
}