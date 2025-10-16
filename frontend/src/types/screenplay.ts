/**
 * TypeScript types for Screenplay feature
 */

export interface Screenplay {
  id: string;
  title: string;
  filename: string;
  pdf_url: string;
  text_content?: string;
  page_count?: number;
  file_size_bytes?: number;
  created_at: string;
  updated_at: string;
}

export interface ScreenplayCreate {
  title: string;
  filename: string;
  pdf_url: string;
  file_size_bytes?: number;
}

export interface ScreenplayListResponse {
  screenplays: Screenplay[];
  total: number;
}

export interface TextSelection {
  screenplay_id: string;
  selected_text: string;
}

export interface TextSelectionResponse {
  screenplay_id: string;
  selected_text: string;
  processed_prompt: string;
}

export interface PresignRequest {
  filename: string;
  mime: string;
  kind: 'IMAGE' | 'AUDIO' | 'VIDEO' | 'SCREENPLAY';
  content_length?: number;
}

export interface PresignResponse {
  uploadUrl: string;
  fileUrl: string;
}
