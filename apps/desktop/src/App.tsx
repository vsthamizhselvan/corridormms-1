import React, { useState, useEffect } from "react";
import { TopMenu } from "./components/TopMenu";
import { MediaBrowser } from "./panels/MediaBrowser/MediaBrowser";
import { Viewer } from "./panels/Preview/Viewer";
import { Inspector } from "./panels/Inspector/Inspector";
import { Timeline } from "./panels/Timeline/Timeline";
import { StatusBar } from "./panels/StatusBar/StatusBar";
import { useWorkspaceStore } from "./project/workspaceStore";
import { usePlaybackStore } from "./project/playbackStore";

export const App: React.FC = () => {
  const {
    leftPanelWidth,
    rightPanelWidth,
    bottomPanelHeight,
    showMediaBrowser,
    showInspector,
    showTimeline,
    setLeftPanelWidth,
    setRightPanelWidth,
    setBottomPanelHeight,
  } = useWorkspaceStore();

  const { togglePlay, stepFrame } = usePlaybackStore();

  const [resizing, setResizing] = useState<"left" | "right" | "bottom" | null>(null);

  // Global VFX Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore when focused in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        togglePlay();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        stepFrame(-1);
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        stepFrame(1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [togglePlay, stepFrame]);

  // Handle panel resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!resizing) return;
      if (resizing === "left") {
        setLeftPanelWidth(e.clientX);
      } else if (resizing === "right") {
        setRightPanelWidth(window.innerWidth - e.clientX);
      } else if (resizing === "bottom") {
        setBottomPanelHeight(window.innerHeight - e.clientY - 24); // Account for status bar
      }
    };

    const handleMouseUp = () => setResizing(null);

    if (resizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [resizing, setLeftPanelWidth, setRightPanelWidth, setBottomPanelHeight]);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#121214] text-[#f4f4f6] overflow-hidden font-sans select-none">
      {/* 1. Top Menu Navigation */}
      <TopMenu />

      {/* 2. Main Middle Workspace Area (Left + Center + Right) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Panel: Media Browser */}
        {showMediaBrowser && (
          <div style={{ width: `${leftPanelWidth}px` }} className="shrink-0 h-full">
            <MediaBrowser />
          </div>
        )}

        {/* Left Resize Handle */}
        {showMediaBrowser && (
          <div
            onMouseDown={() => setResizing("left")}
            className={`resize-handle-x ${resizing === "left" ? "active" : ""}`}
          />
        )}

        {/* Center Panel: Main Preview Viewer */}
        <div className="flex-1 h-full min-w-[300px]">
          <Viewer />
        </div>

        {/* Right Resize Handle */}
        {showInspector && (
          <div
            onMouseDown={() => setResizing("right")}
            className={`resize-handle-x ${resizing === "right" ? "active" : ""}`}
          />
        )}

        {/* Right Panel: Inspector Controls */}
        {showInspector && (
          <div style={{ width: `${rightPanelWidth}px` }} className="shrink-0 h-full">
            <Inspector />
          </div>
        )}
      </div>

      {/* Bottom Resize Handle */}
      {showTimeline && (
        <div
          onMouseDown={() => setResizing("bottom")}
          className={`resize-handle-y ${resizing === "bottom" ? "active" : ""}`}
        />
      )}

      {/* 3. Bottom Panel: Timeline */}
      {showTimeline && (
        <div style={{ height: `${bottomPanelHeight}px` }} className="shrink-0">
          <Timeline />
        </div>
      )}

      {/* 4. Bottom Status Bar */}
      <StatusBar />
    </div>
  );
};
