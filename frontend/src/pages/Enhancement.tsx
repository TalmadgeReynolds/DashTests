import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { VideoPlayer } from '@/components/video/VideoPlayer';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api-client';
import { logger } from '@/lib/logger';

import type { TopazModel, TopazSettings } from '@/types';

interface VideoMetadata {
  size: number;
  duration: number;
  frameCount: number;
  frameRate: number;
  width: number;
  height: number;
}

interface TopazRecommendations {
  suggestedModel: string;
  suggestedSettings: {
    denoiseLevel?: number;
    sharpness?: number;
    stabilization?: boolean;
  };
  qualityAnalysis: {
    noise: number;
    sharpness: number;
    stability: number;
  };
  performanceEstimate: {
    processingTime: number;
    gpuMemoryRequired: number;
  };
}

interface CostEstimate {
  estimatedCost: number;
  metadata: VideoMetadata;
  recommendations?: TopazRecommendations;
}

const getContainerFromFile = (file: File): 'mov' | 'mp4' => {
  // Check file extension
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (ext === 'mov' || file.type === 'video/quicktime') {
    return 'mov';
  }
  return 'mp4';
};

const defaultSettings: TopazSettings = {
  inputResolution: { width: 1920, height: 1080 },
  frameRate: 30,
  outputResolution: { width: 1920, height: 1080 },
  outputFrameRate: 30,
  audioCodec: 'AAC',
  audioTransfer: 'Copy',
  dynamicCompressionLevel: 'Mid',
  container: 'mp4',
  filters: [{
    model: 'prob-4',  // Proteus - Best for most videos
    slowmo: 1,
    denoiseLevel: 0.5,
    sharpness: 0.5,
    stabilization: false,
    colorGrading: {
      brightness: 0,
      contrast: 0,
      saturation: 0,
      temperature: 0,
      tint: 0
    }
  }]
};

