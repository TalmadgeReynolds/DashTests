// Topaz Video AI types
export type TopazModel = 
  // Enhancement Models
  | 'prob-4'      // Proteus - Best for most videos
  | 'ahq-12'     // Artemis High Quality
  | 'amq-13'     // Artemis Medium Quality
  | 'alq-13'     // Artemis Low Quality
  | 'nyx-3'      // Nyx - Dedicated for denoise
  | 'nxf-1'      // Nyx Fast
  | 'rhea-1'     // Rhea - Advanced 4x upscaling
  | 'ghq-5'      // Gaia High Quality - Best for GenAI/CG/Animation
  | 'gcg-5'      // Gaia Computer Generated
  // Frame Interpolation Models
  | 'apo-8'      // Apollo - Best overall, up to 8x slowmo
  | 'apf-2'      // Apollo Fast
  | 'chr-2'      // Chronos - General framerate conversions
  | 'chf-3'      // Chronos Fast
  // Advanced Enhancement Models
  | 'ddv-3'      // Dione DV Footage
  | 'dtd-4'      // Dione Robust
  | 'dtds-2'     // Dione Robust Dehalo
  | 'dtv-4'      // Dione TV
  | 'dtvs-2'     // Dione Halo
  | 'alqs-2'     // Artemis Strong Halo
  | 'amqs-2'     // Artemis Dehalo
  | 'aaa-9'      // Artemis Aliased & Moire
  | 'thd-3'      // Theia Detail - High fidelity
  | 'thf-4'      // Theia Fidelity
  | 'iris-3'     // Iris - Specialized for faces
  | 'thm-2';     // Themis - Motion deblur
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