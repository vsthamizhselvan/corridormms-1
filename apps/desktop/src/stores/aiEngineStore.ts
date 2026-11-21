import { create } from "zustand";

export interface GpuDeviceInfo {
  index: number;
  name: string;
  backend: "cuda" | "mps" | "cpu";
  total_memory_mb: number;
  free_memory_mb: number;
  compute_capability?: string;
  is_supported: boolean;
  recommended: boolean;
}

export interface HardwareReportData {
  os_name: string;
  os_version: string;
  architecture: string;
  cpu_model: string;
  cpu_threads: number;
  total_ram_mb: number;
  available_ram_mb: number;
  python_version: string;
  pytorch_version: string | null;
  cuda_available: boolean;
  cuda_version: string | null;
  mps_available: boolean;
  mps_built: boolean;
  ffmpeg_available: boolean;
  ffmpeg_path: string | null;
  ffmpeg_version: string | null;
  devices: GpuDeviceInfo[];
  recommended_backend: "cuda" | "mps" | "cpu";
  compatibility_notes: string[];
}

export interface ModelAssetInfo {
  name: string;
  path: string;
  exists: boolean;
  size_mb: number;
  required: boolean;
}

export interface ModelStatusData {
  model_name: string;
  is_loaded: boolean;
  active_device: string | null;
  all_assets_present: boolean;
  total_size_gb: number;
  assets: Record<string, ModelAssetInfo>;
  load_error: string | null;
}

interface AiEngineState {
  isRunning: boolean;
  pythonPath: string | null;
  isLoading: boolean;
  hardware: HardwareReportData | null;
  modelStatus: ModelStatusData | null;
  activeDevice: string;
  lastError: string | null;

  // Actions
  fetchEngineStatus: () => Promise<void>;
  detectHardware: () => Promise<void>;
  checkModelStatus: () => Promise<void>;
  loadModel: (device?: string) => Promise<boolean>;
  startEngine: () => Promise<void>;
  stopEngine: () => Promise<void>;
  setActiveDevice: (device: string) => void;
}

export const useAiEngineStore = create<AiEngineState>((set, get) => ({
  isRunning: false,
  pythonPath: null,
  isLoading: false,
  hardware: null,
  modelStatus: null,
  activeDevice: "auto",
  lastError: null,

  fetchEngineStatus: async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const res: any = await invoke("get_engine_status");
      set({ isRunning: res.running, pythonPath: res.python_path });
    } catch {
      // Fallback
      set({ isRunning: true });
    }
  },

  detectHardware: async () => {
    set({ isLoading: true });
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const hw: HardwareReportData = await invoke("detect_hardware");
      set({ hardware: hw, isLoading: false });
    } catch (err: any) {
      set({ lastError: err?.toString() || "Hardware detection failed", isLoading: false });
    }
  },

  checkModelStatus: async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const status: ModelStatusData = await invoke("check_model_status");
      set({ modelStatus: status });
    } catch (err: any) {
      set({ lastError: err?.toString() || "Failed to check model status" });
    }
  },

  loadModel: async (device = "auto") => {
    set({ isLoading: true });
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const res: any = await invoke("load_corridor_key_model", { device });
      await get().checkModelStatus();
      set({ isLoading: false, activeDevice: res.device || device });
      return true;
    } catch (err: any) {
      set({ lastError: err?.toString() || "Failed to load model", isLoading: false });
      return false;
    }
  },

  startEngine: async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_ai_engine");
      await get().fetchEngineStatus();
    } catch (err: any) {
      set({ lastError: err?.toString() });
    }
  },

  stopEngine: async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("stop_ai_engine");
      await get().fetchEngineStatus();
    } catch (err: any) {
      set({ lastError: err?.toString() });
    }
  },

  setActiveDevice: (device) => set({ activeDevice: device }),
}));
