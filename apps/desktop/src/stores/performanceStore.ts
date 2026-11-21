import { create } from "zustand";

export interface SystemMetrics {
  cpuUsagePct: number;
  processRssMb: number;
  totalRamMb: number;
  usedRamMb: number;
  availableRamMb: number;
  gpuAllocatedMb: number;
  backend: string;
  cacheEntries: number;
  cacheUsedMb: number;
  cacheMaxMb: number;
  cacheHitRatePct: number;
  cacheEvictions: number;
  inferenceLatencyMs: number;
  playbackFps: number;
  isMemoryPressure: boolean;
  activeQueueLength: number;
}

interface PerformanceState extends SystemMetrics {
  historyCpu: number[];
  historyRam: number[];
  historyFps: number[];
  updateMetrics: (partial: Partial<SystemMetrics>) => void;
  fetchSystemMetrics: () => Promise<void>;
}

export const usePerformanceStore = create<PerformanceState>((set) => ({
  cpuUsagePct: 0,
  processRssMb: 0,
  totalRamMb: 16384,
  usedRamMb: 0,
  availableRamMb: 8192,
  gpuAllocatedMb: 0,
  backend: "Apple Metal (MPS)",
  cacheEntries: 0,
  cacheUsedMb: 0,
  cacheMaxMb: 1024,
  cacheHitRatePct: 100,
  cacheEvictions: 0,
  inferenceLatencyMs: 2.8,
  playbackFps: 24.0,
  isMemoryPressure: false,
  activeQueueLength: 0,

  historyCpu: [10, 15, 12, 18, 14, 20, 16, 22, 18, 15],
  historyRam: [200, 220, 230, 240, 235, 250, 260, 255, 270, 280],
  historyFps: [24, 24, 24, 23.9, 24.0, 24.1, 24.0, 23.8, 24.0, 24.0],

  updateMetrics: (partial) =>
    set((state) => {
      const nextCpu =
        partial.cpuUsagePct !== undefined
          ? [...state.historyCpu.slice(-19), partial.cpuUsagePct]
          : state.historyCpu;
      const nextRam =
        partial.processRssMb !== undefined
          ? [...state.historyRam.slice(-19), partial.processRssMb]
          : state.historyRam;
      const nextFps =
        partial.playbackFps !== undefined
          ? [...state.historyFps.slice(-19), partial.playbackFps]
          : state.historyFps;

      return {
        ...state,
        ...partial,
        historyCpu: nextCpu,
        historyRam: nextRam,
        historyFps: nextFps,
      };
    }),

  fetchSystemMetrics: async () => {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const telemetry: any = await invoke("get_system_telemetry");
      if (telemetry) {
        set((state) => ({
          cpuUsagePct: Math.round(telemetry.cpu_usage_pct * 10) / 10,
          processRssMb: Math.round(telemetry.process_rss_mb * 10) / 10,
          totalRamMb: telemetry.total_ram_mb,
          usedRamMb: telemetry.used_ram_mb,
          availableRamMb: telemetry.available_ram_mb,
          backend: telemetry.backend,
          isMemoryPressure: telemetry.available_ram_mb < 1536,
          historyCpu: [...state.historyCpu.slice(-19), Math.round(telemetry.cpu_usage_pct * 10) / 10],
          historyRam: [...state.historyRam.slice(-19), Math.round(telemetry.process_rss_mb * 10) / 10],
        }));
      }
    } catch {
      // In web dev mode or when native invoke unavailable
    }
  },
}));
