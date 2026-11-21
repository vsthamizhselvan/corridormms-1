import React, { useEffect } from "react";
import { Cpu, HardDrive, Activity, Zap, CheckCircle2 } from "lucide-react";
import { useSettingsStore } from "../../project/settingsStore";
import { useInspectorStore } from "../../project/inspectorStore";
import { useWorkspaceStore } from "../../project/workspaceStore";

export const StatusBar: React.FC = () => {
  const { hardware, setHardware } = useSettingsStore();
  const { setActiveTab } = useInspectorStore();
  const { showInspector } = useWorkspaceStore();

  const openPerformance = () => {
    setActiveTab("performance");
  };

  // Try to query real hardware info via Tauri command or python detector
  useEffect(() => {
    const fetchHardware = async () => {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const hw: any = await invoke("get_hardware_status");
        if (hw) {
          setHardware(hw);
        }
      } catch {
        // Fallback or web dev mode - hardware remains default
      }
    };
    fetchHardware();
  }, [setHardware]);

  const backendBadgeColor =
    hardware.activeBackend === "cuda"
      ? "bg-green-950/80 text-green-400 border-green-800"
      : hardware.activeBackend === "mps"
      ? "bg-purple-950/80 text-purple-400 border-purple-800"
      : "bg-blue-950/80 text-blue-400 border-blue-800";

  return (
    <div className="h-6 bg-[#121216] border-t border-[#24242c] flex items-center justify-between px-3 text-[10px] select-none text-[#808090] font-sans">
      {/* Left: Hardware Backend Indicators */}
      <div className="flex items-center gap-4">
        {/* Backend Tag */}
        <div
          onClick={openPerformance}
          title="Click to open Performance Telemetry"
          className="flex items-center gap-1.5 cursor-pointer hover:opacity-90 transition-opacity"
        >
          <Zap className="w-3 h-3 text-amber-400" />
          <span className="font-semibold text-[#a0a0b0]">BACKEND:</span>
          <span
            className={`px-1.5 py-0.2 rounded border font-mono font-medium uppercase ${backendBadgeColor}`}
          >
            {hardware.activeBackend}
          </span>
          <span className="text-[#a0a0b0] font-mono">({hardware.gpuName})</span>
        </div>

        {/* Separator */}
        <span className="text-[#30303c]">•</span>

        {/* CPU */}
        <div
          onClick={openPerformance}
          title="Click to view CPU & RAM Telemetry"
          className="flex items-center gap-1.5 cursor-pointer hover:text-white transition-colors"
        >
          <Cpu className="w-3 h-3 text-[#707080]" />
          <span>{hardware.cpuModel} ({hardware.cpuThreads} Threads)</span>
        </div>

        {/* Separator */}
        <span className="text-[#30303c]">•</span>

        {/* RAM */}
        <div
          onClick={openPerformance}
          title="Click to view RAM Telemetry"
          className="flex items-center gap-1.5 cursor-pointer hover:text-white transition-colors"
        >
          <HardDrive className="w-3 h-3 text-[#707080]" />
          <span>{(hardware.availableRamMb / 1024).toFixed(1)} GB Free / {(hardware.totalRamMb / 1024).toFixed(0)} GB RAM</span>
        </div>
      </div>

      {/* Right: Engine State */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium">ENGINE IDLE</span>
        </div>

        <span className="text-[#30303c]">•</span>

        <span className="text-[#606070] font-mono">CorridorKey v2.0 Desktop</span>
      </div>
    </div>
  );
};
