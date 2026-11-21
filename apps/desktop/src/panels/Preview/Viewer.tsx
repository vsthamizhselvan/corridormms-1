import React, { useRef, useEffect, useState, useCallback } from "react";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Eye,
  Sliders,
  Layers,
  Sparkles,
  Split,
  Columns,
  Minus,
  Plus,
  Move,
  Check,
  Film,
} from "lucide-react";
import { usePlaybackStore } from "../../project/playbackStore";
import { useMediaStore } from "../../project/mediaStore";
import { useInspectorStore } from "../../project/inspectorStore";
import { useViewerStore, DisplayMode, BackgroundType, CompareMode } from "../../stores/viewerStore";
import { useVFXStore } from "../../stores/vfxStore";
import { WebGLCompositor } from "../../components/viewer/webgl/compositor";

export const Viewer: React.FC = () => {
  const {
    currentFrame,
    totalFrames,
    fps,
    isPlaying,
    loop,
    setCurrentFrame,
    setIsPlaying,
    togglePlay,
    stepFrame,
  } = usePlaybackStore();

  const { media, selectedMediaId } = useMediaStore();
  const { keying, matte, transform } = useInspectorStore();
  const {
    displayMode,
    backgroundType,
    backgroundColor,
    gradientColorA,
    gradientColorB,
    compareMode,
    wipePosition,
    panX,
    panY,
    zoomLevel,
    zoomFitMode,
    checkerboardSize,
    alphaMode,
    exposure,
    saturation,
    setDisplayMode,
    setBackgroundType,
    setCompareMode,
    setWipePosition,
    updatePan,
    resetPan,
    setZoomLevel,
    setZoomFitMode,
    zoomIn,
    zoomOut,
    resetView,
  } = useViewerStore();

  const { masks, colorGrade, layers } = useVFXStore();

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const compositorRef = useRef<WebGLCompositor | null>(null);

  // Pan & Drag state
  const [isPanning, setIsPanning] = useState(false);
  const [isWiping, setIsWiping] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number; panX: number; panY: number }>({ x: 0, y: 0, panX: 0, panY: 0 });

  const selectedMedia = media.find((m) => m.id === selectedMediaId) || media[0];

  // Initialize WebGL2 Compositor
  useEffect(() => {
    if (!canvasRef.current) return;
    try {
      const comp = new WebGLCompositor(canvasRef.current);
      compositorRef.current = comp;
    } catch (e) {
      console.error("WebGL2 initialization failed:", e);
    }

    return () => {
      if (compositorRef.current) {
        compositorRef.current.dispose();
        compositorRef.current = null;
      }
    };
  }, []);

  // Sync Video time with currentFrame
  useEffect(() => {
    if (!videoRef.current || isPlaying) return;
    const targetTime = currentFrame / fps;
    if (Math.abs(videoRef.current.currentTime - targetTime) > 0.04) {
      videoRef.current.currentTime = targetTime;
    }
  }, [currentFrame, fps, isPlaying]);

  // Video Playback loop
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.play().catch(() => setIsPlaying(false));
    } else {
      video.pause();
    }
  }, [isPlaying, setIsPlaying]);

  // Handle video timeupdate
  const handleTimeUpdate = () => {
    if (!videoRef.current || !isPlaying) return;
    const frame = Math.round(videoRef.current.currentTime * fps);
    if (frame >= totalFrames) {
      if (loop) {
        videoRef.current.currentTime = 0;
        setCurrentFrame(0);
      } else {
        setIsPlaying(false);
      }
    } else {
      setCurrentFrame(frame);
    }
  };

  // Render Frame onto WebGL2 Canvas
  const renderFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const comp = compositorRef.current;
    if (!video || !canvas || !comp || video.videoWidth === 0 || video.videoHeight === 0) return;

    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    // Upload current video frame to GPU
    comp.uploadSourceFrame(video);

    const activeMask = masks.find((m) => m.visible);

    // Execute GLSL compositing pass
    comp.render({
      displayMode,
      backgroundType,
      compareMode,
      wipePosition,
      contrast: matte.contrast,
      alphaThreshold: matte.alphaThreshold,
      invertMatte: matte.invert,
      despillStrength: keying.despillStrength,
      exposure: exposure + colorGrade.exposure,
      saturation: saturation * colorGrade.saturation,
      alphaMode,
      backgroundColor,
      gradientColorA,
      gradientColorB,
      checkerboardSize,
      temperature: colorGrade.temperature,
      tint: colorGrade.tint,
      lift: colorGrade.lift,
      gamma: colorGrade.gamma,
      gain: colorGrade.gain,
      hasMask: !!activeMask,
      maskInvert: activeMask?.inverted ?? false,
      maskFeather: (activeMask?.feather ?? 0) / 100.0,
      blendMode: layers[0]?.blendMode ?? "normal",
    });
  }, [
    displayMode,
    backgroundType,
    compareMode,
    wipePosition,
    matte.contrast,
    matte.alphaThreshold,
    matte.invert,
    keying.despillStrength,
    exposure,
    saturation,
    alphaMode,
    backgroundColor,
    gradientColorA,
    gradientColorB,
    checkerboardSize,
    colorGrade,
    masks,
    layers,
  ]);

  // Trigger render when state or frame changes
  useEffect(() => {
    renderFrame();
  }, [renderFrame, currentFrame]);

  // RequestAnimationFrame loop for silky smooth 60fps playback
  useEffect(() => {
    if (!isPlaying) return;
    let animId: number;
    const loopRender = () => {
      renderFrame();
      animId = requestAnimationFrame(loopRender);
    };
    animId = requestAnimationFrame(loopRender);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying, renderFrame]);

  // Pan & Zoom event handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 1 || e.button === 2 || e.altKey || e.shiftKey) {
      // Middle or right click or modifier key: Pan
      setIsPanning(true);
      dragStartRef.current = { x: e.clientX, y: e.clientY, panX, panY };
      e.preventDefault();
    } else if (compareMode === "wipe") {
      // Check if clicking near wipe divider line
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const mouseNormX = (e.clientX - rect.left) / rect.width;
        if (Math.abs(mouseNormX - wipePosition) < 0.05) {
          setIsWiping(true);
          e.preventDefault();
        }
      }
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      const dx = e.clientX - dragStartRef.current.x;
      const dy = e.clientY - dragStartRef.current.y;
      updatePan(dx, dy);
      dragStartRef.current.x = e.clientX;
      dragStartRef.current.y = e.clientY;
    } else if (isWiping && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const normX = Math.max(0.01, Math.min(0.99, (e.clientX - rect.left) / rect.width));
      setWipePosition(normX);
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setIsWiping(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      zoomIn();
    } else {
      zoomOut();
    }
  };

  // Format SMPTE Timecode: HH:MM:SS:FF
  const formatTimecode = (frame: number, frameRate: number) => {
    const totalSecs = Math.floor(frame / frameRate);
    const f = Math.floor(frame % frameRate);
    const s = Math.floor(totalSecs % 60);
    const m = Math.floor((totalSecs / 60) % 60);
    const h = Math.floor(totalSecs / 3600);
    const pad = (n: number) => n.toString().padStart(2, "0");
    return `${pad(h)}:${pad(m)}:${pad(s)}:${pad(f)}`;
  };

  // Compute CSS zoom transform
  const getScaleStyle = () => {
    let scale = 1.0;
    if (zoomLevel > 0) {
      scale = zoomLevel;
    }
    return {
      transform: `translate(${panX}px, ${panY}px) scale(${scale})`,
      transformOrigin: "center center",
      maxWidth: zoomLevel === 0 ? "100%" : "none",
      maxHeight: zoomLevel === 0 ? "100%" : "none",
    };
  };

  return (
    <div className="h-full flex flex-col bg-[#0f0f13] select-none text-xs">
      {/* Top Toolbar */}
      <div className="h-9 bg-[#17171d] border-b border-[#282830] flex items-center justify-between px-3 gap-2">
        {/* Left: View Mode Pills */}
        <div className="flex items-center gap-1 overflow-x-auto">
          <span className="text-[10px] text-[#707080] font-semibold uppercase tracking-wider mr-1">
            VIEW:
          </span>
          {(
            [
              { id: "original", label: "RGB Plate" },
              { id: "foreground", label: "Foreground" },
              { id: "alpha", label: "Alpha Matte" },
              { id: "composite", label: "Composite" },
              { id: "background", label: "Background" },
            ] as const
          ).map((mode) => (
            <button
              key={mode.id}
              onClick={() => setDisplayMode(mode.id)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                displayMode === mode.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-[#202028] text-[#8e8e9e] hover:bg-[#282834] hover:text-white"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* Center: Transparency Background Selector */}
        <div className="flex items-center gap-1 bg-[#121216] border border-[#262630] rounded p-0.5">
          {(
            [
              { id: "checkerboard", label: "Checker", title: "Transparency Checkerboard" },
              { id: "black", label: "Black", title: "Black Background" },
              { id: "white", label: "White", title: "White Background" },
              { id: "gradient", label: "Gradient", title: "Linear Gradient Background" },
              { id: "custom_color", label: "Custom", title: "Custom Color Background" },
            ] as const
          ).map((bg) => (
            <button
              key={bg.id}
              onClick={() => setBackgroundType(bg.id)}
              title={bg.title}
              className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors ${
                backgroundType === bg.id
                  ? "bg-[#282834] text-white border border-[#383848]"
                  : "text-[#707080] hover:text-white"
              }`}
            >
              {bg.label}
            </button>
          ))}
        </div>

        {/* Right: Compare & Zoom Controls */}
        <div className="flex items-center gap-2">
          {/* Comparison Mode dropdown */}
          <div className="flex items-center gap-1 bg-[#121216] border border-[#262630] rounded px-1.5 py-0.5 text-[11px]">
            <Split className="w-3 h-3 text-blue-400" />
            <select
              value={compareMode}
              onChange={(e) => setCompareMode(e.target.value as CompareMode)}
              className="bg-transparent text-white text-[11px] outline-none cursor-pointer"
            >
              <option value="none">Compare: Off</option>
              <option value="wipe">Split Wipe (A/B)</option>
              <option value="side_by_side">Side-by-Side (2-Up)</option>
              <option value="difference">Difference</option>
            </select>
          </div>

          {/* Zoom Selector */}
          <div className="flex items-center gap-1 bg-[#121216] border border-[#262630] rounded px-1.5 py-0.5">
            <button onClick={zoomOut} title="Zoom Out" className="p-0.5 text-[#808090] hover:text-white">
              <Minus className="w-2.5 h-2.5" />
            </button>
            <select
              value={zoomLevel}
              onChange={(e) => setZoomLevel(parseFloat(e.target.value))}
              className="bg-transparent text-white text-[11px] font-mono outline-none cursor-pointer"
            >
              <option value="0">Fit</option>
              <option value="0.25">25%</option>
              <option value="0.5">50%</option>
              <option value="1">100%</option>
              <option value="2">200%</option>
            </select>
            <button onClick={zoomIn} title="Zoom In" className="p-0.5 text-[#808090] hover:text-white">
              <Plus className="w-2.5 h-2.5" />
            </button>
          </div>

          {/* Reset View */}
          <button
            onClick={resetView}
            title="Reset Pan & Zoom"
            className="p-1 rounded bg-[#202028] hover:bg-[#282834] text-[#808090] hover:text-white border border-[#282830]"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Main Viewport Container */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        onContextMenu={(e) => e.preventDefault()}
        className="flex-1 relative flex items-center justify-center overflow-hidden bg-[#0a0a0e] cursor-crosshair"
      >
        {selectedMedia ? (
          <div
            className="relative transition-transform duration-75 shadow-2xl border border-[#202028]"
            style={getScaleStyle()}
          >
            {/* Hidden source video element feeding WebGL2 textures */}
            <video
              ref={videoRef}
              src={selectedMedia.path}
              onTimeUpdate={handleTimeUpdate}
              onEnded={() => setIsPlaying(false)}
              className="hidden"
              playsInline
              muted
            />

            {/* GPU WebGL2 Canvas Viewport */}
            <canvas
              ref={canvasRef}
              className="block max-h-[calc(100vh-360px)] object-contain shadow-2xl"
            />

            {/* Wipe Split Interactive Draggable Bar */}
            {compareMode === "wipe" && (
              <div
                className="absolute inset-y-0 w-1 bg-blue-500 shadow-lg cursor-ew-resize flex items-center justify-center"
                style={{ left: `${wipePosition * 100}%` }}
                onMouseDown={(e) => {
                  setIsWiping(true);
                  e.stopPropagation();
                }}
              >
                <div className="w-5 h-5 rounded-full bg-blue-600 border-2 border-white text-[9px] flex items-center justify-center text-white font-bold shadow-md">
                  ↔
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-[#505060] space-y-2">
            <Eye className="w-12 h-12 stroke-[1.2] opacity-40" />
            <span className="text-xs font-medium text-[#707080]">No Active Media Selected</span>
            <span className="text-[11px] text-[#505060]">Import video to preview original, matte & composite</span>
          </div>
        )}

        {/* Viewport Info Overlay */}
        <div className="absolute top-2 left-3 bg-[#14141a]/90 backdrop-blur border border-[#282834] px-2.5 py-1 rounded text-[11px] text-[#a0a0b0] flex items-center gap-2 shadow-lg pointer-events-none">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>WebGL2 GPU Compositor</span>
          <span className="text-[#606070]">•</span>
          <span className="font-mono text-white uppercase text-[10px]">{displayMode}</span>
          {compareMode !== "none" && (
            <>
              <span className="text-[#606070]">•</span>
              <span className="text-amber-400 text-[10px] uppercase font-mono">{compareMode}</span>
            </>
          )}
        </div>
      </div>

      {/* Bottom Transport Controls Bar */}
      <div className="h-10 bg-[#14141a] border-t border-[#24242c] flex items-center justify-between px-3">
        {/* Left: Timecode Readouts */}
        <div className="flex items-center gap-3 font-mono">
          <div className="flex items-center gap-1.5 bg-[#0d0d10] border border-[#262630] px-2 py-0.5 rounded text-white text-xs font-semibold">
            <span className="text-blue-400 font-sans text-[10px] font-bold">TC</span>
            <span>{formatTimecode(currentFrame, fps)}</span>
          </div>

          <div className="text-[11px] text-[#808090]">
            <span className="text-white font-medium">{currentFrame.toString().padStart(4, "0")}</span>
            <span className="mx-1">/</span>
            <span>{totalFrames.toString().padStart(4, "0")}f</span>
          </div>
        </div>

        {/* Center: Playhead Controls */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setCurrentFrame(0)}
            title="First Frame (Home)"
            className="p-1.5 rounded hover:bg-[#282832] text-[#a0a0b0] hover:text-white"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => stepFrame(-1)}
            title="Previous Frame (Left Arrow)"
            className="p-1.5 rounded hover:bg-[#282832] text-[#a0a0b0] hover:text-white"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={togglePlay}
            title="Play / Pause (Space)"
            className="w-7 h-7 rounded bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shadow-md"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>
          <button
            onClick={() => stepFrame(1)}
            title="Next Frame (Right Arrow)"
            className="p-1.5 rounded hover:bg-[#282832] text-[#a0a0b0] hover:text-white"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right: Playback Options */}
        <div className="flex items-center gap-2">
          {selectedMedia && (
            <span className="text-[10px] font-mono text-[#707080]">
              {selectedMedia.width}×{selectedMedia.height}
            </span>
          )}
          <span className="text-[10px] font-mono text-[#707080]">{fps} FPS</span>
        </div>
      </div>
    </div>
  );
};
