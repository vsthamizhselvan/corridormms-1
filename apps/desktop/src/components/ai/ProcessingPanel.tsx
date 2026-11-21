import React from "react";
import {
  Play,
  Square,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Film,
  Sparkles,
  Layers,
  ArrowRight,
} from "lucide-react";
import { useAiJobStore } from "../../stores/aiJobStore";
import { useMediaStore } from "../../project/mediaStore";
import { useInspectorStore } from "../../project/inspectorStore";
import { usePlaybackStore } from "../../project/playbackStore";

export const ProcessingPanel: React.FC = () => {
  const {
    jobId,
    status,
    progress,
    processedFrames,
    totalFrames,
    fps,
    etaSeconds,
    currentStage,
    outputs,
    errorMessage,
    startJob,
    cancelJob,
    resetJob,
  } = useAiJobStore();

  const { media, selectedMediaId, addMedia, selectMedia } = useMediaStore();
  const { keying } = useInspectorStore();
  const { setDisplayMode } = usePlaybackStore();

  const selectedMedia = media.find((m) => m.id === selectedMediaId);

  const handleStartInference = async () => {
    if (!selectedMedia) return;

    // Use output directory next to input clip or in temp/renders
    const inputDir = selectedMedia.path.includes("/")
      ? selectedMedia.path.substring(0, selectedMedia.path.lastIndexOf("/"))
      : "renders";
    const outputDir = `${inputDir}/renders_${Date.now()}`;

    await startJob({
      inputPath: selectedMedia.path,
      outputDir,
      outputs: ["alpha", "fg", "cutout"],
      hannChunk: keying.hannChunk,
      hannStride: keying.hannStride,
      lowVram: keying.lowVram,
      despillStrength: keying.despillStrength,
    });
  };

  const handlePreviewAlpha = () => {
    if (!outputs.alpha) return;
    // Register alpha plate in media store and select it
    const alphaItem = {
      id: `med_alpha_${Date.now()}`,
      name: `Alpha_${selectedMedia?.name || "Plate"}`,
      path: outputs.alpha,
      width: selectedMedia?.width || 1920,
      height: selectedMedia?.height || 1080,
      frameRate: selectedMedia?.frameRate || 24,
      durationFrames: totalFrames || 240,
      durationSeconds: Math.round(totalFrames / (selectedMedia?.frameRate || 24)),
      codec: "H.264 10-bit YUV444p10le",
      fileSizeBytes: 12000000,
    };
    addMedia(alphaItem);
    selectMedia(alphaItem.id);
    setDisplayMode("alpha");
  };

  const handlePreviewForeground = () => {
    if (!outputs.foreground) return;
    const fgItem = {
      id: `med_fg_${Date.now()}`,
      name: `FG_${selectedMedia?.name || "Plate"}`,
      path: outputs.foreground,
      width: selectedMedia?.width || 1920,
      height: selectedMedia?.height || 1080,
      frameRate: selectedMedia?.frameRate || 24,
      durationFrames: totalFrames || 240,
      durationSeconds: Math.round(totalFrames / (selectedMedia?.frameRate || 24)),
      codec: "H.264 Despilled RGB",
      fileSizeBytes: 18000000,
    };
    addMedia(fgItem);
    selectMedia(fgItem.id);
    setDisplayMode("foreground");
  };

  return (
    <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-3 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          Neural Keying Execution
        </span>
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
            status === "running"
              ? "bg-amber-950 text-amber-400 border border-amber-800 animate-pulse"
              : status === "completed"
              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
              : status === "failed"
              ? "bg-red-950 text-red-400 border border-red-800"
              : "bg-[#22222a] text-[#808090]"
          }`}
        >
          {status}
        </span>
      </div>

      {/* Target Media Plate Banner */}
      <div className="bg-[#141418] border border-[#24242c] rounded p-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Film className="w-4 h-4 text-blue-400 shrink-0" />
          <div className="min-w-0">
            <div className="text-white font-medium truncate" title={selectedMedia?.name || "None"}>
              {selectedMedia ? selectedMedia.name : "No clip selected in project"}
            </div>
            {selectedMedia && (
              <div className="text-[10px] text-[#707080] font-mono mt-0.5">
                {selectedMedia.width}×{selectedMedia.height} • {selectedMedia.durationFrames}f • {selectedMedia.frameRate} fps
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Execution Buttons */}
      <div className="flex items-center gap-2">
        {status !== "running" ? (
          <button
            onClick={handleStartInference}
            disabled={!selectedMedia}
            className={`flex-1 py-2 px-3 rounded font-medium text-xs flex items-center justify-center gap-2 transition-all ${
              selectedMedia
                ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg cursor-pointer"
                : "bg-[#24242c] text-[#606070] cursor-not-allowed border border-[#30303c]"
            }`}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Process CorridorKey 2.0</span>
          </button>
        ) : (
          <button
            onClick={cancelJob}
            className="flex-1 py-2 px-3 rounded font-medium text-xs bg-red-600 hover:bg-red-500 text-white flex items-center justify-center gap-2 shadow-lg"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Cancel Processing</span>
          </button>
        )}

        {(status === "completed" || status === "failed" || status === "cancelled") && (
          <button
            onClick={resetJob}
            title="Reset Job"
            className="p-2 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white border border-[#30303c]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Progress & Stage Status (When running or completed) */}
      {(status === "running" || status === "completed" || status === "failed") && (
        <div className="space-y-2 pt-2 border-t border-[#24242c]">
          {/* Progress Bar */}
          <div className="w-full bg-[#121216] border border-[#24242c] h-2 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-200 ${
                status === "completed"
                  ? "bg-emerald-500"
                  : status === "failed"
                  ? "bg-red-500"
                  : "bg-blue-600"
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Metric Numbers */}
          <div className="flex justify-between text-[11px] text-[#a0a0b0] font-mono">
            <span>
              {processedFrames} / {totalFrames} frames ({progress.toFixed(0)}%)
            </span>
            <span>
              {fps > 0 ? `${fps} FPS • ` : ""}
              {etaSeconds > 0 ? `ETA: ${etaSeconds}s` : ""}
            </span>
          </div>

          {/* Stage Description */}
          <div className="text-[11px] text-white font-medium truncate" title={currentStage}>
            {currentStage}
          </div>

          {/* Error Message */}
          {status === "failed" && errorMessage && (
            <div className="bg-red-950/60 border border-red-800 rounded p-2 text-[11px] text-red-300">
              {errorMessage}
            </div>
          )}

          {/* Completed Quick Preview Actions */}
          {status === "completed" && (
            <div className="pt-2 flex items-center gap-2">
              {outputs.alpha && (
                <button
                  onClick={handlePreviewAlpha}
                  className="flex-1 py-1.5 px-2 rounded bg-[#22222a] hover:bg-blue-600 border border-[#30303c] hover:border-blue-500 text-white text-[11px] font-medium flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Layers className="w-3 h-3 text-blue-400" />
                  <span>Preview Alpha Matte</span>
                </button>
              )}

              {outputs.foreground && (
                <button
                  onClick={handlePreviewForeground}
                  className="flex-1 py-1.5 px-2 rounded bg-[#22222a] hover:bg-blue-600 border border-[#30303c] hover:border-blue-500 text-white text-[11px] font-medium flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Film className="w-3 h-3 text-emerald-400" />
                  <span>Preview Foreground</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
