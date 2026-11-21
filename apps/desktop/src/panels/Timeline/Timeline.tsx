import React, { useRef, useState, useEffect, useCallback } from "react";
import {
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Volume2,
  VolumeX,
  ZoomIn,
  ZoomOut,
  Plus,
  Scissors,
  MousePointer,
  Magnet,
  RotateCcw,
  RotateCw,
  Trash2,
  Copy,
  ChevronUp,
  ChevronDown,
  Film,
  ListFilter,
} from "lucide-react";
import { useTimelineStore } from "../../project/timelineStore";
import { usePlaybackStore } from "../../project/playbackStore";
import { useMediaStore } from "../../project/mediaStore";
import { ProcessingQueue } from "../../components/ai/ProcessingQueue";

export const Timeline: React.FC = () => {
  const {
    tracks,
    selectedClipId,
    durationFrames,
    zoomRatio,
    activeTool,
    snappingEnabled,
    canUndo,
    canRedo,
    toggleTrackVisibility,
    toggleTrackLock,
    toggleTrackMute,
    toggleTrackSolo,
    addTrack,
    deleteTrack,
    reorderTrack,
    selectClip,
    moveClip,
    trimClipIn,
    trimClipOut,
    splitClip,
    splitClipAtPlayhead,
    deleteClip,
    rippleDeleteClip,
    duplicateClip,
    setActiveTool,
    toggleSnapping,
    findSnapTarget,
    setZoomRatio,
    undo,
    redo,
  } = useTimelineStore();

  const { currentFrame, setCurrentFrame, isPlaying, togglePlay } = usePlaybackStore();
  const { selectMedia } = useMediaStore();

  const rulerRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isScrubbing, setIsScrubbing] = useState(false);
  const [activeBottomTab, setActiveBottomTab] = useState<"timeline" | "queue">("timeline");
  const [snapGuideFrame, setSnapGuideFrame] = useState<number | null>(null);

  // Drag interaction state
  const [dragState, setDragState] = useState<{
    type: "move" | "trimIn" | "trimOut";
    clipId: string;
    startMouseX: number;
    initialStartFrame: number;
    initialEndFrame: number;
    sourceTrackId: string;
    currentTrackId: string;
  } | null>(null);

  // Frame tick marks calculation
  const tickInterval = zoomRatio > 2.5 ? 10 : zoomRatio > 1.0 ? 24 : 48;
  const numTicks = Math.ceil(durationFrames / tickInterval);

  // Playhead scrubbing handler
  const handleScrub = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!rulerRef.current) return;
      const rect = rulerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      let frame = Math.round(clickX / zoomRatio);

      if (snappingEnabled) {
        const snap = findSnapTarget(frame, 6);
        if (snap !== null) {
          frame = snap;
          setSnapGuideFrame(snap);
        } else {
          setSnapGuideFrame(null);
        }
      }

      setCurrentFrame(Math.max(0, Math.min(durationFrames - 1, frame)));
    },
    [durationFrames, findSnapTarget, setCurrentFrame, snappingEnabled, zoomRatio]
  );

  // Mouse move / up handler for scrubbing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isScrubbing || !rulerRef.current) return;
      const rect = rulerRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      let frame = Math.round(clickX / zoomRatio);

      if (snappingEnabled) {
        const snap = findSnapTarget(frame, 6);
        if (snap !== null) {
          frame = snap;
          setSnapGuideFrame(snap);
        } else {
          setSnapGuideFrame(null);
        }
      }

      setCurrentFrame(Math.max(0, Math.min(durationFrames - 1, frame)));
    };

    const handleMouseUp = () => {
      setIsScrubbing(false);
      setSnapGuideFrame(null);
    };

    if (isScrubbing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isScrubbing, zoomRatio, durationFrames, setCurrentFrame, snappingEnabled, findSnapTarget]);

  // Drag interaction handler for moving and trimming clips
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!dragState) return;

      const deltaX = e.clientX - dragState.startMouseX;
      const deltaFrames = Math.round(deltaX / zoomRatio);

      if (dragState.type === "move") {
        let newStart = Math.max(0, dragState.initialStartFrame + deltaFrames);
        if (snappingEnabled) {
          const snap = findSnapTarget(newStart, 6);
          if (snap !== null) {
            newStart = snap;
            setSnapGuideFrame(snap);
          } else {
            setSnapGuideFrame(null);
          }
        }
        moveClip(dragState.clipId, dragState.currentTrackId, newStart);
      } else if (dragState.type === "trimIn") {
        let newStart = Math.max(0, dragState.initialStartFrame + deltaFrames);
        if (snappingEnabled) {
          const snap = findSnapTarget(newStart, 6);
          if (snap !== null) {
            newStart = snap;
            setSnapGuideFrame(snap);
          } else {
            setSnapGuideFrame(null);
          }
        }
        trimClipIn(dragState.clipId, newStart);
      } else if (dragState.type === "trimOut") {
        let newEnd = Math.max(dragState.initialStartFrame + 1, dragState.initialEndFrame + deltaFrames);
        if (snappingEnabled) {
          const snap = findSnapTarget(newEnd, 6);
          if (snap !== null) {
            newEnd = snap;
            setSnapGuideFrame(snap);
          } else {
            setSnapGuideFrame(null);
          }
        }
        trimClipOut(dragState.clipId, newEnd);
      }
    };

    const handleMouseUp = () => {
      setDragState(null);
      setSnapGuideFrame(null);
    };

    if (dragState) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [dragState, zoomRatio, snappingEnabled, findSnapTarget, moveClip, trimClipIn, trimClipOut]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.key === " " && !e.repeat) {
        e.preventDefault();
        togglePlay();
      } else if ((e.key === "v" || e.key === "V") && !e.metaKey && !e.ctrlKey) {
        setActiveTool("select");
      } else if ((e.key === "c" || e.key === "C") && !e.metaKey && !e.ctrlKey) {
        setActiveTool("razor");
      } else if ((e.key === "s" || e.key === "S") && !e.metaKey && !e.ctrlKey) {
        toggleSnapping();
      } else if (
        (e.key === "Delete" || e.key === "Backspace") &&
        selectedClipId
      ) {
        e.preventDefault();
        if (e.shiftKey) {
          rippleDeleteClip(selectedClipId);
        } else {
          deleteClip(selectedClipId);
        }
      } else if ((e.metaKey || e.ctrlKey) && (e.key === "d" || e.key === "D")) {
        e.preventDefault();
        if (selectedClipId) duplicateClip(selectedClipId);
      } else if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        splitClipAtPlayhead(currentFrame);
      } else if ((e.metaKey || e.ctrlKey) && (e.key === "z" || e.key === "Z")) {
        e.preventDefault();
        if (e.shiftKey) {
          redo();
        } else {
          undo();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    currentFrame,
    deleteClip,
    duplicateClip,
    redo,
    rippleDeleteClip,
    selectedClipId,
    setActiveTool,
    splitClipAtPlayhead,
    togglePlay,
    toggleSnapping,
    undo,
  ]);

  return (
    <div
      ref={containerRef}
      className="h-full flex flex-col bg-[#141418] border-t border-[#262630] select-none text-xs"
    >
      {/* Timeline Toolbar Header with Tabs */}
      <div className="h-9 bg-[#1c1c22] border-b border-[#262630] flex items-center justify-between px-3">
        {/* Left: Tab Switcher & Edit Tools */}
        <div className="flex items-center gap-2">
          {/* Tabs */}
          <div className="flex items-center gap-1 border-r border-[#2c2c34] pr-2 mr-1">
            <button
              onClick={() => setActiveBottomTab("timeline")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium flex items-center gap-1.5 transition-colors ${
                activeBottomTab === "timeline"
                  ? "bg-[#282832] text-white"
                  : "text-[#808090] hover:text-white"
              }`}
            >
              <Film className="w-3.5 h-3.5" />
              <span>Timeline</span>
            </button>
            <button
              onClick={() => setActiveBottomTab("queue")}
              className={`px-2.5 py-1 rounded text-[11px] font-medium flex items-center gap-1.5 transition-colors ${
                activeBottomTab === "queue"
                  ? "bg-[#282832] text-white"
                  : "text-[#808090] hover:text-white"
              }`}
            >
              <ListFilter className="w-3.5 h-3.5 text-blue-400" />
              <span>Render Queue</span>
            </button>
          </div>

          {activeBottomTab === "timeline" && (
            <div className="flex items-center gap-1">
              {/* Tool Selection */}
              <button
                onClick={() => setActiveTool("select")}
                title="Selection Tool (V)"
                className={`p-1.5 rounded flex items-center gap-1 transition-colors ${
                  activeTool === "select"
                    ? "bg-[#0d9488] text-white shadow-sm"
                    : "bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
                }`}
              >
                <MousePointer className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setActiveTool("razor")}
                title="Razor / Split Tool (C)"
                className={`p-1.5 rounded flex items-center gap-1 transition-colors ${
                  activeTool === "razor"
                    ? "bg-amber-600 text-white shadow-sm"
                    : "bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
                }`}
              >
                <Scissors className="w-3.5 h-3.5" />
              </button>

              <div className="w-[1px] h-4 bg-[#2e2e38] mx-1" />

              {/* Magnetic Snapping */}
              <button
                onClick={toggleSnapping}
                title={`Magnetic Snapping (S) — ${snappingEnabled ? "Enabled" : "Disabled"}`}
                className={`p-1.5 rounded flex items-center gap-1 transition-colors ${
                  snappingEnabled
                    ? "bg-[#2563eb]/30 text-blue-400 border border-blue-500/50"
                    : "bg-[#24242c] hover:bg-[#30303c] text-[#707080] hover:text-white"
                }`}
              >
                <Magnet className="w-3.5 h-3.5" />
              </button>

              <div className="w-[1px] h-4 bg-[#2e2e38] mx-1" />

              {/* Ripple Delete & Duplicate */}
              <button
                onClick={() => selectedClipId && rippleDeleteClip(selectedClipId)}
                disabled={!selectedClipId}
                title="Ripple Delete Clip (Shift+Delete)"
                className="p-1.5 rounded bg-[#24242c] hover:bg-red-950/40 text-[#a0a0b0] hover:text-red-400 disabled:opacity-40 disabled:hover:bg-[#24242c] disabled:hover:text-[#a0a0b0]"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => selectedClipId && duplicateClip(selectedClipId)}
                disabled={!selectedClipId}
                title="Duplicate Clip (Ctrl/Cmd+D)"
                className="p-1.5 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white disabled:opacity-40"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>

              <div className="w-[1px] h-4 bg-[#2e2e38] mx-1" />

              {/* Undo / Redo */}
              <button
                onClick={undo}
                disabled={!canUndo}
                title="Undo (Ctrl/Cmd+Z)"
                className="p-1.5 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white disabled:opacity-30"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={redo}
                disabled={!canRedo}
                title="Redo (Ctrl/Cmd+Shift+Z)"
                className="p-1.5 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white disabled:opacity-30"
              >
                <RotateCw className="w-3.5 h-3.5" />
              </button>

              <div className="w-[1px] h-4 bg-[#2e2e38] mx-1" />

              {/* Track Adders */}
              <button
                onClick={() => addTrack("video")}
                title="Add Video Track"
                className="px-2 py-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-teal-300 flex items-center gap-1 text-[11px]"
              >
                <Plus className="w-3 h-3 text-teal-400" />
                <span>+V</span>
              </button>

              <button
                onClick={() => addTrack("audio")}
                title="Add Audio Track"
                className="px-2 py-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-sky-300 flex items-center gap-1 text-[11px]"
              >
                <Plus className="w-3 h-3 text-sky-400" />
                <span>+A</span>
              </button>
            </div>
          )}
        </div>

        {/* Right: Zoom & Metrics */}
        <div className="flex items-center gap-3 text-[11px] text-[#707080]">
          {activeBottomTab === "timeline" && (
            <>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setZoomRatio(zoomRatio * 1.25)}
                  title="Zoom In Timeline"
                  className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setZoomRatio(zoomRatio / 1.25)}
                  title="Zoom Out Timeline"
                  className="p-1 rounded bg-[#24242c] hover:bg-[#30303c] text-[#a0a0b0] hover:text-white"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
              </div>
              <span>Zoom: {(zoomRatio * 100).toFixed(0)}%</span>
              <span>•</span>
              <span>{durationFrames} Frames Total</span>
            </>
          )}
        </div>
      </div>

      {activeBottomTab === "queue" ? (
        <div className="flex-1 overflow-hidden">
          <ProcessingQueue />
        </div>
      ) : (
        /* Main Track Workspace with Header Column and Sequence Track Area */
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Track Headers */}
          <div className="w-56 shrink-0 bg-[#18181e] border-r border-[#262630] flex flex-col z-10 shadow-sm">
            {/* Ruler spacer */}
            <div className="h-6 bg-[#16161a] border-b border-[#262630] flex items-center justify-between px-2 text-[10px] text-[#606070] font-medium">
              <span>TRACK CONTROLS</span>
              <span>M / S / L / V</span>
            </div>

            {/* Track Headers */}
            <div className="flex-1 overflow-y-auto">
              {tracks.map((track) => (
                <div
                  key={track.id}
                  className="h-14 border-b border-[#262630] bg-[#1a1a20] px-2 flex items-center justify-between hover:bg-[#202028] transition-colors"
                >
                  <div className="flex items-center gap-1.5 truncate">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        track.type === "video" ? "bg-teal-500" : "bg-sky-500"
                      }`}
                    />
                    <div>
                      <div className="font-medium text-white text-xs truncate w-20">
                        {track.name}
                      </div>
                      <div className="text-[9px] text-[#707080] capitalize">
                        {track.type} • {track.clips.length} clip{track.clips.length === 1 ? "" : "s"}
                      </div>
                    </div>
                  </div>

                  {/* Track Controls */}
                  <div className="flex items-center gap-0.5 text-[#707080]">
                    {/* Solo Button */}
                    <button
                      onClick={() => toggleTrackSolo(track.id)}
                      title={track.solo ? "Disable Solo" : "Solo Track"}
                      className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center transition-colors ${
                        track.solo
                          ? "bg-amber-500 text-black shadow-sm"
                          : "hover:bg-[#282834] text-[#808090]"
                      }`}
                    >
                      S
                    </button>

                    {/* Mute Button */}
                    <button
                      onClick={() => toggleTrackMute(track.id)}
                      title={track.muted ? "Unmute Track" : "Mute Track"}
                      className={`p-1 rounded hover:bg-[#282834] transition-colors ${
                        track.muted ? "text-amber-400 bg-amber-950/30" : "text-[#707080]"
                      }`}
                    >
                      {track.muted ? (
                        <VolumeX className="w-3.5 h-3.5" />
                      ) : (
                        <Volume2 className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {/* Lock Button */}
                    <button
                      onClick={() => toggleTrackLock(track.id)}
                      title={track.locked ? "Unlock Track" : "Lock Track"}
                      className={`p-1 rounded hover:bg-[#282834] transition-colors ${
                        track.locked ? "text-red-400 bg-red-950/30" : "text-[#707080]"
                      }`}
                    >
                      {track.locked ? (
                        <Lock className="w-3.5 h-3.5" />
                      ) : (
                        <Unlock className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {/* Visibility Button */}
                    <button
                      onClick={() => toggleTrackVisibility(track.id)}
                      title={track.visible ? "Hide Track" : "Show Track"}
                      className={`p-1 rounded hover:bg-[#282834] transition-colors ${
                        track.visible ? "text-[#a0a0b0]" : "text-amber-500 bg-amber-950/30"
                      }`}
                    >
                      {track.visible ? (
                        <Eye className="w-3.5 h-3.5" />
                      ) : (
                        <EyeOff className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {/* Reorder Up / Down */}
                    <div className="flex flex-col ml-0.5">
                      <button
                        onClick={() => reorderTrack(track.id, "up")}
                        title="Move Track Up"
                        className="hover:text-white p-0.5"
                      >
                        <ChevronUp className="w-2.5 h-2.5" />
                      </button>
                      <button
                        onClick={() => reorderTrack(track.id, "down")}
                        title="Move Track Down"
                        className="hover:text-white p-0.5"
                      >
                        <ChevronDown className="w-2.5 h-2.5" />
                      </button>
                    </div>

                    {/* Delete Track */}
                    {tracks.length > 1 && (
                      <button
                        onClick={() => deleteTrack(track.id)}
                        title="Delete Track"
                        className="p-1 rounded hover:bg-red-950/40 text-[#606070] hover:text-red-400"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Area: Time Ruler & Clip Tracks */}
          <div className="flex-1 flex flex-col overflow-x-auto relative bg-[#121216]">
            {/* Time Ruler */}
            <div
              ref={rulerRef}
              onMouseDown={(e) => {
                setIsScrubbing(true);
                handleScrub(e);
              }}
              className="h-6 bg-[#16161c] border-b border-[#282832] relative cursor-pointer select-none"
              style={{ width: `${Math.max(durationFrames * zoomRatio + 200, 1200)}px` }}
            >
              {Array.from({ length: numTicks }).map((_, i) => {
                const frame = i * tickInterval;
                const leftPos = frame * zoomRatio;
                return (
                  <div
                    key={frame}
                    className="absolute top-0 bottom-0 border-l border-[#2e2e38] pl-1 pt-0.5 text-[9px] font-mono text-[#606070] pointer-events-none"
                    style={{ left: `${leftPos}px` }}
                  >
                    {frame}f
                  </div>
                );
              })}

              {/* Playhead Marker on Ruler */}
              <div
                className="absolute top-0 bottom-0 w-3 -ml-1.5 flex flex-col items-center pointer-events-none z-30"
                style={{ left: `${currentFrame * zoomRatio}px` }}
              >
                <div className="w-3 h-3 bg-red-500 rounded-sm shadow-md" />
              </div>
            </div>

            {/* Tracks Clip Workspace */}
            <div
              className="flex-1 relative"
              style={{ width: `${Math.max(durationFrames * zoomRatio + 200, 1200)}px` }}
            >
              {/* Playhead Vertical Line */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-500/90 z-20 pointer-events-none shadow-sm"
                style={{ left: `${currentFrame * zoomRatio}px` }}
              />

              {/* Snap Guide Line */}
              {snapGuideFrame !== null && (
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-blue-400 z-20 pointer-events-none shadow"
                  style={{ left: `${snapGuideFrame * zoomRatio}px` }}
                />
              )}

              {/* Track Lanes */}
              {tracks.map((track) => (
                <div
                  key={track.id}
                  className={`h-14 border-b border-[#22222a] relative transition-colors ${
                    track.locked
                      ? "bg-[#101014] opacity-75 cursor-not-allowed"
                      : "bg-[#141418] hover:bg-[#16161c]"
                  }`}
                >
                  {/* Clips in this track */}
                  {track.clips.map((clip) => {
                    const isSelected = selectedClipId === clip.id;
                    const clipLeft = clip.startFrame * zoomRatio;
                    const clipWidth = Math.max((clip.endFrame - clip.startFrame) * zoomRatio, 24);

                    return (
                      <div
                        key={clip.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (activeTool === "razor") {
                            // Split at exact click frame
                            const rect = e.currentTarget.getBoundingClientRect();
                            const clickOffset = e.clientX - rect.left;
                            const splitFrame =
                              clip.startFrame + Math.round(clickOffset / zoomRatio);
                            splitClip(clip.id, splitFrame);
                          } else {
                            selectClip(clip.id);
                            selectMedia(clip.mediaId);
                          }
                        }}
                        className={`group absolute top-1.5 bottom-1.5 rounded overflow-hidden flex items-center justify-between text-xs border shadow transition-all ${
                          activeTool === "razor"
                            ? "cursor-crosshair"
                            : "cursor-grab active:cursor-grabbing"
                        } ${
                          track.type === "video"
                            ? isSelected
                              ? "bg-teal-700 border-white text-white ring-1 ring-white"
                              : "bg-teal-800/80 hover:bg-teal-700 border-teal-600/70 text-[#e6f4f2]"
                            : isSelected
                            ? "bg-sky-700 border-white text-white ring-1 ring-white"
                            : "bg-sky-800/80 hover:bg-sky-700 border-sky-600/70 text-[#e0f2fe]"
                        }`}
                        style={{
                          left: `${clipLeft}px`,
                          width: `${clipWidth}px`,
                        }}
                        onMouseDown={(e) => {
                          if (activeTool === "razor" || track.locked) return;
                          // If click was not on handles, initiate move drag
                          setDragState({
                            type: "move",
                            clipId: clip.id,
                            startMouseX: e.clientX,
                            initialStartFrame: clip.startFrame,
                            initialEndFrame: clip.endFrame,
                            sourceTrackId: track.id,
                            currentTrackId: track.id,
                          });
                        }}
                      >
                        {/* Trim In Handle (Left) */}
                        <div
                          onMouseDown={(e) => {
                            e.stopPropagation();
                            if (track.locked) return;
                            setDragState({
                              type: "trimIn",
                              clipId: clip.id,
                              startMouseX: e.clientX,
                              initialStartFrame: clip.startFrame,
                              initialEndFrame: clip.endFrame,
                              sourceTrackId: track.id,
                              currentTrackId: track.id,
                            });
                          }}
                          title="Trim In Point"
                          className="absolute left-0 top-0 bottom-0 w-2 hover:w-3 bg-white/20 hover:bg-white/60 cursor-ew-resize transition-all z-10"
                        />

                        {/* Simulated Audio Waveform Display if Audio Track */}
                        {track.type === "audio" && (
                          <div className="absolute inset-0 flex items-center justify-around opacity-30 pointer-events-none px-2">
                            {Array.from({ length: 16 }).map((_, idx) => (
                              <div
                                key={idx}
                                className="w-1 bg-white rounded-full"
                                style={{
                                  height: `${20 + Math.sin(idx * 0.8) * 50 + ((idx * 7) % 30)}%`,
                                }}
                              />
                            ))}
                          </div>
                        )}

                        {/* Clip Content Label */}
                        <div className="px-3 flex items-center justify-between w-full z-0 pointer-events-none">
                          <span className="truncate font-medium text-[11px] drop-shadow-sm">
                            {clip.name}
                          </span>
                          <span className="text-[10px] opacity-75 font-mono ml-1 shrink-0 drop-shadow-sm">
                            {clip.endFrame - clip.startFrame}f
                          </span>
                        </div>

                        {/* Trim Out Handle (Right) */}
                        <div
                          onMouseDown={(e) => {
                            e.stopPropagation();
                            if (track.locked) return;
                            setDragState({
                              type: "trimOut",
                              clipId: clip.id,
                              startMouseX: e.clientX,
                              initialStartFrame: clip.startFrame,
                              initialEndFrame: clip.endFrame,
                              sourceTrackId: track.id,
                              currentTrackId: track.id,
                            });
                          }}
                          title="Trim Out Point"
                          className="absolute right-0 top-0 bottom-0 w-2 hover:w-3 bg-white/20 hover:bg-white/60 cursor-ew-resize transition-all z-10"
                        />
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
