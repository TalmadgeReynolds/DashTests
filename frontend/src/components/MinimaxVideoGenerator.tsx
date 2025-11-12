/**
 * MinimaxVideoGenerator
 * Comprehensive component for MiniMax Hailuo 2.3 video generation
 * Supports all 4 generation modes: T2V, I2V, FL2V, S2V
 */
import { useState } from 'react';
import {
  VideoCameraIcon,
  PhotoIcon,
  ArrowPathIcon,
  SparklesIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import PromptSharpenerModal from './PromptSharpenerModal';

// Types
type GenerationMode = 't2v' | 'i2v' | 'fl2v' | 's2v';
type MinimaxModel = 'MiniMax-Hailuo-2.3' | 'MiniMax-Hailuo-2.3-Fast' | 'MiniMax-Hailuo-02';
type AspectRatio = '16:9' | '9:16' | '1:1' | '4:3' | '3:4' | '21:9' | '9:21';
type TaskStatus = 'queued' | 'processing' | 'success' | 'failed';

interface GenerationTask {
  taskId: string;
  mode: GenerationMode;
  status: TaskStatus;
  progress?: number;
  videoUrl?: string;
  error?: string;
}

interface MinimaxVideoGeneratorProps {
  onVideoGenerated?: (videoUrl: string, taskId: string) => void;
  defaultMode?: GenerationMode;
}

export default function MinimaxVideoGenerator({
  onVideoGenerated,
  defaultMode = 't2v',
}: MinimaxVideoGeneratorProps) {
  // State
  const [mode, setMode] = useState<GenerationMode>(defaultMode);
  const [model, setModel] = useState<MinimaxModel>('MiniMax-Hailuo-2.3');
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('16:9');
  const [duration, setDuration] = useState(6);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [promptOptimizer, setPromptOptimizer] = useState(true);
  const [showSharpenerModal, setShowSharpenerModal] = useState(false);
  
  // Image inputs
  const [firstFrameImage, setFirstFrameImage] = useState<string>('');
  const [lastFrameImage, setLastFrameImage] = useState<string>('');
  const [referenceImage, setReferenceImage] = useState<string>('');
  const [referenceType, setReferenceType] = useState<'character' | 'style'>('character');
  
  // Task tracking
  const [currentTask, setCurrentTask] = useState<GenerationTask | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [recentTasks, setRecentTasks] = useState<GenerationTask[]>([]);

  // File to base64 converter
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  // Handle file upload
  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    setter: (value: string) => void
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        const base64 = await fileToBase64(file);
        setter(base64);
      } catch (error) {
        console.error('Error converting file to base64:', error);
      }
    }
  };

  // Generate video
  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt');
      return;
    }

    // Validate inputs based on mode
    if (mode === 'i2v' && !firstFrameImage) {
      alert('Please upload a first frame image for Image-to-Video mode');
      return;
    }
    if (mode === 'fl2v' && (!firstFrameImage || !lastFrameImage)) {
      alert('Please upload both first and last frame images for FL2V mode');
      return;
    }
    if (mode === 's2v' && !referenceImage) {
      alert('Please upload a reference image for Subject Reference mode');
      return;
    }

    setIsGenerating(true);

    try {
      // Build request based on mode
      let endpoint = '';
      const payload: Record<string, unknown> = {
        prompt,
        model,
        aspect_ratio: aspectRatio,
        duration_seconds: duration,
        prompt_optimizer: promptOptimizer,
      };

      if (seed !== undefined) {
        payload.seed = seed;
      }

      switch (mode) {
        case 't2v':
          endpoint = '/api/v1/minimax/generate/text-to-video';
          break;
        case 'i2v':
          endpoint = '/api/v1/minimax/generate/image-to-video';
          payload.first_frame_image = firstFrameImage;
          break;
        case 'fl2v':
          endpoint = '/api/v1/minimax/generate/first-last-frame';
          payload.first_frame_image = firstFrameImage;
          payload.last_frame_image = lastFrameImage;
          break;
        case 's2v':
          endpoint = '/api/v1/minimax/generate/subject-reference';
          payload.reference_image = referenceImage;
          payload.reference_type = referenceType;
          break;
      }

      // Create task
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Generation failed: ${response.statusText}`);
      }

      const result = await response.json();
      const taskId = result.task_id;

      // Initialize task tracking
      const task: GenerationTask = {
        taskId,
        mode,
        status: 'queued',
        progress: 0,
      };

      setCurrentTask(task);
      setRecentTasks(prev => [task, ...prev.slice(0, 9)]);

      // Start polling
      pollTaskStatus(taskId);

    } catch (error) {
      console.error('Generation error:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsGenerating(false);
    }
  };

  // Poll task status
  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 60; // 5 minutes with 5s intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/v1/minimax/task/${taskId}/status`);
        if (!response.ok) {
          throw new Error('Failed to get status');
        }

        const status = await response.json();
        
        // Update task
        setCurrentTask(prev => prev ? {
          ...prev,
          status: status.status,
          progress: status.progress || prev.progress,
          error: status.error,
        } : null);

        // Update recent tasks
        setRecentTasks(prev => prev.map(t => 
          t.taskId === taskId ? { ...t, status: status.status, progress: status.progress } : t
        ));

        if (status.status === 'success') {
          // Download and store video
          await downloadVideo(taskId);
          setIsGenerating(false);
          return;
        }

        if (status.status === 'failed') {
          setIsGenerating(false);
          alert(`Generation failed: ${status.error || 'Unknown error'}`);
          return;
        }

        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setIsGenerating(false);
          alert('Polling timeout - please check task status manually');
        }

      } catch (error) {
        console.error('Polling error:', error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setIsGenerating(false);
        }
      }
    };

    poll();
  };

  // Download video
  const downloadVideo = async (taskId: string) => {
    try {
      const response = await fetch(`/api/v1/minimax/task/${taskId}/download`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to download video');
      }

      const result = await response.json();
      
      // Update task with video URL
      setCurrentTask(prev => prev ? { ...prev, videoUrl: result.video_url } : null);
      setRecentTasks(prev => prev.map(t => 
        t.taskId === taskId ? { ...t, videoUrl: result.video_url } : t
      ));

      // Callback
      if (onVideoGenerated) {
        onVideoGenerated(result.video_url, taskId);
      }

    } catch (error) {
      console.error('Download error:', error);
      alert(`Error downloading video: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Mode info
  const modeInfo = {
    t2v: {
      title: 'Text to Video',
      description: 'Generate videos from text descriptions',
      icon: VideoCameraIcon,
    },
    i2v: {
      title: 'Image to Video',
      description: 'Animate static images into videos',
      icon: PhotoIcon,
    },
    fl2v: {
      title: 'First/Last Frame',
      description: 'Interpolate between two keyframes',
      icon: ArrowPathIcon,
    },
    s2v: {
      title: 'Subject Reference',
      description: 'Maintain character/style consistency',
      icon: SparklesIcon,
    },
  };

  const currentModeInfo = modeInfo[mode];
  const ModeIcon = currentModeInfo.icon;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          MiniMax Hailuo 2.3 Video Generator
        </h1>
        <p className="text-gray-600">
          Advanced AI video generation with multiple modes
        </p>
      </div>

      {/* Mode Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Generation Mode</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {(Object.keys(modeInfo) as GenerationMode[]).map((m) => {
            const info = modeInfo[m];
            const Icon = info.icon;
            return (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  mode === m
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Icon className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                <div className="font-medium text-sm">{info.title}</div>
                <div className="text-xs text-gray-500 mt-1">{info.description}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <ModeIcon className="h-5 w-5 text-blue-500" />
          {currentModeInfo.title} Configuration
        </h2>

        {/* Prompt */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Prompt *
            </label>
            <button
              type="button"
              onClick={() => setShowSharpenerModal(true)}
              className="inline-flex items-center gap-1 px-3 py-1 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors"
            >
              <SparklesIcon className="w-4 h-4" />
              Enhance Prompt
            </button>
          </div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={`Describe the video you want to generate...`}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
          />
          <p className="text-xs text-gray-500 mt-1">
            Use "Enhance Prompt" to expand and improve your description with AI
          </p>
        </div>

        {/* Image uploads based on mode */}
        {mode === 'i2v' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              First Frame Image *
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleFileUpload(e, setFirstFrameImage)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {firstFrameImage && (
              <img src={firstFrameImage} alt="First frame" className="mt-2 h-32 rounded" />
            )}
          </div>
        )}

        {mode === 'fl2v' && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                First Frame *
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileUpload(e, setFirstFrameImage)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {firstFrameImage && (
                <img src={firstFrameImage} alt="First frame" className="mt-2 h-32 rounded" />
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Last Frame *
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleFileUpload(e, setLastFrameImage)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              {lastFrameImage && (
                <img src={lastFrameImage} alt="Last frame" className="mt-2 h-32 rounded" />
              )}
            </div>
          </div>
        )}

        {mode === 's2v' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Image *
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleFileUpload(e, setReferenceImage)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {referenceImage && (
              <img src={referenceImage} alt="Reference" className="mt-2 h-32 rounded" />
            )}
            <div className="mt-2">
              <label className="inline-flex items-center mr-4">
                <input
                  type="radio"
                  value="character"
                  checked={referenceType === 'character'}
                  onChange={(e) => setReferenceType(e.target.value as 'character')}
                  className="form-radio"
                />
                <span className="ml-2">Character</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  value="style"
                  checked={referenceType === 'style'}
                  onChange={(e) => setReferenceType(e.target.value as 'style')}
                  className="form-radio"
                />
                <span className="ml-2">Style</span>
              </label>
            </div>
          </div>
        )}

        {/* Model selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value as MinimaxModel)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="MiniMax-Hailuo-2.3">Hailuo 2.3 (Best Quality)</option>
              <option value="MiniMax-Hailuo-2.3-Fast">Hailuo 2.3-Fast (Speed)</option>
              <option value="MiniMax-Hailuo-02">Hailuo 02 (1080p, 10s)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Aspect Ratio
            </label>
            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value as AspectRatio)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="16:9">16:9 (Widescreen)</option>
              <option value="9:16">9:16 (Vertical)</option>
              <option value="1:1">1:1 (Square)</option>
              <option value="4:3">4:3 (Standard)</option>
              <option value="3:4">3:4 (Portrait)</option>
              <option value="21:9">21:9 (Ultrawide)</option>
              <option value="9:21">9:21 (Ultra Vertical)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Duration (seconds)
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              min={2}
              max={model === 'MiniMax-Hailuo-02' ? 10 : 6}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Advanced options */}
        <div className="flex items-center justify-between pt-4 border-t">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={promptOptimizer}
              onChange={(e) => setPromptOptimizer(e.target.checked)}
              className="form-checkbox h-5 w-5 text-blue-600"
            />
            <div className="ml-2">
              <span className="text-sm text-gray-700">Enable Prompt Optimizer</span>
              <p className="text-xs text-gray-500">MiniMax's built-in enhancement (recommended)</p>
            </div>
          </label>

          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-700">Seed (optional):</label>
            <input
              type="number"
              value={seed || ''}
              onChange={(e) => setSeed(e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="Random"
              className="w-32 px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
            isGenerating
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
          }`}
        >
          {isGenerating ? (
            <span className="flex items-center justify-center gap-2">
              <ArrowPathIcon className="h-5 w-5 animate-spin" />
              Generating...
            </span>
          ) : (
            'Generate Video'
          )}
        </button>
      </div>

      {/* Current Task Status */}
      {currentTask && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Current Task</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Task ID:</span>
              <span className="font-mono text-sm">{currentTask.taskId}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <div className="flex items-center gap-2">
                {currentTask.status === 'success' && (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                )}
                {currentTask.status === 'failed' && (
                  <XCircleIcon className="h-5 w-5 text-red-500" />
                )}
                {(currentTask.status === 'queued' || currentTask.status === 'processing') && (
                  <ClockIcon className="h-5 w-5 text-yellow-500 animate-pulse" />
                )}
                <span className="capitalize">{currentTask.status}</span>
              </div>
            </div>
            {currentTask.progress !== undefined && (
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{currentTask.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${currentTask.progress}%` }}
                  />
                </div>
              </div>
            )}
            {currentTask.videoUrl && (
              <div className="pt-4 border-t">
                <video
                  src={currentTask.videoUrl}
                  controls
                  className="w-full rounded-lg"
                />
                <a
                  href={currentTask.videoUrl}
                  download
                  className="mt-2 inline-block text-blue-600 hover:underline"
                >
                  Download Video
                </a>
              </div>
            )}
            {currentTask.error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded">
                {currentTask.error}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recent Tasks */}
      {recentTasks.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Tasks</h2>
          <div className="space-y-2">
            {recentTasks.map((task) => (
              <div
                key={task.taskId}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <div className="font-mono text-sm">{task.taskId}</div>
                  <div className="text-xs text-gray-500 capitalize">
                    {modeInfo[task.mode].title}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {task.status === 'success' && (
                    <CheckCircleIcon className="h-5 w-5 text-green-500" />
                  )}
                  {task.status === 'failed' && (
                    <XCircleIcon className="h-5 w-5 text-red-500" />
                  )}
                  {(task.status === 'queued' || task.status === 'processing') && (
                    <ClockIcon className="h-5 w-5 text-yellow-500" />
                  )}
                  <span className="text-sm capitalize">{task.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompt Sharpener Modal */}
      <PromptSharpenerModal
        isOpen={showSharpenerModal}
        onClose={() => setShowSharpenerModal(false)}
        initialPrompt={prompt}
        onApplyVariant={(text) => {
          setPrompt(text);
          setShowSharpenerModal(false);
        }}
      />
    </div>
  );
}
