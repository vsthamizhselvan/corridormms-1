import React, { useEffect } from "react";
import { Sparkles, CheckCircle, AlertCircle, RefreshCw, Download, Database } from "lucide-react";
import { useAiEngineStore } from "../../stores/aiEngineStore";

export const ModelStatus: React.FC = () => {
  const { modelStatus, checkModelStatus, loadModel, isLoading } = useAiEngineStore();

  useEffect(() => {
    if (!modelStatus) {
      checkModelStatus();
    }
  }, [modelStatus, checkModelStatus]);

  if (!modelStatus) {
    return (
      <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 flex items-center justify-between text-xs text-[#808090]">
        <span>Checking CorridorKey 2.0 assets...</span>
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-2.5 text-xs">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider flex items-center gap-1.5">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          Model Weights Integrity
        </span>
        <button
          onClick={() => checkModelStatus()}
          title="Re-check Weights"
          className="p-1 rounded hover:bg-[#282834] text-[#707080] hover:text-white"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      </div>

      {/* Model Name & Loaded Badge */}
      <div className="flex items-center justify-between pt-1 border-t border-[#24242c]">
        <div>
          <div className="text-white font-medium">CorridorKey 2.0</div>
          <div className="text-[10px] text-[#707080]">Transformer-Native Two-Stage Architecture</div>
        </div>

        <span
          className={`px-2 py-0.5 rounded text-[10px] font-medium flex items-center gap-1 border ${
            modelStatus.is_loaded
              ? "bg-emerald-950/80 text-emerald-400 border-emerald-800"
              : "bg-[#24242e] text-[#a0a0b0] border-[#30303e]"
          }`}
        >
          {modelStatus.is_loaded ? <CheckCircle className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
          <span>{modelStatus.is_loaded ? "Cached in VRAM" : "Unloaded"}</span>
        </span>
      </div>

      {/* Foundation Checkpoints Checklist */}
      <div className="space-y-1 bg-[#141418] border border-[#24242c] rounded p-2 text-[11px]">
        {Object.entries(modelStatus.assets).map(([key, asset]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-[#a0a0b0] truncate max-w-[170px]" title={asset.name}>
              {key}:
            </span>
            <span className={asset.exists ? "text-emerald-400 font-mono" : "text-amber-400 font-mono"}>
              {asset.exists ? `${asset.size_mb} MB` : "Download Needed"}
            </span>
          </div>
        ))}
      </div>

      {/* Action: Load Model / Weights Info */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] text-[#707080]">
          Total Checkpoint Size: {modelStatus.total_size_gb} GB
        </span>

        <button
          onClick={() => loadModel()}
          disabled={isLoading || modelStatus.is_loaded}
          className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
            modelStatus.is_loaded
              ? "bg-[#22222a] text-[#707080] cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-500 text-white shadow-sm"
          }`}
        >
          {isLoading && <RefreshCw className="w-3 h-3 animate-spin" />}
          <span>{modelStatus.is_loaded ? "Model Ready" : "Pre-load Model"}</span>
        </button>
      </div>
    </div>
  );
};
