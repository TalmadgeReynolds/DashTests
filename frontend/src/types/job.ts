/**
 * Job type definitions for the Composer
 */

export interface PostFX {
  interpolate: boolean;
  upscale: boolean;
}

export interface VideoOpts {
  fps: 24 | 30;
  aspect: '16:9' | '9:16' | '1:1';
  max_duration: number;
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