export default function Enhancement() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [settings, setSettings] = useState<TopazSettings>(defaultSettings);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [topazMetadata, setTopazMetadata] = useState<Record<string, unknown> | null>(null);
  
  const [processedVideo, setProcessedVideo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoPreviewId = 'video-preview';
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll for job status
  useEffect(() => {
    const pollStatus = async () => {
      if (!jobId || jobStatus === 'completed' || jobStatus === 'failed') return;
      
      try {
        const status = await apiClient.getProcessingStatus(jobId);
        logger.info('Job status update', { jobId, status: status.status, progress: status.progress });
        
        setJobStatus(status.status);
        setProgress(status.progress || 0);
        
        // Store all Topaz metadata
        setTopazMetadata(status);
        
        if (status.status === 'completed' && status.processedVideoUrl) {
          logger.info('Processing complete!', { url: status.processedVideoUrl });
          setProcessedVideo(status.processedVideoUrl);
          setProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        } else if (status.status === 'failed') {
          logger.error('Processing failed', new Error(JSON.stringify(status)));
          setProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
          alert('Video processing failed. Please try again.');
        }
      } catch (error) {
        logger.error('Failed to check status', error instanceof Error ? error : new Error(String(error)));
      }
    };
    
    if (jobId && processing) {
      // Poll every 5 seconds
      pollIntervalRef.current = setInterval(pollStatus, 5000);
      pollStatus(); // Check immediately
      
      return () => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
        }
      };
    }
  }, [jobId, processing, jobStatus]);

  // Get cost estimate when file is selected or settings change
  useEffect(() => {
    const getEstimate = async () => {
      if (selectedFile?.name && settings.inputResolution.width > 0 && settings.inputResolution.height > 0) {
        try {
          // Upload file first
          const formData = new FormData();
          formData.append('file', selectedFile);
          const response = await fetch('/api/v1/enhancement/upload', {
            method: 'POST',
            body: formData
          });
          const { videoKey } = await response.json();
          
          // Then get cost estimate with recommendations
          const estimate = await apiClient.getProcessingCostEstimate(videoKey, settings);
          setCostEstimate(estimate);
        } catch (error) {
          logger.error('Failed to get cost estimate', error instanceof Error ? error.message : String(error));
        }
      }
    };
    getEstimate();
  }, [selectedFile, settings.inputResolution, settings]);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      logger.info('Starting video upload process', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      });

      // Get presigned URL
      const { uploadUrl, videoKey } = await apiClient.getVideoUploadUrl(file);
      logger.debug('Received presigned URL', { videoKey });
      
      // Upload with progress tracking
      const xhr = new XMLHttpRequest();
      await new Promise((resolve, reject) => {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            setProgress(progress);
            logger.debug('Upload progress', { progress: `${progress.toFixed(2)}%` });
          }
        };
        
        xhr.onload = () => {
          logger.info('Upload completed successfully', { videoKey });
          resolve(xhr.response);
        };

          xhr.onerror = () => {
          logger.error('Upload failed', xhr.statusText);
          reject(xhr.statusText);
        };        xhr.open('PUT', uploadUrl);
        
        // Set the correct content type for ProRes MOV
        if (file.name.toLowerCase().endsWith('.mov')) {
          xhr.setRequestHeader('Content-Type', 'video/quicktime');
        } else {
          xhr.setRequestHeader('Content-Type', file.type || 'video/mp4');
        }
        
        xhr.send(file);
      });

      return videoKey;
    }
  });

  const processMutation = useMutation({
    mutationFn: async ({ video_key, settings }: { video_key: string; settings: TopazSettings }) => {
      logger.info('Starting video processing', {
        video_key,
        settings: {
          inputResolution: settings.inputResolution,
          outputResolution: settings.outputResolution,
          frameRate: settings.frameRate,
          outputFrameRate: settings.outputFrameRate,
          filters: settings.filters.map(f => ({ model: f.model, stabilization: f.stabilization }))
        }
      });

      try {
        const response = await apiClient.processVideo(video_key, settings);
        logger.info('Processing job created', { 
          jobId: response.jobId,
          estimatedCost: response.estimatedCost,
          metadata: response.metadata 
        });
        
        // Store all Topaz data from initial response
        if (response.metadata) {
          setTopazMetadata(response.metadata as Record<string, unknown>);
        } else if (response.estimatedCost || response.estimatedFrames) {
          // If metadata not nested, create from top-level fields
          setTopazMetadata({
            estimatedCost: response.estimatedCost,
            estimatedFrames: response.estimatedFrames,
            estimatedDuration: response.estimatedDuration,
            recommendations: response.recommendations
          } as Record<string, unknown>);
        }
        
        return response.jobId;
      } catch (error) {
        logger.error('Processing failed', error instanceof Error ? error : String(error));
        throw error;
      }
    }
  });

  const getVideoResolution = (file: File): Promise<{ width: number; height: number }> => {
    return new Promise((resolve) => {
      const video = document.createElement('video');
      video.preload = 'metadata';

      video.onloadedmetadata = () => {
        URL.revokeObjectURL(video.src);
        resolve({
          width: video.videoWidth || 1920, // Default to 1080p if can't detect
          height: video.videoHeight || 1080
        });
      };

      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        resolve({ width: 1920, height: 1080 }); // Default if metadata can't be read
      };

      video.src = URL.createObjectURL(file);
    });
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.size > 2 * 1024 * 1024 * 1024) { // 2GB
      alert('File size must be less than 2GB');
      return;
    }

    try {
      // Get video metadata first
      const resolution = await getVideoResolution(file);
      logger.debug('Video resolution detected', resolution);

      // Set file and update settings
      setSelectedFile(file);
      const container = getContainerFromFile(file);
      setSettings(prev => ({
        ...prev,
        inputResolution: {
          width: Math.max(resolution.width, 1),
          height: Math.max(resolution.height, 1)
        },
        outputResolution: {
          width: Math.max(resolution.width, 1),
          height: Math.max(resolution.height, 1)
        },
        container,
        outputContainer: container
      }));
    } catch (error) {
      logger.error('Failed to get video metadata', error instanceof Error ? error.message : String(error));
      alert('Error reading video file. Please try another file.');
    }
  };

  const handleModelChange = (model: TopazSettings['filters'][0]['model']) => {
    setSettings(prev => ({
      ...prev,
      filters: [{
        ...prev.filters[0],
        model
      }]
    }));
  };

  const handleUploadAndProcess = async () => {
    if (!selectedFile || !settings.inputResolution.width || !settings.inputResolution.height) {
      logger.warn('No file selected or invalid resolution', { 
        hasFile: !!selectedFile,
        resolution: settings.inputResolution
      });
      alert('Please select a valid video file');
      return;
    }
    
    try {
      setProcessing(true);
      logger.info('Starting upload and process workflow', {
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        fileType: selectedFile.type,
        resolution: settings.inputResolution
      });
      
      // Upload file
      logger.debug('Initiating file upload');
      const videoKey = await uploadMutation.mutateAsync(selectedFile);
      logger.info('Upload completed', { videoKey });
      
      // Process with Topaz
      logger.debug('Initiating Topaz processing', {
        videoKey,
        inputResolution: settings.inputResolution,
        outputResolution: settings.outputResolution
      });

      const processedVideoUrl = await processMutation.mutateAsync({
        video_key: videoKey,
        settings: {
          ...settings,
          // Ensure non-zero resolution values
          inputResolution: {
            width: Math.max(settings.inputResolution.width, 1),
            height: Math.max(settings.inputResolution.height, 1)
          },
          outputResolution: {
            width: Math.max(settings.outputResolution.width, 1),
            height: Math.max(settings.outputResolution.height, 1)
          }
        }
      });
      logger.info('Job submitted', { jobId: processedVideoUrl });
      
      // Start polling for status
      setJobId(processedVideoUrl);
      setJobStatus('processing');
      // Keep processing=true so polling continues
    } catch (error) {
      logger.error('Upload and process workflow failed', error instanceof Error ? error : String(error));
      alert('Error processing video. Please try again.');
      setProcessing(false); // Only set false on error
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Video Enhancement</h1>
        <div className="flex gap-4 items-center">
          {costEstimate && (
            <div className="text-slate-600">
              Estimated Cost: ${costEstimate.estimatedCost.toFixed(2)}
            </div>
          )}
          {jobStatus && (
            <div className="text-sm px-3 py-1 rounded-full bg-blue-100 text-blue-800">
              Status: {jobStatus} {progress > 0 && `(${progress.toFixed(0)}%)`}
            </div>
          )}
        </div>
      </div>

            {/* Topaz Metadata Display */}
      {topazMetadata && Object.keys(topazMetadata).length > 0 && (
        <div className="mb-6 p-4 bg-slate-50 rounded-lg">
          <h3 className="font-semibold mb-2">Processing Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {topazMetadata.estimatedCost !== null && topazMetadata.estimatedCost !== undefined && (
              <div>
                <span className="text-slate-600">Cost:</span>{' '}
                <span className="font-medium">${Number(topazMetadata.estimatedCost).toFixed(2)}</span>
              </div>
            )}
            {topazMetadata.estimatedFrames !== null && topazMetadata.estimatedFrames !== undefined && (
              <div>
                <span className="text-slate-600">Frames:</span>{' '}
                <span className="font-medium">{String(topazMetadata.estimatedFrames)}</span>
              </div>
            )}
            {topazMetadata.estimatedDuration !== null && topazMetadata.estimatedDuration !== undefined && (
              <div>
                <span className="text-slate-600">Duration:</span>{' '}
                <span className="font-medium">{String(topazMetadata.estimatedDuration)}s</span>
              </div>
            )}
            {topazMetadata.inputFormat !== null && topazMetadata.inputFormat !== undefined && (
              <div>
                <span className="text-slate-600">Format:</span>{' '}
                <span className="font-medium">{String(topazMetadata.inputFormat)}</span>
              </div>
            )}
          </div>
          {topazMetadata.recommendations !== null && topazMetadata.recommendations !== undefined && (
            <div className="mt-3 pt-3 border-t border-slate-200">
              <h4 className="text-sm font-semibold mb-2">Recommendations</h4>
              <pre className="text-xs text-slate-700 overflow-auto">
                {JSON.stringify(topazMetadata.recommendations, null, 2)}
              </pre>
            </div>
          )}
          {/* Debug: Show all metadata */}
          <details className="mt-3 pt-3 border-t border-slate-200">
            <summary className="text-xs cursor-pointer text-slate-500">Show all metadata</summary>
            <pre className="text-xs text-slate-700 overflow-auto mt-2">
              {JSON.stringify(topazMetadata, null, 2)}
            </pre>
          </details>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left side - Video preview and upload */}
        <div>
          <div className="aspect-video bg-slate-100 rounded-lg mb-4 overflow-hidden">
            {selectedFile && !processedVideo && (
              <video
                id={videoPreviewId}
                src={URL.createObjectURL(selectedFile)}
                className="w-full h-full object-contain"
                controls
                aria-label="Video preview"
              />
            )}
            {processedVideo && (
              <div className="relative">
                <VideoPlayer
                  src={processedVideo}
                  className="w-full"
                />
              </div>
            )}
            {!selectedFile && !processedVideo && (
              <div className="h-full flex items-center justify-center">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="p-4 text-slate-500 hover:text-slate-700"
                >
                  Click or drop video file here
                </button>
              </div>
            )}
          </div>
          
                    <label htmlFor="video-upload" className="sr-only">
            Upload video file
          </label>
          <input
            ref={fileInputRef}
            id="video-upload"
            name="video-upload"
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            className="hidden"
            aria-label="Upload video file"
          />

          {selectedFile && (
            <div className="space-y-4">
              <p className="text-sm text-slate-600">
                Selected: {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
              
              <Button
                onClick={handleUploadAndProcess}
                disabled={processing}
                className="w-full"
              >
                {processing ? (
                  <>
                    Processing... {progress.toFixed(0)}%
                    <div className="ml-2 h-1 w-24 bg-white/20 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-white"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </>
                ) : (
                  'Process with Topaz'
                )}
              </Button>
            </div>
          )}
        </div>

        {/* Right side - Topaz settings */}
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Enhancement Model</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                'prob-4',   // Proteus
                'ahq-12',   // Artemis HQ
                'amq-13',   // Artemis MQ
                'alq-13',   // Artemis LQ
                'nyx-3',    // Nyx
                'nxf-1',    // Nyx Fast
                'rhea-1',   // Rhea
                'ghq-5',    // Gaia HQ
                'gcg-5',    // Gaia CG
                'apo-8',    // Apollo
                'apf-2',    // Apollo Fast
                'chr-2',    // Chronos
                'chf-3',    // Chronos Fast
                'ddv-3',    // Dione DV
                'dtd-4',    // Dione Robust
                'dtds-2',   // Dione Robust Dehalo
                'dtv-4',    // Dione TV
                'dtvs-2',   // Dione Halo
                'alqs-2',   // Artemis Strong Halo
                'amqs-2',   // Artemis Dehalo
                'aaa-9',    // Artemis Aliased
                'thd-3',    // Theia Detail
                'thf-4',    // Theia Fidelity
                'iris-3',   // Iris
                'thm-2'     // Themis
              ].map((model) => (
                <button
                  key={model}
                  onClick={() => handleModelChange(model as TopazModel)}
                  className={`p-4 rounded-lg border ${
                    settings.filters[0].model === model
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="font-medium">{model}</div>
                  <div className="text-sm text-slate-500">
                    {getModelDescription(model)}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Output Settings</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Resolution
                </label>
                <select
                  value={`${settings.outputResolution.width}x${settings.outputResolution.height}`}
                  onChange={(e) => {
                    const [width, height] = e.target.value.split('x').map(Number);
                    setSettings(prev => ({
                      ...prev,
                      outputResolution: { width, height }
                    }));
                  }}
                  className="w-full rounded-md border-slate-200"
                >
                  <option value="1920x1080">1080p (1920x1080)</option>
                  <option value="2560x1440">1440p (2560x1440)</option>
                  <option value="3840x2160">4K (3840x2160)</option>
                </select>
              </div>

              {costEstimate && (
                <div className="p-4 bg-slate-50 rounded-lg space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-medium text-slate-900">Estimated Cost</h3>
                    <span className="text-lg font-semibold text-slate-900">
                      ${costEstimate.estimatedCost}
                    </span>
                  </div>
                  
                  {costEstimate.metadata && (
                    <div className="text-sm text-slate-600">
                      <div>Duration: {Math.round(costEstimate.metadata.duration / 60)} minutes</div>
                      <div>Resolution: {costEstimate.metadata.width}x{costEstimate.metadata.height}</div>
                      <div>Frame Rate: {Math.round(costEstimate.metadata.frameRate)} fps</div>
                    </div>
                  )}

                  {costEstimate.recommendations && (
                    <div className="mt-3 border-t border-slate-200 pt-3">
                      <h4 className="text-sm font-medium text-slate-900 mb-2">Topaz Recommendations</h4>
                      <div className="space-y-2 text-sm text-slate-600">
                        <div>Suggested Model: {costEstimate.recommendations.suggestedModel}</div>
                        {costEstimate.recommendations.suggestedSettings && (
                          <div className="space-y-1">
                            {costEstimate.recommendations.suggestedSettings.denoiseLevel !== undefined && (
                              <div>Denoise Level: {costEstimate.recommendations.suggestedSettings.denoiseLevel}</div>
                            )}
                            {costEstimate.recommendations.suggestedSettings.sharpness !== undefined && (
                              <div>Sharpness: {costEstimate.recommendations.suggestedSettings.sharpness}</div>
                            )}
                            {costEstimate.recommendations.suggestedSettings.stabilization !== undefined && (
                              <div>Stabilization: {costEstimate.recommendations.suggestedSettings.stabilization ? 'Recommended' : 'Not Needed'}</div>
                            )}
                          </div>
                        )}
                        {costEstimate.recommendations.performanceEstimate && (
                          <div className="mt-2">
                            <div>Est. Processing Time: {Math.round(costEstimate.recommendations.performanceEstimate.processingTime / 60)} minutes</div>
                            <div>GPU Memory Required: {Math.round(costEstimate.recommendations.performanceEstimate.gpuMemoryRequired / 1024)} GB</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Frame Rate
                </label>
                <select
                  value={settings.outputFrameRate}
                  onChange={(e) => {
                    setSettings(prev => ({
                      ...prev,
                      outputFrameRate: Number(e.target.value)
                    }));
                  }}
                  className="w-full rounded-md border-slate-200"
                >
                  <option value="24">24 fps</option>
                  <option value="30">30 fps</option>
                  <option value="60">60 fps</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Compression Level
                </label>
                <select
                  value={settings.dynamicCompressionLevel}
                  onChange={(e) => {
                    setSettings(prev => ({
                      ...prev,
                      dynamicCompressionLevel: e.target.value as TopazSettings['dynamicCompressionLevel']
                    }));
                  }}
                  className="w-full rounded-md border-slate-200"
                >
                  <option value="None">None</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Enhancement Settings</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Denoise Level
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.filters[0].denoiseLevel}
                  onChange={(e) => {
                    setSettings(prev => ({
                      ...prev,
                      filters: [{
                        ...prev.filters[0],
                        denoiseLevel: Number(e.target.value)
                      }]
                    }));
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500">
                  <span>None</span>
                  <span>Max</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Sharpness
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.filters[0].sharpness}
                  onChange={(e) => {
                    setSettings(prev => ({
                      ...prev,
                      filters: [{
                        ...prev.filters[0],
                        sharpness: Number(e.target.value)
                      }]
                    }));
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Soft</span>
                  <span>Sharp</span>
                </div>
              </div>

              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.filters[0].stabilization}
                    onChange={(e) => {
                      setSettings(prev => ({
                        ...prev,
                        filters: [{
                          ...prev.filters[0],
                          stabilization: e.target.checked
                        }]
                      }));
                    }}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm font-medium text-slate-700">
                    Enable Video Stabilization
                  </span>
                </label>
              </div>

              {/* Slowmo control - only for frame interpolation models */}
              {['apo-8', 'apf-2', 'chr-2', 'chf-3'].includes(settings.filters[0].model) && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Slow Motion Factor
                    <span className="text-xs text-slate-500 ml-2">
                      ({settings.filters[0].slowmo || 1}x slower)
                    </span>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="8"
                    step="0.5"
                    value={settings.filters[0].slowmo || 1}
                    onChange={(e) => {
                      setSettings(prev => ({
                        ...prev,
                        filters: [{
                          ...prev.filters[0],
                          slowmo: Number(e.target.value)
                        }]
                      }));
                    }}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>1x (Normal)</span>
                    <span>8x (Ultra Slow)</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Frame interpolation will create smoother slow-motion by generating intermediate frames
                  </p>
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Color Grading</h3>
            
            <div className="space-y-4">
              {['brightness', 'contrast', 'saturation', 'temperature', 'tint'].map((param) => (
                <div key={param}>
                  <label className="block text-sm font-medium text-slate-700 mb-1 capitalize">
                    {param}
                  </label>
                  <input
                    type="range"
                    min="-1"
                    max="1"
                    step="0.1"
                    value={settings.filters[0].colorGrading?.[param as 'brightness' | 'contrast' | 'saturation' | 'temperature' | 'tint'] ?? 0}
                    onChange={(e) => {
                      setSettings(prev => ({
                        ...prev,
                        filters: [{
                          ...prev.filters[0],
                          colorGrading: {
                            ...prev.filters[0].colorGrading!,
                            [param]: Number(e.target.value)
                          }
                        }]
                      }));
                    }}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>-100%</span>
                    <span>+100%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getModelDescription(model: string): string {
  switch (model) {
    // Enhancement Models
    case 'prob-4':
      return 'Proteus - Best for most videos';
    case 'ahq-12':
      return 'Artemis High Quality - Denoise & sharpen';
    case 'amq-13':
      return 'Artemis Medium Quality';
    case 'alq-13':
      return 'Artemis Low Quality';
    case 'nyx-3':
      return 'Nyx - Dedicated for denoise';
    case 'nxf-1':
      return 'Nyx Fast';
    case 'rhea-1':
      return 'Rhea - Advanced 4x upscaling';
    case 'ghq-5':
      return 'Gaia HQ - Best for GenAI/CG/Animation';
    case 'gcg-5':
      return 'Gaia - Computer Generated';
    // Frame Interpolation
    case 'apo-8':
      return 'Apollo - Best overall, up to 8x slowmo';
    case 'apf-2':
      return 'Apollo Fast';
    case 'chr-2':
      return 'Chronos - General framerate conversions';
    case 'chf-3':
      return 'Chronos Fast';
    // Advanced Enhancement
    case 'ddv-3':
      return 'Dione - DV Footage';
    case 'dtd-4':
      return 'Dione - Robust';
    case 'dtds-2':
      return 'Dione - Robust Dehalo';
    case 'dtv-4':
      return 'Dione - TV';
    case 'dtvs-2':
      return 'Dione - Halo';
    case 'alqs-2':
      return 'Artemis - Strong Halo';
    case 'amqs-2':
      return 'Artemis - Dehalo';
    case 'aaa-9':
      return 'Artemis - Aliased & Moire';
    case 'thd-3':
      return 'Theia - Detail (High fidelity)';
    case 'thf-4':
      return 'Theia - Fidelity';
    case 'iris-3':
      return 'Iris - Specialized for faces';
    case 'thm-2':
      return 'Themis - Motion deblur';
    default:
      return '';
  }
}