/**
 * Composer page - Create new lip-sync jobs
 * Supports two workflows:
 * - Option 1: Prompt → Lip-Sync (VEO 3)
 * - Option 2: Avatar + Audio → Lip-Sync (Heygen Photo Avatar + ElevenLabs)
 */
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createPromptJob, createAudioJob, getPresignedUrl, uploadToPresignedUrl } from '@/lib/job-api';
import { generatePortrait } from '@/lib/imagen-api';
import { voiceApi } from '@/lib/voice-api';
import type { CreatePromptJobRequest, CreateAudioJobRequest } from '@/types/job';
import { SparklesIcon, ArrowPathIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { AvatarSelector } from '@/components/AvatarSelector';

type WorkflowOption = 'prompt' | 'audio';

export default function Composer() {
  const navigate = useNavigate();
  const location = useLocation();
  const [workflow, setWorkflow] = useState<WorkflowOption>('prompt');
  
  // Get pre-filled prompt from location state (from screenplay selection)
  const prefilledPrompt = location.state?.prompt || '';

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Create New Job</h1>
      <p className="text-gray-600 mb-8">Generate AI-powered lip-sync videos</p>

      {/* Workflow Selection Tabs */}
      <div className="flex gap-4 mb-8 border-b border-gray-200">
        <button
          onClick={() => setWorkflow('prompt')}
          className={`px-6 py-3 font-medium border-b-2 transition-colors ${
            workflow === 'prompt'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Option 1: Prompt → Video
          <span className="block text-xs mt-1">VEO 3 Text-to-Video</span>
        </button>
        <button
          onClick={() => setWorkflow('audio')}
          className={`px-6 py-3 font-medium border-b-2 transition-colors ${
            workflow === 'audio'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          Option 2: Avatar + Audio
          <span className="block text-xs mt-1">Heygen Photo Avatar + ElevenLabs</span>
        </button>
      </div>

      {/* Workflow Forms */}
      {workflow === 'prompt' && <Option1Form initialPrompt={prefilledPrompt} onSuccess={(jobId) => navigate(`/jobs/${jobId}`)} />}
      {workflow === 'audio' && <Option2Form onSuccess={(jobId) => navigate(`/jobs/${jobId}`)} />}
    </div>
  );
}

// Option 1: Prompt → Lip-Sync (VEO 3)
function Option1Form({ initialPrompt, onSuccess }: { initialPrompt: string; onSuccess: (jobId: string) => void }) {
  const [script, setScript] = useState(initialPrompt);
  const [imageSource, setImageSource] = useState<'upload' | 'generate'>('upload');
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referenceImageUrl, setReferenceImageUrl] = useState('');
  const [portraitPrompt, setPortraitPrompt] = useState('');
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [fps, setFps] = useState<24 | 30>(24);
  const [aspect, setAspect] = useState<'16:9' | '9:16' | '1:1'>('16:9');
  const [interpolate, setInterpolate] = useState(true);
  const [upscale, setUpscale] = useState(false);
  const [priority, setPriority] = useState<'high' | 'low'>('low');

  const createJobMutation = useMutation({
    mutationFn: async (data: CreatePromptJobRequest) => {
      return createPromptJob(data);
    },
    onSuccess: (data) => {
      onSuccess(data.job_id);
    },
  });

  const handleImageUpload = async (file: File) => {
    try {
      // Get presigned URL
      const { uploadUrl, fileUrl } = await getPresignedUrl({
        filename: file.name,
        mime: file.type,
        kind: 'IMAGE',
        content_length: file.size,
      });
      
      // Upload file
      await uploadToPresignedUrl(uploadUrl, file);
      setReferenceImageUrl(fileUrl);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload image');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (script.length < 8 || script.length > 500) {
      alert('Script must be between 8 and 500 characters');
      return;
    }

    // Upload image if provided
    if (referenceImage && !referenceImageUrl) {
      await handleImageUpload(referenceImage);
    }

    const data: CreatePromptJobRequest = {
      script,
      reference_image_url: referenceImageUrl || undefined,
      post: {
        interpolate,
        upscale,
      },
      video: {
        fps,
        aspect,
        max_duration: 12,
      },
      priority,
    };

    createJobMutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Script Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Script <span className="text-red-500">*</span>
          <span className="text-xs text-gray-500 ml-2">({script.length}/500 characters)</span>
        </label>
        <textarea
          value={script}
          onChange={(e) => setScript(e.target.value)}
          placeholder="Enter the dialogue or narration for your video..."
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          required
          minLength={8}
          maxLength={500}
        />
        <p className="text-xs text-gray-500 mt-1">
          The AI will generate a video with a speaking character based on this script
        </p>
      </div>

      {/* Reference Image - Upload or Generate */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          Reference Image (Optional)
        </label>
        
        {/* Image Source Toggle */}
        <div className="flex gap-4 mb-4">
          <button
            type="button"
            onClick={() => setImageSource('upload')}
            className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors ${
              imageSource === 'upload'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:border-gray-400'
            }`}
          >
            Upload Image
          </button>
          <button
            type="button"
            onClick={() => setImageSource('generate')}
            className={`flex-1 px-4 py-2 rounded-lg border-2 transition-colors flex items-center justify-center gap-2 ${
              imageSource === 'generate'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:border-gray-400'
            }`}
          >
            <SparklesIcon className="w-5 h-5" />
            Generate with AI
          </button>
        </div>

        {imageSource === 'upload' ? (
          <div>
            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  setReferenceImage(file);
                  setReferenceImageUrl('');
                }
              }}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-gray-500 mt-1">
              Upload a reference image to guide the AI character generation
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <input
                type="text"
                value={portraitPrompt}
                onChange={(e) => setPortraitPrompt(e.target.value)}
                placeholder="e.g., professional man in a suit, serious expression"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Describe the character you want to generate
              </p>
            </div>
            <button
              type="button"
              onClick={async () => {
                if (!portraitPrompt.trim()) {
                  alert('Please enter a description');
                  return;
                }
                setIsGeneratingImage(true);
                try {
                  const result = await generatePortrait({
                    description: portraitPrompt,
                    style: 'photorealistic',
                    aspect_ratio: '1:1',
                  });
                  setReferenceImageUrl(result.image_url);
                  setReferenceImage(null);
                  alert('Reference image generated successfully!');
                } catch (error) {
                  console.error('Failed to generate image:', error);
                  alert('Failed to generate image. Please try again.');
                } finally {
                  setIsGeneratingImage(false);
                }
              }}
              disabled={isGeneratingImage || !portraitPrompt.trim()}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isGeneratingImage ? (
                <>
                  <ArrowPathIcon className="w-5 h-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  Generate Image
                </>
              )}
            </button>
          </div>
        )}
        
        {/* Show preview if image URL exists */}
        {referenceImageUrl && (
          <div className="mt-3">
            <img
              src={referenceImageUrl}
              alt="Reference"
              className="max-w-xs rounded-lg border border-gray-300"
            />
            <p className="text-xs text-gray-500 mt-1">✓ Reference image ready</p>
          </div>
        )}
      </div>

      {/* Video Options */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">FPS</label>
          <select
            value={fps}
            onChange={(e) => setFps(parseInt(e.target.value) as 24 | 30)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={24}>24 fps</option>
            <option value={30}>30 fps</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Aspect Ratio</label>
          <select
            value={aspect}
            onChange={(e) => setAspect(e.target.value as '16:9' | '9:16' | '1:1')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="16:9">16:9 (Landscape)</option>
            <option value="9:16">9:16 (Portrait/Shorts)</option>
            <option value="1:1">1:1 (Square)</option>
          </select>
        </div>
      </div>

      {/* Post-Processing */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Post-Processing Enhancement</label>
        <div className="bg-gray-50 p-3 rounded-lg space-y-3">
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="interpolate1"
              checked={interpolate}
              onChange={(e) => setInterpolate(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
            />
            <div className="flex-1">
              <label htmlFor="interpolate1" className="text-sm font-medium text-gray-900">
                Frame Interpolation <span className="text-xs font-normal text-purple-600">(RIFE)</span>
              </label>
              <p className="text-xs text-gray-500 mt-0.5">Smooth motion, reduce wobble</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="upscale1"
              checked={upscale}
              onChange={(e) => setUpscale(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
            />
            <div className="flex-1">
              <label htmlFor="upscale1" className="text-sm font-medium text-gray-900">
                Upscale Video <span className="text-xs font-normal text-purple-600">(Topaz/Real-ESRGAN)</span>
              </label>
              <p className="text-xs text-gray-500 mt-0.5">Higher resolution, enhanced detail</p>
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-500 italic">💡 Recommended: Enable interpolation before upscaling for best results</p>
      </div>

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Processing Priority</label>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as 'high' | 'low')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="low">Low Priority (Standard)</option>
          <option value="high">High Priority (Faster)</option>
        </select>
      </div>

      {/* Submit Button */}
      <div className="flex gap-4 pt-4">
        <button
          type="submit"
          disabled={createJobMutation.isPending || script.length < 8}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {createJobMutation.isPending ? 'Creating Job...' : 'Create Prompt Job'}
        </button>
        <button
          type="button"
          onClick={() => window.history.back()}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>

      {createJobMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            {createJobMutation.error?.message || 'Failed to create job'}
          </p>
        </div>
      )}
    </form>
  );
}

// Option 2: Avatar + Audio → Lip-Sync (Heygen Photo Avatar + ElevenLabs)
function Option2Form({ onSuccess }: { onSuccess: (jobId: string) => void }) {
  // Avatar settings
  const [avatarId, setAvatarId] = useState('');
  const [actionPrompt, setActionPrompt] = useState('');
  
  // Video settings
  const [fps, setFps] = useState<24 | 30>(24);
  const [aspect, setAspect] = useState<'16:9' | '9:16' | '1:1'>('16:9');
  const [interpolate, setInterpolate] = useState(true);
  const [upscale, setUpscale] = useState(false);
  const [priority, setPriority] = useState<'high' | 'low'>('low');

  // Audio settings
  const [audioSource, setAudioSource] = useState<'upload' | 'tts'>('tts');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [ttsText, setTtsText] = useState('');
  const [voiceId, setVoiceId] = useState('');
  
  // ElevenLabs advanced settings
  const [modelId, setModelId] = useState('eleven_turbo_v2_5');
  const [outputFormat, setOutputFormat] = useState('mp3_44100_128');
  const [stability, setStability] = useState(0.65);
  const [similarityBoost, setSimilarityBoost] = useState(0.75);
  const [style, setStyle] = useState(0.0);
  const [speakerBoost, setSpeakerBoost] = useState(true);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [optimizeStreamingLatency, setOptimizeStreamingLatency] = useState(0);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [showVoiceBrowser, setShowVoiceBrowser] = useState(false);
  const [showVoiceClone, setShowVoiceClone] = useState(false);
  const [voiceSearchFilter, setVoiceSearchFilter] = useState('');
  
  // Fetch voices and models
  const { data: voicesData } = useQuery({
    queryKey: ['voices', voiceSearchFilter],
    queryFn: () => voiceApi.listVoices(voiceSearchFilter || undefined),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  const { data: modelsData } = useQuery({
    queryKey: ['models'],
    queryFn: () => voiceApi.getModels(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
  
  const { data: formatsData } = useQuery({
    queryKey: ['formats'],
    queryFn: () => voiceApi.getFormats(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
  
  const { data: subscriptionData } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => voiceApi.getSubscriptionInfo(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
  
  const voices = voicesData || [];
  const selectedVoice = voices.find((v) => v.voice_id === voiceId);

  const createJobMutation = useMutation({
    mutationFn: async (data: CreateAudioJobRequest) => {
      return createAudioJob(data);
    },
    onSuccess: (data) => {
      onSuccess(data.job_id);
    },
  });

  const handleFileUpload = async (file: File, kind: 'IMAGE' | 'AUDIO') => {
    try {
      const { uploadUrl, fileUrl } = await getPresignedUrl({
        filename: file.name,
        mime: file.type,
        kind,
        content_length: file.size,
      });
      
      await uploadToPresignedUrl(uploadUrl, file);
      return fileUrl;
    } catch (error) {
      console.error('Upload failed:', error);
      throw new Error('Failed to upload file');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Require avatar selection
      if (!avatarId) {
        alert('Please select an avatar');
        return;
      }
      
      // Upload audio if needed
      let uploadedAudioUrl = audioUrl;
      if (audioSource === 'upload' && audioFile && !audioUrl) {
        uploadedAudioUrl = await handleFileUpload(audioFile, 'AUDIO');
        setAudioUrl(uploadedAudioUrl);
      }
      
      const data: CreateAudioJobRequest = {
        avatar: {
          avatar_id: avatarId,
          provider: 'heygen',
        },
        audio_url: audioSource === 'upload' ? uploadedAudioUrl : undefined,
        tts: audioSource === 'tts' ? {
          provider: 'elevenlabs',
          text: ttsText,
          voice_id: voiceId || undefined,
          model_id: modelId,
          output_format: outputFormat,
          stability,
          similarity_boost: similarityBoost,
          style,
          speaker_boost: speakerBoost,
          seed,
          optimize_streaming_latency: optimizeStreamingLatency,
          pace: 1.0,
        } : undefined,
        action_prompt: actionPrompt || undefined,
        post: {
          interpolate,
          upscale,
        },
        video: {
          fps,
          aspect,
          max_duration: 12,
        },
        priority,
      };
      
      createJobMutation.mutate(data);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to create job');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Avatar Selector */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-gray-700">
          Photo Avatar <span className="text-red-500">*</span>
        </label>
        <AvatarSelector 
          value={avatarId} 
          onChange={setAvatarId} 
        />
        <p className="text-xs text-gray-500 mt-1">
          Photo Avatars are created from your uploaded face images and can perform more dynamic movements and expressions.
        </p>
      </div>

      {/* Action Prompt */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Action Prompt (Optional)
        </label>
        <input
          type="text"
          value={actionPrompt}
          onChange={(e) => setActionPrompt(e.target.value)}
          placeholder="e.g., 'nod head', 'smile', 'look left'"
          maxLength={120}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">
          Add subtle actions like head nods or expressions (max 120 characters)
        </p>
      </div>
      
      {/* Audio Source Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Audio Source <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-4 mb-4">
          <button
            type="button"
            onClick={() => setAudioSource('tts')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-colors ${
              audioSource === 'tts'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            🎙️ Text-to-Speech (ElevenLabs)
          </button>
          <button
            type="button"
            onClick={() => setAudioSource('upload')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-colors ${
              audioSource === 'upload'
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            📁 Upload Audio File
          </button>
        </div>

        {audioSource === 'tts' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text to Speak <span className="text-red-500">*</span>
              </label>
              <textarea
                value={ttsText}
                onChange={(e) => setTtsText(e.target.value)}
                placeholder="Enter the text you want the character to speak..."
                className="w-full h-24 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                required={audioSource === 'tts'}
                minLength={3}
              />
            </div>
            
            {/* Voice Selection with ElevenLabs Features */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700">
                Voice Selection
              </label>
              
              {/* Voice Selector Dropdown */}
              <div>
                <select
                  value={voiceId}
                  onChange={(e) => setVoiceId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a voice...</option>
                  {voices.map((voice) => (
                    <option key={voice.voice_id} value={voice.voice_id}>
                      {voice.name} {voice.labels && Object.keys(voice.labels).length > 0 ? `(${Object.values(voice.labels).join(', ')})` : ''}
                    </option>
                  ))}
                </select>
                {selectedVoice && (
                  <p className="text-xs text-gray-500 mt-1">
                    {selectedVoice.category || 'Voice'} • {selectedVoice.description || 'No description'}
                  </p>
                )}
              </div>

              {/* Voice Management Buttons */}
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowVoiceBrowser(true)}
                  className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                >
                  🎭 Browse Voices
                </button>
                <button
                  type="button"
                  onClick={() => setShowVoiceClone(true)}
                  className="flex-1 px-3 py-2 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium hover:bg-purple-200 transition-colors"
                >
                  🎙️ Clone Voice
                </button>
              </div>

              {/* Subscription Info */}
              {subscriptionData && (
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-blue-900">
                      Character Usage ({subscriptionData.tier})
                    </span>
                    <span className="text-xs text-blue-700">
                      {subscriptionData.character_count.toLocaleString()} / {subscriptionData.character_limit.toLocaleString()}
                    </span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${(subscriptionData.character_count / subscriptionData.character_limit) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AI Model
                </label>
                <select
                  value={modelId}
                  onChange={(e) => setModelId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  {modelsData && Object.entries(modelsData.models).map(([key, description]) => (
                    <option key={key} value={key}>
                      {description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Output Format */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Audio Format
                </label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  {formatsData && Object.entries(formatsData.formats).map(([key, description]) => (
                    <option key={key} value={key}>
                      {description}
                    </option>
                  ))}
                </select>
              </div>

              {/* Advanced Settings Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                className="mt-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
              >
                {showAdvancedSettings ? (
                  <>
                    <ChevronUpIcon className="inline-block w-4 h-4 mr-1" />
                    Hide Advanced Settings
                  </>
                ) : (
                  <>
                    <ChevronDownIcon className="inline-block w-4 h-4 mr-1" />
                    Show Advanced Settings
                  </>
                )}
              </button>

              {/* Advanced Settings */}
              {showAdvancedSettings && (
                <div className="space-y-3 mt-3 bg-gray-50 p-3 rounded-lg border border-gray-200">
                  {/* Stability Slider */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Stability <span className="text-xs text-gray-500">({stability})</span>
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={stability}
                      onChange={(e) => setStability(Number(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500">
                      Higher values prevent voice breaks but reduce expressiveness
                    </p>
                  </div>

                  {/* Similarity Boost Slider */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Similarity Boost <span className="text-xs text-gray-500">({similarityBoost})</span>
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={similarityBoost}
                      onChange={(e) => setSimilarityBoost(Number(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500">
                      Higher values make voice sound more like the reference
                    </p>
                  </div>

                  {/* Style Slider */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Style <span className="text-xs text-gray-500">({style})</span>
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={style}
                      onChange={(e) => setStyle(Number(e.target.value))}
                      className="w-full"
                    />
                    <p className="text-xs text-gray-500">
                      Higher values increase style transfer strength
                    </p>
                  </div>

                  {/* Speaker Boost Toggle */}
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      id="speakerBoost"
                      checked={speakerBoost}
                      onChange={(e) => setSpeakerBoost(e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
                    />
                    <div className="flex-1">
                      <label htmlFor="speakerBoost" className="text-sm font-medium text-gray-900">
                        Speaker Boost
                      </label>
                      <p className="text-xs text-gray-500">Boost similarity to speaker (recommended)</p>
                    </div>
                  </div>

                  {/* Seed Input */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Seed (Optional)
                    </label>
                    <input
                      type="number"
                      value={seed || ''}
                      onChange={(e) => setSeed(e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Random seed for reproducibility"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <p className="text-xs text-gray-500 mt-1">Set a seed for reproducible results</p>
                  </div>

                  {/* Optimize Streaming Latency */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Optimize Streaming Latency
                    </label>
                    <select
                      value={optimizeStreamingLatency}
                      onChange={(e) => setOptimizeStreamingLatency(parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                      <option value={0}>0 - Default (best quality)</option>
                      <option value={1}>1 - Slight optimization</option>
                      <option value={2}>2 - Moderate optimization</option>
                      <option value={3}>3 - Strong optimization</option>
                      <option value={4}>4 - Maximum optimization</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Higher values reduce latency but may affect quality</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {audioSource === 'upload' && (
          <div>
            <input
              type="file"
              accept="audio/mpeg,audio/wav"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setAudioFile(file);
              }}
              required={audioSource === 'upload'}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-gray-500 mt-1">
              Upload an MP3 or WAV audio file
            </p>
          </div>
        )}
      </div>

      {/* Video Options */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">FPS</label>
          <select
            value={fps}
            onChange={(e) => setFps(parseInt(e.target.value) as 24 | 30)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={24}>24 fps</option>
            <option value={30}>30 fps</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Aspect Ratio</label>
          <select
            value={aspect}
            onChange={(e) => setAspect(e.target.value as '16:9' | '9:16' | '1:1')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="16:9">16:9 (Landscape)</option>
            <option value="9:16">9:16 (Portrait/Shorts)</option>
            <option value="1:1">1:1 (Square)</option>
          </select>
        </div>
      </div>

      {/* Post-Processing */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Post-Processing Enhancement</label>
        <div className="bg-gray-50 p-3 rounded-lg space-y-3">
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="interpolate2"
              checked={interpolate}
              onChange={(e) => setInterpolate(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
            />
            <div className="flex-1">
              <label htmlFor="interpolate2" className="text-sm font-medium text-gray-900">
                Frame Interpolation <span className="text-xs font-normal text-purple-600">(RIFE)</span>
              </label>
              <p className="text-xs text-gray-500 mt-0.5">Smooth motion, reduce wobble (recommended for Heygen)</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="upscale2"
              checked={upscale}
              onChange={(e) => setUpscale(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
            />
            <div className="flex-1">
              <label htmlFor="upscale2" className="text-sm font-medium text-gray-900">
                Upscale Video <span className="text-xs font-normal text-purple-600">(Topaz/Real-ESRGAN)</span>
              </label>
              <p className="text-xs text-gray-500 mt-0.5">Higher resolution, enhanced detail</p>
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-500 italic">💡 Recommended: Enable interpolation before upscaling for best results</p>
      </div>

      {/* Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Processing Priority</label>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value as 'high' | 'low')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="low">Low Priority (Standard)</option>
          <option value="high">High Priority (Faster)</option>
        </select>
      </div>

      {/* Submit Button */}
      <div className="flex gap-4 pt-4">
        <button
          type="submit"
          disabled={
            createJobMutation.isPending || 
            !avatarId || 
            (audioSource === 'tts' ? !ttsText : !audioFile)
          }
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {createJobMutation.isPending ? 'Creating Job...' : 'Create Avatar Job'}
        </button>
        <button
          type="button"
          onClick={() => window.history.back()}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>

      {createJobMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            {createJobMutation.error?.message || 'Failed to create job'}
          </p>
        </div>
      )}

      {/* Voice Browser Modal */}
      {showVoiceBrowser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowVoiceBrowser(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Browse Voices</h2>
                <button
                  onClick={() => setShowVoiceBrowser(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              <input
                type="text"
                value={voiceSearchFilter}
                onChange={(e) => setVoiceSearchFilter(e.target.value)}
                placeholder="Search voices..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-200px)]">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {voices.map((voice) => (
                  <div
                    key={voice.voice_id}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      voiceId === voice.voice_id
                        ? 'border-blue-600 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      setVoiceId(voice.voice_id);
                      setShowVoiceBrowser(false);
                    }}
                  >
                    <div className="font-medium">{voice.name}</div>
                    <div className="text-sm text-gray-600">{voice.description || 'No description'}</div>
                    {voice.labels && Object.keys(voice.labels).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {Object.entries(voice.labels).map(([key, value]) => (
                          <span key={key} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                            {value}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Voice Clone Modal */}
      {showVoiceClone && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowVoiceClone(false)}>
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Clone Voice</h2>
                <button
                  onClick={() => setShowVoiceClone(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-gray-600">
                Voice cloning requires audio samples of the voice you want to clone. Upload 1-3 clear audio samples (30-120 seconds each) of a single person speaking.
              </p>
              <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> Voice cloning requires ElevenLabs subscription and may take several minutes to process.
                </p>
              </div>
              <p className="text-xs text-gray-500">
                By using voice cloning, you confirm that you have the right to use this voice and that you comply with ElevenLabs' Terms of Service.
              </p>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => {
                    alert('Voice cloning will be available soon!');
                    setShowVoiceClone(false);
                  }}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                >
                  Clone Voice
                </button>
                <button
                  onClick={() => setShowVoiceClone(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </form>
  );
}