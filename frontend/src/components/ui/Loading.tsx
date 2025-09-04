import React from 'react';
import { Loader2, Mic } from 'lucide-react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  variant?: 'default' | 'transcription' | 'upload' | 'processing';
  className?: string;
}

interface SkeletonLoaderProps {
  className?: string;
}

interface PageLoadingProps {
  message?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  text = 'Loading...',
  variant = 'default',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const renderIcon = () => {
    switch (variant) {
      case 'transcription':
        return <Mic className={`${sizeClasses[size]} animate-pulse`} />;
      case 'upload':
        return <Loader2 className={`${sizeClasses[size]} animate-spin`} />;
      case 'processing':
        return (
          <div className="relative">
            <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-500`} />
            <div className="absolute inset-0 animate-ping">
              <Loader2 className={`${sizeClasses[size]} text-blue-300`} />
            </div>
          </div>
        );
      default:
        return <Loader2 className={`${sizeClasses[size]} animate-spin`} />;
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      {renderIcon()}
      {text && (
        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
};

// Skeleton loader for content
export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({ className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
    </div>
  </div>
);

// Page-level loading component
export const PageLoading: React.FC<PageLoadingProps> = ({
  message = 'Loading your content...'
}) => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
    <div className="text-center space-y-6">
      <div className="relative">
        <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center animate-pulse">
          <Mic className="w-10 h-10 text-white" />
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-ping opacity-75"></div>
      </div>
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {message}
        </h2>
        <div className="flex justify-center space-x-1">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  </div>
);
