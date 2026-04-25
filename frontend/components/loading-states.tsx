/**
 * Loading States and Skeleton Components
 * Provides consistent loading experiences across the application
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Loader2, FlaskConical } from 'lucide-react';

// Generic loading spinner
export function LoadingSpinner({ size = 'default', className = '' }: { 
  size?: 'sm' | 'default' | 'lg'; 
  className?: string;
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  return (
    <Loader2 className={`animate-spin ${sizeClasses[size]} ${className}`} />
  );
}

// Full page loading
export function PageLoading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <FlaskConical className="h-12 w-12 mx-auto text-blue-600 animate-pulse" />
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">{message}</h2>
          <LoadingSpinner size="lg" />
        </div>
      </div>
    </div>
  );
}

// Card loading skeleton
export function CardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
        </div>
      </CardContent>
    </Card>
  );
}

// Plan list loading skeleton
export function PlanListSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <Skeleton className="h-5 w-3/4" />
                <div className="flex items-center space-x-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Skeleton className="h-8 w-20" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Plan viewer loading skeleton
export function PlanViewerSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-8 w-1/2" />
              <div className="flex space-x-2">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-20" />
              </div>
            </div>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <div className="space-y-4">
        <div className="flex space-x-4 border-b">
          {['Protocol', 'Materials', 'Timeline', 'Validation'].map((tab) => (
            <Skeleton key={tab} className="h-8 w-20" />
          ))}
        </div>

        {/* Tab content */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-4 w-2/3" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-5 w-1/4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Materials table loading skeleton
export function MaterialsTableSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-1/4" />
        <Skeleton className="h-8 w-32" />
      </div>
      
      <div className="border rounded-lg">
        {/* Table header */}
        <div className="grid grid-cols-6 gap-4 p-4 border-b bg-gray-50">
          {['Material', 'Catalog #', 'Supplier', 'Quantity', 'Price', 'Total'].map((header) => (
            <Skeleton key={header} className="h-4 w-full" />
          ))}
        </div>
        
        {/* Table rows */}
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-6 gap-4 p-4 border-b">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ))}
        
        {/* Total row */}
        <div className="grid grid-cols-6 gap-4 p-4 bg-gray-50 font-semibold">
          <div className="col-span-4"></div>
          <Skeleton className="h-5 w-16" />
          <Skeleton className="h-5 w-20" />
        </div>
      </div>
    </div>
  );
}

// Timeline loading skeleton
export function TimelineSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-4 w-1/4" />
      </div>
      
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-start space-x-4">
          <div className="flex flex-col items-center">
            <Skeleton className="h-8 w-8 rounded-full" />
            {i < 4 && <Skeleton className="h-12 w-0.5 mt-2" />}
          </div>
          
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-4 w-20" />
            </div>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
            
            {/* Dependencies */}
            <div className="flex space-x-2 mt-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-20" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Progress loading with shimmer effect
export function ProgressSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Skeleton className="h-5 w-5 rounded-full" />
          <Skeleton className="h-6 w-1/2" />
        </div>
        <Skeleton className="h-4 w-3/4" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall progress */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-8" />
            </div>
            <Skeleton className="h-2 w-full rounded-full" />
          </div>
          
          {/* Stage progress */}
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-start space-x-4 p-4 border rounded-lg">
              <Skeleton className="h-5 w-5 rounded-full mt-1" />
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-1 w-full rounded-full" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Button loading state
export function ButtonLoading({ 
  children, 
  isLoading, 
  ...props 
}: { 
  children: React.ReactNode; 
  isLoading: boolean; 
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button {...props} disabled={isLoading || props.disabled}>
      {isLoading ? (
        <div className="flex items-center space-x-2">
          <LoadingSpinner size="sm" />
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </button>
  );
}

// Input loading state
export function InputSkeleton() {
  return <Skeleton className="h-10 w-full" />;
}

// Text loading skeleton
export function TextSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i} 
          className={`h-4 ${i === lines - 1 ? 'w-3/4' : 'w-full'}`} 
        />
      ))}
    </div>
  );
}

// Avatar loading skeleton
export function AvatarSkeleton() {
  return <Skeleton className="h-10 w-10 rounded-full" />;
}

// Badge loading skeleton
export function BadgeSkeleton() {
  return <Skeleton className="h-5 w-16 rounded-full" />;
}