import { create } from "zustand";

export type ExportFormat =
  | "prores_4444"
  | "prores_4444_xq"
  | "qtrle"
  | "vp9"
  | "openexr"
  | "png_sequence";

export type AlphaMode = "straight" | "premultiplied";
export type ColorSpace = "rec709" | "srgb" | "linear" | "rec2020" | "acescg";

export interface ExportSettings {
  format: ExportFormat;
  resolution: "source" | "1080p" | "4k" | "720p";
  framerate: "source" | "24" | "25" | "29.97" | "30" | "60";
  alphaMode: AlphaMode;
  colorSpace: ColorSpace;
  preserveAudio: boolean;
  despillStrength: number;
  outputDirectory: string;
  customFilename: string;
  exrBitDepth: "half" | "float";
  pngBitDepth: 8 | 16;
}

interface ExportStoreState {
  settings: ExportSettings;
  isExporting: boolean;
  decodingProgress: number;
  inferenceProgress: number;
  encodingProgress: number;
  overallProgress: number;
  currentStage: string;
  currentFps: number;
  etaSeconds: number;
  lastValidationResult: any | null;
  lastColorReport: any | null;

  updateSettings: (partial: Partial<ExportSettings>) => void;
  setExporting: (exporting: boolean) => void;
  updateProgress: (data: {
    decodingProgress?: number;
    inferenceProgress?: number;
    encodingProgress?: number;
    overallProgress?: number;
    currentStage?: string;
    currentFps?: number;
    etaSeconds?: number;
  }) => void;
  setCompleted: (validation: any, colorReport: any) => void;
  resetProgress: () => void;
}

export const useExportStore = create<ExportStoreState>((set) => ({
  settings: {
    format: "prores_4444",
    resolution: "source",
    framerate: "source",
    alphaMode: "straight",
    colorSpace: "rec709",
    preserveAudio: true,
    despillStrength: 0.5,
    outputDirectory: "",
    customFilename: "",
    exrBitDepth: "half",
    pngBitDepth: 8,
  },
  isExporting: false,
  decodingProgress: 0,
  inferenceProgress: 0,
  encodingProgress: 0,
  overallProgress: 0,
  currentStage: "Idle",
  currentFps: 0,
  etaSeconds: 0,
  lastValidationResult: null,
  lastColorReport: null,

  updateSettings: (partial) =>
    set((state) => ({
      settings: { ...state.settings, ...partial },
    })),

  setExporting: (exporting) => set({ isExporting: exporting }),

  updateProgress: (data) =>
    set((state) => ({
      ...state,
      ...data,
    })),

  setCompleted: (validation, colorReport) =>
    set({
      isExporting: false,
      overallProgress: 1.0,
      decodingProgress: 1.0,
      inferenceProgress: 1.0,
      encodingProgress: 1.0,
      currentStage: "Completed",
      lastValidationResult: validation,
      lastColorReport: colorReport,
    }),

  resetProgress: () =>
    set({
      isExporting: false,
      decodingProgress: 0,
      inferenceProgress: 0,
      encodingProgress: 0,
      overallProgress: 0,
      currentStage: "Idle",
      currentFps: 0,
      etaSeconds: 0,
      lastValidationResult: null,
      lastColorReport: null,
    }),
}));
