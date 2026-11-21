import React from "react";
import { Plus, Trash2, Eye, EyeOff, Square, Circle, PenTool, Spline, Shield, Sliders } from "lucide-react";
import { useVFXStore, MaskItem } from "../../stores/vfxStore";

export const MasksPanel: React.FC = () => {
  const { masks, selectedMaskId, addMask, removeMask, updateMask, selectMask } = useVFXStore();

  const selectedMask = masks.find((m) => m.id === selectedMaskId);

  return (
    <div className="space-y-4 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[#808090] uppercase tracking-wider text-[11px]">
          Vector Masks ({masks.length})
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => addMask("rectangle")}
            title="Add Rectangle Mask"
            className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
          >
            <Square className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => addMask("ellipse")}
            title="Add Ellipse Mask"
            className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
          >
            <Circle className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => addMask("bezier")}
            title="Add Bezier Path Mask"
            className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
          >
            <Spline className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => addMask("polygon")}
            title="Add Polygon Mask"
            className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
          >
            <PenTool className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mask List */}
      <div className="space-y-1.5 max-h-40 overflow-y-auto">
        {masks.map((mask) => {
          const isSelected = mask.id === selectedMaskId;
          return (
            <div
              key={mask.id}
              onClick={() => selectMask(mask.id)}
              className={`p-2 rounded border flex items-center justify-between cursor-pointer transition-colors ${
                isSelected
                  ? "bg-teal-950/40 border-teal-500/60 text-white"
                  : "bg-[#181820] border-[#262630] text-[#a0a0b0] hover:bg-[#202028]"
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                {mask.type === "rectangle" && <Square className="w-3.5 h-3.5 text-teal-400" />}
                {mask.type === "ellipse" && <Circle className="w-3.5 h-3.5 text-sky-400" />}
                {mask.type === "bezier" && <Spline className="w-3.5 h-3.5 text-purple-400" />}
                {mask.type === "polygon" && <PenTool className="w-3.5 h-3.5 text-amber-400" />}
                <span className="truncate font-medium">{mask.name}</span>
                <span className="text-[10px] opacity-60 uppercase">[{mask.mode}]</span>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateMask(mask.id, { visible: !mask.visible });
                  }}
                  className="p-1 hover:text-white"
                >
                  {mask.visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5 text-amber-500" />}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeMask(mask.id);
                  }}
                  className="p-1 hover:text-red-400"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
        {masks.length === 0 && (
          <div className="text-center py-4 text-[#606070] italic">
            No masks created. Click an icon above to add a mask.
          </div>
        )}
      </div>

      {/* Selected Mask Inspector */}
      {selectedMask && (
        <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
          <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center justify-between">
            <span>{selectedMask.name} Settings</span>
            <span className="text-[10px] text-[#707080] capitalize">{selectedMask.type}</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-[#808090]">Mode</label>
              <select
                value={selectedMask.mode}
                onChange={(e) => updateMask(selectedMask.id, { mode: e.target.value as any })}
                className="w-full mt-0.5 bg-[#121216] border border-[#2c2c36] rounded px-2 py-1 text-white text-xs"
              >
                <option value="add">Add</option>
                <option value="subtract">Subtract</option>
              </select>
            </div>

            <div className="flex items-center pt-4">
              <label className="flex items-center gap-1.5 cursor-pointer text-xs">
                <input
                  type="checkbox"
                  checked={selectedMask.inverted}
                  onChange={(e) => updateMask(selectedMask.id, { inverted: e.target.checked })}
                  className="rounded border-[#30303c] bg-[#121216] text-blue-500"
                />
                <span className="text-white">Invert Mask</span>
              </label>
            </div>
          </div>

          {/* Feather Slider */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-[#9090a0]">Feather</span>
              <span className="font-mono text-white">{selectedMask.feather.toFixed(1)} px</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="0.5"
              value={selectedMask.feather}
              onChange={(e) => updateMask(selectedMask.id, { feather: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>

          {/* Expansion / Choke Slider */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-[#9090a0]">Expansion / Choke</span>
              <span className="font-mono text-white">{selectedMask.expansion.toFixed(1)} px</span>
            </div>
            <input
              type="range"
              min="-30"
              max="30"
              step="0.5"
              value={selectedMask.expansion}
              onChange={(e) => updateMask(selectedMask.id, { expansion: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>

          {/* Opacity Slider */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-[#9090a0]">Mask Opacity</span>
              <span className="font-mono text-white">{(selectedMask.opacity * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={selectedMask.opacity}
              onChange={(e) => updateMask(selectedMask.id, { opacity: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>
        </div>
      )}
    </div>
  );
};
