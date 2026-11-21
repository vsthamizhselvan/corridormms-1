import { create } from "zustand";

export interface JobOutputs {
  alpha?: string;
  foreground?: string;
  cutout?: string;
  checker?: string;
  settings?: string;
}

export interface JobHistoryItem {
  jobId: string;
  plateName: string;
  status: "completed" | "failed" | "cancelled";
  outputs: JobOutputs;
  timestamp: string;
}

interface AiJobState {
  jobId: string | null;
  status: "idle" | "running" | "completed" | "cancelled" | "failed";
  progress: number;
  processedFrames: number;
  totalFrames: number;
  fps: number;
  etaSeconds: number;
  currentStage: string;
  outputs: JobOutputs;
  errorMessage: string | null;
  jobHistory: JobHistoryItem[];

  // Actions
  startJob: (params: {
    inputPath: string;
    outputDir: string;
    outputs?: string[];
    hannChunk?: number;
    hannStride?: number;
    lowVram?: boolean;
    despillStrength?: number;
    device?: string;
    exportFormat?: string;
    colorProfile?: string;
    alphaMode?: string;
    preserveAudio?: boolean;
  }) => Promise<boolean>;
  cancelJob: () => Promise<boolean>;
  resetJob: () => void;
  updateProgress: (payload: any) => void;
  setJobCompleted: (outputs: JobOutputs) => void;
  setJobFailed: (errorMsg: string) => void;
}

export const useAiJobStore = create<AiJobState>((set, get) => ({
  jobId: null,
  status: "idle",
  progress: 0,
  processedFrames: 0,
  totalFrames: 0,
  fps: 0,
  etaSeconds: 0,
  currentStage: "Idle",
  outputs: {},
  errorMessage: null,
  jobHistory: [],

  startJob: async (params) => {
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
    set({
      jobId,
      status: "running",
      progress: 0,
      processedFrames: 0,
      totalFrames: 100,
      fps: 0,
      etaSeconds: 0,
      currentStage: "Starting AI Inference Pipeline...",
      outputs: {},
      errorMessage: null,
    });

    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const { listen } = await import("@tauri-apps/api/event");

      // Setup listeners for asynchronous progress & completion
      const unlistenProgress = await listen("ai-progress", (event: any) => {
        const data = event.payload;
        if (data.job_id === jobId) {
          get().updateProgress(data);
        }
      });

      const unlistenCompleted = await listen("ai-job-completed", (event: any) => {
        const data = event.payload;
        if (data.job_id === jobId) {
          get().setJobCompleted(data.outputs || {});
          unlistenProgress();
          unlistenCompleted();
        }
      });

      const unlistenError = await listen("ai-error", (event: any) => {
        const data = event.payload;
        if (data.job_id === jobId) {
          get().setJobFailed(data.error_message || "Inference failed");
          unlistenProgress();
          unlistenCompleted();
          unlistenError();
        }
      });

      // Invoke Tauri start_inference_job
      await invoke("start_inference_job", {
        config: {
          job_id: jobId,
          input_path: params.inputPath,
          output_dir: params.outputDir,
          outputs: params.outputs || ["alpha", "fg"],
          hann_chunk: params.hannChunk || 24,
          hann_stride: params.hannStride || 12,
          low_vram: params.lowVram || false,
          despill_strength: params.despillStrength ?? 0.5,
          hint_first_frame: null,
          hint_video: null,
          hint_quality: 0.95,
          device: params.device || "auto",
          output_format: "video",
        },
      });

      return true;
    } catch (err: any) {
      set({
        status: "failed",
        errorMessage: err?.toString() || "Failed to start inference job",
        currentStage: "Error occurred",
      });
      return false;
    }
  },

  cancelJob: async () => {
    const currentId = get().jobId;
    if (!currentId) return false;

    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("cancel_inference_job", { jobId: currentId });
      set({
        status: "cancelled",
        currentStage: "Cancelled by user",
      });
      return true;
    } catch (err: any) {
      console.error("Cancellation error:", err);
      return false;
    }
  },

  resetJob: () =>
    set({
      jobId: null,
      status: "idle",
      progress: 0,
      processedFrames: 0,
      totalFrames: 0,
      fps: 0,
      etaSeconds: 0,
      currentStage: "Idle",
      outputs: {},
      errorMessage: null,
    }),

  updateProgress: (payload) => {
    set({
      processedFrames: payload.processed_frames || 0,
      totalFrames: payload.total_frames || 0,
      progress: payload.percentage || 0,
      fps: payload.fps || 0,
      etaSeconds: payload.eta_seconds || 0,
      currentStage: payload.current_stage || "Processing frames...",
    });
  },

  setJobCompleted: (outputs) => {
    const state = get();
    const historyItem: JobHistoryItem = {
      jobId: state.jobId || "unknown",
      plateName: "Clip",
      status: "completed",
      outputs,
      timestamp: new Date().toLocaleTimeString(),
    };

    set({
      status: "completed",
      progress: 100,
      currentStage: "Inference completed successfully!",
      outputs,
      jobHistory: [historyItem, ...state.jobHistory],
    });
  },

  setJobFailed: (errorMsg) => {
    const state = get();
    const historyItem: JobHistoryItem = {
      jobId: state.jobId || "unknown",
      plateName: "Clip",
      status: "failed",
      outputs: {},
      timestamp: new Date().toLocaleTimeString(),
    };

    set({
      status: "failed",
      errorMessage: errorMsg,
      currentStage: `Failed: ${errorMsg}`,
      jobHistory: [historyItem, ...state.jobHistory],
    });
  },
}));
