import { create } from "zustand";

export interface HardwareInfo {
  osName: string;
  osVersion: string;
  architecture: string;
  cpuModel: string;
  cpuThreads: number;
  totalRamMb: number;
  availableRamMb: number;
  activeBackend: "cuda" | "mps" | "cpu";
  gpuName: string;
  gpuMemoryMb: number;
  ffmpegAvailable: boolean;
  ffmpegVersion?: string;
}

interface SettingsState {
  hardware: HardwareInfo;
  tempDirectory: string;
  setHardware: (hw: HardwareInfo) => void;
  setTempDirectory: (dir: string) => void;
}

const defaultHardware: HardwareInfo = {
  osName: "macOS",
  osVersion: "26.6.2",
  architecture: "arm64",
  cpuModel: "Apple M5",
  cpuThreads: 10,
  totalRamMb: 16384,
  availableRamMb: 8192,
  activeBackend: "cpu",
  gpuName: "Apple M5 GPU",
  gpuMemoryMb: 16384,
  ffmpegAvailable: true,
  ffmpegVersion: "ffmpeg 9.0.2",
};

export const useSettingsStore = create<SettingsState>((set) => ({
  hardware: defaultHardware,
  tempDirectory: "",

  setHardware: (hardware) => set({ hardware }),
  setTempDirectory: (tempDirectory) => set({ tempDirectory }),
}));
