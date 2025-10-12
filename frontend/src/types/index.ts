// Core types for the AI Lip-Sync App

export type JobStatus = 'PENDING' | 'RUNNING' | 'DONE' | 'FAILED';

export type Engine = 'veo3' | 'heygen';

export type WorkflowMethod = 'PROMPT_TO_LIPSYNC' | 'IMAGE_AUDIO_TO_LIPSYNC';

export interface Job {
  id: string;
  status: JobStatus;
  method: WorkflowMethod;
  engine: Engine;
  
  // Prompt mode fields
  script?: string;
  reference_image_url?: string;
  
  // Image+Audio mode fields
  portrait_image_url?: string;
  audio_url?: string;
  audio_text?: string;
  action_prompts?: string;
  
  // Common settings
  fps?: number;
  aspect_ratio?: string;
  duration_override?: number;
  
  // Post-FX settings
  interpolate?: boolean;
  upscale?: boolean;
  use_topaz?: boolean;
  
  // Results
  output_video_url?: string;
  thumbnail_url?: string;
  
  // Metadata
  cost?: number;
  duration?: number;
  progress?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  
  // Provider details
  provider_job_id?: string;
}

export interface Preset {
  id: string;
  name: string;
  method: WorkflowMethod;
  engine: Engine;
  fps: number;
  aspect_ratio: string;
  interpolate: boolean;
  upscale: boolean;
  use_topaz: boolean;
  duration_override?: number;
  tags?: string[];
  usage_count: number;
  last_used?: string;
  created_at: string;
}

export interface CreateJobRequest {
  method: WorkflowMethod;
  engine: Engine;
  script?: string;
  reference_image_url?: string;
  portrait_image_url?: string;
  audio_url?: string;
  audio_text?: string;
  action_prompts?: string;
  fps?: number;
  aspect_ratio?: string;
  duration_override?: number;
  interpolate?: boolean;
  upscale?: boolean;
  use_topaz?: boolean;
}

export interface PromptSharpenRequest {
  prompt: string;
  model: 'gpt' | 'claude' | 'both';
  num_variants?: number;
  temperature?: number;
}

export interface PromptVariant {
  model: 'gpt-4o' | 'claude-3.5-sonnet';
  variant: string;
  score: number;
  changes: string[];
  reasoning: string;
  similarity: number;
}

export interface PromptSharpenResponse {
  original: string;
  variants: PromptVariant[];
  best_variant: PromptVariant;
}

export interface CostEstimate {
  generation_cost: number;
  tts_cost?: number;
  interpolation_cost?: number;
  upscale_cost?: number;
  topaz_cost?: number;
  total_cost: number;
  estimated_duration?: number;
}
