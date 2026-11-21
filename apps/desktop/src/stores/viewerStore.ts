import { create } from "zustand";

export type DisplayMode = "original" | "foreground" | "alpha" | "composite" | "background";
export type BackgroundType = "checkerboard" | "black" | "white" | "custom_color" | "gradient" | "image" | "video";
export type CompareMode = "none" | "wipe" | "side_by_side" | "difference";
export type ZoomFitMode = "fit" | "fit_width" | "fit_height" | "custom";
export type ViewerAlphaMode = "straight" | "premultiplied";
export type PreviewResolution = "full" | "half" | "quarter" | "eighth";

interface ViewerState {
  displayMode: DisplayMode;
  backgroundType: BackgroundType;
  backgroundColor: string;
  gradientColorA: string;
  gradientColorB: string;
  gradientAngle: number;
  backgroundImageUrl: string | null;
  compareMode: CompareMode;
  wipePosition: number; // 0.0 to 1.0
  panX: number;
  panY: number;
  zoomLevel: number; // 0 means Fit, > 0 is scale factor (e.g. 0.5, 1.0, 2.0)
  zoomFitMode: ZoomFitMode;
  checkerboardSize: number;
  alphaMode: ViewerAlphaMode;
  exposure: number; // in EV (-3.0 to +3.0)
  saturation: number; // 0.0 to 2.0
  previewResolution: PreviewResolution;
  playbackFps: number;
  droppedFrames: number;

  // Actions
  setDisplayMode: (mode: DisplayMode) => void;
  setBackgroundType: (bg: BackgroundType) => void;
  setBackgroundColor: (color: string) => void;
  setGradient: (colorA: string, colorB: string, angle?: number) => void;
  setBackgroundImageUrl: (url: string | null) => void;
  setCompareMode: (mode: CompareMode) => void;
  setWipePosition: (pos: number) => void;
  setPan: (x: number, y: number) => void;
  updatePan: (deltaX: number, deltaY: number) => void;
  resetPan: () => void;
  setZoomLevel: (zoom: number) => void;
  setZoomFitMode: (mode: ZoomFitMode) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  resetView: () => void;
  setAlphaMode: (mode: ViewerAlphaMode) => void;
  setExposure: (ev: number) => void;
  setSaturation: (sat: number) => void;
  setPreviewResolution: (res: PreviewResolution) => void;
  updatePlaybackMetrics: (fps: number, dropped: number) => void;
}

export const useViewerStore = create<ViewerState>((set) => ({
  displayMode: "composite",
  backgroundType: "checkerboard",
  backgroundColor: "#18181e",
  gradientColorA: "#1e3a8a",
  gradientColorB: "#0f172a",
  gradientAngle: 45,
  backgroundImageUrl: null,
  compareMode: "none",
  wipePosition: 0.5,
  panX: 0,
  panY: 0,
  zoomLevel: 0, // 0 = Fit
  zoomFitMode: "fit",
  checkerboardSize: 20,
  alphaMode: "straight",
  exposure: 0.0,
  saturation: 1.0,
  previewResolution: "full",
  playbackFps: 24.0,
  droppedFrames: 0,

  setDisplayMode: (mode) => set({ displayMode: mode }),
  setBackgroundType: (bg) => set({ backgroundType: bg }),
  setBackgroundColor: (color) => set({ backgroundColor: color }),
  setGradient: (colorA, colorB, angle = 45) =>
    set({ gradientColorA: colorA, gradientColorB: colorB, gradientAngle: angle }),
  setBackgroundImageUrl: (url) => set({ backgroundImageUrl: url }),
  setCompareMode: (mode) => set({ compareMode: mode }),
  setWipePosition: (pos) => set({ wipePosition: Math.max(0.0, Math.min(1.0, pos)) }),
  setPan: (x, y) => set({ panX: x, panY: y }),
  updatePan: (deltaX, deltaY) => set((s) => ({ panX: s.panX + deltaX, panY: s.panY + deltaY })),
  resetPan: () => set({ panX: 0, panY: 0 }),
  setZoomLevel: (zoom) => set({ zoomLevel: zoom, zoomFitMode: zoom === 0 ? "fit" : "custom" }),
  setZoomFitMode: (mode) =>
    set({
      zoomFitMode: mode,
      zoomLevel: mode === "fit" ? 0 : mode === "fit_width" ? -1 : mode === "fit_height" ? -2 : 1.0,
    }),
  zoomIn: () =>
    set((s) => {
      const current = s.zoomLevel === 0 ? 1.0 : s.zoomLevel;
      const next = Math.min(4.0, current * 1.25);
      return { zoomLevel: next, zoomFitMode: "custom" };
    }),
  zoomOut: () =>
    set((s) => {
      const current = s.zoomLevel === 0 ? 1.0 : s.zoomLevel;
      const next = Math.max(0.1, current / 1.25);
      return { zoomLevel: next, zoomFitMode: "custom" };
    }),
  resetView: () =>
    set({
      panX: 0,
      panY: 0,
      zoomLevel: 0,
      zoomFitMode: "fit",
      wipePosition: 0.5,
      compareMode: "none",
    }),
  setAlphaMode: (mode) => set({ alphaMode: mode }),
  setExposure: (ev) => set({ exposure: Math.max(-3.0, Math.min(3.0, ev)) }),
  setSaturation: (sat) => set({ saturation: Math.max(0.0, Math.min(2.0, sat)) }),
  setPreviewResolution: (res) => set({ previewResolution: res }),
  updatePlaybackMetrics: (fps, dropped) => set({ playbackFps: fps, droppedFrames: dropped }),
}));
