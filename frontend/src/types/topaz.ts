// Topaz Video AI types
export type TopazModel = 'apo-8' | 'chronos' | 'proteus' | 'dione' | 'artemis' | 'gaia';
export type AudioCodec = 'AAC' | 'Copy';
export type AudioTransfer = 'Copy' | 'PassThrough';
export type CompressionLevel = 'None' | 'Low' | 'Mid' | 'High';
export type VideoContainer = 'mp4' | 'mov';

export interface Resolution {
  width: number;
  height: number;
}

export interface ColorGrading {
  brightness: number;
  contrast: number;
  saturation: number;
  temperature: number;
  tint: number;
}

export interface TopazFilter {
  model: TopazModel;
  slowmo?: number;
  denoiseLevel?: number;
  sharpness?: number;
  stabilization?: boolean;
  colorGrading?: ColorGrading;
}

export interface TopazSettings {
  inputResolution: Resolution;
  frameRate: number;
  outputResolution: Resolution;
  outputFrameRate: number;
  audioCodec: AudioCodec;
  audioTransfer: AudioTransfer;
  dynamicCompressionLevel: CompressionLevel;
  container: VideoContainer;
  filters: TopazFilter[];
}