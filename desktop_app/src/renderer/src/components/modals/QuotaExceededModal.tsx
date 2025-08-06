/**
 * Quota Exceeded Modal
 * Displays when user exceeds their usage quota with upgrade options
 */

import React from 'react';
import { useUsage } from '../../contexts/UsageContext';

interface QuotaExceededModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpgrade: () => void;
}

export function QuotaExceededModal({ isOpen, onClose, onUpgrade }: QuotaExceededModalProps) {
  const { state, clearError } = useUsage();

  if (!isOpen) return null;

  const handleClose = () => {
    clearError();
    onClose();
  };

  const handleUpgrade = () => {
    onUpgrade();
    handleClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                />
              </svg>
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Usage Quota Exceeded
              </h3>
              <div className="mt-2">
                {state.error ? (
                  <p className="text-sm text-gray-500">
                    {state.error}
                  </p>
                ) : (
                  <p className="text-sm text-gray-500">
                    You've reached your usage limit for your current plan. 
                    Upgrade to continue using premium features.
                  </p>
                )}
                
                {state.usage && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Current Plan: {state.usage.plan.name}
                    </h4>
                    <div className="space-y-2 text-sm text-gray-600">
                      {Object.entries(state.usage.usage).map(([type, usage]) => {
                        if (usage.percentage_used >= 90) {
                          return (
                            <div key={type} className="flex justify-between">
                              <span className="capitalize">{type.replace('_', ' ')}:</span>
                              <span className="font-medium text-red-600">
                                {usage.current} / {usage.limit} ({usage.percentage_used.toFixed(1)}%)
                              </span>
                            </div>
                          );
                        }
                        return null;
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={handleUpgrade}
            >
              Upgrade Plan
            </button>
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
              onClick={handleClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface FeatureBlockedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpgrade: () => void;
  featureName?: string;
}

export function FeatureBlockedModal({ isOpen, onClose, onUpgrade, featureName }: FeatureBlockedModalProps) {
  const { state, clearError } = useUsage();

  if (!isOpen) return null;

  const handleClose = () => {
    clearError();
    onClose();
  };

  const handleUpgrade = () => {
    onUpgrade();
    handleClose();
  };

  const formatFeatureName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
              <svg
                className="h-6 w-6 text-yellow-600"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"
                />
              </svg>
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Premium Feature Required
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  {featureName ? (
                    <>
                      The <strong>{formatFeatureName(featureName)}</strong> feature requires a premium subscription.
                    </>
                  ) : (
                    'This feature requires a premium subscription.'
                  )}
                  {' '}Upgrade your plan to access all premium features.
                </p>
                
                {state.usage && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">
                      Current Plan: {state.usage.plan.name}
                    </h4>
                    <p className="text-sm text-gray-600">
                      Upgrade to unlock premium features including:
                    </p>
                    <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
                      <li>Advanced analytics and insights</li>
                      <li>Custom AI models and prompts</li>
                      <li>Real-time collaboration</li>
                      <li>Priority support</li>
                      <li>White-label options</li>
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={handleUpgrade}
            >
              Upgrade Plan
            </button>
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
              onClick={handleClose}
            >
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}