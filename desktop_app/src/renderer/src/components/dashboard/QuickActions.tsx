import React from 'react';
import { motion } from 'framer-motion';

interface QuickAction {
  title: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  action: () => void;
  color: string;
}

interface QuickActionsProps {
  actions: QuickAction[];
}

const QuickActions: React.FC<QuickActionsProps> = ({ actions }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {actions.map((action, index) => (
        <motion.button
          key={action.title}
          onClick={action.action}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 text-left hover:shadow-md transition-shadow"
        >
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-lg ${action.color}`}>
              <action.icon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                {action.title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {action.description}
              </p>
            </div>
          </div>
        </motion.button>
      ))}
    </div>
  );
};

export default QuickActions;