import React from "react";
import { Plus, Trash2, Eye, EyeOff, Lock, Unlock, Layers, Move } from "lucide-react";
import { useVFXStore, LayerItem } from "../../stores/vfxStore";

export const LayersPanel: React.FC = () => {
  const { layers, selectedLayerId, addLayer, removeLayer, updateLayer, selectLayer } = useVFXStore();

  const selectedLayer = layers.find((l) => l.id === selectedLayerId);

  return (
    <div className="space-y-4 text-xs select-none">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[#808090] uppercase tracking-wider text-[11px]">
          Composite Layers ({layers.length})
        </span>

        <button
          onClick={() => addLayer("video", `Layer ${layers.length + 1}`)}
          className="px-2 py-1 rounded bg-teal-600 hover:bg-teal-500 text-white font-medium flex items-center gap-1 text-[11px] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Layer</span>
        </button>
      </div>

      {/* Layer List */}
      <div className="space-y-1.5 max-h-48 overflow-y-auto">
        {layers.map((layer) => {
          const isSelected = layer.id === selectedLayerId;
          return (
            <div
              key={layer.id}
              onClick={() => selectLayer(layer.id)}
              className={`p-2.5 rounded-lg border flex items-center justify-between cursor-pointer transition-colors ${
                isSelected
                  ? "bg-teal-950/40 border-teal-500/60 text-white"
                  : "bg-[#181820] border-[#262630] text-[#a0a0b0] hover:bg-[#202028]"
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <Layers className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                <span className="truncate font-medium">{layer.name}</span>
                <span className="text-[10px] opacity-60 uppercase">[{layer.blendMode}]</span>
              </div>

              <div className="flex items-center gap-1">
                {/* Visibility */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateLayer(layer.id, { visible: !layer.visible });
                  }}
                  className="p-1 hover:text-white"
                >
                  {layer.visible ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5 text-amber-500" />}
                </button>

                {/* Lock */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateLayer(layer.id, { locked: !layer.locked });
                  }}
                  className="p-1 hover:text-white"
                >
                  {layer.locked ? <Lock className="w-3.5 h-3.5 text-red-400" /> : <Unlock className="w-3.5 h-3.5" />}
                </button>

                {/* Delete */}
                {layers.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeLayer(layer.id);
                    }}
                    className="p-1 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Layer Properties */}
      {selectedLayer && (
        <div className="bg-[#181820] border border-[#282834] rounded-lg p-3 space-y-3">
          <div className="font-semibold text-white border-b border-[#262630] pb-1.5 flex items-center justify-between">
            <span>{selectedLayer.name} Blending & Transforms</span>
          </div>

          {/* Blend Mode */}
          <div>
            <label className="text-[10px] text-[#808090]">Blend Mode</label>
            <select
              value={selectedLayer.blendMode}
              onChange={(e) => updateLayer(selectedLayer.id, { blendMode: e.target.value as any })}
              className="w-full mt-0.5 bg-[#121216] border border-[#2c2c36] rounded px-2 py-1 text-white text-xs"
            >
              <option value="normal">Normal</option>
              <option value="multiply">Multiply</option>
              <option value="screen">Screen</option>
              <option value="add">Add (Linear Dodge)</option>
              <option value="overlay">Overlay</option>
              <option value="difference">Difference</option>
            </select>
          </div>

          {/* Opacity */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-[#9090a0]">Layer Opacity</span>
              <span className="font-mono text-white">{(selectedLayer.opacity * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={selectedLayer.opacity}
              onChange={(e) => updateLayer(selectedLayer.id, { opacity: parseFloat(e.target.value) })}
              className="w-full accent-blue-500 h-1 bg-[#282834] rounded"
            />
          </div>

          {/* Position X / Y */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-[#808090]">Position X</span>
                <span className="font-mono text-white">{selectedLayer.posX.toFixed(0)} px</span>
              </div>
              <input
                type="range"
                min="-500"
                max="500"
                step="1"
                value={selectedLayer.posX}
                onChange={(e) => updateLayer(selectedLayer.id, { posX: parseFloat(e.target.value) })}
                className="w-full accent-teal-500 h-1 bg-[#282834] rounded"
              />
            </div>

            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-[#808090]">Position Y</span>
                <span className="font-mono text-white">{selectedLayer.posY.toFixed(0)} px</span>
              </div>
              <input
                type="range"
                min="-500"
                max="500"
                step="1"
                value={selectedLayer.posY}
                onChange={(e) => updateLayer(selectedLayer.id, { posY: parseFloat(e.target.value) })}
                className="w-full accent-teal-500 h-1 bg-[#282834] rounded"
              />
            </div>
          </div>

          {/* Scale & Rotation */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-[#808090]">Scale</span>
                <span className="font-mono text-white">{(selectedLayer.scaleX * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="3.0"
                step="0.05"
                value={selectedLayer.scaleX}
                onChange={(e) => {
                  const s = parseFloat(e.target.value);
                  updateLayer(selectedLayer.id, { scaleX: s, scaleY: s });
                }}
                className="w-full accent-teal-500 h-1 bg-[#282834] rounded"
              />
            </div>

            <div>
              <div className="flex justify-between text-[10px] mb-1">
                <span className="text-[#808090]">Rotation</span>
                <span className="font-mono text-white">{selectedLayer.rotation.toFixed(0)}°</span>
              </div>
              <input
                type="range"
                min="-180"
                max="180"
                step="1"
                value={selectedLayer.rotation}
                onChange={(e) => updateLayer(selectedLayer.id, { rotation: parseFloat(e.target.value) })}
                className="w-full accent-teal-500 h-1 bg-[#282834] rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
