import React from "react";
import {
  Activity,
  Cpu,
  Layers,
  Film,
  HardDrive,
  Clock,
  Gauge,
  Sparkles,
  CheckCircle,
} from "lucide-react";
import { useExportStore } from "../../stores/exportStore";
import { useAiEngineStore } from "../../stores/aiEngineStore";
import { useMediaStore } from "../../project/mediaStore";

export const VideoProcessingPanel: React.FC = () => {
  const {
    isExporting,
    decodingProgress,
    inferenceProgress,
    encodingProgress,
    overallProgress,
    currentStage,
    currentFps,
    etaSeconds,
    settings,
    lastValidationResult,
  } = useExportStore();

  const { hardware } = useAiEngineStore();
  const { media, selectedMediaId } = useMediaStore();

  const selectedMedia = media.find((m) => m.id === selectedMediaId);

  return (
    <div className="space-y-4 text-xs select-none">
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-2 border-b border-[#282832]">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-white tracking-wide uppercase text-[11px]">
            Video Processing & Pipeline Monitor
          </span>
        </div>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
            isExporting
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse"
              : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
          }`}
        >
          {isExporting ? "Processing" : "Ready"}
        </span>
      </div>

      {/* Input & Pipeline Topology Cards */}
      <div className="grid grid-cols-2 gap-2 text-[11px]">
        {/* Card 1: Input Footage */}
        <div className="bg-[#1a1a20] border border-[#282830] rounded p-2.5 space-y-1.5">
          <div className="flex items-center gap-1.5 text-white font-medium border-b border-[#24242c] pb-1">
            <Film className="w-3.5 h-3.5 text-blue-400" />
            <span>Input Footage</span>
          </div>
          <div className="text-[#8a8a98] space-y-0.5 text-[10px]">
            <div className="truncate text-white font-medium">
              {selectedMedia ? selectedMedia.name : "No Media Selected"}
            </div>
            <div>
              Res: <span className="text-white font-mono">{selectedMedia ? `${selectedMedia.width}×${selectedMedia.height}` : "—"}</span>
            </div>
            <div>
              FPS: <span className="text-white font-mono">{selectedMedia ? selectedMedia.frameRate : "—"}</span>
            </div>
            <div>
              Codec: <span className="text-white font-mono">{selectedMedia ? selectedMedia.codec.toUpperCase() : "—"}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Pipeline Execution Backends */}
        <div className="bg-[#1a1a20] border border-[#282830] rounded p-2.5 space-y-1.5">
          <div className="flex items-center gap-1.5 text-white font-medium border-b border-[#24242c] pb-1">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            <span>Execution Engines</span>
          </div>
          <div className="text-[#8a8a98] space-y-0.5 text-[10px]">
            <div>
              Decoder: <span className="text-white font-mono">VideoToolbox / NVDEC</span>
            </div>
            <div>
              Inference:{" "}
              <span className="text-emerald-400 font-mono">
                {hardware ? hardware.recommended_backend.toUpperCase() : "MPS / CUDA"}
              </span>
            </div>
            <div>
              Encoder: <span className="text-white font-mono">{settings.format.toUpperCase()}</span>
            </div>
            <div>
              Color: <span className="text-blue-400 font-mono">{settings.colorSpace.toUpperCase()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Concurrent 4-Stage Progress Indicators */}
      <div className="bg-[#1a1a20] border border-[#282830] rounded p-3 space-y-3">
        <div className="flex items-center justify-between text-white font-medium pb-1 border-b border-[#24242c]">
          <div className="flex items-center gap-2">
            <Gauge className="w-3.5 h-3.5 text-blue-400" />
            <span>Pipeline Execution Stages</span>
          </div>
          <span className="text-[10px] text-[#808090] font-mono">{currentStage}</span>
        </div>

        {/* Stage 1: Decoding Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-[#8a8a98]">1. FFmpeg Frame Decoding (VideoToolbox/HW)</span>
            <span className="text-white font-mono">{Math.round(decodingProgress * 100)}%</span>
          </div>
          <div className="w-full bg-[#121216] h-1.5 rounded overflow-hidden">
            <div
              className="bg-cyan-500 h-full transition-all duration-200"
              style={{ width: `${decodingProgress * 100}%` }}
            />
          </div>
        </div>

        {/* Stage 2: AI Inference Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-[#8a8a98]">2. CorridorKey Neural Inference (Stage 1 & 2)</span>
            <span className="text-white font-mono">{Math.round(inferenceProgress * 100)}%</span>
          </div>
          <div className="w-full bg-[#121216] h-1.5 rounded overflow-hidden">
            <div
              className="bg-blue-500 h-full transition-all duration-200"
              style={{ width: `${inferenceProgress * 100}%` }}
            />
          </div>
        </div>

        {/* Stage 3: Encoding Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px]">
            <span className="text-[#8a8a98]">3. Video Encoding & Alpha Channel Assembly</span>
            <span className="text-white font-mono">{Math.round(encodingProgress * 100)}%</span>
          </div>
          <div className="w-full bg-[#121216] h-1.5 rounded overflow-hidden">
            <div
              className="bg-indigo-500 h-full transition-all duration-200"
              style={{ width: `${encodingProgress * 100}%` }}
            />
          </div>
        </div>

        {/* Stage 4: Overall Progress */}
        <div className="pt-2 border-t border-[#24242c] space-y-1.5">
          <div className="flex justify-between text-[11px] font-medium">
            <span className="text-white">Overall Pipeline Progress</span>
            <span className="text-blue-400 font-mono">{Math.round(overallProgress * 100)}%</span>
          </div>
          <div className="w-full bg-[#121216] h-2 rounded overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-600 to-emerald-500 h-full transition-all duration-200"
              style={{ width: `${overallProgress * 100}%` }}
            />
          </div>

          {/* Performance Telemetry */}
          <div className="flex justify-between text-[10px] text-[#707080] font-mono pt-1">
            <div className="flex items-center gap-1">
              <Activity className="w-3 h-3 text-emerald-400" />
              <span>Throughput: {currentFps} FPS</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>ETA: {etaSeconds}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
