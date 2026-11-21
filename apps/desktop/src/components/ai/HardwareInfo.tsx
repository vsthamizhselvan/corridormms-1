import React, { useEffect } from "react";
import { Zap, Cpu, HardDrive, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { useAiEngineStore } from "../../stores/aiEngineStore";

export const HardwareInfo: React.FC = () => {
  const { hardware, detectHardware, isLoading } = useAiEngineStore();

  useEffect(() => {
    if (!hardware) {
      detectHardware();
    }
  }, [hardware, detectHardware]);

  if (!hardware) {
    return (
      <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 flex items-center justify-between text-xs text-[#808090]">
        <span>Probing acceleration hardware...</span>
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
      </div>
    );
  }

  const primaryGpu = hardware.devices.find((d) => d.backend !== "cpu") || hardware.devices[0];

  const backendBadgeColor =
    hardware.recommended_backend === "cuda"
      ? "bg-emerald-950/80 text-emerald-400 border-emerald-800"
      : hardware.recommended_backend === "mps"
      ? "bg-purple-950/80 text-purple-400 border-purple-800"
      : "bg-blue-950/80 text-blue-400 border-blue-800";

  return (
    <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-2 text-xs">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          Hardware Acceleration
        </span>
        <button
          onClick={() => detectHardware()}
          disabled={isLoading}
          title="Re-scan Hardware"
          className="p-1 rounded hover:bg-[#282834] text-[#707080] hover:text-white"
        >
          <RefreshCw className={`w-3 h-3 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Recommended Device Tag */}
      <div className="flex items-center justify-between pt-1 border-t border-[#24242c]">
        <span className="text-[#a0a0b0]">Active Backend:</span>
        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase border ${backendBadgeColor}`}>
          {hardware.recommended_backend}
        </span>
      </div>

      {/* GPU Name & VRAM */}
      {primaryGpu && (
        <div className="flex items-center justify-between">
          <span className="text-[#a0a0b0]">Accelerator:</span>
          <span className="text-white font-medium truncate max-w-[170px]" title={primaryGpu.name}>
            {primaryGpu.name}
          </span>
        </div>
      )}

      {primaryGpu && primaryGpu.compute_capability && (
        <div className="flex items-center justify-between">
          <span className="text-[#a0a0b0]">Compute Arch:</span>
          <span className="text-white font-mono text-[11px]">{primaryGpu.compute_capability}</span>
        </div>
      )}

      {/* Host CPU & Memory */}
      <div className="flex items-center justify-between">
        <span className="text-[#a0a0b0]">Host CPU:</span>
        <span className="text-white truncate max-w-[170px]">{hardware.cpu_model} ({hardware.cpu_threads}T)</span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[#a0a0b0]">System Memory:</span>
        <span className="text-white font-mono text-[11px]">
          {(hardware.available_ram_mb / 1024).toFixed(1)} GB Free / {(hardware.total_ram_mb / 1024).toFixed(0)} GB Total
        </span>
      </div>

      {/* FFmpeg status */}
      <div className="flex items-center justify-between pt-1 border-t border-[#24242c] text-[11px]">
        <span className="text-[#a0a0b0]">FFmpeg Video IO:</span>
        <span className={hardware.ffmpeg_available ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}>
          {hardware.ffmpeg_available ? "Verified Ready" : "Missing from PATH"}
        </span>
      </div>
    </div>
  );
};
