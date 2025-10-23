/**
 * Types for prompt sharpening functionality
 */

// Emphasis layers for structured mode
export type EmphasisLayer = 'descriptive' | 'dynamic' | 'cinematic' | 'conceptual';

// Creative elements extracted in structured mode
export interface CreativeElement {
  character?: string;
  action?: string;
  expression?: string;
  camera?: string;
  location?: string;
  art_direction?: string;
  dialogue?: string;
  context?: string;
}

// Request parameters for prompt sharpening
export interface PromptSharpenRequest {
  original: string;
  model?: 'gpt' | 'claude' | 'both';
  variants?: number;
  temperature?: number;
  max_tokens?: number;
  structured?: boolean;
  emphasis?: EmphasisLayer[];
}

// Single variant in the response
export interface PromptVariant {
  text: string;
  source: string;
  score: number;
  similarity: number;
  diff: string;
  elements?: CreativeElement;
  model_optimized?: string;
}

// Complete response from the sharpening endpoint
export interface PromptSharpenResponse {
  original: string;
  variants: PromptVariant[];
}