import React, { useState, useMemo } from 'react';

const TranscriptionViewer = ({ transcription, entities = [], showTimestamps = true }) => {
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [highlightEnabled, setHighlightEnabled] = useState(true);
  const [entityFilter, setEntityFilter] = useState('all');
  
  // Entity type colors
  const entityColors = {
    PERSON: 'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200',
    ORGANIZATION: 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200',
    LOCATION: 'bg-purple-200 dark:bg-purple-800 text-purple-800 dark:text-purple-200',
    DATE: 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200',
    EVENT: 'bg-pink-200 dark:bg-pink-800 text-pink-800 dark:text-pink-200',
    PRODUCT: 'bg-indigo-200 dark:bg-indigo-800 text-indigo-800 dark:text-indigo-200',
    TECHNOLOGY: 'bg-orange-200 dark:bg-orange-800 text-orange-800 dark:text-orange-200',
    default: 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
  };

  // Process entities by type
  const entitiesByType = useMemo(() => {
    const grouped = {};
    entities.forEach(entity => {
      const type = entity.label || 'OTHER';
      if (!grouped[type]) grouped[type] = [];
      grouped[type].push(entity);
    });
    return grouped;
  }, [entities]);

  // Filter entities based on selected type
  const filteredEntities = useMemo(() => {
    if (entityFilter === 'all') return entities;
    return entities.filter(e => e.label === entityFilter);
  }, [entities, entityFilter]);

  // Highlight entities in text
  const highlightedText = useMemo(() => {
    if (!highlightEnabled || !transcription?.text || filteredEntities.length === 0) {
      return transcription?.text || '';
    }

    let text = transcription.text;
    const highlights = [];

    // Sort entities by position (if available) or by length (longer first to avoid partial matches)
    const sortedEntities = [...filteredEntities].sort((a, b) => {
      if (a.start !== undefined && b.start !== undefined) {
        return a.start - b.start;
      }
      return b.text.length - a.text.length;
    });

    // Create a map of replacements
    sortedEntities.forEach((entity, index) => {
      const regex = new RegExp(`\\b${entity.text}\\b`, 'gi');
      const color = entityColors[entity.label] || entityColors.default;
      const replacement = `<mark data-entity="${index}" class="${color} px-1 rounded cursor-pointer hover:opacity-80 transition-opacity">${entity.text}</mark>`;
      
      highlights.push({
        pattern: regex,
        replacement,
        entity
      });
    });

    // Apply highlights
    highlights.forEach(({ pattern, replacement }) => {
      text = text.replace(pattern, replacement);
    });

    return text;
  }, [transcription, filteredEntities, highlightEnabled, entityColors]);

  // Handle entity click
  const handleEntityClick = (entityIndex) => {
    const entity = filteredEntities[entityIndex];
    setSelectedEntity(entity);
  };

  // Parse segments with timestamps
  const segments = useMemo(() => {
    if (!transcription?.segments || !showTimestamps) {
      return [{ text: highlightedText, timestamp: '' }];
    }

    return transcription.segments.map(segment => ({
      text: segment.text,
      timestamp: formatTimestamp(segment.start),
      speaker: segment.speaker
    }));
  }, [transcription, highlightedText, showTimestamps]);

  const formatTimestamp = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex gap-6">
      {/* Main Transcription Panel */}
      <div className="flex-1">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          {/* Controls */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setHighlightEnabled(!highlightEnabled)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    highlightEnabled 
                      ? 'bg-primary-600 text-white' 
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  {highlightEnabled ? 'Highlighting On' : 'Highlighting Off'}
                </button>

                <select
                  value={entityFilter}
                  onChange={(e) => setEntityFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="all">All Entities</option>
                  {Object.keys(entitiesByType).map(type => (
                    <option key={type} value={type}>
                      {type} ({entitiesByType[type].length})
                    </option>
                  ))}
                </select>
              </div>

              <div className="text-sm text-gray-600 dark:text-gray-400">
                {filteredEntities.length} entities highlighted
              </div>
            </div>
          </div>

          {/* Transcription Text */}
          <div className="p-6 max-h-[600px] overflow-y-auto">
            {showTimestamps && transcription?.segments ? (
              <div className="space-y-4">
                {segments.map((segment, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400 min-w-[60px]">
                      {segment.timestamp}
                    </div>
                    {segment.speaker && (
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300 min-w-[80px]">
                        {segment.speaker}:
                      </div>
                    )}
                    <div 
                      className="flex-1 text-gray-800 dark:text-gray-200"
                      dangerouslySetInnerHTML={{ __html: segment.text }}
                      onClick={(e) => {
                        if (e.target.hasAttribute('data-entity')) {
                          handleEntityClick(parseInt(e.target.getAttribute('data-entity')));
                        }
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div 
                className="text-gray-800 dark:text-gray-200 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: highlightedText }}
                onClick={(e) => {
                  if (e.target.hasAttribute('data-entity')) {
                    handleEntityClick(parseInt(e.target.getAttribute('data-entity')));
                  }
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Entity Sidebar */}
      <div className="w-80">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 sticky top-0">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Entities Found</h3>
          </div>
          
          <div className="p-4 max-h-[600px] overflow-y-auto">
            {Object.entries(entitiesByType).map(([type, typeEntities]) => (
              <div key={type} className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {type} ({typeEntities.length})
                </h4>
                <div className="space-y-2">
                  {typeEntities.map((entity, index) => (
                    <div
                      key={`${type}-${index}`}
                      onClick={() => setSelectedEntity(entity)}
                      className={`p-2 rounded-lg cursor-pointer transition-all ${
                        selectedEntity === entity 
                          ? 'ring-2 ring-primary-500' 
                          : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                      } ${entityColors[entity.label] || entityColors.default}`}
                    >
                      <div className="font-medium">{entity.text}</div>
                      {entity.count && (
                        <div className="text-xs opacity-75 mt-1">
                          Appears {entity.count} time{entity.count > 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {entities.length === 0 && (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No entities found in this transcription
              </p>
            )}
          </div>

          {/* Selected Entity Details */}
          {selectedEntity && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Entity Details</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Text:</span>{' '}
                  <span className="font-medium text-gray-900 dark:text-white">{selectedEntity.text}</span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Type:</span>{' '}
                  <span className="font-medium text-gray-900 dark:text-white">{selectedEntity.label}</span>
                </div>
                {selectedEntity.confidence && (
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Confidence:</span>{' '}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {(selectedEntity.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TranscriptionViewer;