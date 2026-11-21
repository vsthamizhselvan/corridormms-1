import React from "react";
import { Sliders, Sun, Thermometer, Droplet, RotateCcw, Palette } from "lucide-react";
import { useVFXStore } from "../../stores/vfxStore";

export const ColorGradePanel: React.FC = () => {
  const { colorGrade, updateColorGrade, resetColorGrade } = useVFXStore();

  return (
    <div className="space-y-4 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[#808090] uppercase tracking-wider text-[11px]">
          Colour Correction & Grading
        </span>
        <button
          onClick={resetColorGrade}
          className="p-1 rounded hover:bg-[#282834] text-[#808090] hover:text-white flex items-center gap-1 text-[10px]"
          title="Reset Grading"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Primary Exposure & Tones */}
      <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
        <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center gap-1.5">
          <Sun className="w-3.5 h-3.5 text-amber-400" />
          <span>Exposure & Tone Controls</span>
        </div>

        {/* Exposure EV */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Exposure (EV)</span>
            <span className="font-mono text-white">{colorGrade.exposure > 0 ? `+${colorGrade.exposure.toFixed(2)}` : colorGrade.exposure.toFixed(2)} EV</span>
          </div>
          <input
            type="range"
            min="-3"
            max="3"
            step="0.05"
            value={colorGrade.exposure}
            onChange={(e) => updateColorGrade({ exposure: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Contrast */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Contrast</span>
            <span className="font-mono text-white">{colorGrade.contrast.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.3"
            max="2.5"
            step="0.05"
            value={colorGrade.contrast}
            onChange={(e) => updateColorGrade({ contrast: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Highlights & Shadows */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#808090]">Highlights</span>
              <span className="font-mono text-white">{colorGrade.highlights.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.05"
              value={colorGrade.highlights}
              onChange={(e) => updateColorGrade({ highlights: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>

          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#808090]">Shadows</span>
              <span className="font-mono text-white">{colorGrade.shadows.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.05"
              value={colorGrade.shadows}
              onChange={(e) => updateColorGrade({ shadows: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>
        </div>
      </div>

      {/* White Balance & Saturation */}
      <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
        <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center gap-1.5">
          <Thermometer className="w-3.5 h-3.5 text-sky-400" />
          <span>White Balance & Color Intensity</span>
        </div>

        {/* Temperature */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Temperature (Cool ↔ Warm)</span>
            <span className="font-mono text-white">{colorGrade.temperature.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="-1"
            max="1"
            step="0.02"
            value={colorGrade.temperature}
            onChange={(e) => updateColorGrade({ temperature: parseFloat(e.target.value) })}
            className="w-full accent-amber-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Tint */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Tint (Green ↔ Magenta)</span>
            <span className="font-mono text-white">{colorGrade.tint.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="-1"
            max="1"
            step="0.02"
            value={colorGrade.tint}
            onChange={(e) => updateColorGrade({ tint: parseFloat(e.target.value) })}
            className="w-full accent-purple-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Saturation */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Saturation</span>
            <span className="font-mono text-white">{(colorGrade.saturation * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="2.5"
            step="0.05"
            value={colorGrade.saturation}
            onChange={(e) => updateColorGrade({ saturation: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        {/* Vibrance */}
        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Vibrance</span>
            <span className="font-mono text-white">{colorGrade.vibrance.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="-1"
            max="1"
            step="0.05"
            value={colorGrade.vibrance}
            onChange={(e) => updateColorGrade({ vibrance: parseFloat(e.target.value) })}
            className="w-full accent-teal-500 h-1 bg-[#282834] rounded"
          />
        </div>
      </div>

      {/* Lift / Gamma / Gain (ASC-CDL) */}
      <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
        <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center gap-1.5">
          <Palette className="w-3.5 h-3.5 text-teal-400" />
          <span>ASC-CDL Color Wheels (Lift / Gamma / Gain)</span>
        </div>

        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Lift (Shadows)</span>
            <span className="font-mono text-white">{colorGrade.lift.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="-0.5"
            max="0.5"
            step="0.02"
            value={colorGrade.lift}
            onChange={(e) => updateColorGrade({ lift: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Gamma (Midtones)</span>
            <span className="font-mono text-white">{colorGrade.gamma.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.3"
            max="2.5"
            step="0.05"
            value={colorGrade.gamma}
            onChange={(e) => updateColorGrade({ gamma: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>

        <div>
          <div className="flex justify-between text-[11px] mb-1">
            <span className="text-[#9090a0]">Gain (Highlights)</span>
            <span className="font-mono text-white">{colorGrade.gain.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.0"
            max="2.5"
            step="0.05"
            value={colorGrade.gain}
            onChange={(e) => updateColorGrade({ gain: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
          />
        </div>
      </div>
    </div>
  );
};
