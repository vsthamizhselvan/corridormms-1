import { create } from "zustand";
import { ViewerDisplayMode } from "../types/project";

interface PlaybackState {
  currentFrame: number;
  totalFrames: number;
  fps: number;
  isPlaying: boolean;
  loop: boolean;
  displayMode: ViewerDisplayMode;
  zoomLevel: number; // 0 is 'fit', otherwise 0.5, 1.0, 2.0
  setCurrentFrame: (frame: number) => void;
  setTotalFrames: (total: number) => void;
  setFps: (fps: number) => void;
  setIsPlaying: (playing: boolean) => void;
  togglePlay: () => void;
  setLoop: (loop: boolean) => void;
  setDisplayMode: (mode: ViewerDisplayMode) => void;
  setZoomLevel: (zoom: number) => void;
  stepFrame: (delta: number) => void;
}

export const usePlaybackStore = create<PlaybackState>((set) => ({
  currentFrame: 0,
  totalFrames: 240,
  fps: 24.0,
  isPlaying: false,
  loop: true,
  displayMode: "original",
  zoomLevel: 0, // Fit

  setCurrentFrame: (frame) =>
    set((state) => ({
      currentFrame: Math.max(0, Math.min(state.totalFrames - 1, Math.round(frame))),
    })),

  setTotalFrames: (total) => set({ totalFrames: Math.max(1, total) }),

  setFps: (fps) => set({ fps: Math.max(1, fps) }),

  setIsPlaying: (playing) => set({ isPlaying: playing }),

  togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),

  setLoop: (loop) => set({ loop }),

  setDisplayMode: (mode) => set({ displayMode: mode }),

  setZoomLevel: (zoom) => set({ zoomLevel: zoom }),

  stepFrame: (delta) =>
    set((state) => ({
      currentFrame: Math.max(0, Math.min(state.totalFrames - 1, state.currentFrame + delta)),
      isPlaying: false,
    })),
}));
