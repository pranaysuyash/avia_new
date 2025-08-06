import React, { useState, useEffect } from 'react';
import {
  Video,
  Upload,
  Wand2,
  Sparkles,
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
  FileVideo,
  Cpu,
  HardDrive,
  Activity,
  Download,
  Eye,
  Trash2
} from 'lucide-react';
import VideoPlayer from './VideoPlayer';
import { api } from '../../services/api';

interface VideoProcessingJob {
  id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  endTime?: string;
  input: {
    duration: number;
    resolution: string;
    size: number;
    codec: string;
  };
  output?: {
    duration: number;
    resolution: string;
    size: number;
    format: string;
  };
  error?: string;
  transcriptionId?: string;
}

interface ProcessingOptions {
  resolution: string;
  format: string;
  quality: string;
  removeAudio: boolean;
  extractAudio: boolean;
  generateThumbnails: boolean;
  autoTranscribe: boolean;
  enhanceVideo: boolean;
}

export const VideoProcessing: React.FC = () => {
  const [jobs, setJobs] = useState<VideoProcessingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<VideoProcessingJob | null>(null);
  const [processingOptions, setProcessingOptions] = useState<ProcessingOptions>({
    resolution: 'original',
    format: 'mp4',
    quality: 'high',
    removeAudio: false,
    extractAudio: false,
    generateThumbnails: true,
    autoTranscribe: true,
    enhanceVideo: false
  });
  const [showOptions, setShowOptions] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await api.get('/video-processing/jobs');
      setJobs(response.data.jobs);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('options', JSON.stringify(processingOptions));

      const response = await api.post('/video-processing/upload', formData);
      const newJob = response.data.job;
      setJobs([newJob, ...jobs]);
    } catch (err) {
      console.error('Failed to upload file:', err);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const videoFile = files.find(file => file.type.startsWith('video/'));
    
    if (videoFile) {
      handleFileUpload(videoFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const deleteJob = async (jobId: string) => {
    try {
      await api.delete(`/video-processing/jobs/${jobId}`);
      setJobs(jobs.filter(job => job.id !== jobId));
      if (selectedJob?.id === jobId) {
        setSelectedJob(null);
      }
    } catch (err) {
      console.error('Failed to delete job:', err);
    }
  };

  const downloadOutput = async (jobId: string) => {
    try {
      // Use fetch directly for blob download
      const response = await fetch(`http://localhost:8001/video-processing/jobs/${jobId}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `processed_${jobId}.mp4`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download:', err);
    }
  };

  const getStatusIcon = (status: VideoProcessingJob['status']) => {
    switch (status) {
      case 'queued':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'processing':
        return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  return (
    <div className="h-full flex">
      {/* Jobs List */}
      <div className="w-96 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Video className="w-5 h-5" />
              Video Processing
            </h2>
            <button
              onClick={() => setShowOptions(!showOptions)}
              className="p-2 hover:bg-gray-700 rounded transition"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>

          {/* Upload Area */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`border-2 border-dashed rounded-lg p-6 text-center transition ${
              isDragging 
                ? 'border-blue-500 bg-blue-500/10' 
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm text-gray-400">
              Drop video file here or click to browse
            </p>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
              className="hidden"
              id="video-upload"
            />
            <label
              htmlFor="video-upload"
              className="mt-2 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 cursor-pointer"
            >
              Select Video
            </label>
          </div>

          {/* Processing Options */}
          {showOptions && (
            <div className="mt-4 p-4 bg-gray-900 rounded-lg space-y-3">
              <h3 className="text-sm font-medium mb-2">Processing Options</h3>
              
              <div>
                <label className="text-xs text-gray-400">Output Format</label>
                <select
                  value={processingOptions.format}
                  onChange={(e) => setProcessingOptions({...processingOptions, format: e.target.value})}
                  className="w-full mt-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-sm"
                >
                  <option value="mp4">MP4</option>
                  <option value="webm">WebM</option>
                  <option value="mov">MOV</option>
                  <option value="avi">AVI</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400">Resolution</label>
                <select
                  value={processingOptions.resolution}
                  onChange={(e) => setProcessingOptions({...processingOptions, resolution: e.target.value})}
                  className="w-full mt-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-sm"
                >
                  <option value="original">Original</option>
                  <option value="1080p">1080p</option>
                  <option value="720p">720p</option>
                  <option value="480p">480p</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400">Quality</label>
                <select
                  value={processingOptions.quality}
                  onChange={(e) => setProcessingOptions({...processingOptions, quality: e.target.value})}
                  className="w-full mt-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-sm"
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={processingOptions.autoTranscribe}
                    onChange={(e) => setProcessingOptions({...processingOptions, autoTranscribe: e.target.checked})}
                    className="mr-2"
                  />
                  Auto-transcribe
                </label>
                
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={processingOptions.generateThumbnails}
                    onChange={(e) => setProcessingOptions({...processingOptions, generateThumbnails: e.target.checked})}
                    className="mr-2"
                  />
                  Generate thumbnails
                </label>
                
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={processingOptions.enhanceVideo}
                    onChange={(e) => setProcessingOptions({...processingOptions, enhanceVideo: e.target.checked})}
                    className="mr-2"
                  />
                  AI video enhancement
                </label>
                
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={processingOptions.extractAudio}
                    onChange={(e) => setProcessingOptions({...processingOptions, extractAudio: e.target.checked})}
                    className="mr-2"
                  />
                  Extract audio track
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Jobs List */}
        <div className="flex-1 overflow-y-auto">
          {jobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <FileVideo className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No processing jobs yet</p>
            </div>
          ) : (
            <div className="space-y-2 p-2">
              {jobs.map(job => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  className={`w-full p-3 rounded-lg text-left transition ${
                    selectedJob?.id === job.id 
                      ? 'bg-blue-600/20 border border-blue-600' 
                      : 'hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {getStatusIcon(job.status)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{job.filename}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {job.status === 'processing' && job.progress > 0 && (
                          <div className="mb-1">{job.progress}% complete</div>
                        )}
                        <div className="flex items-center gap-3">
                          <span>{job.input.resolution}</span>
                          <span>{formatFileSize(job.input.size)}</span>
                          <span>{formatDuration(job.input.duration)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {job.status === 'processing' && (
                    <div className="mt-2 bg-gray-700 rounded-full h-1 overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Job Details / Video Player */}
      <div className="flex-1 bg-gray-900">
        {selectedJob ? (
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">{selectedJob.filename}</h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                    {getStatusIcon(selectedJob.status)}
                    <span className="capitalize">{selectedJob.status}</span>
                    {selectedJob.endTime && (
                      <span>
                        Processed in {formatDuration(
                          (new Date(selectedJob.endTime).getTime() - new Date(selectedJob.startTime).getTime()) / 1000
                        )}
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {selectedJob.status === 'completed' && (
                    <>
                      <button
                        onClick={() => downloadOutput(selectedJob.id)}
                        className="flex items-center gap-2 px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                      {selectedJob.transcriptionId && (
                        <button className="flex items-center gap-2 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                          <Eye className="w-4 h-4" />
                          View Transcript
                        </button>
                      )}
                    </>
                  )}
                  <button
                    onClick={() => deleteJob(selectedJob.id)}
                    className="flex items-center gap-2 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 p-4">
              {selectedJob.status === 'completed' && selectedJob.output ? (
                <div className="h-full flex flex-col gap-4">
                  <VideoPlayer 
                    src={`/api/video-processing/jobs/${selectedJob.id}/preview`}
                    poster={`/api/video-processing/jobs/${selectedJob.id}/thumbnail`}
                  />
                  
                  {/* Processing Details */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Cpu className="w-5 h-5 text-blue-500" />
                        <span className="font-medium">Input</span>
                      </div>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Resolution:</dt>
                          <dd>{selectedJob.input.resolution}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Size:</dt>
                          <dd>{formatFileSize(selectedJob.input.size)}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Codec:</dt>
                          <dd>{selectedJob.input.codec}</dd>
                        </div>
                      </dl>
                    </div>
                    
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="w-5 h-5 text-green-500" />
                        <span className="font-medium">Output</span>
                      </div>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Resolution:</dt>
                          <dd>{selectedJob.output.resolution}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Size:</dt>
                          <dd>{formatFileSize(selectedJob.output.size)}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-400">Format:</dt>
                          <dd>{selectedJob.output.format.toUpperCase()}</dd>
                        </div>
                      </dl>
                    </div>
                    
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="w-5 h-5 text-purple-500" />
                        <span className="font-medium">Enhancements</span>
                      </div>
                      <ul className="space-y-1 text-sm">
                        <li className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Stabilization applied</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Noise reduction</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Color correction</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              ) : selectedJob.status === 'processing' ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <div className="relative w-32 h-32 mx-auto mb-6">
                      <div className="absolute inset-0 border-4 border-gray-700 rounded-full"></div>
                      <div 
                        className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"
                        style={{
                          animationDuration: '2s'
                        }}
                      ></div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-2xl font-bold">{selectedJob.progress}%</span>
                      </div>
                    </div>
                    <p className="text-lg mb-2">Processing video...</p>
                    <p className="text-sm text-gray-400">This may take several minutes</p>
                  </div>
                </div>
              ) : selectedJob.status === 'failed' ? (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <AlertCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
                    <p className="text-lg mb-2">Processing failed</p>
                    <p className="text-sm text-gray-400">{selectedJob.error || 'An error occurred'}</p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <Clock className="w-16 h-16 mx-auto mb-4 text-yellow-500" />
                    <p className="text-lg mb-2">Queued for processing</p>
                    <p className="text-sm text-gray-400">Your video will be processed soon</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Wand2 className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="text-lg text-gray-400">Select a video to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoProcessing;