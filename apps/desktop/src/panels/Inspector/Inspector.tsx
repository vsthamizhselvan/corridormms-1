import React, { useState } from "react";
import {
  FileText,
  Sparkles,
  Sliders,
  Move,
  Layers,
  Cpu,
  Info,
  CheckCircle,
  AlertCircle,
  Lock,
  Download,
  Activity,
  Palette,
  Square,
  Sun,
  Wand2,
} from "lucide-react";
import { useInspectorStore, InspectorTab } from "../../project/inspectorStore";
import { useMediaStore } from "../../project/mediaStore";
import { HardwareInfo } from "../../components/ai/HardwareInfo";
import { ModelStatus } from "../../components/ai/ModelStatus";
import { ProcessingPanel } from "../../components/ai/ProcessingPanel";
import { ExportPanel } from "../../components/export/ExportPanel";
import { VideoProcessingPanel } from "../../components/pipeline/VideoProcessingPanel";
import { useViewerStore } from "../../stores/viewerStore";
import { MasksPanel } from "../../components/vfx/MasksPanel";
import { MatteRefinePanel } from "../../components/vfx/MatteRefinePanel";
import { ColorGradePanel } from "../../components/vfx/ColorGradePanel";
import { EffectStackPanel } from "../../components/vfx/EffectStackPanel";
import { LayersPanel } from "../../components/vfx/LayersPanel";
import { NodeEditorModal } from "../../components/vfx/NodeEditorModal";
import { PerformancePanel } from "../../components/performance/PerformancePanel";
import { Gauge } from "lucide-react";

