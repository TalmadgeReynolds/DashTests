/**
 * Job type definitions for the Composer
 */

export interface PostFX {
  interpolate: boolean;
  upscale: boolean;
}

export interface ReferenceImage {
  image_url?: string;
  image_base64?: string;
  reference_type: 'asset' | 'style';
}

export interface VideoOpts {
  // Legacy settings (for backward compatibility with Heygen)
  fps?: 24 | 30;
  aspect: '16:9' | '9:16' | '1:1';  // '1:1' supported by Heygen but not Veo
  max_duration?: number;
  
  // Veo 3 specific settings
  model_id?: string;
  duration_seconds?: 4 | 6 | 8;
  resolution?: '720p' | '1080p';
  generate_audio?: boolean;
  
  // Video generation modes
  input_image_url?: string;
  input_video_url?: string;
  last_frame_url?: string;
  mask_url?: string;
  mask_mode?: string;
  
  // Reference images
  reference_images?: ReferenceImage[];
  
  // Control parameters
  enhance_prompt?: boolean;
  negative_prompt?: string;
  seed?: number;
  person_generation?: 'allow_adult' | 'allow_all' | 'dont_allow';
  compression_quality?: 'optimized' | 'lossless';
  resize_mode?: 'pad' | 'crop';
  sample_count?: number;
}

export interface TTSRequest {
  provider: 'elevenlabs';
  voice_id?: string;
  text: string;
  model_id?: string;
  output_format?: string;
  stability: number;
  similarity_boost: number;
  style?: number;
  speaker_boost?: boolean;
  seed?: number;
  optimize_streaming_latency?: number;
  pace: number;
}

export interface CreatePromptJobRequest {
  script: string;
  reference_image_url?: string;
  post?: PostFX;
  video?: VideoOpts;
  priority: 'high' | 'low';
}

export interface HeygenAvatarConfig {
  avatar_id: string;
  provider: 'heygen';
}

export interface CreateAudioJobRequest {
  image_url?: string;
  avatar?: HeygenAvatarConfig;
  audio_url?: string;
  tts?: TTSRequest;
  action_prompt?: string;
  post?: PostFX;
  video?: VideoOpts;
  priority: 'high' | 'low';
}

export interface JobResponse {
  job_id: string;
}

export interface PresignResponse {
  uploadUrl: string;
  fileUrl: string;
}
