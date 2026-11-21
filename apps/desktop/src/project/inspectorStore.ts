import { create } from "zustand";
import { KeyingSettings, MatteSettings, TransformSettings } from "../types/project";

export type InspectorTab =
  | "media"
  | "keying"
  | "matte"
  | "masks"
  | "color"
  | "effects"
  | "layers"
  | "composite"
  | "background"
  | "export"
  | "pipeline"
  | "transform"
  | "nodes"
  | "performance";

interface InspectorState {
  activeTab: InspectorTab;
  keying: KeyingSettings;
  matte: MatteSettings;
  transform: TransformSettings;
  setActiveTab: (tab: InspectorTab) => void;
  updateKeying: (partial: Partial<KeyingSettings>) => void;
  updateMatte: (partial: Partial<MatteSettings>) => void;
  updateTransform: (partial: Partial<TransformSettings>) => void;
}

export const useInspectorStore = create<InspectorState>((set) => ({
  activeTab: "media",

  keying: {
    hannChunk: 24,
    hannStride: 12,
    lowVram: false,
    despillStrength: 0.5,
    hintMode: "none",
    hintQuality: 0.95,
  },

  matte: {
    contrast: 1.0,
    edgeRefinement: 0.0,
    invert: false,
    alphaThreshold: 0.0,
  },

  transform: {
    posX: 0,
    posY: 0,
    scale: 100,
    rotation: 0,
    opacity: 100,
  },

  setActiveTab: (tab) => set({ activeTab: tab }),

  updateKeying: (partial) =>
    set((state) => ({
      keying: { ...state.keying, ...partial },
    })),

  updateMatte: (partial) =>
    set((state) => ({
      matte: { ...state.matte, ...partial },
    })),

  updateTransform: (partial) =>
    set((state) => ({
      transform: { ...state.transform, ...partial },
    })),
}));
