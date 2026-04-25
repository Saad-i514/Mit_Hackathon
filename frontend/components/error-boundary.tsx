/**
 * Error Boundary Component
 * Catches JavaScript errors in component tree and displays fallback UI
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Log to external service in production
    if (process.env.NODE_ENV === 'production') {
      this.logErrorToService(error, errorInfo);
    }
  }

  private logErrorToService(error: Error, errorInfo: ErrorInfo) {
    // In a real application, you would send this to your error tracking service
    // like Sentry, LogRocket, or Bugsnag
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Example: Send to error tracking service
    // errorTrackingService.captureException(errorData);
    
    console.error('Error logged:', errorData);
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: '',
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-6 w-6" />
                Something went wrong
              </CardTitle>
              <CardDescription>
                An unexpected error occurred. We apologize for the inconvenience.
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <Alert variant="destructive">
                <Bug className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <p className="font-medium">Error ID: {this.state.errorId}</p>
                    {this.state.error && (
                      <p className="text-sm">{this.state.error.message}</p>
                    )}
                  </div>
                </AlertDescription>
              </Alert>

              {/* Error details for development */}
              {this.props.showDetails && process.env.NODE_ENV === 'development' && this.state.error && (
                <Card className="bg-gray-100">
                  <CardHeader>
                    <CardTitle className="text-sm">Error Details (Development)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-xs font-mono">
                      <div>
                        <strong>Message:</strong>
                        <pre className="mt-1 whitespace-pre-wrap">{this.state.error.message}</pre>
                      </div>
                      
                      {this.state.error.stack && (
                        <div>
                          <strong>Stack Trace:</strong>
                          <pre className="mt-1 whitespace-pre-wrap overflow-x-auto">
                            {this.state.error.stack}
                          </pre>
                        </div>
                      )}
                      
                      {this.state.errorInfo?.componentStack && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre className="mt-1 whitespace-pre-wrap overflow-x-auto">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button onClick={this.handleRetry} className="flex-1">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
                
                <Button variant="outline" onClick={this.handleReload} className="flex-1">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reload Page
                </Button>
                
                <Button variant="outline" onClick={this.handleGoHome} className="flex-1">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Button>
              </div>

              {/* Help text */}
              <div className="text-sm text-gray-600 space-y-2">
                <p>
                  If this problem persists, please try the following:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Clear your browser cache and cookies</li>
                  <li>Disable browser extensions</li>
                  <li>Try using an incognito/private browsing window</li>
                  <li>Contact support with the Error ID above</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook version for functional components
export function useErrorHandler() {
  return (error: Error, errorInfo?: ErrorInfo) => {
    console.error('Error caught by useErrorHandler:', error, errorInfo);
    
    // In production, log to error tracking service
    if (process.env.NODE_ENV === 'production') {
      // Log error to external service
      const errorData = {
        message: error.message,
        stack: error.stack,
        errorInfo,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };
      
      console.error('Error logged:', errorData);
    }
  };
}

// Wrapper component for easier usage
interface ErrorBoundaryWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
  showDetails?: boolean;
}

export function ErrorBoundaryWrapper({ 
  children, 
  fallback, 
  showDetails = false 
}: ErrorBoundaryWrapperProps) {
  return (
    <ErrorBoundary fallback={fallback} showDetails={showDetails}>
      {children}
    </ErrorBoundary>
  );
}

// Specific error boundaries for different parts of the app
export function PipelineErrorBoundary({ children }: { children: ReactNode }) {
  const fallback = (
    <Alert variant="destructive" className="m-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <div className="space-y-2">
          <p className="font-medium">Pipeline Error</p>
          <p>There was an error with the experiment planning pipeline. Please try refreshing the page.</p>
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh Page
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );

  return (
    <ErrorBoundary fallback={fallback} showDetails={true}>
      {children}
    </ErrorBoundary>
  );
}

export function PlanViewerErrorBoundary({ children }: { children: ReactNode }) {
  const fallback = (
    <Card className="m-4">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-red-600">
          <AlertTriangle className="h-5 w-5" />
          Unable to Display Plan
        </CardTitle>
        <CardDescription>
          There was an error loading the experiment plan. The data might be corrupted or incomplete.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant="outline" onClick={() => window.history.back()}>
          Go Back
        </Button>
      </CardContent>
    </Card>
  );

  return (
    <ErrorBoundary fallback={fallback}>
      {children}
    </ErrorBoundary>
  );
}