export const Inspector: React.FC = () => {
  const { activeTab, setActiveTab, keying, matte, transform, updateKeying, updateMatte, updateTransform } =
    useInspectorStore();
  const { media, selectedMediaId } = useMediaStore();
  const {
    backgroundType,
    backgroundColor,
    gradientColorA,
    gradientColorB,
    compareMode,
    wipePosition,
    alphaMode,
    exposure,
    saturation,
    setBackgroundType,
    setBackgroundColor,
    setGradient,
    setCompareMode,
    setWipePosition,
    setAlphaMode,
    setExposure,
    setSaturation,
  } = useViewerStore();

  const [isNodeEditorOpen, setIsNodeEditorOpen] = useState(false);
  const selectedMedia = media.find((m) => m.id === selectedMediaId);

  const tabs: { id: InspectorTab; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: "media", label: "Media", icon: FileText },
    { id: "keying", label: "AI Keying", icon: Sparkles },
    { id: "matte", label: "Matte Refine", icon: Sliders },
    { id: "masks", label: "Masks", icon: Square },
    { id: "color", label: "Color Grade", icon: Sun },
    { id: "effects", label: "Effects", icon: Wand2 },
    { id: "layers", label: "Layers", icon: Layers },
    { id: "composite", label: "Composite", icon: Layers },
    { id: "background", label: "Background", icon: Palette },
    { id: "transform", label: "Transform", icon: Move },
    { id: "export", label: "Export", icon: Download },
    { id: "pipeline", label: "Pipeline", icon: Activity },
    { id: "performance", label: "Performance", icon: Gauge },
  ];

  return (
    <div className="h-full flex flex-col bg-[#16161a] border-l border-[#282830] select-none text-xs">
      {/* Tab Navigation Header */}
      <div className="h-8 bg-[#1e1e24] border-b border-[#282830] flex items-center px-1 gap-0.5 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-2.5 py-1 font-medium rounded text-[11px] flex items-center gap-1.5 transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-[#16161a] text-white border-t-2 border-blue-500"
                  : "text-[#8a8a96] hover:text-white"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}

        {/* Node Graph Launch Button */}
        <button
          onClick={() => setIsNodeEditorOpen(true)}
          className="ml-auto px-2 py-0.5 rounded bg-blue-600/30 hover:bg-blue-600 border border-blue-500/40 text-blue-300 hover:text-white font-medium text-[10px] flex items-center gap-1 shrink-0"
        >
          <Cpu className="w-3 h-3" />
          <span>Nodes</span>
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* TAB: MEDIA */}
        {activeTab === "media" && (
          <div className="space-y-3">
            <div className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider">
              Footage Properties
            </div>
            {selectedMedia ? (
              <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-2 text-xs">
                <div className="flex justify-between border-b border-[#24242c] pb-1.5">
                  <span className="text-[#808090]">Name:</span>
                  <span className="text-white font-medium truncate max-w-[180px]" title={selectedMedia.name}>
                    {selectedMedia.name}
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#24242c] pb-1.5">
                  <span className="text-[#808090]">Resolution:</span>
                  <span className="text-white font-mono">
                    {selectedMedia.width} x {selectedMedia.height}
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#24242c] pb-1.5">
                  <span className="text-[#808090]">Frame Rate:</span>
                  <span className="text-white font-mono">{selectedMedia.frameRate.toFixed(2)} fps</span>
                </div>
                <div className="flex justify-between border-b border-[#24242c] pb-1.5">
                  <span className="text-[#808090]">Duration:</span>
                  <span className="text-white font-mono">
                    {selectedMedia.durationFrames} frames ({selectedMedia.durationSeconds.toFixed(1)}s)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#808090]">Codec:</span>
                  <span className="text-white font-mono">{selectedMedia.codec}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-[#606070] italic border border-dashed border-[#24242c] rounded">
                No media selected
              </div>
            )}

            <div className="pt-2">
              <ModelStatus />
            </div>
          </div>
        )}

        {/* TAB: KEYING */}
        {activeTab === "keying" && (
          <div className="space-y-4">
            <ProcessingPanel />
          </div>
        )}

        {/* TAB: MATTE REFINE */}
        {activeTab === "matte" && (
          <div className="space-y-4">
            <MatteRefinePanel />
          </div>
        )}

        {/* TAB: MASKS */}
        {activeTab === "masks" && <MasksPanel />}

        {/* TAB: COLOR GRADE */}
        {activeTab === "color" && <ColorGradePanel />}

        {/* TAB: EFFECTS */}
        {activeTab === "effects" && <EffectStackPanel />}

        {/* TAB: LAYERS */}
        {activeTab === "layers" && <LayersPanel />}

        {/* TAB: COMPOSITE */}
        {activeTab === "composite" && (
          <div className="space-y-4">
            <div className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider">
              Composite & Alpha Modes
            </div>
            <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-3">
              <div>
                <label className="text-[11px] text-[#a0a0b0] block mb-1">Alpha Interpretation</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setAlphaMode("premultiplied")}
                    className={`py-1.5 rounded text-xs font-medium border ${
                      alphaMode === "premultiplied"
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                    }`}
                  >
                    Premultiplied
                  </button>
                  <button
                    onClick={() => setAlphaMode("straight")}
                    className={`py-1.5 rounded text-xs font-medium border ${
                      alphaMode === "straight"
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                    }`}
                  >
                    Straight Alpha
                  </button>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[#a0a0b0]">Exposure Adjustment</span>
                  <span className="text-white font-mono">{exposure > 0 ? `+${exposure.toFixed(1)}` : exposure.toFixed(1)} EV</span>
                </div>
                <input
                  type="range"
                  min="-3"
                  max="3"
                  step="0.1"
                  value={exposure}
                  onChange={(e) => setExposure(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 bg-[#282834] h-1.5 rounded cursor-pointer"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-[#a0a0b0]">Saturation</span>
                  <span className="text-white font-mono">{(saturation * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.05"
                  value={saturation}
                  onChange={(e) => setSaturation(parseFloat(e.target.value))}
                  className="w-full accent-blue-600 bg-[#282834] h-1.5 rounded cursor-pointer"
                />
              </div>
            </div>
          </div>
        )}

        {/* TAB: BACKGROUND */}
        {activeTab === "background" && (
          <div className="space-y-4">
            <div className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider">
              Viewer Background Mode
            </div>
            <div className="bg-[#1a1a20] border border-[#282832] rounded p-3 space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setBackgroundType("checkerboard")}
                  className={`py-1.5 rounded text-xs font-medium border ${
                    backgroundType === "checkerboard"
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                  }`}
                >
                  Checkerboard
                </button>
                <button
                  onClick={() => setBackgroundType("black")}
                  className={`py-1.5 rounded text-xs font-medium border ${
                    backgroundType === "black"
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                  }`}
                >
                  Black Solid
                </button>
                <button
                  onClick={() => setBackgroundType("white")}
                  className={`py-1.5 rounded text-xs font-medium border ${
                    backgroundType === "white"
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                  }`}
                >
                  White Solid
                </button>
                <button
                  onClick={() => setBackgroundType("gradient")}
                  className={`py-1.5 rounded text-xs font-medium border ${
                    backgroundType === "gradient"
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-[#141418] border-[#2c2c36] text-[#808090] hover:text-white"
                  }`}
                >
                  Gradient
                </button>
              </div>

              {backgroundType === "gradient" && (
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-[#24242c]">
                  <div>
                    <label className="text-[10px] text-[#808090] block mb-1">Color A</label>
                    <input
                      type="color"
                      value={gradientColorA}
                      onChange={(e) => setGradient(e.target.value, gradientColorB)}
                      className="w-full h-7 bg-transparent cursor-pointer rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-[#808090] block mb-1">Color B</label>
                    <input
                      type="color"
                      value={gradientColorB}
                      onChange={(e) => setGradient(gradientColorA, e.target.value)}
                      className="w-full h-7 bg-transparent cursor-pointer rounded"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB: TRANSFORM */}
        {activeTab === "transform" && (
          <div className="space-y-3">
            <div className="text-[11px] font-semibold text-[#808090] uppercase tracking-wider">
              2D Plate Transform
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-[#808090] block mb-1">Position X</label>
                <input
                  type="number"
                  value={transform.posX}
                  onChange={(e) => updateTransform({ posX: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#1c1c22] border border-[#282832] rounded px-2 py-1 text-white text-xs font-mono"
                />
              </div>
              <div>
                <label className="text-[10px] text-[#808090] block mb-1">Position Y</label>
                <input
                  type="number"
                  value={transform.posY}
                  onChange={(e) => updateTransform({ posY: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-[#1c1c22] border border-[#282832] rounded px-2 py-1 text-white text-xs font-mono"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#a0a0b0]">Scale</span>
                <span className="text-white font-mono">{transform.scale}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="200"
                step="1"
                value={transform.scale}
                onChange={(e) => updateTransform({ scale: parseInt(e.target.value) })}
                className="w-full accent-blue-600 bg-[#282834] h-1.5 rounded cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#a0a0b0]">Opacity</span>
                <span className="text-white font-mono">{transform.opacity}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={transform.opacity}
                onChange={(e) => updateTransform({ opacity: parseInt(e.target.value) })}
                className="w-full accent-blue-600 bg-[#282834] h-1.5 rounded cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* TAB: EXPORT */}
        {activeTab === "export" && <ExportPanel />}

        {/* TAB: PIPELINE */}
        {activeTab === "pipeline" && <VideoProcessingPanel />}

        {/* TAB: PERFORMANCE */}
        {activeTab === "performance" && <PerformancePanel />}
      </div>

      {/* Footer Advisory */}
      <div className="p-2 border-t border-[#282830] bg-[#141418] text-[10px] text-[#707080] flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Info className="w-3 h-3 text-blue-400 shrink-0" />
          <span>VFX Compositing Engine Connected</span>
        </div>
        <button
          onClick={() => setIsNodeEditorOpen(true)}
          className="text-blue-400 hover:text-blue-300 font-medium"
        >
          Open Node Graph
        </button>
      </div>

      {/* Node Compositing Editor Modal */}
      <NodeEditorModal
        isOpen={isNodeEditorOpen}
        onClose={() => setIsNodeEditorOpen(false)}
      />
    </div>
  );
};
