import React, { useState, useMemo } from 'react';

const SpeakerDiarization = ({ segments = [], duration = 0 }) => {
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);
  const [hoveredSegment, setHoveredSegment] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [timelinePosition, setTimelinePosition] = useState(0);

  // Extract unique speakers and assign colors
  const speakers = useMemo(() => {
    const speakerSet = new Set(segments.map(s => s.speaker));
    const speakerArray = Array.from(speakerSet);
    const colors = [
      '#3B82F6', // blue
      '#10B981', // emerald
      '#8B5CF6', // violet
      '#F59E0B', // amber
      '#EF4444', // red
      '#EC4899', // pink
      '#14B8A6', // teal
      '#6366F1', // indigo
    ];
    
    return speakerArray.map((speaker, index) => ({
      name: speaker,
      color: colors[index % colors.length],
      segments: segments.filter(s => s.speaker === speaker),
      totalTime: segments.filter(s => s.speaker === speaker)
        .reduce((acc, s) => acc + (s.end - s.start), 0),
    }));
  }, [segments]);

  // Calculate overlapping segments
  const overlappingSegments = useMemo(() => {
    const overlaps = [];
    for (let i = 0; i < segments.length; i++) {
      for (let j = i + 1; j < segments.length; j++) {
        const seg1 = segments[i];
        const seg2 = segments[j];
        
        // Check if segments overlap
        if (seg1.start < seg2.end && seg2.start < seg1.end && seg1.speaker !== seg2.speaker) {
          overlaps.push({
            start: Math.max(seg1.start, seg2.start),
            end: Math.min(seg1.end, seg2.end),
            speakers: [seg1.speaker, seg2.speaker],
            segments: [seg1, seg2]
          });
        }
      }
    }
    return overlaps;
  }, [segments]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimelineClick = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const clickedTime = (x / rect.width) * duration / zoomLevel + timelinePosition;
    console.log('Clicked at time:', formatTime(clickedTime));
  };

  const getSegmentWidth = (segment) => {
    return ((segment.end - segment.start) / duration) * 100 * zoomLevel;
  };

  const getSegmentLeft = (segment) => {
    return ((segment.start - timelinePosition) / duration) * 100 * zoomLevel;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Speaker Diarization Timeline
        </h3>
        
        {/* Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setZoomLevel(Math.max(1, zoomLevel - 0.5))}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                disabled={zoomLevel <= 1}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel(Math.min(5, zoomLevel + 0.5))}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                disabled={zoomLevel >= 5}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>
          </div>
          
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Duration: {formatTime(duration)}
          </div>
        </div>

        {/* Timeline Container */}
        <div className="relative bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-hidden">
          {/* Time markers */}
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-500 mb-3">
            {Array.from({ length: 5 }, (_, i) => {
              const time = (i / 4) * duration;
              return <span key={i}>{formatTime(time)}</span>;
            })}
          </div>

          {/* Timeline tracks */}
          <div className="space-y-2">
            {speakers.map((speaker, speakerIndex) => (
              <div key={speaker.name} className="relative">
                {/* Speaker label */}
                <div className="flex items-center mb-1">
                  <div 
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: speaker.color }}
                  />
                  <span className={`text-sm font-medium ${
                    selectedSpeaker === speaker.name 
                      ? 'text-gray-900 dark:text-white' 
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                    {speaker.name}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-500 ml-2">
                    ({formatTime(speaker.totalTime)})
                  </span>
                </div>

                {/* Track */}
                <div 
                  className="relative h-8 bg-gray-200 dark:bg-gray-700 rounded cursor-pointer overflow-hidden"
                  onClick={handleTimelineClick}
                  onMouseEnter={() => setSelectedSpeaker(speaker.name)}
                  onMouseLeave={() => setSelectedSpeaker(null)}
                >
                  {speaker.segments.map((segment, segIndex) => (
                    <div
                      key={segIndex}
                      className={`absolute h-full rounded transition-all ${
                        hoveredSegment === `${speakerIndex}-${segIndex}`
                          ? 'ring-2 ring-offset-1 ring-gray-400'
                          : ''
                      }`}
                      style={{
                        backgroundColor: speaker.color,
                        left: `${getSegmentLeft(segment)}%`,
                        width: `${getSegmentWidth(segment)}%`,
                        opacity: selectedSpeaker && selectedSpeaker !== speaker.name ? 0.3 : 0.8,
                      }}
                      onMouseEnter={() => setHoveredSegment(`${speakerIndex}-${segIndex}`)}
                      onMouseLeave={() => setHoveredSegment(null)}
                    >
                      {/* Tooltip */}
                      {hoveredSegment === `${speakerIndex}-${segIndex}` && (
                        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                          {formatTime(segment.start)} - {formatTime(segment.end)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Overlap indicators */}
          {overlappingSegments.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-300 dark:border-gray-600">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Overlapping Speech ({overlappingSegments.length} instances)
              </h4>
              <div className="relative h-6 bg-gray-200 dark:bg-gray-700 rounded">
                {overlappingSegments.map((overlap, index) => (
                  <div
                    key={index}
                    className="absolute h-full bg-red-500 opacity-50 rounded"
                    style={{
                      left: `${(overlap.start / duration) * 100}%`,
                      width: `${((overlap.end - overlap.start) / duration) * 100}%`,
                    }}
                    title={`${overlap.speakers.join(' & ')} overlap`}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Speaker Statistics */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {speakers.map((speaker) => (
            <div 
              key={speaker.name}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                selectedSpeaker === speaker.name
                  ? 'bg-gray-100 dark:bg-gray-700 border-gray-400 dark:border-gray-500'
                  : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700'
              }`}
              onClick={() => setSelectedSpeaker(
                selectedSpeaker === speaker.name ? null : speaker.name
              )}
            >
              <div className="flex items-center mb-2">
                <div 
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: speaker.color }}
                />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {speaker.name}
                </span>
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <div>Time: {formatTime(speaker.totalTime)}</div>
                <div>Segments: {speaker.segments.length}</div>
                <div>Share: {Math.round((speaker.totalTime / duration) * 100)}%</div>
              </div>
            </div>
          ))}
        </div>

        {/* Interaction Patterns */}
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Speaking Patterns
          </h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                Average Turn Length
              </div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {formatTime(segments.reduce((acc, s) => acc + (s.end - s.start), 0) / segments.length)}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                Total Overlaps
              </div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                {overlappingSegments.length}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpeakerDiarization;