/**
 * Server-Sent Events (SSE) hook for real-time communication
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { SSEEvent, EventType, UseSSEResult } from '../types';
import { APP_CONFIG, getSSEUrl } from '../config';

export function useSSE(): UseSSEResult {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setIsConnected(false);
    setError(null);
    reconnectAttemptsRef.current = 0;
  }, []);

  const connect = useCallback((url: string, onMessage: (event: SSEEvent) => void) => {
    // Disconnect any existing connection
    disconnect();

    try {
      const fullUrl = url.startsWith('http') ? url : getSSEUrl(url);
      const eventSource = new EventSource(fullUrl);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        console.log('SSE connection established');
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (parseError) {
          console.error('Failed to parse SSE message:', parseError);
          setError('Failed to parse server message');
        }
      };

      // Handle specific event types
      eventSource.addEventListener(EventType.PROGRESS, (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (parseError) {
          console.error('Failed to parse progress event:', parseError);
        }
      });

      eventSource.addEventListener(EventType.ERROR, (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
          setError(data.data?.message || 'Server error occurred');
        } catch (parseError) {
          console.error('Failed to parse error event:', parseError);
        }
      });

      eventSource.addEventListener(EventType.COMPLETE, (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
          // Don't disconnect immediately, let the component handle it
        } catch (parseError) {
          console.error('Failed to parse complete event:', parseError);
        }
      });

      eventSource.addEventListener(EventType.STAGE_START, (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (parseError) {
          console.error('Failed to parse stage start event:', parseError);
        }
      });

      eventSource.addEventListener(EventType.STAGE_COMPLETE, (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (parseError) {
          console.error('Failed to parse stage complete event:', parseError);
        }
      });

      eventSource.onerror = (event) => {
        console.error('SSE connection error:', event);
        setIsConnected(false);
        
        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < APP_CONFIG.sseReconnectAttempts) {
          const delay = APP_CONFIG.sseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          reconnectAttemptsRef.current += 1;
          
          setError(`Connection lost. Reconnecting in ${delay / 1000}s... (${reconnectAttemptsRef.current}/${APP_CONFIG.sseReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting SSE reconnection ${reconnectAttemptsRef.current}/${APP_CONFIG.sseReconnectAttempts}`);
            connect(url, onMessage);
          }, delay);
        } else {
          setError('Connection failed after multiple attempts. Please refresh the page.');
          disconnect();
        }
      };

    } catch (connectionError) {
      console.error('Failed to establish SSE connection:', connectionError);
      setError('Failed to establish connection');
    }
  }, [disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected,
    error,
  };
}