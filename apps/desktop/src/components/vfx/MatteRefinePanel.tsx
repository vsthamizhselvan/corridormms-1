import React from "react";
import { Sliders, RotateCcw } from "lucide-react";
import { useVFXStore } from "../../stores/vfxStore";

export const MatteRefinePanel: React.FC = () => {
  const { matteRefine, updateMatteRefine, resetMatteRefine } = useVFXStore();

  return (
    <div className="space-y-4 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[#808090] uppercase tracking-wider text-[11px]">
          Alpha Matte Refinement
        </span>
        <button
          onClick={resetMatteRefine}
          className="p-1 rounded hover:bg-[#282834] text-[#808090] hover:text-white flex items-center gap-1 text-[10px]"
          title="Reset Matte Refinement"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
        {/* Choke & Expand */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Choke / Expand</span>
            <span className="font-mono text-white">{matteRefine.chokeExpand.toFixed(1)} px</span>
          </div>
          <input
            type="range"
            min="-20"
            max="20"
            step="0.5"
            value={matteRefine.chokeExpand}
            onChange={(e) => updateMatteRefine({ chokeExpand: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Edge Softness */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Edge Softness</span>
            <span className="font-mono text-white">{matteRefine.edgeSoftness.toFixed(1)} px</span>
          </div>
          <input
            type="range"
            min="0"
            max="20"
            step="0.5"
            value={matteRefine.edgeSoftness}
            onChange={(e) => updateMatteRefine({ edgeSoftness: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Edge Feather */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Edge Feather</span>
            <span className="font-mono text-white">{matteRefine.edgeFeather.toFixed(1)} px</span>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            step="0.5"
            value={matteRefine.edgeFeather}
            onChange={(e) => updateMatteRefine({ edgeFeather: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Alpha Threshold */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Alpha Threshold (Pedestal)</span>
            <span className="font-mono text-white">{matteRefine.alphaThreshold.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="0.8"
            step="0.01"
            value={matteRefine.alphaThreshold}
            onChange={(e) => updateMatteRefine({ alphaThreshold: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Matte Contrast */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Matte Contrast</span>
            <span className="font-mono text-white">{matteRefine.contrast.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.2"
            max="3.0"
            step="0.05"
            value={matteRefine.contrast}
            onChange={(e) => updateMatteRefine({ contrast: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Edge Decontamination */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Edge Decontamination</span>
            <span className="font-mono text-white">{(matteRefine.edgeDecontamination * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={matteRefine.edgeDecontamination}
            onChange={(e) => updateMatteRefine({ edgeDecontamination: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Spill Suppression */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Background Spill Suppression</span>
            <span className="font-mono text-white">{(matteRefine.spillSuppression * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={matteRefine.spillSuppression}
            onChange={(e) => updateMatteRefine({ spillSuppression: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        <div className="pt-2 border-t border-[#262630]">
          <label className="flex items-center gap-1.5 cursor-pointer text-xs">
            <input
              type="checkbox"
              checked={matteRefine.invert}
              onChange={(e) => updateMatteRefine({ invert: e.target.checked })}
              className="rounded border-[#30303c] bg-[#121216] text-blue-500"
            />
            <span className="text-white">Invert Alpha Matte</span>
          </label>
        </div>
      </div>
    </div>
  );
};
