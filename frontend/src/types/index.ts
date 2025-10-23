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

export interface CreativeElement {
  character?: string; // Who is present, traits, emotion, wardrobe, role
  action?: string; // What characters are doing, physical movement, gestures
  expression?: string; // Mood, tone, energy in the scene
  camera?: string; // Framing, motion, shot style
  location?: string; // Where the scene takes place, atmosphere, time, lighting
  art_direction?: string; // Cinematic style, color palette, lens type
  dialogue?: string; // Spoken text or narrative meaning
  context?: string; // Implicit cues, subtext, symbolism
}

export type EmphasisLayer = 'descriptive' | 'dynamic' | 'cinematic' | 'conceptual';

export interface PromptSharpenRequest {
  original: string;
  model: 'gpt' | 'claude' | 'both';
  variants?: number; // Between 1 and 6
  temperature?: number; // Between 0.0 and 1.0
  max_tokens?: number; // Between 50 and 500
  structured: boolean;
  emphasis?: EmphasisLayer[]; // Only sent when structured is true
}

export interface PromptVariant {
  text: string; // The sharpened prompt text
  source: string; // Model that generated this variant (gpt or claude)
  score: number; // Overall quality score (0-1)
  similarity: number; // Semantic similarity to original (0-1)
  diff: string; // Human-readable diff showing changes
  elements?: CreativeElement; // Structured creative elements
  model_optimized?: string; // Version optimized for generation models
}

export interface PromptSharpenResponse {
  original: string; // Original input prompt
  variants: PromptVariant[]; // Ranked list of sharpened variants
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

// Export prompt sharpening types
export * from './prompt';

// Export Topaz types
export type {
  TopazSettings,
  TopazFilter,
  Resolution,
  ColorGrading,
  TopazModel,
  AudioCodec,
  AudioTransfer,
  CompressionLevel,
  VideoContainer
} from './topaz';
