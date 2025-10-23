import { useState, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { VideoPlayer } from '@/components/video/VideoPlayer';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api-client';

import type { TopazModel } from '@/types';

interface TopazSettings {
  // Source settings
  inputResolution: { width: number; height: number };
  frameRate: number;
  
  // Output settings
  outputResolution: { width: number; height: number };
  outputFrameRate: number;
  audioCodec: 'AAC' | 'Copy';
  audioTransfer: 'Copy' | 'PassThrough';
  dynamicCompressionLevel: 'None' | 'Low' | 'Medium' | 'High';
  container: 'mp4' | 'mov';

  // Enhancement filters
  filters: Array<{
    model: 'apo-8' | 'chronos' | 'proteus' | 'dione' | 'artemis' | 'gaia';
    slowmo?: number;
    denoiseLevel?: number;
    sharpness?: number;
    stabilization?: boolean;
    colorGrading?: {
      brightness: number;
      contrast: number;
      saturation: number;
      temperature: number;
      tint: number;
    };
  }>;
}

const defaultSettings: TopazSettings = {
  inputResolution: { width: 1920, height: 1080 },
  frameRate: 30,
  outputResolution: { width: 1920, height: 1080 },
  outputFrameRate: 30,
  audioCodec: 'AAC',
  audioTransfer: 'Copy',
  dynamicCompressionLevel: 'Medium',
  container: 'mp4',
  filters: [{
    model: 'apo-8',
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

  const [processedVideo, setProcessedVideo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      // Get presigned URL
      const { uploadUrl, videoKey } = await apiClient.getVideoUploadUrl();
      
      // Upload with progress tracking
      const xhr = new XMLHttpRequest();
      await new Promise((resolve, reject) => {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            setProgress((event.loaded / event.total) * 100);
          }
        };
        
        xhr.onload = () => resolve(xhr.response);
        xhr.onerror = () => reject(xhr.statusText);
        
        xhr.open('PUT', uploadUrl);
        xhr.send(file);
      });

      return videoKey;
    }
  });

  const processMutation = useMutation({
    mutationFn: async ({ videoKey, settings }: { videoKey: string; settings: TopazSettings }) => {
      const response = await apiClient.processVideo(videoKey, settings);
      return response.jobId;
    }
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 1024 * 1024 * 1024) { // 1GB
        alert('File size must be less than 1GB');
        return;
      }
      setSelectedFile(file);
      
      // Update input resolution and frame rate based on the selected video
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        setSettings(prev => ({
          ...prev,
          inputResolution: {
            width: video.videoWidth,
            height: video.videoHeight
          },
          frameRate: video.videoHeight
        }));
      };
      video.src = URL.createObjectURL(file);
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
    if (!selectedFile) return;
    
    try {
      setProcessing(true);
      
      // Upload file
      const videoKey = await uploadMutation.mutateAsync(selectedFile);
      
      // Process with Topaz
      const processedVideoUrl = await processMutation.mutateAsync({
        videoKey,
        settings
      });
      
      setProcessedVideo(processedVideoUrl);
    } catch (error) {
      console.error('Error processing video:', error);
      alert('Error processing video. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  // Get cost estimate when settings change
  const { data: estimatedCost } = useQuery({
    queryKey: ['costEstimate', settings],
    queryFn: () => apiClient.getProcessingCostEstimate(settings),
    enabled: !!selectedFile
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Video Enhancement</h1>
        {estimatedCost && (
          <div className="text-slate-600">
            Estimated Cost: ${estimatedCost.toFixed(2)}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left side - Video preview and upload */}
        <div>
          <div className="aspect-video bg-slate-100 rounded-lg mb-4 overflow-hidden">
            {selectedFile && !processedVideo && (
              <video
                src={URL.createObjectURL(selectedFile)}
                className="w-full h-full object-contain"
                controls
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
          
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            className="hidden"
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
              {['apo-8', 'chronos', 'proteus', 'dione', 'artemis', 'gaia'].map((model) => (
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
    case 'apo-8':
      return 'General purpose enhancement and upscaling';
    case 'chronos':
      return 'Frame interpolation and slow motion';
    case 'proteus':
      return 'Noise reduction and detail preservation';
    case 'dione':
      return 'Advanced stabilization and motion smoothing';
    case 'artemis':
      return 'Color grading and HDR optimization';
    case 'gaia':
      return 'AI-powered scene optimization';
    default:
      return '';
  }
}