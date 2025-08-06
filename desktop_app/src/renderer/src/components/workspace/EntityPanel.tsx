import React from 'react';
import { motion } from 'framer-motion';
import { 
  UserIcon, 
  BuildingOfficeIcon, 
  MapPinIcon, 
  CurrencyDollarIcon,
  CalendarIcon,
  TagIcon
} from '@heroicons/react/24/outline';

interface EntityPanelProps {
  entities: { [type: string]: string[] };
  isProcessing: boolean;
}

const EntityPanel: React.FC<EntityPanelProps> = ({ entities, isProcessing }) => {
  const exportEntities = async (format: 'json' | 'csv') => {
    try {
      // For now, use current transcription ID or generate mock one
      const transcriptionId = 'transcript_001';
      
      const response = await fetch(`http://localhost:8001/api/export/entities/${transcriptionId}?format=${format}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `entities_${transcriptionId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to export entities:', error);
    }
  };

  if (isProcessing) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500 dark:text-gray-400">Extracting entities...</p>
        </div>
      </div>
    );
  }

  const entityTypes = [
    { key: 'PERSON', label: 'People', icon: UserIcon, color: 'bg-blue-100 text-blue-800' },
    { key: 'ORG', label: 'Organizations', icon: BuildingOfficeIcon, color: 'bg-green-100 text-green-800' },
    { key: 'LOC', label: 'Locations', icon: MapPinIcon, color: 'bg-red-100 text-red-800' },
    { key: 'MONEY', label: 'Money', icon: CurrencyDollarIcon, color: 'bg-yellow-100 text-yellow-800' },
    { key: 'DATE', label: 'Dates', icon: CalendarIcon, color: 'bg-purple-100 text-purple-800' },
    { key: 'MISC', label: 'Other', icon: TagIcon, color: 'bg-gray-100 text-gray-800' }
  ];

  const hasEntities = Object.values(entities).some(entityList => entityList.length > 0);

  if (!hasEntities) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <TagIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">No entities found</p>
          <p className="text-sm text-gray-400 mt-2">Upload an audio file to extract entities</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="h-full overflow-y-auto"
    >
      <div className="p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
          Extracted Entities
        </h3>

        <div className="space-y-6">
          {entityTypes.map((entityType, index) => {
            const entityList = entities[entityType.key] || [];
            
            if (entityList.length === 0) return null;

            return (
              <motion.div
                key={entityType.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
              >
                <div className="flex items-center mb-4">
                  <div className={`p-2 rounded-lg ${entityType.color} mr-3`}>
                    <entityType.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                      {entityType.label}
                    </h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {entityList.length} found
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {entityList.map((entity, entityIndex) => (
                    <span
                      key={entityIndex}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                    >
                      {entity}
                    </span>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Entity Statistics */}
        <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
            Statistics
          </h4>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Total Entities</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                {Object.values(entities).flat().length}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Categories</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                {Object.keys(entities).filter(key => entities[key].length > 0).length}
              </dd>
            </div>
          </dl>
        </div>

        {/* Export Options */}
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">
            Export Entities
          </h4>
          <div className="flex space-x-3">
            <button 
              onClick={() => exportEntities('json')}
              className="btn-secondary text-sm"
            >
              Download JSON
            </button>
            <button 
              onClick={() => exportEntities('csv')}
              className="btn-secondary text-sm"
            >
              Download CSV
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default EntityPanel;