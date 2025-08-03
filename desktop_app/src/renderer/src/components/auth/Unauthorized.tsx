import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiAlertTriangle, FiHome, FiArrowLeft } from 'react-icons/fi';

const Unauthorized: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full"
      >
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 dark:bg-red-900">
            <FiAlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          
          <h1 className="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
            403
          </h1>
          
          <h2 className="mt-2 text-xl font-semibold text-gray-900 dark:text-white">
            Access Denied
          </h2>
          
          <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            You don't have permission to access this page. Please contact your administrator if you believe this is an error.
          </p>
          
          <div className="mt-8 space-y-3">
            <button
              onClick={() => navigate(-1)}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              <FiArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </button>
            
            <button
              onClick={() => navigate('/')}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <FiHome className="mr-2 h-4 w-4" />
              Go to Dashboard
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Unauthorized;