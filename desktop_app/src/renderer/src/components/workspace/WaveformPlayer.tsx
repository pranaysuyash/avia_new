import React, { useEffect, useRef } from 'react';
import { PlayIcon, PauseIcon } from '@heroicons/react/24/solid';

interface WaveformPlayerProps {
  audioUrl: string;
  isPlaying: boolean;
  onPlayPause: () => void;
}

const WaveformPlayer: React.FC<WaveformPlayerProps> = ({ 
  audioUrl, 
  isPlaying, 
  onPlayPause 
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.play();
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying]);

  // Simple waveform visualization (placeholder)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    // Generate mock waveform
    ctx.fillStyle = '#6366f1';
    for (let i = 0; i < width; i += 4) {
      const amplitude = Math.random() * height * 0.8;
      const y = (height - amplitude) / 2;
      ctx.fillRect(i, y, 2, amplitude);
    }
  }, [audioUrl]);

  return (
    <div className="h-full flex flex-col">
      <audio ref={audioRef} src={audioUrl} />
      
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={onPlayPause}
          className="flex items-center justify-center w-12 h-12 bg-indigo-600 hover:bg-indigo-700 rounded-full text-white transition-colors"
        >
          {isPlaying ? (
            <PauseIcon className="h-6 w-6" />
          ) : (
            <PlayIcon className="h-6 w-6 ml-1" />
          )}
        </button>
        
        <div className="flex-1 mx-4">
          <div className="bg-gray-600 rounded-full h-2">
            <div className="bg-indigo-400 h-2 rounded-full w-1/3"></div>
          </div>
        </div>
        
        <div className="text-white text-sm font-mono">
          00:45 / 02:30
        </div>
      </div>

      {/* Waveform */}
      <div className="flex-1">
        <canvas
          ref={canvasRef}
          width={800}
          height={120}
          className="w-full h-full"
        />
      </div>
    </div>
  );
};

export default WaveformPlayer;