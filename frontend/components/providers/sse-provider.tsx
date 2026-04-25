/**
 * SSE Provider Component
 * Provides SSE connection management context to the application
 */

'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { useSSE } from '@/lib/hooks/use-sse';
import { SSEEvent, UseSSEResult } from '@/lib/types';

interface SSEContextType extends UseSSEResult {
  // Additional context methods can be added here
}

const SSEContext = createContext<SSEContextType | undefined>(undefined);

interface SSEProviderProps {
  children: ReactNode;
}

export function SSEProvider({ children }: SSEProviderProps) {
  const sseHook = useSSE();

  const contextValue: SSEContextType = {
    ...sseHook,
  };

  return (
    <SSEContext.Provider value={contextValue}>
      {children}
    </SSEContext.Provider>
  );
}

export function useSSEContext(): SSEContextType {
  const context = useContext(SSEContext);
  
  if (context === undefined) {
    throw new Error('useSSEContext must be used within an SSEProvider');
  }
  
  return context;
}

// Export hook for convenience
export { useSSE };