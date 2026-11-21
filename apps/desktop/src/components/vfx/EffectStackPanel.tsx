import React, { useState } from "react";
import { Plus, Trash2, Copy, Eye, EyeOff, ChevronUp, ChevronDown, Sparkles, Sliders } from "lucide-react";
import { useVFXStore, EffectItem } from "../../stores/vfxStore";

export const EffectStackPanel: React.FC = () => {
  const {
    effects,
    selectedEffectId,
    addEffect,
    removeEffect,
    duplicateEffect,
    toggleEffect,
    reorderEffect,
    updateEffectParams,
    selectEffect,
  } = useVFXStore();

  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);

  const availableEffects = [
    { type: "gaussian_blur", name: "Gaussian Blur" },
    { type: "sharpen", name: "Sharpen" },
    { type: "glow", name: "Glow" },
    { type: "drop_shadow", name: "Drop Shadow" },
    { type: "gaussian_noise", name: "Gaussian Noise" },
    { type: "film_grain", name: "Film Grain" },
    { type: "vignette", name: "Vignette" },
    { type: "hue_saturation", name: "Hue / Saturation" },
    { type: "color_correction", name: "Colour Correction" },
    { type: "spill_suppression", name: "Chroma Spill Suppression" },
  ];

  const selectedEffect = effects.find((e) => e.id === selectedEffectId);

  return (
    <div className="space-y-4 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[#808090] uppercase tracking-wider text-[11px]">
          Non-Destructive Effect Stack ({effects.length})
        </span>

        <div className="relative">
          <button
            onClick={() => setIsAddMenuOpen(!isAddMenuOpen)}
            className="px-2 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium flex items-center gap-1 text-[11px] transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Effect</span>
          </button>

          {isAddMenuOpen && (
            <div className="absolute right-0 top-full mt-1 w-52 bg-[#1c1c24] border border-[#2c2c38] rounded-lg shadow-xl py-1 z-50">
              {availableEffects.map((eff) => (
                <button
                  key={eff.type}
                  onClick={() => {
                    addEffect(eff.type);
                    setIsAddMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-blue-600 hover:text-white text-slate-200 text-xs block transition-colors"
                >
                  {eff.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Effects List */}
      <div className="space-y-1.5 max-h-52 overflow-y-auto">
        {effects.map((eff, index) => {
          const isSelected = eff.id === selectedEffectId;
          return (
            <div
              key={eff.id}
              onClick={() => selectEffect(eff.id)}
              className={`p-2.5 rounded-lg border flex items-center justify-between cursor-pointer transition-colors ${
                isSelected
                  ? "bg-blue-950/40 border-blue-500/60 text-white"
                  : "bg-[#181820] border-[#262630] text-[#a0a0b0] hover:bg-[#202028]"
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <span className="text-[10px] font-mono text-[#606070] w-4">{index + 1}.</span>
                <span className="truncate font-medium">{eff.name}</span>
              </div>

              <div className="flex items-center gap-1">
                {/* Reorder Up */}
                <button
                  disabled={index === 0}
                  onClick={(e) => {
                    e.stopPropagation();
                    reorderEffect(eff.id, index - 1);
                  }}
                  className="p-1 hover:text-white disabled:opacity-20"
                >
                  <ChevronUp className="w-3.5 h-3.5" />
                </button>

                {/* Reorder Down */}
                <button
                  disabled={index === effects.length - 1}
                  onClick={(e) => {
                    e.stopPropagation();
                    reorderEffect(eff.id, index + 1);
                  }}
                  className="p-1 hover:text-white disabled:opacity-20"
                >
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>

                {/* Duplicate */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    duplicateEffect(eff.id);
                  }}
                  title="Duplicate Effect"
                  className="p-1 hover:text-white"
                >
                  <Copy className="w-3 h-3" />
                </button>

                {/* Enable / Disable */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleEffect(eff.id);
                  }}
                  title={eff.enabled ? "Disable Effect" : "Enable Effect"}
                  className={`p-1 ${eff.enabled ? "text-teal-400" : "text-[#505060]"}`}
                >
                  {eff.enabled ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                </button>

                {/* Remove */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeEffect(eff.id);
                  }}
                  title="Delete Effect"
                  className="p-1 hover:text-red-400"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}

        {effects.length === 0 && (
          <div className="text-center py-6 text-[#606070] italic border border-dashed border-[#262630] rounded-lg">
            No effects in stack. Click &quot;Add Effect&quot; above to add one.
          </div>
        )}
      </div>

      {/* Selected Effect Parameter Editor */}
      {selectedEffect && (
        <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
          <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center justify-between">
            <span>{selectedEffect.name} Parameters</span>
            <span className="text-[10px] text-[#707080] font-mono">{selectedEffect.type}</span>
          </div>

          {/* Dynamic parameter controls based on type */}
          {selectedEffect.type === "gaussian_blur" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Blur Radius</span>
                <span className="font-mono text-white">{selectedEffect.parameters.radius?.toFixed(1) ?? "10.0"} px</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={selectedEffect.parameters.radius ?? 10.0}
                onChange={(e) => updateEffectParams(selectedEffect.id, { radius: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}

          {selectedEffect.type === "sharpen" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Sharpen Strength</span>
                <span className="font-mono text-white">{selectedEffect.parameters.strength?.toFixed(2) ?? "1.00"}</span>
              </div>
              <input
                type="range"
                min="0"
                max="3"
                step="0.05"
                value={selectedEffect.parameters.strength ?? 1.0}
                onChange={(e) => updateEffectParams(selectedEffect.id, { strength: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}

          {selectedEffect.type === "glow" && (
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-[#9090a0]">Glow Intensity</span>
                  <span className="font-mono text-white">{selectedEffect.parameters.intensity?.toFixed(2) ?? "1.00"}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="0.05"
                  value={selectedEffect.parameters.intensity ?? 1.0}
                  onChange={(e) => updateEffectParams(selectedEffect.id, { intensity: parseFloat(e.target.value) })}
                  className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
                />
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-[#9090a0]">Glow Radius</span>
                  <span className="font-mono text-white">{selectedEffect.parameters.radius?.toFixed(0) ?? "20"} px</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="60"
                  step="1"
                  value={selectedEffect.parameters.radius ?? 20}
                  onChange={(e) => updateEffectParams(selectedEffect.id, { radius: parseFloat(e.target.value) })}
                  className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
                />
              </div>
            </div>
          )}

          {selectedEffect.type === "film_grain" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Grain Intensity</span>
                <span className="font-mono text-white">{((selectedEffect.parameters.intensity ?? 0.08) * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.3"
                step="0.01"
                value={selectedEffect.parameters.intensity ?? 0.08}
                onChange={(e) => updateEffectParams(selectedEffect.id, { intensity: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}

          {selectedEffect.type === "vignette" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Vignette Amount</span>
                <span className="font-mono text-white">{((selectedEffect.parameters.amount ?? 0.5) * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.02"
                value={selectedEffect.parameters.amount ?? 0.5}
                onChange={(e) => updateEffectParams(selectedEffect.id, { amount: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}

          {selectedEffect.type === "hue_saturation" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Hue Shift</span>
                <span className="font-mono text-white">{selectedEffect.parameters.hueShift?.toFixed(0) ?? "0"}°</span>
              </div>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={selectedEffect.parameters.hueShift ?? 0}
                onChange={(e) => updateEffectParams(selectedEffect.id, { hueShift: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}

          {selectedEffect.type === "spill_suppression" && (
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-[#9090a0]">Suppression Strength</span>
                <span className="font-mono text-white">{((selectedEffect.parameters.strength ?? 0.8) * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.02"
                value={selectedEffect.parameters.strength ?? 0.8}
                onChange={(e) => updateEffectParams(selectedEffect.id, { strength: parseFloat(e.target.value) })}
                className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
