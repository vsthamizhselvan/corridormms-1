import React from "react";
import {
  Film,
  Download,
  Sliders,
  Folder,
  Volume2,
  VolumeX,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useExportStore, ExportFormat, AlphaMode, ColorSpace } from "../../stores/exportStore";
import { useMediaStore } from "../../project/mediaStore";
import { useAiJobStore } from "../../stores/aiJobStore";

export const ExportPanel: React.FC = () => {
  const { settings, updateSettings, isExporting, setExporting, lastValidationResult } =
    useExportStore();
  const { media, selectedMediaId } = useMediaStore();
  const { startJob } = useAiJobStore();

  const selectedMedia = media.find((m) => m.id === selectedMediaId);

  const formatOptions: { id: ExportFormat; label: string; desc: string; ext: string }[] = [
    {
      id: "prores_4444",
      label: "Apple ProRes 4444",
      desc: "10/12-bit VFX Master with Alpha (yuva444p10le)",
      ext: ".mov",
    },
    {
      id: "prores_4444_xq",
      label: "Apple ProRes 4444 XQ",
      desc: "Extreme Quality 12-bit Master (ap4x)",
      ext: ".mov",
    },
    {
      id: "qtrle",
      label: "QuickTime Animation (RLE)",
      desc: "Lossless Animation with Alpha",
      ext: ".mov",
    },
    {
      id: "vp9",
      label: "VP9 WebM Transparent",
      desc: "Efficient Web Delivery with Alpha",
      ext: ".webm",
    },
    {
      id: "openexr",
      label: "OpenEXR Sequence",
      desc: "16-bit Half-Float HDR Multi-channel",
      ext: "folder",
    },
    {
      id: "png_sequence",
      label: "PNG Image Sequence",
      desc: "RGBA 8/16-bit Transparent Sequence",
      ext: "folder",
    },
  ];

  const handleStartExport = async () => {
    if (!selectedMedia) return;
    setExporting(true);

    const outDir = settings.outputDirectory || "/Volumes/VST SSD/corridor key 2.0/renders";
    const jobPayload = {
      inputPath: selectedMedia.path,
      outputDir: outDir,
      exportFormat: settings.format,
      colorProfile: settings.colorSpace,
      alphaMode: settings.alphaMode,
      despillStrength: settings.despillStrength,
      preserveAudio: settings.preserveAudio,
    };

    try {
      await startJob(jobPayload);
    } catch (e) {
      console.error("Export error:", e);
      setExporting(false);
    }
  };

  return (
    <div className="space-y-4 text-xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-[#282832]">
        <div className="flex items-center gap-2">
          <Film className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-white tracking-wide uppercase text-[11px]">
            Master Video & Sequence Export
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
          FFmpeg 9.0.2
        </span>
      </div>

      {/* Target Format Selector */}
      <div className="space-y-1.5">
        <label className="text-[11px] font-medium text-[#8a8a98]">Export Container & Codec</label>
        <div className="grid grid-cols-1 gap-1.5">
          {formatOptions.map((opt) => (
            <button
              key={opt.id}
              onClick={() => updateSettings({ format: opt.id })}
              className={`p-2.5 rounded border text-left transition-colors flex items-center justify-between ${
                settings.format === opt.id
                  ? "bg-blue-600/15 border-blue-500/50 text-white"
                  : "bg-[#1a1a20] border-[#282830] text-[#90909c] hover:border-[#383842] hover:text-[#d0d0dc]"
              }`}
            >
              <div>
                <div className="font-medium text-xs text-white">{opt.label}</div>
                <div className="text-[10px] text-[#787888]">{opt.desc}</div>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#202028] text-[#a0a0b0]">
                {opt.ext}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Alpha Transparency & Compositing Mode */}
      <div className="bg-[#1a1a20] border border-[#282830] rounded p-3 space-y-3">
        <div className="flex items-center gap-2 text-white font-medium pb-1 border-b border-[#24242c]">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>Alpha Transparency Mode</span>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => updateSettings({ alphaMode: "straight" })}
            className={`py-1.5 px-2 rounded text-center text-[11px] font-medium border transition-colors ${
              settings.alphaMode === "straight"
                ? "bg-blue-600 text-white border-blue-500"
                : "bg-[#141418] border-[#282830] text-[#808090] hover:text-white"
            }`}
          >
            Straight Alpha (RGBA)
          </button>
          <button
            onClick={() => updateSettings({ alphaMode: "premultiplied" })}
            className={`py-1.5 px-2 rounded text-center text-[11px] font-medium border transition-colors ${
              settings.alphaMode === "premultiplied"
                ? "bg-blue-600 text-white border-blue-500"
                : "bg-[#141418] border-[#282830] text-[#808090] hover:text-white"
            }`}
          >
            Premultiplied Alpha
          </button>
        </div>

        {/* Despill Slider */}
        <div className="space-y-1">
          <div className="flex justify-between text-[11px]">
            <span className="text-[#808090]">Edge Despill Suppression:</span>
            <span className="text-white font-mono">{Math.round(settings.despillStrength * 100)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.despillStrength}
            onChange={(e) => updateSettings({ despillStrength: parseFloat(e.target.value) })}
            className="w-full accent-blue-500 bg-[#282830] h-1.5 rounded cursor-pointer"
          />
        </div>
      </div>

      {/* Colour Space Management */}
      <div className="bg-[#1a1a20] border border-[#282830] rounded p-3 space-y-2">
        <div className="flex items-center justify-between text-white font-medium pb-1 border-b border-[#24242c]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Target Colour Space</span>
          </div>
          <span className="text-[10px] text-[#707080]">No Alpha Gamma Transform</span>
        </div>

        <select
          value={settings.colorSpace}
          onChange={(e) => updateSettings({ colorSpace: e.target.value as ColorSpace })}
          className="w-full bg-[#141418] border border-[#282830] rounded px-2.5 py-1.5 text-white text-[11px] outline-none focus:border-blue-500"
        >
          <option value="rec709">Rec.709 (ITU-R BT.709 / Broadcast)</option>
          <option value="srgb">sRGB (IEC 61966-2-1 / Web / UI)</option>
          <option value="linear">Scene-Linear (Uncompressed VFX Pipeline)</option>
          <option value="rec2020">Rec.2020 (Wide Color Gamut / HDR)</option>
          <option value="acescg">ACEScg (AP1 Scene-Referred VFX Standard)</option>
        </select>
      </div>

      {/* Audio Stream Options */}
      <div className="bg-[#1a1a20] border border-[#282830] rounded p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {settings.preserveAudio ? (
            <Volume2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <VolumeX className="w-4 h-4 text-[#707080]" />
          )}
          <div>
            <div className="text-white font-medium">Source Audio Passthrough</div>
            <div className="text-[10px] text-[#707080]">Mux original audio stream with sync</div>
          </div>
        </div>
        <button
          onClick={() => updateSettings({ preserveAudio: !settings.preserveAudio })}
          className={`px-3 py-1 rounded text-[11px] font-medium border transition-colors ${
            settings.preserveAudio
              ? "bg-emerald-600/20 text-emerald-400 border-emerald-500/30"
              : "bg-[#141418] text-[#707080] border-[#282830]"
          }`}
        >
          {settings.preserveAudio ? "Enabled" : "Muted"}
        </button>
      </div>

      {/* Last Validation Badge if exists */}
      {lastValidationResult && (
        <div className="bg-emerald-950/20 border border-emerald-500/30 rounded p-3 space-y-1 text-[11px]">
          <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            <span>Output Alpha Verified</span>
          </div>
          <div className="text-[#a0a0b0] text-[10px]">{lastValidationResult.details}</div>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleStartExport}
        disabled={isExporting || !selectedMedia}
        className={`w-full py-2.5 px-4 rounded font-medium text-xs flex items-center justify-center gap-2 transition-colors ${
          isExporting || !selectedMedia
            ? "bg-[#282830] text-[#606070] cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20"
        }`}
      >
        <Download className="w-4 h-4" />
        <span>{isExporting ? "Rendering Video Pipeline..." : "Export Transparent Master"}</span>
      </button>
    </div>
  );
};
